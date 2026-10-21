"""Post-fix verification for UX-001: with the panel capped and scrollable, is every
menu entry reachable on a real phone viewport?"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.async_api import async_playwright  # noqa: E402

from common import UA, to_local  # noqa: E402

DEVICES = [("iPhone SE", 375, 667), ("Galaxy S8", 360, 740), ("iPhone 12", 390, 844),
           ("iPhone 14 Pro Max", 430, 932), ("iPad mini", 768, 1024)]

REACH_JS = """() => {
    const n = document.querySelector('.main-nav');
    const items = Array.from(n.querySelectorAll('a, button, select'))
        .filter(e => e.offsetParent !== null || e.getClientRects().length);
    // scroll the PANEL (not the page) to the bottom, like a thumb swipe would
    n.scrollTop = n.scrollHeight;
    const navRect = n.getBoundingClientRect();
    const atBottom = Array.from(items).filter(e => {
        const r = e.getBoundingClientRect();
        return r.top >= navRect.top - 1 && r.bottom <= navRect.bottom + 1;
    });
    const stillOut = items.filter(e => {
        const r = e.getBoundingClientRect();
        return r.bottom > window.innerHeight + 1;
    }).map(e => (e.textContent || e.tagName).replace(/\\s+/g, ' ').trim().slice(0, 22));
    return {
        scrollable: n.scrollHeight > n.clientHeight,
        scrollHeight: n.scrollHeight, clientHeight: n.clientHeight,
        scrollTopAfter: Math.round(n.scrollTop),
        items: items.length,
        visibleAtTop: items.filter(e => e.getBoundingClientRect().bottom <= window.innerHeight + 1).length,
        visibleAtBottom: atBottom.length,
        beyondViewportEvenAfterScrolling: stillOut,
    };
}"""


async def main() -> None:
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        allgood = True
        for name, w, h in DEVICES:
            ctx = await b.new_context(viewport={"width": w, "height": h}, user_agent=UA,
                                      service_workers="block", locale="en-US", has_touch=True)
            await ctx.add_init_script("try{localStorage.setItem('wa_cookie_consent','all')}catch(e){}")

            async def block(route):
                from urllib.parse import urlparse
                u = urlparse(route.request.url)
                return await route.continue_() if u.hostname in ("127.0.0.1", "localhost") else await route.abort()

            pg = await ctx.new_page()
            await pg.route("**/*", block)
            await pg.goto(to_local("/"), wait_until="load")
            await pg.wait_for_timeout(400)
            await pg.click(".mobile-menu-toggle")
            await pg.wait_for_timeout(350)
            r = await pg.evaluate(REACH_JS)
            ok = len(r["beyondViewportEvenAfterScrolling"]) == 0
            allgood = allgood and ok
            print(f"{'PASS' if ok else 'FAIL'}  {name:<18} {w}x{h}  "
                  f"panel scrollHeight={r['scrollHeight']} clientHeight={r['clientHeight']} "
                  f"scrollable={r['scrollable']} | items={r['items']} "
                  f"visible top={r['visibleAtTop']} bottom={r['visibleAtBottom']} "
                  f"| still out of reach={r['beyondViewportEvenAfterScrolling']}")
            # can we actually reach and click the primary CTA?
            cta = await pg.evaluate("""() => {
                const a = Array.from(document.querySelectorAll('.main-nav a'))
                    .find(x => /quote|order/i.test(x.getAttribute('href') || ''));
                if (!a) return {found: false};
                a.scrollIntoView({block: 'center'});
                const r = a.getBoundingClientRect();
                return {found: true, text: a.textContent.trim().slice(0,24),
                        inViewport: r.top >= 0 && r.bottom <= window.innerHeight, top: Math.round(r.top), bottom: Math.round(r.bottom)};
            }""")
            print(f"        CTA reachable after panel scroll: {cta}")
            await pg.close()
            await ctx.close()
        await b.close()
        print("\nUX-001 verification:", "ALL PASS" if allgood else "STILL FAILING")


asyncio.run(main())
