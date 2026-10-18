"""Show raw JSON-LD for one file so we can see exact bug pattern."""
import re
from pathlib import Path

p = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai/ar/tools/wedding-photo-book-planner/index.html")
text = p.read_text(encoding="utf-8", errors="ignore")
m = re.search(r'<script type="application/ld\+json">(.+?)</script>', text, re.DOTALL)
if m:
    raw = m.group(1)
    print("=== first 1000 chars of JSON-LD ===")
    print(raw[:1000])
    print("=== keys with 'name' in it ===")
    for m2 in re.finditer(r'"name"\s*:\s*"[^"]*"', raw):
        print(repr(m2.group(0)[:200]))
