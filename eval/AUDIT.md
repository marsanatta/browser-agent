# Audit Trace — per-task evidence (human-readable, not a metric)

Generated **2026-06-25 03:44 UTC** by `eval.audit` from the executor's event stream (no LLM, no network in the audit itself).

- **attribution_coverage = 1.000** (fraction of FAILING tasks deterministically tagged plan-time/ground-time — 1.0 by construction)
- flag tally: BLOCKED=1, HONEST_FAIL=2, OK=13, SILENT_FAILURE=1
- Tokens are reported for cost transparency only — never minimized (abstaining more to lower tokens would game the metric and is not done).

---

### live_wikipedia_helium_retrieval — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=1 | tokens(out=728 in=12485 reason=680 nano_aiu=1563650000)

plan:
- 1. navigate https://www.wikipedia.org
- 2. fill "Search Wikipedia" = "Helium"
- 3. press "Search Wikipedia" = "Enter"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | fill | Search Wikipedia | Helium | RESOLVED | CHANGED | — |
| 3 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |

---

### live_pydocs_json_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=5 calls=1 | tokens(out=4637 in=185992 reason=4132 nano_aiu=18317500000)

plan:
- 1. navigate https://docs.python.org/3/
- 2. click "Library reference"
- 3. click "modules"
- 4. click "j"
- 5. click "json"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Library reference | — | RESOLVED | CHANGED | — |
| 3 | click | modules | — | RESOLVED | CHANGED | — |
| 4 | click | j | — | RESOLVED | CHANGED | — |
| 5 | click | json | — | RESOLVED | CHANGED | — |

---

### live_google_search_steam — AUDIT: BLOCKED — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=3 calls=1 | tokens(out=186 in=12289 reason=141 nano_aiu=701650000)

plan:
- 1. navigate https://www.google.com
- 2. fill "Search" = "steam"
- 3. press "Search" = "Enter"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | fill | Search | steam | RESOLVED | CHANGED | — |
| 3 | press | Search | Enter | RESOLVED | NO_CHANGE | ASK_USER |

---

### live_wikipedia_signin_synonym — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=397 in=12292 reason=364 nano_aiu=1018900000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Main_Page
- 2. click "Log in"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Log in | — | RESOLVED | CHANGED | — |

---

### live_wikipedia_search_submit — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=1 | tokens(out=564 in=12297 reason=516 nano_aiu=1270650000)

plan:
- 1. navigate https://www.wikipedia.org
- 2. fill "Search Wikipedia" = "Oxygen"
- 3. press "Search Wikipedia" = "Enter"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | fill | Search Wikipedia | Oxygen | RESOLVED | CHANGED | — |
| 3 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |

---

### live_wikipedia_autocomplete — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=4 | tokens(out=819 in=49644 reason=753 nano_aiu=3041100000)

plan:
- 1. navigate https://en.wikipedia.org
- 2. fill "Search Wikipedia" = "Argon"
- 3. click "Argon"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | fill | Search Wikipedia | Argon | RESOLVED | CHANGED | — |
| 3 | click | Argon | — | AMBIGUOUS_L2 | CHANGED | REGROUND |

---

### live_internet_lazyload — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=2 calls=1 | tokens(out=668 in=12489 reason=651 nano_aiu=1474650000)

plan:
- 1. navigate https://the-internet.herokuapp.com/dynamic_loading/2
- 2. click "Start"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Start | — | RESOLVED | CHANGED | — |

---

### live_internet_modal — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=2790 in=12478 reason=2769 nano_aiu=4654900000)

plan:
- 1. navigate <provided page URL>

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | — | — |

---

### live_internet_iframe — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=4 calls=18 | tokens(out=3084 in=223586 reason=2884 nano_aiu=12829700000)

plan:
- 1. navigate https://the-internet.herokuapp.com/iframe
- 2. click "Rich Text Area"
- 3. fill "Rich Text Area" = "browser agent was here"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REGROUND,REGROUND,REPLAN |
| 3 | click | Rich Text Editor | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REGROUND,REGROUND |

---

### internet_form_auth_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=185 in=12478 reason=152 nano_aiu=747400000)

plan:
- 1. navigate https://the-internet.herokuapp.com/
- 2. click "Form Authentication"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Form Authentication | — | RESOLVED | CHANGED | — |

---

### internet_login_page_reached — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=548 in=12292 reason=516 nano_aiu=1245400000)

plan:
- 1. navigate https://the-internet.herokuapp.com
- 2. click "Form Authentication"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Form Authentication | — | RESOLVED | CHANGED | — |

---

### books_open_light_in_attic — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=6 | tokens(out=13459 in=73534 reason=13387 nano_aiu=22674400000)

plan:
- 1. navigate https://books.toscrape.com
- 2. click "A Light in the Attic"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | A Light in the Attic | — | AMBIGUOUS_L2 | CHANGED | REGROUND,REGROUND |

---

### books_open_travel_category — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=808 in=12290 reason=776 nano_aiu=1634900000)

plan:
- 1. navigate http://books.toscrape.com
- 2. click "Travel"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Travel | — | RESOLVED | CHANGED | — |

---

### books_price_visible — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=1589 in=12484 reason=1552 nano_aiu=2854900000)

plan:
- 1. navigate https://books.toscrape.com/
- 2. click "A Light in the ..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | A Light in the ... | — | RESOLVED | CHANGED | — |

---

### quotes_open_einstein_author — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=547 in=12474 reason=516 nano_aiu=1289400000)

plan:
- 1. navigate https://quotes.toscrape.com/author/Albert-Einstein

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### quotes_open_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=541 in=12478 reason=516 nano_aiu=1281400000)

plan:
- 1. navigate https://quotes.toscrape.com/login

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### synonym_label_signin_vs_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=2 | tokens(out=315 in=24860 reason=290 nano_aiu=1388300000)

plan:
- 1. navigate data:text/html,%3Cbutton%20id%3D%22b%22%3ELog%20in%3C/button%3E%0A%3Cdiv%20id%3D%22out%22%3Enone%3C/div%3E%0A%3Cscript%3Edocument.getElementById%28%27b%27%29.onclick%3Dfunction%28%29%7Bdocument.getElementById%28%27out%27%29.textContent%3D%27SUBMITTED%27%7D%3B%3C/script%3E%0A
- 2. click "Sign In"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Sign In | — | AMBIGUOUS_L2 | CHANGED | — |

---
