import re
from pathlib import Path
ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
EXCLUDE_DIRS = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}
seen = set()
samples = {}
for p in sorted(ROOT.rglob('*.html')):
    if set(p.parts) & {Path(d) for d in EXCLUDE_DIRS}: continue
    if p.name == 'google-site-verification.html': continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'href="(/[^"#?]+)"', text):
        href = m.group(1)
        if href.startswith('//') or href.startswith('http'): continue
        if '${' in href: continue  # JS template
        target = (ROOT / href.lstrip('/')).resolve()
        target_idx = (ROOT / href.lstrip('/') / 'index.html').resolve()
        if not target.exists() and not target_idx.exists():
            if href not in seen:
                seen.add(href)
                samples[href] = p.relative_to(ROOT)
for href in sorted(seen):
    print(f'  [{samples[href]}]  {href}')
