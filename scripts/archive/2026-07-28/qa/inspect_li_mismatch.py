import re
from pathlib import Path
ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
EXCLUDE_DIRS = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

# Collect all patterns of lines that end with </li> but don't start with <li
patterns = {}
for p in sorted(ROOT.rglob('*.html')):
    if set(p.parts) & {Path(d) for d in EXCLUDE_DIRS}: continue
    if p.name == 'google-site-verification.html': continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    opens = len(re.findall(r'<li[\s>]', text))
    closes = len(re.findall(r'</li>', text))
    if opens == closes: continue
    lines = text.split('\n')
    for ln in lines:
        stripped = ln.strip()
        if not stripped.endswith('</li>'): continue
        if stripped.startswith('<li') or stripped.startswith('<a'): continue  # valid cases
        # Get leading tag
        m = re.match(r'^\s*(<\w+)', ln)
        leading_tag = m.group(1) if m else 'TEXT'
        patterns.setdefault(leading_tag, []).append((p.relative_to(ROOT), stripped[:80]))

# Print top patterns
for tag, items in sorted(patterns.items(), key=lambda x: -len(x[1]))[:15]:
    print(f'\n{tag} ({len(items)} occurrences):')
    seen = set()
    for path, snip in items:
        if snip in seen: continue
        seen.add(snip)
        print(f'  [{path}] {snip!r}')
        if len(seen) > 3: break
