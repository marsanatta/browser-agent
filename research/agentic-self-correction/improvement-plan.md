# LLM-in-loop browser-agent —— 改進實驗計畫(handoff brief)

> **讀者**:在 `_wt/ba-llm-loop`(branch `llm-in-loop`,`AGENT_MODE=agentic`)工作的 coding agent。
> **目的**:讀完這一份就具備執行所需的完整 context —— 研究依據、現狀 code 缺口、重排後的 TODO、
> 新增的受控診斷 eval set、以及每一項的獨立驗證方式。**先讀完全文再動手。**
> **語言**:繁體中文敘述,技術術語 / 路徑 / 函式名 / error message 一律 English。
> **日期基準**:2026-06-28。Homework deadline 在即,計畫已 deadline-aware(見 §8 排程 + 切線)。
>
> ⚠️ **先讀 Part II(§11 起)**:那是 2026-06-28 對著 `_wt/ba-llm-loop` **實際 code 核對過**的
> ground truth + 操作細節(run 指令、task schema、worked example、blast radius、baseline 擷取)。
> **凡 Part II 與 Part I 衝突,以 Part II 為準** —— Part I 是策略敘事,Part II 是執行真相
> (例如:pass^k **已經存在**、診斷集是**擴充現有檔**而非從零建)。

---

## 0. TL;DR(一段話)

現在的 LLM-in-loop executor **成本已勝 browser-agent 5.2×、verified-rate ~打平**,但 grader 的核心軸
**self-correction / 策略適應**目前**沒有好機制**:我們有「戰術重試」(retry 同一招、換 target),
沒有「策略切換」(偵測整個 approach 不通 → 換 approach),而且**比 browser-agent 原版的 replanner 還弱**
(我們把顯式策略層換成了無觸發、被 give-up cap 壓制的隱式 LLM 適應)。

本計畫:用 5 個 OSS 的研究依據,做**三件套策略適應**(stagnation 偵測 → 丟 filter 看清現況 → 用「歧義 vs 不存在」
訊號選策略)+ **嚴格化 verify**(抬 trustability、修 amazon wrong-page bug)+ **pass^k 量測**。
全部 **cost-neutral 或 cost-positive**,不動 headline 成本優勢。

**關鍵前提(§6 #0)**:這些實驗**無法**用現有 live 80-set 驗證(live 站不可控、pass^k 被站噪音污染),
必須先建一個**小型受控診斷集**當尺。沒有它,「self-correct 改善了」只能靠 agent 自報 ——
違反工程鐵則「never 用 self-consistency 當驗證」。

---

## 1. 背景:這個 executor 是什麼

`backend/app/agent/agentic_executor.py` 是 browser-agent 的 LLM-in-loop 替代執行器,與原本的
plan-then-execute `Executor` **同介面、同 Event stream**(SSE 前端 + eval harness 不改即可消費),
差別在內部:不是 `while i < len(subtasks)` 的確定性 plan loop,而是**一個 Copilot function-calling
session 自驅**,呼叫 tools:`observe / read / click / fill / navigate / verify / finish`。

- **成功判定**:由 browser-agent **自己的** `app/agent/verify.py`(`_goal_satisfied` + `detect_block`)
  以 `verify` **tool** 形式暴露,讀**真實 page**,**never** LLM 自報。`finish(success=true)` 被這個
  deterministic gate 把關。
- **單一模型**(`_model_for`,預設 `claude-haiku-4.5`);plan era 的 planner/replanner/executor
  模型區分**已折疊**(這點很重要,見 §5 的架構諷刺)。
- **max_attempts / max_replans → tool budget**(`TOOL_BUDGET=25`,`skill.py:15`)。
- **感知便宜化**:`agentic/cdp.py` 的 `perceive` 在瀏覽器內 JS 過濾,只回名稱與 target 相關的元素
  (`_SCAN_JS`),這是成本勝出的結構性槓桿(filtered vs full-page perceive)。

**現狀 head-to-head(80-task live set,真實 Σnano/1e11 USD,獨立 state_check)**:
成本每個 split 都贏(總 5.2×);verified 總體 ~打平(0.838 vs 0.80)。
**已知共同天花板**:wrong-page / soft-login-wall 的 silent failure 在 production 無 oracle
(你昨天親手抓到的 amazon「light」案例就是這個)。

---

## 2. 目標與權重(排序的透鏡)

| Target | 角色 | 對排序的影響 |
|---|---|---|
| **COST**(headline)| **constraint,非 improvement** —— 已 5.2× 領先 | 任何改動**不准**惡化成本;cost-positive 優先 |
| **Self-correction / 策略適應** | **主要 improvement target**(grader 核心軸)| 最高權重 |
| **Trustability / verified-rate**(wrong-page 天花板)| 次要 improvement | 高 grader 價值 |
| **pass^k 可信度量** | **證明**上面有效的工具(量測,非機制)| 必要但服務性 |

**判準**:策略適應三件套 cost-positive 又直打 grader 軸 → 第一。
把 LLM 塞進成功判定、或加 per-call 成本的 → 砍(見 §6 ❌)。

---

## 3. 研究依據(5 個 OSS,已 clone 至 `~/workspace/repos/job/homeworks/reference/`,全 cited)

5 個獨立 reader agent 精讀了 5 個不同 codebase,**對我們的 3 個弱點收斂到同一組修法**。
以下是可採用的 lesson(附原始 file:line,供你需要時去 reference 對照)。

### 3.1 browser-use(`reference/browser-use/`)
- **感知**:index **所有** interactive element,**從不**按 name 過濾。`clickable_elements.py:6-246`
  用 ~12 個與名稱無關的訊號判互動性(真實 CDP click listener、tag set、AX focusable/editable、
  role、event-handler attr、`cursor:pointer` fallback);`serializer.py:617-727` 序列化整樹,
  行格式 `*[<id>]<tag attrs/>`(`*`=自上步新增)。
- **成本控制(讓「index everything」可行)**:bbox-containment 抑制子節點 `serializer.py:45-57,729-838`;
  paint-order occlusion 移除 `paint_order.py`;wrapper flatten `:542-576`;attr allow-list `views.py:18-62`。
- **grounding**:LLM 選的整數**就是** CDP `backend_node_id`(`serializer.py:712-713`),動作端 O(1)
  dict lookup → `DOM.resolveNode`;**沒有 xpath/CSS/role-name 定位**。壞/stale id = **soft 可復原 observation**
  (`tools/service.py:711-714`),**不是 halt**。
- **verify**:獨立 LLM-judge 第二道(`agent/judge.py`,「be doubtful / 每步雙重確認真的發生」`:170-175`,
  `ground_truth` ABSOLUTE precedence `:96-103`)—— **但它 telemetry-only,不 gate runtime**(`service.py:1623-1625`),
  這是它的弱點。另有 prompt 強制的 `pre_done_verification` checklist(`system_prompt.md:139-153`:
  「每個 URL/price/value 必須逐字出現在 tool output/browser_state,不准用常識」)。
- **loop 偵測**:`views.py:157-248` rolling hash + 在 5/8/12 次重複時發**升級的 soft nudge**;
  最後一步 / max_failures 後 **forced-done schema swap**(`service.py:1560-1582`)。

### 3.2 stagehand(`reference/stagehand/`)
- **act 層 self-heal**:動作用 deterministic Playwright xpath(**no LLM**),**只在 selector throw 時**
  才 re-snapshot + 一次 LLM re-ground + 用**同 intent** 重試(`actHandler.ts:327-433`)。
- **快取 resolved selector**:key=`sha256(instruction+normalizedURL+sortedVariableKeys)`,
  **變數值排除**、執行時代入(`ActCache.ts:151-199`);命中時 `waitForSelector(attached)` + Playwright,
  **不呼叫 LLM** → 讓重複跑的 pass^k 幾乎零 act-LLM 成本。
- **outcome vs process 拆開**:verifier 回 `outcomeSuccess: boolean` + `processScore∈[0,1]`
  (`rubricVerifier.ts:673-693`);outcome 規則明文(`fusedOutcome.ts:62-90`):
  **到對的頁 ≠ 成功,除非最終答案含要求的 deliverable;URL/值不符 = 矛盾,不是 assumed redirect;
  只 judge 抓到的 browser state,不靠模型常識**。
- **prompt 禁造假 + null-action**:`prompt.ts:192,229`,`inference.ts:456-459`(找不到就回 null,不要瞎掰)。
- **多 trial 但只 mean-pass,無真 pass^k**(`runner.ts:308,443`)。

### 3.3 Agent-E(`reference/Agent-E/`)
- **感知 = 完整 AX-tree,不按 target 過濾**(`get_detailed_accessibility_tree.py:496,508-509`),
  唯一 filter 旋鈕是 role 層的 `only_input_fields`,**不是 name filter**;LLM 自己從整樹挑。
  成本靠**確定性後處理**:attr dedup `:260-289`、tree prune/unravel `:353-451`、
  `<select>` flatten 成 options `:139-153`、icon-only button 收 child attr 成 `additional_info` `:209-233`。
- **grounding**:注入 sequential `mmid` 到每個元素(`:38-52`),動作用 `querySelector([mmid="…"])`,
  事後 cleanup `:333-350`;**每次 observe 重新注入**(re-render 即失效)。
- **per-action change signal**:in-page `MutationObserver`(`dom_mutation_observer.py:30-65`),
  click/type 前後 subscribe;若有新節點 → 回 LLM「動作尚未完成,需進一步互動」。
  **自承漏 attribute/visibility 變化**(`:27`)。另有 `aria-expanded` before/after 檢查
  (`click_using_selector.py:200-205`)。
- **loop 偵測**:`detect_llm_loops.py:6-46`(最近 3 個 tool-call/response 對相同 → 強制 terminate)。
- **eval**:WebArena 式確定性 evaluators(`test/evaluators.py`),`HTMLContentEvaluator` 重新導航到
  目標頁、跑 JS locator、斷言**真實 DOM 副作用**(非 agent 自報)。

### 3.4 agent-browser(`reference/agent-browser/`)
- **它沒有 task-level 成功 gate**:deterministic Rust toolbelt,LLM 在外驅動;
  `tool_result_from_run`(`mcp.rs:3559-3587`)只回 per-command 執行成功(「這個 click 有沒有 dispatch」),
  **不是**「task 有沒有成功」。
- **discriminating verify 教條**:`SKILL.md:169-173` + `references/authentication.md:143-144`:
  `get url # Should be dashboard, not login` —— verify 必須是**判別式**(對的頁真、似是而非的錯頁假)。
- **wait primitives**(對應我們的 verify):`actions.rs:4161-4304` —— `wait --url`(glob 錨定)、
  `wait --text`、`wait --fn`(**任意 JS predicate**,比我們三個 primitive 更表達力強),每 100ms poll 到 25s。
- **每個 snapshot 都帶 `origin`(live URL)**(`snapshot.rs:298-419`)→ driver 每次觀測免費 re-ground URL。
- **deterministic-gate + LLM-advisory-score 分離** + `forbiddenPatterns`(負向 gate)(`evals/lib/judge.ts:11-88`);
  single-trial(`run.ts:119-147`)。

### 3.5 browser-use/benchmark(`reference/benchmark/`)
- **k=5 全集重跑 + bootstrap 95% CI**(`orchestrator.py:27`,`generate_plots.py:163-174`);
  **丟棄不完整的 run**(`:138`)。**注意:它只到 run-level CI,沒有 per-task pass^k**。
- **「加密 task」= 公鑰混淆,非 secret holdout**:key=`sha256(公開 benchmark 名)` 寫死在 repo
  (`run_eval.py:64`)→ 只防爬蟲,任何人 3 行解密。**我們的 dev/holdout/sealed disjoint-by-site 是更強的 primitive**;
  只需抄它的 hygiene(sealed 用 repo 外 key 加密 at-rest、trace 標 never-publish)。
- **runtime `impossible/excluded` flag**(`judge.py:120-134`):網站當機記 excluded 非 failed
  —— 對 **live** bench 至關重要(real-site flakiness)。
- **per-category accuracy + accuracy-vs-cost/throughput Pareto**(`generate_plots.py:299`)。
- **subprocess + `ExecutionResult` adapter**(`frameworks/__init__.py:63-71,256`):多 agent 比較時的
  crash/dependency 隔離 + 單一共用 scoring 函式。

### 3.6 跨 repo 收斂結論(高 confidence)
| 我們的弱點 | browser-use | stagehand | Agent-E | agent-browser | benchmark |
|---|---|---|---|---|---|
| synonym-blindness | ✅ index 全部 | ✅ pruned a11y LLM 選 | ✅ 全 AX 不 filter | — | — |
| wrong-page silent fail | ✅ LLM-judge 2nd | ✅ outcome 拆 process | — | ✅ discriminator | — |
| ambiguity-stop / grounding | ✅ id=backend_node | ✅ self-heal+cache | ✅ mmid | ✅ self-heal | — |
| pass^k / eval rigor | 無 | mean-pass(無真 pass^k)| WebArena | 無 | ✅ k=5+CI(無 pass^k)|

**5 個 repo 沒有任何一個有真 per-task pass^k,也沒有任何一個有「caller criterion 強制進 finish gate」的
deterministic 成功閘。** 我們的 deterministic verify gate + sealed split 是真 moat —— 保留它,別退化。

---

## 4. 現狀 code trace —— 我們已有的 self-correction(帶 file:line)

executor **本來就是會自我修正的 loop**:每個 tool handler 都 return 字串給 LLM,session 繼續,
所以錯誤是當 observation 餵回去,不是終止。

| 機制 | 位置 | 餵回 LLM 的訊號 |
|---|---|---|
| click 變化偵測 | `agentic_executor.py:339-343` | `before/after` snapshot diff → `{"changed": false}`;SKILL 規定「沒變=點歪,observe again」 |
| NOT_FOUND 可復原 | `:328-329` | 「observe again or finish」(非 halt)|
| timeout 可復原 | `:325,357,385` | 「try a different target」 |
| **finish reject 後餵回重試** | `:430-437` | 「REJECTED… call verify(goal) and only finish once it confirms」 |
| state change 後強制重新 verify | `:316,348,377` | `last_verify_ok=False` 防 stale verify 假性 finish |
| **每動作重新 ground(無快取)** | `:323,354` → `cdp.ground:372` | UI 改 class/id **不會壞**,因為不綁 selector,每次從 role+name 重推 |
| 7-tier locate cascade | `cdp.py:232,254-274` | `role_name→role→id→testid→aria_exact→href→text`,某招失效換下一招;歧義(n>1)**STOP** `:273` |

---

## 5. 現狀缺口 —— 策略適應(這是 grader 軸的真洞)

把問題拆兩層,我們在兩層狀況**相反**:

- **selector / locator 層**:✅ **夠強**。每動作重跑 cascade + 不快取 → 純 selector 漂移撐得住
  (stagehand 要 self-heal/cache-invalidation 才解的,我們因「不快取」免疫)。**這層不是洞。**
- **策略層**:❌ **真洞**。那個 7-tier cascade 是**定位冗餘,不是策略適應**:

1. **cascade 對 LLM 隱形**:LLM 只收到 `NOT_FOUND`(`executor:329`)。`locate` 其實**知道**
   「name 中了但歧義」vs「完全沒中」(`cdp.py:269-273`),但在 `ground→None` 就**把這資訊丟掉**。
   LLM 無從判斷「UI 變了」還是「東西不存在」,無法據此換策略。
2. **重試的感測器是瞎的**:`observe` 用 `_SCAN_JS` 按 target name 過濾(`cdp.py:33,61-66`)。
   click 點歪 → 「observe again」→ **同一 target 字串再 filter → 同樣空結果**。UI 真變了/換 label,
   **看不到**,因為 filter 把改掉的 UI 藏起來。戰術迴圈空轉。
3. **give-up cap 主動壓抑策略探索**:`skill.py:56-61`「2 個 observe 找不到就 finish(false)」——
   為省成本 + abstain 正確性設的,但砍掉「換 approach 再試」的空間。
4. **架構諷刺(誠實話)**:browser-agent **原版** plan-then-execute 有 **REPLANNER**(opus-4.8)——
   那**就是**策略適應機制(step 失敗 → replan 剩餘策略)。改 LLM-in-loop 單模型時,
   **把顯式 replan 層換成了無 scaffold、無觸發、被 give-up cap 壓的隱式 LLM 適應**。

| | 戰術重試 | 策略適應 |
|---|---|---|
| plan-then-execute(原版)| 弱 | **強(replanner 顯式)** |
| LLM-in-loop(現在)| **強(自由 function-calling)** | **弱(隱式、無觸發、被壓)** |

**結論:我們有戰術靈活,失去顯式策略適應。要補的就是把「偵測 approach 失敗 → 看清現況 → 換策略」這條鏈接回來。**

---

## 6. 重排後的 TODO(含可行性、檔案、驗證)

### 🟦 #0 —— 受控診斷 eval set(**Tier-1 量測的前提,必須先做**)

**為什麼非做不可**:這些實驗**無法**用現有 live 80-set 驗證 ——
- 我**無法**把真的 amazon.com 搜尋鈕改名 → 策略擾動做不出來;
- live 站第 2 次失敗可能是**網站**(A-B/captcha/網路)→ pass^k = 站噪音 + agent 混在一起,**量不到 self-correction 本身**;
- 若 task 第一次就過,**根本不觸發**錯 selector/UI 變化 → 整個 set 系統性地**沒在考**策略適應。

用 agent 自報 recovery 來驗,違反 CLAUDE.md「never self-consistency」。所以這把尺是**誠實主張改善的前提**。

**設計**:小型**本地 static HTML** 受控集,4 個 capability slice,每 slice 3-5 task(共 12-20),
**contrast-pair**(control 版 vs 擾動版)。接到 harness **已支援的 `inline_html → data: URL`**
(見 STATUS.md harness loader)—— **同一 harness + 同一 state_check 判定,harness 一行不改**
(尊重「eval untouched / judge READ-ONLY」)。

| slice | 驗哪個機制 | 內容 | metric |
|---|---|---|---|
| **selector-perturbation** | #1+#2+#3 策略適應 | 同頁 control(正常 label)+ 擾動(目標鈕**改名 / 換 id / 藏進 menu**,讓 tier-1 role_name 失敗)| 擾動版 pass^k 能否逼近 control 版 pass^k;**差距=策略適應缺口** |
| **decoy / wrong-page** | #4a trustability | body **提到** target("light")但真目標在別處(results 頁 vs 商品頁)| **false-success rate**(nominal=true 但 verified=false)應 →0 |
| **stagnation** | #1 + 守 abstain | 動了等於沒動的鈕 / 真不可能任務 | budget 內**跳出並 abstain**,不燒到 BUDGET_EXCEEDED |
| **synonym** | #3 感知 | task 講 "Sign in",元素 label 是 "Log in" | 找不找得到 |

**防 overfit(鐵律)**:診斷集**只當 before/after 探針,絕不當 autoexp 的 evolve target**
(evolve target 仍是 live dev-39)。這結構性杜絕 teaching-to-the-test。另把 ~1/3 task 留 **sealed**,
最後跑一次報。擾動規則寫死成客觀類別(rename / reassign-id / hide-in-menu),不針對特定弱點挑。

**可行性**:M(12-20 個極小 HTML + state_check spec;deterministic、跑 k 次便宜)。
**完全不碰 live-80 的 cost headline。**

---

### 🥇 Tier 1 —— 策略適應三件套(主 target、保護成本)

> 這三個是**一個包**:#1 偵測卡住 → #3 丟 filter 看清現況 → #2 用「歧義 vs 不存在」選策略。少一個鏈就斷。

| # | 項目 | 成本 | 可行性 | 動到的檔 | 驗證(獨立 ground truth) |
|---|---|---|---|---|---|
| **1** | **stagnation 偵測 → 策略升級 prompt**:`gate()` 追蹤最近 N 個 `(action,target)`,連 3 次相同 → 不執行,改注入「approach 失敗了,退一步重新感知**整頁**,考慮不同路徑(控制項可能移位/藏 menu/要 scroll)」(browser-use `views.py:157-248` escalating nudge + Agent-E `detect_llm_loops.py:6-46`)| **cost-positive**(打斷會燒 budget 的空轉)| **S**,~30 LOC in `gate()`。**風險:可能 bleed 進 abstain(iter3 教訓)** | `agentic_executor.py`(`:262-271`)、`skill.py` | diagnostic **stagnation slice** + abstain-correctness count before/after **不准跌** |
| **2** | **暴露 locator-tier 結果給 LLM**:`ground` 回 `("ambiguous", n)` vs `("absent")` 而非 `None`;executor 映成不同 NOT_FOUND 訊息(歧義→disambiguate;不存在→wide observe)| **零** | **S**,資訊本來就在 `locate`(`cdp.py:269-273`),只是被丟掉 | `cdp.py`(`ground:372`、`locate:254`)、`agentic_executor.py`(`:327-329,358-360`)| 構造「同名 3 個」與「完全沒中」fixture,斷言 LLM 收到字串不同 |
| **3** | **失敗時 wide / unfiltered observe**:連 2 次 observe-miss 後自動用**不帶 target filter** 的感知(`_SCAN_JS` 已支援 empty target → 回全部 capped 40,`cdp.py:62`),讓 LLM 看到**當下真實 UI**(Agent-E 全樹精神,但保留我們的 cap 控成本)| **僅失敗時 +tokens 且有 cap**;正常路徑零增 | **M**,需在 executor 控觸發條件 + cap 防濫用 | `agentic_executor.py`(`observe:278`)、`skill.py` | diagnostic **selector-perturbation slice** 的 pass^k ↑ + dev-39 成本守住 |

---

### 🥈 Tier 2 —— Trustability(修 amazon bug + 抬 eval verified)

> **必須拆兩半,因為 anti-gaming。**

| # | 項目 | 打哪 | 成本 | 可行性 | 驗證 |
|---|---|---|---|---|---|
| **4a**(eval-legit)| **stricter verify 教條**:discriminating verify(對的頁真、來源頁假,agent-browser `authentication.md:143-144`)+ 兩訊號 AND(`url_contains` AND `text`)+ **結構性禁 loose**(禁止 verify 一個 pre-action snapshot 就已出現的 token)。Agent **自己**挑更嚴的 verify,**不餵答案** | eval verified-rate | 零 | **M**,prompt 規則 + executor 在 `verify_tool`(`:392`)記 pre-action token 做結構檢查 | diagnostic **decoy slice** false-success →0;dev/holdout verified before/after。**禁用 state_check 自我一致驗**(它是判官)|
| **4b**(production-only)| **caller criterion 進 finish gate**:production 下使用者給了 criterion(如「url contains light」),gate **直接跑它取代** LLM 自選 loose verify。`main.py` 已有 `_parse_criterion` / `_make_verify_hook`,把它接進 `finish` gate(`:428-437`)| production 正確性(你踩到的 amazon)| 零 | **S**,但**只走 production path,絕不進 eval gate**(否則=教到考題)| 重跑 amazon「light」task,**trace** finish 在 url 無 "light" 時被 REJECT |

> **誠實校準**:4b 修的是你 demo 踩到的 bug,但**不會動 eval 分數**(eval 為防作弊,agent 本來就拿不到 judge criterion)。
> 抬 eval verified 的是 **4a**。兩者別混。

---

### 🥉 Tier 3 —— 量測(證明 Tier 1/2 有效,服務性)

| # | 項目 | 成本 | 可行性 / guardrail | 驗證 |
|---|---|---|---|---|
| **5** | **pass^k = 外層 wrapper**:跑現有 harness k 次(diagnostic 用 k=5;live dev k=3),aggregate 多份結果檔算 **per-task pass^k + mean±bootstrap CI**(benchmark `generate_plots.py:163-174` 可照抄 ~10 行)。**harness 一行不改** | eval 成本 ×k(可接受)| **High,遵守「eval untouched」** —— judge 不動,只外部多跑再聚合 | 已知 deterministic task → pass^k=1;已知 flaky → 顯 variance,驗證量測本身沒壞 |
| **6** | **per-category accuracy + cost Pareto 報表**(benchmark `:299`)| 零 | **S**,純報表 | non-blocking;對 grader 易讀 |
| **7**(選配,guardrail 張力)| impossible/excluded runtime flag(benchmark `judge.py:120-134`)| 零 | **碰判定 → 暫緩**,或只做「事後人工排除 + 記錄理由」| 若做,記錄每個 exclude 的證據防 gaming |

---

### ❌ 砍掉 / 降級(附理由)

- **independent LLM-judge 當第二道 gate**(stagehand/browser-use `judge.py`)—— **砍**。
  (a) **加 per-finish 成本** → 違背 cost headline;(b) 把 LLM 塞進成功判定 →
  **違背明定的「成功永遠由 deterministic state_check 判,never LLM」**。最多當 eval 的 advisory score,**不進 gate**。
- **per-action change signal 擴到 fill/navigate + attribute**(Agent-E)—— **降級**。有用,但 #1+#3 已覆蓋大部分卡住偵測。
- **selector cache / self-heal**(stagehand)—— **降級**。我們每動作重 ground,**無 stale-ref 失敗模式** → 它對我們**主要省成本**而非 self-correct;deadline 下次要。
- **forced-done schema swap、sealed 加密、interleave、subprocess adapter** —— 低優先,非機制。

---

## 7. 統一驗證方法學(全部獨立 ground truth,反自我一致)

| 閘 | 驗什麼 | 怎麼驗(獨立) |
|---|---|---|
| **G1 perturbation pass^k** | 策略適應(#1+#3)| diagnostic **selector-perturbation slice**:擾動是**我們控制的 ground truth**,非 agent 自報。before/after 量 perturbed 版 recovery rate |
| **G2 成本硬閘** | 守 5.2× | unperturbed **dev-39** 的 Σnano before/after 必須在噪音內。任何 Tier-1 改動把成本推出噪音 → **退回** |
| **G3 abstain 回歸閘** | iter3 教訓 | `expect_abstain` 任務的 abstain-correctness count **不准跌**(#1 最可能在此出事)|
| **G4 amazon RCA replay** | #4b | 用原 criterion 在 production 重跑,**trace** finish 在 url 無 "light" 時被 REJECT |
| **G5 pass^k 自驗** | 量測工具本身 | 已知 deterministic → pass^k=1;已知 flaky → 顯 variance |

**鐵則(CLAUDE.md)**:#4a 的 verified 改善**不能**用 state_check 驗(它就是判官);
用 diagnostic perturbation/decoy slice 的獨立 metric + 人工 trace 個案。
**Never** 用「跟 production 同一條公式」當驗證 —— 兩者都錯時會一起 pass。

---

## 8. 排程 + 切線(deadline-aware)

```
Day 1 上午: #0 建診斷集 + 跑現狀 baseline   ‖ 並行寫 #2 / #4a / #4b 的 code
Day 1 下午: #1 + #3(策略三件套核心,配 G3 abstain 守門)→ 用 #0 的尺讀 before/after
Day 1 晚:   #5 pass^k wrapper 在 #0 受控集跑(乾淨)+ live dev-39 跑 G2 成本守門
Day 2 上午: live-80 headline 複跑(apples-to-apples)+ #6 報表
Day 2:      writeup
```

**切線(時間不夠由下往上砍)**:先砍 #7 → #6 → #3。
**底線必守:#0 + #1 + #2 + #4a** —— 這是「能在 writeup 主張 self-correct + trustability 改善且**可獨立驗證**」的最小集合,全部 cost-neutral。

---

## 9. Guardrails —— 不可碰 / 不可退化的東西

1. **deterministic verify gate 不可退化成 LLM judge。** 成功永遠由 `verify.py`(state_check)在 live page
   獨立判定,never LLM 自報。這是 moat,5 個 OSS 全部沒有。
2. **eval judge READ-ONLY / 不 gaming。** harness + state_check 評分方式不改;pass^k 是**外層多跑再聚合**;
   診斷集**不當 evolve target**;4b 的 caller criterion **絕不進 eval gate**(只 production)。
3. **成本是 constraint。** 每個 Tier-1/2 項目必須 cost-neutral 或 cost-positive;G2 是硬閘。
4. **abstain 正確性不可退化**(G3)。#1 的 stagnation 邏輯最易 bleed 進 abstain(iter3 曾 54→51 被 revert)。
5. **surgical changes。** 只動 `agentic_executor.py` / `skill.py` / `cdp.py` + 新增診斷集檔 + pass^k wrapper script。
   前端、harness、verify.py、原 plan-executor **不動**。
6. **誠實 disclosure。** writeup 要寫:(a) 5 OSS 無真 pass^k,我加是**比 reference 更嚴的 upgrade**,
   不可 imply 抄來;(b) 受控診斷集 ≠ 真實,**補充**不取代 live-80(live=external validity,診斷=internal);
   (c) 4b 修 production 不動 eval 分數。

---

## 10. 你該回報什麼(給 orchestrator 的 hand-back 格式)

每完成一項,回報:改了哪些檔(file:line)、跑了哪個驗證閘(G1-G5)、**真實數字 before/after**(非「應該會」)、
是否有 regression(尤其 G2 成本 / G3 abstain)。任何閘沒過 → 停下走 eng-debug RCA,別硬推。

> 引用 CLAUDE.md:**「NEVER claim 'passes' without tracing actual code with concrete examples.」**
> 報數字,不報 vibes。

---
---

# Part II —— 執行操作附錄(2026-06-28,對實際 code 核對)

> 以執行者視角補上 Part I 缺的「how to actually run / build / 改哪裡會炸到誰」。**衝突以本 Part 為準。**

## 11. 對 Part I 的更正(先讀,會改變你的工作量)

| Part I 說法 | 實際 code | 影響 |
|---|---|---|
| 「pass^k 是 confessed gap,要建 wrapper」 | **已存在**:`harness.py:42` `K_SIDE_EFFECT=3`、`run_eval` 對 `task_type=="side_effect"` 的 task 重跑 k=3(`:274-279`)、`scoring.pass_hat_k`(`summarize:312`)| #5 **大幅縮小**:不是建,是 **(a) 讓 perturbation/decoy 也吃 pass^k**(它們是 action/retrieval,目前不重跑)+ **(b) 加 full-set bootstrap CI**(目前沒有)|
| 「建一個新的診斷 eval set」 | **機制已備**:`loader.py:100-103` 支援 `inline_html → data:URL`;`EvalTask` 已有 `purpose`、`split`、`expect_abstain`、`abstain_reason`、`regression_anchor` 欄位;`tasks.yaml` 已有 inline + 練習站 task;DAY3_BATCH 已有 `synonym_label_signin_vs_login` | #0 變成「**擴充 `tasks.yaml`**」:NET 新增約 8-12 個 task(主要是 selector-perturbation 的 contrast-pair),decoy/synonym/abstain 的 `purpose` 類別部分已在 |
| 「4b 要新接 criterion 接線」 | **接線已存在**:`main.py:169 _parse_criterion`(已含「criterion 不可弱化成意外通過的 check」防呆)、`:196 _make_verify_hook`、`:280-283` 在 caller 給 criterion 時 wire `verify_hook` | 4b = 把**已驗證的** `parsed_criterion` **再 thread 進 finish gate**(目前它只到 post-run verify_hook)。**就是 amazon RCA 的修法** |
| (未提)| **metrics 名稱**:TSR / TCR / **CuP-gap**(silent_failure_gap)/ pass^k | 你的 before/after 要報這四個,**CuP-gap 就是 trustability 數字**(nominal=true 但 verified=false 的比率,越低越好)|

## 12. Repo map(你會碰的檔)

```
_wt/ba-llm-loop/
├─ backend/app/agent/
│   ├─ agentic_executor.py   # ★ LLM-in-loop 主體(gate/observe/click/verify_tool/finish)
│   ├─ agentic/skill.py      # ★ SKILL system prompt + TOOL_BUDGET=25
│   ├─ agentic/cdp.py        # ★ perceive(_SCAN_JS)/ground(7-tier locate)/snapshot
│   ├─ verify.py             #   agent 的 verify TOOL 後端(_goal_satisfied + detect_block)
│   └─ executor.py           #   原 plan-then-execute(不要動)
├─ backend/app/verify/state.py  #   eval JUDGE 的 state_check(獨立判官,不要動評分邏輯)
├─ backend/app/main.py       # ★ /agent/run;_parse_criterion / _make_verify_hook(4b)
├─ backend/tests/            #   97 個 offline 測試(必須維持綠)
├─ eval/
│   ├─ harness.py            #   _run_once / run_eval / summarize(TSR/TCR/CuP/pass^k)
│   ├─ run_live_tier.py      #   live 站 on-demand runner → eval/REPORT.md
│   ├─ loader.py             # ★ EvalTask schema + inline_html(#0 在這擴充 tasks.yaml）
│   ├─ scoring.py            #   mean_se / tcr / silent_failure_gap / pass_hat_k
│   └─ eval_set/
│        ├─ tasks.yaml       # ★ sandbox/inline 集(診斷 task 加這裡)
│        └─ live_real_world.yaml  # live 80-set headline(不要改)
└─ scripts/run-eval.ps1      #   PowerShell 包好的 eval 跑法
```

## 13. 怎麼跑(指令,已對 docstring 核對)

> 你在 Windows PowerShell。bash 形式取自 `harness.py:13` / `run_live_tier.py:7` 的 docstring;PowerShell 形式照翻。

**offline 綠燈閘(必過,無網路、無 Copilot,97 tests)**
```powershell
$env:PYTHONPATH="backend"; pytest -m "not live"
```

**診斷 / sandbox eval(跑 `tasks.yaml`,算 TSR/TCR/CuP/pass^k;這是你 before/after 的主尺)**
```powershell
$env:AGENT_MODE="agentic"; $env:GH_TOKEN=(gh auth token); $env:PYTHONPATH="backend"
python -m eval.harness            # 全集;--limit N 快測;--k 3 設 pass^k 次數
# 印出:agent TSR=… TCR=… CuP-gap=… pass^k=… Copilot calls=…
```

**live tier(真實站,on-demand,寫 eval/REPORT.md + eval/AUDIT.md)**
```powershell
$env:AGENT_MODE="agentic"; $env:GH_TOKEN=(gh auth token); $env:PYTHONPATH="backend"
python -m eval.run_live_tier          # dev+holdout+day3
python -m eval.run_live_tier --sealed # 一次性 sealed,單獨計分,別洩進 keep loop
```
> `AGENT_MODE=agentic` 對兩個 runner 都生效(`harness._run_once:175` 讀它,`run_live_tier` 走同一條 `_run_once`)。
> 不設 `AGENT_MODE` 會跑回原 plan-executor —— 量錯對象。

## 14. Metrics glossary(報數字用)

| 名稱 | 定義 | code | 方向 |
|---|---|---|---|
| **TSR** | task success rate = mean(verified),**獨立 state_check 判**,非自報 | `scoring.mean_se` | ↑ |
| **TCR** | completion rate = mean(nominal),agent 自己宣稱完成 | `scoring.tcr` | ↑ |
| **CuP-gap** | **silent-failure 率**:nominal=true 但 verified=false | `scoring.silent_failure_gap` | **↓(trustability)** |
| **pass^k** | side_effect task 在**全部 k 次**都過的比率 | `scoring.pass_hat_k` | ↑(可信度)|
| **Copilot calls** | 成本 proxy(requests-per-task)+ `tokens.total_nano_aiu`/1e11=USD | `_CountingGateway.calls` | ↓(cost)|

**Tier-2 的成敗看 CuP-gap 下降;Tier-1 策略適應看 perturbation task 的 TSR/pass^k 上升;成本守門看 Copilot calls 不升。**

## 15. 兩套 verify vocab —— 別搞混(重要陷阱)

- **agent 的 verify TOOL**(`agentic_executor.py:77 _Verify`,後端 `verify._goal_satisfied`):
  `url_contains` / `text_visible` / `selector_visible`。← 4a 你叫 agent「兩訊號 AND」是用**這套**。
- **eval JUDGE 的 state_check**(`app/verify/state.py`,= `tasks.yaml` 的 `assert`):
  `url_contains` / `text_contains` / `h1_equals` / `selector_text_equals{css,value}` / `iframe_text_equals{frame,css,value}`。
  **沒有 `selector_visible`/`text_visible`。** ← #0 你寫 `assert` 用**這套**。

兩者是不同模組、不同 primitive。4b 把 production criterion 接進 gate 時,criterion 走的是 **state_check 那套**
(因為 `_make_verify_hook` 用 `state_check`)。

## 16. 診斷 task 的真實 schema + worked examples(照抄改)

`tasks.yaml` 每筆欄位(來自 `loader.py:26-58`):
`id, instruction, (start_url | inline_html), domain, task_type{action|retrieval|side_effect},
difficulty{single|multi_same_domain|multi_cross_domain}, split{dev|holdout|sealed}, purpose,
key_nodes[primitive…], assert{primitive}, expect_abstain, abstain_reason{blocked|impossible}, regression_anchor`。

**selector-perturbation contrast-pair**(驗 #1+#2+#3 —— control 能過、perturbed 是否還能 recover):
```yaml
  - id: perturb_search_control
    instruction: "Find the search box, type 'toy', then submit the search."
    inline_html: |
      <input type="search" aria-label="Search query"/>
      <button id="b" aria-label="Search">Search</button>
      <div id="r" style="display:none">toy results</div>
      <script>b.onclick=()=>{r.style.display='block';location.hash='#searched'}</script>
    domain: search
    task_type: action
    difficulty: single
    split: dev
    purpose: selector_perturb_control
    assert: { url_contains: "#searched" }

  - id: perturb_search_renamed         # 同頁但鈕改名 → tier-1 role_name "Search" 失效
    instruction: "Find the search box, type 'toy', then submit the search."
    inline_html: |
      <input type="search" aria-label="Search query"/>
      <button id="b" aria-label="Go">🔍</button>     # 沒有 "Search" 這個 name 了
      <div id="r" style="display:none">toy results</div>
      <script>b.onclick=()=>{r.style.display='block';location.hash='#searched'}</script>
    domain: search
    task_type: action
    difficulty: single
    split: dev
    purpose: selector_perturb_renamed
    assert: { url_contains: "#searched" }
```

**decoy / wrong-page**(驗 #4a —— body 提到 'light' 但 assert 要求真的打開商品,直接複刻 amazon bug):
```yaml
  - id: decoy_results_not_product
    instruction: "Open the product page for the item whose title contains 'light'."
    inline_html: |
      <h1>Search results</h1>
      <p>Showing: A Light in the Attic, Bright Lights, ...</p>   # 純文字提到 light(decoy)
      <a href="#product-light" id="p">A Light in the Attic</a>
      <script>p.onclick=()=>{location.hash='#product-light'}</script>
    domain: ecommerce
    task_type: action
    difficulty: single
    split: dev
    purpose: intent_drift_decoy
    assert: { url_contains: "#product-light" }     # 停在 results 頁 = 不過
```

> 已存在可參考的同類:`synonym_label_signin_vs_login`(DAY3_BATCH)。**擾動規則寫死成客觀類別**
> (rename label / reassign id / hide-in-menu),不要針對特定弱點挑,避免「挑對自己有利的 task」之嫌。
> sealed 變體記得 `split: sealed`,且只在最後 `--sealed` 跑一次。

## 17. 各 TODO 的 blast radius(改哪裡、會炸到誰、配哪個測試)

| TODO | 改的點 | 連帶會炸 / 要注意 | 既有測試(改完要綠 + 可仿照新增)|
|---|---|---|---|
| **#1 stagnation** | `agentic_executor.py:262-271 gate()`;state 加 `state["history"]`(`:142`)| gate() 在 tool handler 內、**可能跨 thread** —— 與既有 `state["tools"]+=1` 同模式,GIL-safe。**升級訊息要 SOFT**(只 nudge,不 force-finish),否則 bleed 進 abstain(iter3 54→51 教訓)| `test_loop_mock.py`, `test_abstain_reason.py`(守 G3)|
| **#2 tier 訊號** | `cdp.py:372 ground` 回 `(loc, reason)` reason∈{ok,ambiguous,absent};`locate:269-273` 已知 ambiguity | **2 個 caller**:click(`executor:323`)、fill(`:354`),都做 `if loc is None` → **都要改**;NOT_FOUND 訊息(`:328-329,358-360`)分流 | `test_ambiguity_grounding.py`, `test_navigate_resolve.py` |
| **#3 wide observe** | `executor:278 observe`,連 2 次 miss 後改呼 `perceive(page,"")`(`cdp.py:62,162` empty target 回全部 capped 40)| 觸發計數放 `state`;**保留 main-frame-first + child-frame fallback**(`cdp.py:175-194`),別破 iframe task | `test_perceive.py`, `test_view_scope.py` |
| **#4a 嚴 verify** | **便宜部分**:`skill.py` prompt(discriminating + 兩訊號 AND)。**較貴部分**:禁 pre-action token 需在 `verify_tool:392` 前**新存一份 pre-action page text**(`snapshot:338` 只有 url+dom_hash,**沒有 text**)| prompt 部分近乎零風險先做;結構性 pre-token check 是新 plumbing → **可延後** | `test_predict_then_verify.py`, `test_step_diagnostics.py` |
| **#4b criterion 進 gate** | `main.py:294` 多傳 `parsed_criterion` 給 `AgenticExecutor`;`executor.py:428-437 finish` 在現有 gate **外加** `state_check(page, gate_criterion)` | **production-only**:`harness.py` 建 executor 時**不傳** gate_criterion → eval 不受影響、anti-gaming 保住 | **`test_production_verify_wiring.py`**(直接 extend 它)|
| **#5 pass^k 擴 + CI** | **【已定案:(c) 外層 k-loop】** 寫一支獨立 wrapper script(例 `eval/passk_diag.py`),對診斷 task 跑現有 `_run_once` k 次(diag k=5)、自己 aggregate per-task pass^k + mean±bootstrap CI(照抄 benchmark `generate_plots.py:163-174`)。**`harness.py` 與 native side_effect pass^k 一行不動** | 守「eval untouched」:judge / 重跑條件 / 計分公式都不碰,只外部多跑再聚合。輸出獨立寫一份 `eval/PASSK_DIAG.md`,別污染 headline REPORT | `test_eval_scoring.py`(bootstrap_ci 的 unit test)|

## 18. Baseline 擷取協定(動手前先做 —— 這是誠實的 before)

**不要 hardcode 舊數字**(AUTORESEARCH 的 iter4 best≈54 可當 sanity anchor,但會 stale)。動任何 code 前先跑、存檔:
```powershell
$env:AGENT_MODE="agentic"; $env:GH_TOKEN=(gh auth token); $env:PYTHONPATH="backend"
python -m eval.harness        # 記下 TSR/TCR/CuP-gap/pass^k/Copilot calls
python -m eval.run_live_tier  # 記下 live verified 比數 + eval/REPORT.md
```
每個 TODO 完成後重跑同指令,**並排 before/after**。任一驗證閘(§7 G1-G5)沒過 → 停,走 eng-debug RCA,別硬推。

## 19. Open decisions(已給 recommended default,別卡住)

1. **stagnation N** = 3 個相同 `(action,target)`(Agent-E `detect_llm_loops.py`)。target 要正規化(lower/trim)。
2. **wide-observe 觸發** = 連 2 次 observe-miss(與 `skill.py:60` 既有「2 observes 放棄」co-locate,順手把「放棄」改成「先 wide observe 再決定」)。
3. **#4a 結構性 pre-token check** = **DEFER**;先做 prompt 層 discriminating + 兩訊號 AND(近乎零成本零風險)。
4. **pass^k 覆蓋** = **【已定案】外層 k-loop**(獨立 wrapper script,守 eval-untouched);`harness.py` 與 native side_effect pass^k **一行不動**。不採用碰 harness 的 opt-in flag 做法。
5. **診斷集大小** = 12-20(NET 新增約 8-12,因 decoy/synonym/abstain purpose 部分已在);1/3 留 `split: sealed`。

## 20. 一句話交接

**先跑 §18 baseline → 擴 `tasks.yaml` 做 §16 contrast-pair(#0)→ 寫 §17 的 #2/#4b(零成本低風險先拿穩)
→ 再做 #1/#3(策略核心,配 G3 守 abstain)→ 用 §13 指令量 before/after,報 §14 的四個數字。**
pass^k 與 criterion 接線**都已存在**,你是在**延伸**,不是從零造 —— 別重造輪子。
