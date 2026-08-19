"""Re-verify after a brief wait."""
import sys
import time
import urllib.request

BASE = "https://weddingai.video"
GALLERY_URL = BASE + "/gallery/"

# 1. Gallery HTML — does it reference the new videos?
print("=== Gallery HTML ===", flush=True)
req = urllib.request.Request(GALLERY_URL, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
})
with urllib.request.urlopen(req, timeout=30) as r:
    html = r.read().decode("utf-8", errors="replace")

print(f"  HTML length: {len(html)} bytes", flush=True)

needles = [
    ("Ahmed &amp; Layla", "Ahmed & Layla card title"),
    ("case-ahmed-layla-broadcast", "Ahmed & Layla video URL"),
    ("Rodriguez", "Rodriguez card title"),
    ("case-rodriguez-glamorous-opener", "Rodriguez video URL"),
    ("Mei &amp; Jin", "Mei & Jin card title"),
    ("case-mei-jin-celebrity-package", "Mei & Jin video URL"),
]
for n, desc in needles:
    c = html.count(n)
    flag = "OK" if c > 0 else "MISSING"
    color = "\033[32m" if c > 0 else "\033[31m"
    print(f"  {color}{flag}\033[0m  {c:>3} hits  {desc}  ({n!r})", flush=True)

# Old static refs (should be GONE on the 3 replaced cards, but may still appear elsewhere)
old_refs = [
    ("/images/hero-wedding-vineyard-1024.webp", "Ahmed & Layla old static — used elsewhere on site (homepage, services), so non-zero is OK"),
    ("/images/catalog-celebrity-message-1280.webp", "Rodriguez old static — used elsewhere, non-zero OK"),
    ("/images/wedding-trailer-sunset-720.webp", "Mei & Jin old static — used elsewhere, non-zero OK"),
]
for o, desc in old_refs:
    c = html.count(o)
    print(f"  REF  {c:>3} hits  {desc}  ({o!r})", flush=True)

# 2. 9 video files — content-length check
print("\n=== 9 video/poster files on production ===", flush=True)
all_ok = True
for base in ["case-ahmed-layla-broadcast", "case-rodriguez-glamorous-opener", "case-mei-jin-celebrity-package"]:
    for ext in [".webm", ".mp4", "-poster.webp"]:
        url = f"{BASE}/images/{base}{ext}"
        try:
            req = urllib.request.Request(url, method="HEAD", headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126",
            })
            with urllib.request.urlopen(req, timeout=15) as r:
                cl = r.headers.get("Content-Length", "?")
                ct = r.headers.get("Content-Type", "?")
                color = "\033[32m"
                print(f"  {color}{r.status}\033[0m  cl={cl:>9}  ct={ct:<22}  {url}", flush=True)
        except Exception as e:
            all_ok = False
            print(f"  \033[31mERR\033[0m  {url}  ({e})", flush=True)

print("\n=== Verdict ===", flush=True)
if all_ok and all(html.count(n) > 0 for n, _ in needles if "video URL" in _):
    print("\033[32mDEPLOY OK: all 9 assets serve 200, gallery page references all 3 new videos.\033[0m", flush=True)
    sys.exit(0)
else:
    print("\033[31mDEPLOY INCOMPLETE — see above.\033[0m", flush=True)
    sys.exit(1)
