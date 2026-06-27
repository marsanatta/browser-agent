"""EXECUTOR: drive perceive -> locate -> act -> verify per sub-task, with the
M2 bounded escalation ladder.

The ladder (docs/architecture/02 §1.2/§1.3): classify the failure from
OBSERVABLE browser state (is_visible/is_enabled, exception text, NO_CHANGE
diff), pick the per-class recovery, and retry ONLY when the recovery produced a
NEW observation. Escalation order: retry-same-action -> re-ground/heal (local
strategy switch) -> global replan -> ask_user. Retries are bounded (no infinite
loop); side-effecting (submit) retries are gated behind confirmation. The
correction signal is never the LLM's self-report (§1.6).

`run()` is an async generator of stream Events so the SSE endpoint and tests
consume the same source of truth. The browser is driven through BrowserProvider
(swappable runtime).
"""

from __future__ import annotations

import uuid
from typing import Any, AsyncIterator, Awaitable, Callable

from app.agent import act, recover, verify
from app.agent.classify import FailureClass, Recovery, classify_exception, classify_located, recovery_for
from app.agent.locate import LocatorCache, locate, make_l2_fallback
from app.agent.perceive import IndexedElement, perceive
from app.agent.planner import Planner, SubTask
from app.browser.provider import BrowserProvider
from app.stream import events, screenshots
from app.stream.events import Event

_MAX_ATTEMPTS = 4  # bound the ladder; each attempt needs a new observation

# verify_hook(page) -> bool: an independent post-run ground-truth check run on the
# LIVE final page, before the browser closes. Wired by the eval harness (M3) so
# `verified_completion` reflects a programmatic state assertion rather than the
# agent's own self-report — the basis of the nominal-vs-verified (CuP) gap.
VerifyHook = Callable[[Any], Awaitable[bool]]


class Executor:
    def __init__(
        self,
        provider: BrowserProvider,
        planner: Planner,
        gateway: Any = None,
        confirm_submit: Any = None,
        verify_hook: VerifyHook | None = None,
        step_hook: VerifyHook | None = None,
        max_attempts: int = _MAX_ATTEMPTS,
    ) -> None:
        self._provider = provider
        self._planner = planner
        self._gateway = gateway  # enables the L2 LLM locator fallback when set
        # confirm-before-submit hook: async () -> bool. Default autopilot approves
        # (no human-in-the-loop yet) but the gate is real.
        self._confirm_submit = confirm_submit
        self._verify_hook = verify_hook
        # step_hook(page) is awaited on the live page after EACH sub-task so the
        # eval harness can test key-node checkpoints as the trajectory passes
        # through intermediate states (WebCanvas key-node TCR, architecture/03 §3.1):
        # a checkpoint counts if it was observable at ANY point, not just the end.
        self._step_hook = step_hook
        # max_attempts=1 disables the recovery ladder (and, with gateway=None, the
        # L2 heal) — the budget-matched vanilla baseline the ablation rule requires
        # (architecture/03 §4). The full agent keeps the default 4-step ladder.
        self._max_attempts = max_attempts
        self._cache = LocatorCache()

    async def run(self, task: str) -> AsyncIterator[Event]:
        run_id = uuid.uuid4().hex[:8]
        yield events.run_started(task, run_id)

        yield events.phase(run_id, "planning")
        try:
            subtasks = await self._planner.plan(task)
        except Exception as exc:  # planner is the LLM seam; surface, don't crash
            yield Event(events.EventType.RUN_ERROR, {"run_id": run_id, "error": str(exc)})
            return

        yield events.plan_ready(run_id, [_args(st) for st in subtasks])

        yield events.phase(run_id, "launching")
        await self._provider.launch()
        page = await self._provider.new_page()
        all_ok = True
        replanned = False
        verified = None

        try:
            i = 0
            while i < len(subtasks):
                st = subtasks[i]
                step_id = f"{run_id}-s{i + 1}"
                yield events.step_started(step_id, _describe(st))
                outcome = _Outcome(False)
                async for ev in self._run_subtask(page, step_id, st):
                    if isinstance(ev, _Outcome):
                        outcome = ev
                    else:
                        yield ev
                yield events.step_finished(
                    step_id,
                    "ok" if outcome.ok else "failed",
                    failure_category=None if outcome.ok else outcome.failure_class,
                    verdict="CHANGED" if outcome.ok else "NO_CHANGE",
                )

                if self._step_hook is not None:
                    try:
                        await self._step_hook(page)
                    except Exception:
                        pass

                if outcome.ok:
                    i += 1
                    continue

                if outcome.failure_class == FailureClass.BLOCKED.value:
                    # Bot-wall / CAPTCHA / consent interstitial: a DISTINCT outcome —
                    # neither a capability pass nor a silent fail. Abstain and route
                    # blocked-unsupported (never evade); replanning can't help.
                    yield events.ask_user(
                        step_id,
                        "Blocked by a bot-wall / CAPTCHA / consent interstitial; "
                        "routing as unsupported (not evading, not claiming success).",
                    )
                    all_ok = False
                    break

                # Exhausted local recovery on this sub-task. Global replan once
                # (docs/architecture/02 §1.3: replan only on local exhaustion),
                # then ask_user.
                if not replanned:
                    replanned = True
                    yield events.recovery(step_id, outcome.failure_class, Recovery.REPLAN.value, _MAX_ATTEMPTS)
                    yield events.phase(run_id, "planning")
                    # Peek the page: feed the planner the failed step + failure class
                    # + the current page's REAL elements, and re-plan the suffix from
                    # here. Closes the open loop where the original plan's words
                    # matched no element on the live page (vs blindly re-issuing the
                    # same from-scratch plan, which fails identically).
                    try:
                        observation = _format_observation(await perceive(page))
                        new_subtasks = await self._planner.replan(
                            task, _describe(st), outcome.failure_class, observation
                        )
                    except Exception:
                        new_subtasks = None
                    if new_subtasks:
                        subtasks = subtasks[:i] + new_subtasks
                        # Surface the replan's output so the live view shows what
                        # changed. The ids the frontend seeds (`${run_id}-s${i+1}`)
                        # are still computed off the FULL `subtasks` list, so emit
                        # the full reconciled plan, not just the tail.
                        yield events.plan_ready(run_id, [_args(s) for s in subtasks])
                        continue
                yield events.ask_user(
                    step_id, f"Could not complete '{_describe(st)}' after recovery; need guidance."
                )
                all_ok = False
                break

            # Independent post-run ground-truth check on the live page, BEFORE
            # close (architecture/02 §1.6, eval/01 §4): never trust the agent's
            # self-report. verified diverges from nominal exactly when the agent
            # claims success but the state assertion fails — the CuP silent-failure
            # signal. Hook absent -> verified mirrors nominal (unchanged M1 behavior).
            if self._verify_hook is not None:
                try:
                    verified = await self._verify_hook(page)
                except Exception:
                    verified = False
        finally:
            await self._provider.close()

        yield events.run_finished(
            run_id,
            nominal=all_ok,
            verified=all_ok if verified is None else verified,
            tokens=getattr(self._gateway, "tokens", {}) or {},
        )

    async def _run_subtask(
        self, page: Any, step_id: str, st: SubTask
    ) -> AsyncIterator[Event | "_Outcome"]:
        call_id = uuid.uuid4().hex[:8]
        yield events.tool_call_start(step_id, st.action, call_id)
        yield events.tool_call_args(call_id, _args(st))

        if st.action == "navigate":
            response = await act.navigate(page, st.url or "")
            block = await verify.detect_block(page)
            if block is not None:
                yield events.tool_call_end(call_id, f"navigate -> BLOCKED ({block})")
                yield _Outcome(False, failure_class=FailureClass.BLOCKED.value)
                return
            status = getattr(response, "status", None)
            if status is not None and status >= 400:
                yield events.tool_call_end(call_id, f"navigate -> HTTP {status}")
                yield _Outcome(False, failure_class=FailureClass.NOT_FOUND.value)
                return
            yield events.tool_call_end(call_id, f"navigated to {page.url}")
            shot = await screenshots.capture_step(page, step_id, None, f"navigated to {page.url}")
            if shot is not None:
                yield events.screenshot_annotated(shot)
            yield _Outcome(True)
            return

        last_class = FailureClass.NOT_FOUND
        reground = False
        prev_fingerprint = None
        for attempt in range(1, self._max_attempts + 1):
            result, fc, located, shot = await self._attempt(
                page, step_id, st, reground=reground, attempt=attempt
            )
            if located is not None:
                ground = "AMBIGUOUS_L2" if located.via == "l2" else "RESOLVED"
                yield events.locator_resolved(step_id, located.tier, located.strategy, ground)
            if shot is not None:
                yield events.screenshot_annotated(shot)
            if result is verify.VerifyResult.CHANGED:
                yield events.tool_call_end(call_id, f"{st.action} -> CHANGED (attempt {attempt})")
                yield _Outcome(True)
                return

            if fc is FailureClass.BLOCKED:
                # Bot-wall / CAPTCHA: terminal. Never retry or try to solve it.
                yield events.recovery(
                    step_id, fc.value, Recovery.ASK_USER.value, attempt,
                    tried=_tried(st), detail=_recovery_detail(fc, located),
                )
                yield events.tool_call_end(call_id, f"{st.action} -> BLOCKED")
                yield _Outcome(False, failure_class=FailureClass.BLOCKED.value)
                return

            last_class = fc
            rec = recovery_for(fc)
            yield events.recovery(
                step_id, fc.value, rec.value, attempt,
                tried=_tried(st),
                tier=located.tier if located is not None else None,
                strategy=located.strategy if located is not None else None,
                detail=_recovery_detail(fc, located),
            )

            # A retry must be justified by a NEW observation (§1.3): apply the
            # per-class recovery and only continue if it actually changed state.
            if rec is Recovery.REGROUND:
                fingerprint = await self._perception_fingerprint(page)
                progressed = fingerprint != prev_fingerprint
                prev_fingerprint = fingerprint
                reground = True  # local strategy switch: invalidate + re-perceive (+ L2)
            else:
                progressed = await self._apply_recovery(page, st, rec)
            if not progressed and attempt >= 2:
                break  # recovery is a no-op -> stop escalating locally

        yield events.tool_call_end(call_id, f"{st.action} failed: {last_class.value}")
        yield _Outcome(False, failure_class=last_class.value)

    def _target_and_l2(self, perception: Any, st: SubTask):
        """Map a sub-task to (target_element, l2_fallback), shared by the action
        path (_attempt) and the recovery path (_current_locator) so BOTH get the L2
        re-ground. Three cases, each ending at a (pseudo-or-real) target plus the
        right L2 candidate pool; (None, None) only when the page has no elements:
          - unique deterministic match -> that element; L2 over the full perception.
          - genuine ambiguity          -> pseudo-target; L2 over the tied candidates.
          - ZERO deterministic candidates (synonym / label mismatch, e.g. "Sign In"
            vs "Log in") -> pseudo-target; L2 over the FULL perception so the LLM
            picks the element best matching intent. This closes the open loop where
            the planner's word matches no accessible name.
        A pseudo-target has empty attrs so the deterministic cascade misses and
        resolution routes to L2; with no gateway every pseudo path falls through to
        an honest abstain (NOT_FOUND), never a silent pick."""
        target, ambiguous = _match(perception.elements, st)
        if target is not None:
            l2_candidates = perception.elements
        elif ambiguous:
            target = IndexedElement(
                index=-1, role=st.role or ambiguous[0].role, name=(st.target or "").strip()
            )
            l2_candidates = ambiguous
        elif perception.elements:
            default_role = "textbox" if st.action in ("fill", "press") else "button"
            target = IndexedElement(
                index=-1, role=st.role or default_role, name=(st.target or "").strip()
            )
            l2_candidates = perception.elements
        else:
            return None, None
        l2 = make_l2_fallback(self._gateway, l2_candidates) if self._gateway else None
        return target, l2

    async def _attempt(self, page: Any, step_id: str, st: SubTask, reground: bool, attempt: int):
        """One perceive->locate->(precondition)->act->verify pass. Returns
        (VerifyResult|None, FailureClass, Located|None, ScreenshotAnnotated|None).

        The Located surfaces the chosen locator tier and the screenshot is the
        annotated diagnostic for this step (DESIGN §8). The screenshot is taken
        BEFORE the action so the highlight box references the element on the page
        the agent acted on (after a click that navigates, the element detaches and
        its box would be empty)."""
        perception = await perceive(page)
        target, l2 = self._target_and_l2(perception, st)
        if target is None:
            shot = await self._shot(page, step_id, st, None, "NO_TARGET", attempt)
            return None, FailureClass.NOT_FOUND, None, shot

        if reground:
            self._cache.invalidate(_page_key(page), target)

        located = await locate(page, target, cache=self._cache, l2_fallback=l2)
        if located is None:
            shot = await self._shot(page, step_id, st, None, "NO_TARGET", attempt)
            return None, FailureClass.NOT_FOUND, None, shot

        # Precondition check (UFO2 §1.4): is the element interactable BEFORE we
        # act? is_visible/is_enabled is ground truth, not the LLM's opinion.
        pre = await classify_located(located.locator)
        if pre is not FailureClass.NONE:
            shot = await self._shot(page, step_id, st, located, pre.value, attempt)
            return verify.VerifyResult.NO_CHANGE, pre, located, shot

        if act.requires_confirmation(act.Action(kind=st.action)):
            if not await self._confirm():
                return verify.VerifyResult.NO_CHANGE, FailureClass.WRONG_PAGE, located, None

        # Capture with the target still attached, before the action mutates/detaches it.
        shot = await self._shot(page, step_id, st, located, "acting", attempt)

        before = await verify.snapshot(page)
        try:
            if st.action == "fill":
                await act.fill(located.locator, st.value or "")
                expect = verify.Expectation(
                    dom_changes=True,
                    target_locator=located.locator,
                    target_effect="value",
                    target_value=st.value or "",
                )
            elif st.action == "press":
                await act.press(located.locator, st.value or "Enter")
                expect = verify.Expectation(url_changes=True, dom_changes=True, goal=st.expect)
            else:
                await act.click(located.locator)
                expect = verify.Expectation(url_changes=True, dom_changes=True, goal=st.expect)
        except Exception as exc:
            return verify.VerifyResult.NO_CHANGE, classify_exception(exc), located, shot

        await recover.settle_loading(page)  # wait out an async-loading spinner before the check (timing only)
        result = await verify.verify_after_act(page, before, expect)
        if await verify.detect_block(page) is not None:
            # Landed on a bot-wall / CAPTCHA — do NOT claim success even if the DOM
            # changed (e.g. a /sorry/ navigation). Route as blocked-unsupported.
            return verify.VerifyResult.NO_CHANGE, FailureClass.BLOCKED, located, shot
        if result is verify.VerifyResult.NO_CHANGE:
            return result, FailureClass.NOT_FOUND, located, shot  # re-ground on a silent no-op
        return result, FailureClass.NONE, located, shot

    async def _shot(self, page, step_id, st, located, verdict, attempt):
        locator = located.locator if located is not None else None
        caption = f"{_describe(st)} -> {verdict} (attempt {attempt})"
        return await screenshots.capture_step(page, step_id, locator, caption)

    async def _apply_recovery(self, page: Any, st: SubTask, rec: Recovery) -> bool:
        located = await self._current_locator(page, st)
        if rec is Recovery.WAIT_SCROLL_DISMISS and located is not None:
            return await recover.wait_scroll_dismiss(page, located.locator)
        if rec is Recovery.STATE_WAIT and located is not None:
            return await recover.state_wait(page, located.locator)
        return False

    async def _perception_fingerprint(self, page: Any) -> tuple:
        """Cheap observable-state digest for the REGROUND no-progress check: the
        page URL plus the sorted (role, name) set. A re-perception that yields the
        same digest is NOT a new observation, so REGROUND made no progress."""
        perception = await perceive(page)
        return (
            _page_key(page),
            tuple(sorted((e.role, e.name) for e in perception.elements)),
        )

    async def _current_locator(self, page: Any, st: SubTask):
        perception = await perceive(page)
        target, l2 = self._target_and_l2(perception, st)
        if target is None:
            return None
        return await locate(page, target, cache=self._cache, l2_fallback=l2)

    async def _confirm(self) -> bool:
        if self._confirm_submit is None:
            return True  # autopilot default; the gate exists for human-in-the-loop
        return await self._confirm_submit()


class _Outcome:
    __slots__ = ("ok", "failure_class")

    def __init__(self, ok: bool, failure_class: str = "") -> None:
        self.ok = ok
        self.failure_class = failure_class


def _format_observation(perception: Any, limit: int = 40) -> str:
    """Compact role|name(+href) list of the live page for the peek-replan — never
    raw DOM (token blowup); the same indexed-element vocabulary perceive/locate use."""
    lines = []
    for e in perception.elements[:limit]:
        href = (e.attrs or {}).get("href")
        tail = f" -> {href}" if href else ""
        lines.append(f'{e.role} "{e.name}"{tail}')
    extra = len(perception.elements) - limit
    if extra > 0:
        lines.append(f"... (+{extra} more elements)")
    return "\n".join(lines) if lines else "(no interactive elements found)"


def _match(
    elements: list[IndexedElement], st: SubTask
) -> tuple[IndexedElement | None, list[IndexedElement]]:
    """Resolve the sub-task target to a single element, or surface the ambiguity.

    Returns (target, []) for a unique match, (None, candidates) when several
    distinct candidates remain (route to L2 — never silently pick candidates[0]),
    or (None, []) when nothing matches. Exact-name matches take priority over
    substring matches structurally (the substring pass runs only when the exact
    pass is empty), and an explicit role narrows before the count is taken."""
    target = (st.target or "").strip().lower()
    if not target:
        return None, []
    candidates = [e for e in elements if e.name.strip().lower() == target]
    if not candidates and not st.role:
        candidates = [e for e in elements if target in e.name.strip().lower()]
    if st.role:
        candidates = [e for e in candidates if e.role == st.role] or candidates
    if not candidates:
        return None, []
    if len(candidates) == 1:
        return candidates[0], []
    return None, candidates


def _page_key(page: Any) -> str:
    return page.url.split("?", 1)[0].split("#", 1)[0]


def _tried(st: SubTask) -> str:
    """Short human-readable note of what the agent attempted this attempt: the
    sub-task's action + target (or url for navigate). Frontend shows it verbatim."""
    if st.action == "navigate":
        return f"navigate {st.url or ''}".strip()
    return f"{st.action} '{st.target or ''}'"


# Stable machine tokens (the frontend translates them, like `phase`): a concise
# observable "why" for the attempt, grounded in browser state, not the LLM.
_DETAIL_TOKENS = {
    FailureClass.NOT_FOUND: "no_element_matched",
    FailureClass.NOT_INTERACTABLE: "not_visible_or_enabled",
    FailureClass.WRONG_PAGE: "wrong_page",
    FailureClass.STALE_TIMING: "stale_or_timeout",
    FailureClass.BLOCKED: "blocked",
}


def _recovery_detail(fc: FailureClass, located: Any) -> str:
    if fc is FailureClass.NOT_FOUND and located is not None:
        return "no_state_change"  # element resolved but the action produced NO_CHANGE
    return _DETAIL_TOKENS.get(fc, fc.value)


def _describe(st: SubTask) -> str:
    if st.description:
        return st.description
    if st.action == "navigate":
        return f"navigate to {st.url}"
    return f"{st.action} '{st.target}'"


def _args(st: SubTask) -> dict[str, Any]:
    return {k: v for k, v in {
        "action": st.action,
        "target": st.target,
        "url": st.url,
        "value": st.value,
    }.items() if v is not None}
