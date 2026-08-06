"""Re-check og:url status after the fix."""
import re
from pathlib import Path
ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
files = list(ROOT.rglob("*.html"))
files = [f for f in files if "qa" not in f.parts and "tmp" not in f.parts and "internal-tools" not in f.parts and "admin" not in f.parts]

# Check success
succ = ROOT / "success" / "index.html"
text = succ.read_text(encoding="utf-8")
m = re.search(r'<meta\s+property="og:url"\s+content="([^"]+)"', text)
print(f"success og:url: {m.group(1) if m else 'NOT FOUND'}")
print()

# Re-check stray quote issues
print("=== Re-check stray quote issues ===")
broken = 0
for f in files:
    text = f.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r'<meta\s+property="og:url"\s+content="([^"]*)"([^>]*)>', text):
        url = m.group(1)
        after = m.group(2)
        # Normal close is ">" or "/>"
        if after and after not in (">", "/>"):
            rel = f.relative_to(ROOT)
            print(f"  STILL BROKEN: {rel}: content=\"{url}\" after=\"{after}\"")
            broken += 1
print(f"Total broken: {broken}")
print()

# Also check missing trailing slash
print("=== Missing trailing slash ===")
missing = 0
for f in files:
    text = f.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r'<meta\s+property="og:url"\s+content="(https://weddingai\.video/[^"?#]+)"\s*/?>', text):
        url = m.group(1)
        if not url.endswith("/") and "/" in url[len("https://weddingai.video/"):]:
            rel = f.relative_to(ROOT)
            print(f"  {rel}: {url}")
            missing += 1
print(f"Total missing trailing slash: {missing}")
