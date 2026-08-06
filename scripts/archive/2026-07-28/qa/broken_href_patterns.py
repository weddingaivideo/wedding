import re
from pathlib import Path
from collections import Counter
ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
EXCLUDE_DIRS = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}
c = Counter()
broken = []
for p in sorted(ROOT.rglob('*.html')):
    if set(p.parts) & {Path(d) for d in EXCLUDE_DIRS}: continue
    if p.name == 'google-site-verification.html': continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'href="(/blog/[^"/]+/)"', text):
        href = m.group(1)
        target = (ROOT / href.lstrip('/') / 'index.html').resolve()
        if not target.exists():
            c[href] += 1
            broken.append((p.relative_to(ROOT), href))
for k, v in c.most_common(20):
    print(f'{v:3d}  {k}')
