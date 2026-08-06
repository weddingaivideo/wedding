"""Re-inspect with proper categorization (filter out scripts that have src=)."""
import re
from pathlib import Path
from collections import Counter

ROOT = Path('.')
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}
files = [p for p in ROOT.rglob('*.html') if not (set(str(x) for x in p.parts) & EXCLUDE)]

real_inline = []
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)</script>', text):
        # Inline only (no src attribute)
        script_tag = m.group(0)
        body = m.group(1).strip()
        if not body:
            continue  # empty <script></script> (rare)
        real_inline.append((f.relative_to(ROOT), body[:300]))

print(f'Real inline <script> blocks (no src=): {len(real_inline)}')

categories = Counter()
samples = {}
for path, body in real_inline:
    b = body.lower()
    if 'application/ld+json' in b or '"@context"' in body:
        cat = 'JSON-LD'
    elif 'datalayer' in b or 'gtag(' in b:
        cat = 'gtag-dataLayer'
    elif 'serviceworker' in b.replace(' ', ''):
        cat = 'service-worker-registration'
    elif 'adsbygoogle' in b or 'ad-lazy' in b:
        cat = 'AdSense-loader'
    elif 'loadads' in b or 'loadgtag' in b:
        cat = 'lazy-third-party-loader'
    else:
        cat = 'other'
    categories[cat] += 1
    if cat not in samples:
        samples[cat] = (path, body[:200])

print(f'\nCategories:')
for cat, n in categories.most_common():
    print(f'  {cat}: {n}')

# JSON-LD doesn't actually need to be in script-src; it's data, not code.
# But CSP spec says JSON-LD <script type="application/ld+json"> is checked
# against script-src unless 'strict-dynamic' or nonce/hash is set.
# In practice JSON-LD is considered data and many CSPs allow it.
# However, in our strict setup we'd need nonce OR allow 'unsafe-inline'
# JUST for JSON-LD. Use a hash-based approach.
print('\nJSON-LD needs nonce OR hash. Hash is more performant (no server round-trip).')
print('Non-JSON-LD needs nonce.')
