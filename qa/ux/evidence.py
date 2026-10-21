"""Evidence capture.

1. Mobile screenshots of the worst horizontal-overflow pages (390px viewport,
   scrolled to the offending element) so the report shows the defect, not just
   a number.
2. A small, paced spot-check against production (weddingai.video) to separate
   local-only artefacts (Cloudflare /cdn-cgi scripts, miniflare) from real
   production defects, and to measure the real compressed page weight.

Production probes are deliberately few and paced: Cloudflare throttles bursts
and starts answering 503 error 1102.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.async_api import async_playwright  # noqa: E402

from common import BASE, RESULTS, SHOTS, UA, save, to_local  # noqa: E402

OVERFLOW_PAGES = [
    "/ai-wedding-video-generator/",
    "/tools/wedding-seating-chart-maker/",
    "/tools/compress-wedding-photos/",
    "/pricing/",
    "/services/absence-compensation/family-tribute/",
    "/tools/wedding-video-invitation-maker/",
]

PROD_PATHS = [
    "/",
    "/pricing/",
    "/ai-wedding-video-generator/",
    "/success/",
    "/zh/",
    "/blog/",
]


async def shoot() -> list[dict]:
    out = []
    SHOTS.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=["--disable-dev-shm-usage"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, user_agent=UA,
                                  service_workers="block", locale="en-US")
        await ctx.add_init_script("try{localStorage.setItem('wa_cookie_consent','all')}catch(e){}")

        async def block(route):
            u = urlparse(route.request.url)
            if u.hostname in ("127.0.0.1", "localhost") or u.scheme not in ("http", "https"):
                return await route.continue_()
            await route.abort()

        for path in OVERFLOW_PAGES:
            pg = await ctx.new_page()
            await pg.route("**/*", block)
            try:
                await pg.goto(to_local(path), wait_until="load", timeout=45000)
                await pg.wait_for_timeout(400)
                ov = await pg.evaluate("""() => {
                    const de = document.documentElement;
                    return de.scrollWidth - de.clientWidth;
                }""")
                # scroll the first over-wide element into view
                await pg.evaluate("""() => {
                    const vw = de = document.documentElement.clientWidth;
                    const all = document.body.querySelectorAll('*');
                    for (const el of all) {
                        const r = el.getBoundingClientRect();
                        if (r.right > vw + 4 && r.width > 0) { el.scrollIntoView({block:'center'}); return; }
                    }
                }""")
                await pg.wait_for_timeout(500)
                name = f"overflow-{path.strip('/').replace('/', '_') or 'home'}-390.png"
                await pg.screenshot(path=str(SHOTS / name))
                out.append({"path": path, "overflowX": ov, "shot": name})
                print(f"  shot {path} overflow={ov}px -> {name}", flush=True)
            except Exception as exc:  # noqa: BLE001
                print(f"  shot {path} FAILED: {exc}"[:120], flush=True)
            await pg.close()
        await ctx.close()
        await b.close()
    return out


def prod_probe() -> list[dict]:
    import urllib.error
    import urllib.request
    res = []
    for p in PROD_PATHS:
        url = "https://weddingai.video" + p
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, br"})
        rec = {"path": p}
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
                rec.update({
                    "status": r.status,
                    "encoding": r.headers.get("Content-Encoding"),
                    "cache": r.headers.get("Cache-Control"),
                    "cf_cache": r.headers.get("CF-Cache-Status"),
                    "bytes": len(body),
                    "server_timing": (r.headers.get("Server-Timing") or "")[:120],
                })
        except urllib.error.HTTPError as e:
            rec.update({"status": e.code, "error": str(e)[:120]})
        except Exception as exc:  # noqa: BLE001
            rec.update({"status": 0, "error": str(exc)[:120]})
        print(f"  PROD {p:<36} {rec.get('status')} enc={rec.get('encoding')} "
              f"bytes={rec.get('bytes')} cf={rec.get('cf_cache')}", flush=True)
        res.append(rec)
        time.sleep(1.2)  # stay well under any Cloudflare burst throttle

    # the /cdn-cgi/ email-decode script that 404s locally
    for p in ["/cdn-cgi/scripts/5c5dd728/cloudflare-static/email-decode.min.js"]:
        req = urllib.request.Request("https://weddingai.video" + p, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                print(f"  PROD {p} -> {r.status} ({r.headers.get('content-type')})", flush=True)
                res.append({"path": p, "status": r.status})
        except urllib.error.HTTPError as e:
            print(f"  PROD {p} -> {e.code}", flush=True)
            res.append({"path": p, "status": e.code})
        except Exception as exc:  # noqa: BLE001
            print(f"  PROD {p} -> {exc}"[:100], flush=True)
            res.append({"path": p, "status": 0, "error": str(exc)[:100]})
    return res


def main() -> None:
    print("== mobile overflow evidence ==", flush=True)
    shots = asyncio.run(shoot())
    save("evidence-shots.json", shots)
    print("== production spot-check (paced) ==", flush=True)
    prod = prod_probe()
    save("evidence-prod.json", prod)


if __name__ == "__main__":
    main()
