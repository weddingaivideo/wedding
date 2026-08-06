"""Inject hero image into blog post page-hero-bg so the title sits on a real image.

The .page-hero-bg div on blog posts is empty, so the title appears on a flat gray
gradient (.page-hero-overlay). We already generated 50 hero images at
/images/blog/hero/{slug}.jpg — put them inside .page-hero-bg so the dark overlay
falls on the image and the title has a proper backdrop.
"""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
BLOG = ROOT / "blog"

# Match: <div class="page-hero-bg"></div>  (empty)
BG_RE = re.compile(r'<div class="page-hero-bg"></div>')
# Match h1 text to use as alt
H1_RE = re.compile(r'<h1>(.*?)</h1>', re.DOTALL)

count = 0
for html_file in sorted(BLOG.glob("*/index.html")):
    slug = html_file.parent.name
    text = html_file.read_text(encoding='utf-8')
    if BG_RE.search(text) is None:
        # already has a non-empty page-hero-bg
        continue
    # Get h1 alt
    h1_match = H1_RE.search(text)
    if not h1_match:
        print(f"  WARN {slug}: no <h1> found")
        continue
    alt = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
    alt = alt.replace('"', '&quot;')
    new_bg = (
        f'<div class="page-hero-bg">\n'
        f'                <img src="/images/blog/hero/{slug}.jpg" alt="{alt}" loading="eager" width="1280" height="720" />\n'
        f'            </div>'
    )
    text = BG_RE.sub(new_bg, text, count=1)
    html_file.write_text(text, encoding='utf-8')
    print(f"  OK  {slug}")
    count += 1

print(f"\nInjected hero into {count} blog posts.")
