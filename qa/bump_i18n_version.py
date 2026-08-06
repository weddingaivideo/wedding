"""Bump i18n.js cache buster from 3.19 to 3.21 across all HTML files."""
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
EXCLUDE_DIRS = {"admin", "functions", "tmp", "__pycache__", "qa", "i18n", "js", "styles", "scripts", "docs"}

def should_process(p):
    if p.name == "google-site-verification.html": return False
    return not (set(p.parts) & {Path(d) for d in EXCLUDE_DIRS})

total = 0
for p in sorted(ROOT.rglob("*.html")):
    if not should_process(p): continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    new = text.replace('i18n.js?v=3.19', 'i18n.js?v=3.21')
    if new != text:
        p.write_text(new, encoding='utf-8')
        total += 1
print(f"Bumped {total} files: i18n.js?v=3.19 -> ?v=3.21")
