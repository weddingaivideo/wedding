"""Inspect what inline scripts exist across the site.
Categorize them by purpose: critical (gtag dataLayer, JSON-LD, etc.) vs
non-critical (could be externalized)."""
import re
from pathlib import Path
from collections import Counter

ROOT = Path('.')
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

files = [p for p in ROOT.rglob('*.html') if not (set(str(x) for x in p.parts) & EXCLUDE)]

inline_scripts = []
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'(?s)<script(?!\s+src=)[^>]*>(.*?)</script>', text):
        inline_scripts.append((f.relative_to(ROOT), m.group(0)[:200]))

print(f'Total inline <script> blocks: {len(inline_scripts)}')

# Categorize
categories = Counter()
samples = {}
for path, script in inline_scripts:
    s = script.lower()
    if 'application/ld+json' in s:
        cat = 'JSON-LD'
    elif 'dataLayer' in s or 'gtag' in s:
        cat = 'gtag/dataLayer'
    elif 'adsbygoogle' in s or 'ad-lazy' in s:
        cat = 'adsense'
    elif 'serviceworker' in s.replace(' ', ''):
        cat = 'service-worker'
    elif 'critical-css' in s or 'onload' in s:
        cat = 'lazy-CSS-load'
    elif len(script) < 200:
        cat = 'short-snippet'
    else:
        cat = 'other'
    categories[cat] += 1
    if cat not in samples:
        samples[cat] = (path, script[:120])

print(f'\nCategories:')
for cat, n in categories.most_common():
    print(f'  {cat}: {n}')
    if cat in samples:
        print(f'    sample: {samples[cat][0]}: {samples[cat][1]!r}')
