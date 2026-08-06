import re
from pathlib import Path

f = Path("blog/01-restore-old-wedding-videos/index.html")
text = f.read_text(encoding="utf-8")
# Count all h1 in document
h1s = re.findall(r"<h1>([^<]+)</h1>", text)
print(f"Total <h1> in document: {len(h1s)}")
for h in h1s:
    print(f"  H1: {h[:80]}")

# Find first h1 in body section
m = re.search(r'<div class="blog-article"[^>]*>(.*)', text, re.DOTALL)
if m:
    body = m.group(1)
    for h in re.finditer(r"<h[12]>([^<]+)</h[12]>", body[:2000]):
        print(f"  body tag: {h.group(0)}")
