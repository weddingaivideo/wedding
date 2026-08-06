"""Find all og:url lines and check for trailing slash / stray quote issues."""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
files = list(ROOT.rglob("*.html"))
files = [f for f in files if "qa" not in f.parts and "tmp" not in f.parts and "internal-tools" not in f.parts and "admin" not in f.parts]

print("=== Stray quote in og:url ===")
for f in files:
    text = f.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r'<meta\s+property="og:url"\s+content="([^"]*)"([^>]*)>', text):
        url = m.group(1)
        after = m.group(2)
        # Check for stray quote (closing `"` followed by something other than `>`)
        if after and not after.startswith(">"):
            # possibly a stray quote issue
            if '"' in after or url.endswith('"'):
                rel = f.relative_to(ROOT)
                print(f"  {rel}: content=\"{url}\" after=\"{after}\"")

print()
print("=== og:url missing trailing slash ===")
for f in files:
    text = f.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r'<meta\s+property="og:url"\s+content="(https://weddingai\.video/[^"?#]+)"\s*>', text):
        url = m.group(1)
        # Skip if URL ends with .xml, .png, etc. (none of our og:url do)
        if not url.endswith("/") and "/" in url[len("https://weddingai.video/"):]:
            rel = f.relative_to(ROOT)
            print(f"  {rel}: {url}")
