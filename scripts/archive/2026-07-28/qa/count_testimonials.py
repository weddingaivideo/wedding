import re
from pathlib import Path
ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
EXCLUDE_DIRS = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}
for p in sorted(ROOT.rglob('*.html')):
    if set(p.parts) & {Path(d) for d in EXCLUDE_DIRS}: continue
    if p.name == 'google-site-verification.html': continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    avatars = len(re.findall(r'class="testimonial-avatar"', text))
    opens = len(re.findall(r'<blockquote', text))
    closes = len(re.findall(r'</blockquote>', text))
    if avatars > 0 and opens != closes:
        print(f'{p.relative_to(ROOT)}: avatars={avatars} <blockquote>={opens} </blockquote>={closes}')
