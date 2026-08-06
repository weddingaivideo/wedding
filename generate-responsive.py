"""
Generate responsive image variants + WebP for every JPG/PNG.
Inject srcset + sizes attributes into <img> tags.

Strategy
--------
We classify each image by its display size on the page:

  * avatar        — 48x48 CSS pixels        -> gen 48, 96
  * logo          — 356x126 CSS px (max)   -> gen 178, 356, 712
  * service-card  — fluid, aspect 16:9     -> gen 360, 720, 1280
  * case-card     — fluid, aspect 16:9     -> gen 360, 720, 1280
  * hero          — fluid, full-width      -> gen 640, 1024, 1280
  * generic       — fall back              -> gen 360, 720, 1280

For each size, we generate both the original format (jpg/png) and a .webp
counterpart. HTML srcset is then assembled: "small.webp 360w, med.webp 720w, big.webp 1280w"
with a sizes attribute that approximates the layout.

Idempotent. Skips variants that already exist.
"""
import re
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
IMG_DIR = ROOT / "images"

# ---------------------------------------------------------------------------
# Display size classifier.  The "kind" is inferred from the file basename
# or by inspecting the surrounding CSS.
# ---------------------------------------------------------------------------

# Filename -> kind
NAMED_KINDS = {
    "avatar-jennifer": "avatar",
    "avatar-mike-rachel": "avatar",
    "avatar-priya-arjun": "avatar",
    "avatar-sophie-david": "avatar",
    "avatar-emma": "avatar",
    "avatar-carolina": "avatar",
    "logo-full": "logo",
    "logo-icon": "icon",
    "hero-wedding-vineyard": "hero",
    "favicon": "favicon",
}

# Default sizes per kind: list of widths (px) to generate
KIND_SIZES = {
    "avatar":       [48, 96],
    "logo":         [178, 356, 712],
    "hero":         [640, 1024, 1280],
    "service-card": [360, 720, 1280],
    "case-card":    [360, 720, 1280],
    "icon":         [64, 128],
    "favicon":      [],
    "generic":      [360, 720, 1280],
}

# Per-kind srcset `sizes` attribute — describes how wide the image is
# displayed at common viewport widths.
KIND_SIZES_ATTR = {
    "avatar":       "(max-width: 600px) 48px, 48px",
    "logo":         "(max-width: 600px) 178px, 356px",
    "hero":         "(max-width: 600px) 100vw, (max-width: 1024px) 100vw, 100vw",
    "service-card": "(max-width: 600px) 100vw, (max-width: 1024px) 50vw, 33vw",
    "case-card":    "(max-width: 600px) 100vw, (max-width: 1024px) 50vw, 33vw",
    "icon":         "64px",
    "generic":      "(max-width: 600px) 100vw, (max-width: 1024px) 50vw, 33vw",
}

# Filename heuristic for cards (service card images and case card images)
CARD_KEYWORDS = ["service", "catalog", "preset", "cartoon-", "meme-",
                 "tribute-", "familymsg-", "petwedding-", "trailer-feat-",
                 "wedding-restoration-", "wedding-trailer-",
                 "slow-motion-first-dance", "family-tribute-hologram",
                 "interactive-screen", "realtime-cut", "guide-", "avatar-",
                 "testimonial-", "order-form", "pricing-cards", "live-comments",
                 "multilingual-split", "ai-video-generator-workspace",
                 "family-tribute-frame", "family-message-videocall",
                 "celebrity-message-screen", "meme-generator-gif-collage",
                 "cartoon-ghibli-style", "cartoon-realistic-combo",
                 "pet-wedding-golden-retrievers", "wedding-restoration-vhs-tv",
                 "gallery-collage"]

def classify(filename: str, max_native: int) -> str:
    base = Path(filename).stem
    if base in NAMED_KINDS:
        return NAMED_KINDS[base]
    for kw in CARD_KEYWORDS:
        if kw in base:
            return "service-card"
    # PNG with no specific keyword — likely a UI element / card
    if Path(filename).suffix.lower() == ".png":
        return "service-card"
    return "generic"

# ---------------------------------------------------------------------------
# Image processing
# ---------------------------------------------------------------------------

def gen_variant(src: Path, target_w: int, fmt_ext: str) -> Path:
    """Generate src-{w}.{ext} if it doesn't already exist."""
    out = src.parent / f"{src.stem}-{target_w}{fmt_ext}"
    if out.exists() and out.stat().st_mtime > src.stat().st_mtime:
        return out  # already generated and source hasn't changed
    with Image.open(src) as im:
        im.load()
        w, h = im.size
        # Never upscale
        if target_w >= w:
            return None  # skip — would be wasteful
        ratio = target_w / w
        new_size = (target_w, max(1, round(h * ratio)))
        im2 = im.resize(new_size, Image.LANCZOS)
        if fmt_ext == ".webp":
            im2 = im2.convert("RGB") if im2.mode == "RGBA" else im2
            im2.save(out, "WEBP", quality=78, method=6)
        elif fmt_ext == ".jpg" or fmt_ext == ".jpeg":
            im2 = im2.convert("RGB") if im2.mode == "RGBA" else im2
            im2.save(out, "JPEG", quality=80, optimize=True, progressive=True)
        elif fmt_ext == ".png":
            # Convert to palette for smaller PNG
            im2 = im2.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT, dither=Image.NONE)
            im2.save(out, "PNG", optimize=True, compress_level=9)
    return out

def process_image(src: Path):
    """Generate all sized variants + WebP versions for one source image."""
    base = src.stem
    if base in NAMED_KINDS and NAMED_KINDS[base] == "favicon":
        return None
    with Image.open(src) as im:
        w, _ = im.size
    kind = classify(src.name, w)
    sizes = KIND_SIZES.get(kind, KIND_SIZES["generic"])
    if not sizes:
        return None
    src_ext = src.suffix.lower()
    # For PNG sources, generate PNG variants; for JPG, generate JPG
    out_exts = [".webp"]
    if src_ext in (".jpg", ".jpeg"):
        out_exts.insert(0, ".jpg")
    elif src_ext == ".png":
        out_exts.insert(0, ".webp")  # PNG can stay as-is, just add WebP
        # Also add a PNG sized variant since some browsers still need it
        out_exts.insert(0, ".png")

    generated = []
    for ext in set(out_exts):
        for size in sizes:
            v = gen_variant(src, size, ext)
            if v:
                generated.append(v)
    return {
        "src": src,
        "kind": kind,
        "sizes_attr": KIND_SIZES_ATTR.get(kind, KIND_SIZES_ATTR["generic"]),
        "variants": generated,
    }

def main():
    srcs = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        srcs.extend(IMG_DIR.glob(ext))
    srcs = sorted(srcs)

    results = []
    for s in srcs:
        try:
            r = process_image(s)
            if r:
                results.append(r)
        except Exception as e:
            print(f"  [err] {s.name}: {e}")

    total_orig = sum(r["src"].stat().st_size for r in results)
    total_new = sum(v.stat().st_size for r in results for v in r["variants"])
    print(f"\n[ok] Generated variants for {len(results)} source images")
    print(f"     Original total: {total_orig/1024:,.0f} KB")
    print(f"     Variants total: {total_new/1024:,.0f} KB")
    print()
    print(f"{'Source':<40} {'Kind':<14} {'#vars':<8} {'TotalKB':<10}")
    print("-" * 72)
    for r in results:
        total = sum(v.stat().st_size for v in r["variants"]) / 1024
        print(f"  {r['src'].name:<38} {r['kind']:<14} {len(r['variants']):<8} {total:,.0f}")
    return results

if __name__ == "__main__":
    main()
