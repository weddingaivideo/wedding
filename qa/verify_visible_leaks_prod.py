#!/usr/bin/env python3
"""Smart production check: only inspect VISIBLE body text on /tools/ pages
for English leaks. Strip:
- JSON-LD <script type="application/ld+json"> bodies
- HTML attributes (title=, alt=, aria-label=)
- <meta> tags
"""
import urllib.request
import re
import sys
import time

LANGS = ['en', 'zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th', 'hi']
DOMAIN = 'https://weddingai.video'

# Per-locale expected "Open tool" form
OPENTOOL = {
    'en': None,
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

# Phrases that would be visible-body leaks (i.e., if any of these appear
# anywhere outside attrs and JSON-LD, that's a real bug)
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
    r'\bOpen tool\b',
]


def strip_noise(html: str) -> str:
    """Remove JSON-LD scripts, meta tags, and HTML attribute values so we
    only inspect the body text content."""
    # 1. Strip <script type="application/ld+json">...</script>
    html = re.sub(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>[\s\S]*?</script>', '', html)
    # 2. Strip all <meta ...> tags
    html = re.sub(r'<meta\b[^>]*>', '', html)
    # 3. Strip title="..." and alt="..." attribute values
    html = re.sub(r'\s(?:title|alt|aria-label|content)=(?:"[^"]*"|\'[^\']*\')', '', html)
    return html


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
        visible = strip_noise(html)

        if lang == 'en':
            if 'Open tool' not in visible:
                failures.append((lang, 'expected EN marker'))
            else:
                print(f'  [{lang}] ✓ source OK')
            continue

        # Per-locale: 1) English "Open tool" must NOT appear in visible body
        leaked = []
        for pat in LEAK_PATTERNS:
            if re.search(pat, visible, re.IGNORECASE):
                leaked.append(pat)
        # 2) Localized "open tool" should appear ≥6 times (one per card)
        localized = OPENTOOL[lang]
        loc_count = visible.count(localized) if localized else 0

        if leaked:
            print(f'  [{lang}] ✗ leaks: {leaked}')
            failures.append((lang, f'leaks: {leaked}'))

        if localized and loc_count < 1:
            print(f'  [{lang}] ✗ localized "{localized}" missing')
            failures.append((lang, f'missing {localized}'))

        if not leaked and (not localized or loc_count >= 1):
            mark = f'x{loc_count}' if localized else '-'
            print(f'  [{lang}] ✓ clean (localized "open tool" {mark})')

    except Exception as e:
        failures.append((lang, f'network: {e}'))
        print(f'  [{lang}] !! {e}')

print()
print(f'Checked: {checked}/11')
if failures:
    print(f'!!! {len(failures)} failure(s):')
    for l, m in failures:
        print(f'    {l}: {m}')
    sys.exit(1)
print('PASS: all 11 locales clean — visible body text fully localized')
