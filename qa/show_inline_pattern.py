"""Show 1 example of each inline-script type to plan nonce injection."""
import re
from pathlib import Path

ROOT = Path('.')
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}
files = [p for p in ROOT.rglob('*.html') if not (set(str(x) for x in p.parts) & EXCLUDE)]

# Find one example of each kind
seen = {}
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'(<script(?![^>]*\bsrc=)[^>]*>[\s\S]*?</script>)', text):
        script = m.group(0)
        # Categorize
        if 'application/ld+json' in script:
            cat = 'JSON-LD'
        elif 'dataLayer' in script:
            cat = 'gtag-dataLayer'
        elif 'serviceWorker' in script.replace(' ', ''):
            cat = 'service-worker'
        elif 'loadAds' in script or 'loadGtag' in script or 'adsbygoogle' in script:
            cat = 'AdSense-loader'
        else:
            cat = 'other'
        if cat not in seen:
            seen[cat] = (f.relative_to(ROOT), script[:300])

for cat, (path, script) in seen.items():
    print(f'\n=== {cat} (from {path}) ===')
    print(repr(script))
