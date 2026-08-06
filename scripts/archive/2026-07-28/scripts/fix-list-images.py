"""Replace <div class="img-placeholder">NN</div> with the actual hero image
in blog/index.html. Idempotent."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = ROOT / "blog" / "index.html"
ARTICLES = ROOT / "articles"
HERO = ROOT / "images" / "blog" / "hero"


def slug_from_href(match):
    href = match.group(1)
    m = re.search(r"/blog/([^/\"]+)/?", href)
    if m:
        return m.group(1)
    return None


text = LIST.read_text(encoding="utf-8")
n = 0

# Pattern: a card with a /blog/<slug>/ link and a placeholder inside
# We need: <div class="case-img"...> ... <div class="img-placeholder">NN</div> ... </div>
# Replace with: wrap image inside the case-img
def repl(m):
    global n
    full = m.group(0)
    slug_m = re.search(r'href="(/blog/([^/"]+)/?)"', full)
    if not slug_m:
        return full
    slug = slug_m.group(2)
    # Get article title from the H3 link
    title_m = re.search(r'title="Read: ([^\"]+)"', full)
    title = title_m.group(1) if title_m else slug
    # Check hero file exists
    hero_path = HERO / f"{slug}.jpg"
    if not hero_path.exists():
        return full
    # Replace the placeholder div with an img, and wrap the case-img with a link
    new = re.sub(
        r'<div class="case-img" role="img" aria-label="[^"]*">\s*<div class="img-placeholder">[^<]+</div>\s*</div>',
        f'<a href="/blog/{slug}/" class="case-img-link" title="Read: {title}">'
        f'<div class="case-img" role="img" aria-label="{title}">'
        f'<img src="/images/blog/hero/{slug}.jpg" alt="{title}" loading="lazy" width="640" height="360" />'
        f'</div></a>',
        full,
    )
    if new != full:
        n += 1
    return new

# Find every <article class="case-card">...</article>
new_text = re.sub(
    r'<article class="case-card">.*?</article>',
    repl,
    text,
    flags=re.DOTALL,
)

LIST.write_text(new_text, encoding="utf-8")
print(f"[ok] blog/index.html: {n} cards updated with hero images")
