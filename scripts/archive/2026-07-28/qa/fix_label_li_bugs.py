#!/usr/bin/env python3
"""Fix i18n_inject leftover bugs:
 - `<span class="required">*</span></label>` → drop the spurious </label>
 - `<li></select></li>` → drop the spurious <li></li>
 - Other orphan closing tags injected by i18n_inject
"""
import re
from pathlib import Path

ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
EXCLUDE_DIRS = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

def should_process(p):
    if p.name == 'google-site-verification.html': return False
    return not (set(p.parts) & {Path(d) for d in EXCLUDE_DIRS})

def fix_text(text):
    # 1. Spurious </label> after </span>: pattern <span class="required">*</span></label>
    text = re.sub(r'(<span class="required">[^<]*</span>)</label>', r'\1', text)
    # 2. <li></select></li> and <li></X></li> where X is select/textarea/input
    text = re.sub(r'<li></(select|textarea|input)></li>', r'</\1>', text)
    # 3. Spurious </li> right after </span> or </strong> (when previous was content)
    # This is more aggressive — only if line ends with </li> and no matching <li>
    new_lines = []
    for line in text.split('\n'):
        li_opens = len(re.findall(r'<li[\s>]', line))
        li_closes = len(re.findall(r'</li>', line))
        if li_closes > li_opens:
            n_needed = li_closes - li_opens
            m = re.match(r'^(\s*)(.*)$', line)
            if m:
                ws, content = m.group(1), m.group(2)
                line = ws + '<li>' * n_needed + content
        new_lines.append(line)
    text = '\n'.join(new_lines)
    return text

total = 0
for p in sorted(ROOT.rglob('*.html')):
    if not should_process(p): continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    new_text = fix_text(text)
    if new_text != text:
        p.write_text(new_text, encoding='utf-8')
        total += 1
        print(f'  {p.relative_to(ROOT)}')
print(f'\nTotal: {total} files updated')
