# Audit Trace — per-task evidence (human-readable, not a metric)

Generated **2026-06-26 15:28 UTC** by `eval.audit` from the executor's event stream (no LLM, no network in the audit itself).

- **attribution_coverage = 1.000** (fraction of FAILING tasks deterministically tagged plan-time/ground-time — 1.0 by construction)
- flag tally: BLOCKED=1, HONEST_FAIL=7, OK=20, SILENT_FAILURE=1
- Tokens are reported for cost transparency only — never minimized (abstaining more to lower tokens would game the metric and is not done).

---

### live_wikipedia_helium_retrieval — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=1 | tokens(out=59 in=19338 reason=0 nano_aiu=7064825000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Main_Page
- 2. fill "Search Wikipedia" = "Helium"
- 3. press "Search Wikipedia" = "Enter"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | fill | Search Wikipedia | Helium | RESOLVED | CHANGED | — |
| 3 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |

---

### live_pydocs_json_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=2 calls=4 | tokens(out=1012 in=67044 reason=622 nano_aiu=16675370000)

plan:
- 1. navigate https://docs.python.org/3/
- 2. click "The Python Standard Library"
- 3. click "json — JSON encoder and decoder"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | The Python Standard Library | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_google_search_steam — AUDIT: BLOCKED — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=3 calls=1 | tokens(out=46 in=19029 reason=0 nano_aiu=1360600000)

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
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=19 in=19050 reason=0 nano_aiu=1306225000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Main_Page
- 2. click "Log in"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Log in | — | RESOLVED | CHANGED | — |

---

### live_wikipedia_search_submit — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=1 | tokens(out=61 in=19059 reason=0 nano_aiu=1416850000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Main_Page
- 2. fill "Search Wikipedia" = "Oxygen"
- 3. press "Search Wikipedia" = "Enter"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | fill | Search Wikipedia | Oxygen | RESOLVED | CHANGED | — |
| 3 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |

---

### live_wikipedia_autocomplete — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=2 | tokens(out=277 in=32856 reason=195 nano_aiu=1712185000)

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
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=18 in=19061 reason=0 nano_aiu=1310600000)

plan:
- 1. navigate https://the-internet.herokuapp.com/dynamic_loading/2
- 2. click "Start"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Start | — | RESOLVED | CHANGED | — |

---

### live_internet_modal — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=2 calls=1 | tokens(out=52 in=19048 reason=0 nano_aiu=1387475000)

plan:
- 1. navigate https://the-internet.herokuapp.com/entry_ad
- 2. click "click here"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | click here | — | RESOLVED | CHANGED | REGROUND |

---

### live_internet_iframe — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=2 calls=4 | tokens(out=370 in=66806 reason=243 nano_aiu=16313920000)

plan:
- 1. navigate https://the-internet.herokuapp.com/iframe
- 2. fill "Rich Text Area" = "browser agent was here"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | fill | Rich Text Area | browser agent was here | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_example_more_info_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=2 calls=4 | tokens(out=388 in=66488 reason=274 nano_aiu=16151170000)

plan:
- 1. navigate https://example.com/
- 2. click "More information..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | More information... | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_hackernews_newest_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=17 in=19339 reason=0 nano_aiu=6960450000)

plan:
- 1. navigate https://news.ycombinator.com/
- 2. click "new"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | new | — | RESOLVED | CHANGED | — |

---

### live_gnu_licenses_nav — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=20 in=19337 reason=0 nano_aiu=6966700000)

plan:
- 1. navigate https://www.gnu.org/
- 2. click "Licenses"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | — | — |

---

### live_osm_login_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=19 in=19323 reason=0 nano_aiu=6955450000)

plan:
- 1. navigate https://www.openstreetmap.org/
- 2. click "Log In"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Log In | — | RESOLVED | CHANGED | — |

---

### live_lobsters_comments_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=19 in=19318 reason=0 nano_aiu=6952325000)

plan:
- 1. navigate https://lobste.rs/
- 2. click "Comments"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Comments | — | RESOLVED | CHANGED | — |

---

### live_mdn_blog_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=19 in=19317 reason=0 nano_aiu=6951700000)

plan:
- 1. navigate https://developer.mozilla.org/
- 2. click "Blog"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Blog | — | RESOLVED | CHANGED | — |

---

### live_archive_login_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=2 calls=2 | tokens(out=135 in=38642 reason=26 nano_aiu=14150900000)

plan:
- 1. navigate https://archive.org/
- 2. click "Log In"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Log In | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_govuk_help_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=52 in=19326 reason=25 nano_aiu=7039825000)

plan:
- 1. navigate https://www.gov.uk/
- 2. click "Help"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Help | — | RESOLVED | CHANGED | — |

---

### live_arxiv_help_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=34 in=19317 reason=0 nano_aiu=6989200000)

plan:
- 1. navigate https://info.arxiv.org/help/index.html

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_yahoofinance_aapl_quote — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=37 in=19329 reason=0 nano_aiu=7004200000)

plan:
- 1. navigate https://finance.yahoo.com/quote/AAPL

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_openlibrary_login_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=19 in=19327 reason=0 nano_aiu=6957950000)

plan:
- 1. navigate https://openlibrary.org/
- 2. click "Log In"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Log In | — | RESOLVED | CHANGED | — |

---

### live_stackoverflow_questions_nav — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=2 | tokens(out=177 in=38709 reason=35 nano_aiu=14297775000)

plan:
- 1. navigate https://stackoverflow.com/
- 2. click "Questions"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | NOT_FOUND | NO_CHANGE | REPLAN |

---

### internet_form_auth_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=97 in=19328 reason=28 nano_aiu=7153575000)

plan:
- 1. navigate https://the-internet.herokuapp.com/
- 2. click "Form Authentication"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Form Authentication | — | RESOLVED | CHANGED | — |

---

### internet_login_page_reached — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=34 in=19043 reason=0 nano_aiu=1339350000)

plan:
- 1. navigate https://the-internet.herokuapp.com/login

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### books_open_light_in_attic — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=23 in=19044 reason=0 nano_aiu=1312475000)

plan:
- 1. navigate https://books.toscrape.com
- 2. click "A Light in the ..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | A Light in the ... | — | RESOLVED | CHANGED | — |

---

### books_open_travel_category — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=46 in=19035 reason=0 nano_aiu=1364350000)

plan:
- 1. navigate https://books.toscrape.com/catalogue/category/books/travel_2/index.html

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### books_price_visible — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=23 in=19046 reason=0 nano_aiu=1313725000)

plan:
- 1. navigate https://books.toscrape.com
- 2. click "A Light in the ..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | A Light in the ... | — | RESOLVED | CHANGED | — |

---

### quotes_open_einstein_author — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=2 calls=4 | tokens(out=374 in=66254 reason=257 nano_aiu=9140720000)

plan:
- 1. navigate https://quotes.toscrape.com
- 2. click "(about)"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | (about) | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### quotes_open_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=32 in=19038 reason=0 nano_aiu=1331225000)

plan:
- 1. navigate https://quotes.toscrape.com/login

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### synonym_label_signin_vs_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=19 in=19194 reason=0 nano_aiu=1396225000)

plan:
- 1. navigate data:text/html,%3Cbutton%20id%3D%22b%22%3ELog%20in%3C/button%3E%0A%3Cdiv%20id%3D%22out%22%3Enone%3C/div%3E%0A%3Cscript%3Edocument.getElementById%28%27b%27%29.onclick%3Dfunction%28%29%7Bdocument.getElementById%28%27out%27%29.textContent%3D%27SUBMITTED%27%7D%3B%3C/script%3E%0A
- 2. click "Log in"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Log in | — | RESOLVED | CHANGED | — |

---
