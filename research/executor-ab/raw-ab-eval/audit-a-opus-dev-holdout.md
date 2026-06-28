# Audit Trace — per-task evidence (human-readable, not a metric)

Generated **2026-06-28 03:21 UTC** by `eval.audit` from the executor's event stream (no LLM, no network in the audit itself).

- **attribution_coverage = 1.000** (fraction of FAILING tasks deterministically tagged plan-time/ground-time — 1.0 by construction)
- flag tally: ABSTAIN=7, BLOCKED=1, HONEST_FAIL=7, OK=47, SILENT_FAILURE=6
- Tokens are reported for cost transparency only — never minimized (abstaining more to lower tokens would game the metric and is not done).

---

### live_wikipedia_helium_retrieval — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=77 in=20724 reason=0 nano_aiu=13144750000)

plan:
- 1. fill "Search Wikipedia" = "Helium"
- 2. press "Search Wikipedia" = "Enter"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Helium | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |

---

### live_pydocs_json_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=99 in=20204 reason=0 nano_aiu=7706075000)

plan:
- 1. navigate https://docs.python.org/3/library/index.html
- 2. navigate https://docs.python.org/3/library/json.html

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | — | CHANGED | — |

---

### live_google_search_steam — AUDIT: BLOCKED — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=2 calls=1 | tokens(out=67 in=20845 reason=0 nano_aiu=2548100000)

plan:
- 1. fill "Search" = "steam"
- 2. press "Search" = "Enter"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search | steam | RESOLVED | CHANGED | — |
| 2 | press | Search | Enter | RESOLVED | NO_CHANGE | ASK_USER |

---

### live_wikipedia_signin_synonym — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=40 in=20395 reason=0 nano_aiu=2199350000)

plan:
- 1. click "Log in"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Log in | — | RESOLVED | CHANGED | — |

---

### live_wikipedia_search_submit — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=80 in=20404 reason=0 nano_aiu=2304975000)

plan:
- 1. fill "Search Wikipedia" = "Oxygen"
- 2. press "Search Wikipedia" = "Enter"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Oxygen | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |

---

### live_wikipedia_autocomplete — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=2 | tokens(out=391 in=34697 reason=272 nano_aiu=9852950000)

plan:
- 1. fill "Search Wikipedia" = "Argon"
- 2. click "Argon"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Argon | RESOLVED | CHANGED | — |
| 2 | click | Argon | — | AMBIGUOUS_L2 | CHANGED | — |

---

### live_internet_lazyload — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=36 in=19536 reason=0 nano_aiu=7131075000)

plan:
- 1. click "Start"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Start | — | RESOLVED | CHANGED | — |

---

### live_internet_modal — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=2 | tokens(out=615 in=39246 reason=126 nano_aiu=20897075000)

plan:
- 1. click "click here"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | click here | — | RESOLVED | NO_CHANGE | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |

---

### live_internet_iframe — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=2 | tokens(out=388 in=39553 reason=41 nano_aiu=15352775000)

plan:
- 1. fill "Your content goes here." = "browser agent was here"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Your content goes here. | browser agent was here | RESOLVED | NO_CHANGE | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |

---

### live_example_more_info_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=2 calls=4 | tokens(out=673 in=67065 reason=335 nano_aiu=17194295000)

plan:
- 1. navigate https://example.com
- 2. click "More information..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | More information... | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_hackernews_newest_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=32 in=20410 reason=0 nano_aiu=7667325000)

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
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=34 in=20282 reason=0 nano_aiu=7592325000)

plan:
- 1. click "Log In"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Log In | — | RESOLVED | CHANGED | — |

---

### live_lobsters_comments_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=35 in=20344 reason=0 nano_aiu=7633575000)

plan:
- 1. click "Comments"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Comments | — | RESOLVED | CHANGED | — |

---

### live_mdn_blog_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=58 in=20734 reason=0 nano_aiu=7934825000)

plan:
- 1. navigate https://developer.mozilla.org/en-US/blog/

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_archive_login_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=2 calls=2 | tokens(out=215 in=39221 reason=48 nano_aiu=14712775000)

plan:
- 1. navigate https://archive.org
- 2. click "Log In"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Log In | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_govuk_help_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=104 in=20264 reason=32 nano_aiu=7756075000)

plan:
- 1. navigate https://www.gov.uk/help

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_arxiv_help_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=41 in=20396 reason=0 nano_aiu=7681075000)

plan:
- 1. click "Help"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Help | — | RESOLVED | CHANGED | — |

---

### live_stackoverflow_questions_nav — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=4 calls=5 | tokens(out=3650 in=119250 reason=387 nano_aiu=46447650000)

plan:
- 1. navigate https://stackoverflow.com/questions?tab=Newest
- 2. click "Questions"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | NOT_FOUND | NO_CHANGE | REPLAN,REPLAN,REPLAN,REPLAN |

---

### live_internet_status_code_200 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=36 in=19622 reason=0 nano_aiu=7184825000)

plan:
- 1. click "200"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | 200 | — | RESOLVED | CHANGED | — |

---

### live_internet_challenging_dom_intro — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=281 in=40337 reason=67 nano_aiu=9498675000)

plan:
- 1. navigate https://the-internet.herokuapp.com/challenging_dom

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_books_sapiens_price — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=218 in=20632 reason=53 nano_aiu=8271075000)

plan:
- 1. navigate https://books.toscrape.com/catalogue/sapiens-a-brief-history-of-humankind_996/index.html

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_books_open_mystery_category — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=37 in=20611 reason=0 nano_aiu=7805450000)

plan:
- 1. click "Mystery"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Mystery | — | RESOLVED | CHANGED | — |

---

### live_books_sapiens_stock — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=198 in=20632 reason=35 nano_aiu=8221075000)

plan:
- 1. navigate https://books.toscrape.com/catalogue/sapiens-a-brief-history-of-humankind_996/index.html

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_books_grand_design_price — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=446 in=19915 reason=62 nano_aiu=8392950000)

plan:
- 1. navigate https://books.toscrape.com/catalogue/the-grand-design_405/index.html

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_books_dune_price — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=2 calls=4 | tokens(out=547 in=69789 reason=312 nano_aiu=18513795000)

plan:
- 1. click "Science Fiction"
- 2. click "Dune (Dune #1)"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Science Fiction | — | RESOLVED | CHANGED | — |
| 2 | click | Dune (Dune #1) | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_books_page2_pagination — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=55 in=20435 reason=0 nano_aiu=7740450000)

plan:
- 1. navigate https://books.toscrape.com/catalogue/page-2.html

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_wikipedia_oxygen_search — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=81 in=20690 reason=0 nano_aiu=7964825000)

plan:
- 1. fill "Search Wikipedia" = "Oxygen"
- 2. press "Search Wikipedia" = "Enter"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search Wikipedia | Oxygen | RESOLVED | CHANGED | — |
| 2 | press | Search Wikipedia | Enter | RESOLVED | CHANGED | — |

---

### live_wikipedia_periodic_table_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=140 in=20711 reason=24 nano_aiu=8125450000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Oxygen
- 2. click "periodic table"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | periodic table | — | RESOLVED | CHANGED | — |

---

### live_wikipedia_einstein_body_text — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=2 | tokens(out=405 in=34651 reason=261 nano_aiu=9219460000)

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
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=42 in=20494 reason=0 nano_aiu=7744825000)

plan:
- 1. click "Tutorial"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Tutorial | — | RESOLVED | CHANGED | — |

---

### live_hackernews_show_then_ask — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=60 in=20446 reason=0 nano_aiu=7759825000)

plan:
- 1. click "show"
- 2. click "ask"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | show | — | RESOLVED | CHANGED | — |
| 2 | click | ask | — | RESOLVED | CHANGED | — |

---

### live_mdn_html_input — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=69 in=20758 reason=0 nano_aiu=7977325000)

plan:
- 1. navigate https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_mdn_css_flex — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=68 in=20746 reason=0 nano_aiu=7967325000)

plan:
- 1. navigate https://developer.mozilla.org/en-US/docs/Web/CSS/flex

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_govuk_bank_holidays — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=52 in=20283 reason=0 nano_aiu=7637950000)

plan:
- 1. navigate https://www.gov.uk/bank-holidays

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_govuk_vat_rates — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=278 in=20286 reason=45 nano_aiu=8204825000)

plan:
- 1. navigate https://www.gov.uk/guidance/rates-of-vat-on-different-goods-and-services

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_govuk_min_wage — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=60 in=20271 reason=0 nano_aiu=7650450000)

plan:
- 1. navigate https://www.gov.uk/national-minimum-wage-rates

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_govuk_check_uk_visa — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=97 in=20279 reason=29 nano_aiu=7747950000)

plan:
- 1. navigate https://www.gov.uk/check-uk-visa

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_govuk_driving_licences — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=4 | tokens(out=510 in=69506 reason=290 nano_aiu=18243420000)

plan:
- 1. click "Driving and transport"
- 2. click "Driving licences"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Driving and transport | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_wikipedia_jupiter — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=62 in=20700 reason=0 nano_aiu=7923575000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Jupiter

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_books_fiction_page2 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=2 | tokens(out=196 in=34544 reason=106 nano_aiu=8944585000)

plan:
- 1. click "Fiction"
- 2. click "next"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Fiction | — | RESOLVED | CHANGED | — |
| 2 | click | next | — | RESOLVED | CHANGED | REGROUND |

---

### live_arxiv_attention_paper — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=2 calls=4 | tokens(out=926 in=69924 reason=364 nano_aiu=19609670000)

plan:
- 1. fill "Search term or terms" = "Attention Is All You Need"
- 2. click "Search"
- 3. click "Attention Is All You Need"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Search term or terms | Attention Is All You Need | RESOLVED | CHANGED | — |
| 2 | click | Search | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_wikipedia_preferences_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=6 calls=10 | tokens(out=6579 in=169915 reason=1726 nano_aiu=52919735000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Special:Preferences
- 2. navigate https://en.wikipedia.org/wiki/Special:Preferences#mw-prefsection-personal-i18n
- 3. click "Log in"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | RESOLVED | CHANGED | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN,WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |
| 3 | click | Log in | — | RESOLVED | CHANGED | REGROUND,REGROUND,REPLAN |

---

### live_wikipedia_watchlist_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=42 in=20684 reason=0 nano_aiu=7863575000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Special:Watchlist

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_github_settings_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=7 calls=11 | tokens(out=4717 in=186210 reason=1465 nano_aiu=53347685000)

plan:
- 1. navigate https://github.com/login
- 2. navigate https://github.com/settings/profile
- 3. navigate https://github.com/settings/profile
- 4. press "Password" = "Enter"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | — | CHANGED | — |
| 3 | navigate | url | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN |
| 4 | press | Password | Enter | RESOLVED | NO_CHANGE | REGROUND,REGROUND,REPLAN,REGROUND,WAIT_SCROLL_DISMISS,REPLAN,REGROUND,REGROUND,REPLAN |

---

### live_github_notifications_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=5 calls=10 | tokens(out=4265 in=165475 reason=1250 nano_aiu=44956735000)

plan:
- 1. navigate https://github.com/notifications
- 2. navigate https://github.com/notifications
- 3. click "Sign in"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN |
| 3 | click | Sign in | — | AMBIGUOUS_L2 | NO_CHANGE | REGROUND,REGROUND,REPLAN,REGROUND,WAIT_SCROLL_DISMISS,REPLAN |

---

### live_github_new_repo_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=2 calls=4 | tokens(out=1660 in=68799 reason=856 nano_aiu=19438545000)

plan:
- 1. navigate https://github.com/new
- 2. fill "Repository name" = "demo"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | fill | Repository name | demo | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_gitlab_profile_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=1 calls=2 | tokens(out=345 in=40177 reason=98 nano_aiu=15635275000)

plan:
- 1. navigate https://gitlab.com/-/profile

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | NOT_FOUND | NO_CHANGE | REPLAN |

---

### live_gitlab_new_project_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=2 calls=3 | tokens(out=873 in=59953 reason=150 nano_aiu=24146350000)

plan:
- 1. navigate https://gitlab.com/-/projects/new

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | NOT_FOUND | NO_CHANGE | REPLAN,REPLAN |

---

### live_arxiv_account_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=2 calls=1 | tokens(out=61 in=20408 reason=0 nano_aiu=7738575000)

plan:
- 1. click "Login"
- 2. navigate https://arxiv.org/user

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Login | — | RESOLVED | CHANGED | — |
| 2 | navigate | — | — | — | CHANGED | — |

---

### live_bitbucket_account_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=55 in=20531 reason=0 nano_aiu=7800450000)

plan:
- 1. navigate https://bitbucket.org/account/settings/

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_wikipedia_decoy_mercury_planet — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=67 in=20714 reason=0 nano_aiu=7944825000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Mercury_(planet)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_wikipedia_decoy_python_snake — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=65 in=20697 reason=0 nano_aiu=7929200000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Python_(genus)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_wikipedia_decoy_java_proglang — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=63 in=20684 reason=0 nano_aiu=7916075000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Java_(programming_language)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_wikipedia_decoy_phoenix_city — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=62 in=20701 reason=0 nano_aiu=7924200000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Phoenix,_Arizona

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_wikipedia_decoy_apple_company — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=71 in=20687 reason=8 nano_aiu=7937950000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Apple_Inc.

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_wikipedia_decoy_turkey_bird — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=61 in=20688 reason=0 nano_aiu=7913575000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Turkey_(bird)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_wikipedia_decoy_saturn_god — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=92 in=20702 reason=21 nano_aiu=7999825000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Saturn_(mythology)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_wikipedia_decoy_amazon_rainforest — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=60 in=20689 reason=0 nano_aiu=7911700000)

plan:
- 1. navigate https://en.wikipedia.org/wiki/Amazon_rainforest

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_wikipedia_signup_captcha_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=41 in=20682 reason=0 nano_aiu=7859825000)

plan:
- 1. click "Create account"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Create account | — | RESOLVED | CHANGED | — |

---

### internet_form_auth_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=39 in=20231 reason=0 nano_aiu=7572950000)

plan:
- 1. click "Form Authentication"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Form Authentication | — | RESOLVED | CHANGED | — |

---

### internet_login_page_reached — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=39 in=19944 reason=0 nano_aiu=7393575000)

plan:
- 1. click "Form Authentication"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Form Authentication | — | RESOLVED | CHANGED | — |

---

### books_open_light_in_attic — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=125 in=20341 reason=47 nano_aiu=2378100000)

plan:
- 1. click "A Light in the ..."

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | A Light in the ... | — | RESOLVED | CHANGED | — |

---

### books_open_travel_category — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=35 in=20614 reason=0 nano_aiu=7802325000)

plan:
- 1. click "Travel"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Travel | — | RESOLVED | CHANGED | — |

---

### books_price_visible — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=4 | tokens(out=1419 in=70630 reason=688 nano_aiu=20608420000)

plan:
- 1. click "A Light in the ..."
- 2. navigate https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | A Light in the ... | — | RESOLVED | CHANGED | REGROUND,REGROUND,REPLAN |
| 2 | navigate | — | — | — | CHANGED | — |

---

### quotes_open_einstein_author — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=4 | tokens(out=418 in=68508 reason=297 nano_aiu=17365670000)

plan:
- 1. navigate /author/Albert-Einstein

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN |

---

### quotes_open_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=33 in=20214 reason=0 nano_aiu=7547325000)

plan:
- 1. click "Login"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Login | — | RESOLVED | CHANGED | — |

---

### synonym_label_signin_vs_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=45 in=19491 reason=22 nano_aiu=7125450000)

plan:
- 1. click "Log in"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Log in | — | RESOLVED | CHANGED | — |

---
