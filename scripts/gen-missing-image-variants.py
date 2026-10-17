#!/usr/bin/env python3
"""Generate missing srcset variants for the 7 broken-image masters.

Run once. Idempotent (skips if variant already exists).

Output: -360.jpg, -720.jpg, -1280.jpg + -360.webp, -720.webp, -1280.webp
for each master in MISSING_MASTERS (per the 2026-10-16 SF crawl + Tier 1b).
"""
from pathlib import Path
from PIL import Image

IMG_DIR = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai\images")

MISSING_MASTERS = [
    "cartoon-pixar.jpg",
    "meme-best-man-speech.jpg",
    "pet-wedding-ceremony.png",
    "multilingual-split-screen.png",
    "trailer-premium.jpg",
    "trailer-standard.jpg",
    "pet-proposal.jpg",
]

SIZES = [360, 720, 1280]
JPG_QUALITY = 80
WEBP_QUALITY = 78


def gen_variant(src: Path, target_w: int, fmt_ext: str) -> Path:
    out = src.parent / f"{src.stem}-{target_w}{fmt_ext}"
    if out.exists():
        return out  # idempotent
    with Image.open(src) as im:
        im.load()
        w, h = im.size
        if target_w >= w:
            # Never upscale — write same-size file so srcset still resolves
            ratio = 1.0
        else:
            ratio = target_w / w
        new_size = (target_w, max(1, round(h * ratio)))
        im2 = im.resize(new_size, Image.LANCZOS)
        # Convert any non-RGB mode (P, RGBA, LA, etc.) to RGB before JPEG save
        if im2.mode != "RGB":
            im2 = im2.convert("RGB")
        if fmt_ext == ".webp":
            im2.save(out, "WEBP", quality=WEBP_QUALITY, method=6)
        else:
            im2.save(out, "JPEG", quality=JPG_QUALITY, optimize=True, progressive=True)
    return out


def main():
    total = 0
    for name in MISSING_MASTERS:
        src = IMG_DIR / name
        if not src.exists():
            print(f"  [skip] {name} (master missing)")
            continue
        # JPG variants (skip for PNG masters — they get .png variants only)
        exts = [".webp"]
        if src.suffix.lower() in (".jpg", ".jpeg"):
            exts.insert(0, ".jpg")
        elif src.suffix.lower() == ".png":
            exts.insert(0, ".png")
        for ext in exts:
            for size in SIZES:
                v = gen_variant(src, size, ext)
                if v:
                    print(f"  [ok] {v.name}  ({v.stat().st_size / 1024:.1f} KB)")
                    total += 1
    print(f"\nTotal: {total} variants generated")


if __name__ == "__main__":
    main()
