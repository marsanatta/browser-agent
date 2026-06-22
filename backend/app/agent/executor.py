"""EXECUTOR: drive perceive -> locate -> act -> verify per sub-task.

M1 = happy path + a single re-ground attempt on NO_CHANGE. Full per-class
recovery and global replan are M2 (docs/architecture/02 §1.2/§1.3). The
correction signal is observable browser state (verify-after-act), never the
LLM's self-report (§1.6).

`run()` is an async generator of stream Events so the SSE endpoint and tests
consume the same source of truth. The browser is driven through BrowserProvider
(swappable runtime).
"""

from __future__ import annotations

import uuid
from typing import Any, AsyncIterator

from app.agent import act, verify
from app.agent.locate import LocatorCache, locate
from app.agent.perceive import IndexedElement, perceive
from app.agent.planner import Planner, SubTask
from app.browser.provider import BrowserProvider
from app.stream import events
from app.stream.events import Event


class Executor:
    def __init__(self, provider: BrowserProvider, planner: Planner) -> None:
        self._provider = provider
        self._planner = planner
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

        try:
            for i, st in enumerate(subtasks, start=1):
                step_id = f"{run_id}-s{i}"
                yield events.step_started(step_id, _describe(st))
                ok = False
                async for ev in self._run_subtask(page, step_id, st):
                    if isinstance(ev, _Outcome):
                        ok = ev.ok
                    else:
                        yield ev
                all_ok = all_ok and ok
                yield events.step_finished(step_id, "ok" if ok else "no_change")
                if not ok:
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
            yield _Outcome(True)
            return

        # click / fill: perceive -> locate -> act -> verify, single re-ground.
        result = await self._perceive_locate_act_verify(page, st, reground=False)
        if result is verify.VerifyResult.NO_CHANGE:
            yield events.text_message("agent", f"NO_CHANGE on '{st.target}', re-grounding")
            result = await self._perceive_locate_act_verify(page, st, reground=True)

        if result is None:
            yield events.tool_call_end(call_id, f"element not found: {st.target}")
            yield _Outcome(False)
            return

        yield events.tool_call_end(call_id, f"{st.action} -> {result.value}")
        yield _Outcome(result is verify.VerifyResult.CHANGED)

    async def _perceive_locate_act_verify(
        self, page: Any, st: SubTask, reground: bool
    ):
        perception = await perceive(page)
        target = _match(perception.elements, st)
        if target is None:
            return None

        if reground:
            self._cache.invalidate(_page_key(page), target)

        located = await locate(page, target, cache=self._cache)
        if located is None:
            return None

        before = await verify.snapshot(page)
        if st.action == "fill":
            await act.fill(located.locator, st.value or "")
            expect = verify.Expectation(dom_changes=True)
        else:
            await act.click(located.locator)
            expect = verify.Expectation(url_changes=True, dom_changes=True)
        return await verify.verify_after_act(page, before, expect)


class _Outcome:
    __slots__ = ("ok",)

    def __init__(self, ok: bool) -> None:
        self.ok = ok


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
