# Audit Trace — per-task evidence (human-readable, not a metric)

Generated **2026-06-28 03:26 UTC** by `eval.audit` from the executor's event stream (no LLM, no network in the audit itself).

- **attribution_coverage = 1.000** (fraction of FAILING tasks deterministically tagged plan-time/ground-time — 1.0 by construction)
- flag tally: ABSTAIN=1, HONEST_FAIL=2, OK=13, SILENT_FAILURE=4
- Tokens are reported for cost transparency only — never minimized (abstaining more to lower tokens would game the metric and is not done).

---

### live_scrapethissite_goto_simple — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=49 in=19756 reason=0 nano_aiu=7301075000)

plan:
- 1. click "Countries of the World: A Simple Example"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Countries of the World: A Simple Example | — | RESOLVED | CHANGED | — |

---

### live_scrapethissite_goto_forms — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=56 in=19742 reason=0 nano_aiu=7309825000)

plan:
- 1. click "Hockey Teams: Forms, Searching and Pagination"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Hockey Teams: Forms, Searching and Pagination | — | RESOLVED | CHANGED | — |

---

### live_scrapethissite_search_boston — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=1 | tokens(out=131 in=19764 reason=0 nano_aiu=7511075000)

plan:
- 1. click "Hockey Teams: Forms, Searching and Pagination"
- 2. fill "Search for Teams" = "Boston"
- 3. press "Search for Teams" = "Enter"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Hockey Teams: Forms, Searching and Pagination | — | RESOLVED | CHANGED | — |
| 2 | fill | Search for Teams | Boston | RESOLVED | CHANGED | — |
| 3 | press | Search for Teams | Enter | RESOLVED | CHANGED | — |

---

### live_scrapethissite_forms_page2 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=2 | tokens(out=198 in=33670 reason=94 nano_aiu=8433835000)

plan:
- 1. click "Hockey Teams: Forms, Searching and Pagination"
- 2. click "2"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Hockey Teams: Forms, Searching and Pagination | — | RESOLVED | CHANGED | — |
| 2 | click | 2 | — | RESOLVED | CHANGED | REGROUND |

---

### live_rfceditor_open_http11 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=86 in=20331 reason=22 nano_aiu=7752950000)

plan:
- 1. navigate https://www.rfc-editor.org/info/rfc2616/

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_rfceditor_title_rfc8259 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=91 in=20332 reason=20 nano_aiu=7766075000)

plan:
- 1. navigate https://www.rfc-editor.org/info/rfc8259/

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_rfceditor_open_ip — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=58 in=20342 reason=0 nano_aiu=7689825000)

plan:
- 1. navigate https://www.rfc-editor.org/info/rfc791/

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_rfceditor_title_rfc1149 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=112 in=20340 reason=42 nano_aiu=7823575000)

plan:
- 1. navigate https://www.rfc-editor.org/info/rfc1149/

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_rfceditor_title_rfc3986 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=91 in=20339 reason=20 nano_aiu=7770450000)

plan:
- 1. navigate https://www.rfc-editor.org/info/rfc3986/

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_rfceditor_title_rfc2046 — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=60 in=20340 reason=0 nano_aiu=7693575000)

plan:
- 1. navigate https://www.rfc-editor.org/info/rfc2046/

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_webscraper_nav_laptops — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=1 calls=4 | tokens(out=571 in=68805 reason=346 nano_aiu=17980795000)

plan:
- 1. click "Navigation category"
- 2. navigate https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Navigation category | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_webscraper_nav_tablets — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=3 calls=4 | tokens(out=764 in=68793 reason=451 nano_aiu=18173795000)

plan:
- 1. navigate https://webscraper.io/test-sites/e-commerce/allinone/computers
- 2. navigate https://webscraper.io/test-sites/e-commerce/allinone/computers/tablets

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | NOT_FOUND | CHANGED | REGROUND,REGROUND,REPLAN |
| 2 | navigate | — | — | — | CHANGED | — |

---

### live_webscraper_nav_phones — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=1 calls=1 | tokens(out=164 in=20333 reason=36 nano_aiu=7949200000)

plan:
- 1. navigate https://webscraper.io/test-sites/e-commerce/allinone/phones

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_webscraper_open_ipad_mini_product — AUDIT: OK — attribution: n/a (passed)
`nominal=True` `verified=True` `asked=False` | steps=2 calls=1 | tokens(out=211 in=20365 reason=55 nano_aiu=8086700000)

plan:
- 1. navigate https://webscraper.io/test-sites/e-commerce/allinone/computers/tablets
- 2. click "IdeaTab A3500L"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | IdeaTab A3500L | — | RESOLVED | CHANGED | — |

---

### live_webscraper_nav_phones_touch — AUDIT: HONEST_FAIL — attribution: plan-time
`nominal=False` `verified=False` `asked=True` | steps=2 calls=4 | tokens(out=576 in=68727 reason=315 nano_aiu=18091545000)

plan:
- 1. navigate https://webscraper.io/test-sites/e-commerce/allinone/phones
- 2. click "Touch"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |
| 2 | click | Touch | — | NOT_FOUND | NO_CHANGE | REGROUND,REGROUND,REPLAN |

---

### live_reddit_settings_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=2 calls=2 | tokens(out=249 in=39302 reason=92 nano_aiu=14848400000)

plan:
- 1. click "Log in"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Log in | — | RESOLVED | CHANGED | REPLAN |

---

### live_reddit_inbox_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=2 calls=2 | tokens(out=312 in=39311 reason=36 nano_aiu=15011525000)

plan:
- 1. click "Log in"

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | click | Log in | — | RESOLVED | CHANGED | REPLAN |

---

### live_x_notifications_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=43 in=19848 reason=0 nano_aiu=7343575000)

plan:
- 1. navigate https://x.com/notifications

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---

### live_codeberg_settings_abstain — AUDIT: ABSTAIN — attribution: n/a (passed)
`nominal=False` `verified=True` `asked=True` | steps=1 calls=2 | tokens(out=1273 in=39299 reason=114 nano_aiu=17406525000)

plan:
- 1. navigate https://codeberg.org/user/settings

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | NOT_FOUND | NO_CHANGE | REPLAN |

---

### live_x_messages_abstain — AUDIT: SILENT_FAILURE — attribution: ground-time
`nominal=True` `verified=False` `asked=False` | steps=1 calls=1 | tokens(out=41 in=19855 reason=0 nano_aiu=7342950000)

plan:
- 1. navigate https://x.com/messages

| # | action | target | value | ground | verdict | recovery |
|---|---|---|---|---|---|---|
| 1 | navigate | — | — | — | CHANGED | — |

---
