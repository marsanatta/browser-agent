# Audit Trace — per-task evidence (human-readable, not a metric)

Generated **2026-06-28 02:42 UTC** by `eval.audit` from the executor's event stream (no LLM, no network in the audit itself).

- **attribution_coverage = 1.000** (fraction of FAILING tasks deterministically tagged plan-time/ground-time — 1.0 by construction)
- flag tally: ABSTAIN=7, BLOCKED=3, HONEST_FAIL=7, OK=50, SILENT_FAILURE=1
- Tokens are reported for cost transparency only — never minimized (abstaining more to lower tokens would game the metric and is not done).

---

### live_wikipedia_helium_retrieval — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=15 calls=16 | tokens(out=2746 in=168909 reason=1322 nano_aiu=6350605000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page | — | — | — | — |
| 2 | observe | search | — | — | — | — |
| 3 | fill | Search Wikipedia | Helium | — | — | — |
| 4 | click | Search | — | — | — | — |
| 5 | read | Helium | — | — | — | — |
| 6 | observe | Helium | — | — | — | — |
| 7 | click | Helium | — | — | — | — |
| 8 | read | page | — | — | — | — |
| 9 | navigate | — | — | — | — | — |
| 10 | read | atomic number | — | — | — | — |
| 11 | read | Helium 2 atomic number symbol He | — | — | — | — |
| 12 | verify | — | — | — | — | — |
| 13 | read | page | — | — | — | — |
| 14 | verify | — | — | — | — | — |
| 15 | finish | — | — | — | — | — |

---

### live_pydocs_json_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=7 calls=8 | tokens(out=991 in=76182 reason=486 nano_aiu=3558395000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Python Standard Library | — | — | — | — |
| 2 | read | Python Standard Library | — | — | — | — |
| 3 | click | Library reference | — | — | — | — |
| 4 | observe | json | — | — | — | — |
| 5 | click | json — JSON encoder and decoder | — | — | — | — |
| 6 | verify | — | — | — | — | — |
| 7 | finish | — | — | — | — | — |

---

### live_google_search_steam — AUDIT: BLOCKED — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=9 calls=10 | tokens(out=1283 in=72265 reason=546 nano_aiu=3928465000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search | steam | — | — | — |
| 3 | click | Google Search | — | — | — | — |
| 4 | observe | search button | — | — | — | — |
| 5 | navigate | — | — | — | — | — |
| 6 | fill | Search | steam | — | — | — |
| 7 | observe | Steam | — | — | — | — |
| 8 | click | steam | — | — | — | — |
| 9 | finish | — | — | — | — | — |

---

### live_wikipedia_signin_synonym — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=7 calls=8 | tokens(out=804 in=49126 reason=360 nano_aiu=3837850000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Sign In | — | — | — | — |
| 2 | observe | login | — | — | — | — |
| 3 | observe | account | — | — | — | — |
| 4 | observe | Log in | — | — | — | — |
| 5 | click | Log in | — | — | — | — |
| 6 | verify | — | — | — | — | — |
| 7 | finish | — | — | — | — | — |

---

### live_wikipedia_search_submit — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=12 calls=13 | tokens(out=1870 in=111744 reason=820 nano_aiu=4869920000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | Oxygen | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | observe | Oxygen | — | — | — | — |
| 5 | click | Oxygen | — | — | — | — |
| 6 | read | Oxygen | — | — | — | — |
| 7 | observe | Oxygen is a chemical element | — | — | — | — |
| 8 | click | Oxygen | — | — | — | — |
| 9 | observe | Search in | — | — | — | — |
| 10 | navigate | — | — | — | — | — |
| 11 | verify | — | — | — | — | — |
| 12 | finish | — | — | — | — | — |

---

### live_wikipedia_autocomplete — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=823 in=46586 reason=394 nano_aiu=3894575000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | Argon | — | — | — |
| 3 | observe | Argon | — | — | — | — |
| 4 | click | Argon
Chemical element with atomic number 18 (Ar) | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_internet_lazyload — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=7 calls=7 | tokens(out=889 in=45088 reason=453 nano_aiu=3185425000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Start | — | — | — | — |
| 2 | read | page content | — | — | — | — |
| 3 | click | Start | — | — | — | — |
| 4 | read | page content | — | — | — | — |
| 5 | read | page content | — | — | — | — |
| 6 | verify | — | — | — | — | — |
| 7 | finish | — | — | — | — | — |

---

### live_internet_modal — AUDIT: SILENT_FAILURE — attribution: plan-time
`nominal=True` `verified=False` `asked=False` | steps=4 calls=5 | tokens(out=671 in=30974 reason=442 nano_aiu=2890415000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page content | — | — | — | — |
| 2 | verify | — | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_internet_iframe — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=6 calls=7 | tokens(out=819 in=43585 reason=384 nano_aiu=3731590000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | iframe | — | — | — | — |
| 2 | click | Rich Text Area | — | — | — | — |
| 3 | observe | text editor | — | — | — | — |
| 4 | read | editor alert message | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_example_more_info_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=773 in=43170 reason=347 nano_aiu=3083635000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | More information | — | — | — | — |
| 2 | observe | More information... | — | — | — | — |
| 3 | read | More information | — | — | — | — |
| 4 | click | Learn more | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_hackernews_newest_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=543 in=29955 reason=272 nano_aiu=2687860000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | new | — | — | — | — |
| 2 | click | new | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_gnu_licenses_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=False` | steps=0 calls=0 | tokens(out=0 in=0 reason=0 nano_aiu=0.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|

---

### live_osm_login_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=441 in=29667 reason=206 nano_aiu=1886045000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Log In | — | — | — | — |
| 2 | click | Log In | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_lobsters_comments_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=424 in=30326 reason=246 nano_aiu=3281385000.0)

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
`nominal=True` `verified=True` `asked=False` | steps=8 calls=9 | tokens(out=1191 in=60566 reason=587 nano_aiu=2908295000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Blog | — | — | — | — |
| 2 | click | Blog | — | — | — | — |
| 3 | observe | Blog | — | — | — | — |
| 4 | read | Blog | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | navigate | — | — | — | — | — |
| 7 | verify | — | — | — | — | — |
| 8 | finish | — | — | — | — | — |

---

### live_archive_login_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=25 calls=26 | tokens(out=3009 in=193803 reason=1132 nano_aiu=6016145000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Log In | — | — | — | — |
| 2 | observe | login | — | — | — | — |
| 3 | read | page | — | — | — | — |
| 4 | navigate | — | — | — | — | — |
| 5 | observe | Log In | — | — | — | — |
| 6 | observe | Sign In | — | — | — | — |
| 7 | observe | account | — | — | — | — |
| 8 | read | page content | — | — | — | — |
| 9 | verify | — | — | — | — | — |
| 10 | observe | user | — | — | — | — |
| 11 | click | Log In | — | — | — | — |
| 12 | click | login | — | — | — | — |
| 13 | click | Sign In | — | — | — | — |
| 14 | click | signin | — | — | — | — |
| 15 | click | Account | — | — | — | — |
| 16 | navigate | — | — | — | — | — |
| 17 | verify | — | — | — | — | — |
| 18 | read | sign | — | — | — | — |
| 19 | observe | archive | — | — | — | — |
| 20 | navigate | — | — | — | — | — |
| 21 | observe | header | — | — | — | — |
| 22 | click | sign in | — | — | — | — |
| 23 | verify | — | — | — | — | — |
| 24 | click | All | — | — | — | — |
| 25 | finish | — | — | — | — | — |

---

### live_govuk_help_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=614 in=30079 reason=365 nano_aiu=1358195000.0)

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
`nominal=True` `verified=True` `asked=False` | steps=9 calls=10 | tokens(out=1058 in=64671 reason=444 nano_aiu=3549555000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Help | — | — | — | — |
| 2 | click | Help | — | — | — | — |
| 3 | click | Help Pages | — | — | — | — |
| 4 | observe | navigation menu | — | — | — | — |
| 5 | click | Open navigation menu | — | — | — | — |
| 6 | read | Help | — | — | — | — |
| 7 | navigate | — | — | — | — | — |
| 8 | verify | — | — | — | — | — |
| 9 | finish | — | — | — | — | — |

---

### live_stackoverflow_questions_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=6 calls=7 | tokens(out=612 in=43774 reason=488 nano_aiu=3622725000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Questions | — | — | — | — |
| 2 | observe | navigation | — | — | — | — |
| 3 | read | page | — | — | — | — |
| 4 | verify | — | — | — | — | — |
| 5 | observe | click | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_internet_status_code_200 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=653 in=30250 reason=351 nano_aiu=2110435000.0)

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
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=738 in=31374 reason=369 nano_aiu=2890515000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Challenging DOM | — | — | — | — |
| 2 | read | page content | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_books_sapiens_price — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=5 calls=6 | tokens(out=766 in=40875 reason=314 nano_aiu=3134065000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page title and structure | — | — | — | — |
| 2 | click | Sapiens: A Brief History ... | — | — | — | — |
| 3 | read | price | — | — | — | — |
| 4 | verify | — | — | — | — | — |
| 5 | finish | — | — | — | — | — |

---

### live_books_open_mystery_category — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=633 in=30238 reason=372 nano_aiu=2793995000.0)

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
`nominal=True` `verified=True` `asked=False` | steps=7 calls=7 | tokens(out=914 in=47738 reason=438 nano_aiu=4688785000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | read | page content | — | — | — | — |
| 3 | click | Sapiens: A Brief History ... | — | — | — | — |
| 4 | read | stock | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | verify | — | — | — | — | — |
| 7 | finish | — | — | — | — | — |

---

### live_books_grand_design_price — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=556 in=30695 reason=273 nano_aiu=3475595000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | page | — | — | — | — |
| 2 | read | main content | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_books_dune_price — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=8 calls=9 | tokens(out=1023 in=59991 reason=487 nano_aiu=2775490000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Science Fiction | — | — | — | — |
| 2 | click | Science Fiction | — | — | — | — |
| 3 | observe | Dune | — | — | — | — |
| 4 | click | Dune (Dune #1) | — | — | — | — |
| 5 | observe | Dune | — | — | — | — |
| 6 | read | Dune price | — | — | — | — |
| 7 | verify | — | — | — | — | — |
| 8 | finish | — | — | — | — | — |

---

### live_books_page2_pagination — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=926 in=46425 reason=594 nano_aiu=3382115000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | page | — | — | — | — |
| 2 | read | page content | — | — | — | — |
| 3 | observe | next page | — | — | — | — |
| 4 | click | next | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_wikipedia_oxygen_search — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=10 calls=9 | tokens(out=1339 in=64713 reason=600 nano_aiu=3979560000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page | — | — | — | — |
| 2 | observe | search | — | — | — | — |
| 3 | click | Search Wikipedia | — | — | — | — |
| 4 | fill | Special:Search | Oxygen | — | — | — |
| 5 | click | Search | — | — | — | — |
| 6 | observe | search button | — | — | — | — |
| 7 | navigate | — | — | — | — | — |
| 8 | verify | — | — | — | — | — |
| 9 | read | Oxygen element chemical | — | — | — | — |
| 10 | finish | — | — | — | — | — |

---

### live_wikipedia_periodic_table_nav — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=26 calls=28 | tokens(out=4980 in=315829 reason=2331 nano_aiu=9758545000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Oxygen | — | — | — | — |
| 2 | read | page content | — | — | — | — |
| 3 | observe | search | — | — | — | — |
| 4 | fill | Search Wikipedia | Oxygen | — | — | — |
| 5 | click | Search | — | — | — | — |
| 6 | observe | Oxygen | — | — | — | — |
| 7 | click | Oxygen | — | — | — | — |
| 8 | read | Oxygen article | — | — | — | — |
| 9 | observe | Oxygen is a chemical element | — | — | — | — |
| 10 | click | Oxygen | — | — | — | — |
| 11 | navigate | — | — | — | — | — |
| 12 | observe | periodic table | — | — | — | — |
| 13 | click | periodic table | — | — | — | — |
| 14 | navigate | — | — | — | — | — |
| 15 | verify | — | — | — | — | — |
| 16 | read | periodic table | — | — | — | — |
| 17 | verify | — | — | — | — | — |
| 18 | navigate | — | — | — | — | — |
| 19 | read | periodic table | — | — | — | — |
| 20 | observe | periodic | — | — | — | — |
| 21 | click | periodic table | — | — | — | — |
| 22 | click | Period | — | — | — | — |
| 23 | navigate | — | — | — | — | — |
| 24 | observe | chalcogen | — | — | — | — |
| 25 | observe | element table | — | — | — | — |
| 26 | finish | — | — | — | — | — |

---

### live_wikipedia_einstein_body_text — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=15 calls=16 | tokens(out=2370 in=150167 reason=1039 nano_aiu=5601845000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | E=mc^2 | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | read | search results | — | — | — | — |
| 5 | observe | Albert Einstein | — | — | — | — |
| 6 | fill | Search Wikipedia | Albert Einstein | — | — | — |
| 7 | click | Search | — | — | — | — |
| 8 | read | search results | — | — | — | — |
| 9 | observe | Albert Einstein | — | — | — | — |
| 10 | click | Albert Einstein | — | — | — | — |
| 11 | read | Albert Einstein | — | — | — | — |
| 12 | observe | Results 1 | — | — | — | — |
| 13 | navigate | — | — | — | — | — |
| 14 | verify | — | — | — | — | — |
| 15 | finish | — | — | — | — | — |

---

### live_pydocs_tutorial_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=5 calls=6 | tokens(out=672 in=41733 reason=377 nano_aiu=3333925000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Python Tutorial | — | — | — | — |
| 2 | read | The Python Tutorial | — | — | — | — |
| 3 | click | Tutorial | — | — | — | — |
| 4 | verify | — | — | — | — | — |
| 5 | finish | — | — | — | — | — |

---

### live_hackernews_show_then_ask — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=7 calls=7 | tokens(out=1038 in=45174 reason=622 nano_aiu=4039130000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Show HN | — | — | — | — |
| 2 | observe | Ask HN | — | — | — | — |
| 3 | click | show | — | — | — | — |
| 4 | verify | — | — | — | — | — |
| 5 | click | ask | — | — | — | — |
| 6 | verify | — | — | — | — | — |
| 7 | finish | — | — | — | — | — |

---

### live_mdn_html_input — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=13 calls=14 | tokens(out=2109 in=117293 reason=775 nano_aiu=5995965000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page content | — | — | — | — |
| 2 | observe | input element HTML reference documentation | — | — | — | — |
| 3 | click | Elements | — | — | — | — |
| 4 | click | HTML: Markup language | — | — | — | — |
| 5 | navigate | — | — | — | — | — |
| 6 | verify | — | — | — | — | — |
| 7 | read | page title heading | — | — | — | — |
| 8 | verify | — | — | — | — | — |
| 9 | observe | <input> HTML element reference | — | — | — | — |
| 10 | verify | — | — | — | — | — |
| 11 | read | <input> heading title | — | — | — | — |
| 12 | verify | — | — | — | — | — |
| 13 | finish | — | — | — | — | — |

---

### live_mdn_css_flex — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=16 calls=17 | tokens(out=2290 in=136679 reason=908 nano_aiu=5281445000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page | — | — | — | — |
| 2 | observe | search | — | — | — | — |
| 3 | click | Skip to search | — | — | — | — |
| 4 | observe | search box input | — | — | — | — |
| 5 | click | Flexbox | — | — | — | — |
| 6 | observe | CSS | — | — | — | — |
| 7 | click | See all CSS references | — | — | — | — |
| 8 | navigate | — | — | — | — | — |
| 9 | verify | — | — | — | — | — |
| 10 | read | page | — | — | — | — |
| 11 | verify | — | — | — | — | — |
| 12 | verify | — | — | — | — | — |
| 13 | verify | — | — | — | — | — |
| 14 | verify | — | — | — | — | — |
| 15 | read | flex CSS property | — | — | — | — |
| 16 | finish | — | — | — | — | — |

---

### live_govuk_bank_holidays — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=17 calls=18 | tokens(out=2325 in=144359 reason=990 nano_aiu=5362590000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | bank holidays | — | — | — | — |
| 2 | observe | search | — | — | — | — |
| 3 | click | Search GOV.UK | — | — | — | — |
| 4 | fill | Search GOV.UK | bank holidays | — | — | — |
| 5 | read | main content | — | — | — | — |
| 6 | click | Search | — | — | — | — |
| 7 | fill | Search | bank holidays | — | — | — |
| 8 | observe | Search | — | — | — | — |
| 9 | click | bank holidays | — | — | — | — |
| 10 | read | bank holidays | — | — | — | — |
| 11 | click | UK bank holidays | — | — | — | — |
| 12 | verify | — | — | — | — | — |
| 13 | read | bank holidays | — | — | — | — |
| 14 | verify | — | — | — | — | — |
| 15 | verify | — | — | — | — | — |
| 16 | verify | — | — | — | — | — |
| 17 | finish | — | — | — | — | — |

---

### live_govuk_vat_rates — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=26 calls=28 | tokens(out=3944 in=283903 reason=1327 nano_aiu=8140860000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | VAT rates | — | — | — | — |
| 2 | read | main content | — | — | — | — |
| 3 | observe | Search | — | — | — | — |
| 4 | click | Search GOV.UK | — | — | — | — |
| 5 | click | Search | — | — | — | — |
| 6 | observe | search input | — | — | — | — |
| 7 | fill | Search | VAT rates | — | — | — |
| 8 | click | Search GOV.UK | — | — | — | — |
| 9 | observe | VAT | — | — | — | — |
| 10 | read | VAT | — | — | — | — |
| 11 | observe | button | — | — | — | — |
| 12 | navigate | — | — | — | — | — |
| 13 | read | guidance VAT rates standard reduced zero | — | — | — | — |
| 14 | click | VAT rates | — | — | — | — |
| 15 | click | Current VAT rates - standard 20% and rates for reduced rate and zero-rated items | — | — | — | — |
| 16 | navigate | — | — | — | — | — |
| 17 | read | VAT rates standard reduced zero what they apply | — | — | — | — |
| 18 | navigate | — | — | — | — | — |
| 19 | observe | link | — | — | — | — |
| 20 | read | link | — | — | — | — |
| 21 | observe | VAT rates on different goods and services | — | — | — | — |
| 22 | click | Money and tax | — | — | — | — |
| 23 | read | VAT | — | — | — | — |
| 24 | click | VAT | — | — | — | — |
| 25 | read | standard reduced zero rates | — | — | — | — |
| 26 | finish | — | — | — | — | — |

---

### live_govuk_min_wage — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=17 calls=18 | tokens(out=2605 in=144877 reason=920 nano_aiu=5624840000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | main content | — | — | — | — |
| 2 | observe | search | — | — | — | — |
| 3 | click | Search GOV.UK | — | — | — | — |
| 4 | click | Search | — | — | — | — |
| 5 | fill | Search GOV.UK | National Minimum Wage | — | — | — |
| 6 | observe | wage | — | — | — | — |
| 7 | observe | business | — | — | — | — |
| 8 | click | Business and self-employed | — | — | — | — |
| 9 | read | page title | — | — | — | — |
| 10 | navigate | — | — | — | — | — |
| 11 | read | main content | — | — | — | — |
| 12 | click | Employ people | — | — | — | — |
| 13 | read | main content | — | — | — | — |
| 14 | click | National Minimum Wage and National Living Wage rates | — | — | — | — |
| 15 | read | National Minimum Wage National Living Wage rates | — | — | — | — |
| 16 | verify | — | — | — | — | — |
| 17 | finish | — | — | — | — | — |

---

### live_govuk_check_uk_visa — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=16 calls=12 | tokens(out=1932 in=99335 reason=712 nano_aiu=4698225000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page content | — | — | — | — |
| 2 | observe | visa | — | — | — | — |
| 3 | click | Visas and immigration | — | — | — | — |
| 4 | observe | visa check | — | — | — | — |
| 5 | read | page heading | — | — | — | — |
| 6 | click | Visas and immigration | — | — | — | — |
| 7 | read | page content | — | — | — | — |
| 8 | observe | check visa requirements | — | — | — | — |
| 9 | observe | Check if you need | — | — | — | — |
| 10 | click | What you need to do | — | — | — | — |
| 11 | read | page content | — | — | — | — |
| 12 | observe | check if you need visa | — | — | — | — |
| 13 | click | Check if you need a UK visa | — | — | — | — |
| 14 | verify | — | — | — | — | — |
| 15 | read | page heading and purpose | — | — | — | — |
| 16 | finish | — | — | — | — | — |

---

### live_govuk_driving_licences — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=8 calls=9 | tokens(out=1123 in=63330 reason=471 nano_aiu=3640510000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Driving and transport | — | — | — | — |
| 2 | click | Driving and transport | — | — | — | — |
| 3 | observe | Driving and transport | — | — | — | — |
| 4 | click | Driving and transport | — | — | — | — |
| 5 | observe | Driving licences | — | — | — | — |
| 6 | click | Driving licences | — | — | — | — |
| 7 | verify | — | — | — | — | — |
| 8 | finish | — | — | — | — | — |

---

### live_wikipedia_jupiter — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=13 calls=13 | tokens(out=1608 in=104648 reason=819 nano_aiu=3723295000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Wikipedia | — | — | — | — |
| 2 | read | page content | — | — | — | — |
| 3 | click | Search Wikipedia | — | — | — | — |
| 4 | fill | Search Wikipedia | Jupiter | — | — | — |
| 5 | observe | Search | — | — | — | — |
| 6 | click | Fifth planet from the Sun | — | — | — | — |
| 7 | click | Jupiter | — | — | — | — |
| 8 | click | Search | — | — | — | — |
| 9 | observe | Jupiter planet | — | — | — | — |
| 10 | click | Jupiter | — | — | — | — |
| 11 | navigate | — | — | — | — | — |
| 12 | verify | — | — | — | — | — |
| 13 | finish | — | — | — | — | — |

---

### live_books_fiction_page2 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=842 in=43318 reason=308 nano_aiu=3080745000.0)

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
`nominal=True` `verified=True` `asked=False` | steps=15 calls=15 | tokens(out=2017 in=118116 reason=792 nano_aiu=4006160000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | read | page content | — | — | — | — |
| 3 | fill | Search term or terms | Attention Is All You Need | — | — | — |
| 4 | click | Search | — | — | — | — |
| 5 | read | Attention Is All You Need | — | — | — | — |
| 6 | observe | paper title result | — | — | — | — |
| 7 | observe | Search in all archives | — | — | — | — |
| 8 | click | Search in all archives. | — | — | — | — |
| 9 | fill | Search term or terms | Attention Is All You Need | — | — | — |
| 10 | click | Search | — | — | — | — |
| 11 | click | Advanced Search | — | — | — | — |
| 12 | navigate | — | — | — | — | — |
| 13 | verify | — | — | — | — | — |
| 14 | verify | — | — | — | — | — |
| 15 | finish | — | — | — | — | — |

---

### live_wikipedia_preferences_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=11 calls=12 | tokens(out=1785 in=86423 reason=971 nano_aiu=3506660000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Preferences | — | — | — | — |
| 2 | read | page content | — | — | — | — |
| 3 | observe | account | — | — | — | — |
| 4 | observe | user | — | — | — | — |
| 5 | observe | settings | — | — | — | — |
| 6 | observe | Tools | — | — | — | — |
| 7 | click | Personal tools | — | — | — | — |
| 8 | observe | Preferences | — | — | — | — |
| 9 | observe | Log in | — | — | — | — |
| 10 | navigate | — | — | — | — | — |
| 11 | finish | — | — | — | — | — |

---

### live_wikipedia_watchlist_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=11 calls=12 | tokens(out=1628 in=79862 reason=744 nano_aiu=5475305000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | watchlist | — | — | — | — |
| 2 | observe | menu | — | — | — | — |
| 3 | click | Main menu | — | — | — | — |
| 4 | observe | account | — | — | — | — |
| 5 | observe | personal | — | — | — | — |
| 6 | click | Personal tools | — | — | — | — |
| 7 | observe | watchlist | — | — | — | — |
| 8 | navigate | — | — | — | — | — |
| 9 | verify | — | — | — | — | — |
| 10 | read | page content | — | — | — | — |
| 11 | finish | — | — | — | — | — |

---

### live_github_settings_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=7 calls=7 | tokens(out=801 in=46522 reason=465 nano_aiu=2525745000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | profile settings account | — | — | — | — |
| 2 | observe | settings account profile | — | — | — | — |
| 3 | observe | Sign in | — | — | — | — |
| 4 | click | Sign in | — | — | — | — |
| 5 | observe | password username login | — | — | — | — |
| 6 | navigate | — | — | — | — | — |
| 7 | finish | — | — | — | — | — |

---

### live_github_notifications_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=7 calls=8 | tokens(out=1473 in=54406 reason=980 nano_aiu=4275725000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | notifications | — | — | — | — |
| 2 | observe | inbox | — | — | — | — |
| 3 | observe | bell | — | — | — | — |
| 4 | read | notification | — | — | — | — |
| 5 | observe | Sign in | — | — | — | — |
| 6 | click | Sign in | — | — | — | — |
| 7 | finish | — | — | — | — | — |

---

### live_github_new_repo_abstain — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=False` | steps=25 calls=19 | tokens(out=5683 in=209379 reason=3581 nano_aiu=8364545000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | new repository | — | — | — | — |
| 2 | observe | create repository | — | — | — | — |
| 3 | observe | repositories | — | — | — | — |
| 4 | observe | New | — | — | — | — |
| 5 | read | page content | — | — | — | — |
| 6 | click | Sign in | — | — | — | — |
| 7 | read | page content | — | — | — | — |
| 8 | navigate | — | — | — | — | — |
| 9 | navigate | — | — | — | — | — |
| 10 | read | page content | — | — | — | — |
| 11 | observe | menu | — | — | — | — |
| 12 | observe | + | — | — | — | — |
| 13 | observe | profile | — | — | — | — |
| 14 | observe | create | — | — | — | — |
| 15 | observe | repo | — | — | — | — |
| 16 | verify | — | — | — | — | — |
| 17 | observe | account | — | — | — | — |
| 18 | observe | user | — | — | — | — |
| 19 | navigate | — | — | — | — | — |
| 20 | read | page content | — | — | — | — |
| 21 | verify | — | — | — | — | — |
| 22 | observe | repository | — | — | — | — |
| 23 | observe | demo | — | — | — | — |
| 24 | observe | form | — | — | — | — |
| 25 | observe | name | — | — | — | — |

---

### live_gitlab_profile_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=15 calls=16 | tokens(out=2850 in=137970 reason=1372 nano_aiu=4716685000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | profile settings | — | — | — | — |
| 2 | observe | user account menu | — | — | — | — |
| 3 | read | current page URL | — | — | — | — |
| 4 | observe | Sign in | — | — | — | — |
| 5 | click | Sign in | — | — | — | — |
| 6 | read | login form | — | — | — | — |
| 7 | navigate | — | — | — | — | — |
| 8 | observe | profile | — | — | — | — |
| 9 | click | Main Menu | — | — | — | — |
| 10 | observe | settings | — | — | — | — |
| 11 | navigate | — | — | — | — | — |
| 12 | navigate | — | — | — | — | — |
| 13 | read | page content | — | — | — | — |
| 14 | navigate | — | — | — | — | — |
| 15 | finish | — | — | — | — | — |

---

### live_gitlab_new_project_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=15 calls=16 | tokens(out=2138 in=124821 reason=948 nano_aiu=4218485000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | create new project | — | — | — | — |
| 2 | observe | project | — | — | — | — |
| 3 | read | create | — | — | — | — |
| 4 | observe | button | — | — | — | — |
| 5 | observe | help | — | — | — | — |
| 6 | observe | New | — | — | — | — |
| 7 | observe | Projects | — | — | — | — |
| 8 | observe | link | — | — | — | — |
| 9 | navigate | — | — | — | — | — |
| 10 | observe | new project | — | — | — | — |
| 11 | navigate | — | — | — | — | — |
| 12 | observe | New | — | — | — | — |
| 13 | observe | + | — | — | — | — |
| 14 | navigate | — | — | — | — | — |
| 15 | finish | — | — | — | — | — |

---

### live_arxiv_account_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=11 calls=7 | tokens(out=1423 in=47916 reason=650 nano_aiu=2128485000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | account | — | — | — | — |
| 2 | observe | user | — | — | — | — |
| 3 | observe | submissions | — | — | — | — |
| 4 | observe | login | — | — | — | — |
| 5 | observe | profile | — | — | — | — |
| 6 | read | main navigation | — | — | — | — |
| 7 | click | Login | — | — | — | — |
| 8 | read | login page | — | — | — | — |
| 9 | observe | login form | — | — | — | — |
| 10 | verify | — | — | — | — | — |
| 11 | finish | — | — | — | — | — |

---

### live_bitbucket_account_abstain — AUDIT: BLOCKED — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=9 calls=9 | tokens(out=1391 in=61028 reason=681 nano_aiu=4456595000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | account settings | — | — | — | — |
| 2 | observe | settings menu profile | — | — | — | — |
| 3 | observe | profile avatar user menu | — | — | — | — |
| 4 | read | page content buttons links | — | — | — | — |
| 5 | observe | Sign in | — | — | — | — |
| 6 | click | Sign in | — | — | — | — |
| 7 | observe | email password sign in button | — | — | — | — |
| 8 | navigate | — | — | — | — | — |
| 9 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_mercury_planet — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=17 calls=17 | tokens(out=2584 in=155219 reason=1154 nano_aiu=6122290000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | observe | Mercury | — | — | — | — |
| 3 | fill | Search Wikipedia | Mercury planet | — | — | — |
| 4 | click | Search | — | — | — | — |
| 5 | observe | Mercury | — | — | — | — |
| 6 | click | Mercury (planet) | — | — | — | — |
| 7 | click | Mercury planet | — | — | — | — |
| 8 | click | Mercury | — | — | — | — |
| 9 | read | main heading | — | — | — | — |
| 10 | observe | Mercury (planet) | — | — | — | — |
| 11 | click | Mercury (planet) | — | — | — | — |
| 12 | verify | — | — | — | — | — |
| 13 | read | smallest planet closest to Sun | — | — | — | — |
| 14 | read | closest planet to the Sun | — | — | — | — |
| 15 | read | Mercury | — | — | — | — |
| 16 | verify | — | — | — | — | — |
| 17 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_python_snake — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=9 calls=10 | tokens(out=1200 in=72606 reason=417 nano_aiu=3884880000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page main content | — | — | — | — |
| 2 | observe | search | — | — | — | — |
| 3 | click | Search Wikipedia | — | — | — | — |
| 4 | fill | Search Wikipedia | Python snake | — | — | — |
| 5 | click | Search | — | — | — | — |
| 6 | read | search results | — | — | — | — |
| 7 | click | Python (genus) | — | — | — | — |
| 8 | verify | — | — | — | — | — |
| 9 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_java_proglang — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=11 calls=12 | tokens(out=1500 in=89364 reason=652 nano_aiu=4252735000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | Java programming language | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | observe | Java programming language | — | — | — | — |
| 5 | click | Java (programming language) | — | — | — | — |
| 6 | observe | Java | — | — | — | — |
| 7 | click | Java programming language | — | — | — | — |
| 8 | read | Java | — | — | — | — |
| 9 | navigate | — | — | — | — | — |
| 10 | verify | — | — | — | — | — |
| 11 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_phoenix_city — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=14 calls=15 | tokens(out=2141 in=139900 reason=877 nano_aiu=5396515000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | Phoenix Arizona | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | read | Phoenix Arizona | — | — | — | — |
| 5 | click | Phoenix, Arizona | — | — | — | — |
| 6 | observe | Phoenix, Arizona | — | — | — | — |
| 7 | click | Phoenix, Arizona | — | — | — | — |
| 8 | observe | Phoenix, Arizona capital city | — | — | — | — |
| 9 | navigate | — | — | — | — | — |
| 10 | verify | — | — | — | — | — |
| 11 | read | Phoenix capital Arizona | — | — | — | — |
| 12 | read | Phoenix capital most populous city Arizona | — | — | — | — |
| 13 | verify | — | — | — | — | — |
| 14 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_apple_company — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=11 calls=12 | tokens(out=1993 in=98132 reason=961 nano_aiu=4703295000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | Apple Inc | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | observe | Apple Inc | — | — | — | — |
| 5 | click | Apple Inc. | — | — | — | — |
| 6 | click | Apple Inc | — | — | — | — |
| 7 | observe | search results | — | — | — | — |
| 8 | read | search results Apple Inc technology company | — | — | — | — |
| 9 | navigate | — | — | — | — | — |
| 10 | verify | — | — | — | — | — |
| 11 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_turkey_bird — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=7 calls=8 | tokens(out=1018 in=51396 reason=434 nano_aiu=3365665000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | turkey bird | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | observe | turkey | — | — | — | — |
| 5 | click | Turkey (bird) | — | — | — | — |
| 6 | verify | — | — | — | — | — |
| 7 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_saturn_god — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=8 calls=9 | tokens(out=1069 in=61144 reason=492 nano_aiu=2869065000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | fill | Search Wikipedia | Saturn god | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | observe | Saturn | — | — | — | — |
| 5 | click | Saturn (mythology) | — | — | — | — |
| 6 | read | Saturn Roman god agriculture time | — | — | — | — |
| 7 | verify | — | — | — | — | — |
| 8 | finish | — | — | — | — | — |

---

### live_wikipedia_decoy_amazon_rainforest — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=15 calls=16 | tokens(out=2446 in=149840 reason=1098 nano_aiu=6404300000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Amazon rainforest | — | — | — | — |
| 2 | read | page text | — | — | — | — |
| 3 | observe | search | — | — | — | — |
| 4 | fill | Search Wikipedia | Amazon rainforest | — | — | — |
| 5 | click | Search | — | — | — | — |
| 6 | read | search results | — | — | — | — |
| 7 | observe | Amazon rainforest | — | — | — | — |
| 8 | click | Amazon rainforest | — | — | — | — |
| 9 | read | Amazon rainforest link | — | — | — | — |
| 10 | click | The Amazon rainforest, also called the Amazon jungle, Amazonia, or simply the Amazon, is a moist broadleaf tropical rainforest in the Amazon biome that | — | — | — | — |
| 11 | observe | Amazon rainforest also called jungle | — | — | — | — |
| 12 | click | Amazon rainforest | — | — | — | — |
| 13 | navigate | — | — | — | — | — |
| 14 | verify | — | — | — | — | — |
| 15 | finish | — | — | — | — | — |

---

### live_wikipedia_signup_captcha_abstain — AUDIT: BLOCKED — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=4 calls=5 | tokens(out=573 in=30037 reason=297 nano_aiu=2686405000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | account creation sign-up register | — | — | — | — |
| 2 | click | Create account | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### internet_form_auth_nav — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=880 in=43610 reason=447 nano_aiu=3192760000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Form Authentication | — | — | — | — |
| 2 | click | Form Authentication | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | read | Form Authentication | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### internet_login_page_reached — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=5 calls=6 | tokens(out=531 in=37606 reason=420 nano_aiu=3668330000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | login | — | — | — | — |
| 2 | read | main content | — | — | — | — |
| 3 | click | Form Authentication | — | — | — | — |
| 4 | verify | — | — | — | — | — |
| 5 | finish | — | — | — | — | — |

---

### books_open_light_in_attic — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=711 in=30623 reason=340 nano_aiu=2106965000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | A Light in the | — | — | — | — |
| 2 | click | A Light in the ... | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### books_open_travel_category — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=586 in=30245 reason=443 nano_aiu=3435380000.0)

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
`nominal=True` `verified=True` `asked=False` | steps=5 calls=6 | tokens(out=772 in=38396 reason=407 nano_aiu=2393500000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | A Light in the | — | — | — | — |
| 2 | click | A Light in the ... | — | — | — | — |
| 3 | read | price | — | — | — | — |
| 4 | verify | — | — | — | — | — |
| 5 | finish | — | — | — | — | — |

---

### quotes_open_einstein_author — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=16 calls=17 | tokens(out=2486 in=127895 reason=1090 nano_aiu=5120545000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page content | — | — | — | — |
| 2 | observe | Albert Einstein | — | — | — | — |
| 3 | observe | about | — | — | — | — |
| 4 | click | (about) | — | — | — | — |
| 5 | observe | author | — | — | — | — |
| 6 | observe | Einstein | — | — | — | — |
| 7 | observe | link | — | — | — | — |
| 8 | observe | page | — | — | — | — |
| 9 | observe | menu | — | — | — | — |
| 10 | observe | Authors | — | — | — | — |
| 11 | observe | Top | — | — | — | — |
| 12 | read | all text | — | — | — | — |
| 13 | read | clickable | — | — | — | — |
| 14 | navigate | — | — | — | — | — |
| 15 | verify | — | — | — | — | — |
| 16 | finish | — | — | — | — | — |

---

### quotes_open_login — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=560 in=29678 reason=264 nano_aiu=2671050000.0)

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
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=610 in=42506 reason=272 nano_aiu=3653180000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Sign In | — | — | — | — |
| 2 | read | sign in button | — | — | — | — |
| 3 | observe | Log in | — | — | — | — |
| 4 | click | Log in | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---
