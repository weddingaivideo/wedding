"""Last remaining overflow page: why is table.full-pricing-table still wide?"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.async_api import async_playwright  # noqa: E402

from common import UA, to_local  # noqa: E402

JS = """() => {
    const t = document.querySelector('table.full-pricing-table');
    if (!t) return {found: false, overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth};
    const cs = getComputedStyle(t);
    const chain = [];
    let p = t;
    for (let i = 0; i < 6 && p; i++) {
        const s = getComputedStyle(p);
        const r = p.getBoundingClientRect();
        chain.push(p.tagName.toLowerCase() + (p.id ? '#' + p.id : '') +
                   (typeof p.className === 'string' && p.className ? '.' + p.className.trim().split(/\\s+/).slice(0, 2).join('.') : '') +
                   ' w=' + Math.round(r.width) + ' d=' + s.display + ' ovx=' + s.overflowX +
                   ' minw=' + s.minWidth + ' maxw=' + s.maxWidth);
        p = p.parentElement;
    }
    // which ancestor actually sticks out?
    const vw = document.documentElement.clientWidth;
    const wide = [];
    document.querySelectorAll('body *').forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width > 0 && r.right > vw + 2 && getComputedStyle(el).position !== 'fixed') {
            let inScroller = false, q = el.parentElement;
            while (q && q !== document.documentElement) {
                if (/(auto|scroll|hidden|clip)/.test(getComputedStyle(q).overflowX)) { inScroller = true; break; }
                q = q.parentElement;
            }
            if (!inScroller) wide.push(el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\\s+/)[0] : '') + ' right=' + Math.round(r.right));
        }
    });
    return {
        found: true,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        tableDisplay: cs.display, tableOverflowX: cs.overflowX,
        tableWidth: Math.round(t.getBoundingClientRect().width),
        tableScrollW: t.scrollWidth, tableClientW: t.clientWidth,
        tableInline: t.getAttribute('style'),
        chain, wideNotInScroller: wide.slice(0, 6),
    };
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

        pg = await ctx.new_page()
        await pg.route("**/*", block)
        await pg.goto(to_local("/tools/wedding-budget-calculator/") + "?nc=" + str(int(time.time())),
                      wait_until="load", timeout=90000)
        await pg.wait_for_timeout(500)
        r = await pg.evaluate(JS)
        print("overflow:", r["overflow"], "px  (found table:", r["found"], ")")
        if r["found"]:
            print("table: display=" + r["tableDisplay"] + " overflowX=" + r["tableOverflowX"] +
                  " width=" + str(r["tableWidth"]) + " scrollWidth=" + str(r["tableScrollW"]) +
                  " clientWidth=" + str(r["tableClientW"]) + " inline=" + str(r["tableInline"]))
            print("ancestors:")
            for c in r["chain"]:
                print("   ", c)
        print("elements outside any scroller that stick out:", r["wideNotInScroller"])
        await pg.close()
        await ctx.close()
        await b.close()


asyncio.run(main())
