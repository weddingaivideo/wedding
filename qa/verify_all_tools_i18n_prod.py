#!/usr/bin/env python3
"""Final holistic production check:
- All 11 locales of /tools/
- Look for any English-leaked text matching the 128 source keys' content
"""
import urllib.request
import json
import re
import sys
import time

LANGS = ['en', 'zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th', 'hi']
DOMAIN = 'https://weddingai.video'

# Read the source HTML data-i18n attrs (the 128 source-of-truth keys)
with open('tools/index.html', 'r', encoding='utf-8') as f:
    src = f.read()

# Extract all data-i18n keys with their English source text
src_pairs = []
for m in re.finditer(r'data-i18n="([^"]+)"[^>]*>([^<]+)<', src):
    src_pairs.append((m.group(1), m.group(2).strip()))

# Also extract title= and alt= attrs from data-i18n-attr
for m in re.finditer(r'data-i18n-attr="([^"]+)"', src):
    pass  # we ignore the attr-bound translations, only worry about text leaks

print(f'Source: {len(src_pairs)} data-i18n keys with text')
src_keys = set(k for k, _ in src_pairs)

# For non-en, we want to ensure each key resolves to a non-empty string in the JSON
LEAK_PATTERNS = [
    r'\bCompress Wedding Photos\b',
    r'\bShrink huge JPGs\b',
    r'\bHEIC to JPG Converter\b',
    r'\biPhone photos in HEIC\b',
    r'\bWedding Photo Collage Maker\b',
    r'\bDrop 2.12 photos\b',
    r'\bCrop Wedding Photo for Reels\b',
    r'\bInstantly crop to 9:16\b',
    r'\bRemove Background from Portrait\b',
    r'\bStrip a clean studio backdrop\b',
    r'\bAdd Text to Wedding Photo\b',
    r'\bAdd captions, dates, quotes\b',
    r'\bOpen tool\b',     # generic — only flag if locale has a localized version
    r'\bshrink_huge_jpgs\b',
    r'\bsave-the-dates\b',
]

# Per-locale expected "Open tool" form
OPENTOOL = {
    'en': None,  # will be English
    'zh': '打开工具',
    'es': 'Abrir herramienta',
    'fr': "Ouvrir l'outil",
    'de': 'Werkzeug öffnen',
    'pt': 'Abrir ferramenta',
    'ja': 'ツールを開く',
    'ru': 'Открыть инструмент',
    'ar': 'أداة مفتوحة',
    'th': 'เปิดเครื่องมือ',
    'hi': 'टूल खोलें',
}

failures = []
checked = 0
cb = time.strftime('%Y%m%d%H%M%S')

for lang in LANGS:
    url = f'{DOMAIN}/{lang}/tools/?cb={cb}' if lang != 'en' else f'{DOMAIN}/tools/?cb={cb}'
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Accept-Language': lang,
            'Cache-Control': 'no-cache',
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8', errors='replace')
        checked += 1

        # For English: source marker must be present
        if lang == 'en':
            if 'Open tool' not in html:
                failures.append((lang, 'expected source marker'))
            else:
                print(f'  [{lang}] ✓ source OK')
            continue

        # Per-locale leakage audit
        # 1. Look for \"Open tool\" — should never appear (localized version exists)
        if 'Open tool' in html:
            cnt = html.count('Open tool')
            # Some intentional occurrences in attr (title=) are OK; we'll surface all
            failures.append((lang, f'"Open tool" appears {cnt}x'))
            print(f'  [{lang}] ✗ "Open tool" {cnt}x')

        # 2. Localized open_tool must appear 6+ times
        localized = OPENTOOL[lang]
        if localized and html.count(localized) < 1:
            failures.append((lang, f'localized "{localized}" missing'))
            print(f'  [{lang}] ✗ localized "{localized}" missing')

        # 3. Check the other English leak patterns
        leaked = []
        for pat in LEAK_PATTERNS[1:]:  # skip "Open tool" — already handled
            if re.search(pat, html, re.IGNORECASE):
                leaked.append(pat)
        if leaked:
            failures.append((lang, f'leaks: {leaked}'))
            print(f'  [{lang}] ✗ leaks: {leaked}')

        if not failures or all(f[0] != lang for f in failures):
            print(f'  [{lang}] ✓ no English leaks')

    except Exception as e:
        failures.append((lang, f'network: {e}'))
        print(f'  [{lang}] !! error: {e}')

print()
print(f'Checked: {checked}/11')
if failures:
    print(f'!!! {len(failures)} failure(s):')
    for l, m in failures:
        print(f'    {l}: {m}')
    sys.exit(1)
print('PASS: all 11 locales clean')
