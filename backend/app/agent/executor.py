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
from typing import Any, AsyncIterator

from app.agent import act, recover, verify
from app.agent.classify import FailureClass, Recovery, classify_exception, classify_located, recovery_for
from app.agent.locate import LocatorCache, locate, make_l2_fallback
from app.agent.perceive import IndexedElement, perceive
from app.agent.planner import Planner, SubTask
from app.browser.provider import BrowserProvider
from app.stream import events, screenshots
from app.stream.events import Event

_MAX_ATTEMPTS = 4  # bound the ladder; each attempt needs a new observation


class Executor:
    def __init__(
        self,
        provider: BrowserProvider,
        planner: Planner,
        gateway: Any = None,
        confirm_submit: Any = None,
    ) -> None:
        self._provider = provider
        self._planner = planner
        self._gateway = gateway  # enables the L2 LLM locator fallback when set
        # confirm-before-submit hook: async () -> bool. Default autopilot approves
        # (no human-in-the-loop yet) but the gate is real.
        self._confirm_submit = confirm_submit
        self._cache = LocatorCache()

    async def run(self, task: str) -> AsyncIterator[Event]:
        run_id = uuid.uuid4().hex[:8]
        yield events.run_started(task, run_id)

        try:
            subtasks = await self._planner.plan(task)
        except Exception as exc:  # planner is the LLM seam; surface, don't crash
            yield Event(events.EventType.RUN_ERROR, {"run_id": run_id, "error": str(exc)})
            return

        await self._provider.launch()
        page = await self._provider.new_page()
        all_ok = True
        replanned = False

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
                )

                if outcome.ok:
                    i += 1
                    continue

                # Exhausted local recovery on this sub-task. Global replan once
                # (docs/architecture/02 §1.3: replan only on local exhaustion),
                # then ask_user.
                if not replanned:
                    replanned = True
                    yield events.recovery(step_id, outcome.failure_class, Recovery.REPLAN.value, _MAX_ATTEMPTS)
                    try:
                        new_subtasks = await self._planner.plan(task)
                    except Exception:
                        new_subtasks = None
                    if new_subtasks:
                        subtasks = subtasks[:i] + new_subtasks
                        continue
                yield events.ask_user(
                    step_id, f"Could not complete '{_describe(st)}' after recovery; need guidance."
                )
                all_ok = False
                break
        finally:
            await self._provider.close()

        yield events.run_finished(run_id, nominal=all_ok, verified=all_ok)

    async def _run_subtask(
        self, page: Any, step_id: str, st: SubTask
    ) -> AsyncIterator[Event | "_Outcome"]:
        call_id = uuid.uuid4().hex[:8]
        yield events.tool_call_start(step_id, st.action, call_id)
        yield events.tool_call_args(call_id, _args(st))

        if st.action == "navigate":
            await act.navigate(page, st.url or "")
            yield events.tool_call_end(call_id, f"navigated to {page.url}")
            shot = await screenshots.capture_step(page, step_id, None, f"navigated to {page.url}")
            if shot is not None:
                yield events.screenshot_annotated(shot)
            yield _Outcome(True)
            return

        last_class = FailureClass.NOT_FOUND
        reground = False
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            result, fc, located, shot = await self._attempt(
                page, step_id, st, reground=reground, attempt=attempt
            )
            if located is not None:
                yield events.locator_resolved(step_id, located.tier, located.strategy)
            if shot is not None:
                yield events.screenshot_annotated(shot)
            if result is verify.VerifyResult.CHANGED:
                yield events.tool_call_end(call_id, f"{st.action} -> CHANGED (attempt {attempt})")
                yield _Outcome(True)
                return

            last_class = fc
            rec = recovery_for(fc)
            yield events.recovery(step_id, fc.value, rec.value, attempt)

            # A retry must be justified by a NEW observation (§1.3): apply the
            # per-class recovery and only continue if it actually changed state.
            progressed = await self._apply_recovery(page, st, rec)
            if rec is Recovery.REGROUND:
                reground = True  # local strategy switch: invalidate + re-perceive (+ L2)
            if not progressed and attempt >= 2:
                break  # recovery is a no-op -> stop escalating locally

        yield events.tool_call_end(call_id, f"{st.action} failed: {last_class.value}")
        yield _Outcome(False, failure_class=last_class.value)

    async def _attempt(self, page: Any, step_id: str, st: SubTask, reground: bool, attempt: int):
        """One perceive->locate->(precondition)->act->verify pass. Returns
        (VerifyResult|None, FailureClass, Located|None, ScreenshotAnnotated|None).

        The Located surfaces the chosen locator tier and the screenshot is the
        annotated diagnostic for this step (DESIGN §8). The screenshot is taken
        BEFORE the action so the highlight box references the element on the page
        the agent acted on (after a click that navigates, the element detaches and
        its box would be empty)."""
        perception = await perceive(page)
        target = _match(perception.elements, st)
        if target is None:
            shot = await self._shot(page, step_id, st, None, "NO_TARGET", attempt)
            return None, FailureClass.NOT_FOUND, None, shot

        if reground:
            self._cache.invalidate(_page_key(page), target)

        l2 = make_l2_fallback(self._gateway, perception.elements) if self._gateway else None
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

        if st.action == "fill" and act.requires_confirmation(act.Action(kind="fill")):
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
            else:
                await act.click(located.locator)
                expect = verify.Expectation(url_changes=True, dom_changes=True)
        except Exception as exc:
            return verify.VerifyResult.NO_CHANGE, classify_exception(exc), located, shot

        result = await verify.verify_after_act(page, before, expect)
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
        if rec is Recovery.REGROUND:
            return True  # the next attempt re-perceives with the cache invalidated
        return False

    async def _current_locator(self, page: Any, st: SubTask):
        perception = await perceive(page)
        target = _match(perception.elements, st)
        if target is None:
            return None
        return await locate(page, target, cache=self._cache)

    async def _confirm(self) -> bool:
        if self._confirm_submit is None:
            return True  # autopilot default; the gate exists for human-in-the-loop
        return await self._confirm_submit()


class _Outcome:
    __slots__ = ("ok", "failure_class")

    def __init__(self, ok: bool, failure_class: str = "") -> None:
        self.ok = ok
        self.failure_class = failure_class


def _match(elements: list[IndexedElement], st: SubTask) -> IndexedElement | None:
    target = (st.target or "").strip().lower()
    if not target:
        return None
    candidates = [e for e in elements if e.name.strip().lower() == target]
    if not candidates and not st.role:
        candidates = [e for e in elements if target in e.name.strip().lower()]
    if st.role:
        candidates = [e for e in candidates if e.role == st.role] or candidates
    return candidates[0] if candidates else None


def _page_key(page: Any) -> str:
    return page.url.split("?", 1)[0].split("#", 1)[0]


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
