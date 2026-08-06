import re
from pathlib import Path
from collections import Counter
ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
EXCLUDE_DIRS = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

# Look for <a href="X"...><a href="X"...> pattern (dup anchor)
dup_anchor = []
for p in sorted(ROOT.rglob('*.html')):
    if set(p.parts) & {Path(d) for d in EXCLUDE_DIRS}: continue
    if p.name == 'google-site-verification.html': continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'<a\s+href="([^"]+)"[^>]*>\s*<a\s+href="\1"', text):
        dup_anchor.append((p.relative_to(ROOT), m.group(0)[:100], text[max(0,m.start()-30):m.start()+120]))

print(f'Dup anchor <a href="X"><a href="X">: {len(dup_anchor)}')
# Categorize
c = Counter()
samples = {}
for path, m, snip in dup_anchor:
    # Type 1: empty outer, inner has data-i18n
    # Type 2: outer has data-i18n, inner has data-i18n (different content?)
    # Get inner part
    inner_m = re.search(r'<a\s+href="[^"]+"[^>]*data-i18n="([^"]+)"', m)
    if inner_m:
        c['both_have_i18n'] += 1
    else:
        c['other'] += 1
print(c)
# Sample
for path, m, snip in dup_anchor[:5]:
    print(f'\n[{path}]')
    print(f'  ...{snip}...')
