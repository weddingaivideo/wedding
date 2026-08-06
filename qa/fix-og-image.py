#!/usr/bin/env python3
"""
Fix og:image across all top-level pages — replace hero-wedding-vineyard.png
with og-image-1200x630.webp (8x smaller, proper 1.91:1 ratio for FB/Twitter).

Idempotent: re-running is a no-op.

Changed 2026-07-28 (Mavis SEO audit): swapped 295KB PNG for 38KB webp + 25KB avif.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Each page has a per-page og/twitter image rule: (page, old_image_basename, new_og_image)
# Hero pages share the same vineyard hero; gallery has its own collage.
PAGE_RULES = [
    # (relative page path, old image filename, new og image filename)
    ("index.html", "hero-wedding-vineyard.png", "og-image-1200x630.webp"),
    ("blog/index.html", "hero-wedding-vineyard.png", "og-image-1200x630.webp"),
    ("gallery/index.html", "gallery-collage.png", "og-gallery-1200x630.webp"),
    ("pricing/index.html", "hero-wedding-vineyard.png", "og-image-1200x630.webp"),
    ("privacy/index.html", "hero-wedding-vineyard.png", "og-image-1200x630.webp"),
    ("search/index.html", "hero-wedding-vineyard.png", "og-image-1200x630.webp"),
    ("services/index.html", "hero-wedding-vineyard.png", "og-image-1200x630.webp"),
    ("terms/index.html", "hero-wedding-vineyard.png", "og-image-1200x630.webp"),
]

PAGES = [p[0] for p in PAGE_RULES]

# (filename, alt text) — used to build the new og:image block
ALT_TEXT = {
    "og-image-1200x630.webp": "WeddingAI.video — AI-powered wedding video services",
    "og-gallery-1200x630.webp": "WeddingAI.video gallery — real before/after wedding video case studies",
}


def _make_old_pat(filename: str) -> re.Pattern:
    return re.compile(
        r'<meta\s+property="og:image"\s+content="https://weddingai\.video/images/'
        + re.escape(filename)
        + r'"\s*>'
    )


def _make_old_tw_pat(filename: str) -> re.Pattern:
    return re.compile(
        r'<meta\s+name="twitter:image"\s+content="https://weddingai\.video/images/'
        + re.escape(filename)
        + r'"\s*>'
    )

NEW_OG_TEMPLATE = (
    '<meta property="og:image" content="https://weddingai.video/images/{new_name}">\n'
    '    <meta property="og:image:width" content="1200">\n'
    '    <meta property="og:image:height" content="630">\n'
    '    <meta property="og:image:alt" content="{alt}">\n'
    '    <meta property="og:image:type" content="image/webp">'
)


def _new_tw(new_name: str) -> str:
    return f'<meta name="twitter:image" content="https://weddingai.video/images/{new_name}">'


def main() -> int:
    changed = 0
    for rel, old_filename, new_name in PAGE_RULES:
        p = ROOT / rel
        if not p.exists():
            print(f"  SKIP (not found): {rel}")
            continue
        content = p.read_text(encoding="utf-8")
        original = content
        og_pat = _make_old_pat(old_filename)
        tw_pat = _make_old_tw_pat(old_filename)
        n_og = len(og_pat.findall(content))
        n_tw = len(tw_pat.findall(content))
        new_og = NEW_OG_TEMPLATE.format(new_name=new_name, alt=ALT_TEXT.get(new_name, ""))
        content = og_pat.sub(new_og, content)
        content = tw_pat.sub(_new_tw(new_name), content)
        if content != original:
            p.write_text(content, encoding="utf-8")
            print(f"  ✓ {rel}: og={n_og} tw={n_tw} ({old_filename} -> {new_name})")
            changed += 1
        else:
            print(f"  - {rel}: no match for {old_filename}")
    print(f"\n{changed} files updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
