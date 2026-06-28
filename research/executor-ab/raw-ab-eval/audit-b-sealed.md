# Audit Trace — per-task evidence (human-readable, not a metric)

Generated **2026-06-28 02:59 UTC** by `eval.audit` from the executor's event stream (no LLM, no network in the audit itself).

- **attribution_coverage = 1.000** (fraction of FAILING tasks deterministically tagged plan-time/ground-time — 1.0 by construction)
- flag tally: ABSTAIN=5, OK=15
- Tokens are reported for cost transparency only — never minimized (abstaining more to lower tokens would game the metric and is not done).

---

### live_scrapethissite_goto_simple — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=528 in=30096 reason=282 nano_aiu=3308455000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Countries of the World: A Simple Example | — | — | — | — |
| 2 | click | Countries of the World: A Simple Example | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_scrapethissite_goto_forms — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=5 | tokens(out=481 in=29882 reason=210 nano_aiu=2672255000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Hockey Teams: Forms, Searching and Pagination | — | — | — | — |
| 2 | click | Hockey Teams: Forms, Searching and Pagination | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_scrapethissite_search_boston — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=8 calls=9 | tokens(out=1187 in=60776 reason=573 nano_aiu=3517620000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Search for Teams | — | — | — | — |
| 2 | read | page content | — | — | — | — |
| 3 | click | Hockey Teams: Forms, Searching and Pagination | — | — | — | — |
| 4 | observe | Search for Teams | — | — | — | — |
| 5 | fill | Search for Teams: | Boston | — | — | — |
| 6 | click | Search | — | — | — | — |
| 7 | verify | — | — | — | — | — |
| 8 | finish | — | — | — | — | — |

---

### live_scrapethissite_forms_page2 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=9 calls=10 | tokens(out=1101 in=67243 reason=616 nano_aiu=2812785000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | pagination | — | — | — | — |
| 2 | observe | next page | — | — | — | — |
| 3 | observe | page | — | — | — | — |
| 4 | read | page | — | — | — | — |
| 5 | click | Hockey Teams: Forms, Searching and Pagination | — | — | — | — |
| 6 | observe | 2 | — | — | — | — |
| 7 | click | 2 | — | — | — | — |
| 8 | verify | — | — | — | — | — |
| 9 | finish | — | — | — | — | — |

---

### live_rfceditor_open_http11 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=9 calls=10 | tokens(out=1218 in=68332 reason=433 nano_aiu=4425105000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | RFC 2616 | — | — | — | — |
| 2 | fill | Find an RFC (number, subseries, title, author, etc.) | 2616 | — | — | — |
| 3 | observe | submit | — | — | — | — |
| 4 | click | Submit search | — | — | — | — |
| 5 | observe | RFC 2616 | — | — | — | — |
| 6 | read | RFC 2616 | — | — | — | — |
| 7 | navigate | — | — | — | — | — |
| 8 | verify | — | — | — | — | — |
| 9 | finish | — | — | — | — | — |

---

### live_rfceditor_title_rfc8259 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=13 calls=13 | tokens(out=2286 in=113750 reason=1141 nano_aiu=5217965000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page content | — | — | — | — |
| 2 | observe | search | — | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | observe | RFC 8259 | — | — | — | — |
| 5 | observe | input search field | — | — | — | — |
| 6 | fill | Search | 8259 | — | — | — |
| 7 | click | Submit the search query | — | — | — | — |
| 8 | read | RFC 8259 | — | — | — | — |
| 9 | observe | RFC 8259 | — | — | — | — |
| 10 | navigate | — | — | — | — | — |
| 11 | read | title RFC 8259 | — | — | — | — |
| 12 | verify | — | — | — | — | — |
| 13 | finish | — | — | — | — | — |

---

### live_rfceditor_open_ip — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=12 calls=12 | tokens(out=1691 in=97301 reason=744 nano_aiu=5228775000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | RFC 791 | — | — | — | — |
| 2 | read | page content | — | — | — | — |
| 3 | fill | Find an RFC (number, subseries, title, author, etc.) | 791 | — | — | — |
| 4 | observe | search button submit | — | — | — | — |
| 5 | click | Submit search | — | — | — | — |
| 6 | observe | RFC 791 | — | — | — | — |
| 7 | click | RFC 791: | — | — | — | — |
| 8 | read | RFC 791 | — | — | — | — |
| 9 | click | RFC 791: STD 5: Internet Protocol | — | — | — | — |
| 10 | navigate | — | — | — | — | — |
| 11 | verify | — | — | — | — | — |
| 12 | finish | — | — | — | — | — |

---

### live_rfceditor_title_rfc1149 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=12 calls=13 | tokens(out=1841 in=96817 reason=692 nano_aiu=4410565000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | RFC search | — | — | — | — |
| 2 | fill | Find an RFC (number, subseries, title, author, etc.) | 1149 | — | — | — |
| 3 | click | Submit search | — | — | — | — |
| 4 | observe | 1149 | — | — | — | — |
| 5 | click | RFC 1149: | — | — | — | — |
| 6 | read | RFC 1149 | — | — | — | — |
| 7 | observe | RFC 1149: | — | — | — | — |
| 8 | click | RFC 1149: | — | — | — | — |
| 9 | navigate | — | — | — | — | — |
| 10 | read | title | — | — | — | — |
| 11 | verify | — | — | — | — | — |
| 12 | finish | — | — | — | — | — |

---

### live_rfceditor_title_rfc3986 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=13 calls=14 | tokens(out=2131 in=117216 reason=821 nano_aiu=4323235000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page content | — | — | — | — |
| 2 | observe | search | — | — | — | — |
| 3 | click | Search | — | — | — | — |
| 4 | observe | RFC number | — | — | — | — |
| 5 | observe | search input | — | — | — | — |
| 6 | fill | Search | RFC 3986 | — | — | — |
| 7 | click | Submit the search query | — | — | — | — |
| 8 | read | RFC 3986 | — | — | — | — |
| 9 | observe | RFC 3986 | — | — | — | — |
| 10 | navigate | — | — | — | — | — |
| 11 | read | RFC 3986 title | — | — | — | — |
| 12 | verify | — | — | — | — | — |
| 13 | finish | — | — | — | — | — |

---

### live_rfceditor_title_rfc2046 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=12 calls=13 | tokens(out=2281 in=95779 reason=1146 nano_aiu=4715280000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | search | — | — | — | — |
| 2 | observe | RFC 2046 | — | — | — | — |
| 3 | fill | Find an RFC (number, subseries, title, author, etc.) | 2046 | — | — | — |
| 4 | click | Submit search | — | — | — | — |
| 5 | observe | 2046 | — | — | — | — |
| 6 | click | RFC 2046: | — | — | — | — |
| 7 | observe | info page | — | — | — | — |
| 8 | navigate | — | — | — | — | — |
| 9 | navigate | — | — | — | — | — |
| 10 | read | title | — | — | — | — |
| 11 | verify | — | — | — | — | — |
| 12 | finish | — | — | — | — | — |

---

### live_webscraper_nav_laptops — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=6 calls=7 | tokens(out=1001 in=44188 reason=641 nano_aiu=3182310000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Computers | — | — | — | — |
| 2 | click | Computers | — | — | — | — |
| 3 | observe | Laptops | — | — | — | — |
| 4 | click | Laptops | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_webscraper_nav_tablets — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=14 calls=15 | tokens(out=2414 in=112675 reason=1070 nano_aiu=5664950000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Computers | — | — | — | — |
| 2 | click | Computers | — | — | — | — |
| 3 | observe | Tablets | — | — | — | — |
| 4 | click | Tablets | — | — | — | — |
| 5 | verify | — | — | — | — | — |
| 6 | observe | Tablets | — | — | — | — |
| 7 | click | Tablets | — | — | — | — |
| 8 | verify | — | — | — | — | — |
| 9 | read | navigation | — | — | — | — |
| 10 | observe | Tablets Phones | — | — | — | — |
| 11 | read | Tablets | — | — | — | — |
| 12 | navigate | — | — | — | — | — |
| 13 | verify | — | — | — | — | — |
| 14 | finish | — | — | — | — | — |

---

### live_webscraper_nav_phones — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=11 calls=12 | tokens(out=1525 in=85193 reason=592 nano_aiu=4004820000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Phones | — | — | — | — |
| 2 | click | Phones | — | — | — | — |
| 3 | observe | Phones | — | — | — | — |
| 4 | click | Phones | — | — | — | — |
| 5 | read | category title | — | — | — | — |
| 6 | observe | Phones | — | — | — | — |
| 7 | click | Phones | — | — | — | — |
| 8 | verify | — | — | — | — | — |
| 9 | navigate | — | — | — | — | — |
| 10 | verify | — | — | — | — | — |
| 11 | finish | — | — | — | — | — |

---

### live_webscraper_open_ipad_mini_product — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=11 calls=12 | tokens(out=1707 in=81088 reason=688 nano_aiu=4831495000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Computers | — | — | — | — |
| 2 | click | Computers | — | — | — | — |
| 3 | observe | Tablets | — | — | — | — |
| 4 | click | Tablets | — | — | — | — |
| 5 | observe | Tablets | — | — | — | — |
| 6 | click | Tablets | — | — | — | — |
| 7 | navigate | — | — | — | — | — |
| 8 | observe | IdeaTab A3500L | — | — | — | — |
| 9 | click | IdeaTab A3500L | — | — | — | — |
| 10 | verify | — | — | — | — | — |
| 11 | finish | — | — | — | — | — |

---

### live_webscraper_nav_phones_touch — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=18 calls=19 | tokens(out=2773 in=159211 reason=1003 nano_aiu=5080120000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | Phones | — | — | — | — |
| 2 | click | Phones | — | — | — | — |
| 3 | observe | Touch | — | — | — | — |
| 4 | read | subcategory | — | — | — | — |
| 5 | observe | Phones | — | — | — | — |
| 6 | click | Phones | — | — | — | — |
| 7 | observe | category | — | — | — | — |
| 8 | read | category | — | — | — | — |
| 9 | observe | Phones | — | — | — | — |
| 10 | click | Phones | — | — | — | — |
| 11 | read | subcategory | — | — | — | — |
| 12 | navigate | — | — | — | — | — |
| 13 | observe | Touch | — | — | — | — |
| 14 | click | Touch | — | — | — | — |
| 15 | read | Touch | — | — | — | — |
| 16 | navigate | — | — | — | — | — |
| 17 | verify | — | — | — | — | — |
| 18 | finish | — | — | — | — | — |

---

### live_reddit_settings_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=6 calls=7 | tokens(out=833 in=42639 reason=431 nano_aiu=3065250000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | verify | — | — | — | — | — |
| 2 | observe | account settings | — | — | — | — |
| 3 | observe | profile menu user | — | — | — | — |
| 4 | observe | settings | — | — | — | — |
| 5 | read | page content | — | — | — | — |
| 6 | finish | — | — | — | — | — |

---

### live_reddit_inbox_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=3 calls=4 | tokens(out=405 in=23372 reason=155 nano_aiu=3123325000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | private message inbox mail messages | — | — | — | — |
| 2 | read | page content | — | — | — | — |
| 3 | finish | — | — | — | — | — |

---

### live_x_notifications_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=5 calls=6 | tokens(out=665 in=37603 reason=485 nano_aiu=3592560000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | notifications | — | — | — | — |
| 2 | observe | Home | — | — | — | — |
| 3 | read | page layout and navigation | — | — | — | — |
| 4 | observe | Continue | — | — | — | — |
| 5 | finish | — | — | — | — | — |

---

### live_codeberg_settings_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=4 calls=4 | tokens(out=436 in=23803 reason=236 nano_aiu=1882275000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | read | page | — | — | — | — |
| 2 | observe | account settings profile menu | — | — | — | — |
| 3 | verify | — | — | — | — | — |
| 4 | finish | — | — | — | — | — |

---

### live_x_messages_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=5 calls=6 | tokens(out=830 in=36874 reason=454 nano_aiu=3013190000.0)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | observe | direct messages | — | — | — | — |
| 2 | observe | messages | — | — | — | — |
| 3 | observe | inbox | — | — | — | — |
| 4 | read | navigation | — | — | — | — |
| 5 | finish | — | — | — | — | — |

---
