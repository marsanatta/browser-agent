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
  verdict: {
    runError: "Run error: {{error}}",
    connectionLost: "connection lost — your access session may have expired",
    running: "Running…",
    nominal: "Nominal",
    verified: "Verified",
    complete: "complete",
    incomplete: "incomplete",
    silentFlag: "⚠ silent failure (nominal ≠ verified)",
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
  verdict: {
    runError: "執行錯誤：{{error}}",
    connectionLost: "連線中斷——你的存取工作階段可能已過期",
    running: "執行中…",
    nominal: "宣稱結果",
    verified: "驗證結果",
    complete: "已完成",
    incomplete: "未完成",
    silentFlag: "⚠ 隱性失敗（宣稱 ≠ 驗證）",
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
