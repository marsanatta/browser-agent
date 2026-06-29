"""Verify the close-it strategy end to end: trigger vignette -> perceive a close
control -> click it (agent's own perceive+locate+click path) -> confirm the
blocker is gone -> the original Apple click now works."""
import asyncio, os, sys
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _ROOT); sys.path.insert(0, os.path.join(_ROOT, "backend"))
from app.browser.provider import PlaywrightProvider
from app.agent.agentic import cdp

HOME = "https://companiesmarketcap.com/"


async def trigger(page):
    for _ in range(3):
        try:
            await page.locator("a[href*='/marketcap/'], a:has-text('Apple')").first.click(timeout=4000)
        except Exception:
            pass
        await asyncio.sleep(2.5)
        if "google_vignette" in await page.evaluate("()=>location.hash") or \
           await page.evaluate("()=>document.querySelectorAll('iframe[id*=aswift]').length"):
            return True
        await page.goto(HOME, wait_until="domcontentloaded"); await asyncio.sleep(2)
    return False


async def state(page):
    h = await page.evaluate("()=>location.hash")
    ads = await page.evaluate("()=>document.querySelectorAll('iframe[id*=aswift],iframe[src*=googleads]').length")
    return h, ads


async def main():
    p = PlaywrightProvider(headless=True); await p.launch()
    page = await p.new_page()
    await page.goto(HOME, wait_until="domcontentloaded"); await asyncio.sleep(2)
    print("triggered:", await trigger(page), "| state before close:", await state(page))

    # agent path: perceive 'close' -> locate -> click
    els = await cdp.perceive(page, "close")
    print("perceive('close') count:", len(els))
    if not els:
        print("NO close control perceived"); await p.close(); return
    loc = await cdp.locate(page, els[0])
    print("cdp.locate(close) ->", "None (cascade gap)" if loc is None else "resolved")
    if loc is not None:
        try:
            await cdp.click(loc); print("agent-path click -> OK")
        except Exception as e:
            print("agent-path click ->", type(e).__name__)
    # Independent: is the close clickable AT ALL via direct Playwright?
    for sel in ['button:has-text("Close Ad")', 'button[aria-label*="Close" i]', ':text("Close Ad X")']:
        try:
            l = page.locator(sel).first
            if await l.count():
                await l.click(force=True, timeout=3000)
                print(f"direct click {sel!r} -> OK"); break
        except Exception as e:
            print(f"direct click {sel!r} ->", type(e).__name__)
    await asyncio.sleep(1.5)
    print("state after close attempt:", await state(page))

    # now retry Apple
    before = await cdp.snapshot(page)
    apple = await cdp.perceive(page, "Apple")
    if apple:
        aloc = await cdp.locate(page, apple[0])
        try:
            await cdp.click(aloc)
        except Exception as e:
            print("apple click err:", type(e).__name__)
    await asyncio.sleep(2)
    url = await page.evaluate("()=>location.href")
    print("after retry Apple -> url:", url)
    print("SUCCESS" if "/apple/marketcap" in url else "still not on Apple page")
    await p.close()


asyncio.run(main())
