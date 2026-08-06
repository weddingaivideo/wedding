"""
LCP optimization for index.html hero image (hero-wedding-vineyard).

Three things, in order of impact:

1. <link rel="preload" as="image" image-srcset=...> in <head>
   - Browser discovers the LCP candidate during HTML parse, starts fetch
     immediately. Saves ~100-200ms vs. discovering it from the <body>.

2. <img fetchpriority="high">
   - Tells the browser this image is the LCP candidate. Even if other
     resources are queued, this one jumps the line.

3. Remove loading="lazy" from the LCP image
   - Lazy loading defers loading until layout confirms image is in
     viewport. For an above-the-fold LCP image, this adds 50-200ms of
     unnecessary delay. (Browser heuristics do handle this in some
     cases, but explicit is better.)

Idempotent. Only touches the hero on index.html.
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
target = ROOT / "index.html"
text = target.read_text(encoding="utf-8")
original = text

# ---------------------------------------------------------------------------
# 1) Inject <link rel="preload"> in <head> after the existing preconnects
# ---------------------------------------------------------------------------

preload_html = '''    <link rel="preload" as="image"
          href="images/hero-wedding-vineyard-1024.webp"
          imagesrcset="images/hero-wedding-vineyard-640.webp 640w, images/hero-wedding-vineyard-1024.webp 1024w, images/hero-wedding-vineyard-1280.webp 1280w, images/hero-wedding-vineyard.webp 1600w"
          imagesizes="100vw"
          fetchpriority="high">'''

# Also generate the 1280 and 1600 webp variants from the original PNG if not present.
# (We already have 1280; 1600 doesn't exist for this hero, but the srcset above
#  will gracefully fall back to 1280w on browsers that hit a 1600w viewport.)
# To be safe, generate the 1600 variant right now.
from PIL import Image
img1280 = Image.open(ROOT / "images" / "hero-wedding-vineyard.png")
if img1280.width >= 1600:
    img1600 = img1280.resize((1600, int(img1280.height * 1600 / img1280.width)), Image.LANCZOS)
    out = ROOT / "images" / "hero-wedding-vineyard-1600.webp"
    if not out.exists():
        img1600.convert("RGB").save(out, "WEBP", quality=78, method=6)
        print(f"[gen] {out.name} ({out.stat().st_size//1024} KB)")

if "rel=\"preload\" as=\"image\"" not in text:
    # Inject right after the preconnect block (after the last dns-prefetch line)
    text = re.sub(
        r'(<link rel="dns-prefetch"[^>]+static\.cloudflareinsights\.com[^>]*>)',
        rf'\1\n{preload_html}',
        text,
        count=1
    )

# ---------------------------------------------------------------------------
# 2 + 3) Update the hero <picture>/<img> in <body>
# - Remove loading="lazy" from the hero <img>
# - Add fetchpriority="high"
# - Update srcset to include 1280w (and 1600w if we just generated it)
# ---------------------------------------------------------------------------

# Match the hero <picture> block specifically (it's the only one in the hero section)
hero_pat = re.compile(
    r'(<picture><source\s+)'
    r'srcset="hero-wedding-vineyard-640\.webp 640w, hero-wedding-vineyard-1024\.webp 1024w"'
    r'(\s+type="image/webp"\s+sizes="[^"]*">)'
    r'(<img\s+)'
    r'src="images/hero-wedding-vineyard\.png"\s+'
    r'alt="([^"]+)"\s+'
    r'width="(\d+)"\s+height="(\d+)"\s+'
    r'loading="lazy"\s+'
    r'srcset="hero-wedding-vineyard-640\.png 640w, hero-wedding-vineyard-1024\.png 1024w"\s+'
    r'sizes="([^"]*)"',
    re.DOTALL
)

def fix_hero(m):
    pre_source = m.group(1)
    mid_source = m.group(2)
    pre_img = m.group(3)
    alt = m.group(4)
    w = m.group(5)
    h = m.group(6)
    sizes = m.group(7)

    new_source = (
        f'{pre_source}'
        f'srcset="images/hero-wedding-vineyard-640.webp 640w, '
        f'images/hero-wedding-vineyard-1024.webp 1024w, '
        f'images/hero-wedding-vineyard-1280.webp 1280w, '
        f'images/hero-wedding-vineyard.webp 1600w"'
        f'{mid_source}'
    )
    new_img = (
        f'{pre_img}'
        f'src="images/hero-wedding-vineyard.png" '
        f'alt="{alt}" '
        f'width="{w}" height="{h}" '
        f'fetchpriority="high" '
        f'srcset="images/hero-wedding-vineyard-640.png 640w, '
        f'images/hero-wedding-vineyard-1024.png 1024w, '
        f'images/hero-wedding-vineyard-1280.png 1280w" '
        f'sizes="{sizes}"'
    )
    return f'{new_source}{new_img}'

text = hero_pat.sub(fix_hero, text)

# ---------------------------------------------------------------------------
# Write back
# ---------------------------------------------------------------------------

if text != original:
    target.write_text(text, encoding="utf-8")
    print(f"[ok] index.html updated")
else:
    print("[skip] no changes (already optimized or hero not found)")
