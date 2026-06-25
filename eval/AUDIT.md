# Audit Trace — per-task evidence (human-readable, not a metric)

Generated **2026-06-25 09:05 UTC** by `eval.audit` from the executor's event stream (no LLM, no network in the audit itself).

- **attribution_coverage = 1.000** (fraction of FAILING tasks deterministically tagged plan-time/ground-time — 1.0 by construction)
- flag tally: BLOCKED=1, HONEST_FAIL=2, OK=16, SILENT_FAILURE=1
- Tokens are reported for cost transparency only — never minimized (abstaining more to lower tokens would game the metric and is not done).

---

### live_wikipedia_helium_retrieval — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=2546 in=12491 reason=2521 nano_aiu=4292150000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Helium

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_pydocs_json_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=1 | tokens(out=562 in=12306 reason=516 nano_aiu=1269900000)

plan:
- 1. navigate https://docs.python.org/3/
- 2. click "Library Reference"
- 3. click "json — JSON encoder and decoder"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Library Reference | — | RESOLVED | CHANGED | — |
| 3 | click | json — JSON encoder and decoder | — | RESOLVED | CHANGED | — |

---

### live_google_search_steam — AUDIT: BLOCKED — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=6 calls=10 | tokens(out=1322 in=123462 reason=1179 nano_aiu=9002100000)

plan:
- 1. navigate https://www.google.com
- 2. fill "Search" = "steam"
- 3. click "Google Search"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | fill | Search | steam | RESOLVED | CHANGED | — |
| 3 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REGROUND,REGROUND,REPLAN |
| 4 | fill | Search | steam | RESOLVED | CHANGED | — |
| 5 | press | Search | Enter | RESOLVED | NO_CHANGE | ASK_USER |

---

### live_wikipedia_signin_synonym — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=10 | tokens(out=1984 in=124080 reason=1857 nano_aiu=7500000000)

plan:
- 1. navigate https://www.wikipedia.org
- 2. click "Log in"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REGROUND,REGROUND,REPLAN |
| 3 | click | Log in | — | RESOLVED | CHANGED | — |

---

### live_wikipedia_search_submit — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=1 | tokens(out=164 in=12483 reason=116 nano_aiu=717150000)

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
`nominal=True` `verified=True` `asked=False` | steps=3 calls=2 | tokens(out=661 in=24965 reason=610 nano_aiu=1933550000)

plan:
- 1. navigate https://en.wikipedia.org
- 2. fill "Search Wikipedia" = "Argon"
- 3. click "Argon"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | fill | Search Wikipedia | Argon | RESOLVED | CHANGED | — |
| 3 | click | Argon | — | AMBIGUOUS_L2 | CHANGED | — |

---

### live_internet_lazyload — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=440 in=12487 reason=423 nano_aiu=1132150000)

plan:
- 1. navigate https://the-internet.herokuapp.com/dynamic_loading/2
- 2. click "Start"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Start | — | RESOLVED | CHANGED | — |

---

### live_internet_modal — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=523 in=12486 reason=516 nano_aiu=1256400000)

plan:
- 1. navigate https://the-internet.herokuapp.com/entry_ad

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_internet_iframe — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=4 calls=18 | tokens(out=4692 in=223746 reason=4492 nano_aiu=15281700000)

plan:
- 1. navigate https://the-internet.herokuapp.com/iframe
- 2. click "Rich Text Area"
- 3. fill "Rich Text Area" = "browser agent was here"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REGROUND,REGROUND,REPLAN |
| 3 | click | Rich Text Area | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REGROUND,REGROUND |

---

### live_example_more_info_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=2 | tokens(out=735 in=24898 reason=698 nano_aiu=2027800000)

plan:
- 1. navigate https://example.com
- 2. click "More information..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | More information... | — | AMBIGUOUS_L2 | CHANGED | — |

---

### live_hackernews_newest_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=237 in=12486 reason=205 nano_aiu=827400000)

plan:
- 1. navigate https://news.ycombinator.com
- 2. click "new"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | new | — | RESOLVED | CHANGED | — |

---

### live_gnu_licenses_nav — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=197 in=12492 reason=167 nano_aiu=768900000)

plan:
- 1. navigate https://www.gnu.org
- 2. click "Licenses"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | — | — |

---

### internet_form_auth_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=231 in=12482 reason=198 nano_aiu=817400000)

plan:
- 1. navigate https://the-internet.herokuapp.com/
- 2. click "Form Authentication"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Form Authentication | — | RESOLVED | CHANGED | — |

---

### internet_login_page_reached — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=549 in=12300 reason=516 nano_aiu=1248900000)

plan:
- 1. navigate https://the-internet.herokuapp.com/
- 2. click "Form Authentication"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Form Authentication | — | RESOLVED | CHANGED | — |

---

### books_open_light_in_attic — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=2634 in=57775 reason=2481 nano_aiu=6874750000)

plan:
- 1. navigate https://books.toscrape.com/
- 2. click "A Light in the ..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | A Light in the ... | — | RESOLVED | CHANGED | — |

---

### books_open_travel_category — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=230 in=12298 reason=198 nano_aiu=769900000)

plan:
- 1. navigate https://books.toscrape.com
- 2. click "Travel"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Travel | — | RESOLVED | CHANGED | — |

---

### books_price_visible — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=553 in=12308 reason=516 nano_aiu=1256900000)

plan:
- 1. navigate https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### quotes_open_einstein_author — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=548 in=12300 reason=516 nano_aiu=1247400000)

plan:
- 1. navigate https://quotes.toscrape.com/author/Albert-Einstein/

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### quotes_open_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=548 in=12298 reason=516 nano_aiu=1246900000)

plan:
- 1. navigate https://quotes.toscrape.com
- 2. click "Login"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Login | — | RESOLVED | CHANGED | — |

---

### synonym_label_signin_vs_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=2 | tokens(out=300 in=24876 reason=275 nano_aiu=1369800000)

plan:
- 1. navigate data:text/html,%3Cbutton%20id%3D%22b%22%3ELog%20in%3C/button%3E%0A%3Cdiv%20id%3D%22out%22%3Enone%3C/div%3E%0A%3Cscript%3Edocument.getElementById%28%27b%27%29.onclick%3Dfunction%28%29%7Bdocument.getElementById%28%27out%27%29.textContent%3D%27SUBMITTED%27%7D%3B%3C/script%3E%0A
- 2. click "Sign In"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Sign In | — | AMBIGUOUS_L2 | CHANGED | — |

---
