# Audit Trace — per-task evidence (human-readable, not a metric)

Generated **2026-06-28 11:08 UTC** by `eval.audit` from the executor's event stream (no LLM, no network in the audit itself).

- **attribution_coverage = 1.000** (fraction of FAILING tasks deterministically tagged plan-time/ground-time — 1.0 by construction)
- flag tally: ABSTAIN=9, BLOCKED=2, HONEST_FAIL=6, OK=49, SILENT_FAILURE=2
- Tokens are reported for cost transparency only — never minimized (abstaining more to lower tokens would game the metric and is not done).

---

### live_wikipedia_helium_retrieval — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=16 calls=17 | tokens(out=2591 in=172538 reason=1164 nano_aiu=6214790000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | Helium | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | observe | Helium | — | — | — | — |
| 5 | click | Helium | — | — | — | — |
| 6 | observe | — | — | — | — | — |
| 7 | read | Helium | — | — | — | — |
| 8 | click | Helium | — | — | — | — |
| 9 | navigate | — | — | — | — | — |
| 10 | verify | — | — | — | — | — |
| 11 | read | atomic number | — | — | — | — |
| 12 | observe | atomic number 2 | — | — | — | — |
| 13 | read | He atomic number Z 2 | — | — | — | — |
| 14 | read | 2 | — | — | — | — |
| 15 | verify | — | — | — | — | — |
| 16 | finish | — | — | — | — | — |

---

### live_pydocs_json_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=7 calls=8 | tokens(out=988 in=75086 reason=375 nano_aiu=3515690000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Python Standard Library | — | — | — | — |
| 2 | observe | Standard Library | — | — | — | — |
| 3 | click | Library reference | — | — | — | — |
| 4 | observe | json | — | — | — | — |
| 5 | click | json — JSON encoder and decoder | — | — | — | — |
| 6 | verify | — | — | — | — | — |
| 7 | finish | — | — | — | — | — |

---

### live_google_search_steam — AUDIT: BLOCKED — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=21 calls=22 | tokens(out=3152 in=218484 reason=1414 nano_aiu=7863015000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search | steam | — | — | — |
| 3 | click | Google Search | — | — | — | — |
| 4 | observe | search | — | — | — | — |
| 5 | navigate | — | — | — | — | — |
| 6 | fill | Search | steam | — | — | — |
| 7 | click | Google Search | — | — | — | — |
| 8 | verify | — | — | — | — | — |
| 9 | read | page content | — | — | — | — |
| 10 | navigate | — | — | — | — | — |
| 11 | observe | search box | — | — | — | — |
| 12 | fill | Search | steam | — | — | — |
| 13 | click | Google Search | — | — | — | — |
| 14 | navigate | — | — | — | — | — |
| 15 | observe | — | — | — | — | — |
| 16 | fill | Search | steam | — | — | — |
| 17 | observe | search button | — | — | — | — |
| 18 | read | steam | — | — | — | — |
| 19 | click | steam | — | — | — | — |
| 20 | verify | — | — | — | — | — |
| 21 | finish | — | — | — | — | — |

---

### live_wikipedia_signin_synonym — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=645 in=47107 reason=385 nano_aiu=3130560000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Sign In | — | — | — | — |
| 2 | observe | — | — | — | — | — |
| 3 | observe | Log in | — | — | — | — |
| 4 | click | Log in | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_wikipedia_search_submit — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=11 calls=12 | tokens(out=2018 in=99917 reason=1030 nano_aiu=4054955000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | Oxygen | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | observe | Oxygen | — | — | — | — |
| 5 | click | Oxygen | — | — | — | — |
| 6 | observe | — | — | — | — | — |
| 7 | read | Oxygen | — | — | — | — |
| 8 | click | Oxygen is a chemical element | — | — | — | — |
| 9 | navigate | — | — | — | — | — |
| 10 | verify | — | — | — | — | — |
| 11 | finish | — | — | — | — | — |

---

### live_wikipedia_autocomplete — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=7 calls=8 | tokens(out=1121 in=55681 reason=428 nano_aiu=2777145000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | click | Search Wikipedia | — | — | — | — |
| 3 | fill | Search Wikipedia | Argon | — | — | — |
| 4 | observe | Argon | — | — | — | — |
| 5 | click | Argon
Chemical element with atomic number 18 (Ar) | — | — | — | — |
| 6 | verify | — | — | — | — | — |
| 7 | finish | — | — | — | — | — |

---

### live_internet_lazyload — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=7 calls=8 | tokens(out=1055 in=52742 reason=464 nano_aiu=3474445000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Start | — | — | — | — |
| 2 | click | Start | — | — | — | — |
| 3 | read | hidden text | — | — | — | — |
| 4 | read | Hello World! | — | — | — | — |
| 5 | read | text | — | — | — | — |
| 6 | verify | — | — | — | — | — |
| 7 | finish | — | — | — | — | — |

---

### live_internet_modal — AUDIT: SILENT_FAILURE — attribution: plan-time
`nominal=True` `verified=False` `asked=False` | steps=4 calls=4 | tokens(out=533 in=25558 reason=278 nano_aiu=2738490000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page | — | — | — | — |
| 2 | observe | — | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_internet_iframe — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=5 calls=6 | tokens(out=795 in=38234 reason=338 nano_aiu=3001480000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | iframe | — | — | — | — |
| 2 | fill | Rich Text Area | browser agent was here | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | read | Rich Text Area | — | — | — | — |
| 5 | finish | — | — | — | — | — |

---

### live_example_more_info_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=937 in=45630 reason=513 nano_aiu=2501065000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | More information | — | — | — | — |
| 2 | read | More information | — | — | — | — |
| 3 | observe | — | — | — | — | — |
| 4 | click | Learn more | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_hackernews_newest_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=970 in=46757 reason=421 nano_aiu=3394235000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | new | — | — | — | — |
| 2 | click | new | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | read | page title or heading | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_gnu_licenses_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=False` | steps=0 calls=0 | tokens(out=0 in=0 reason=0 nano_aiu=0.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|

---

### live_osm_login_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=871 in=45382 reason=373 nano_aiu=3249540000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Log In | — | — | — | — |
| 2 | click | Log In | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | read | login | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_lobsters_comments_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=484 in=32205 reason=349 nano_aiu=2779785000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Comments | — | — | — | — |
| 2 | click | Comments | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_mdn_blog_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=11 calls=12 | tokens(out=1600 in=88462 reason=669 nano_aiu=3384395000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Blog | — | — | — | — |
| 2 | click | Blog | — | — | — | — |
| 3 | click | MDN blog RSS feed | — | — | — | — |
| 4 | click | Hacks blog | — | — | — | — |
| 5 | observe | — | — | — | — | — |
| 6 | read | Blog | — | — | — | — |
| 7 | observe | About | — | — | — | — |
| 8 | observe | Blog | — | — | — | — |
| 9 | navigate | — | — | — | — | — |
| 10 | verify | — | — | — | — | — |
| 11 | finish | — | — | — | — | — |

---

### live_archive_login_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=26 calls=28 | tokens(out=3698 in=222764 reason=1464 nano_aiu=6747465000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Log In | — | — | — | — |
| 2 | observe | — | — | — | — | — |
| 3 | read | Log In | — | — | — | — |
| 4 | verify | — | — | — | — | — |
| 5 | observe | sign in | — | — | — | — |
| 6 | observe | account | — | — | — | — |
| 7 | observe | user | — | — | — | — |
| 8 | read | — | — | — | — | — |
| 9 | navigate | — | — | — | — | — |
| 10 | observe | Log In | — | — | — | — |
| 11 | read | login | — | — | — | — |
| 12 | observe | user menu | — | — | — | — |
| 13 | observe | Patron | — | — | — | — |
| 14 | observe | Search | — | — | — | — |
| 15 | read | archive | — | — | — | — |
| 16 | click | Log In | — | — | — | — |
| 17 | observe | — | — | — | — | — |
| 18 | verify | — | — | — | — | — |
| 19 | navigate | — | — | — | — | — |
| 20 | verify | — | — | — | — | — |
| 21 | observe | Account | — | — | — | — |
| 22 | navigate | — | — | — | — | — |
| 23 | read | search | — | — | — | — |
| 24 | verify | — | — | — | — | — |
| 25 | observe | login | — | — | — | — |
| 26 | finish | — | — | — | — | — |

---

### live_govuk_help_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=623 in=31679 reason=375 nano_aiu=2898855000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Help | — | — | — | — |
| 2 | click | Help | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_arxiv_help_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=12 calls=13 | tokens(out=1779 in=98338 reason=940 nano_aiu=3717570000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Help | — | — | — | — |
| 2 | click | Help | — | — | — | — |
| 3 | click | Help Pages | — | — | — | — |
| 4 | observe | — | — | — | — | — |
| 5 | read | Help | — | — | — | — |
| 6 | click | Help | — | — | — | — |
| 7 | click | Help Pages | — | — | — | — |
| 8 | click | Open navigation menu | — | — | — | — |
| 9 | verify | — | — | — | — | — |
| 10 | navigate | — | — | — | — | — |
| 11 | verify | — | — | — | — | — |
| 12 | finish | — | — | — | — | — |

---

### live_stackoverflow_questions_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=4 calls=5 | tokens(out=509 in=31602 reason=313 nano_aiu=2778270000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Questions | — | — | — | — |
| 2 | observe | navigation menu | — | — | — | — |
| 3 | observe | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_internet_status_code_200 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=568 in=31296 reason=256 nano_aiu=2826815000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | 200 | — | — | — | — |
| 2 | click | 200 | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_internet_challenging_dom_intro — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=860 in=47493 reason=410 nano_aiu=2565950000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Challenging DOM | — | — | — | — |
| 2 | observe | — | — | — | — | — |
| 3 | click | Elemental Selenium | — | — | — | — |
| 4 | read | introductory description | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_books_sapiens_price — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=5 calls=6 | tokens(out=774 in=42183 reason=333 nano_aiu=2559010000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page content | — | — | — | — |
| 2 | click | Sapiens: A Brief History ... | — | — | — | — |
| 3 | read | Sapiens price | — | — | — | — |
| 4 | verify | — | — | — | — | — |
| 5 | finish | — | — | — | — | — |

---

### live_books_open_mystery_category — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=475 in=31167 reason=246 nano_aiu=3440735000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Mystery | — | — | — | — |
| 2 | click | Mystery | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_books_sapiens_stock — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=894 in=50312 reason=422 nano_aiu=4116950000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page | — | — | — | — |
| 2 | observe | Sapiens: A Brief History | — | — | — | — |
| 3 | click | Sapiens: A Brief History ... | — | — | — | — |
| 4 | read | stock | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_books_grand_design_price — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=4 | tokens(out=388 in=25620 reason=222 nano_aiu=1989400000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page | — | — | — | — |
| 2 | verify | — | — | — | — | — |
| 3 | finish | — | — | — | — | — |

---

### live_books_dune_price — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=8 calls=9 | tokens(out=1075 in=63578 reason=417 nano_aiu=3680400000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Science Fiction | — | — | — | — |
| 2 | click | Science Fiction | — | — | — | — |
| 3 | observe | Dune | — | — | — | — |
| 4 | click | Dune (Dune #1) | — | — | — | — |
| 5 | observe | — | — | — | — | — |
| 6 | read | Dune price | — | — | — | — |
| 7 | verify | — | — | — | — | — |
| 8 | finish | — | — | — | — | — |

---

### live_books_page2_pagination — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=530 in=31727 reason=395 nano_aiu=2131095000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | page navigation next | — | — | — | — |
| 2 | click | next | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_wikipedia_oxygen_search — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=15 calls=16 | tokens(out=2542 in=146367 reason=1125 nano_aiu=5726000000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | Oxygen | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | observe | Oxygen | — | — | — | — |
| 5 | click | Oxygen | — | — | — | — |
| 6 | observe | — | — | — | — | — |
| 7 | read | Oxygen | — | — | — | — |
| 8 | observe | chemical element | — | — | — | — |
| 9 | click | Oxygen | — | — | — | — |
| 10 | observe | symbol O | — | — | — | — |
| 11 | navigate | — | — | — | — | — |
| 12 | read | Oxygen chemical element atomic number 8 | — | — | — | — |
| 13 | verify | — | — | — | — | — |
| 14 | verify | — | — | — | — | — |
| 15 | finish | — | — | — | — | — |

---

### live_wikipedia_periodic_table_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=False` | steps=24 calls=24 | tokens(out=3638 in=235220 reason=1733 nano_aiu=8256540000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | verify | — | — | — | — | — |
| 2 | navigate | — | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | observe | periodic table | — | — | — | — |
| 5 | click | periodic table | — | — | — | — |
| 6 | observe | — | — | — | — | — |
| 7 | read | periodic table | — | — | — | — |
| 8 | click | Oxygen in the periodic table | — | — | — | — |
| 9 | observe | Periodic table | — | — | — | — |
| 10 | read | Period 2 | — | — | — | — |
| 11 | navigate | — | — | — | — | — |
| 12 | verify | — | — | — | — | — |
| 13 | navigate | — | — | — | — | — |
| 14 | observe | periodic | — | — | — | — |
| 15 | click | periodic table | — | — | — | — |
| 16 | click | Period | — | — | — | — |
| 17 | read | tabular arrangement | — | — | — | — |
| 18 | observe | Periodic table | — | — | — | — |
| 19 | click | periodic table | — | — | — | — |
| 20 | navigate | — | — | — | — | — |
| 21 | observe | chemical elements | — | — | — | — |
| 22 | click | chemical element | — | — | — | — |
| 23 | observe | group | — | — | — | — |
| 24 | click | Group | — | — | — | — |

---

### live_wikipedia_einstein_body_text — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=12 calls=13 | tokens(out=1498 in=97161 reason=555 nano_aiu=3525815000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | E=mc^2 | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | observe | Einstein | — | — | — | — |
| 5 | read | E=mc^2 | — | — | — | — |
| 6 | observe | Mass | — | — | — | — |
| 7 | click | Mass–energy equivalence | — | — | — | — |
| 8 | observe | Einstein | — | — | — | — |
| 9 | click | Albert Einstein | — | — | — | — |
| 10 | click | Einstein, Albert | — | — | — | — |
| 11 | verify | — | — | — | — | — |
| 12 | finish | — | — | — | — | — |

---

### live_pydocs_tutorial_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=5 calls=6 | tokens(out=713 in=42743 reason=409 nano_aiu=3121990000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Python Tutorial | — | — | — | — |
| 2 | observe | Tutorial | — | — | — | — |
| 3 | click | Tutorial | — | — | — | — |
| 4 | verify | — | — | — | — | — |
| 5 | finish | — | — | — | — | — |

---

### live_hackernews_show_then_ask — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=1008 in=45696 reason=480 nano_aiu=3316465000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Show HN | — | — | — | — |
| 2 | click | show | — | — | — | — |
| 3 | observe | Ask HN | — | — | — | — |
| 4 | click | ask | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_mdn_html_input — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=18 calls=19 | tokens(out=2559 in=181628 reason=955 nano_aiu=6092410000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | input | — | — | — | — |
| 2 | observe | — | — | — | — | — |
| 3 | read | main content | — | — | — | — |
| 4 | click | Elements | — | — | — | — |
| 5 | click | HTML: Markup language | — | — | — | — |
| 6 | click | HTML | — | — | — | — |
| 7 | observe | — | — | — | — | — |
| 8 | click | Elements | — | — | — | — |
| 9 | observe | input | — | — | — | — |
| 10 | click | <input> | — | — | — | — |
| 11 | read | input element link | — | — | — | — |
| 12 | read | input form element | — | — | — | — |
| 13 | navigate | — | — | — | — | — |
| 14 | verify | — | — | — | — | — |
| 15 | read | input element reference | — | — | — | — |
| 16 | verify | — | — | — | — | — |
| 17 | verify | — | — | — | — | — |
| 18 | finish | — | — | — | — | — |

---

### live_mdn_css_flex — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=12 calls=12 | tokens(out=1690 in=95025 reason=616 nano_aiu=3714415000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | CSS flex | — | — | — | — |
| 2 | read | page | — | — | — | — |
| 3 | observe | search | — | — | — | — |
| 4 | click | Skip to search | — | — | — | — |
| 5 | observe | — | — | — | — | — |
| 6 | click | Properties | — | — | — | — |
| 7 | navigate | — | — | — | — | — |
| 8 | verify | — | — | — | — | — |
| 9 | read | page | — | — | — | — |
| 10 | verify | — | — | — | — | — |
| 11 | verify | — | — | — | — | — |
| 12 | finish | — | — | — | — | — |

---

### live_govuk_bank_holidays — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=17 calls=16 | tokens(out=2220 in=138014 reason=939 nano_aiu=4561295000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page content | — | — | — | — |
| 2 | observe | bank holidays | — | — | — | — |
| 3 | observe | — | — | — | — | — |
| 4 | observe | Search | — | — | — | — |
| 5 | click | Search GOV.UK | — | — | — | — |
| 6 | fill | Search GOV.UK | bank holidays | — | — | — |
| 7 | click | Show search menu | — | — | — | — |
| 8 | fill | Search | bank holidays | — | — | — |
| 9 | click | Search | — | — | — | — |
| 10 | read | bank holidays | — | — | — | — |
| 11 | observe | bank holidays | — | — | — | — |
| 12 | click | bank holidays | — | — | — | — |
| 13 | read | bank holidays | — | — | — | — |
| 14 | navigate | — | — | — | — | — |
| 15 | read | bank holidays England Wales Scotland Northern Ireland | — | — | — | — |
| 16 | verify | — | — | — | — | — |
| 17 | finish | — | — | — | — | — |

---

### live_govuk_vat_rates — AUDIT: SILENT_FAILURE — attribution: plan-time
`nominal=True` `verified=False` `asked=False` | steps=26 calls=27 | tokens(out=3621 in=259380 reason=1183 nano_aiu=7607210000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | VAT | — | — | — | — |
| 2 | observe | — | — | — | — | — |
| 3 | click | Business and self-employed | — | — | — | — |
| 4 | click | Go to the GOV.UK homepage | — | — | — | — |
| 5 | observe | Business and self-employed | — | — | — | — |
| 6 | click | Money and tax | — | — | — | — |
| 7 | navigate | — | — | — | — | — |
| 8 | observe | search | — | — | — | — |
| 9 | click | Search GOV.UK | — | — | — | — |
| 10 | fill | Search GOV.UK | VAT rates | — | — | — |
| 11 | navigate | — | — | — | — | — |
| 12 | read | VAT rates standard reduced zero | — | — | — | — |
| 13 | navigate | — | — | — | — | — |
| 14 | read | VAT rates | — | — | — | — |
| 15 | navigate | — | — | — | — | — |
| 16 | read | VAT | — | — | — | — |
| 17 | observe | Business tax | — | — | — | — |
| 18 | click | Business tax and returns | — | — | — | — |
| 19 | read | VAT | — | — | — | — |
| 20 | observe | VAT rates on different goods and services | — | — | — | — |
| 21 | observe | VAT rates | — | — | — | — |
| 22 | click | VAT rates on different goods and services | — | — | — | — |
| 23 | read | standard reduced zero rates | — | — | — | — |
| 24 | verify | — | — | — | — | — |
| 25 | verify | — | — | — | — | — |
| 26 | finish | — | — | — | — | — |

---

### live_govuk_min_wage — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=26 calls=29 | tokens(out=3487 in=300158 reason=1031 nano_aiu=8072620000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Minimum Wage National Living Wage | — | — | — | — |
| 2 | observe | — | — | — | — | — |
| 3 | read | wage rates | — | — | — | — |
| 4 | observe | Employment Work Pay | — | — | — | — |
| 5 | click | Working, jobs and pensions | — | — | — | — |
| 6 | observe | Minimum Wage | — | — | — | — |
| 7 | observe | — | — | — | — | — |
| 8 | read | Search | — | — | — | — |
| 9 | click | Search GOV.UK | — | — | — | — |
| 10 | navigate | — | — | — | — | — |
| 11 | observe | Search | — | — | — | — |
| 12 | fill | Search GOV.UK | National Minimum Wage | — | — | — |
| 13 | navigate | — | — | — | — | — |
| 14 | read | National Minimum Wage National Living Wage rates | — | — | — | — |
| 15 | navigate | — | — | — | — | — |
| 16 | read | minimum wage living wage rates current | — | — | — | — |
| 17 | observe | rates current rates 2024 2025 2026 | — | — | — | — |
| 18 | observe | — | — | — | — | — |
| 19 | read | £ per hour rate apprentice | — | — | — | — |
| 20 | navigate | — | — | — | — | — |
| 21 | read | £ rate per hour April 2024 2025 | — | — | — | — |
| 22 | navigate | — | — | — | — | — |
| 23 | observe | current rates what the rates are rates for | — | — | — | — |
| 24 | click | Who gets the minimum wage | — | — | — | — |
| 25 | read | minimum wage rate £ per hour | — | — | — | — |
| 26 | finish | — | — | — | — | — |

---

### live_govuk_check_uk_visa — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=7 calls=8 | tokens(out=1059 in=53737 reason=426 nano_aiu=2723830000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | visa | — | — | — | — |
| 2 | click | Visas and immigration | — | — | — | — |
| 3 | observe | check visa | — | — | — | — |
| 4 | navigate | — | — | — | — | — |
| 5 | read | visa check | — | — | — | — |
| 6 | verify | — | — | — | — | — |
| 7 | finish | — | — | — | — | — |

---

### live_govuk_driving_licences — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=8 calls=9 | tokens(out=1152 in=64004 reason=530 nano_aiu=2891480000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Driving and transport | — | — | — | — |
| 2 | click | Driving and transport | — | — | — | — |
| 3 | observe | Driving licences | — | — | — | — |
| 4 | click | Driving and transport | — | — | — | — |
| 5 | observe | Driving licences | — | — | — | — |
| 6 | click | Driving licences | — | — | — | — |
| 7 | verify | — | — | — | — | — |
| 8 | finish | — | — | — | — | — |

---

### live_wikipedia_jupiter — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=12 calls=13 | tokens(out=1758 in=112009 reason=756 nano_aiu=3924630000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page content | — | — | — | — |
| 2 | observe | search | — | — | — | — |
| 3 | click | Search Wikipedia | — | — | — | — |
| 4 | fill | Search Wikipedia | Jupiter | — | — | — |
| 5 | click | Search | — | — | — | — |
| 6 | read | Jupiter article search results | — | — | — | — |
| 7 | click | Jupiter | — | — | — | — |
| 8 | observe | Jupiter planet | — | — | — | — |
| 9 | click | Jupiter | — | — | — | — |
| 10 | navigate | — | — | — | — | — |
| 11 | verify | — | — | — | — | — |
| 12 | finish | — | — | — | — | — |

---

### live_books_fiction_page2 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=817 in=45814 reason=380 nano_aiu=4002050000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Fiction | — | — | — | — |
| 2 | click | Fiction | — | — | — | — |
| 3 | observe | next | — | — | — | — |
| 4 | click | next | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_arxiv_attention_paper — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=23 calls=24 | tokens(out=3039 in=209697 reason=973 nano_aiu=6469980000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search term or terms | Attention Is All You Need | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | observe | Attention Is All You Need | — | — | — | — |
| 5 | click | Search in all archives. | — | — | — | — |
| 6 | read | Attention Is All You Need | — | — | — | — |
| 7 | observe | Search | — | — | — | — |
| 8 | fill | Search term or terms | Attention Is All You Need | — | — | — |
| 9 | click | Search | — | — | — | — |
| 10 | observe | — | — | — | — | — |
| 11 | click | Advanced Search | — | — | — | — |
| 12 | navigate | — | — | — | — | — |
| 13 | observe | search | — | — | — | — |
| 14 | fill | Search term or terms | Attention Is All You Need | — | — | — |
| 15 | click | Search | — | — | — | — |
| 16 | read | Attention Is All You Need | — | — | — | — |
| 17 | observe | all archives | — | — | — | — |
| 18 | click | Search in all archives. | — | — | — | — |
| 19 | navigate | — | — | — | — | — |
| 20 | navigate | — | — | — | — | — |
| 21 | read | Attention Is All You Need | — | — | — | — |
| 22 | verify | — | — | — | — | — |
| 23 | finish | — | — | — | — | — |

---

### live_wikipedia_preferences_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=17 calls=17 | tokens(out=2925 in=147860 reason=1579 nano_aiu=5769145000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | current page | — | — | — | — |
| 2 | observe | account preferences settings | — | — | — | — |
| 3 | observe | user menu account | — | — | — | — |
| 4 | click | Main menu | — | — | — | — |
| 5 | observe | Preferences | — | — | — | — |
| 6 | observe | — | — | — | — | — |
| 7 | read | top right user account | — | — | — | — |
| 8 | observe | username profile | — | — | — | — |
| 9 | observe | Tools | — | — | — | — |
| 10 | click | Personal tools | — | — | — | — |
| 11 | observe | Personal tools | — | — | — | — |
| 12 | read | Personal tools Preferences | — | — | — | — |
| 13 | observe | Preferences language settings | — | — | — | — |
| 14 | read | Log in Create account user | — | — | — | — |
| 15 | navigate | — | — | — | — | — |
| 16 | read | login form | — | — | — | — |
| 17 | finish | — | — | — | — | — |

---

### live_wikipedia_watchlist_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=9 calls=10 | tokens(out=1384 in=71822 reason=605 nano_aiu=5110955000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | watchlist | — | — | — | — |
| 2 | observe | — | — | — | — | — |
| 3 | click | Main menu | — | — | — | — |
| 4 | observe | watchlist | — | — | — | — |
| 5 | observe | — | — | — | — | — |
| 6 | read | watchlist | — | — | — | — |
| 7 | observe | Log in | — | — | — | — |
| 8 | navigate | — | — | — | — | — |
| 9 | finish | — | — | — | — | — |

---

### live_github_settings_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=10 calls=11 | tokens(out=2126 in=97431 reason=1307 nano_aiu=5001420000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | settings account profile | — | — | — | — |
| 2 | observe | — | — | — | — | — |
| 3 | read | user profile menu settings | — | — | — | — |
| 4 | click | Sign in | — | — | — | — |
| 5 | observe | — | — | — | — | — |
| 6 | navigate | — | — | — | — | — |
| 7 | navigate | — | — | — | — | — |
| 8 | observe | profile avatar user menu | — | — | — | — |
| 9 | observe | — | — | — | — | — |
| 10 | finish | — | — | — | — | — |

---

### live_github_notifications_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=7 calls=8 | tokens(out=1170 in=61311 reason=631 nano_aiu=3071960000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | notifications | — | — | — | — |
| 2 | observe | — | — | — | — | — |
| 3 | read | current page | — | — | — | — |
| 4 | observe | bell | — | — | — | — |
| 5 | navigate | — | — | — | — | — |
| 6 | verify | — | — | — | — | — |
| 7 | finish | — | — | — | — | — |

---

### live_github_new_repo_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=6 calls=7 | tokens(out=986 in=51970 reason=486 nano_aiu=2788260000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | create repository | — | — | — | — |
| 2 | observe | new | — | — | — | — |
| 3 | observe | — | — | — | — | — |
| 4 | click | Sign in | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_gitlab_profile_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=12 calls=13 | tokens(out=1933 in=108083 reason=970 nano_aiu=3891765000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | profile settings | — | — | — | — |
| 2 | observe | user menu | — | — | — | — |
| 3 | click | Main Menu | — | — | — | — |
| 4 | read | main content | — | — | — | — |
| 5 | observe | Sign in | — | — | — | — |
| 6 | click | Sign in | — | — | — | — |
| 7 | observe | login | — | — | — | — |
| 8 | observe | — | — | — | — | — |
| 9 | read | security verification | — | — | — | — |
| 10 | observe | — | — | — | — | — |
| 11 | navigate | — | — | — | — | — |
| 12 | finish | — | — | — | — | — |

---

### live_gitlab_new_project_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=14 calls=15 | tokens(out=2116 in=116131 reason=976 nano_aiu=5530580000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | new project | — | — | — | — |
| 2 | observe | create | — | — | — | — |
| 3 | observe | — | — | — | — | — |
| 4 | observe | + | — | — | — | — |
| 5 | click | Home | — | — | — | — |
| 6 | click | gitlab.com | — | — | — | — |
| 7 | navigate | — | — | — | — | — |
| 8 | observe | project | — | — | — | — |
| 9 | read | page content | — | — | — | — |
| 10 | observe | Sign in | — | — | — | — |
| 11 | click | Sign in | — | — | — | — |
| 12 | observe | — | — | — | — | — |
| 13 | navigate | — | — | — | — | — |
| 14 | finish | — | — | — | — | — |

---

### live_arxiv_account_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=16 calls=17 | tokens(out=3842 in=151548 reason=2303 nano_aiu=6274165000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | account | — | — | — | — |
| 2 | observe | user | — | — | — | — |
| 3 | observe | — | — | — | — | — |
| 4 | read | logged in status | — | — | — | — |
| 5 | click | Login | — | — | — | — |
| 6 | observe | — | — | — | — | — |
| 7 | observe | User menu | — | — | — | — |
| 8 | read | login account manage submissions | — | — | — | — |
| 9 | click | Accounts v1.1.0 | — | — | — | — |
| 10 | navigate | — | — | — | — | — |
| 11 | navigate | — | — | — | — | — |
| 12 | observe | — | — | — | — | — |
| 13 | verify | — | — | — | — | — |
| 14 | navigate | — | — | — | — | — |
| 15 | read | user profile account logged | — | — | — | — |
| 16 | finish | — | — | — | — | — |

---

### live_bitbucket_account_abstain — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=False` | steps=0 calls=0 | tokens(out=0 in=0 reason=0 nano_aiu=0.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|

---

### live_wikipedia_decoy_mercury_planet — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=17 calls=17 | tokens(out=2286 in=181571 reason=774 nano_aiu=6427875000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | read | page | — | — | — | — |
| 3 | fill | Search Wikipedia | Mercury planet | — | — | — |
| 4 | click | Search | — | — | — | — |
| 5 | read | Mercury planet | — | — | — | — |
| 6 | click | Mercury (planet) | — | — | — | — |
| 7 | observe | Mercury planet | — | — | — | — |
| 8 | click | Mercury (planet) | — | — | — | — |
| 9 | read | page | — | — | — | — |
| 10 | observe | Mercury | — | — | — | — |
| 11 | navigate | — | — | — | — | — |
| 12 | verify | — | — | — | — | — |
| 13 | read | Mercury planet smallest Sun | — | — | — | — |
| 14 | verify | — | — | — | — | — |
| 15 | read | Mercury smallest closest Sun planet Solar System | — | — | — | — |
| 16 | read | Mercury is the smallest and innermost planet | — | — | — | — |
| 17 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_python_snake — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=9 calls=8 | tokens(out=1168 in=61712 reason=516 nano_aiu=3140535000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | title | — | — | — | — |
| 2 | observe | search | — | — | — | — |
| 3 | fill | Search Wikipedia | Python snake | — | — | — |
| 4 | click | Search | — | — | — | — |
| 5 | observe | Python | — | — | — | — |
| 6 | click | Python (genus) | — | — | — | — |
| 7 | read | Python genus snake | — | — | — | — |
| 8 | verify | — | — | — | — | — |
| 9 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_java_proglang — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=14 calls=15 | tokens(out=2133 in=135091 reason=879 nano_aiu=4613330000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page content | — | — | — | — |
| 2 | observe | search | — | — | — | — |
| 3 | click | Search Wikipedia | — | — | — | — |
| 4 | fill | Search Wikipedia | Java programming language | — | — | — |
| 5 | click | Search | — | — | — | — |
| 6 | read | page content | — | — | — | — |
| 7 | click | Java (programming language) | — | — | — | — |
| 8 | observe | Java programming language | — | — | — | — |
| 9 | click | Java (programming language) | — | — | — | — |
| 10 | read | Java programming language article | — | — | — | — |
| 11 | observe | Java is a high-level | — | — | — | — |
| 12 | navigate | — | — | — | — | — |
| 13 | verify | — | — | — | — | — |
| 14 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_phoenix_city — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=13 calls=14 | tokens(out=1780 in=123753 reason=762 nano_aiu=3515420000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | current page | — | — | — | — |
| 2 | observe | search | — | — | — | — |
| 3 | fill | Search Wikipedia | Phoenix Arizona | — | — | — |
| 4 | click | Search | — | — | — | — |
| 5 | read | search results | — | — | — | — |
| 6 | click | Phoenix, Arizona | — | — | — | — |
| 7 | observe | Phoenix, Arizona | — | — | — | — |
| 8 | click | Phoenix, Arizona | — | — | — | — |
| 9 | read | page | — | — | — | — |
| 10 | navigate | — | — | — | — | — |
| 11 | read | Phoenix Arizona city capital | — | — | — | — |
| 12 | verify | — | — | — | — | — |
| 13 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_apple_company — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=13 calls=12 | tokens(out=1806 in=115584 reason=836 nano_aiu=4377480000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page content | — | — | — | — |
| 2 | observe | search | — | — | — | — |
| 3 | click | Search Wikipedia | — | — | — | — |
| 4 | fill | Search Wikipedia | Apple Inc. | — | — | — |
| 5 | click | Search | — | — | — | — |
| 6 | read | Apple Inc. | — | — | — | — |
| 7 | observe | Apple Inc. | — | — | — | — |
| 8 | click | Apple Inc. | — | — | — | — |
| 9 | observe | link Apple Inc. | — | — | — | — |
| 10 | read | first result Apple Inc. | — | — | — | — |
| 11 | navigate | — | — | — | — | — |
| 12 | verify | — | — | — | — | — |
| 13 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_turkey_bird — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=9 calls=9 | tokens(out=1397 in=66976 reason=796 nano_aiu=3856150000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | turkey bird | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | click | Search | — | — | — | — |
| 5 | observe | turkey | — | — | — | — |
| 6 | click | Turkey (bird) | — | — | — | — |
| 7 | read | genus Meleagris | — | — | — | — |
| 8 | verify | — | — | — | — | — |
| 9 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_saturn_god — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=9 calls=10 | tokens(out=1512 in=83781 reason=807 nano_aiu=4305885000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | Saturn god | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | read | Saturn | — | — | — | — |
| 5 | click | Saturn (mythology) | — | — | — | — |
| 6 | verify | — | — | — | — | — |
| 7 | read | agriculture time Roman god | — | — | — | — |
| 8 | verify | — | — | — | — | — |
| 9 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_amazon_rainforest — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=12 calls=13 | tokens(out=1894 in=108522 reason=745 nano_aiu=4821410000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | Amazon rainforest | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | observe | Amazon rainforest | — | — | — | — |
| 5 | click | Amazon rainforest | — | — | — | — |
| 6 | click | Amazon Rainforest | — | — | — | — |
| 7 | observe | — | — | — | — | — |
| 8 | read | Amazon rainforest | — | — | — | — |
| 9 | observe | Amazon rainforest moist broadleaf tropical | — | — | — | — |
| 10 | navigate | — | — | — | — | — |
| 11 | verify | — | — | — | — | — |
| 12 | finish | — | — | — | — | — |

---

### live_wikipedia_signup_captcha_abstain — AUDIT: BLOCKED — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=4 calls=5 | tokens(out=548 in=31604 reason=366 nano_aiu=2854140000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | sign up account create | — | — | — | — |
| 2 | click | Create account | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### internet_form_auth_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=810 in=47113 reason=429 nano_aiu=3313540000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page content | — | — | — | — |
| 2 | click | Form Authentication | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | read | page content | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### internet_login_page_reached — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=830 in=48484 reason=485 nano_aiu=2473920000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | login | — | — | — | — |
| 2 | observe | — | — | — | — | — |
| 3 | read | login | — | — | — | — |
| 4 | click | Form Authentication | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### books_open_light_in_attic — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=5 calls=6 | tokens(out=893 in=42905 reason=475 nano_aiu=2566045000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | books | — | — | — | — |
| 2 | observe | A Light in the | — | — | — | — |
| 3 | click | A Light in the ... | — | — | — | — |
| 4 | verify | — | — | — | — | — |
| 5 | finish | — | — | — | — | — |

---

### books_open_travel_category — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=545 in=31148 reason=247 nano_aiu=2087610000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Travel | — | — | — | — |
| 2 | click | Travel | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### books_price_visible — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=991 in=54131 reason=568 nano_aiu=4406155000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | A Light in the | — | — | — | — |
| 2 | observe | A Light in the ... | — | — | — | — |
| 3 | click | A Light in the ... | — | — | — | — |
| 4 | read | price | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### quotes_open_einstein_author — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=16 calls=17 | tokens(out=3150 in=146410 reason=1739 nano_aiu=4307460000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page | — | — | — | — |
| 2 | observe | Albert Einstein | — | — | — | — |
| 3 | observe | about | — | — | — | — |
| 4 | observe | — | — | — | — | — |
| 5 | click | (about) | — | — | — | — |
| 6 | observe | Authors | — | — | — | — |
| 7 | read | navigation menu | — | — | — | — |
| 8 | observe | Top 10 | — | — | — | — |
| 9 | observe | Einstein | — | — | — | — |
| 10 | read | author | — | — | — | — |
| 11 | click | Albert Einstein (about) | — | — | — | — |
| 12 | click | The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking. | — | — | — | — |
| 13 | navigate | — | — | — | — | — |
| 14 | navigate | — | — | — | — | — |
| 15 | verify | — | — | — | — | — |
| 16 | finish | — | — | — | — | — |

---

### quotes_open_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=491 in=31560 reason=365 nano_aiu=3518100000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | login | — | — | — | — |
| 2 | click | Login | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### synonym_label_signin_vs_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=748 in=44963 reason=311 nano_aiu=3867845000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Sign In | — | — | — | — |
| 2 | observe | — | — | — | — | — |
| 3 | click | Log in | — | — | — | — |
| 4 | read | SUBMITTED | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---
