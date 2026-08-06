#!/usr/bin/env python3
"""Fix missing <blockquote> in gallery testimonials section.
Pattern: </div><p style=...>quote</p><footer>...</footer></blockquote>
Need to add <blockquote> before <p style=...>
"""
import re
from pathlib import Path
ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
EXCLUDE_DIRS = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

def should_process(p):
    if p.name == 'google-site-verification.html': return False
    return not (set(p.parts) & {Path(d) for d in EXCLUDE_DIRS})

for p in sorted(ROOT.rglob('*.html')):
    if not should_process(p): continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    bq_open = len(re.findall(r'<blockquote', text))
    bq_close = len(re.findall(r'</blockquote>', text))
    if bq_close > bq_open:
        n_needed = bq_close - bq_open
        # Pattern: <p style="color: var(--color-text); font-style: italic; line-height: 1.6;" data-i18n="gallery.p_text..."
        text = re.sub(
            r'(<p style="color: var\(--color-text\); font-style: italic; line-height: 1\.6;"[^>]*data-i18n="gallery\.p_text)',
            r'<blockquote class="testimonial-card">\1',
            text,
            count=n_needed
        )
        # Fix any malformed <blockquoteclass= from previous run
        text = re.sub(r'<blockquoteclass="', r'<blockquote class="', text)
        if text != p.read_text(encoding='utf-8', errors='ignore'):
            p.write_text(text, encoding='utf-8')
            print(f"  {p.relative_to(ROOT)}: added {n_needed} <blockquote>")
