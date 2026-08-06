#!/usr/bin/env python3
"""Add missing <blockquote class="testimonial-card"> before each
<picture class="testimonial-avatar"> in testimonials sections.
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
    # Check if there are </blockquote> without matching <blockquote
    avatar_count = len(re.findall(r'class="testimonial-avatar"', text))
    bq_open = len(re.findall(r'<blockquote', text))
    bq_close = len(re.findall(r'</blockquote>', text))
    if avatar_count > 0 and bq_close > bq_open:
        # Add <blockquote class="testimonial-card"> before each <picture class="testimonial-avatar">
        n_needed = bq_close - bq_open
        text = re.sub(
            r'(<picture class="testimonial-avatar">)',
            r'<blockquote class="testimonial-card">\1',
            text,
            count=n_needed
        )
        p.write_text(text, encoding='utf-8')
        print(f"  {p.relative_to(ROOT)}: added {n_needed} <blockquote>")
