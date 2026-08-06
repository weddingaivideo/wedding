"""Remove the standalone <figure class="blog-hero"> below page-hero.

The hero image now sits inside .page-hero-bg as a backdrop for the title.
The standalone <figure class="blog-hero"> below is a duplicate and should
go away.
"""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
BLOG = ROOT / "blog"

# Match the entire figure.blog-hero block including surrounding whitespace
PAT = re.compile(
    r'[ \t]*<figure class="blog-hero">\s*<img[^>]+/?>\s*</figure>\s*',
    re.DOTALL,
)

count = 0
for html_file in sorted(BLOG.glob("*/index.html")):
    text = html_file.read_text(encoding='utf-8')
    new_text, n = PAT.subn('', text)
    if n == 0:
        continue
    html_file.write_text(new_text, encoding='utf-8')
    print(f"  OK  {html_file.parent.name}")
    count += 1

print(f"\nRemoved {count} duplicate <figure class='blog-hero'>.")
