"""
Add <source srcset="...avif" type="image/avif"> BEFORE the existing
<source srcset="...webp" type="image/webp"> in every <picture> tag.

Picture tag source order matters: browser picks the first matching type.
So AVIF first (smallest), WebP second, original img last (fallback).

Idempotent.
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
IMG_DIR = ROOT / "images"
AVIF_SET = {p.stem for p in IMG_DIR.glob("*.avif")}

files = list(ROOT.rglob("*.html"))
files = [p for p in files if p.name != "google-site-verification.html"]

# Match a <source srcset="..." type="image/webp"> line and the corresponding
# <img src="...jpg/png" srcset="..."> we need to also AVIF.
# We'll rebuild each <picture> block.
PICTURE_PAT = re.compile(
    r'(<picture>)'
    r'\s*<source\s+'
    r'srcset="([^"]+)"\s+'
    r'type="image/webp"\s+'
    r'sizes="([^"]*)"'
    r'\s*>'
    r'\s*(<img\s+[^>]+?/?>)'
    r'\s*</picture>',
    re.DOTALL
)

def has_avif(stem_set, srcset):
    """Return True if at least one of the URLs in srcset has a matching .avif."""
    for url in re.findall(r'(\S+\.(?:jpg|jpeg|png|webp))', srcset):
        stem = Path(url).stem
        if stem in stem_set:
            return True
    return False

def make_avif_srcset(webp_srcset):
    """Build the AVIF srcset by swapping each WebP filename for its .avif sibling."""
    out = []
    for entry in webp_srcset.split(","):
        entry = entry.strip()
        if not entry:
            continue
        # entry like "url 360w"
        parts = entry.rsplit(" ", 1)
        if len(parts) != 2:
            continue
        url, w = parts
        # Find the basename
        path = Path(url)
        # Look for the matching -NNN.{ext} variant
        m = re.match(r"^(.+)-(\d+)\.(jpg|jpeg|png|webp)$", path.name, re.IGNORECASE)
        if m:
            base, size, ext = m.groups()
            new_name = f"{base}-{size}.avif"
        else:
            # Plain image (no -NNN suffix) — just swap extension
            new_name = path.stem + ".avif"
        new_url = str(path.parent / new_name).replace("\\", "/")
        out.append(f"{new_url} {w}")
    return ", ".join(out)

n = 0
for p in files:
    text = p.read_text(encoding="utf-8")
    original = text
    # Compute per-file AVIF set to keep this fast
    local_avif = {p.stem for p in p.parent.glob("*.avif")} if p.parent.exists() else set()

    def replace_pic(m):
        prefix, webp_srcset, sizes, img_tag = m.group(1), m.group(2), m.group(3), m.group(4)
        if "type=\"image/avif\"" in (m.group(0)):
            return m.group(0)  # already has AVIF
        # Build the AVIF srcset
        avif_srcset = make_avif_srcset(webp_srcset)
        return (
            f'{prefix}\n'
            f'    <source srcset="{avif_srcset}" type="image/avif" sizes="{sizes}">\n'
            f'    <source srcset="{webp_srcset}" type="image/webp" sizes="{sizes}">\n'
            f'    {img_tag}\n'
            f'  </picture>'
        )

    text = PICTURE_PAT.sub(replace_pic, text)

    if text != original:
        p.write_text(text, encoding="utf-8")
        n += 1

print(f"Done. {n} file(s) updated")
