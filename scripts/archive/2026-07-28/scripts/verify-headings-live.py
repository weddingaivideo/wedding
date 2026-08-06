"""Verify live pages have no heading skips."""
import re
import urllib.request

URLS = [
    'https://weddingai.video/blog/',
    'https://weddingai.video/order/',
    'https://weddingai.video/services/absence-compensation/family-tribute/',
    'https://weddingai.video/',
]

for url in URLS:
    print(f"==== {url} ====")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; WeddingAI-Audit/1.0)'})
        opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
        with opener.open(req, timeout=15) as r:
            html = r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  ERR: {e}")
        continue
    pat = re.compile(r'<h([1-6])[^>]*>(.*?)</h\1>', re.DOTALL)
    headings = pat.findall(html)
    prev = 0
    skips = 0
    for lvl, txt in headings:
        clean = re.sub(r'<[^>]+>', '', txt).strip()
        lvl_i = int(lvl)
        if prev > 0 and lvl_i > prev + 1:
            print(f"  SKIP h{prev}->h{lvl_i}: {clean[:60]!r}")
            skips += 1
        prev = lvl_i
    status = "OK" if skips == 0 else f"{skips} SKIPS"
    print(f"  {len(headings)} headings, ends at h{prev} — {status}")
