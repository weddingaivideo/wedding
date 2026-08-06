import re
from pathlib import Path
from collections import Counter
ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
EXCLUDE_DIRS = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

# My fix's regex
fix_pattern = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)((?:[^<>]*?))<([a-zA-Z][a-zA-Z0-9]*)')
# Full qa's regex
qa_pattern = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)(<[a-zA-Z][a-zA-Z0-9]*)')

# Apply fix to all files
all_files = []
for p in sorted(ROOT.rglob('*.html')):
    if set(p.parts) & {Path(d) for d in EXCLUDE_DIRS}: continue
    if p.name == 'google-site-verification.html': continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    # Apply fix
    new_text = fix_pattern.sub(lambda m: f'<{m.group(1)}><{m.group(3)}>' if not m.group(2) else f'<{m.group(1)}{m.group(2)}><{m.group(3)}>', text)
    new_text = re.sub(r'<ahref=', '<a href=', new_text)
    new_text = re.sub(r'<listyle=', '<li style=', new_text)
    # Count remaining cross-tag in new_text
    qa_matches = list(qa_pattern.finditer(new_text))
    if qa_matches:
        for m in qa_matches[:3]:
            print(f'{p.relative_to(ROOT)}: {m.group(0)[:60]} ... {new_text[max(0,m.start()-20):m.start()+50]}')
