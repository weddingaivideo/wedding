"""
Recompress damaged PNG files using palette quantization.
Original PNGs were created with a tool that produced ~270KB files at 1024x1024.
Pillow's default save bloated them to ~1MB. This converts to 256-color palette
which is the typical strategy used by pngquant and gives comparable sizes.
"""
from PIL import Image
from pathlib import Path
import os

ROOT = Path("images")
results = []
pngs = sorted(ROOT.glob("*.png"))

for p in pngs:
    orig_size = p.stat().st_size
    # Skip small ones
    if orig_size < 200_000:
        continue
    try:
        with Image.open(p) as im:
            im.load()
            if im.mode == "RGBA":
                # Has alpha - preserve it
                alpha = im.split()[-1]
                rgb = im.convert("RGB")
                p_img = rgb.quantize(colors=255, method=Image.MEDIANCUT, dither=Image.NONE)
                # Re-apply alpha
                p_img.putalpha(alpha)
            else:
                rgb = im.convert("RGB")
                p_img = rgb.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.NONE)
            p_img.save(p, "PNG", optimize=True, compress_level=9)
        new_size = p.stat().st_size
        results.append((p.name, orig_size, new_size, (1 - new_size/orig_size)*100))
    except Exception as e:
        results.append((p.name, orig_size, -1, str(e)))

# Print
print(f"{'File':<40} {'Before':>10} {'After':>10} {'Saved':>8}")
print("-" * 72)
total_before = total_after = 0
for name, before, after, saved in results:
    if after < 0:
        print(f"  [err] {name}: {saved}")
    else:
        total_before += before
        total_after += after
        print(f"  {name:<38} {before/1024:>8.0f}KB {after/1024:>8.0f}KB {saved:>6.1f}%")
print("-" * 72)
print(f"  {'TOTAL':<38} {total_before/1024:>8.0f}KB {total_after/1024:>8.0f}KB {(1-total_after/total_before)*100:>6.1f}%")
