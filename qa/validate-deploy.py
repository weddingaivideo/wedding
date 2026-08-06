#!/usr/bin/env python3
"""Validate the deployed SEO fixes against the live preview URL."""
import re
import sys
import urllib.request

URL = "https://ff111fb5.weddingai-video.pages.dev"


def fetch(path: str) -> str:
    req = urllib.request.Request(URL + path, headers={"User-Agent": "Mavis-Audit/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def main() -> int:
    print("===== Deploy 验证 =====")
    print(f"  Target: {URL}")
    print()

    # 1. index.html og:image / twitter:image
    print("--- 1. index.html og/twitter image ---")
    idx = fetch("/")
    og = re.search(r'<meta property="og:image" content="([^"]+)"', idx)
    tw = re.search(r'<meta name="twitter:image" content="([^"]+)"', idx)
    og_w = re.search(r'<meta property="og:image:width" content="([^"]+)"', idx)
    og_h = re.search(r'<meta property="og:image:height" content="([^"]+)"', idx)
    print(f"  og:image = {og.group(1) if og else 'NOT FOUND'}")
    print(f"  og:image:width = {og_w.group(1) if og_w else 'NOT FOUND'}")
    print(f"  og:image:height = {og_h.group(1) if og_h else 'NOT FOUND'}")
    print(f"  twitter:image = {tw.group(1) if tw else 'NOT FOUND'}")
    is_webp = og and og.group(1).endswith(".webp")
    print(f"  → og is webp: {is_webp}")
    print()

    # 2. Service JSON-LD
    print("--- 2. Service JSON-LD (P1-1) ---")
    blocks = re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>', idx, re.DOTALL
    )
    found_service = False
    review_marker = '"@type": "Review"'
    for b in blocks:
        if '"@type": "Service"' in b or '"@type":"Service"' in b:
            found_service = True
            has_agg = "aggregateRating" in b
            has_review = review_marker in b
            has_provider = '"provider"' in b
            has_service_type = '"serviceType"' in b
            has_area = '"areaServed"' in b
            has_catalog = '"hasOfferCatalog"' in b
            print(f"  aggregateRating removed: {not has_agg}")
            print(f"  Review removed: {not has_review}")
            print(f"  provider added: {has_provider}")
            print(f"  serviceType added: {has_service_type}")
            print(f"  areaServed added: {has_area}")
            print(f"  hasOfferCatalog added: {has_catalog}")
    if not found_service:
        print("  [WARN] Service JSON-LD block not found")
    print()

    # 3. robots.txt
    print("--- 3. robots.txt (P0-1) ---")
    rt = fetch("/robots.txt")
    print(f"  size: {len(rt)} bytes")
    print(f"  User-agent rules: {len(re.findall(r'^User-agent:', rt, re.M))}")
    print(f"  Sitemap declarations: {len(re.findall(r'^Sitemap:', rt, re.M))}")
    print(f"  Disallow rules: {len(re.findall(r'^Disallow:', rt, re.M))}")
    print(f"  AI bots allowed (GPTBot/Claude): {('GPTBot' in rt and 'ClaudeBot' in rt)}")
    print()

    # 4. sitemap-en.xml
    print("--- 4. sitemap-en.xml (P0-2, P1-2) ---")
    sm = fetch("/sitemap-en.xml")
    n_urls = len(re.findall(r"<url>", sm))
    n_hreflang = len(re.findall(r'hreflang=', sm))
    n_image = len(re.findall(r"<image:image>", sm))
    print(f"  URLs: {n_urls} (expected 71)")
    print(f"  hreflang links: {n_hreflang} (expected 781 = 71×11)")
    print(f"  image:image: {n_image} (expected 71)")
    print()

    # 5. i18n.js EN skip + idle load
    print("--- 5. i18n.js (P1-3) ---")
    i18n = fetch("/js/i18n.js")
    print(f"  EN skip fetch comment present: {'English is the source language' in i18n}")
    print(f"  requestIdleCallback for non-EN: {'requestIdleCallback(startLoad' in i18n}")
    print()

    # 6. llms.txt
    print("--- 6. llms.txt (P2-1) ---")
    llms = fetch("/llms.txt")
    n_links = len(re.findall(r"^- \[", llms, re.M))
    n_index = len(re.findall(r"^- \[index\]\(", llms, re.M))
    print(f"  total links: {n_links}")
    print(f"  broken [index] entries: {n_index}")
    print()

    # 7. 404 fallback
    print("--- 7. 404.html fallback (P2-2) ---")
    try:
        r = urllib.request.Request(URL + "/non-existent-url-12345")
        with urllib.request.urlopen(r, timeout=20) as resp:
            print(f"  /non-existent-url status: {resp.status}")
            body = resp.read().decode("utf-8", errors="replace")
            has_404 = "Page Not Found" in body
            print(f"  has 404 page content: {has_404}")
    except urllib.error.HTTPError as e:
        print(f"  /non-existent-url status: {e.code}")
    print()

    # 8. IndexNow key
    print("--- 8. IndexNow key file ---")
    import re as _re
    key_match = _re.search(r"https://weddingai\.video/([a-f0-9]+\.txt)", rt)
    if not key_match:
        # Try to find in submit-indexnow output via local file
        pass
    # 直接试访问 root
    try:
        with urllib.request.urlopen(URL + "/", timeout=20) as r:
            pass
    except Exception:
        pass
    # 看 indexnow-key.txt 是否还存在
    try:
        with urllib.request.urlopen(URL + "/indexnow-key.txt", timeout=20) as r:
            print(f"  /indexnow-key.txt: {r.status} (should be 404)")
    except urllib.error.HTTPError as e:
        print(f"  /indexnow-key.txt: {e.code} (private key, should be 404)")

    print()
    print("===== Deploy 验证完成 =====")
    return 0


if __name__ == "__main__":
    sys.exit(main())
