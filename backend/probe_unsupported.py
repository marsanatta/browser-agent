"""One-off M5 probe: visit known bot-walled / login / CAPTCHA sites with the
real PlaywrightProvider + perceive(), record the OBSERVED state. Not a test;
run manually to produce the probe evidence."""

from __future__ import annotations

import asyncio
import json

from app.agent.perceive import perceive
from app.browser.provider import PlaywrightProvider

PROBES = [
    ("login-wall", "https://github.com/login"),
    ("captcha-demo", "https://www.google.com/recaptcha/api2/demo"),
    ("anti-bot-news", "https://www.g2.com/"),
]


async def probe(provider: PlaywrightProvider, label: str, url: str) -> dict:
    page = await provider.new_page()
    out: dict = {"label": label, "url": url}
    try:
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        out["http_status"] = resp.status if resp else None
        out["final_url"] = page.url
        out["title"] = await page.title()
        body = (await page.inner_text("body"))[:600]
        out["body_excerpt"] = body
        per = await perceive(page)
        out["n_interactive"] = len(per.elements)
        out["element_names"] = [e.name for e in per.elements[:15]]
        html = (await page.content()).lower()
        out["signals"] = {
            "has_password_field": await page.locator("input[type=password]").count() > 0,
            "mentions_captcha": "captcha" in html or "recaptcha" in html,
            "mentions_cloudflare": "cloudflare" in html or "cf-challenge" in html,
            "mentions_turnstile": "turnstile" in html,
            "mentions_datadome": "datadome" in html,
            "mentions_just_a_moment": "just a moment" in html or "checking your browser" in html,
            "login_word": "sign in" in html or "log in" in html or "login" in html,
        }
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        await page.close()
    return out


async def main() -> None:
    provider = PlaywrightProvider(headless=True)
    await provider.launch()
    results = []
    try:
        for label, url in PROBES:
            results.append(await probe(provider, label, url))
    finally:
        await provider.close()
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
