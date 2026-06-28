# Audit Trace — per-task evidence (human-readable, not a metric)

Generated **2026-06-28 04:26 UTC** by `eval.audit` from the executor's event stream (no LLM, no network in the audit itself).

- **attribution_coverage = 1.000** (fraction of FAILING tasks deterministically tagged plan-time/ground-time — 1.0 by construction)
- flag tally: ABSTAIN=6, HONEST_FAIL=6, OK=5, SILENT_FAILURE=3
- Tokens are reported for cost transparency only — never minimized (abstaining more to lower tokens would game the metric and is not done).

---

### live_scrapethissite_goto_simple — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=504 in=14386 reason=409 nano_aiu=1293760000)

plan:
- 1. click "Countries of the World: A Simple Example"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Countries of the World: A Simple Example | — | RESOLVED | CHANGED | — |

---

### live_scrapethissite_goto_forms — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=402 in=14168 reason=325 nano_aiu=454440000)

plan:
- 1. click "Hockey Teams: Forms, Searching and Pagination"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Hockey Teams: Forms, Searching and Pagination | — | RESOLVED | CHANGED | — |

---

### live_scrapethissite_search_boston — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=1 | tokens(out=576 in=14174 reason=407 nano_aiu=542190000)

plan:
- 1. navigate https://scrapethissite.com/pages/forms/
- 2. fill "Search for Teams" = "Boston"
- 3. press "Search for Teams" = "Enter"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | fill | Search for Teams | Boston | RESOLVED | CHANGED | — |
| 3 | press | Search for Teams | Enter | RESOLVED | CHANGED | — |

---

### live_scrapethissite_forms_page2 — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=2 calls=4 | tokens(out=3048 in=56659 reason=1541 nano_aiu=5580415000)

plan:
- 1. click "Hockey Teams: Forms, Searching and Pagination"
- 2. click "2"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Hockey Teams: Forms, Searching and Pagination | — | RESOLVED | CHANGED | — |
| 2 | click | 2 | — | RESOLVED | NO_CHANGE | REGROUND,REGROUND,REGROUND,REGROUND,REPLAN |

---

### live_rfceditor_open_http11 — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=3 calls=5 | tokens(out=2996 in=72493 reason=1846 nano_aiu=6777175000)

plan:
- 1. fill "Find an RFC (number, subseries, title, author, etc.)" = "2616"
- 2. fill "Search" = "2616"
- 3. click "Submit the search query"
- 4. click "RFC 2616:"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Find an RFC (number, subseries, title, author, etc.) | 2616 | RESOLVED | CHANGED | — |
| 2 | fill | Search | 2616 | RESOLVED | NO_CHANGE | REGROUND,REGROUND,REGROUND,REPLAN,STATE_WAIT,STATE_WAIT,STATE_WAIT,STATE_WAIT,REPLAN |

---

### live_rfceditor_title_rfc8259 — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=7 calls=14 | tokens(out=7776 in=206995 reason=5010 nano_aiu=19171515000)

plan:
- 1. fill "Find an RFC (number, subseries, title, author, etc.)" = "8259"
- 2. navigate /info/rfc8259/
- 3. click "RFC 8259"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Find an RFC (number, subseries, title, author, etc.) | 8259 | RESOLVED | CHANGED | — |
| 2 | navigate | — | — | RESOLVED | CHANGED | REGROUND,REGROUND,REGROUND,REPLAN |
| 3 | click | RFC 8259 | — | RESOLVED | NO_CHANGE | REGROUND,REGROUND,REPLAN,REGROUND,REGROUND,REPLAN,WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN,REGROUND,REGROUND,REPLAN |

---

### live_rfceditor_open_ip — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=2019 in=14869 reason=781 nano_aiu=2111635000)

plan:
- 1. navigate https://www.rfc-editor.org/info/rfc791/

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_rfceditor_title_rfc1149 — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=4 calls=7 | tokens(out=4387 in=100567 reason=2569 nano_aiu=9468945000)

plan:
- 1. fill "Find an RFC (number, subseries, title, author, etc.)" = "1149"
- 2. navigate /info/rfc1149/
- 3. click "RFC 1149:"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Find an RFC (number, subseries, title, author, etc.) | 1149 | RESOLVED | CHANGED | — |
| 2 | navigate | — | — | RESOLVED | CHANGED | REGROUND,REGROUND,REGROUND,REPLAN |
| 3 | click | RFC 1149: | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_rfceditor_title_rfc3986 — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=2 calls=4 | tokens(out=3602 in=57863 reason=1693 nano_aiu=6007915000)

plan:
- 1. fill "Find an RFC (number, subseries, title, author, etc.)" = "3986"
- 2. press "Find an RFC (number, subseries, title, author, etc.)" = "Enter"
- 3. click "RFC 3986"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Find an RFC (number, subseries, title, author, etc.) | 3986 | RESOLVED | CHANGED | — |
| 2 | press | Find an RFC (number, subseries, title, author, etc.) | Enter | RESOLVED | NO_CHANGE | REGROUND,REGROUND,REGROUND,REPLAN |

---

### live_rfceditor_title_rfc2046 — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=2 calls=4 | tokens(out=2377 in=57856 reason=1462 nano_aiu=5394540000)

plan:
- 1. fill "Find an RFC (number, subseries, title, author, etc.)" = "2046"
- 2. press "Find an RFC (number, subseries, title, author, etc.)" = "Enter"
- 3. click "RFC 2046:"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | fill | Find an RFC (number, subseries, title, author, etc.) | 2046 | RESOLVED | CHANGED | — |
| 2 | press | Find an RFC (number, subseries, title, author, etc.) | Enter | RESOLVED | NO_CHANGE | REGROUND,REGROUND,REGROUND,REPLAN |

---

### live_webscraper_nav_laptops — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=4 calls=7 | tokens(out=4038 in=100522 reason=2324 nano_aiu=9288820000)

plan:
- 1. navigate /test-sites/e-commerce/allinone/computers
- 2. navigate /test-sites/e-commerce/allinone/computers/laptops

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN |
| 2 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN |

---

### live_webscraper_nav_tablets — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=4 | tokens(out=2427 in=57672 reason=1372 nano_aiu=5396540000)

plan:
- 1. click "Navigation category"
- 2. click "Tablets"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Navigation category | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_webscraper_nav_phones — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=2 | tokens(out=1781 in=29768 reason=1078 nano_aiu=3098520000)

plan:
- 1. click "Toggle navigation"
- 2. click "Phones"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Toggle navigation | — | RESOLVED | NO_CHANGE | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |

---

### live_webscraper_open_ipad_mini_product — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=4 | tokens(out=3230 in=57718 reason=1804 nano_aiu=5803790000)

plan:
- 1. click "Navigation category"
- 2. click "Tablets"
- 3. click "IdeaTab A3500L"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Navigation category | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_webscraper_nav_phones_touch — AUDIT: HONEST_FAIL — attribution: ground-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=2 | tokens(out=1851 in=29787 reason=999 nano_aiu=3135895000)

plan:
- 1. click "Toggle navigation"
- 2. click "Phones"
- 3. click "Touch"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Toggle navigation | — | RESOLVED | NO_CHANGE | WAIT_SCROLL_DISMISS,WAIT_SCROLL_DISMISS,REPLAN |

---

### live_reddit_settings_abstain — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=False` | steps=0 calls=1 | tokens(out=1689 in=14279 reason=696 nano_aiu=1872885000)

plan:
- (empty / planner error)

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|

---

### live_reddit_inbox_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=4 calls=3 | tokens(out=2903 in=43096 reason=1674 nano_aiu=4569030000)

plan:
- 1. click "Log in"
- 2. click "Log in"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Log in | — | RESOLVED | CHANGED | REPLAN |
| 2 | click | Log in | — | RESOLVED | CHANGED | REPLAN |

---

### live_x_notifications_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=658 in=14499 reason=480 nano_aiu=1384885000)

plan:
- 1. navigate https://x.com/i/notifications

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_codeberg_settings_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=5 calls=6 | tokens(out=7591 in=86459 reason=4128 nano_aiu=10063935000)

plan:
- 1. navigate https://codeberg.org/
- 2. click "user avatar or menu"
- 3. click "Account Settings"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | NOT_FOUND | NO_CHANGE | REPLAN,REPLAN,REPLAN,REPLAN,REPLAN |

---

### live_x_messages_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=1099 in=14502 reason=604 nano_aiu=1605760000)

plan:
- 1. navigate https://x.com/messages

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---
