"""Focused mobile-nav probe: is the open panel scrollable, and does focus stay inside?"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.async_api import async_playwright  # noqa: E402

from common import UA, to_local  # noqa: E402


async def main() -> None:
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, user_agent=UA,
                                  service_workers="block", locale="en-US",
                                  is_mobile=False, has_touch=True)
        await ctx.add_init_script("try{localStorage.setItem('wa_cookie_consent','all')}catch(e){}")

        async def block(route):
            from urllib.parse import urlparse
            u = urlparse(route.request.url)
            return await route.continue_() if u.hostname in ("127.0.0.1", "localhost") else await route.abort()

        pg = await ctx.new_page()
        await pg.route("**/*", block)
        await pg.goto(to_local("/"), wait_until="load")
        await pg.wait_for_timeout(500)

        await pg.click(".mobile-menu-toggle")
        await pg.wait_for_timeout(400)

        geo = await pg.evaluate("""() => {
            const n = document.querySelector('.main-nav');
            const cs = getComputedStyle(n);
            const r = n.getBoundingClientRect();
            const focusables = n.querySelectorAll('a, button, select, input, [tabindex]:not([tabindex="-1"])');
            const last = focusables[focusables.length - 1];
            return {
                panelTop: Math.round(r.top), panelBottom: Math.round(r.bottom),
                panelHeight: Math.round(r.height), viewportH: window.innerHeight,
                overflowY: cs.overflowY, position: cs.position, zIndex: cs.zIndex,
                scrollable: n.scrollHeight > n.clientHeight,
                clientHeight: n.clientHeight, scrollHeight: n.scrollHeight,
                focusableCount: focusables.length,
                lastFocusable: last ? last.tagName + ':' + (last.textContent||'').trim().slice(0,24) : null,
                lastFocusableBottom: last ? Math.round(last.getBoundingClientRect().bottom) : null,
                navChildren: Array.from(n.querySelectorAll('*')).filter(e => e.tabIndex >= 0)
                    .map(e => e.tagName.toLowerCase() + (e.id ? '#'+e.id : '') + (e.textContent||'').trim().slice(0,14)),
            };
        }""")
        print("=== open mobile menu geometry (390x844) ===")
        for k, v in geo.items():
            if k == "navChildren":
                print(f"  {k}: {v[:26]}")
            else:
                print(f"  {k}: {v}")

        # can the user reach the last menu item?
        reach = await pg.evaluate("""() => {
            const n = document.querySelector('.main-nav');
            const f = n.querySelectorAll('a, button, select, input, [tabindex]:not([tabindex="-1"])');
            const last = f[f.length - 1];
            last.scrollIntoView({block: 'center'});
            const r = last.getBoundingClientRect();
            return {afterScrollTop: Math.round(n.getBoundingClientRect().top),
                    lastVisibleTop: Math.round(r.top), lastVisibleBottom: Math.round(r.bottom),
                    inViewport: r.top >= 0 && r.bottom <= window.innerHeight};
        }""")
        print("\n=== after scrollIntoView on the last menu item ===")
        print(f"  {reach}")

        # focus order inside the open menu
        await pg.evaluate("() => window.scrollTo(0,0)")
        await pg.click(".mobile-menu-toggle")
        await pg.wait_for_timeout(300)
        trail = []
        for i in range(geo["focusableCount"] + 4):
            await pg.keyboard.press("Tab")
            el = await pg.evaluate("""() => {
                const a = document.activeElement;
                if (!a) return 'none';
                return a.tagName.toLowerCase() + (a.id ? '#' + a.id : '') +
                       (a.className && typeof a.className === 'string' ? '.' + a.className.split(/\\s+/)[0] : '') +
                       '[' + (a.textContent||'').trim().slice(0,14) + ']' +
                       (a.closest('.main-nav') ? '' : '  <-- OUTSIDE MENU');
            }""")
            trail.append(el)
        escaped = [t for t in trail if "OUTSIDE MENU" in t]
        print(f"\n=== tab order through the open menu ({len(trail)} tabs) ===")
        print(f"  focusables in menu: {geo['focusableCount']}")
        print(f"  tabs that escaped the menu: {len(escaped)}")
        for t in trail[:6]:
            print("   ", t)
        if escaped:
            print("    ...")
            for t in trail[-6:]:
                print("   ", t)
        await pg.close()
        await ctx.close()
        await b.close()


asyncio.run(main())
