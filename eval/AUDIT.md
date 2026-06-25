# Audit Trace — per-task evidence (human-readable, not a metric)

Generated **2026-06-25 12:10 UTC** by `eval.audit` from the executor's event stream (no LLM, no network in the audit itself).

- **attribution_coverage = 1.000** (fraction of FAILING tasks deterministically tagged plan-time/ground-time — 1.0 by construction)
- flag tally: ABSTAIN=1, HONEST_FAIL=3, OK=15, SILENT_FAILURE=1
- Tokens are reported for cost transparency only — never minimized (abstaining more to lower tokens would game the metric and is not done).

---

### live_wikipedia_helium_retrieval — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=4 calls=2 | tokens(out=929 in=24754 reason=870 nano_aiu=4932400000)

plan:
- 1. navigate https://www.wikipedia.org
- 2. fill "Search Wikipedia" = "Helium"
- 3. click "Search"
- 4. click "Helium"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | fill | Search Wikipedia | Helium | RESOLVED | CHANGED | — |
| 3 | click | Search | — | RESOLVED | CHANGED | — |
| 4 | click | Helium | — | AMBIGUOUS_L2 | CHANGED | — |

---

### live_pydocs_json_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=1 | tokens(out=3904 in=164832 reason=3473 nano_aiu=14462400000)

plan:
- 1. navigate https://docs.python.org/3/
- 2. click "Library reference"
- 3. click "modules"
- 4. click "json"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Library reference | — | RESOLVED | CHANGED | — |
| 3 | click | modules | — | RESOLVED | CHANGED | — |
| 4 | click | json | — | RESOLVED | CHANGED | — |

---

### live_google_search_steam — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=6 calls=18 | tokens(out=1925 in=223622 reason=1729 nano_aiu=13749800000)

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
| 5 | click | Google Search | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REGROUND,REGROUND |

---

### live_wikipedia_signin_synonym — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=10 | tokens(out=2442 in=124256 reason=2315 nano_aiu=10880600000)

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
`nominal=True` `verified=True` `asked=False` | steps=3 calls=1 | tokens(out=217 in=12489 reason=169 nano_aiu=798150000)

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
`nominal=True` `verified=True` `asked=False` | steps=3 calls=4 | tokens(out=712 in=50139 reason=645 nano_aiu=5653950000)

plan:
- 1. navigate https://www.wikipedia.org/
- 2. fill "Search Wikipedia" = "Argon"
- 3. click "Argon"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | fill | Search Wikipedia | Argon | RESOLVED | CHANGED | — |
| 3 | click | Argon | — | AMBIGUOUS_L2 | CHANGED | REGROUND |

---

### live_internet_lazyload — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=961 in=12483 reason=944 nano_aiu=1912650000)

plan:
- 1. navigate https://the-internet.herokuapp.com/dynamic_loading/2
- 2. click "Start"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Start | — | RESOLVED | CHANGED | — |

---

### live_internet_modal — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=2887 in=12486 reason=2869 nano_aiu=4802400000)

plan:
- 1. navigate this page

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | — | — |

---

### live_internet_iframe — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=4 calls=18 | tokens(out=4167 in=223766 reason=3967 nano_aiu=17148800000)

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
`nominal=True` `verified=True` `asked=False` | steps=2 calls=4 | tokens(out=2247 in=49672 reason=2195 nano_aiu=5190100000)

plan:
- 1. navigate https://example.com
- 2. click "More information..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | More information... | — | AMBIGUOUS_L2 | CHANGED | REGROUND |

---

### live_hackernews_newest_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=201 in=12488 reason=168 nano_aiu=773900000)

plan:
- 1. navigate https://news.ycombinator.com/
- 2. click "new"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | new | — | RESOLVED | CHANGED | — |

---

### live_gnu_licenses_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=4 calls=2 | tokens(out=410 in=24982 reason=350 nano_aiu=1561300000)

plan:
- 1. navigate https://www.gnu.org
- 2. click "Licenses"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REGROUND,REGROUND,REPLAN |
| 3 | click | Licenses | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REGROUND,REGROUND |

---

### internet_form_auth_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=203 in=12484 reason=171 nano_aiu=775900000)

plan:
- 1. navigate https://the-internet.herokuapp.com
- 2. click "Form Authentication"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Form Authentication | — | RESOLVED | CHANGED | — |

---

### internet_login_page_reached — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=444 in=12300 reason=411 nano_aiu=1091400000)

plan:
- 1. navigate https://the-internet.herokuapp.com/
- 2. click "Form Authentication"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Form Authentication | — | RESOLVED | CHANGED | — |

---

### books_open_light_in_attic — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=1589 in=12307 reason=1552 nano_aiu=2810650000)

plan:
- 1. navigate https://books.toscrape.com/
- 2. click "A Light in the ..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | A Light in the ... | — | RESOLVED | CHANGED | — |

---

### books_open_travel_category — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=406 in=12298 reason=374 nano_aiu=1033900000)

plan:
- 1. navigate https://books.toscrape.com
- 2. click "Travel"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Travel | — | RESOLVED | CHANGED | — |

---

### books_price_visible — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=1913 in=26161 reason=1834 nano_aiu=4110550000)

plan:
- 1. navigate https://books.toscrape.com/
- 2. click "A Light in the ..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | A Light in the ... | — | RESOLVED | CHANGED | — |

---

### quotes_open_einstein_author — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=2052 in=42523 reason=1949 nano_aiu=5299150000)

plan:
- 1. navigate http://quotes.toscrape.com/author/Albert-Einstein

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### quotes_open_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=531 in=12484 reason=506 nano_aiu=1267900000)

plan:
- 1. navigate https://quotes.toscrape.com/login

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### synonym_label_signin_vs_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=2 | tokens(out=251 in=24878 reason=226 nano_aiu=1296800000)

plan:
- 1. navigate data:text/html,%3Cbutton%20id%3D%22b%22%3ELog%20in%3C/button%3E%0A%3Cdiv%20id%3D%22out%22%3Enone%3C/div%3E%0A%3Cscript%3Edocument.getElementById%28%27b%27%29.onclick%3Dfunction%28%29%7Bdocument.getElementById%28%27out%27%29.textContent%3D%27SUBMITTED%27%7D%3B%3C/script%3E%0A
- 2. click "Sign In"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Sign In | — | AMBIGUOUS_L2 | CHANGED | — |

---
