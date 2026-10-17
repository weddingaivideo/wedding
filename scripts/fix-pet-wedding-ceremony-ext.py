#!/usr/bin/env python3
"""Convert pet-wedding-ceremony master from PNG to JPG and regenerate variants.

The HTML references pet-wedding-ceremony.jpg (not .png), so the master
must be JPG to match.
"""
from pathlib import Path
from PIL import Image

IMG_DIR = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai\images")
SIZES = [360, 720, 1280]

src_png = IMG_DIR / "pet-wedding-ceremony.png"
src_jpg = IMG_DIR / "pet-wedding-ceremony.jpg"

# Step 1: Convert master PNG -> JPG
with Image.open(src_png) as im:
    if im.mode != "RGB":
        im = im.convert("RGB")
    im.save(src_jpg, "JPEG", quality=80, optimize=True, progressive=True)
print(f"[ok] master: {src_jpg.name} ({src_jpg.stat().st_size / 1024:.1f} KB)")

# Step 2: Delete old PNG variants (cleanup)
for size in SIZES:
    for ext in [".png", ".webp"]:
        v = IMG_DIR / f"pet-wedding-ceremony-{size}{ext}"
        if v.exists():
            v.unlink()
            print(f"[rm] {v.name}")

# Step 3: Regenerate JPG variants
for size in SIZES:
    out = IMG_DIR / f"pet-wedding-ceremony-{size}.jpg"
    if out.exists():
        continue
    with Image.open(src_jpg) as im:
        im.load()
        w, h = im.size
        ratio = size / w if size < w else 1.0
        new_size = (size, max(1, round(h * ratio)))
        im2 = im.resize(new_size, Image.LANCZOS)
        if im2.mode != "RGB":
            im2 = im2.convert("RGB")
        im2.save(out, "JPEG", quality=80, optimize=True, progressive=True)
    print(f"[ok] {out.name} ({out.stat().st_size / 1024:.1f} KB)")

# Step 4: Delete the PNG master (cleanup)
if src_png.exists():
    src_png.unlink()
    print(f"[rm] {src_png.name}")
