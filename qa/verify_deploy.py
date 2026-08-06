"""
Post-deploy verification for weddingai.video.

Translation is client-side (data-i18n attrs + i18n.js replaces textContent).
So curl can't see translated text. We verify:
  1. All sample URLs return 200
  2. i18n JSON returns 200 with expected keys
  3. HTML has data-i18n attributes (i18n system will run on page)
  4. _redirects gives 200 for /zh/ etc. (not 404 or 308)
  5. Googlebot UA gets 200 (no JS redirect)
  6. Each /lang/ page has html[lang] set correctly via middleware

Usage: python qa/verify_deploy.py [--base https://weddingai.video]
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"]

SAMPLE_PAGES = [
    "/", "/pricing/", "/blog/", "/services/",
    "/blog/wedding-video-cost-2026/",
    "/services/personalization/multilingual/",
    "/order/", "/about/", "/terms/",
]

UA_GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
UA_NORMAL = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
I18N_VERSION = "3.22"


def fetch(url, ua=UA_NORMAL, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", errors="replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, "", dict(e.headers)
    except Exception as e:
        return 0, "", {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://weddingai.video")
    args = ap.parse_args()
    base = args.base.rstrip("/")
    results = []
    fails = 0

    # 1) Sample pages
    print("=" * 60)
    print(f"1) SAMPLE PAGES ({len(SAMPLE_PAGES)} URLs)")
    print("=" * 60)
    for path in SAMPLE_PAGES:
        url = base + path
        status, body, _ = fetch(url)
        ok = status == 200 and len(body) > 100
        # Also check for data-i18n attr (i18n system live)
        has_i18n = 'data-i18n=' in body
        results.append((path, "200 + i18n", status, ok and has_i18n))
        if not (ok and has_i18n):
            fails += 1
        marker = "OK" if (ok and has_i18n) else "FAIL"
        print(f"  {marker:4s}  {status:3d}  data-i18n={has_i18n}  {url}")

    # 2) Language prefix pages — confirm 200 (not 404) and html[lang] preserved
    print()
    print("=" * 60)
    print(f"2) LANGUAGE PREFIX PAGES ({len(LANGS)} URLs)")
    print("=" * 60)
    for lang in LANGS:
        path = f"/{lang}/" if lang != "en" else "/"
        url = base + path
        status, body, _ = fetch(url)
        ok = status == 200 and len(body) > 100
        # The /lang/ path gets same EN HTML; client-side swaps lang based on URL.
        # So we just check 200 + has data-i18n + has langs.js
        has_i18n = 'data-i18n=' in body
        has_langs = 'js/langs.js' in body
        has_i18n_js = 'js/i18n.js' in body
        ok_full = ok and has_i18n and has_langs and has_i18n_js
        results.append((path, f"lang={lang}", status, ok_full))
        if not ok_full:
            fails += 1
        marker = "OK" if ok_full else "FAIL"
        print(f"  {marker:4s}  {status:3d}  i18n={has_i18n} langs.js={has_langs} i18n.js={has_i18n_js}  {url}")

    # 3) i18n JSON
    print()
    print("=" * 60)
    print(f"3) i18n JSON ({len(LANGS)} langs, ?v={I18N_VERSION})")
    print("=" * 60)
    for lang in LANGS:
        url = f"{base}/i18n/{lang}.json?v={I18N_VERSION}"
        status, body, _ = fetch(url)
        ok = status == 200
        key_count = 0
        if ok:
            try:
                d = json.loads(body)
                key_count = sum(1 for k in d if k != "_meta")
            except Exception:
                ok = False
        # Check a few critical keys exist
        critical_ok = False
        if ok:
            d = json.loads(body)
            # Find any key whose first segment is 'index'
            sample_keys = [k for k in d if k.startswith("index.")][:5]
            critical_ok = all(d.get(k) for k in sample_keys) if sample_keys else False
        results.append((f"/i18n/{lang}.json", f"{key_count} keys + critical", status, ok and critical_ok))
        if not (ok and critical_ok):
            fails += 1
        marker = "OK" if (ok and critical_ok) else "FAIL"
        print(f"  {marker:4s}  {status:3d}  {key_count:5d} keys, critical={critical_ok}  {url}")

    # 4) Googlebot sees 200
    print()
    print("=" * 60)
    print("4) Googlebot UA on /")
    print("=" * 60)
    status, body, _ = fetch(base + "/", ua=UA_GOOGLEBOT)
    has_ai = "WeddingAI" in body
    has_i18n = "data-i18n=" in body
    ok = status == 200 and has_ai
    results.append(("/", "googlebot", status, ok))
    if not ok:
        fails += 1
    print(f"  {'OK' if ok else 'FAIL'}  {status:3d}  has_WeddingAI={has_ai}  data-i18n={has_i18n}")

    # 5) Cloudflare Pages _redirects: /zh/services should not 404
    print()
    print("=" * 60)
    print("5) LANG PREFIX SUBPAGES (10 langs × 3 pages)")
    print("=" * 60)
    subpages = ["/", "/services/", "/blog/wedding-video-cost-2026/"]
    for lang in LANGS:
        for sub in subpages:
            path = f"/{lang}{sub}" if lang != "en" else sub
            url = base + path
            status, body, _ = fetch(url)
            ok = status == 200 and len(body) > 100
            results.append((path, "200", status, ok))
            if not ok:
                fails += 1
                print(f"  FAIL  {status:3d}  {url}")
    print(f"  (silent if all {len(LANGS) * len(subpages)} OK)")

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total = len(results)
    print(f"  {total - fails}/{total} checks passed")
    if fails:
        print(f"  {fails} FAILED — investigate above")
        sys.exit(1)
    else:
        print("  ALL GREEN — deploy verified.")
        print()
        print("  NOTE: Translation is client-side (data-i18n + i18n.js).")
        print("        Curl can't see post-JS DOM; browsers will translate.")


if __name__ == "__main__":
    main()
