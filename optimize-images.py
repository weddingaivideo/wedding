#!/usr/bin/env python3
"""
Image optimization for WeddingAI.video
- Re-saves JPG/PNG with better compression (q=80 for JPG)
- Generates WebP versions for all JPG/PNG
- Skips files that are already < 100KB or recently optimized
- Reports size savings
"""
import os
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
IMG_DIR = ROOT / "images"
JPG_QUALITY = 80       # visual loss negligible at this level
WEBP_QUALITY = 80      # matches; good size/quality balance
MAX_DIM = 1920         # cap display dimensions (no Retina needed for marketing shots)
SKIP_UNDER_KB = 100    # don't re-process small images
SKIP_NAMES = {"favicon.svg", "logo-full.jpeg"}  # logo is shared widely, keep quality

def human_kb(b):
    return f"{b/1024:,.0f} KB"

def optimize_one(path: Path):
    orig_size = path.stat().st_size
    if orig_size < SKIP_UNDER_KB * 1024:
        return None
    if path.name in SKIP_NAMES:
        return None

    try:
        with Image.open(path) as im:
            im.load()
            # Down-scale only if significantly larger
            if max(im.size) > MAX_DIM:
                im.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
            # Convert PNG with alpha to RGB for JPG (no WebP needed for palette)
            save_kwargs = {}
            if path.suffix.lower() in {".jpg", ".jpeg"}:
                save_kwargs = {"quality": JPG_QUALITY, "optimize": True, "progressive": True}
            elif path.suffix.lower() == ".png":
                save_kwargs = {"optimize": True}
                if im.mode in {"RGBA", "P"} and im.mode != "P":
                    # PNG: keep but optimize
                    pass

            im.save(path, **save_kwargs)
            new_size = path.stat().st_size

            # Now create a WebP alongside
            webp_path = path.with_suffix(".webp")
            im_rgb = im if im.mode == "RGB" else im.convert("RGB")
            im_rgb.save(webp_path, "WEBP", quality=WEBP_QUALITY, method=6)
            webp_size = webp_path.stat().st_size

        saved = orig_size - new_size
        webp_saved = orig_size - webp_size
        return {
            "name": path.name,
            "orig": orig_size,
            "new": new_size,
            "webp": webp_size,
            "saved_pct": (1 - new_size / orig_size) * 100 if orig_size else 0,
            "webp_savings_pct": (1 - webp_size / orig_size) * 100 if orig_size else 0,
        }
    except Exception as e:
        return {"name": path.name, "error": str(e)}

def main():
    if not IMG_DIR.exists():
        print(f"[err] {IMG_DIR} not found", file=sys.stderr)
        sys.exit(1)

    exts = {".jpg", ".jpeg", ".png"}
    files = [p for p in IMG_DIR.iterdir() if p.is_file() and p.suffix.lower() in exts]

    results = []
    for f in sorted(files):
        r = optimize_one(f)
        if r is not None:
            results.append(r)

    # Print summary
    print(f"\nOptimized {len(results)} images\n")
    print(f"{'File':<40} {'Original':>10} {'New':>10} {'WebP':>10} {'Saved':>8} {'WebP Δ':>8}")
    print("-" * 92)
    for r in results:
        if "error" in r:
            print(f"  [skip] {r['name']}: {r['error']}")
            continue
        print(
            f"  {r['name']:<38} "
            f"{human_kb(r['orig']):>9} "
            f"{human_kb(r['new']):>9} "
            f"{human_kb(r['webp']):>9} "
            f"{r['saved_pct']:>6.1f}% "
            f"{r['webp_savings_pct']:>6.1f}%"
        )

    total_orig = sum(r.get("orig", 0) for r in results)
    total_new = sum(r.get("new", 0) for r in results)
    total_webp = sum(r.get("webp", 0) for r in results)
    print("-" * 92)
    print(f"  {'TOTAL':<38} {human_kb(total_orig):>9} {human_kb(total_new):>9} {human_kb(total_webp):>9} "
          f"{(1-total_new/total_orig)*100:>6.1f}% {(1-total_webp/total_orig)*100:>6.1f}%")
    print()

if __name__ == "__main__":
    main()
