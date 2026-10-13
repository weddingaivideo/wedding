#!/usr/bin/env python3
"""Quick re-verify de/tools/ alone."""
import urllib.request, re, time, sys

url = 'https://weddingai.video/de/tools/?cb=' + time.strftime('%Y%m%d%H%M%S')
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'de',
    'Cache-Control': 'no-cache',
})

LEAK_PATTERNS = [
    r'\bOpen tool\b',
    r'\bCompress Wedding Photos\b',
    r'\bWedding Photo Collage Maker\b',
    r'\bHEIC to JPG Converter\b',
    r'\bAdd Text to Wedding Photo\b',
]

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode('utf-8', errors='replace')
    # Strip JSON-LD, meta, title/alt
    visible = re.sub(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>[\s\S]*?</script>', '', html)
    visible = re.sub(r'<meta\b[^>]*>', '', visible)
    visible = re.sub(r'\s(?:title|alt|aria-label|content)=(?:"[^"]*"|\'[^\']*\')', '', visible)

    leaked = [p for p in LEAK_PATTERNS if re.search(p, visible, re.IGNORECASE)]
    wer_count = visible.count('Werkzeug öffnen')
    print(f'de: Werkzeug öffnen x{wer_count}, leaks: {leaked}')
    if leaked or wer_count < 1:
        sys.exit(1)
    print('PASS')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
