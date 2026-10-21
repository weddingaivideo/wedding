"""Empirical overflow bisect on the two remaining pages."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.async_api import async_playwright  # noqa: E402

from common import UA, to_local  # noqa: E402

BISECT = """() => {
    const de = document.documentElement;
    const before = de.scrollWidth - de.clientWidth;
    const log = [{step: 'baseline', overflow: before}];
    const t = document.querySelector('table.full-pricing-table, table.comparison-table');
    if (t) {
        const cs = getComputedStyle(t);
        log.push({step: 'table computed', display: cs.display, overflowX: cs.overflowX, width: Math.round(t.getBoundingClientRect().width),
                  scrollWidth: t.scrollWidth, clientWidth: t.clientWidth});
        t.style.overflowX = 'hidden';
        log.push({step: 'table overflow-x:hidden', overflow: de.scrollWidth - de.clientWidth});
        t.style.overflowX = '';
        t.style.display = 'table';
        log.push({step: 'table display:table (revert block)', overflow: de.scrollWidth - de.clientWidth});
        t.style.display = '';
    }
    // hide each top-level section one at a time
    document.querySelectorAll('body > *, main > *').forEach((el, i) => {
        const prev = el.style.display;
        el.style.display = 'none';
        const o = de.scrollWidth - de.clientWidth;
        el.style.display = prev;
        if (o < before) log.push({step: `hiding <${el.tagName.toLowerCase()} class="${String(el.className).slice(0,40)}">`, overflow: o});
    });
    return log;
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

        for path in ["/de/tools/wedding-hashtag-generator/", "/resources/"]:
            pg = await ctx.new_page()
            await pg.route("**/*", block)
            import time
            url = to_local(path) + ("?nocache=" + str(int(time.time())))
            await pg.goto(url, wait_until="load", timeout=90000)
            await pg.wait_for_timeout(600)
            print(f"\n===== {path} =====")
            for row in await pg.evaluate(BISECT):
                print("   ", row)
            await pg.close()
        await ctx.close()
        await b.close()


asyncio.run(main())
