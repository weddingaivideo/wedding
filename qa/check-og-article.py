"""Quick check: are og:article:* tags now in blog posts?"""
import re
from pathlib import Path

samples = [
    "blog/restore-vhs-wedding-footage/index.html",
    "blog/affordable-wedding-video-ai/index.html",
    "zh/blog/restore-vhs-wedding-footage/index.html",
    "ja/blog/restore-vhs-wedding-footage/index.html",
]

OG_META = re.compile(r'<meta\s+property="(og:[^"]+)"[^>]*content="([^"]*)"')
OG_TITLE = re.compile(r'<meta\s+property="og:title"[^>]*content="([^"]*)"')

for s in samples:
    p = Path(s)
    text = p.read_text(encoding="utf-8")
    print(f"{s}:")
    matches = OG_META.findall(text)
    if not matches:
        print("  (no og: meta tags)")
    for k, v in matches:
        v_disp = v[:80] + "..." if len(v) > 80 else v
        print(f"  {k:30s} = {v_disp}")
    print()
