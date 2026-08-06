#!/usr/bin/env python3
"""Full structural check: count opens vs closes for all major tags."""
import re
from pathlib import Path
from collections import Counter
ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
EXCLUDE_DIRS = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}
TAGS = ['html', 'head', 'body', 'header', 'footer', 'main', 'nav', 'section',
        'article', 'ul', 'ol', 'table', 'form', 'picture', 'figure',
        'blockquote', 'details', 'summary', 'aside']

def should_process(p):
    if p.name == 'google-site-verification.html': return False
    return not (set(p.parts) & {Path(d) for d in EXCLUDE_DIRS})

issues = 0
for p in sorted(ROOT.rglob('*.html')):
    if not should_process(p): continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    file_issues = []
    for tag in TAGS:
        opens = len(re.findall(rf'<{tag}[\s>]', text, re.IGNORECASE))
        closes = len(re.findall(rf'</{tag}>', text, re.IGNORECASE))
        if opens != closes:
            file_issues.append((tag, opens, closes))
    if file_issues:
        issues += 1
        rel = p.relative_to(ROOT)
        details = ', '.join(f'{t}:{o}/{c}' for t, o, c in file_issues)
        print(f'{rel}: {details}')

print(f'\nTotal files with tag balance issues: {issues}')
