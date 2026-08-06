"""
Generate AVIF versions of every sized image variant.
AVIF is 20-30% smaller than WebP at equivalent visual quality.

Strategy:
- Generate AVIF for every *-{size}.{jpg,png,webp} variant we already have
- quality=50 (visually equivalent to JPG q=80 in WebP, smaller file)
- Skip generation if AVIF is larger than WebP (rare but possible)
- Idempotent
"""
import re
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
IMG_DIR = ROOT / "images"

# Match our sized variants: name-123.ext
VARIANT_PAT = re.compile(r"^(.+)-(\d+)\.(jpg|jpeg|png|webp)$", re.IGNORECASE)

AVIF_QUALITY = 50  # good visual quality, small file
SKIP_IF_LARGER_THAN_WEBP = True

def main():
    variants = []
    for p in IMG_DIR.iterdir():
        if not p.is_file():
            continue
        m = VARIANT_PAT.match(p.name)
        if not m:
            continue
        # Only generate AVIF for the sized variants, not the original
        base, size_str, ext = m.groups()
        variants.append(p)

    print(f"Found {len(variants)} sized variants to convert")

    generated = 0
    skipped = 0
    failed = 0
    total_orig = 0
    total_avif = 0

    for src in sorted(variants):
        out = src.with_suffix(".avif")
        try:
            with Image.open(src) as im:
                im.load()
                w, h = im.size
                # Convert to RGB if needed (AVIF doesn't support all modes)
                if im.mode not in ("RGB", "RGBA"):
                    im = im.convert("RGB")
                im.save(out, "AVIF", quality=AVIF_QUALITY, speed=6)

            src_size = src.stat().st_size
            avif_size = out.stat().st_size
            total_orig += src_size
            total_avif += avif_size

            # Compare with WebP if exists
            webp = src.with_suffix(".webp")
            if SKIP_IF_LARGER_THAN_WEBP and webp.exists() and avif_size > webp.stat().st_size * 1.1:
                out.unlink()  # AVIF is bigger than WebP — skip
                skipped += 1
                print(f"  [skip] {out.name} - larger than webp ({avif_size//1024}KB > {webp.stat().st_size//1024}KB)")
                continue

            generated += 1
            pct = (1 - avif_size / src_size) * 100
            print(f"  [gen] {out.name} - {src_size//1024}KB -> {avif_size//1024}KB ({pct:+.0f}%)")
        except Exception as e:
            failed += 1
            print(f"  [err]  {src.name}: {e}")

    print()
    print(f"Generated: {generated} | Skipped (bigger than webp): {skipped} | Failed: {failed}")
    if total_orig > 0:
        print(f"Total size: {total_orig//1024:,} KB -> {total_avif//1024:,} KB ({(1 - total_avif/total_orig)*100:+.1f}%)")

if __name__ == "__main__":
    main()
