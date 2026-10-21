"""Per-tool functional verdict.

For every one of the 13 tools: upload a real photo, then measure
  (a) does the uploaded image actually DECODE (blob <img>.naturalWidth > 0) or is
      it blocked (CSP img-src without blob:) - a broken <img> element still counts
      as "present", which is why naive checks miss this;
  (b) does the primary action produce output or an error message.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.async_api import async_playwright  # noqa: E402

from common import UA, to_local  # noqa: E402

FIX = Path(__file__).resolve().parent / "results" / "fixtures"
PHOTO = FIX / "photo-baseline.jpg"

TOOLS = [
    "add-text-to-wedding-photo", "compress-wedding-photos", "crop-wedding-photo-for-reels",
    "heic-to-jpg-wedding-photos", "remove-background-wedding-portrait", "save-the-date-maker",
    "wedding-budget-calculator", "wedding-hashtag-generator", "wedding-invitation-maker",
    "wedding-photo-book-planner", "wedding-photo-collage", "wedding-seating-chart-maker",
    "wedding-video-invitation-maker",
]

DECODE_JS = """() => {
    const imgs = Array.from(document.images).filter(i => (i.currentSrc||i.src||'').startsWith('blob:'));
    const decoded = imgs.filter(i => i.naturalWidth > 0).length;
    return {blobImgs: imgs.length, decoded: decoded,
            broken: imgs.filter(i => i.naturalWidth === 0).length,
            canvases: Array.from(document.querySelectorAll('canvas'))
                .map(c => c.width + 'x' + c.height + (c.width && c.height ? '' : ' (empty)'))};
}"""

RUN_JS = """() => {
    const btns = Array.from(document.querySelectorAll('button')).filter(b => b.offsetParent !== null && !b.disabled);
    const primary = btns.find(b => /run|generate|create|make|start|convert|compress|apply|calculate|preview|render/i.test(b.id + ' ' + b.textContent));
    return {id: primary ? primary.id : null, text: primary ? primary.textContent.trim().slice(0, 34) : null};
}"""

RESULT_JS = """() => {
    const txt = document.body.innerText;
    const decodeErr = (txt.match(/Could not decode[^\\n]*/) || [''])[0];
    const otherErr = (txt.match(/(Error|error|failed|unsupported)[^\\n]{0,80}/) || [''])[0];
    return {
        decodeError: decodeErr,
        status: ((document.querySelector('#status, .status, [class*="status"], [role="status"], #summary') || {}).textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 120),
        downloadLinks: document.querySelectorAll('a[download], a[href^="blob:"]').length,
        blobOutputs: Array.from(document.querySelectorAll('[src^="blob:"], [href^="blob:"]')).length,
        toast: ((document.querySelector('[class*="toast"]') || {}).textContent || '').trim().slice(0, 60),
        otherErr: otherErr,
    };
}"""


async def main() -> None:
    print(f"{'tool':<38}{'decode':<22}{'primary action':<26}{'output'}")
    print("-" * 110)
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1280, "height": 900}, user_agent=UA,
                                  service_workers="block", locale="en-US")
        await ctx.add_init_script("try{localStorage.setItem('wa_cookie_consent','all')}catch(e){}")

        async def block(route):
            from urllib.parse import urlparse
            u = urlparse(route.request.url)
            return await route.continue_() if u.hostname in ("127.0.0.1", "localhost") else await route.abort()

        rows = []
        for slug in TOOLS:
            path = f"/tools/{slug}/"
            pg = await ctx.new_page()
            await pg.route("**/*", block)
            errs: list[str] = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:80]))
            try:
                await pg.goto(to_local(path), wait_until="load", timeout=60000)
                await pg.wait_for_timeout(500)
                has_file = await pg.evaluate("() => !!document.querySelector('input[type=file]')")
                if not has_file:
                    rows.append({"slug": slug, "verdict": "no upload (generator/calculator)"})
                    print(f"{slug:<38}{'n/a':<22}{'n/a':<26}n/a")
                    await pg.close()
                    continue
                await pg.set_input_files("input[type=file]", str(PHOTO))
                await pg.wait_for_timeout(2000)
                dec = await pg.evaluate(DECODE_JS)
                decode_state = ("OK " + str(dec["decoded"]) if dec["decoded"] else
                                ("BLOCKED(" + str(dec["broken"]) + " broken)" if dec["broken"] else "no blob img"))
                run = await pg.evaluate(RUN_JS)
                out_txt = ""
                if run["id"]:
                    try:
                        await pg.click(f"#{run['id']}", timeout=6000)
                        await pg.wait_for_timeout(3500)
                    except Exception as exc:  # noqa: BLE001
                        out_txt = f"click failed: {str(exc)[:40]}"
                    res = await pg.evaluate(RESULT_JS)
                    produced = res["downloadLinks"] or res["blobOutputs"]
                    if res["decodeError"]:
                        verdict = "BROKEN: " + res["decodeError"][:46]
                    elif produced:
                        verdict = f"OK ({res['downloadLinks']} dl / {res['blobOutputs']} blob)"
                    elif res["status"]:
                        verdict = f"ran, no file: {res['status'][:44]}"
                    else:
                        verdict = "ran, no output detected"
                    action = f"{run['id'] or '?'} {'✓' if res['downloadLinks'] else '✗'}"
                else:
                    verdict = "no enabled primary button"
                    action = "n/a"
                rows.append({"slug": slug, "decode": dec, "run": run, "verdict": verdict, "errors": errs[:2]})
                print(f"{slug:<38}{decode_state:<22}{action:<26}{verdict}")
            except Exception as exc:  # noqa: BLE001
                print(f"{slug:<38}ERROR {type(exc).__name__}: {str(exc)[:60]}")
                rows.append({"slug": slug, "verdict": f"ERROR {type(exc).__name__}"})
            await pg.close()
        await ctx.close()
        await b.close()

    import json
    (Path(__file__).resolve().parent / "results" / "tool-verdicts.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("\nsaved results/tool-verdicts.json")


asyncio.run(main())
