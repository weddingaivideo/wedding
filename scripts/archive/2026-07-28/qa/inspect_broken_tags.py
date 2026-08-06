import re
from pathlib import Path
from collections import Counter
ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
EXCLUDE_DIRS = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

# Categorize all structural bugs
patterns = Counter()
samples = {}

# 1. <listyle= missing space
listyle = 0
# 2. Cross-tag dup <TAG1<TAG2
cross = 0
# 3. <a dup <a href=><a href=
a_dup = 0

for p in sorted(ROOT.rglob('*.html')):
    if set(p.parts) & {Path(d) for d in EXCLUDE_DIRS}: continue
    if p.name == 'google-site-verification.html': continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    # <listyle=
    for m in re.finditer(r'<listyle=', text):
        listyle += 1
    # Cross-tag <TAG1<TAG2 (real cross-tag)
    for m in re.finditer(r'<([a-zA-Z][a-zA-Z0-9]*)(<[a-zA-Z][a-zA-Z0-9]*)', text):
        cross += 1
        patterns[m.group(0)] += 1
        if m.group(0) not in samples:
            samples[m.group(0)] = (p.relative_to(ROOT), text[max(0,m.start()-30):m.start()+80])

print(f'listyle bugs: {listyle}')
print(f'cross-tag bugs: {cross}')
print()
for k, v in patterns.most_common(15):
    path, snip = samples[k]
    print(f'  {v:4d}  {k!r}')
    print(f'        [{path}] ...{snip}...')
    print()
