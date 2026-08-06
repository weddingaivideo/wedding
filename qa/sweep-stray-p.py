"""
Site-wide fix: remove stray </p> after Privacy Policy / Terms of Service
links in the footer-bottom block. Pattern occurs in index.html, order/,
404.html (fixed), and likely all 10 service pages + 50 blog posts.

Pattern: `Terms of Service</a></p>` at end of footer-bottom line.
Fix:     `Terms of Service</a>` (no closing p).
"""
import re
from pathlib import Path

ROOT = Path(r"C:/Users/qiaoshan/.openclaw/workspace/weddingai")
total = 0
files = 0

for html_file in ROOT.rglob("*.html"):
    # Skip qa/ and scripts/ and tools/ (not deployed)
    rel = html_file.relative_to(ROOT)
    parts = rel.parts
    if 'qa' in parts or 'scripts' in parts or 'tools' in parts or 'tmp' in parts:
        continue
    content = html_file.read_text(encoding="utf-8")
    # Pattern: Terms of Service</a></p>  →  Terms of Service</a>
    new_content, n = re.subn(r'(Terms of Service</a>)</p>', r'\1', content)
    if n > 0:
        html_file.write_text(new_content, encoding="utf-8")
        total += n
        files += 1
        print(f"  {rel}: fixed {n}")

print(f"\nTotal: {total} stray </p> removed across {files} file(s)")
