"""Why are two pages still overflowing after the fix? Inspect computed styles."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.async_api import async_playwright  # noqa: E402

from common import UA, to_local  # noqa: E402

PAGES = ["/de/tools/wedding-hashtag-generator/", "/resources/"]

JS = """() => {
    const out = {overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth, items: []};
    const vw = document.documentElement.clientWidth;
    document.querySelectorAll('body *').forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width > 0 && r.right > vw + 2 && getComputedStyle(el).position !== 'fixed') {
            let p = el, chain = [];
            for (let i = 0; i < 4 && p && p !== document.body; i++) {
                const cs = getComputedStyle(p);
                chain.push(p.tagName.toLowerCase() + (p.id ? '#' + p.id : '') +
                           (typeof p.className === 'string' && p.className ? '.' + p.className.trim().split(/\\s+/).join('.') : '') +
                           ` [d=${cs.display} ovx=${cs.overflowX} w=${Math.round(p.getBoundingClientRect().width)} minw=${cs.minWidth}]`);
                p = p.parentElement;
            }
            out.items.push({w: Math.round(r.width), right: Math.round(r.right), chain});
        }
    });
    out.items = out.items.slice(0, 4);
    const t = document.querySelector('.full-pricing-table, .comparison-table, .btn');
    out.rules = Array.from(document.styleSheets).flatMap(sh => {
        try { return Array.from(sh.cssRules); } catch (e) { return []; }
    }).filter(r => r.selectorText && /full-pricing-table|comparison-table/.test(r.selectorText))
     .map(r => r.cssText.slice(0, 220));
    out.stylesheetLinks = Array.from(document.querySelectorAll('link[rel=stylesheet]')).map(l => l.getAttribute('href'));
    return out;
}"""


async def main() -> None:
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, user_agent=UA,
                                  service_workers="block", locale="en-US")
        await ctx.add_init_script("try{localStorage.setItem('wa_cookie_consent','all')}catch(e){}")

        async def block(route):
            from urllib.parse import urlparse
            u = urlparse(route.request.url)
            return await route.continue_() if u.hostname in ("127.0.0.1", "localhost") else await route.abort()

        for path in PAGES:
            pg = await ctx.new_page()
            await pg.route("**/*", block)
            try:
                await pg.goto(to_local(path), wait_until="load", timeout=70000)
                await pg.wait_for_timeout(500)
                r = await pg.evaluate(JS)
                print(f"\n===== {path} · overflow {r['overflow']}px =====")
                print("  stylesheets:", r["stylesheetLinks"])
                print("  table rules found:")
                for rule in r["rules"]:
                    print("   ", rule)
                for it in r["items"]:
                    print(f"  offender w={it['w']} right={it['right']}")
                    for c in it["chain"]:
                        print("     ", c[:150])
            except Exception as exc:  # noqa: BLE001
                print(f"\n===== {path} FAILED: {type(exc).__name__}")
            await pg.close()
        await ctx.close()
        await b.close()


asyncio.run(main())
