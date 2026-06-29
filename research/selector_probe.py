"""Free, deterministic selector probe (NO Copilot). Opens each candidate hard-case
page, performs the mutation by hand, and prints whether the intended verify selector
resolves to the expected state. Used to lock assert selectors BEFORE spending pass^3
Copilot budget. Throwaway research tool — not part of the eval gate.

    PYTHONPATH=backend python research/selector_probe.py
"""
from __future__ import annotations

import asyncio
import traceback

from playwright.async_api import async_playwright


async def probe(pw, name, fn):
    browser = await pw.chromium.launch(headless=True)
    ctx = await browser.new_context()
    page = await ctx.new_page()
    try:
        out = await fn(page)
        print(f"[OK]   {name}: {out}")
    except Exception as exc:
        print(f"[FAIL] {name}: {type(exc).__name__}: {exc}")
        traceback.print_exc()
    finally:
        await browser.close()


async def checkboxes(page):
    await page.goto("https://the-internet.herokuapp.com/checkboxes", wait_until="domcontentloaded")
    boxes = page.locator("#checkboxes input[type=checkbox]")
    n = await boxes.count()
    for i in range(n):
        if not await boxes.nth(i).is_checked():
            await boxes.nth(i).check()
    checked = await page.locator("#checkboxes input[type=checkbox]:checked").count()
    return f"total={n} checked_after={checked}  ASSERT element_count(#checkboxes input[type=checkbox]:checked)==2 -> {checked==2}"


async def dynamic_controls(page):
    await page.goto("https://the-internet.herokuapp.com/dynamic_controls", wait_until="domcontentloaded")
    await page.click("#checkbox-example button")  # Remove
    await page.wait_for_selector("#message", timeout=10000)
    msg = (await page.inner_text("#message")).strip()
    cb = await page.locator("#checkbox").count()
    return f"message={msg!r} #checkbox_count={cb}  ASSERT text_contains('gone') -> {'gone' in msg.lower()}"


async def disabledinput(page):
    await page.goto("http://uitestingplayground.com/disabledinput", wait_until="domcontentloaded")
    # enable button, then the field becomes editable after a delay
    btns = page.locator("button")
    enable = page.get_by_role("button", name="Enable Edit Field")
    await enable.click()
    field = page.locator("input[type=text]").first
    await field.wait_for(state="visible", timeout=10000)
    # poll until enabled
    for _ in range(30):
        if await field.is_enabled():
            break
        await page.wait_for_timeout(500)
    await field.fill("hello world")
    val = await field.input_value()
    css = "input[type=text]"
    nbtn = await btns.count()
    return f"buttons={nbtn} field_value={val!r} css={css!r}  ASSERT input_value_equals -> {val=='hello world'}"


async def ajax(page):
    await page.goto("http://uitestingplayground.com/ajax", wait_until="domcontentloaded")
    await page.click("#ajaxButton")
    await page.wait_for_selector("#content p", timeout=20000)
    txt = (await page.inner_text("#content")).strip()
    return f"loaded_text={txt!r}  ASSERT text_contains('Data loaded with AJAX') -> {'data loaded with ajax' in txt.lower()}"


async def form_validation(page):
    await page.goto("https://practice.expandtesting.com/form-validation", wait_until="domcontentloaded")
    # dump the field names + the submit button + any success container, to design the case
    html = await page.content()
    fields = await page.eval_on_selector_all(
        "input,select,textarea,button",
        "els => els.map(e => (e.tagName+'#'+(e.id||'')+'.'+(e.name||'')+'['+(e.type||'')+']')).slice(0,30)")
    return f"controls={fields}"


async def todomvc(page):
    # find a working todomvc example + confirm classic classes
    for url in [
        "https://todomvc.com/examples/javascript-es6/dist/",
        "https://todomvc.com/examples/react/dist/",
        "https://todomvc.com/examples/vanillajs/",
    ]:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            inp = page.locator(".new-todo, input.new-todo, [placeholder*='hat needs']").first
            if await inp.count() == 0:
                continue
            for t in ["buy milk", "walk dog", "write report"]:
                await inp.fill(t)
                await inp.press("Enter")
            toggles = page.locator(".todo-list li .toggle")
            await toggles.nth(1).check()
            count_txt = (await page.locator(".todo-count").inner_text()).strip()
            # click Active filter
            await page.get_by_role("link", name="Active").click()
            active_items = await page.locator(".todo-list li").count()
            return f"url={url} todo_count_text={count_txt!r} active_li_count={active_items}  ASSERT element_count(.todo-list li)==2 -> {active_items==2}"
        except Exception:
            continue
    return "NO working todomvc url found among candidates"


async def selectorshub(page):
    await page.goto("https://selectorshub.com/xpath-practice-page/", wait_until="domcontentloaded", timeout=20000)
    # try to find a shadow-dom input; Playwright css auto-pierces OPEN shadow roots
    candidates = ["#userName", "#snacks", "input#kils", "iframe"]
    found = {}
    for c in candidates:
        try:
            found[c] = await page.locator(c).count()
        except Exception as e:
            found[c] = f"err:{type(e).__name__}"
    # attempt: type into the known shadow input #userName (inside shadow-root) if present
    note = ""
    try:
        u = page.locator("#userName").first
        if await u.count():
            await u.fill("probe-value")
            note = f" typed#userName value={await u.input_value()!r} (shadow pierce OK)"
    except Exception as e:
        note = f" type-fail:{type(e).__name__}:{e}"
    return f"selector_counts={found}{note}"


async def main():
    async with async_playwright() as pw:
        for name, fn in [
            ("checkboxes", checkboxes),
            ("dynamic_controls", dynamic_controls),
            ("disabledinput", disabledinput),
            ("ajax", ajax),
            ("form_validation", form_validation),
            ("todomvc", todomvc),
            ("selectorshub", selectorshub),
        ]:
            await probe(pw, name, fn)


if __name__ == "__main__":
    asyncio.run(main())
