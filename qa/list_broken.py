"""List all broken local hrefs across the site."""
import os
import re
from pathlib import Path
ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
broken = {}
for f in ROOT.rglob('*.html'):
    parts = {str(p) for p in f.parts}
    if parts & {'admin','functions','tmp','__pycache__','qa','i18n','js','styles','scripts','docs'}:
        continue
    text = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'href="(/[^"#?]*)"', text):
        href = m.group(1)
        if href.startswith('//') or href.startswith('http'):
            continue
        target = (ROOT / href.lstrip('/')).resolve()
        if not target.exists():
            target_idx = (ROOT / href.lstrip('/') / 'index.html').resolve()
            if not target_idx.exists():
                rel = str(f.relative_to(ROOT))
                broken.setdefault(rel, []).append(href)
total = 0
for rel, hrefs in sorted(broken.items()):
    for h in hrefs:
        print(f'{rel}  {h}')
        total += 1
print()
print(f'Total files with broken: {len(broken)}')
print(f'Total broken links: {total}')
