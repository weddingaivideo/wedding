#!/usr/bin/env python3
"""Generate a maskable icon from the existing 512x512 icon.

Maskable icons must respect the "safe zone": the inner 40% radius
circle of the 512x512 canvas is the only region guaranteed to be visible
on all platforms (Android adaptive icons, etc.). The outer 20% is
the "bleed" zone where platforms may crop.

Approach:
  1. Load existing 512x512 icon.
  2. Create a 512x512 canvas.
  3. Pad-resize the logo to ~80% of canvas (so it sits inside the safe
     zone with a transparent border).
  4. Save as icon-512-maskable.png.

Reference: https://web.dev/maskable-icon/
"""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "icon-512.png"
DST = ROOT / "icon-512-maskable.png"

# Target size: keep at 512 (maskable spec recommends 512x512 minimum).
# The "safe zone" is a circle of diameter = 0.8 * canvas = 409.6 px
# (i.e. centered area covering ~80% of the canvas, leaving 10% padding
# on each side). The outer 20% is allowed to be cropped by the platform.
SAFE_ZONE_PCT = 80  # 80% of canvas

# Background color: solid (not transparent) so platforms that DON'T
# honor maskable (e.g. older iOS) still see a square icon. Use a neutral
# color matching the brand theme.
BG_COLOR = (253, 251, 248, 255)  # var(--color-bg) #fdfbf8, fully opaque


def main() -> int:
    if not SRC.exists():
        print(f"ERROR: source icon not found: {SRC}")
        return 1

    with Image.open(SRC) as src:
        src.load()
        if src.mode != "RGBA":
            src = src.convert("RGBA")

        size = 512
        # Build the canvas with the brand background color.
        canvas = Image.new("RGBA", (size, size), BG_COLOR)

        # Compute the safe-zone scale. We want the logo to fill 80% of
        # the canvas (so it sits inside the safe-zone circle with a
        # ~10% transparent/brand-color border all around).
        target = int(size * SAFE_ZONE_PCT / 100)
        # Use LANCZOS for high-quality downscale.
        logo = src.resize((target, target), Image.LANCZOS)

        # Center-paste.
        offset = (size - target) // 2
        canvas.paste(logo, (offset, offset), logo)

        canvas.save(DST, "PNG", optimize=True)
        size_bytes = DST.stat().st_size
        print(f"Wrote {DST.relative_to(ROOT)}: {size_bytes:,} bytes ({size}x{size})")
        return 0


if __name__ == "__main__":
    sys.exit(main())
