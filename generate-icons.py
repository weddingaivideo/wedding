"""
Generate PWA icons from the existing logo.
Outputs apple-touch-icon.png (180x180), icon-192.png, icon-512.png
into the project root, then writes manifest.json.
"""
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).parent

# Use the full logo (logo-full.jpeg) as the base
src = ROOT / "images" / "logo-full.jpeg"
img = Image.open(src).convert("RGBA")
print(f"Source: {src.name}  {img.size}")

# Pad to square so the logo isn't squashed
w, h = img.size
side = max(w, h)
square = Image.new("RGBA", (side, side), (255, 255, 255, 255))
square.paste(img, ((side - w) // 2, (side - h) // 2))

# 180x180 apple-touch-icon (no transparency for iOS)
apple = square.copy()
# Solid white background
bg = Image.new("RGBA", apple.size, (255, 255, 255, 255))
bg.paste(apple, mask=apple.split()[-1])
bg.resize((180, 180), Image.LANCZOS).save(ROOT / "apple-touch-icon.png", "PNG", optimize=True)
print(f"[+] apple-touch-icon.png (180x180)")

# 192 and 512 PWA icons (with transparency for the splash/manifest)
square.resize((192, 192), Image.LANCZOS).save(ROOT / "icon-192.png", "PNG", optimize=True)
square.resize((512, 512), Image.LANCZOS).save(ROOT / "icon-512.png", "PNG", optimize=True)
print(f"[+] icon-192.png")
print(f"[+] icon-512.png")
