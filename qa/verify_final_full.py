#!/usr/bin/env python3
"""Final 11-lang production verification for /tools/."""
import json
import urllib.request
import re
import sys

LANGS = ['en', 'zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th', 'hi']
DOMAIN = 'https://weddingai.video'

# 1. Load English source strings from /tools/index.html
with open('tools/index.html', 'r', encoding='utf-8') as f:
    en_html = f.read()

# Extract data-i18n content (the source-of-truth English text)
pattern = re.compile(r'data-i18n="([^"]+)"[^>]*>([^<]+)<', re.DOTALL)
en_strings = {}
for m in pattern.finditer(en_html):
    key = m.group(1)
    val = m.group(2).strip()
    if val and len(val) > 3:
        en_strings[key] = val

print(f'[i] English source: {len(en_strings)} data-i18n keys with non-empty text')

# Also extract raw visible strings (non-data-i18n text that should NOT need translation)
raw_re = re.compile(r'<p[^>]*>([^<]{15,200})</p>|<h[12345][^>]*>([^<]{3,200})</h[12345]>|<span[^>]*>([^<]{5,200})</span>|<a[^>]*>([^<]{3,200})</a>', re.DOTALL)
visible = set()
for m in raw_re.finditer(en_html):
    for g in m.groups():
        if g:
            t = g.strip()
            if 3 < len(t) < 200:
                visible.add(t)
print(f'[i] Visible English strings (heuristic): {len(visible)}')

# 2. Fetch each /<lang>/tools/ page and look for English leaks
errors = []
checked = 0

for lang in LANGS:
    if lang == 'en':
        url = f'{DOMAIN}/tools/'
    else:
        url = f'{DOMAIN}/{lang}/tools/'

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Accept-Language': lang,
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode('utf-8', errors='replace')

        checked += 1
        # Strip data-i18n attrs (middleware does that on render — but we already received the rendered page)
        # Actually we received the post-middleware page, so data-i18n is already stripped
        # We just need to verify no English content remains visible

        # Heuristic: look for common English-only words that would only appear if translation failed
        en_only = [
            'Compress Wedding Photos', 'HEIC to JPG', 'Wedding Photo Collage',
            'Pick the Wedding Photo Tool', 'shrink huge JPGs', 'iPhone photos in HEIC',
            'six pure frontend utilities', '100% in your browser', 'no upload, no signup',
            'Files are processed locally', 'Drag 2-12 photos', 'Crop wedding photos',
            'removes backgrounds', 'Add text overlay', 'open the tool',
            '100% in your browser', 'all your bytes stay on your device',
        ]
        leaks = []
        html_lower = html.lower()
        for w in en_only:
            if w.lower() in html_lower:
                leaks.append(w)

        # also check stale-tell phrases like 'Open tool →' instead of localized '打开工具'
        if 'Open tool →' in html or 'open the tool' in html_lower:
            leaks.append('Open tool →')

        if leaks:
            errors.append((lang, leaks))
            print(f'  [{lang}] ✗ leaks: {leaks}')
        else:
            print(f'  [{lang}] ✓ clean')

    except Exception as e:
        print(f'  [{lang}] !! network error: {e}')
        errors.append((lang, [f'NETWORK: {e}']))

print()
print(f'Checked {checked}/11 languages')
if errors:
    print(f'!!! {len(errors)} locale(s) have leaks:')
    for lang, l in errors:
        print(f'    {lang}: {l}')
    sys.exit(1)
else:
    print('PASS: all 11 languages clean')
    sys.exit(0)
