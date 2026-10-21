"""Focused probe: why do 3 tools fail to decode a valid JPEG?

Tries several real-world JPEG flavours (baseline / progressive / EXIF-rotated /
CMYK-ish / browser-generated) plus PNG, on the tools that reported
"Could not decode this file".
"""
import asyncio
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image, ImageDraw  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402

from common import UA, to_local  # noqa: E402

OUT = Path(__file__).resolve().parent / "results" / "fixtures"
OUT.mkdir(parents=True, exist_ok=True)

TOOLS = ["/tools/compress-wedding-photos/", "/tools/crop-wedding-photo-for-reels/",
         "/tools/remove-background-wedding-portrait/", "/tools/heic-to-jpg-wedding-photos/",
         "/tools/wedding-photo-collage/"]


def build_fixtures() -> dict:
    f = {}

    def photo(w=1600, h=1200):
        img = Image.new("RGB", (w, h))
        px = img.load()
        for y in range(0, h, 4):
            for x in range(0, w, 4):
                px[x, y] = ((x * 7 + y * 3) % 256, (x * 3) % 256, (y * 5) % 256)
        d = ImageDraw.Draw(img)
        d.ellipse((200, 200, w - 200, h - 200), fill=(240, 200, 160))
        return img

    p = OUT / "photo-baseline.jpg"
    if not p.exists():
        photo().save(p, "JPEG", quality=88)
    f["baseline jpg"] = p

    p = OUT / "photo-progressive.jpg"
    if not p.exists():
        photo(1200, 900).save(p, "JPEG", quality=88, progressive=True)
    f["progressive jpg"] = p

    p = OUT / "photo-exif.jpg"
    if not p.exists():
        im = photo(1200, 900)
        exif = im.getexif()
        exif[274] = 6  # Orientation: rotate 90 CW (as phones write)
        im.save(p, "JPEG", quality=90, exif=exif)
    f["exif-rotated jpg"] = p

    p = OUT / "photo.png"
    if not p.exists():
        photo(1000, 800).save(p, "PNG")
    f["png"] = p

    p = OUT / "photo.webp"
    if not p.exists():
        photo(1000, 800).save(p, "WEBP", quality=85)
    f["webp"] = p

    p = OUT / "small.jpg"
    if not p.exists():
        Image.new("RGB", (600, 400), (200, 120, 90)).save(p, "JPEG", quality=70)
    f["small jpg"] = p
    return f


async def try_upload(pg, path: Path):
    await pg.evaluate("() => { const i = document.querySelector('input[type=file]'); if (i) i.value = ''; }")
    try:
        await pg.set_input_files("input[type=file]", str(path))
        await pg.wait_for_timeout(1400)
    except Exception as exc:  # noqa: BLE001
        return f"set_input_files failed: {exc}"[:80]
    return await pg.evaluate("""() => {
        const st = ((document.querySelector('[class*="status"], #status, [role="status"], .wa-tool-error, .error-msg')||{}).textContent||'')
            .replace(/\\s+/g,' ').trim();
        const thumbs = document.querySelectorAll('img[src^="blob:"], canvas, .wa-tool-thumb, [class*="thumb"]').length;
        const f = document.querySelector('input[type=file]');
        const fi = f && f.files[0];
        return {status: st.slice(0,120), thumbs,
                fileInfo: fi ? fi.name + ' / ' + fi.type + ' / ' + fi.size + 'B' : 'none',
                emptyState: ((document.querySelector('#empty-state, [class*="empty"]')||{}).textContent||'').trim().slice(0,60)};
    }""")


async def main() -> None:
    fixtures = build_fixtures()
    for p in fixtures.values():
        with Image.open(p) as im:
            print(f"fixture {p.name:<24} {im.format:<5} {im.size} mode={im.mode} "
                  f"{p.stat().st_size}B magic={p.read_bytes()[:3].hex()}")

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

        for tool in TOOLS:
            print(f"\n===== {tool} =====")
            pg = await ctx.new_page()
            await pg.route("**/*", block)
            await pg.goto(to_local(tool), wait_until="load", timeout=60000)
            await pg.wait_for_timeout(500)
            accept = await pg.evaluate("() => (document.querySelector('input[type=file]')||{}).accept")
            print(f"  accept = {accept!r}")
            for label, path in fixtures.items():
                res = await try_upload(pg, path)
                verdict = "OK " if (res["thumbs"] and "decode" not in res["status"].lower()) else "FAIL"
                print(f"  [{verdict}] {label:<16} file={res['fileInfo']:<34} thumbs={res['thumbs']} status={res['status'][:80]!r}")
                await pg.reload(wait_until="load")
                await pg.wait_for_timeout(400)
            await pg.close()
        await ctx.close()
        await b.close()


asyncio.run(main())
