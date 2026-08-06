#!/usr/bin/env python3
"""Add missing </body> before </html> when there's a <body> open but no close."""
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
    body_open = len(re.findall(r'<body[\s>]', text))
    body_close = len(re.findall(r'</body>', text))
    if body_open > body_close:
        # Add </body> right before </html>
        new_text = re.sub(r'(\s*)</html>', r'\1</body>\n</html>', text, count=1)
        if new_text != text:
            p.write_text(new_text, encoding='utf-8')
            print(f"  {p.relative_to(ROOT)}: added </body>")
