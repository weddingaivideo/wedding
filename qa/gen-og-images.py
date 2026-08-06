#!/usr/bin/env python3
"""Generate 1200x630 OG images for the top-level pages.

Each page gets its own crop from its own source image, exported to both
.webp and .avif. Sized to Facebook/Twitter/LinkedIn's recommended
1.91:1 ratio (1200x630), which gives the best preview across all
social platforms.

Run after any source image is updated:
  python qa/gen-og-images.py
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def make_og(source_rel: str, out_name: str, target=(1200, 630)) -> None:
    src = os.path.join(ROOT, source_rel)
    img = Image.open(src)
    src_w, src_h = img.size
    tgt_w, tgt_h = target
    # Center-crop the source to the target aspect, then resize.
    crop_h = int(src_w / (tgt_w / tgt_h))
    top = max(0, (src_h - crop_h) // 2)
    cropped = img.crop((0, top, src_w, top + crop_h))
    out = cropped.resize(target, Image.LANCZOS)
    webp = os.path.join(ROOT, "images", f"{out_name}.webp")
    avif = os.path.join(ROOT, "images", f"{out_name}.avif")
    out.save(webp, "WEBP", quality=85, method=6)
    out.save(avif, "AVIF", quality=70)
    w_size = os.path.getsize(webp) / 1024
    a_size = os.path.getsize(avif) / 1024
    src_size = os.path.getsize(src) / 1024
    print(f"  {source_rel} ({src_size:.1f} KB) -> {out_name}.webp ({w_size:.1f} KB) / .avif ({a_size:.1f} KB)")


if __name__ == "__main__":
    print("Generating 1200x630 OG images (1.91:1, FB/Twitter/LinkedIn best):")
    make_og("images/hero-wedding-vineyard.png", "og-image-1200x630")
    make_og("images/gallery-collage.png", "og-gallery-1200x630")
    print("Done.")
