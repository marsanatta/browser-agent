# 分析 — browser-agent

> 本文為 [ANALYSIS.md](ANALYSIS.md) 的中文版。技術術語保留英文。

本報告涵蓋作業要求分析的四件事:**runtime performance、cost、scalability,以及如何驗證
correctness。** 最後一項最難 —— 一個自主 agent 很樂意「宣稱」自己在一個根本沒檢查過的頁面上成功了。
系統設計在 [README](README.md);本文只談分析。

*一句話設計(完整設計見 README):* **由單一 language-model session 一步步驅動瀏覽器(*agentic*
engine),而成功與否由確定性檢查決定 —— 絕不是 model 自己說了算。** 這不是最初的設計。專案一開始是
確定性的 **`script-orchestration`** engine(一種 plan-then-execute 設計:model 先寫一次計畫,再由
Python 一步步執行 ——「把 LLM 排除在 loop 之外」),後來在**一次受控量測證明 agentic loop 既更可靠、
又沒有更貴**之後切換([§2](#2-cost))。舊 engine 保留、可用 `AGENT_MODE=script-orchestration` 選用,
但不再是預設(`backend/app/main.py`)。

*數字從哪來。* 可靠度/成本:eval harness 跑自建的 **80-task live set**
(`eval/eval_set/live_real_world.yaml`)+ 一次受控 A/B
(`research/executor-ab-plan-mode-vs-llm-in-loop.md`)。Runtime:對部署的容器實跑 4 個代表性 task、
量測真實 event 時間戳。重現:`python -m eval.run_live_tier`、`python -m pytest -m "not live" -q`。

> **全文兩個術語。** *Nominal* success = agent 結束時宣稱成功。*Verified* success = 獨立檢查在最終
> 頁面確認目標達成。兩者的差距就是 **silent-failure rate**(CuP)—— 最關鍵的可靠度數字。

---

## 1. Runtime performance

**Wall-time 由 language model 主宰,不是瀏覽器。** agentic engine 每個 task 跑一個 tool-calling
session;每次 model 決策之間,Playwright 動作只花幾毫秒。為了看清楚時間**花在哪**,一次實跑對 4 個
代表性 task 做了 instrument,用真實 event 時間戳把 wall-time 分桶(browser launch → LLM round-trips
→ Playwright tool-exec):

![Runtime 分布:~86% LLM round-trips、~10% 瀏覽器動作、~4% launch](docs/runtime-distribution.svg)

| Task(live, measured) | Total | Launch | LLM round-trips | Tool-exec | Calls | LLM % |
|---|---|---|---|---|---|---|
| docs.python.org(2-hop nav) | 20.9 s | 3.0 s | 17.2 s | 0.7 s | 3 | 83% |
| Wikipedia(autocomplete) | 36.2 s | 1.0 s | 33.5 s | 1.7 s | 7 | 92% |
| GOV.UK(2-hop browse) | 54.8 s | 1.6 s | 43.1 s | 10.1 s | 8 | 79% |
| amazon.com(search + click) | 67.9 s | 1.5 s | 61.2 s | 5.2 s | 13 | 90% |
| **平均 / task** | **44.9 s** | **1.8 s (4%)** | **38.8 s (86%)** | **4.4 s (10%)** | **7.8** | **86%** |

- **瓶頸就是 model round-trip:約 86% 的 wall-time、每次 call ~5.2 s × ~8 calls。** Playwright 動作
  (click/fill/navigate/observe + screenshot)只佔 ~10%,browser launch ~4%。Task 時間隨 **model
  call 次數**而非頁面大小變化 —— 3-call 的 task 21 s 完成,13-call 的 68 s。
- **壓低 call 次數靠的是 filtered perception。** `observe` 只回傳 accessibility name 跟目標相關的
  互動元素,絕不回整頁(`backend/app/agent/agentic/cdp.py`),所以每次 round-trip 的 input 都很小,
  loop 只需 ~8 calls 而非 30。
- **Loop 有上限**,卡住的 task 會乾淨結束而不是永遠跑(`backend/app/agent/agentic/skill.py`):

  | 上限 | 值 | 為什麼 |
  |---|---|---|
  | Tool-call budget | 25 calls | 在 wall-clock 前強制收尾 |
  | Session timeout | 120 s | 每個 task 的硬上限 |
  | Per-handler timeout | 15 s | 單一卡住的 navigation 不能拖垮整個 session |

- **未來加速在哪、不在哪。** 因為 86% 時間是 model,真正有效的槓桿只有:**(a) 更少 round-trips**
  (更聰明的 perception / 需要更少步驟的 model)、**(b) 每次 call 延遲更低的 model**、**(c) prompt
  caching** 降低單次延遲。優化瀏覽器那 10% 或 launch 那 4% 都動不了大局。這跟 cost 的槓桿一樣
  ([§2](#2-cost)):model call 同時是時間與花費的單位。

*附註 —— offline 路徑是 sub-second。* 確定性部分(perception 過濾、verify gate、`detect_block`)是
本機 DOM/算術運算;233 個 unit test 在無網路下幾分鐘跑完。上面的 wall-time 完全是 model + live 網路。

---

## 2. Cost

**GitHub Copilot 訂閱是 flat-rate,不是 per-token。** 每次 model call 都經 Copilot SDK 當 gateway,
所以沒有 per-token 帳單。真正會綁住的資源是**每個 task 的 requests 數**(~8–10),受 Copilot
premium-request 配額與 rate limit 限制 —— 不是錢。下面的金額是從 Copilot 自己的 token ledger
(`Σ total_nano_aiu / 1e11 ≈ USD`)**估算**的,僅供比較。

### 2.1 實驗 —— 以及為何從 `script-orchestration` 遷移

從 `script-orchestration` 切到 agentic engine 是基於證據、不是偏好。依據是**一次受控 A/B**
(`research/executor-ab-plan-mode-vs-llm-in-loop.md`),設計來回答一個精確問題:*對同一組 task,哪個
executor **架構**在 verified-rate、silent-failure(CuP)、cost 上勝出 —— 而且成本差距裡有多少是
**架構**、多少是 **model 選擇**?*

**設計 —— 三個 config,把 model 從架構裡拆出來。** 單純「舊 vs 新」會把架構與 model 混在一起
(`script-orchestration` 用貴的 `claude-opus-4.8` 規劃;agentic engine 整段跑一個便宜的
`claude-haiku-4.5`)。所以舊 engine **跑兩次**,湊成三個 config:

| Config | 架構 | Planner model | Exec model | 隔離出什麼 |
|---|---|---|---|---|
| **A-haiku** | `script-orchestration` | haiku | haiku | **model 固定** → 架構本身相對 B 的價值 |
| **A-opus** | `script-orchestration` | opus | haiku | 該 engine 的 production 配置 + 一個 faithfulness anchor |
| **B** | agentic(LLM-in-loop) | —(self-plans) | haiku | agentic engine,原封不動 |

`A-haiku vs B` 是 clean-science 數字(同 model,只有架構不同);`A-opus vs A-haiku` 是貴的 planner
單獨買到多少。

**Invariants —— 讓它成為乾淨科學的關鍵。** 兩個 engine 放在**同一個 worktree**,所以 eval set
(sha256 `7dd278b7…`)、harness、scoring、browser provider、cost 公式都逐位元相同;**只有 executor
不同**,由 `AGENT_MODE` 在 runtime 切換。每個 config 的成功都由**獨立的** `eval/verify` state-check
評斷 —— *絕不是* agent 自報。作為 faithfulness anchor,**A-opus 把先前一次獨立的 head-to-head
重現到分**($9.39),證明這個平台是忠實的重現。

![Cost A/B:$9.39→$3.24 的差距 ~90% 是 model、~10% 是架構](docs/cost-decomposition.svg)

| Engine | Model | Verified | Silent failures (CuP) | Cost | Calls/task | $/task |
|---|---|---|---|---|---|---|
| `script-orchestration` | haiku | 0.500 (40/80) | 18 | $3.85 | 3.4 | $0.048 |
| `script-orchestration` | opus planner | 0.762 (61/80) | 10 | $9.39 | 1.9 | $0.117 |
| **agentic(預設)** | **haiku** | **0.900 (72/80)** | **1** | **$3.24** | **10.4** | **$0.040** |

*(`internet_modal` 在每一欄都被算成 silent failure,後來發現是 verifier 的大小寫 bug —— 與 engine
無關,所以 deltas 不受影響;修正後預設為 73/80、CuP 0。)*

**結果,三個讀法:**

1. **純架構(A-haiku vs B,model 固定):** verified **0.500 → 0.900(+40 pp)**、silent failures
   **18 → 1(少 18×)**,而且**便宜約 16%**,*儘管多打 3× 的 call* —— filtered 逐步 perception 讓
   每次 call 很小,而 `script-orchestration` 每次重送整頁 perception。
2. **opus planner 買到什麼(A-haiku → A-opus):** verified +26 pp,但**貴 2.4×** —— 而且還是
   *輸給* agentic-on-haiku(0.762 vs 0.900),價格約 2.9×。
3. **拆解「`script-orchestration` 便宜約 5×」的舊說法**($9.39 → $3.24):model swap(opus → haiku)是
   **−$5.54 ≈ 90%**;架構 swap 是 **−$0.61 ≈ 10%**。表面的成本優勢*大半是 model*,不是架構。

**`script-orchestration` 為何會 silent fail —— 結構性原因。** 它的 planner 從*整頁*快照先驗地定好
步驟,接著 Python 盲目執行,看不到每步實際落在哪。當某步撞上 login 牆或錯頁面,engine 照跑計畫、
**對一個它從沒重新檢查的 state 宣稱成功** —— `nominal=True, verified=False`。這就是
**planner-open-loop ceiling**,也是 CuP 隨 planner 變弱而上升的原因(B 1、A-opus 10、A-haiku 18)。
engine 帶的 localized step-repair 修的是*另一個*洞(replan 掉了未來目標),不是這個。agentic loop
**從結構上**避開這個 ceiling:它每一步都看到 live 頁面,所以會適應、撞牆時誠實 abstain。

所以我們遷移,是因為 agentic engine **更可靠*且*同 model 下沒有更貴**;輸的那個保留可選,供誠實比較。

### 2.2 一個我們「還沒」量的成本槓桿(future exploration)

上面每個數字都只用**一個 model —— `claude-haiku-4.5`。** 我們**還沒**跑 model sweep,而 §1 說明了
為什麼這很重要:**成本與時間都是 `calls × per-call`。** 一個更貴但更強的 model 可能用**更有效率的
trajectory** 達成目標 —— 更少 round-trips、更少死路重試 —— 因而**整體更便宜也更快**,即使單次 call
更貴。A-opus 那列暗示了另一個極端(又貴、又多打錯方向的 call),但中間是未知的。誠實的下一步是
做 per-model sweep(把 *in-loop* model 從 haiku → sonnet → opus),同時用 verified-rate **與**
calls/task **與** $/task 一起評分 —— 更強的 model 只有在 trajectory 縮短到足以抵銷其單價時才算贏。
此為 future work,並非已成立的結論。

---

## 3. Scalability

這裡的 "scalability" 指三件不同的事;系統對每一件都誠實。

### (a) Runtime / throughput

- **Stateless、每個 task 一個 ephemeral 瀏覽器。** 每個 task 開自己的 browser context
  (~300–500 MB),關閉時回收(`backend/app/browser/`),所以 task 之間不漏狀態、workers 彼此獨立。
  水平擴展就是「多開 workers」—— 沒有共享 session 要協調。
- **天花板是 model rate limit,不是 CPU/RAM。** 既然一個 task 86% 是 model round-trips(§1),
  throughput 受 **Copilot premium-request 配額**限制,不是瀏覽器記憶體。加 workers 只在配額綁住前有用。
- **誠實限制:** 目前部署是單一 Azure Container Apps replica;work-queue + autoscale 的形狀是
  **設計過、但未建置**。

### (b) Code extensibility —— 結構能不能吸收更多 perception、檢查、recovery?

昂貴、有風險的部分都藏在穩定的 seam 後面;報告也誠實標出哪些是乾淨的 plug-in、哪些是 coupling。

- **新 executor engine —— 乾淨。** agentic 與 `script-orchestration` 兩個 executor 共用完全相同的
  constructor 與同一個 `run(task) -> AsyncIterator[Event]` stream,由 `AGENT_MODE` 選
  (`backend/app/main.py`)。前端與 eval harness **原封不動**就能吃任一 engine —— 這正是 §2 A/B 能
  成為乾淨科學的原因(唯一變數是 executor),第三個 engine 也用同樣方式插入。
- **新 bot-wall / block 訊號 —— 乾淨、已驗證。** `detect_block`(`app/agent/verify.py`)是四層有序的
  marker list(URL / 可見 widget / body text / HTML 中的 challenge-host)。已用這方式加了兩個訊號、
  沒有結構改動:modern Cloudflare 的 "Just a moment…" interstitial(兩個 body-text marker)與
  DataDome(`captcha-delivery.com` challenge host,以空 body 為 gate)。每種新牆是一個 list entry,
  不是重寫。
- **新 verification 檢查 —— 乾淨。** 成功由 `app/verify/state.py` 裡的小型確定性 primitives
  (`url_contains` / `selector_text_equals` / `text_visible`)評斷;新檢查 = 一個新 primitive + 一個
  branch,而且 eval harness 與 production **共用**,所以修正只落一處。
- **可抽換 browser runtime —— 乾淨。** `BrowserProvider` 包住瀏覽器,預設 headless Playwright,並有
  **CDP escalation seam** 接真 stealth 瀏覽器(Steel.dev / Browserbase tier)—— 這個 seam 就是把真正
  的 403 牆從硬停變成可恢復案例的關鍵。
- **Failure-handling 策略 —— 部分乾淨。** Failure *類別*是 enum(`classify.py`),
  `script-orchestration` engine 有明確的 recovery 模組(`recover.py`);agentic engine 的 recovery 由
  in-loop prompt(`skill.py`)+ finish gate + rejected-finish abstain cap 驅動。加一個*類別*是乾淨的;
  但改 *agentic recovery 政策*意味著改 prompt contract —— 這是誠實的 coupling,因為下一步策略是由
  model(而非 dispatch table)決定。

### (c) Eval toolchain —— `eval/` 能不能低成本長大?

可以;這比任何單一 engine seam 都更會 scale。

- **加 case —— append-only YAML,不改 code。** `eval_set/*.yaml` 是 pin 好的 task spec;
  `run_live_tier.py` 與 `loader.py` 直接吃,所以加 case 是資料、不是程式。
- **以 *purpose* 設計,而非數量。** 每個 case 帶一個 `purpose` tag(它測的那一個能力或 failure-mode);
  冗餘的同 purpose filler 被裁掉(147 → 80)。Per-purpose 評分來自通用的 group-by,所以**新 purpose
  就是一個 tag**,新的 failure-mode 家族就是一個新檔(`mechanisms.yaml`、`diagnostic.yaml`)——
  不是改 harness。
- **Split 由 code 強制。** dev / holdout / sealed **依站點互斥**,而且 loader **拒絕評分 sealed**,
  除非明確 `--sealed` —— 這是防止意外偷看 / selection over-fit 的守衛,不只是慣例。
- **標準、可重複的評分。** `scoring.py`(nominal-vs-verified / CuP)、`passk_diag.py`(pass^k, k=5)、
  `report.py`、`audit.py` 提供一套標準方式評分任何新 case set,而 two-pass admission probe
  (`validate_candidates.py`)被重用來准入新 case。所以探索新能力就是「加 tagged YAML → 跑標準
  harness」—— 正是把 set 長到 80 所用的 loop。

---

## 4. Correctness 如何驗證(agent 不能給自己打分)

agent 可靠度最難的問題是:**跑完所有步驟的那個 agent,會在它根本沒檢查過的頁面上回報成功。** 所以整個
驗證設計遵守一條規則:**self-report 絕不被當成成功。** 下面每一層都獨立於 agent 的宣稱,由 per-step
gate → 獨立的事後 assertion → 多次重跑門檻,層層加嚴:

![Verification stack:in-loop gate、獨立 assertion、CuP、per-split、pass^k](docs/verify-stack.svg)

### 4.1 為什麼「成功」需要一個提供的 criterion —— 以及它從哪來

一個自然語言的瀏覽器 task **沒有通用的 ground truth。**「開啟 json 模組頁」「找出這本書的價格」
「到 Ask HN」—— 每一個的「完成」定義都不同、都是 task-specific。沒有 task-specific 的檢查,唯一可用的
訊號就是 agent 自己的宣稱 —— **nominal** success —— 而那正是我們不信任的訊號。**把 *nominal* 變成
*verified* 的唯一東西,就是一個確定性、有鑑別力、task-specific 的成功檢查。** 所以系統一律從 agent
之外取得這個檢查,在它跑的兩個地方都是如此:

- **在 eval harness,由 task 作者寫。** 80 個 case 每個都帶一條手寫 assertion(`url_contains` /
  `h1_equals` / `selector_text_equals`),「只有在 task 真的完成時」才為真,並由 two-pass gate 准入
  (§4.4)。
- **在 production,由使用者提供**(前端的 success-criterion 欄位)—— 因為只有 caller 知道*他的* task
  怎樣才算「完成」。`backend/app/main.py` 驗證它(`_parse_criterion`)並包裝它(`_make_verify_hook`),
  在 live 最終頁面跑**與 eval harness 相同的 `state_check`**。兩個設計選擇讓它可信、而非裝飾:
  - **它無法被湊成意外通過。** 只接受確定性、*有鑑別力*的 key;鬆的 body-text `text_contains`
    (或任何未知 key)會被 **HTTP 400 拒絕**。一個「會在錯頁面上通過」的 criterion 在門口就被擋下。
  - **它也 gate 住 agent 自己的 finish。** Production 把 criterion 串進 agentic **finish gate**
    (#4b):agent 必須在使用者的 criterion 於 live 頁面成立時,才能 `finish(success=true)` ——
    不只是它自選的 verify。

這就是為什麼 verdict 標示得很誠實:**有** criterion 時,「verified ✓」代表那個獨立檢查確實跑過且
通過(而 silent failure 即使 agent 宣稱成功也會顯示 `verified=false`);**沒有** criterion 時就沒東西
可斷言,該次 run 顯示為 **「actions completed — not goal-verified」**—— 刻意*不是* verified pass。
我們不宣稱任何 blanket 的 production「verified」保證,因為驗證只跟它背後的 criterion 一樣真實。

### 4.2 結果

| 指標 | 結果 | 範圍 |
|---|---|---|
| Verified rate(總計) | **0.913 (73/80)** | 全部 80 task |
| **Silent-failure rate(CuP)** | **0/80** | 每個失誤都是誠實 abstain 或被標記的失敗,從不假宣稱 |
| pass^k(k=5;5 次全須 verify) | **1.000**、false-success **0/8** | 8 個 adversarial diagnostic task |

分 split 列、絕不彙總(彙總會讓簡單 task 蓋掉難的):

| Split | Tasks | Verified | Silent failures |
|---|---|---|---|
| dev | 39 | 0.923 | 0 |
| holdout | 21 | 0.810 | 0 |
| sealed(只評一次) | 20 | 1.000 | 0 |
| **Total** | **80** | **0.913 (73/80)** | **0** |

**Silent-failure rate 是頭條指標:** 系統只有在它*說出口*時才被允許出錯。silent failure = 一個被獨立
檢查推翻的宣稱成功;eval set 上一個都沒有。**pass^k** 再把重複下的可靠度門檻拉高 —— 在 8 個
adversarial task(intent-drift decoy、renamed / hidden-menu / control selector 擾動、dead-button
與 impossible-goal stagnation、synonym-locate)上,5 次全 verify、**0 個 false success**。

### 4.3 獨立檢查(為什麼用騙的過不了關)

| 檢查 | 證明什麼 | 為何獨立 |
|---|---|---|
| In-loop verify gate(`app/agent/verify.py` + `skill.py`) | agent 只有在確定性檢查於 live DOM/URL 通過**且**頁面未被擋時,才能 `finish(success=true)` | model 的話本身絕不被接受;在源頭擋下最常見的假宣稱 |
| 獨立事後 assertion(`eval/verify/state.py`) | 目標確實在 agent 留下的最終頁面成立 | **獨立的 code**、一個**手寫**的鑑別性 assertion,從不讀 agent 宣稱的輸出 —— 且刻意*不是* in-loop 公式(in-loop goal 由 model 自選,太鬆的 goal 會在錯頁面上通過) |
| Nominal-vs-verified / CuP(`eval/scoring.py`) | 計算「宣稱成功卻被推翻」 | agent 宣稱與獨立檢查之間的差距 |
| Per-split、sealed 只評一次(`loader.py`) | generalization,不是背站點 | loader 拒絕評 sealed,除非 `--sealed` |
| pass^k(`passk_diag.py`) | side-effecting task 在重複下的可靠度 | k 次全須各自獨立 verify |
| Two-pass admission(`validate_candidates.py`) | *assertion 本身*夠嚴 | 真實瀏覽器 probe + 一位獨立 reviewer 確認每條 assert「只有在 task 完成時才為真」(兩位 reviewer 100% 一致);太鬆的「值出現在列表上」assert 被丟掉 |

這個設計從一開始就帶來一個後果:**一個修正只有在某個獨立檢查改善、而控制組不變時才保留** —— 絕不靠
放鬆它被量測的那個檢查來讓改動「過關」,而且改善宣稱都附 **budget-matched baseline**,讓收益藏不住
額外花費。

### 4.4 還做不到的(誠實清單 —— 標記出來,絕不悄悄出錯)

| 案例 | 行為 | 狀態 |
|---|---|---|
| Login / CAPTCHA / anti-bot 牆(例如 g2.com DataDome 403) | agent 偵測到牆並**誠實 abstain** —— 從不假成功、從不偽造指紋(route, don't evade) | 正確處理;CDP-stealth seam 已設計、未建置 |
| iframe 內容(iframe 裡的 rich-text editor) | grounding 只對 top frame,所以動不了 → 誠實 abstain | 已知限制 |
| Bot-wall 偵測是 **post-action,非 pre-flight** | `detect_block` 在動作後才抓 anti-bot/CAPTCHA;純 login 牆或互動式 checkbox 變體仍可能漏成一般 miss | pre-flight detector 是 future work |
| 長 failure tail | 找不到目標時,agentic loop 重試到 25-step budget(~$0.08–0.10/task),比 `script-orchestration` 早早放棄更貴 | 這是逐步可靠度的誠實代價(§1–§2) |

### 4.5 數字的誠實界定

`n = 80` 是 **coverage** 檢查,不是母體估計;per-split 比率是指示性的。Runtime 數字(§1)是一個部署上
4 個代表性 task,所以它刻畫的是時間*花在哪*(86% 是 model 這點很穩健),而非精確的 per-task SLA。
Live 公開站點每次跑會抖幾個 task,而 A/B 是單次跑 —— 所以我們信大差距(verified 40→72、silent
failures 18→1),並明確**不**過度解讀小的 per-split 差異。

---

## Reproduce

```powershell
# offline unit tests(scoring、verify、loader)—— 無網路、不需 Copilot
python -m pytest -m "not live" -q

# live eval,分 engine(預設 = agentic;設 AGENT_MODE 用 script-orchestration)
python -m eval.run_live_tier            # dev + holdout
python -m eval.run_live_tier --sealed   # 只跑一次的 sealed split
python -m eval.passk_diag               # 在 adversarial diagnostic set 上跑 pass^k (k=5)
AGENT_MODE=script-orchestration python -m eval.run_live_tier   # legacy engine
```

受控 A/B 在 `research/executor-ab-plan-mode-vs-llm-in-loop.md`;eval set 與其依站點 split 在
`eval/eval_set/live_real_world.yaml`;pass^k ledger 在 `eval/PASSK_DIAG.md`。
