"""Strip the title region from blog/index.html.

The user wants blog/ to go directly to the article list, with no hero/title.
For SEO/accessibility, keep a heading chain by adding sr-only h1 + h2 at the
top of the list section.
"""
import re
from pathlib import Path

p = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai\blog\index.html")
text = p.read_text(encoding="utf-8")

original = text

# 1) Remove the page-hero block (the title region with the h1 and description).
HERO_RE = re.compile(
    r'\s*<section class="page-hero page-hero-small">.*?</section>\s*',
    re.DOTALL,
)
text, n_hero = HERO_RE.subn('\n        ', text)
print(f"removed page-hero: {n_hero} match(es)")

# 2) Remove the visible h2 "All Wedding Video Guides & Tips" inside the list section.
#    The user wants the list to be the only visible content.
H2_RE = re.compile(
    r'\s*<h2 style="text-align: center; font-size: 1\.5rem; margin-top: 0; margin-bottom: 1\.5rem;">All Wedding Video Guides &amp; Tips</h2>',
)
text, n_h2 = H2_RE.subn('', text)
print(f"removed visible h2: {n_h2} match(es)")

# 3) Inject a sr-only h1 + h2 right at the top of the article list section,
#    so heading structure stays h1 -> h2 -> h3 (no skip, good for SEO/screen readers).
SR_HEADINGS = (
    '                <h1 class="sr-only">WeddingAI.video Blog</h1>\n'
    '                <h2 class="sr-only">All Articles</h2>\n'
    '                '
)

# Find the cases-grid and insert headings right before it
CASES_GRID = '<div class="cases-grid">'
if CASES_GRID in text:
    text = text.replace(CASES_GRID, SR_HEADINGS + CASES_GRID, 1)
    print("inserted sr-only h1 + h2 before cases-grid")
else:
    print("WARN: cases-grid not found")

if text == original:
    raise SystemExit("no changes made")

p.write_text(text, encoding="utf-8")
print(f"\nOK: {p}")
