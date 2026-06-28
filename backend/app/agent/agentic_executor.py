"""AGENTIC EXECUTOR: an LLM-in-loop alternative to the plan-then-execute Executor.

Same interface as app.agent.executor.Executor (constructor kwargs + `run(task) ->
AsyncIterator[Event]`) and the SAME Event stream, so the SSE frontend and the eval
harness consume it unchanged. The difference is INTERNAL: instead of a deterministic
`while i < len(subtasks)` plan loop, ONE Copilot function-calling session self-drives
the browser by calling tools (observe/read/click/fill/navigate/verify/finish). The
LLM makes every grounding and acting decision; the deterministic verifier
(app.agent.verify, surfaced as the `verify` tool) — never the LLM — decides success.

THE BRIDGE (the crux). The Copilot SDK may invoke tool handlers from a different
thread, but the Event stream must be `yield`ed from `run()`'s asyncio task. So:
capture the running loop, hand every handler an `asyncio.Queue`, and have handlers
push Events with `loop.call_soon_threadsafe(q.put_nowait, ev)` (thread-safe hand-off
onto the loop). `run()` starts `send_and_wait` as a background task and concurrently
drains the queue, yielding each Event until a DONE sentinel (enqueued after
send_and_wait returns). A handler emits, in order, per tool call:
  step_started -> tool_call_start -> tool_call_args -> <op> -> screenshot -> tool_call_end
  -> step_finished.
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
import uuid
from typing import Any, AsyncIterator, Awaitable, Callable

from pydantic import BaseModel, Field

from app.agent import verify
from app.agent.agentic import cdp
from app.verify.state import state_check
from app.agent.agentic.skill import (
    HANDLER_TIMEOUT,
    SESSION_TIMEOUT,
    SKILL,
    TOOL_BUDGET,
    TOOL_NAMES,
)
from app.stream import events, screenshots
from app.stream.events import Event

VerifyHook = Callable[[Any], Awaitable[bool]]

_DEFAULT_MODEL = os.getenv("PILOT_MODEL", "claude-haiku-4.5")
_DEBUG = bool(os.getenv("AGENT_DEBUG"))
_DONE = object()  # queue sentinel: send_and_wait has returned, stop draining


def _model_for(gateway: Any) -> str:
    """SINGLE model for the one agentic session: the gateway's workhorse model when
    it carries one, else PILOT_MODEL / claude-haiku-4.5. The plan-era replanner/L2
    model distinctions do not apply — there is only one session."""
    return getattr(gateway, "workhorse_model", None) or _DEFAULT_MODEL


async def _miss_message(page: Any, target: str, kind: str) -> str:
    """#2 (strategy signal): on a locate miss, distinguish AMBIGUOUS (the name matched
    elements but none resolved uniquely) from ABSENT (nothing matched), so the agent can
    switch strategy — disambiguate vs wide-observe — instead of blind retry. The locator
    cascade already knows this; surface it here (principle: the cascade outcome — ambiguous
    vs absent — must reach the agent)."""
    try:
        cands = await cdp.perceive(page, target)
    except Exception:
        cands = []
    if cands:
        return (f"AMBIGUOUS: several {kind}s relate to {target!r} but none resolves uniquely — "
                f"use a MORE SPECIFIC label (the exact visible text).")
    return (f"NOT_FOUND: nothing matched {target!r}. The {kind} may be RENAMED or HIDDEN in a "
            f"menu/expander — observe with an empty target to list ALL elements, then act; or finish.")


# --- tool param schemas (Pydantic, as the SDK requires) ---------------------
class _Target(BaseModel):
    target: str = Field(description="Exact visible text/label of the element")


class _Read(BaseModel):
    target: str = Field(description="What information to read (e.g. 'price', 'atomic number')")


class _Fill(BaseModel):
    target: str = Field(description="Exact label of the field to fill")
    value: str = Field(description="Text to type into the field")


class _Url(BaseModel):
    url: str = Field(description="Absolute URL to navigate to")


class _Verify(BaseModel):
    url_contains: str | None = Field(
        default=None, description="A substring the page URL should contain"
    )
    text_visible: str | None = Field(
        default=None, description="Text that should be visible on the page"
    )
    selector_visible: str | None = Field(
        default=None, description="A CSS selector that should be visible on the page"
    )


class _Finish(BaseModel):
    success: bool = Field(description="True if the goal was reached")
    note: str = Field(default="", description="One-line reason / what was done")


class AgenticExecutor:
    def __init__(
        self,
        provider: Any,
        planner: Any = None,         # accepted for interface parity; the LLM self-plans
        gateway: Any = None,
        confirm_submit: Any = None,  # accepted for parity; no confirm gate in the loop
        verify_hook: VerifyHook | None = None,
        step_hook: VerifyHook | None = None,
        max_attempts: int | None = None,
        peek_plan: bool = False,     # accepted for parity; always peeks (navigates first)
        start_url: str | None = None,
        max_replans: int | None = None,
        view_scope: int | None = None,  # accepted for parity; observe self-caps at 40
        finish_gate_criterion: dict | None = None,
    ) -> None:
        self._provider = provider
        self._gateway = gateway
        self._verify_hook = verify_hook
        self._step_hook = step_hook
        self._start_url = start_url
        # The PRODUCTION caller's success criterion, threaded ONLY from main.py — the eval
        # harness never passes it, so eval scoring is unaffected (anti-gaming). When set, the
        # finish gate ALSO requires this deterministic state_check to hold on the live page,
        # so a loose self-verify can't claim success on a wrong page (the amazon "light" bug).
        self._finish_gate_criterion = finish_gate_criterion
        # max_attempts / max_replans are plan-era knobs; here there is no replan, so they
        # map onto the agentic equivalent: the tool-call budget (the max iterations the
        # LLM may take before being forced to wrap up). Take the largest hint given, else
        # the default. The 1-attempt budget-matched baseline would be unusably tight for a
        # self-driving loop, so floor the budget at a workable minimum.
        hint = max(v for v in (max_attempts, max_replans, 0) if v is not None)
        self._tool_budget = max(hint, TOOL_BUDGET) if hint else TOOL_BUDGET
        self._model = _model_for(gateway)

    async def run(self, task: str) -> AsyncIterator[Event]:
        run_id = uuid.uuid4().hex[:8]
        yield events.run_started(task, run_id)

        # No token: surface a RUN_ERROR like Executor's planner seam does, don't crash.
        if not any(os.getenv(v) for v in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")):
            yield Event(
                events.EventType.RUN_ERROR,
                {"run_id": run_id, "error": "No Copilot token (set GH_TOKEN=$(gh auth token))."},
            )
            yield events.run_finished(run_id, nominal=False, verified=None, goal_checked=False)
            return

        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()
        page = None
        launched = False
        verified = None
        send_task = None
        # Shared state the (possibly cross-thread) tool handlers mutate.
        state: dict[str, Any] = {
            "finished": False,
            "success": False,     # the LLM's claim, AFTER gate approval (-> nominal)
            "tools": 0,
            "counter": 0,         # step/call id counter, like Executor (run_id + n)
            "last_verify_ok": False,
            "blocked": False,
            "client": None,
        }
        # Honest token ledger (browser-pilot pattern): accrued from the assistant.usage
        # event; counts even on a timeout so a hung run records the real $/calls it burned.
        ledger = {k: 0 for k in ("input_tokens", "output_tokens", "reasoning_tokens", "total_nano_aiu")}
        ledger["calls"] = 0

        def emit(ev: Event) -> None:
            """Thread-safe hand-off of an Event onto the run() loop's queue. The SDK may
            call a handler from another thread, so never `q.put_nowait` directly."""
            loop.call_soon_threadsafe(q.put_nowait, ev)

        try:
            yield events.phase(run_id, "launching")
            await self._provider.launch()
            launched = True
            page = await self._provider.new_page()
            if self._start_url:
                await cdp.navigate(page, self._start_url)

            yield events.phase(run_id, "planning")
            send_task = asyncio.create_task(
                self._drive(task, run_id, page, state, ledger, emit, loop)
            )

            # Concurrently drain the queue, yielding each handler-emitted Event, until the
            # driver finishes and enqueues the DONE sentinel.
            while True:
                item = await q.get()
                if item is _DONE:
                    break
                yield item
            # Verdict path. If finish() ended the task the verdict is already decided, so do
            # NOT wait for the model's (unneeded) closing turn — go straight to verify + emit.
            # Only the non-finish path (driver error / session timeout) awaits send_task, to
            # surface a real driver exception as RUN_ERROR.
            if not state["finished"]:
                try:
                    await send_task
                except asyncio.CancelledError:
                    pass
                except Exception as exc:
                    yield Event(
                        events.EventType.RUN_ERROR,
                        {"run_id": run_id, "error": f"{type(exc).__name__}: {exc}"},
                    )

            # step_hook on the final page (key-node checkpoints), like Executor.
            if self._step_hook is not None:
                try:
                    await self._step_hook(page)
                except Exception:
                    pass

            # Independent post-run ground-truth check on the live page, BEFORE close.
            # The harness wires this; verified diverges from nominal exactly when the
            # agent claims success but the state assertion fails (the CuP signal).
            if self._verify_hook is not None:
                try:
                    verified = await self._verify_hook(page)
                except Exception:
                    verified = False

            # Bridge the real per-session call count to where the harness reads it. The int
            # _CountingGateway (harness path) records the agentic calls; the live list-based
            # LLMGateway.calls (which appends prompts) is left untouched. The cancelled closing
            # turn's usage event may race this read by ±1 call — accepted: the verdict is already
            # decided and the call/token ledger is best-effort.
            if isinstance(getattr(self._gateway, "calls", None), int):
                self._gateway.calls += ledger["calls"]

            # Emit the verdict NOW — before the SDK/browser teardown — so the UI renders the
            # result immediately instead of waiting on client.stop() / provider.close().
            yield events.run_finished(
                run_id,
                nominal=bool(state["success"]),
                verified=verified,
                goal_checked=self._verify_hook is not None,
                tokens=self._tokens(ledger),
            )
        finally:
            # Teardown AFTER the verdict is sent. A still-running session (the finish path)
            # is cancelled rather than awaited for its closing turn.
            if send_task is not None and not send_task.done():
                send_task.cancel()
                # gather(return_exceptions=True) absorbs send_task's OWN cancellation without
                # raising, while still propagating an ambient cancel of run()'s task — don't
                # swallow a CancelledError we didn't request.
                await asyncio.gather(send_task, return_exceptions=True)
            client = state.get("client")
            if client is not None:
                try:
                    await client.stop()
                except Exception:
                    pass
            if launched:
                await self._provider.close()

    def _tokens(self, ledger: dict) -> dict:
        """The run's token ledger, in the run_finished/gateway.tokens shape. Also push
        it onto the gateway so the harness (which reads gateway.tokens) carries it."""
        toks = {k: ledger[k] for k in ("input_tokens", "output_tokens", "reasoning_tokens", "total_nano_aiu")}
        gw_tokens = getattr(self._gateway, "tokens", None)
        if isinstance(gw_tokens, dict):
            for k, v in toks.items():
                gw_tokens[k] = gw_tokens.get(k, 0) + v
        return toks

    async def _drive(
        self, task: str, run_id: str, page: Any, state: dict, ledger: dict,
        emit: Callable[[Event], None], loop: Any,
    ) -> None:
        """The one Copilot function-calling session. Defines the tools (closing over the
        live page + emit bridge), runs send_and_wait, and always enqueues _DONE so run()
        stops draining even on error/timeout."""
        try:
            from copilot import CopilotClient
            from copilot.session import PermissionHandler
            from copilot.tools import define_tool

            client = CopilotClient()
            await client.start()
            state["client"] = client

            def next_ids() -> tuple[str, str]:
                state["counter"] += 1
                n = state["counter"]
                return f"{run_id}-s{n}", uuid.uuid4().hex[:8]

            def gate() -> str | None:
                """Pre-flight for the acting tools: stop once finished; force a wrap-up
                past the budget. Keeps the session from looping to the wall-clock timeout."""
                if state["finished"]:
                    return "TASK ALREADY FINISHED. Stop now and end your turn."
                state["tools"] += 1
                if state["tools"] > self._tool_budget:
                    return ("BUDGET_EXCEEDED: too many steps. Call finish(success=false) now "
                            "unless the goal is already reached.")
                return None

            async def shot(step_id: str, locator: Any, caption: str) -> None:
                s = await screenshots.capture_step(page, step_id, locator, caption)
                if s is not None:
                    emit(events.screenshot_annotated(s))

            async def observe(p: _Target) -> str:
                if (g := gate()) is not None:
                    return g
                step_id, call_id = next_ids()
                emit(events.step_started(step_id, f"observe: {p.target}"))
                emit(events.tool_call_start(step_id, "observe", call_id))
                emit(events.tool_call_args(call_id, {"target": p.target}))
                try:
                    els = await asyncio.wait_for(cdp.perceive(page, p.target), HANDLER_TIMEOUT)
                except asyncio.TimeoutError:
                    return self._finish_tool(emit, step_id, call_id, page, "observe timeout", False,
                                             "OBSERVE_TIMEOUT: page slow; pick a different target or finish.")
                payload = json.dumps([{"role": e.role, "name": e.name} for e in els[:20]])
                await shot(step_id, None, f"observe: {p.target}")
                emit(events.tool_call_end(call_id, f"{len(els)} elements"))
                emit(events.step_finished(step_id, "ok"))
                return payload

            async def read(p: _Read) -> str:
                if (g := gate()) is not None:
                    return g
                step_id, call_id = next_ids()
                emit(events.step_started(step_id, f"read: {p.target}"))
                emit(events.tool_call_start(step_id, "read", call_id))
                emit(events.tool_call_args(call_id, {"target": p.target}))
                try:
                    txt = await asyncio.wait_for(cdp.read_text(page, p.target), HANDLER_TIMEOUT)
                except asyncio.TimeoutError:
                    return self._finish_tool(emit, step_id, call_id, page, "read timeout", False,
                                             "READ_TIMEOUT: page slow; try finish.")
                await shot(step_id, None, f"read: {p.target}")
                emit(events.tool_call_end(call_id, f"{len(txt)} chars"))
                emit(events.step_finished(step_id, "ok"))
                return txt

            async def click(p: _Target) -> str:
                if (g := gate()) is not None:
                    return g
                state["last_verify_ok"] = False  # page state changes -> stale verify must not gate finish
                step_id, call_id = next_ids()
                emit(events.step_started(step_id, f"click: {p.target}"))
                emit(events.tool_call_start(step_id, "click", call_id))
                emit(events.tool_call_args(call_id, {"target": p.target}))
                try:
                    before = await asyncio.wait_for(cdp.snapshot(page), HANDLER_TIMEOUT)
                    loc = await asyncio.wait_for(cdp.ground(page, p.target), HANDLER_TIMEOUT)
                except asyncio.TimeoutError:
                    return self._finish_tool(emit, step_id, call_id, page, "click timeout", False,
                                             "CLICK_TIMEOUT: page slow; try a different target or finish.")
                if loc is None:
                    return self._finish_tool(emit, step_id, call_id, page, "not found", False,
                                             await _miss_message(page, p.target, "element"))
                await shot(step_id, loc, f"click: {p.target}")
                try:
                    await asyncio.wait_for(cdp.click(loc), HANDLER_TIMEOUT)
                except asyncio.TimeoutError:
                    return self._finish_tool(emit, step_id, call_id, page, "click timeout", False,
                                             "CLICK_TIMEOUT: the click did not settle; try a different target.")
                except Exception as exc:
                    return self._finish_tool(emit, step_id, call_id, page, f"click error: {type(exc).__name__}", False,
                                             f"CLICK_ERROR: {type(exc).__name__}; try a different target.")
                after = await cdp.snapshot(page)
                ch = cdp.changed(before, after)
                emit(events.tool_call_end(call_id, f"changed={ch} url={page.url}"))
                emit(events.step_finished(step_id, "ok" if ch else "failed"))
                return json.dumps({"changed": ch, "url": page.url})

            async def fill(p: _Fill) -> str:
                if (g := gate()) is not None:
                    return g
                state["last_verify_ok"] = False  # page state changes -> stale verify must not gate finish
                step_id, call_id = next_ids()
                emit(events.step_started(step_id, f"fill: {p.target}"))
                emit(events.tool_call_start(step_id, "fill", call_id))
                emit(events.tool_call_args(call_id, {"target": p.target, "value": p.value}))
                try:
                    loc = await asyncio.wait_for(cdp.ground(page, p.target), HANDLER_TIMEOUT)
                except asyncio.TimeoutError:
                    return self._finish_tool(emit, step_id, call_id, page, "fill timeout", False,
                                             "FILL_TIMEOUT: page slow; try a different target or finish.")
                if loc is None:
                    return self._finish_tool(emit, step_id, call_id, page, "not found", False,
                                             await _miss_message(page, p.target, "field"))
                await shot(step_id, loc, f"fill: {p.target}")
                try:
                    await asyncio.wait_for(cdp.fill(loc, p.value), HANDLER_TIMEOUT)
                except asyncio.TimeoutError:
                    return self._finish_tool(emit, step_id, call_id, page, "fill timeout", False,
                                             "FILL_TIMEOUT: the field did not accept input.")
                except Exception as exc:
                    return self._finish_tool(emit, step_id, call_id, page, f"fill error: {type(exc).__name__}", False,
                                             f"FILL_ERROR: {type(exc).__name__}.")
                emit(events.tool_call_end(call_id, "filled"))
                emit(events.step_finished(step_id, "ok"))
                return "filled"

            async def navigate(p: _Url) -> str:
                if (g := gate()) is not None:
                    return g
                state["last_verify_ok"] = False  # page state changes -> stale verify must not gate finish
                step_id, call_id = next_ids()
                emit(events.step_started(step_id, f"navigate: {p.url}"))
                emit(events.tool_call_start(step_id, "navigate", call_id))
                emit(events.tool_call_args(call_id, {"url": p.url}))
                try:
                    await asyncio.wait_for(cdp.navigate(page, p.url), HANDLER_TIMEOUT)
                except asyncio.TimeoutError:
                    return self._finish_tool(emit, step_id, call_id, page, "navigate timeout", False,
                                             "NAVIGATE_TIMEOUT: the page did not load; try finish or another URL.")
                await shot(step_id, None, f"navigated to {page.url}")
                emit(events.tool_call_end(call_id, f"navigated to {page.url}"))
                emit(events.step_finished(step_id, "ok"))
                return json.dumps({"url": page.url})

            async def verify_tool(p: _Verify) -> str:
                """DETERMINISTIC verifier surfaced as a tool: browser-agent's own
                verify._goal_satisfied + detect_block, reading the REAL page. It never
                trusts the LLM's claim — finish(success=true) is gated on its last result."""
                if (g := gate()) is not None:
                    return g
                step_id, call_id = next_ids()
                goal = {k: v for k, v in {
                    "url_contains": p.url_contains,
                    "text_visible": p.text_visible,
                    "selector_visible": p.selector_visible,
                }.items() if v is not None}
                emit(events.step_started(step_id, f"verify: {goal}"))
                emit(events.tool_call_start(step_id, "verify", call_id))
                emit(events.tool_call_args(call_id, goal))
                block = await verify.detect_block(page)
                state["blocked"] = block is not None
                ok = bool(goal) and await verify._goal_satisfied(page, goal)
                state["last_verify_ok"] = ok and block is None
                await shot(step_id, None, f"verify -> satisfied={state['last_verify_ok']}")
                emit(events.tool_call_end(call_id, f"satisfied={state['last_verify_ok']} blocked={block}"))
                emit(events.step_finished(step_id, "ok" if state["last_verify_ok"] else "failed"))
                if block is not None:
                    return json.dumps({"satisfied": False, "blocked": block})
                if not goal:
                    return json.dumps({"satisfied": False, "error": "supply at least one goal primitive"})
                return json.dumps({"satisfied": ok, "blocked": None})

            async def finish(p: _Finish) -> str:
                # The deterministic verifier (verify tool result) + detect_block, NOT the
                # agent, decide whether a success claim stands. A claim is REJECTED unless
                # the last verify was satisfied AND the page is not blocked.
                step_id, call_id = next_ids()
                emit(events.step_started(step_id, f"finish: success={p.success}"))
                emit(events.tool_call_start(step_id, "finish", call_id))
                emit(events.tool_call_args(call_id, {"success": p.success, "note": p.note}))
                if p.success:
                    block = await verify.detect_block(page)
                    reason = None
                    if block is not None:
                        reason = block
                    elif not state["last_verify_ok"]:
                        reason = "no satisfied verify(goal) before finish"
                    elif self._finish_gate_criterion is not None and not await state_check(
                        page, self._finish_gate_criterion
                    ):
                        reason = "the caller's success criterion is not met on the live page"
                    if reason is not None:
                        emit(events.tool_call_end(call_id, f"REJECTED: {reason}"))
                        emit(events.step_finished(step_id, "failed"))
                        emit(events.ask_user(step_id, f"Success claim rejected by the verifier: {reason}."))
                        return (f"REJECTED by the verification gate: {reason}. The goal is NOT "
                                "verified. Call verify(goal) and only finish(success=true) once it "
                                "confirms, or finish(success=false).")
                state["finished"] = True
                state["success"] = bool(p.success)
                emit(events.tool_call_end(call_id, f"finished success={p.success}"))
                if not p.success:
                    # Honest give-up / abstain. Emit ASK_USER so the harness scores an
                    # expect_abstain task as a correct refusal (asked AND not nominal) —
                    # parity with the plan executor, which abstains via ask_user. If the
                    # page is actually a bot-wall/CAPTCHA, mark the step BLOCKED so audit
                    # sets reduced["blocked"]=True, which expect_abstain(reason="blocked")
                    # additionally requires. Harmless on non-abstain tasks: verified is
                    # decided independently by state_check, which ignores `asked`.
                    blk = await verify.detect_block(page)
                    emit(events.step_finished(step_id, "failed" if blk else "ok",
                                              failure_category="BLOCKED" if blk else None))
                    emit(events.ask_user(step_id, p.note or "Stopping: goal not reachable or blocked."))
                else:
                    emit(events.step_finished(step_id, "ok"))
                # The verdict is decided — release run()'s drain loop NOW so RUN_FINISHED is
                # emitted immediately, instead of waiting for the model's (unneeded) closing turn.
                emit(_DONE)  # type: ignore[arg-type]
                return "ack — end your turn now."

            tools = [
                define_tool("observe", description="List interactive elements related to a target.",
                            handler=observe, params_type=_Target, skip_permission=True),
                define_tool("read", description="Read page text (prices, facts, prose) for a target.",
                            handler=read, params_type=_Read, skip_permission=True),
                define_tool("click", description="Click the element with the given visible text.",
                            handler=click, params_type=_Target, skip_permission=True),
                define_tool("fill", description="Type a value into a labelled field.",
                            handler=fill, params_type=_Fill, skip_permission=True),
                define_tool("navigate", description="Go to an absolute URL.",
                            handler=navigate, params_type=_Url, skip_permission=True),
                define_tool("verify", description="Deterministically check a goal holds on the live page.",
                            handler=verify_tool, params_type=_Verify, skip_permission=True),
                define_tool("finish", description="End the task with a success verdict.",
                            handler=finish, params_type=_Finish, skip_permission=True),
            ]

            session = await client.create_session(
                on_permission_request=PermissionHandler.approve_all,
                model=self._model,
                tools=tools,
                available_tools=TOOL_NAMES,
            )

            def on_event(event: Any) -> None:
                data = getattr(event, "data", None)
                if data is not None and hasattr(data, "reasoning_tokens"):
                    ledger["calls"] += 1
                    for k in ("input_tokens", "output_tokens", "reasoning_tokens"):
                        v = getattr(data, k, None)
                        if v:
                            ledger[k] += v
                    cu = getattr(data, "copilot_usage", None)
                    nano = getattr(cu, "total_nano_aiu", None) if cu is not None else None
                    if nano:
                        ledger["total_nano_aiu"] += nano

            session.on(on_event)
            prompt = f"{SKILL}\n\nTASK: {task}\nThe start page is already open."
            if _DEBUG:
                print(f"[agentic] run thread={threading.get_ident()} model={self._model}", flush=True)
            try:
                await session.send_and_wait(prompt, timeout=SESSION_TIMEOUT)
            except (asyncio.TimeoutError, TimeoutError):
                if _DEBUG:
                    print(f"[agentic] SESSION_TIMEOUT after {ledger['calls']} calls", flush=True)
            try:
                await session.disconnect()
            except Exception:
                pass
        finally:
            # Always release run()'s drain loop, even on an unexpected driver exception.
            emit(_DONE)  # type: ignore[arg-type]

    @staticmethod
    def _finish_tool(
        emit: Callable[[Event], None], step_id: str, call_id: str, page: Any,
        end_note: str, ok: bool, ret: str,
    ) -> str:
        """Close out a tool call's events on an early (timeout/not-found) return, then
        return the model-facing string. Keeps the per-call event ordering complete."""
        emit(events.tool_call_end(call_id, end_note))
        emit(events.step_finished(step_id, "ok" if ok else "failed"))
        return ret
