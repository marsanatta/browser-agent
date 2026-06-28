# Audit Trace — per-task evidence (human-readable, not a metric)

Generated **2026-06-28 04:14 UTC** by `eval.audit` from the executor's event stream (no LLM, no network in the audit itself).

- **attribution_coverage = 1.000** (fraction of FAILING tasks deterministically tagged plan-time/ground-time — 1.0 by construction)
- flag tally: ABSTAIN=5, BLOCKED=1, HONEST_FAIL=17, OK=30, SILENT_FAILURE=15
- Tokens are reported for cost transparency only — never minimized (abstaining more to lower tokens would game the metric and is not done).

---

### live_wikipedia_helium_retrieval — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=3 calls=2 | tokens(out=1756 in=29023 reason=1192 nano_aiu=2992895000)

plan:
- 1. fill "Search Wikipedia" = "Helium"
- 2. press "Search Wikipedia" = "Enter"
- 3. click "Helium"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Helium | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |
| 3 | click | Helium | — | AMBIGUOUS_L2 | CHANGED | — |

---

### live_pydocs_json_nav — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=5 calls=8 | tokens(out=4450 in=116558 reason=3068 nano_aiu=10742830000)

plan:
- 1. click "Library reference"
- 2. fill "Quick search" = "json"
- 3. click "search"
- 4. click "json"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Library reference | — | RESOLVED | CHANGED | — |
| 2 | fill | Quick search | json | RESOLVED | CHANGED | — |
| 3 | click | search | — | AMBIGUOUS_L2 | CHANGED | REGROUND,REGROUND,REGROUND,REPLAN |
| 4 | click | json | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_google_search_steam — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=2 calls=4 | tokens(out=2123 in=59220 reason=1319 nano_aiu=5438040000)

plan:
- 1. fill "Search" = "steam"
- 2. click "Google Search"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search | steam | RESOLVED | CHANGED | — |
| 2 | click | Google Search | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_wikipedia_signin_synonym — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=355 in=15035 reason=282 nano_aiu=1300385000)

plan:
- 1. click "Log in"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Log in | — | RESOLVED | CHANGED | — |

---

### live_wikipedia_search_submit — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=532 in=15041 reason=423 nano_aiu=1389635000)

plan:
- 1. fill "Search Wikipedia" = "Oxygen"
- 2. press "Search Wikipedia" = "Enter"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Oxygen | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |

---

### live_wikipedia_autocomplete — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=4 | tokens(out=1964 in=58858 reason=1479 nano_aiu=5313290000)

plan:
- 1. fill "Special:Search" = "Argon"
- 2. click "Argon"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Special:Search | Argon | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_internet_lazyload — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=667 in=14257 reason=492 nano_aiu=1359135000)

plan:
- 1. click "Start"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Start | — | RESOLVED | CHANGED | — |

---

### live_internet_modal — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=2 calls=2 | tokens(out=1491 in=28617 reason=1031 nano_aiu=2809645000)

plan:
- 1. navigate http://elementalselenium.com/

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | RESOLVED | CHANGED | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |

---

### live_internet_iframe — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=2 calls=3 | tokens(out=2727 in=43456 reason=1569 nano_aiu=4526030000)

plan:
- 1. click "Your content goes here."
- 2. fill "Your content goes here." = "browser agent was here"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Your content goes here. | — | RESOLVED | NO_CHANGE | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN,WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |

---

### live_example_more_info_nav — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=1 calls=2 | tokens(out=1790 in=28910 reason=1105 nano_aiu=2995770000)

plan:
- 1. click "Learn more"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Learn more | — | RESOLVED | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_hackernews_newest_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=812 in=14988 reason=583 nano_aiu=1523010000)

plan:
- 1. click "new"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | new | — | RESOLVED | CHANGED | — |

---

### live_gnu_licenses_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=False` | steps=0 calls=0 | tokens(out=0 in=0 reason=0 nano_aiu=0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|

---

### live_osm_login_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=313 in=14839 reason=231 nano_aiu=1254885000)

plan:
- 1. click "Log In"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Log In | — | RESOLVED | CHANGED | — |

---

### live_lobsters_comments_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=326 in=14902 reason=252 nano_aiu=1269260000)

plan:
- 1. click "Comments"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Comments | — | RESOLVED | CHANGED | — |

---

### live_mdn_blog_nav — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=2 | tokens(out=1428 in=31163 reason=1114 nano_aiu=3096395000)

plan:
- 1. click "Toggle navigation"
- 2. click "Blog"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Toggle navigation | — | RESOLVED | NO_CHANGE | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |

---

### live_archive_login_nav — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=3 calls=2 | tokens(out=1226 in=28587 reason=888 nano_aiu=2673395000)

plan:
- 1. navigate https://archive.org
- 2. navigate https://archive.org/

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN |

---

### live_govuk_help_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=1495 in=14777 reason=623 nano_aiu=1838135000)

plan:
- 1. navigate https://www.gov.uk/help

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_arxiv_help_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=320 in=14900 reason=248 nano_aiu=1266010000)

plan:
- 1. click "Help"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Help | — | RESOLVED | CHANGED | — |

---

### live_stackoverflow_questions_nav — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=2 calls=3 | tokens(out=2285 in=43051 reason=1531 nano_aiu=4254405000)

plan:
- 1. navigate https://stackoverflow.com/questions
- 2. click "Questions"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | NOT_FOUND | NO_CHANGE | REPLAN,REPLAN |

---

### live_internet_status_code_200 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=1494 in=14326 reason=694 nano_aiu=1781260000)

plan:
- 1. click "200"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | 200 | — | RESOLVED | CHANGED | — |

---

### live_internet_challenging_dom_intro — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=1246 in=14283 reason=572 nano_aiu=1651885000)

plan:
- 1. navigate http://the-internet.herokuapp.com/challenging_dom
- 2. click "Elemental Selenium"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Elemental Selenium | — | RESOLVED | CHANGED | — |

---

### live_books_sapiens_price — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=2 calls=4 | tokens(out=3190 in=59017 reason=1801 nano_aiu=5946165000)

plan:
- 1. click "Nonfiction"
- 2. click "Sapiens: A Brief History of Humankind"
- 3. click "Sapiens: A Brief History of Humankind"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Nonfiction | — | RESOLVED | CHANGED | — |
| 2 | click | Sapiens: A Brief History of Humankind | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_books_open_mystery_category — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=314 in=15030 reason=251 nano_aiu=1279260000)

plan:
- 1. click "Mystery"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Mystery | — | RESOLVED | CHANGED | — |

---

### live_books_sapiens_stock — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=5 | tokens(out=2595 in=73463 reason=1927 nano_aiu=6697925000)

plan:
- 1. click "Books"
- 2. click "Sapiens: A Brief History ..."
- 3. click "History"
- 4. click "Sapiens: A Brief History of Humankind"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Books | — | RESOLVED | CHANGED | — |
| 2 | click | Sapiens: A Brief History ... | — | RESOLVED | CHANGED | REGROUND,REGROUND,REPLAN |
| 3 | click | History | — | RESOLVED | CHANGED | REGROUND,REGROUND,REPLAN |
| 4 | click | Sapiens: A Brief History of Humankind | — | AMBIGUOUS_L2 | CHANGED | REGROUND |

---

### live_books_grand_design_price — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=4 | tokens(out=1416 in=58218 reason=1086 nano_aiu=4959290000)

plan:
- 1. click "Science"
- 2. navigate https://books.toscrape.com/catalogue/the-grand-design_405/index.html
- 3. navigate https://books.toscrape.com/catalogue/the-grand-design_405/index.html

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Science | — | RESOLVED | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN |
| 3 | navigate | — | — | — | CHANGED | — |

---

### live_books_dune_price — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=7 | tokens(out=5370 in=102126 reason=2565 nano_aiu=10155320000)

plan:
- 1. click "Science Fiction"
- 2. navigate ../../../dune-dune-1_151/index.html

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Science Fiction | — | RESOLVED | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN,REGROUND,REGROUND,REPLAN |

---

### live_books_page2_pagination — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=2 | tokens(out=4107 in=29325 reason=1606 nano_aiu=4206145000)

plan:
- 1. navigate https://books.toscrape.com/catalogue/page-2.html

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | NOT_FOUND | CHANGED | REPLAN |

---

### live_wikipedia_oxygen_search — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=5 calls=9 | tokens(out=5022 in=133586 reason=3045 nano_aiu=12400840000)

plan:
- 1. fill "Search Wikipedia" = "Oxygen"
- 2. press "Search Wikipedia" = "Enter"
- 3. fill "Search Wikipedia" = "Oxygen"
- 4. click "Search"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Oxygen | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |
| 3 | fill | Search Wikipedia | Oxygen | RESOLVED | CHANGED | REGROUND,REGROUND,REPLAN |
| 4 | click | Search | — | AMBIGUOUS_L2 | NO_CHANGE | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |

---

### live_wikipedia_periodic_table_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=8 calls=12 | tokens(out=5174 in=189884 reason=3683 nano_aiu=17244620000)

plan:
- 1. fill "Search Wikipedia" = "Oxygen"
- 2. press "Search Wikipedia" = "Enter"
- 3. click "Oxygen"
- 4. navigate /wiki/Oxygen
- 5. navigate /wiki/Periodic_table

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Oxygen | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |
| 3 | click | Oxygen | — | AMBIGUOUS_L2 | CHANGED | — |
| 4 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN |
| 5 | navigate | — | — | AMBIGUOUS_L2 | CHANGED | REGROUND,REGROUND,REGROUND,REGROUND,REPLAN,REGROUND,REGROUND,REPLAN |

---

### live_wikipedia_einstein_body_text — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=2 | tokens(out=1597 in=28997 reason=1192 nano_aiu=2910145000)

plan:
- 1. fill "Search Wikipedia" = "Albert Einstein"
- 2. press "Search Wikipedia" = "Enter"
- 3. click "Albert Einstein"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Albert Einstein | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |
| 3 | click | Albert Einstein | — | AMBIGUOUS_L2 | CHANGED | — |

---

### live_pydocs_tutorial_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=332 in=15023 reason=249 nano_aiu=1287385000)

plan:
- 1. click "Tutorial"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Tutorial | — | RESOLVED | CHANGED | — |

---

### live_hackernews_show_then_ask — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=503 in=14969 reason=416 nano_aiu=1366135000)

plan:
- 1. click "show"
- 2. click "ask"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | show | — | RESOLVED | CHANGED | — |
| 2 | click | ask | — | RESOLVED | CHANGED | — |

---

### live_mdn_html_input — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=2 | tokens(out=2022 in=31189 reason=1168 nano_aiu=3396645000)

plan:
- 1. click "Elements"
- 2. click "<input>"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Elements | — | RESOLVED | NO_CHANGE | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |

---

### live_mdn_css_flex — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=3843 in=77037 reason=1970 nano_aiu=7768675000)

plan:
- 1. navigate https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties
- 2. navigate /en-US/docs/Web/CSS/Reference/Properties/flex

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | RESOLVED | CHANGED | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN |

---

### live_govuk_bank_holidays — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=6 | tokens(out=3309 in=86038 reason=1997 nano_aiu=7870310000)

plan:
- 1. fill "Search GOV.UK" = "bank holidays"
- 2. click "Search"
- 3. click "Bank holidays"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search GOV.UK | bank holidays | AMBIGUOUS_L2 | NO_CHANGE | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |

---

### live_govuk_vat_rates — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=5 calls=14 | tokens(out=5946 in=200427 reason=3790 nano_aiu=17435515000)

plan:
- 1. navigate /search
- 2. click "Money and tax"
- 3. click "VAT rates explained"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | AMBIGUOUS_L2 | CHANGED | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |
| 2 | click | Money and tax | — | RESOLVED | CHANGED | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |
| 3 | click | VAT rates explained | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_govuk_min_wage — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=6 | tokens(out=4720 in=86085 reason=2089 nano_aiu=8581685000)

plan:
- 1. click "Search GOV.UK"
- 2. fill "Search GOV.UK" = "National Minimum Wage National Living Wage"
- 3. press "Search GOV.UK" = "Enter"
- 4. click "National Minimum Wage rates"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Search GOV.UK | — | AMBIGUOUS_L2 | NO_CHANGE | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |

---

### live_govuk_check_uk_visa — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=4 | tokens(out=2143 in=58234 reason=1482 nano_aiu=5324790000)

plan:
- 1. click "Visas and immigration"
- 2. click "Check if you need a UK visa"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Visas and immigration | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_govuk_driving_licences — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=7 | tokens(out=2878 in=101848 reason=2036 nano_aiu=8874570000)

plan:
- 1. navigate /browse/driving
- 2. click "Driving licences"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN,REGROUND,REGROUND,REPLAN |
| 2 | click | Driving licences | — | RESOLVED | CHANGED | — |

---

### live_wikipedia_jupiter — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=3 calls=3 | tokens(out=1904 in=44933 reason=1212 nano_aiu=4299155000)

plan:
- 1. fill "Search Wikipedia" = "Jupiter"
- 2. press "Search Wikipedia" = "Enter"
- 3. click "Jupiter"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Jupiter | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |
| 3 | click | Jupiter | — | RESOLVED | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_books_fiction_page2 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=2 | tokens(out=1003 in=28954 reason=650 nano_aiu=2607770000)

plan:
- 1. click "Fiction"
- 2. click "next"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Fiction | — | RESOLVED | CHANGED | — |
| 2 | click | next | — | RESOLVED | CHANGED | REGROUND |

---

### live_arxiv_attention_paper — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=False` | steps=4 calls=4 | tokens(out=3005 in=58506 reason=1761 nano_aiu=5789790000)

plan:
- 1. fill "Search term or terms" = "Attention Is All You Need"
- 2. fill "Search term or terms" = "Attention Is All You Need"
- 3. press "Search term or terms" = "Enter"
- 4. click "Attention Is All You Need"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search term or terms | Attention Is All You Need | RESOLVED | CHANGED | — |
| 2 | fill | Search term or terms | Attention Is All You Need | RESOLVED | CHANGED | REGROUND,REGROUND,REPLAN |
| 3 | press | Search term or terms | Enter | RESOLVED | — | STATE_WAIT |

---

### live_wikipedia_preferences_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=5 calls=7 | tokens(out=9241 in=106244 reason=4284 nano_aiu=12605570000)

plan:
- 1. navigate /wiki/Special:Preferences
- 2. click "Log in"
- 3. click "Language"
- 4. click "Español"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | RESOLVED | CHANGED | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |
| 2 | click | Log in | — | RESOLVED | NO_CHANGE | REGROUND,REGROUND,REPLAN,REGROUND,REGROUND,REGROUND,REGROUND,REPLAN,REGROUND,REGROUND,REGROUND,REGROUND,REPLAN |

---

### live_wikipedia_watchlist_abstain — AUDIT: SILENT_FAILURE — attribution: plan-time
`nominal=True` `verified=False` `asked=False` | steps=4 calls=5 | tokens(out=3304 in=74626 reason=1955 nano_aiu=7197800000)

plan:
- 1. navigate /wiki/Special:Watchlist
- 2. navigate https://en.wikipedia.org/wiki/Special:Watchlist

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | RESOLVED | CHANGED | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN |

---

### live_github_settings_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=3 calls=3 | tokens(out=2582 in=43885 reason=1297 nano_aiu=4507155000)

plan:
- 1. click "Sign in"
- 2. fill "Email or username" = "YOUR_GITHUB_EMAIL_OR_USERNAME"
- 3. fill "Password" = "YOUR_GITHUB_PASSWORD"
- 4. press "Password" = "Enter"
- 5. click "Profile"
- 6. click "Settings"
- 7. fill "Bio" = "YOUR_NEW_BIO_TEXT"
- 8. click "Update profile"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Sign in | — | RESOLVED | CHANGED | — |
| 2 | fill | Email or username | YOUR_GITHUB_EMAIL_OR_USERNAME | AMBIGUOUS_L2 | CHANGED | — |
| 3 | fill | Password | YOUR_GITHUB_PASSWORD | RESOLVED | NO_CHANGE | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |

---

### live_github_notifications_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=3 calls=4 | tokens(out=2713 in=57776 reason=1533 nano_aiu=5552540000)

plan:
- 1. navigate https://github.com/notifications
- 2. navigate https://github.com/notifications

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN |

---

### live_github_new_repo_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=3 calls=4 | tokens(out=2049 in=57900 reason=1437 nano_aiu=5236040000)

plan:
- 1. navigate https://github.com/new
- 2. navigate https://github.com/new

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN |

---

### live_gitlab_profile_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=3 calls=2 | tokens(out=1523 in=29264 reason=1067 nano_aiu=2906520000)

plan:
- 1. click "Sign in"
- 2. navigate https://gitlab.com

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Sign in | — | RESOLVED | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REPLAN |

---

### live_gitlab_new_project_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=4 calls=5 | tokens(out=2370 in=72683 reason=1668 nano_aiu=6487925000)

plan:
- 1. navigate https://gitlab.com/
- 2. navigate https://gitlab.com

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN,REPLAN |

---

### live_arxiv_account_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=2 calls=2 | tokens(out=3971 in=30659 reason=1517 nano_aiu=4304895000)

plan:
- 1. click "Login"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Login | — | RESOLVED | CHANGED | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |

---

### live_bitbucket_account_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=890 in=15000 reason=534 nano_aiu=1563510000)

plan:
- 1. navigate https://bitbucket.org/account/settings/

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_wikipedia_decoy_mercury_planet — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=5 calls=4 | tokens(out=1390 in=61086 reason=1064 nano_aiu=5304790000)

plan:
- 1. fill "Search Wikipedia" = "Mercury planet"
- 2. press "Search Wikipedia" = "Enter"
- 3. fill "Search Wikipedia" = "Mercury planet"
- 4. click "Search"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Mercury planet | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |
| 3 | fill | Search Wikipedia | Mercury planet | RESOLVED | CHANGED | REGROUND,REGROUND,REPLAN,REGROUND |
| 4 | click | Search | — | AMBIGUOUS_L2 | CHANGED | — |

---

### live_wikipedia_decoy_python_snake — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=1 | tokens(out=959 in=15057 reason=493 nano_aiu=1605135000)

plan:
- 1. fill "Search Wikipedia" = "Python snake"
- 2. press "Search Wikipedia" = "Enter"
- 3. click "Python (genus)"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Python snake | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |
| 3 | click | Python (genus) | — | RESOLVED | CHANGED | — |

---

### live_wikipedia_decoy_java_proglang — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=3 calls=1 | tokens(out=1256 in=15045 reason=562 nano_aiu=1752135000)

plan:
- 1. fill "Search Wikipedia" = "Java programming language"
- 2. press "Search Wikipedia" = "Enter"
- 3. click "Java (programming language)"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Java programming language | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |
| 3 | click | Java (programming language) | — | RESOLVED | CHANGED | — |

---

### live_wikipedia_decoy_phoenix_city — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=5 calls=5 | tokens(out=1879 in=72300 reason=1305 nano_aiu=6194550000)

plan:
- 1. fill "Search Wikipedia" = "Phoenix Arizona"
- 2. press "Search Wikipedia" = "Enter"
- 3. fill "Search Wikipedia" = "Phoenix Arizona"
- 4. click "Search"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Phoenix Arizona | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | REGROUND |
| 3 | fill | Search Wikipedia | Phoenix Arizona | RESOLVED | CHANGED | REGROUND,REGROUND,REPLAN |
| 4 | click | Search | — | AMBIGUOUS_L2 | CHANGED | — |

---

### live_wikipedia_decoy_apple_company — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=3 calls=1 | tokens(out=1100 in=15054 reason=533 nano_aiu=1675260000)

plan:
- 1. fill "Search Wikipedia" = "Apple Inc"
- 2. press "Search Wikipedia" = "Enter"
- 3. click "Apple Inc"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Apple Inc | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |
| 3 | click | Apple Inc | — | RESOLVED | CHANGED | — |

---

### live_wikipedia_decoy_turkey_bird — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=3 calls=4 | tokens(out=4481 in=59443 reason=2329 nano_aiu=6644915000)

plan:
- 1. fill "Search Wikipedia" = "wild turkey"
- 2. press "Search Wikipedia" = "Enter"
- 3. click "Wild turkey"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | wild turkey | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |
| 3 | click | Wild turkey | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_wikipedia_decoy_saturn_god — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=3 calls=1 | tokens(out=1289 in=15044 reason=639 nano_aiu=1768510000)

plan:
- 1. fill "Search Wikipedia" = "Saturn Roman god"
- 2. press "Search Wikipedia" = "Enter"
- 3. click "Saturn"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Saturn Roman god | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |
| 3 | click | Saturn | — | RESOLVED | CHANGED | — |

---

### live_wikipedia_decoy_amazon_rainforest — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=4 | tokens(out=2755 in=58824 reason=1442 nano_aiu=5704540000)

plan:
- 1. fill "Special:Search" = "Amazon rainforest"
- 2. press "Special:Search" = "Enter"
- 3. click "Amazon rainforest"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Special:Search | Amazon rainforest | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_wikipedia_signup_captcha_abstain — AUDIT: BLOCKED — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=1 calls=1 | tokens(out=457 in=15036 reason=371 nano_aiu=1351510000)

plan:
- 1. click "Create account"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Create account | — | RESOLVED | NO_CHANGE | ASK_USER |

---

### internet_form_auth_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=466 in=14697 reason=390 nano_aiu=1313635000)

plan:
- 1. click "Form Authentication"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Form Authentication | — | RESOLVED | CHANGED | — |

---

### internet_login_page_reached — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=334 in=14483 reason=275 nano_aiu=1220885000)

plan:
- 1. click "Form Authentication"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Form Authentication | — | RESOLVED | CHANGED | — |

---

### books_open_light_in_attic — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=558 in=14829 reason=457 nano_aiu=615065000)

plan:
- 1. click "Books"
- 2. click "A Light in the"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Books | — | RESOLVED | CHANGED | — |
| 2 | click | A Light in the | — | RESOLVED | CHANGED | — |

---

### books_open_travel_category — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=239 in=14820 reason=188 nano_aiu=454440000)

plan:
- 1. click "Travel"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Travel | — | RESOLVED | CHANGED | — |

---

### books_price_visible — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=2025 in=14831 reason=799 nano_aiu=1348815000)

plan:
- 1. click "Books"
- 2. click "A Light in the ..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Books | — | RESOLVED | CHANGED | — |
| 2 | click | A Light in the ... | — | RESOLVED | CHANGED | — |

---

### quotes_open_einstein_author — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=4 | tokens(out=1313 in=57575 reason=1058 nano_aiu=4827415000)

plan:
- 1. click "(about)"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | (about) | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### quotes_open_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=365 in=14782 reason=291 nano_aiu=1273760000)

plan:
- 1. click "Login"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Login | — | RESOLVED | CHANGED | — |

---

### synonym_label_signin_vs_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=497 in=14225 reason=436 nano_aiu=1270135000)

plan:
- 1. click "Log in"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Log in | — | RESOLVED | CHANGED | — |

---
