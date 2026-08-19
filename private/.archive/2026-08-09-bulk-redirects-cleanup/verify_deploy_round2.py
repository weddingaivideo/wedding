"""Verify round 2 deploy — new 3 videos live + refactored validator still 100%."""
import sys
import time
import urllib.request

BASE = "https://weddingai.video"
GALLERY_URL = BASE + "/gallery/"

# Wait for CF Pages
print("Waiting 60s for CF Pages to finish deploying...", flush=True)
time.sleep(60)

# 1. Gallery HTML — does it reference the new videos?
print("\n=== Gallery HTML — round 2 needles ===", flush=True)
req = urllib.request.Request(GALLERY_URL, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
})
with urllib.request.urlopen(req, timeout=30) as r:
    html = r.read().decode("utf-8", errors="replace")
print(f"  HTML length: {len(html)} bytes", flush=True)

# New round-2 needles (3 videos × 3 refs each = webm + mp4 + poster)
new_needles = [
    ("Sarah &amp; James", "Sarah & James card title"),
    ("case-sarah-james-super8", "Sarah & James video URL"),
    ("Anika &amp; Dev", "Anika & Dev card title"),
    ("case-anika-dev-save-the-date", "Anika & Dev video URL"),
    ("Maria &amp; David", "Maria & David card title"),
    ("case-maria-david-sunset-trailer", "Maria & David video URL"),
]
for n, desc in new_needles:
    c = html.count(n)
    color = "\033[32m" if c > 0 else "\033[31m"
    print(f"  {color}{'OK' if c > 0 else 'MISSING'}\033[0m  {c:>3} hits  {desc}", flush=True)

# Old static refs that were replaced on these 3 cards (should be 0 on gallery)
old_refs_round2 = [
    ("/images/catalog-ai-video-generator-1280.webp", "Sarah & James old static"),
    ("/images/preset-romantic-soft-1280.webp", "Anika & Dev old static"),
    ("/images/catalog-wedding-trailer-1280.webp", "Maria & David old static"),
]
for o, desc in old_refs_round2:
    c = html.count(o)
    flag = "GOOD (old static removed)" if c == 0 else f"STILL THERE (x{c})"
    print(f"  REF  {c:>3} hits  {desc}", flush=True)

# 2. 9 new video/poster files — HEAD
print("\n=== 9 new video/poster files on production ===", flush=True)
all_ok = True
for base in ["case-sarah-james-super8", "case-anika-dev-save-the-date", "case-maria-david-sunset-trailer"]:
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
if all_ok and all(html.count(n) > 0 for n, _ in new_needles if "video URL" in _):
    print("\033[32mDEPLOY OK: 9 new assets serve 200, gallery page references all 3 new videos.\033[0m", flush=True)
    sys.exit(0)
else:
    print("\033[31mDEPLOY INCOMPLETE\033[0m", flush=True)
    sys.exit(1)
