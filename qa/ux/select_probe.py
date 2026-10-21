"""Runtime DOM probe: where does the <span> inside <select> come from?"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from common import BASE, UA, to_local  # noqa: E402

PATHS = ["/es/order/", "/en/order/", "/ru/order/", "/ja/order/", "/th/order/", "/pt/order/", "/ar/order/"]


async def main() -> None:
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1280, "height": 900}, user_agent=UA,
                                  service_workers="block", locale="en-US")
        await ctx.add_init_script("try{localStorage.setItem('wa_cookie_consent','all')}catch(e){}")
        for path in PATHS:
            pg = await ctx.new_page()
            msgs = []
            pg.on("console", lambda m: msgs.append(m.text[:110]) if m.type == "error" else None)
            try:
                resp = await pg.goto(to_local(path), wait_until="load", timeout=60000)
                await pg.wait_for_timeout(600)
                info = await pg.evaluate("""() => {
                    const out = [];
                    document.querySelectorAll('select').forEach(sel => {
                        const kids = Array.from(sel.childNodes)
                            .map(n => n.nodeType === 1 ? n.tagName.toLowerCase() : '#text')
                            .filter((v, i, a) => a.indexOf(v) === i);
                        const stray = Array.from(sel.childNodes).filter(n => n.nodeType === 1 &&
                            !['OPTION','OPTGROUP','#text'].includes(n.tagName)).map(n => n.outerHTML.slice(0,90));
                        out.push({id: sel.id, childKinds: kids, stray: stray,
                                  optionCount: sel.options.length,
                                  firstOptionText: sel.options[0] ? sel.options[0].textContent.trim().slice(0,30) : null,
                                  value: sel.value});
                    });
                    return out;
                }""")
                print(f"\n{path}  status={resp.status if resp else '?'}")
                for s in info:
                    flag = "  <-- STRAY" if s["stray"] else ""
                    print(f"   select #{s['id']:<16} options={s['optionCount']:<3} children={s['childKinds']} "
                          f"first='{s['firstOptionText']}'{flag}")
                    for x in s["stray"]:
                        print(f"        stray: {x}")
                bad = [m for m in msgs if "span tag" in m]
                print(f"   span-in-select console msgs: {len(bad)}")
            except Exception as exc:  # noqa: BLE001
                print(f"\n{path} FAILED {type(exc).__name__}: {exc}"[:140])
            await pg.close()
        await ctx.close()
        await b.close()


asyncio.run(main())
