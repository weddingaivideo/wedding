"""Verify /hi/blog/<tier-2-slug>/ (no physical file) returns translated content via middleware."""
import re
import urllib.request

tier2_slugs = [
    'ai-vs-human-wedding-editing',  # EN-only
    'ai-wedding-video-generator-guide',  # EN-only
    'budget-wedding-video',  # EN-only
    'cartoon-wedding-video',  # EN-only
    'wedding-video-cost-2026',  # EN-only
]
for slug in tier2_slugs:
    url = f'https://weddingai.video/hi/blog/{slug}/'
    print(f'\n=== {url} ===')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        body = resp.read().decode('utf-8', errors='replace')
        status = resp.status
    except urllib.error.HTTPError as e:
        body = ''
        status = e.code
        print(f'  HTTP {status}')
        if e.headers.get('Location'):
            print(f'  Location: {e.headers.get("Location")}')
        continue
    except Exception as e:
        print(f'  ERR: {e}')
        continue
    print(f'  status: {status}')
    # Check
    m = re.search(r'<html[^>]*lang="([^"]+)"', body)
    print(f'  html lang: {m.group(1) if m else "MISSING"}')
    h1 = re.search(r'<h1[^>]*>([^<]+)</h1>', body)
    print(f'  H1: {h1.group(1)[:80] if h1 else "MISSING"}')
    devanagari = len(re.findall(r'[\u0900-\u097F]', body))
    print(f'  Devanagari: {devanagari}')
    # Check if data-i18n still in HTML (means middleware didn't fully replace)
    di = len(re.findall(r'data-i18n', body))
    print(f'  data-i18n attrs remaining: {di} (should be 0 if middleware applied)')
