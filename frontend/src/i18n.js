import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const STORAGE_KEY = "ba_lang";

const en = {
  brand: "browser-agent",
  a11y: { moreInfo: "More info" },
  header: {
    disclosure:
      "Supported: bot-wall-free public sites (search, browse, forms, extraction). Login / MFA / CAPTCHA / anti-bot walls are routed to “unsupported” — never evaded.",
  },
  lang: { en: "EN", zhHant: "繁體中文", groupLabel: "Language", switchTo: "Switch language to {{lang}}" },
  runbar: {
    task: "Task",
    taskPlaceholder: "Describe a task in natural language",
    startUrl: "Start URL (optional)",
    run: "Run",
    stop: "Stop",
  },
  gallery: {
    title: "Example cases",
    hint: "click a card to fill the form and run it",
    groupGood: "Works well",
    groupLimitation: "Known limits",
    badge: {
      verified: "verified",
      abstain: "abstain",
      blocked: "blocked",
    },
    items: {
      "pydocs-json": { label: "docs.python.org: Std Library → json module", why: "Two-hop documentation navigation: open The Python Standard Library, then the json module page — verified on the URL." },
      "wiki-autocomplete": { label: "Wikipedia: pick 'Argon' from autocomplete", why: "Type 'Argon' and choose the autocomplete suggestion to open the article — a real typeahead-widget interaction." },
      "hn-show-ask": { label: "Hacker News: Show HN → Ask HN", why: "Two-hop section navigation: open Show HN, then from there reach Ask HN — verified on the URL." },
      "govuk-driving": { label: "GOV.UK: Driving & transport → Driving licences", why: "Two-hop browse: open the 'Driving and transport' section, then its 'Driving licences' subtopic — verified on the URL." },
      "amazon-headless": { label: "Search Amazon for a product", why: "Amazon shows an anti-bot 'Continue shopping' interstitial on headless; the agent clicks through it, searches, and opens the first product." },
      "internet-modal": { label: "Read the modal window title", why: "A modal pops up on load; the agent reads its title and the independent check confirms it." },
      "internet-iframe": { label: "Type inside an iframe rich-text editor", why: "The editor lives inside an iframe; the agent's grounding cannot act inside it, so it honestly gives up (asks the user) — a real capability gap, not a silent failure." },
      "github-login": { label: "Sign in to GitHub", why: "Login wall — the agent holds no credentials, sees the form, and gives up. Route, don't evade." },
      "recaptcha": { label: "Submit the reCAPTCHA demo form", why: "Submit is gated by a CAPTCHA the agent will not solve, so it abstains honestly." },
      "g2-datadome": { label: "Open a g2.com page", why: "DataDome anti-bot returns HTTP 403 with zero perceivable elements — the agent fails closed." },
      "cloudflare-wall": { label: "Open a Cloudflare-protected page", why: "Cloudflare's 'security verification' managed challenge gates the page; the agent recognizes the block and abstains honestly (route, don't evade)." },
      "sa-balance-sheet": { label: "stockanalysis.com: Apple → Balance Sheet", why: "Multi-step financial drill-down: open Apple's page, then its Balance Sheet under Financials — verified on the URL." },
      "cmc-ranking-detail": { label: "companiesmarketcap: ranking → Apple detail", why: "Find Apple in the market-cap ranking and open its detail page — verified on the URL." },
      "cmc-compare": { label: "companiesmarketcap: compare NVIDIA vs Apple, open the larger", why: "Read both market caps, decide which is larger, then act by opening the larger one's page (NVIDIA at run time)." },
      "screenerin-screen": { label: "screener.in: screens directory → Magic Formula", why: "Open the screens directory and the named 'Magic Formula' screen — verified on the URL." },
      "screenerin-company-metric": { label: "screener.in: search TCS → read ROCE", why: "Search for Tata Consultancy Services, open its company page, and read its ROCE — verified on the URL." },
      "screenerin-loginwall": { label: "screener.in: sort a screen (needs login)", why: "Sorting the screen requires an account; the agent hits the login wall and abstains honestly. Route, don't evade." },
    },
  },
  models: {
    heading: "Engine & models (advanced)",
    engine: "Engine",
    engineAgentic: "Agentic (LLM-in-loop, recommended)",
    engineScript: "Script-orchestration (deprecated)",
    plan: "Planner",
    exec: "Execution",
    replanner: "Replanner",
    model: "model",
    thinking: "thinking",
    maxReplans: "Replan max attempts",
  },
  verdict: {
    runError: "Run error: {{error}}",
    connectionLost: "connection lost — your access session may have expired",
    running: "Running…",
    stopped: "Stopped by you",
    state: {
      verified: "Goal-verified ✓",
      unverified: "Actions completed — not goal-verified",
      silent: "Failed — claimed success, goal check disagreed",
      failed: "Failed",
    },
    nominal: "Nominal",
    verified: "Verified",
    goalCheck: "Goal check",
    notProvided: "not provided (self-report only)",
    complete: "complete",
    incomplete: "incomplete",
    silentFlag: "⚠ silent failure (nominal ≠ verified)",
  },
  criterion: {
    heading: "Success criterion (optional) — independent goal check on the final page",
    check: "check",
    none: "— none (self-report only) —",
    urlContains: "URL contains (case-insensitive)",
    h1Equals: "Page H1 equals (case-insensitive)",
    selectorTextEquals: "Element text equals (case-insensitive)",
    css: "CSS selector",
    cssPlaceholder: "e.g. #cart .count",
    value: "expected value",
    valuePlaceholder: "expected text / substring",
  },
  tokens: {
    label: "tokens",
    out: "out",
    in: "in",
    reasoning: "reasoning",
    aiu: "AIU",
    na: "tokens: n/a",
    title: "Real LLM token usage for this run (cost transparency)",
  },
  timeline: {
    label: "Step timeline",
    empty: "No steps yet. Submit a task to watch the agent work.",
    detailHint:
      "Select a step to inspect its diagnostics — locator tier, recovery chain, annotated screenshot, and verdict.",
  },
  status: { pending: "pending", running: "running", ok: "passed", failed: "failed" },
  plan: {
    heading: "Plan · {{n}} steps",
    replanned: "replanned",
  },
  planHistory: {
    heading: "Plan history",
    initial: "Plan v{{v}} · initial",
    replan: "Replan v{{v}} · after {{n}} failure(s)",
    why: "Why replanned (failures sent to the planner):",
    rawOutput: "Raw planner output (verbatim LLM response)",
  },
  phase: {
    planning: "Planning the task…",
    launching: "Opening browser…",
    running: "Working…",
  },
  live: {
    working: "Agent is working",
  },
  notices: { askUser: "Ask user: {{question}}" },
  gate: {
    disclosure: "This instance is access-controlled. Enter the access token your operator gave you.",
    token: "Access token",
    tokenPlaceholder: "access token",
    unlock: "Unlock",
    unlocking: "Unlocking…",
    noTokenConfigured: "Server has no access token configured.",
    invalidToken: "Invalid access token.",
    unreachable: "Could not reach the server.",
    sessionExpired: "Your access session expired. Re-enter the access token to continue.",
  },
  step: {
    statusLabel: "status",
    locatorLabel: "locator",
    locatorValue: "tier {{tier}} · {{strategy}}",
    failureLabel: "failure",
    screenshots: "Annotated screenshots",
    recoveryChain: "Recovery / retry chain",
    attempt: "attempt {{n}}",
    tried: "tried",
    via: "via",
    detail: {
      no_element_matched: "no element matched",
      no_state_change: "element found, but the action changed nothing",
      not_visible_or_enabled: "element not visible / enabled",
      wrong_page: "landed on the wrong page",
      stale_or_timeout: "stale element / timed out",
      blocked: "blocked by a bot-wall",
    },
    toolCalls: "Tool calls",
    fallbackCaption: "step screenshot",
  },
  hint: {
    task: "What you want the agent to do, written as a plain sentence — for example “find the price of this book and add it to the cart.”",
    startUrl: "An optional web address to open first. Leave it blank and the agent decides where to start.",
    run: "Start the agent on your task. It works step by step and you watch each action appear below in real time.",
    stop: "Halt the agent immediately. It stops where it is and no further actions are taken.",
    unsupported:
      "Sites behind a login, two-factor, or CAPTCHA wall are reported as “unsupported” instead of being worked around — the agent never tries to defeat those protections.",
    nominal: "What the agent itself claims it did — its own report, before any independent check.",
    verified:
      "Whether the task actually succeeded when we re-checked the page — not just what the agent claimed.",
    goalCheck:
      "No success criterion was given, so the page was not independently checked — this result is the agent's own report only, not a verified pass.",
    criterion:
      "Optional. Give a checkable success condition (a URL substring, the page H1, or a specific element's text) and the result is independently re-checked on the final page. Leave it blank and the run is reported as self-report only, never as “verified.”",
    silent: "The agent reported success, but the page check disagreed — a hidden failure.",
    tokens:
      "How much work the language model did for this run. More tokens means more reading and writing, which costs more.",
    aiu: "AI Usage — a single normalized number that rolls all token costs into one figure so runs are easy to compare.",
    locatorTier:
      "How the agent found the on-screen element. A higher tier means it had to fall back to less reliable methods to locate it.",
    failureCategory:
      "The kind of problem the step hit — for example the element wasn’t found, the page changed, or an action timed out.",
    recovery:
      "Each time a step failed, what the agent tried next to recover — its retry attempts shown in order.",
    screenshot:
      "A picture of the page at this step, with a box drawn around the element the agent acted on.",
    askUser: "A point where the agent paused to ask you a question because it couldn’t decide on its own.",
  },
};

const zhHant = {
  brand: "browser-agent",
  a11y: { moreInfo: "更多說明" },
  header: {
    disclosure:
      "支援：沒有 bot 防護牆的公開網站（搜尋、瀏覽、填表、擷取資料）。需要登入／MFA／CAPTCHA／反 bot 防護牆的網站會被歸類為「不支援」——絕不繞過。",
  },
  lang: { en: "EN", zhHant: "繁體中文", groupLabel: "語言", switchTo: "切換語言至 {{lang}}" },
  runbar: {
    task: "任務",
    taskPlaceholder: "用自然語言描述一個任務",
    startUrl: "起始網址（選填）",
    run: "執行",
    stop: "停止",
  },
  gallery: {
    title: "Example 範例",
    hint: "點一張卡片即可填入表單並執行",
    groupGood: "運作良好",
    groupLimitation: "已知限制",
    badge: {
      verified: "已驗證",
      abstain: "誠實放棄",
      blocked: "被封鎖",
    },
    items: {
      "pydocs-json": { label: "docs.python.org：Std Library → json 模組", why: "兩段式文件導覽：先開 The Python Standard Library，再開 json 模組頁 — 用 URL 驗證。" },
      "wiki-autocomplete": { label: "Wikipedia：從 autocomplete 選 'Argon'", why: "輸入 'Argon' 後從 autocomplete 建議中選取開啟條目 — 真實的 typeahead widget 互動。" },
      "hn-show-ask": { label: "Hacker News：Show HN → Ask HN", why: "兩段式分區導覽：先開 Show HN，再從那裡到 Ask HN — 用 URL 驗證。" },
      "govuk-driving": { label: "GOV.UK：Driving & transport → Driving licences", why: "兩段式瀏覽：先開『Driving and transport』分區，再進其『Driving licences』子題 — 用 URL 驗證。" },
      "amazon-headless": { label: "在 Amazon 搜尋商品", why: "Amazon 在 headless 下會跳反爬的『Continue shopping』interstitial；agent 會點過去、搜尋、開啟第一個商品。" },
      "internet-modal": { label: "讀取 modal 視窗標題", why: "頁面載入時跳出 modal；agent 讀出它的標題，獨立檢查確認無誤。" },
      "internet-iframe": { label: "在 iframe 內的 rich-text editor 打字", why: "編輯器在 iframe 裡；agent 的 grounding 無法進到 iframe 內操作，所以誠實放棄（詢問使用者）— 這是真正的能力缺口，不是 silent failure。" },
      "github-login": { label: "登入 GitHub", why: "登入牆 — agent 沒有任何憑證，看到表單就誠實放棄。Route，不繞過。" },
      "recaptcha": { label: "提交 reCAPTCHA demo 表單", why: "Submit 被 CAPTCHA 擋住，agent 不會去解，因此誠實放棄。" },
      "g2-datadome": { label: "開啟 g2.com 頁面", why: "DataDome 反爬回 HTTP 403、零個可感知元素 — agent fail closed。" },
      "cloudflare-wall": { label: "開啟 Cloudflare 防護的頁面", why: "Cloudflare 的『security verification』managed challenge 擋住頁面；agent 辨識出被擋後誠實放棄（route，不繞過）。" },
      "sa-balance-sheet": { label: "stockanalysis.com：Apple → Balance Sheet", why: "多步財報下鑽：先開 Apple 個股頁，再進 Financials 下的 Balance Sheet — 用 URL 驗證。" },
      "cmc-ranking-detail": { label: "companiesmarketcap：排行榜 → Apple 詳情", why: "在市值排行榜找到 Apple 並開啟其詳情頁 — 用 URL 驗證。" },
      "cmc-compare": { label: "companiesmarketcap：比較 NVIDIA vs Apple，開較大者", why: "讀取兩者市值、判斷誰較大，再行動開啟較大者的頁面（執行當下是 NVIDIA）。" },
      "screenerin-screen": { label: "screener.in：screens 目錄 → Magic Formula", why: "開啟 screens 目錄並進入指定的『Magic Formula』screen — 用 URL 驗證。" },
      "screenerin-company-metric": { label: "screener.in：搜尋 TCS → 讀 ROCE", why: "搜尋 Tata Consultancy Services、開啟其個股頁並讀取 ROCE — 用 URL 驗證。" },
      "screenerin-loginwall": { label: "screener.in：對 screen 排序（需登入）", why: "排序需要帳號；agent 撞上登入牆後誠實放棄。Route，不繞過。" },
    },
  },
  models: {
    heading: "Engine 與 models（進階）",
    engine: "Engine（引擎）",
    engineAgentic: "Agentic（LLM-in-loop，推薦）",
    engineScript: "Script-orchestration（已棄用）",
    plan: "Planner（規劃）",
    exec: "Execution（執行）",
    replanner: "Replanner（重新規劃）",
    model: "model（模型）",
    thinking: "thinking（思考強度）",
    maxReplans: "Replan 最大次數",
  },
  verdict: {
    runError: "執行錯誤：{{error}}",
    connectionLost: "連線中斷——你的存取工作階段可能已過期",
    running: "執行中…",
    stopped: "已由你停止",
    state: {
      verified: "目標已驗證 ✓",
      unverified: "動作已完成——未經目標驗證",
      silent: "失敗——宣稱成功，但目標檢查不一致",
      failed: "失敗",
    },
    nominal: "宣稱結果",
    verified: "驗證結果",
    goalCheck: "目標檢查",
    notProvided: "未提供（僅 agent 自我回報）",
    complete: "已完成",
    incomplete: "未完成",
    silentFlag: "⚠ 隱性失敗（宣稱 ≠ 驗證）",
  },
  criterion: {
    heading: "成功條件（選填）——在最終頁面上做獨立的目標檢查",
    check: "檢查方式",
    none: "— 無（僅自我回報）—",
    urlContains: "URL 包含（不分大小寫）",
    h1Equals: "頁面 H1 等於（不分大小寫）",
    selectorTextEquals: "元素文字等於（不分大小寫）",
    css: "CSS selector",
    cssPlaceholder: "例如 #cart .count",
    value: "預期值",
    valuePlaceholder: "預期文字／子字串",
  },
  tokens: {
    label: "tokens",
    out: "輸出",
    in: "輸入",
    reasoning: "推理",
    aiu: "AIU",
    na: "tokens：無資料",
    title: "本次執行實際的 LLM token 用量（成本透明化）",
  },
  timeline: {
    label: "步驟時間軸",
    empty: "尚無步驟。送出一個任務即可即時觀看 agent 運作。",
    detailHint: "選擇一個步驟以檢視其診斷資訊——定位層級、復原鏈、標註截圖與判定結果。",
  },
  status: { pending: "等待中", running: "執行中", ok: "通過", failed: "失敗" },
  plan: {
    heading: "Plan · {{n}} 個步驟",
    replanned: "已重新規劃",
  },
  planHistory: {
    heading: "Plan 歷史",
    initial: "Plan v{{v}} · 初次規劃",
    replan: "Replan v{{v}} · 在 {{n}} 次失敗後",
    why: "為何重新規劃（送給 planner 的失敗紀錄）：",
    rawOutput: "Planner 原始輸出（LLM 逐字回應）",
  },
  phase: {
    planning: "規劃任務中…",
    launching: "開啟 browser 中…",
    running: "執行中…",
  },
  live: {
    working: "agent 正在執行",
  },
  notices: { askUser: "詢問使用者：{{question}}" },
  gate: {
    disclosure: "此服務受存取權限控管。請輸入操作人員提供給你的存取 token。",
    token: "存取 token",
    tokenPlaceholder: "存取 token",
    unlock: "解鎖",
    unlocking: "解鎖中…",
    noTokenConfigured: "伺服器尚未設定存取 token。",
    invalidToken: "存取 token 無效。",
    unreachable: "無法連線到伺服器。",
    sessionExpired: "你的存取工作階段已過期。請重新輸入存取 token 以繼續。",
  },
  step: {
    statusLabel: "狀態",
    locatorLabel: "定位",
    locatorValue: "層級 {{tier}} · {{strategy}}",
    failureLabel: "失敗",
    screenshots: "標註截圖",
    recoveryChain: "復原／重試鏈",
    attempt: "第 {{n}} 次嘗試",
    tried: "嘗試",
    via: "透過",
    detail: {
      no_element_matched: "找不到符合的元素",
      no_state_change: "找到元素，但動作沒有造成任何改變",
      not_visible_or_enabled: "元素不可見／無法操作",
      wrong_page: "停在錯誤的頁面",
      stale_or_timeout: "元素已失效／逾時",
      blocked: "被 bot 防護牆阻擋",
    },
    toolCalls: "工具呼叫",
    fallbackCaption: "步驟截圖",
  },
  hint: {
    task: "你希望 agent 完成的事，用一句白話寫出來——例如「找出這本書的價格並加入購物車」。",
    startUrl: "選填，agent 會先開啟的網址。留空的話，就由 agent 自行決定從哪裡開始。",
    run: "讓 agent 開始執行你的任務。它會一步一步進行，每個動作都會即時顯示在下方供你觀看。",
    stop: "立即中止 agent。它會停在當下，不再執行任何後續動作。",
    unsupported:
      "需要登入、兩步驟驗證或 CAPTCHA 的網站，會被回報為「不支援」，而不是想辦法繞過——agent 絕不會試圖破解這些防護。",
    nominal: "agent 自己宣稱完成了什麼——它的自我回報，尚未經過任何獨立檢查。",
    verified: "重新檢查網頁後，任務是否真的完成——而非只是 agent 自己宣稱完成。",
    goalCheck:
      "因為沒有提供成功條件，所以沒有對頁面做獨立檢查——這個結果只是 agent 的自我回報，並非已驗證的成功。",
    criterion:
      "選填。給一個可檢查的成功條件（URL 子字串、頁面 H1，或某個元素的文字），結果就會在最終頁面上被獨立重新檢查。留空的話，本次執行只會以「自我回報」呈現，絕不會標示為「已驗證」。",
    silent: "agent 回報成功，但網頁檢查結果不一致——這是一個被掩蓋的失敗。",
    tokens:
      "本次執行中語言模型做了多少工作。token 越多代表讀寫越多，成本也越高。",
    aiu: "AI 用量——把所有 token 成本整合成單一標準化數字，方便不同次執行之間互相比較。",
    locatorTier:
      "agent 如何在畫面上找到目標元素。層級越高，代表它得退而求其次、用較不可靠的方式來定位。",
    failureCategory:
      "這個步驟遇到的問題類型——例如找不到元素、網頁改變了，或動作逾時。",
    recovery: "每當步驟失敗時，agent 接著嘗試的復原動作——依序顯示的重試過程。",
    screenshot: "這個步驟當下的網頁畫面，並在 agent 操作的元素周圍框出範圍。",
    askUser: "agent 因無法自行判斷而暫停、向你提問的時間點。",
  },
};

const SUPPORTED = ["en", "zh-Hant"];
const stored = typeof localStorage !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
const initialLng = SUPPORTED.includes(stored) ? stored : "en";

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, "zh-Hant": { translation: zhHant } },
  lng: initialLng,
  fallbackLng: "en",
  supportedLngs: SUPPORTED,
  interpolation: { escapeValue: false },
});

if (typeof document !== "undefined") {
  document.documentElement.lang = initialLng;
}

i18n.on("languageChanged", (lng) => {
  if (typeof localStorage !== "undefined") localStorage.setItem(STORAGE_KEY, lng);
  if (typeof document !== "undefined") document.documentElement.lang = lng;
});

export default i18n;
