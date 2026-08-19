"""Inspect /hi/ response — see what the middleware is actually doing."""
import re
import urllib.request

urls = [
    'https://weddingai.video/hi/',
    'https://weddingai.video/hi/blog/',
    'https://weddingai.video/hi/blog/affordable-wedding-video-ai/',
]
for url in urls:
    print(f'\n=== {url} ===')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'hi'})
    try:
        body = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='replace')
    except Exception as e:
        body = ''
        print(f'  ERR: {e}')
    if not body:
        continue
    # Check html lang
    m = re.search(r'<html[^>]*lang="([^"]+)"', body)
    print(f'  html lang: {m.group(1) if m else "MISSING"}')
    # Check canonical
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*>', body)
    print(f'  canonical: {m.group(0) if m else "MISSING"}')
    # Check hreflangs
    hl = re.findall(r'hreflang="([^"]+)"', body)
    print(f'  hreflangs: {hl[:5]}{"..." if len(hl)>5 else ""} (total {len(hl)})')
    # Check first H1
    h1 = re.search(r'<h1[^>]*>([^<]+)</h1>', body)
    print(f'  H1: {h1.group(1)[:80] if h1 else "MISSING"}')
    # Devanagari
    dev = len(re.findall(r'[\u0900-\u097F]', body))
    print(f'  Devanagari: {dev}')
    # Title
    t = re.search(r'<title[^>]*>([^<]+)</title>', body)
    print(f'  title: {t.group(1)[:100] if t else "MISSING"}')
