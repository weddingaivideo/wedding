"""P3-2: Add HTML default text fallback to 360 empty <a> elements with
nav keys (404.a_text.*). All 72 pages share the same 5 nav keys, so
the fix is uniform.

Default text is English. When i18n.js loads the matching lang JSON, the
textContent is replaced with the translation. When JS fails (offline /
CDN hiccup), the user sees the English fallback (already the canonical
SEO text for the English-canonical site).

This is a defense-in-depth fix: 99% of the time the JS runs fine and
the user sees their lang. 1% of the time (JS off, JSON fetch fails),
they at least see the canonical link text instead of an empty <a>.
"""
import re
import json
from pathlib import Path
import shutil

ROOT = Path('.')
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

# Load en.json to get canonical English text for each nav key
en = json.loads((ROOT / 'i18n' / 'en.json').read_text(encoding='utf-8'))

# Backup
backup = ROOT / 'tmp' / 'nav-fallback-backup'
backup.mkdir(parents=True, exist_ok=True)

# Collect all empty <a data-i18n="X"></a> and group by key
files = [p for p in ROOT.rglob('*.html') if not (set(str(x) for x in p.parts) & EXCLUDE)]
# Collect (file, key) pairs
empty_pairs = []
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'<a\s+([^>]*)data-i18n="([^"]+)"([^>]*)>\s*</a>', text):
        before = m.group(1)
        key = m.group(2)
        after = m.group(3)
        empty_pairs.append((f, before, key, after, m.start(), m.end()))

print(f'Empty <a> elements with data-i18n: {len(empty_pairs)}')

# Get unique keys
unique_keys = set(k for _, _, k, _, _, _ in empty_pairs)
print(f'Unique keys: {len(unique_keys)}')

# Get English fallback for each (only if in en.json)
fallback_map = {}
unresolved = []
for k in unique_keys:
    if k in en:
        fallback_map[k] = en[k]
    else:
        unresolved.append(k)

if unresolved:
    print(f'\nUnresolved keys (not in en.json): {len(unresolved)}')
    for k in unresolved[:5]:
        print(f'  {k}')

# Sample fallback map
print(f'\nFallback map sample:')
for k in list(fallback_map.keys())[:10]:
    print(f'  {k} = {fallback_map[k]!r}')

# Apply fix: add text content to <a data-i18n="X"></a>
# Replace pattern: <a ATTRS data-i18n="KEY" ATTRS></a> -> <a ATTRS data-i18n="KEY" ATTRS>FALLBACK</a>
count = 0
files_touched = set()
for f, before, key, after, _, _ in empty_pairs:
    if key not in fallback_map:
        continue
    text = f.read_text(encoding='utf-8', errors='ignore')
    # Pattern: <a <before> data-i18n="<key>" <after>></a>
    # We need to capture and replace specifically this empty <a> with fallback text
    # Use a non-regex approach: find exact match string and replace
    exact = f'<a {before}data-i18n="{key}"{after}></a>'
    if exact not in text:
        # Try without trailing space inside attributes
        exact2 = f'<a {before.strip()} data-i18n="{key}" {after.strip()}></a>'
        exact2 = re.sub(r'\s+', ' ', exact2)
        if exact2 in text:
            exact = exact2
        else:
            continue
    fallback = fallback_map[key]
    new = f'<a {before}data-i18n="{key}"{after}>{fallback}</a>'
    if exact in text:
        # Backup
        bp = backup / f'{f.relative_to(ROOT)}.bak'
        bp.parent.mkdir(parents=True, exist_ok=True)
        if not bp.exists():
            shutil.copy2(f, bp)
        new_text = text.replace(exact, new, 1)
        f.write_text(new_text, encoding='utf-8')
        count += 1
        files_touched.add(f.relative_to(ROOT))

print(f'\nFixed {count} elements in {len(files_touched)} files')
print(f'Backup: {backup}')
