# Audit Trace — per-task evidence (human-readable, not a metric)

Generated **2026-06-25 12:46 UTC** by `eval.audit` from the executor's event stream (no LLM, no network in the audit itself).

- **attribution_coverage = 1.000** (fraction of FAILING tasks deterministically tagged plan-time/ground-time — 1.0 by construction)
- flag tally: BLOCKED=1, HONEST_FAIL=5, OK=23
- Tokens are reported for cost transparency only — never minimized (abstaining more to lower tokens would game the metric and is not done).

---

### live_wikipedia_helium_retrieval — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=2748 in=12485 reason=2723 nano_aiu=4593650000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Helium

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_pydocs_json_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=1 | tokens(out=2566 in=78916 reason=2227 nano_aiu=11021200000)

plan:
- 1. navigate https://docs.python.org/3/
- 2. click "Library reference"
- 3. click "json — JSON encoder and decoder"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Library reference | — | RESOLVED | CHANGED | — |
| 3 | click | json — JSON encoder and decoder | — | RESOLVED | CHANGED | — |

---

### live_google_search_steam — AUDIT: BLOCKED — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=3 calls=1 | tokens(out=266 in=12297 reason=221 nano_aiu=823650000)

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
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=1860 in=94423 reason=1500 nano_aiu=7042150000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Main_Page
- 2. click "Log in"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Log in | — | RESOLVED | CHANGED | — |

---

### live_wikipedia_search_submit — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=1 | tokens(out=316 in=12501 reason=268 nano_aiu=949650000)

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
`nominal=True` `verified=True` `asked=False` | steps=3 calls=2 | tokens(out=2632 in=129512 reason=2338 nano_aiu=10406000000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Main_Page
- 2. fill "Search Wikipedia" = "Argon"
- 3. click "Argon"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | fill | Search Wikipedia | Argon | RESOLVED | CHANGED | — |
| 3 | click | Argon | — | AMBIGUOUS_L2 | CHANGED | — |

---

### live_internet_lazyload — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=1509 in=25564 reason=1450 nano_aiu=3240100000)

plan:
- 1. navigate https://the-internet.herokuapp.com/dynamic_loading/2
- 2. click "Start"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Start | — | RESOLVED | CHANGED | — |

---

### live_internet_modal — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=1426 in=12488 reason=1405 nano_aiu=2611400000)

plan:
- 1. navigate <provided page URL>

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | — | — |

---

### live_internet_iframe — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=4 calls=18 | tokens(out=3650 in=223712 reason=3450 nano_aiu=13710200000)

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

### live_example_more_info_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=2 | tokens(out=937 in=24876 reason=900 nano_aiu=2325300000)

plan:
- 1. navigate https://example.com
- 2. click "More information..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | More information... | — | AMBIGUOUS_L2 | CHANGED | — |

---

### live_hackernews_newest_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=199 in=12488 reason=166 nano_aiu=770900000)

plan:
- 1. navigate https://news.ycombinator.com/
- 2. click "new"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | new | — | RESOLVED | CHANGED | — |

---

### live_gnu_licenses_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=4 calls=2 | tokens(out=380 in=24990 reason=320 nano_aiu=1518300000)

plan:
- 1. navigate https://www.gnu.org
- 2. click "Licenses"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REGROUND,REGROUND,REPLAN |
| 3 | click | Licenses | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REGROUND,REGROUND |

---

### live_osm_login_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=175 in=12485 reason=143 nano_aiu=734150000)

plan:
- 1. navigate https://www.openstreetmap.org
- 2. click "Log In"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Log In | — | RESOLVED | CHANGED | — |

---

### live_lobsters_comments_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=181 in=12481 reason=152 nano_aiu=742150000)

plan:
- 1. navigate https://lobste.rs
- 2. click "Comments"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Comments | — | RESOLVED | CHANGED | — |

---

### live_mdn_blog_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=2 | tokens(out=251 in=24919 reason=214 nano_aiu=1307050000)

plan:
- 1. navigate https://developer.mozilla.org/
- 2. click "Blog"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Blog | — | AMBIGUOUS_L2 | CHANGED | — |

---

### live_archive_login_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=4 calls=2 | tokens(out=515 in=24976 reason=457 nano_aiu=1717300000)

plan:
- 1. navigate https://archive.org
- 2. click "Log In"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REGROUND,REGROUND,REPLAN |
| 3 | click | Log In | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REGROUND,REGROUND |

---

### live_govuk_help_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=286 in=12485 reason=257 nano_aiu=900650000)

plan:
- 1. navigate https://www.gov.uk
- 2. click "Help"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Help | — | RESOLVED | CHANGED | — |

---

### live_arxiv_help_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=217 in=12487 reason=187 nano_aiu=797650000)

plan:
- 1. navigate https://arxiv.org/
- 2. click "Help"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Help | — | RESOLVED | CHANGED | — |

---

### live_yahoofinance_aapl_quote — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=484 in=12484 reason=459 nano_aiu=1197400000)

plan:
- 1. navigate https://finance.yahoo.com/quote/AAPL

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_openlibrary_login_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=215 in=12485 reason=185 nano_aiu=794150000)

plan:
- 1. navigate https://openlibrary.org
- 2. click "Log In"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Log In | — | RESOLVED | CHANGED | — |

---

### live_stackoverflow_questions_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=4 calls=2 | tokens(out=474 in=24984 reason=418 nano_aiu=1657800000)

plan:
- 1. navigate https://stackoverflow.com
- 2. click "Questions"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REGROUND,REGROUND,REPLAN |
| 3 | click | Questions | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REGROUND,REGROUND |

---

### internet_form_auth_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=216 in=12476 reason=184 nano_aiu=793400000)

plan:
- 1. navigate https://the-internet.herokuapp.com
- 2. click "Form Authentication"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Form Authentication | — | RESOLVED | CHANGED | — |

---

### internet_login_page_reached — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=533 in=12300 reason=500 nano_aiu=1224900000)

plan:
- 1. navigate https://the-internet.herokuapp.com/
- 2. click "Form Authentication"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Form Authentication | — | RESOLVED | CHANGED | — |

---

### books_open_light_in_attic — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=998 in=57694 reason=794 nano_aiu=4515700000)

plan:
- 1. navigate https://books.toscrape.com/
- 2. click "A Light in the ..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | A Light in the ... | — | RESOLVED | CHANGED | — |

---

### books_open_travel_category — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=549 in=12298 reason=516 nano_aiu=1248400000)

plan:
- 1. navigate http://books.toscrape.com/
- 2. click "Travel"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Travel | — | RESOLVED | CHANGED | — |

---

### books_price_visible — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=1071 in=12308 reason=1034 nano_aiu=2033900000)

plan:
- 1. navigate https://books.toscrape.com/
- 2. click "A Light in the ..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | A Light in the ... | — | RESOLVED | CHANGED | — |

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
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=246 in=12298 reason=214 nano_aiu=793900000)

plan:
- 1. navigate https://quotes.toscrape.com
- 2. click "Login"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Login | — | RESOLVED | CHANGED | — |

---

### synonym_label_signin_vs_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=2 | tokens(out=325 in=24876 reason=300 nano_aiu=1407300000)

plan:
- 1. navigate data:text/html,%3Cbutton%20id%3D%22b%22%3ELog%20in%3C/button%3E%0A%3Cdiv%20id%3D%22out%22%3Enone%3C/div%3E%0A%3Cscript%3Edocument.getElementById%28%27b%27%29.onclick%3Dfunction%28%29%7Bdocument.getElementById%28%27out%27%29.textContent%3D%27SUBMITTED%27%7D%3B%3C/script%3E%0A
- 2. click "Sign In"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Sign In | — | AMBIGUOUS_L2 | CHANGED | — |

---
