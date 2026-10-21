"""Page-by-page sweep for WeddingAI.video.

Runs a real Chromium against the local `wrangler pages dev` instance and records,
per page: HTTP status, redirect chain, console errors, uncaught exceptions, failed
/ 4xx same-origin requests, horizontal overflow (with the offending elements),
heading structure, duplicate ids, image alt/broken-image state, accessible names,
tap-target sizes (WCAG 2.2 AA 24px), form labelling, html lang vs URL lang, script
composition (does this page actually show the target language?), dead in-page
anchors, and a weight/timing snapshot.

Usage
-----
    python qa/ux/sweep.py --set en-mobile
    python qa/ux/sweep.py --set archetypes --viewports mobile,desktop --shots issues
    python qa/ux/sweep.py --set langs
    python qa/ux/links          # global internal-link check (threaded HTTP, no browser)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.async_api import async_playwright  # noqa: E402

from common import (  # noqa: E402
    BASE, LANGS, LANG_SCRIPT, PAGE_PROBE_JS, RESULTS, SHOTS, UA, VIEWPORTS,
    archetype_paths, blog_article_path, en_urls, lang_of, save, slugify, sitemap_urls,
    to_local,
)

ALLOW_HOST = ("127.0.0.1", "localhost")

# Console noise that is produced by the harness itself (we abort every third-party
# request and block the service worker) rather than by the site under test.
NOISE = (
    "net::ERR_FAILED",
    "net::ERR_BLOCKED_BY_CLIENT",
    "net::ERR_ABORTED",
    "Service Worker registration blocked",
    "Failed to load resource: net::",
    "third-party cookie",
    "willReadFrequently",
)


def build_set(name: str) -> list[str]:
    """Named URL sets."""
    if name == "en":
        return en_urls()
    if name == "archetypes":
        out: list[str] = []
        for lang in LANGS:
            out += archetype_paths(lang)
            out.append(blog_article_path(lang, 0))
        return out
    if name == "langs":
        # every sitemap URL of the non-EN languages, capped per language
        out = []
        cap = int(24)
        for lang in LANGS:
            if lang == "en":
                continue
            urls = sitemap_urls(lang)
            out += urls[:cap]
        return out
    if name == "lang-archetypes":
        out = []
        for lang in LANGS:
            out += archetype_paths(lang)
            out.append(blog_article_path(lang, 0))
        return out
    if name == "en-archetypes":
        out = archetype_paths("en") + [blog_article_path("en", 0), blog_article_path("en", 3)]
        return out
    if name == "tools":
        return ["/tools/"] + [f"/tools/{s}/" for s in [
            "add-text-to-wedding-photo", "compress-wedding-photos",
            "crop-wedding-photo-for-reels", "heic-to-jpg-wedding-photos",
            "remove-background-wedding-portrait", "save-the-date-maker",
            "wedding-budget-calculator", "wedding-hashtag-generator",
            "wedding-invitation-maker", "wedding-photo-book-planner",
            "wedding-photo-collage", "wedding-seating-chart-maker",
            "wedding-video-invitation-maker"]]
    if name == "special":
        return ["/404.html", "/search/", "/success/", "/success/?id=WA-20260101-ABCD",
                "/privacy/", "/terms/", "/resources/", "/ai-wedding-video-generator/"]
    # allow raw comma-separated paths
    return [p if p.startswith("/") else "/" + p for p in name.split(",")]


# --------------------------------------------------------------------------- #
# browser sweep
# --------------------------------------------------------------------------- #

async def check_page(context, path: str, vp_name: str, shot_mode: str) -> dict:
    page = await context.new_page()
    rec: dict = {"path": path, "lang": lang_of(path), "viewport": vp_name,
                 "consoleErrors": [], "pageErrors": [], "badResponses": [],
                 "failedRequests": [], "redirects": [], "blocked": 0}
    t0 = time.time()

    async def on_console(msg):
        if msg.type not in ("error", "warning"):
            return
        text = msg.text[:300]
        if any(n in text for n in NOISE):
            rec["suppressedConsole"] = rec.get("suppressedConsole", 0) + 1
            return
        rec["consoleErrors"].append({"type": msg.type, "text": text})

    async def on_pageerror(err):
        rec["pageErrors"].append(str(err)[:300])

    async def on_response(resp):
        try:
            u = urlparse(resp.url)
        except Exception:
            return
        if u.hostname in ALLOW_HOST and resp.status >= 400:
            rec["badResponses"].append({"status": resp.status, "url": resp.url.replace(BASE, "")[:140]})

    async def on_requestfailed(req):
        try:
            u = urlparse(req.url)
        except Exception:
            return
        err = (req.failure or "")
        # ERR_ABORTED is normal for <video preload="none"> range requests and for
        # our own route aborts - not a defect.
        if "ERR_ABORTED" in err:
            return
        if u.hostname in ALLOW_HOST:
            rec["failedRequests"].append({"url": req.url.replace(BASE, "")[:140], "err": err[:80]})

    async def route_handler(route):
        try:
            u = urlparse(route.request.url)
        except Exception:
            return await route.abort()
        if u.hostname in ALLOW_HOST or u.scheme not in ("http", "https"):
            return await route.continue_()
        rec["blocked"] += 1
        await route.abort()

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)
    page.on("response", on_response)
    page.on("requestfailed", on_requestfailed)
    await page.route("**/*", route_handler)

    try:
        # The local miniflare server occasionally drops a connection under load;
        # retry a couple of times so a flaky server is not reported as a site bug.
        last_exc = None
        for attempt in range(3):
            try:
                resp = await page.goto(to_local(path), wait_until="load", timeout=45000)
                break
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if "ERR_CONNECTION_REFUSED" in str(exc) or "ERR_CONNECTION_RESET" in str(exc):
                    rec["retries"] = attempt + 1
                    await asyncio.sleep(4 * (attempt + 1))
                    continue
                raise
        else:
            raise last_exc  # type: ignore[misc]
        rec["status"] = resp.status if resp else None
        rec["finalPath"] = urlparse(page.url).path
        rec["redirected"] = page.url.replace(BASE, "") != path
        try:
            chain = await page.evaluate(
                "() => performance.getEntriesByType('navigation')[0]"
                "? (performance.getEntriesByType('navigation')[0].redirectCount || 0) : 0")
            rec["redirectCount"] = chain
        except Exception:
            pass

        await page.wait_for_timeout(350)

        # record + neutralise the cookie banner so it never covers the viewport
        rec["cookieBanner"] = await page.evaluate(
            "() => { const b = document.getElementById('wa-cookie-banner');"
            " if (b) { const t = (b.textContent||'').replace(/\\s+/g,' ').trim().slice(0,80);"
            " b.remove(); return t; } return null; }")

        probe = await page.evaluate(PAGE_PROBE_JS)
        rec["probe"] = probe

        # language sanity: does the rendered text match the language in the URL?
        exp = LANG_SCRIPT[rec["lang"]]
        dom = probe.get("dominantScript")
        rec["langOK"] = (dom == exp) if exp != "latin" else (probe.get("latinRatio", 0) > 0.5)
        rec["langScriptMismatch"] = None if rec["langOK"] else {
            "expected": exp, "got": dom, "latinRatio": probe.get("latinRatio"),
            "scripts": probe.get("scripts")}

        if shot_mode == "all":
            SHOTS.mkdir(parents=True, exist_ok=True)
            f = SHOTS / f"{vp_name}-{slugify(path)}.png"
            await page.screenshot(path=str(f))
            rec["shot"] = f.name
        else:
            rec["_shot_candidate"] = True
    except Exception as exc:  # noqa: BLE001
        rec["error"] = f"{type(exc).__name__}: {exc}"[:300]
        rec["status"] = rec.get("status")
    finally:
        rec["elapsedMs"] = int((time.time() - t0) * 1000)
        await page.close()
    return rec


async def sweep(urls: list[str], viewports: list[str], concurrency: int,
                shot_mode: str, out_name: str) -> list[dict]:
    results: list[dict] = []
    sem = asyncio.Semaphore(concurrency)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--disable-dev-shm-usage"])
        for vp_name in viewports:
            vp = VIEWPORTS[vp_name]
            ctx = await browser.new_context(
                viewport=vp, user_agent=UA, locale="en-US",
                service_workers="block", ignore_https_errors=True,
                extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
            )
            tasks = []

            async def one(p):
                async with sem:
                    return await check_page(ctx, p, vp_name, shot_mode)

            for p in urls:
                tasks.append(asyncio.create_task(one(p)))
            done = 0
            for fut in asyncio.as_completed(tasks):
                r = await fut
                done += 1
                results.append(r)
                flag = "!" if (r.get("status") != 200 or r.get("pageErrors")
                               or r.get("badResponses") or r.get("error")) else " "
                print(f"[{vp_name}] {done:>4}/{len(urls)} {flag} {r['path']} "
                      f"({r.get('elapsedMs')}ms)", flush=True)
            await ctx.close()
        await browser.close()
    save(out_name, results)
    return results


# --------------------------------------------------------------------------- #
# global internal-link check (no browser)
# --------------------------------------------------------------------------- #

def http_status(url: str, timeout: float = 20.0):
    """Status of a URL.

    HEAD is tried first for speed, but the CF Pages middleware only rewrites GET
    requests, so a HEAD 404 does not mean a dead link - always fall back to a real
    GET before reporting anything as broken.
    """
    import urllib.request
    import urllib.error

    def _get():
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                r.read(2048)
                return r.status, r.geturl()
        except urllib.error.HTTPError as e:
            return e.code, url
        except Exception:
            return 0, url

    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            st = r.status
    except urllib.error.HTTPError as e:
        st = e.code
    except Exception:
        st = 0
    if st in (0, 403, 404, 405, 501):
        return _get()
    return st, url


def link_check(pages: list[dict], concurrency: int = 12) -> dict:
    """Every distinct internal link found during the sweep, checked once."""
    ref: dict[str, set] = {}
    for p in pages:
        probe = p.get("probe") or {}
        for href in probe.get("internalLinks", []) or []:
            if not href:
                continue
            u = urlparse(href)
            path = u.path or "/"
            if not path.endswith("/") and "." not in path.split("/")[-1]:
                path += "/"
            ref.setdefault(path, set()).add(p["path"])

    print(f"link check: {len(ref)} distinct internal targets from {len(pages)} pages", flush=True)
    out: dict = {}
    lock = threading.Lock()
    done = [0]

    def work(item):
        path, sources = item
        st, final = http_status(to_local(path))
        with lock:
            out[path] = {"status": st, "final": final.replace(BASE, ""), "sources": sorted(sources)[:6]}
            done[0] += 1
            if done[0] % 100 == 0:
                print(f"  ... {done[0]}/{len(ref)}", flush=True)

    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        list(ex.map(work, list(ref.items())))
    return out


def redirect_check(paths: list[str]) -> dict:
    """Legacy/alternate URL forms must resolve 30x to a canonical page, not 404."""
    out = {}
    for p in paths:
        st, final = http_status(to_local(p))
        out[p] = {"status": st, "final": final.replace(BASE, "")}
        print(f"  {p:<52} {st} -> {final.replace(BASE, '')}", flush=True)
    return out


# --------------------------------------------------------------------------- #

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="en")
    ap.add_argument("--viewports", default="mobile")
    ap.add_argument("--concurrency", type=int, default=5)
    ap.add_argument("--shots", default="none", choices=["none", "all"])
    ap.add_argument("--out", default=None)
    ap.add_argument("--links", action="store_true", help="run the global link check after the sweep")
    ap.add_argument("--links-only", action="store_true")
    ap.add_argument("--redirects", default=None, help="comma-separated legacy paths to probe")
    a = ap.parse_args()

    if a.redirects:
        res = redirect_check([p for p in a.redirects.split(",") if p.strip()])
        save("redirects.json", res)
        return

    pages: list[dict] = []
    if not a.links_only:
        urls = list(dict.fromkeys(build_set(a.set)))
        vps = [v.strip() for v in a.viewports.split(",") if v.strip()]
        out_name = a.out or f"sweep-{slugify(a.set)}.json"
        print(f"sweep: {len(urls)} urls x {len(vps)} viewport(s) -> {out_name}", flush=True)
        pages = asyncio.run(sweep(urls, vps, a.concurrency, a.shots, out_name))
        # screenshot only the pages that actually failed something
        save(out_name, pages)

    if a.links or a.links_only:
        if not pages:
            prev = sorted(RESULTS.glob("sweep-*.json"))
            for f in prev:
                pages += json.loads(f.read_text(encoding="utf-8"))
        res = link_check(pages)
        save("links.json", res)
        bad = {k: v for k, v in res.items() if v["status"] == 0 or v["status"] >= 400}
        print(f"broken internal targets: {len(bad)}")
        for k, v in sorted(bad.items())[:40]:
            print(f"  {v['status']:>4} {k}   (linked from {v['sources'][:3]})")


if __name__ == "__main__":
    main()
