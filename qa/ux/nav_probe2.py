"""Corrected mobile-nav verification.

1) Is the open menu panel reachable on real phone viewports? (menu open state is
   asserted before measuring, and several device heights are tried.)
2) Does the focus trap actually hold while the menu is OPEN?
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.async_api import async_playwright  # noqa: E402

from common import UA, to_local  # noqa: E402

DEVICES = [("iPhone SE", 375, 667), ("iPhone 12", 390, 844), ("iPhone 14 Pro Max", 430, 932),
           ("Galaxy S8", 360, 740), ("iPad mini", 768, 1024)]


async def open_menu(pg):
    state = await pg.evaluate("() => document.querySelector('.main-nav').classList.contains('active')")
    if not state:
        await pg.click(".mobile-menu-toggle")
        await pg.wait_for_timeout(400)
    return await pg.evaluate("() => document.querySelector('.main-nav').classList.contains('active')")


async def main() -> None:
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
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
            await pg.wait_for_timeout(500)
            opened = await open_menu(pg)
            g = await pg.evaluate("""() => {
                const n = document.querySelector('.main-nav');
                const header = document.querySelector('.site-header') || n.parentElement;
                const hcs = getComputedStyle(header);
                const ncs = getComputedStyle(n);
                const r = n.getBoundingClientRect();
                const focusables = Array.from(n.querySelectorAll('a, button, select, input, [tabindex]:not([tabindex="-1"])'))
                    .filter(e => e.offsetParent !== null || e.getClientRects().length);
                const unreachable = focusables.filter(e => {
                    const b = e.getBoundingClientRect();
                    return b.bottom > window.innerHeight + 1 || b.top < 0;
                });
                return {
                    headerPosition: hcs.position,
                    navOverflowY: ncs.overflowY,
                    panelHeight: Math.round(r.height),
                    panelTop: Math.round(r.top),
                    panelBottom: Math.round(r.bottom),
                    viewportH: window.innerHeight,
                    focusables: focusables.length,
                    unreachable: unreachable.length,
                    unreachableLabels: unreachable.map(e => (e.textContent||e.tagName).replace(/\\s+/g,' ').trim().slice(0,22)),
                    docScrollable: document.scrollingElement.scrollHeight > window.innerHeight,
                };
            }""")
            print(f"\n=== {name} {w}x{h} (menu open={opened}) ===")
            print(f"  header position      : {g['headerPosition']}")
            print(f"  panel                : top={g['panelTop']} bottom={g['panelBottom']} height={g['panelHeight']} (viewport {g['viewportH']})")
            print(f"  nav overflow-y       : {g['navOverflowY']}   page scrollable: {g['docScrollable']}")
            print(f"  focusables in menu   : {g['focusables']}")
            print(f"  UNREACHABLE below fold: {g['unreachable']} {g['unreachableLabels'][:8]}")

            # can scrolling bring them into view?
            after = await pg.evaluate("""() => {
                const n = document.querySelector('.main-nav');
                const f = Array.from(n.querySelectorAll('a, button, select, input'));
                const last = f[f.length-1];
                window.scrollTo(0, 400);
                const r = last.getBoundingClientRect();
                const res = {scrollY: Math.round(window.scrollY), lastBottom: Math.round(r.bottom),
                             lastInViewport: r.bottom <= window.innerHeight && r.top >= 0};
                window.scrollTo(0, 0);
                return res;
            }""")
            print(f"  after scrolling page 400px: scrollY={after['scrollY']}, last item bottom={after['lastBottom']}, visible={after['lastInViewport']}")

            # focus trap, with the menu definitely open
            await open_menu(pg)
            escaped, trail = 0, []
            for i in range(g["focusables"] + 3):
                await pg.keyboard.press("Tab")
                info = await pg.evaluate("""() => {
                    const a = document.activeElement;
                    if (!a) return {out: false, label: 'none'};
                    return {out: !a.closest('.main-nav') && a !== document.querySelector('.mobile-menu-toggle'),
                            label: a.tagName.toLowerCase() + (a.id ? '#'+a.id : '') + '[' + (a.textContent||'').replace(/\\s+/g,' ').trim().slice(0,16) + ']'};
                }""")
                trail.append(info["label"] + ("  <-- ESCAPED" if info["out"] else ""))
                if info["out"]:
                    escaped += 1
            print(f"  focus trap            : {escaped}/{len(trail)} tabs escaped the open menu")
            print(f"    first 4: {trail[:4]}")
            print(f"    last  4: {trail[-4:]}")
            await pg.close()
            await ctx.close()
        await b.close()


asyncio.run(main())
