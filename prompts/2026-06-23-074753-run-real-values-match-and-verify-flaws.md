# Run Real Values: _match Tie-break + verify-after-act False Positive

- **Datetime:** 2026-06-23 07:47:53
- **Summary:** Actually ran the login task's planner + perceive (real values, side by side), demonstrated _match's silent first-pick / role-abandon behavior, and proved verify-after-act returns CHANGED on a self-mutating DOM even when the click did nothing. Showed values, not descriptions.

## Prompt

> take that login task and actually run it (or trace with real values), paste the exact
> target name strings the planner produced and the real element names perceive() got from
> the page side by side. i want to see how close the guess was. and the _match part, when
> more than one element name contains the target substring, which one does it pick, show me
> the code path. is there any case it picks the wrong one and nobody notice, or it just
> stop and ask?
>
> second thing ... the verify after act for a click. you traced it is url change or dom
> change. so take a page that has a live clock or a moving ad that change the dom by itself
> every second, and a click that actually did nothing useful. trace verify after act with
> the real before/after values, what does it return? does CHANGED really mean the click did
> what the step needed, or just that the page bytes are different? show me the values that
> decide it, don't describe /save-prompt

## What I Did (real runs, not descriptions)

- Ran the REAL planner (Copilot via backend/.venv) on the login task → targets: navigate /login, fill 'Username'=tomsmith, fill 'Password'=…, click 'Login'.
- Ran perceive() on the live /login page → names: 'Username'(textbox,id=username), 'Password'(textbox,id=password), 'Login'(button), 'Elemental Selenium'(link). Guess was EXACT (the-internet has real <label>s; accessible name == human label). Contrast: books truncated-title is where it misses.
- Demonstrated _match (executor.py:292-301): substring tie → returns candidates[0] (FIRST in perceive order), never count-checks, never asks; role is a SOFT hint (`or candidates`) — asked for a link named 'login', got the button. Wrong-element selection is SILENT; locate()'s count==1 does NOT catch it (it only guarantees uniqueness for the element _match already chose).
- Demonstrated verify_after_act false positive: live-clock DOM, inert no-op click → BEFORE dom_len=154 / AFTER dom_len=166, dom_hash differs, url same → RESULT=CHANGED. The decision (verify.py:87-90) fires on dom_hash change caused by the CLOCK, not the click. CHANGED = "body bytes differ", not "the click did the needed thing". Self-mutating pages make every click (incl. no-ops) read as success.
- Incidental finding: Copilot SDK is installed only in backend/.venv, not the global interpreter used for pytest.
- Net honest verdict: open-loop naming is exact on clean forms but ambiguity is resolved by silent first-pick; per-step click verification can't distinguish "click worked" from "page self-mutated" — only the final independent state_check is trustworthy.
