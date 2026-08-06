"""P1-4: Synchronize all HTML files to use styles.min.css?v=3.21 in <head>.
Currently: 3.21:3 / 3.18:19 / none:51. We want all 73 to be 3.21.
This is a 'styles.min.css' change WITHOUT actually changing the CSS - just
making the version consistent so future CSS changes can bump to 3.22 and
have a clean baseline.

Note: This script also handles the same in <noscript> blocks (already done
in dedup_noscript) and the <link rel="preload"> tag.
"""
import re
from pathlib import Path
import shutil

ROOT = Path('.')
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

backup = ROOT / 'tmp' / 'css-version-sync-backup'
backup.mkdir(parents=True, exist_ok=True)

files = [p for p in ROOT.rglob('*.html') if not (set(str(x) for x in p.parts) & EXCLUDE)]

count = 0
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    orig = text

    # Replace any styles.min.css?v=<any> with styles.min.css?v=3.21
    new = re.sub(
        r'(href="/styles\.min\.css)(?:\?v=[\d.]+)?',
        r'\1?v=3.21',
        text
    )

    if new != orig:
        bp = backup / f'{f.relative_to(ROOT)}.bak'
        bp.parent.mkdir(parents=True, exist_ok=True)
        if not bp.exists():
            shutil.copy2(f, bp)
        f.write_text(new, encoding='utf-8')
        count += 1

print(f'Synchronized {count} files to use styles.min.css?v=3.21')
print(f'Backup: {backup}')

# Verify
from collections import defaultdict
versions = defaultdict(int)
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'styles\.min\.css(?:\?v=([\d.]+))?', text):
        versions[m.group(1) or '(none)'] += 1
print(f'\nPost-sync version distribution: {dict(versions)}')
