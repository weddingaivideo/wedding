"""
Fix duplicate data-i18n-attr=" in blog post meta description lines.
Pattern: <meta name="description" data-i18n-attr="data-i18n-attr="content:...key..." content="..." />
Fix:    <meta name="description" data-i18n-attr="content:...key..." content="..." />
"""
import re
from pathlib import Path

BLOG_DIR = Path(r"C:/Users/qiaoshan/.openclaw/workspace/weddingai/blog")
files_fixed = 0

for html_file in BLOG_DIR.rglob("index.html"):
    content = html_file.read_text(encoding="utf-8")
    if 'data-i18n-attr="data-i18n-attr=' not in content:
        continue
    # Replace the duplicated attribute name
    new_content = content.replace(
        'data-i18n-attr="data-i18n-attr="',
        'data-i18n-attr="'
    )
    # Count fixes
    n = content.count('data-i18n-attr="data-i18n-attr=')
    html_file.write_text(new_content, encoding="utf-8")
    print(f"  {html_file.relative_to(BLOG_DIR.parent.parent)}: fixed {n} occurrence(s)")
    files_fixed += 1

print(f"\nTotal: fixed {files_fixed} file(s)")
