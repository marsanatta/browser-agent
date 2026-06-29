"""Empirically test whether the agent CAN perceive + close the companiesmarketcap
Google vignette ad. Decides the right recovery strategy (close-it vs reload)."""
import asyncio, os, sys
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _ROOT); sys.path.insert(0, os.path.join(_ROOT, "backend"))
from app.browser.provider import PlaywrightProvider
from app.agent.agentic import cdp

HOME = "https://companiesmarketcap.com/"


async def trigger_vignette(page):
    # vignette appears on a navigation click; try up to 3 times
    for attempt in range(3):
        try:
            link = page.locator("a[href*='/marketcap/'], a:has-text('Apple')").first
            await link.click(timeout=4000)
        except Exception:
            pass
        await asyncio.sleep(2.5)
        hash_now = await page.evaluate("() => location.hash")
        ads = await page.evaluate(
            "() => document.querySelectorAll('iframe[id*=aswift],iframe[src*=googleads],ins.adsbygoogle').length")
        if "google_vignette" in hash_now or ads:
            return True, hash_now, ads
        await page.goto(HOME, wait_until="domcontentloaded"); await asyncio.sleep(2)
    return False, hash_now, ads


async def main():
    p = PlaywrightProvider(headless=True); await p.launch()
    page = await p.new_page()
    await page.goto(HOME, wait_until="domcontentloaded"); await asyncio.sleep(2)
    got, h, ads = await trigger_vignette(page)
    print(f"vignette triggered: {got}  (hash={h!r}, ad-iframes={ads})")

    # 1. frames + origins
    frames = []
    for f in page.frames:
        try: frames.append(f.url[:70])
        except Exception: frames.append("(inaccessible)")
    print(f"\nFRAMES ({len(frames)}):"); [print("  ", u) for u in frames]

    # 2. close controls anywhere (main + child frames)
    close_js = """() => {
      const hits = [];
      const RX = /close|dismiss|skip|×|✕|✖|no thanks/i;
      for (const el of document.querySelectorAll('button,[role=button],[aria-label],a,div,span,svg,img')) {
        const t = (el.getAttribute('aria-label')||'') + '|' + (el.title||'') + '|' + (el.id||'') + '|' + (el.textContent||'').slice(0,20);
        if (RX.test(t) && el.offsetParent !== null) hits.push((el.tagName)+' ['+t.replace(/\\s+/g,' ').slice(0,50)+']');
      }
      return hits.slice(0,12);
    }"""
    for f in page.frames:
        try:
            hits = await f.evaluate(close_js)
            if hits: print(f"\nCLOSE-LIKE in frame {f.url[:50]!r}:"); [print("   ", x) for x in hits]
        except Exception as e:
            print(f"\nframe {f.url[:50]!r}: inaccessible ({type(e).__name__})")

    # 3. what does the AGENT's perception surface?
    for tgt in ["", "close", "skip", "dismiss"]:
        try:
            els = await cdp.perceive(page, tgt)
            names = [getattr(e, "name", "")[:30] for e in els[:12]]
            print(f"\nperceive({tgt!r}) -> {len(els)} els: {names}")
        except Exception as e:
            print(f"perceive({tgt!r}) failed: {e}")

    # 4. does Escape close it?
    await page.keyboard.press("Escape"); await asyncio.sleep(1.5)
    h2 = await page.evaluate("() => location.hash")
    ads2 = await page.evaluate("() => document.querySelectorAll('iframe[id*=aswift],iframe[src*=googleads]').length")
    print(f"\nafter ESCAPE: hash={h2!r}, ad-iframes={ads2}")

    await p.close()


asyncio.run(main())
