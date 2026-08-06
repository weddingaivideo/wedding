"""
Fix broken <source srcset="..."> paths in service pages.

inject-avif-source.py had a bug: it extracted AVIF srcset URLs from the
existing WebP srcset and replaced the extension, but DIDN'T preserve the
directory prefix. So in services/personalization/meme-generator.html:

    WRONG: <source srcset="meme-generator-gif-collage-360.avif 360w, ...">
    RIGHT: <source srcset="../../images/meme-generator-gif-collage-360.avif 360w, ...">

The depth-aware prefix has to match the depth of the <img src="..."> that
already exists in the same <picture> block.

Strategy: walk each <picture>...</picture> block. For each <source>, look
at the corresponding <img> to find the correct directory prefix, then
apply it to the source's srcset URLs.

Idempotent.
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
files = list(ROOT.rglob("*.html"))
files = [p for p in files if p.name != "google-site-verification.html"]

# Match a <picture> block
PICTURE_PAT = re.compile(
    r'(<picture>)(.*?)(</picture>)',
    re.DOTALL
)

# Find the img src within a picture block
IMG_SRC_PAT = re.compile(r'<img\s[^>]*src="([^"]+)"')

# Find all source srcset URLs (no leading slash, no .., just bare filename)
BARE_URL_PAT = re.compile(r'\b([a-z][a-z0-9_\-]+\.(avif|webp))(?=\s+[0-9]+w)', re.IGNORECASE)

def compute_prefix(img_src: str) -> str:
    """Extract the directory prefix from an img src, e.g. '../images/' or '../../images/'."""
    # img src like "../images/foo.jpg" or "images/foo.jpg" or "../../images/foo.jpg"
    # Get the directory part
    p = Path(img_src)
    parent = p.parent  # e.g. "../images" or "images" or "."
    parent_str = str(parent).replace("\\", "/")
    if parent_str == ".":
        return ""
    return parent_str + "/"

def fix_picture(m):
    full = m.group(0)
    # Find the img src to determine the correct prefix
    img_match = IMG_SRC_PAT.search(m.group(2))
    if not img_match:
        return full
    img_src = img_match.group(1)
    prefix = compute_prefix(img_src)
    if not prefix:
        return full  # no prefix needed (root-level file)

    # Now fix all <source> tags inside this picture
    new = re.sub(
        r'(<source\s+srcset=")([^"]+)("[^>]*>)',
        lambda sm: sm.group(1) + ", ".join(
            (prefix + url) if not url.startswith(("/", "../", "http", "mailto:")) else url
            for url in (u.strip() for u in sm.group(2).split(","))
        ) + sm.group(3),
        full
    )
    return new

n = 0
for f in files:
    text = f.read_text(encoding="utf-8")
    new = PICTURE_PAT.sub(fix_picture, text)
    if new != text:
        f.write_text(new, encoding="utf-8")
        n += 1
        rel = f.relative_to(ROOT)
        print(f"[fixed] {rel}")

print(f"\nDone. {n} file(s) fixed")
