"""Second selector probe — the cases probe #1 left uncertain. Free, no Copilot."""
from __future__ import annotations

import asyncio
import traceback

from playwright.async_api import async_playwright


async def probe(pw, name, fn):
    b = await pw.chromium.launch(headless=True)
    page = await (await b.new_context()).new_page()
    try:
        print(f"[OK]   {name}: {await fn(page)}")
    except Exception as exc:
        print(f"[FAIL] {name}: {type(exc).__name__}: {exc}")
        traceback.print_exc()
    finally:
        await b.close()


async def disabledinput(page):
    await page.goto("http://uitestingplayground.com/disabledinput", wait_until="domcontentloaded")
    html = await page.locator("#para1, .container, body").first.inner_html()
    inp = page.locator("input").first
    outer = await inp.evaluate("e => e.outerHTML")
    await page.get_by_role("button", name="Enable Edit Field").click()
    for _ in range(30):
        if await inp.is_enabled():
            break
        await page.wait_for_timeout(500)
    await inp.fill("hello world")
    val = await inp.input_value()
    return f"input_outerHTML={outer[:120]!r} value_after={val!r} ASSERT input_value_equals(css='input', value='hello world') -> {val=='hello world'}"


async def form_validation(page):
    await page.goto("https://practice.expandtesting.com/form-validation", wait_until="domcontentloaded")
    await page.fill("#validationCustom01", "Ada Lovelace")
    await page.fill("input[name=contactnumber]", "5551234")
    await page.fill("input[name=pickupdate]", "2026-12-25")
    try:
        await page.select_option("select[name=payment]", index=1)
    except Exception:
        pass
    await page.click("button[type=submit]")
    await page.wait_for_timeout(1500)
    url = page.url
    body = (await page.inner_text("body"))[:400]
    return f"url_after={url!r} body_snippet={body!r}"


async def add_remove(page):
    await page.goto("https://the-internet.herokuapp.com/add_remove_elements/", wait_until="domcontentloaded")
    add = page.get_by_role("button", name="Add Element")
    for _ in range(3):
        await add.click()
    c_class = await page.locator("#elements .added-manually").count()
    c_btn = await page.locator("#elements button").count()
    return f"added-manually={c_class} #elements button={c_btn} ASSERT element_count(#elements .added-manually)==3 -> {c_class==3}"


async def tables(page):
    await page.goto("https://the-internet.herokuapp.com/tables", wait_until="domcontentloaded")
    # table1 has no id/class; sort by Last Name (first column) by clicking its header
    headers = page.locator("#table1 thead th span.last-name, #table1 thead th").all_inner_texts
    first_before = (await page.locator("#table1 tbody tr").first.inner_text()).split("\n")[0]
    await page.click("#table1 thead th:has-text('Last Name')")
    first_after_asc = (await page.locator("#table1 tbody tr").first.inner_text())
    first_lastname = (await page.locator("#table1 tbody tr").first.locator("td").first.inner_text()).strip()
    return f"first_before={first_before!r} first_row_after_sort={first_after_asc.replace(chr(10),'|')!r} first_lastname_after_asc={first_lastname!r}"


async def shifting(page):
    await page.goto("https://the-internet.herokuapp.com/shifting_content/menu", wait_until="domcontentloaded")
    gallery = page.get_by_role("link", name="Gallery")
    href = await gallery.get_attribute("href")
    await gallery.click()
    await page.wait_for_load_state("domcontentloaded")
    return f"gallery_href={href!r} url_after={page.url!r} ASSERT url_contains('/gallery') -> {'/gallery' in page.url.lower()}"


async def selectorshub(page):
    await page.goto("https://selectorshub.com/xpath-practice-page/", wait_until="domcontentloaded", timeout=25000)
    # enumerate ALL real <input> elements (Playwright pierces open shadow) and report which fill
    info = []
    inputs = page.locator("input")
    n = await inputs.count()
    for i in range(min(n, 25)):
        el = inputs.nth(i)
        try:
            iid = await el.get_attribute("id")
            itype = await el.get_attribute("type")
            ph = await el.get_attribute("placeholder")
            info.append(f"#{iid}|t={itype}|ph={ph}")
        except Exception:
            pass
    # try filling the first text-like input that has an id
    filled = None
    for i in range(min(n, 25)):
        el = inputs.nth(i)
        try:
            iid = await el.get_attribute("id")
            itype = (await el.get_attribute("type")) or "text"
            if iid and itype in ("text", "email", "search", None):
                await el.fill("probe-value", timeout=2000)
                if (await el.input_value()) == "probe-value":
                    filled = iid
                    break
        except Exception:
            continue
    return f"n_inputs={n} inputs={info} FIRST_FILLABLE_ID={filled!r}"


async def main():
    async with async_playwright() as pw:
        for name, fn in [
            ("disabledinput", disabledinput),
            ("form_validation", form_validation),
            ("add_remove", add_remove),
            ("tables", tables),
            ("shifting", shifting),
            ("selectorshub", selectorshub),
        ]:
            await probe(pw, name, fn)


if __name__ == "__main__":
    asyncio.run(main())
