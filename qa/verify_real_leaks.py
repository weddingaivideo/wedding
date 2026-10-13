#!/usr/bin/env python3
"""Distinguish real English leaks from tool-name false positives by context."""
import urllib.request
import re

def fetch(url, lang):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept-Language': lang,
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode('utf-8', errors='replace')

# Real leaks: phrases that are clearly NOT tool names / format names
SUSPECT = [
    ('Open tool →', 'phrase used in tool card CTA — should be translated'),
    ('no upload, no signup', 'phrase in body — should be translated'),
    ('Wedding Photo Collage', 'tool name (likely OK as slug)'),
    ('Compress Wedding Photos', 'tool name (likely OK as slug)'),
    ('HEIC to JPG', 'format name + tool (likely OK)'),
]

for lang in ['en', 'zh', 'es', 'fr', 'de']:
    url = f'https://weddingai.video/{lang}/tools/' if lang != 'en' else 'https://weddingai.video/tools/'
    html = fetch(url, lang)
    print(f'\n=== {lang} ===')
    for s, desc in SUSPECT:
        cnt = html.count(s)
        if cnt:
            # Show contexts (find occurrences in surrounding 80 chars)
            print(f'  [{cnt}x] "{s}" — {desc}')
            for m in re.finditer(re.escape(s), html):
                start = max(0, m.start() - 60)
                end = min(len(html), m.end() + 60)
                ctx = html[start:end].replace('\n', ' ').strip()
                print(f'         context: ...{ctx}...')
