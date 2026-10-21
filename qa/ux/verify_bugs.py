"""Verify the search-results link bug and re-check the false-positive FAILs."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.async_api import async_playwright  # noqa: E402

from common import BASE, UA, to_local  # noqa: E402


async def main() -> None:
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1280, "height": 900}, user_agent=UA,
                                  service_workers="block", locale="en-US")
        await ctx.add_init_script("try{localStorage.setItem('wa_cookie_consent','all')}catch(e){}")

        async def block(route):
            from urllib.parse import urlparse
            u = urlparse(route.request.url)
            if u.hostname in ("127.0.0.1", "localhost"):
                return await route.continue_()
            await route.abort()

        # ---- 1. search result links ----
        pg = await ctx.new_page()
        await pg.route("**/*", block)
        await pg.goto(to_local("/search/?q=wedding+video"), wait_until="load")
        await pg.wait_for_timeout(700)
        res = await pg.evaluate("""() => {
            const items = Array.from(document.querySelectorAll('.search-result h3 a'));
            return {
                count: items.length,
                links: items.slice(0, 6).map(a => ({attr: a.getAttribute('href'), resolved: a.href,
                                                     title: (a.textContent||'').trim().slice(0,40)})),
                noResults: !!document.querySelector('.no-results'),
            };
        }""")
        print("=== /search/?q=wedding+video ===")
        print(f"  results rendered: {res['count']}, no-results block: {res['noResults']}")
        for l in res["links"]:
            print(f"   attr={l['attr']!r}\n     -> resolves to {l['resolved']}  ({l['title']})")
        await pg.close()

        # ---- 2. pricing plan cards: correct class names ----
        pg = await ctx.new_page()
        await pg.route("**/*", block)
        await pg.goto(to_local("/pricing/"), wait_until="load")
        await pg.wait_for_timeout(400)
        pr = await pg.evaluate("""() => {
            const classes = new Set();
            document.querySelectorAll('div,section,article').forEach(e => {
                if (e.className && typeof e.className === 'string') e.className.split(/\\s+/)
                    .forEach(c => { if (/price|plan|tier|package/i.test(c)) classes.add(c); });
            });
            const tiers = document.querySelectorAll('.pricing-tier').length;
            return {classes: Array.from(classes).slice(0, 12), pricingTier: tiers,
                    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
                    offenders: (() => {
                        const vw = document.documentElement.clientWidth, out = [];
                        document.querySelectorAll('body *').forEach(e => {
                            const r = e.getBoundingClientRect();
                            if (r.width > 0 && r.right > vw + 2 && getComputedStyle(e).position !== 'fixed')
                                out.push(e.tagName.toLowerCase() + '.' + String(e.className).slice(0,40) + ' w=' + Math.round(r.width));
                        });
                        return out.slice(0, 5);
                    })()};
        }""")
        print("\n=== /pricing/ at 1280px ===")
        print(f"  .pricing-tier count: {pr['pricingTier']}, overflow: {pr['overflow']}px")
        print(f"  price/plan-ish classes: {pr['classes']}")
        print(f"  offenders: {pr['offenders']}")

        # 390px overflow offender for pricing
        await pg.set_viewport_size({"width": 390, "height": 844})
        await pg.wait_for_timeout(400)
        pr2 = await pg.evaluate("""() => {
            const vw = document.documentElement.clientWidth, out = [];
            document.querySelectorAll('body *').forEach(e => {
                const r = e.getBoundingClientRect();
                if (r.width > 0 && r.right > vw + 2 && getComputedStyle(e).position !== 'fixed')
                    out.push({el: e.tagName.toLowerCase() + '.' + String(e.className).slice(0,44), w: Math.round(r.width), right: Math.round(r.right)});
            });
            return {overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth, offenders: out.slice(0, 6)};
        }""")
        print(f"  390px overflow: {pr2['overflow']}px -> {pr2['offenders']}")
        await pg.close()

        # ---- 3. order page: which field is unlabelled ----
        pg = await ctx.new_page()
        await pg.route("**/*", block)
        await pg.goto(to_local("/order/"), wait_until="load")
        await pg.wait_for_timeout(400)
        od = await pg.evaluate("""() => Array.from(document.querySelectorAll('input,select,textarea'))
            .filter(e => !['hidden','submit','button'].includes(e.type))
            .map(e => ({id: e.id, name: e.name, type: e.type,
                        labelled: !!(e.getAttribute('aria-label') || (e.id && document.querySelector('label[for="'+e.id+'"]')) || e.closest('label')),
                        visible: e.offsetParent !== null, parentDisplay: getComputedStyle(e.parentElement).display}))""")
        print("\n=== /order/ fields ===")
        for f in od:
            print(f"   #{f['id'] or '-':<14} name={f['name']:<12} type={f['type']:<8} labelled={f['labelled']} visible={f['visible']} parent={f['parentDisplay']}")
        await pg.close()

        # ---- 4. /api/quote behaviour locally ----
        pg = await ctx.new_page()
        await pg.route("**/*", block)
        await pg.goto(to_local("/order/"), wait_until="load")
        await pg.wait_for_timeout(300)
        form = await pg.evaluate("""() => {
            const f = document.querySelector('.order-form') || document.querySelector('form');
            return f ? {action: f.getAttribute('action'), method: f.getAttribute('method')} : null;
        }""")
        print(f"\n=== order form target: {form} ===")
        r = await pg.request.post(BASE + "/api/quote", form={
            "name": "UX Test", "email": "ux-test@example.com", "service": "ai-video-generator",
            "budget": "100-300", "details": "Automated UX test submission", "country": "US",
            "reference_id": "WA-20260101-TEST"})
        print(f"  POST /api/quote -> {r.status}")
        print(f"  location header: {r.headers.get('location')}")
        print(f"  body (first 300): {(await r.text())[:300]!r}")
        await pg.close()
        await ctx.close()
        await b.close()


asyncio.run(main())
