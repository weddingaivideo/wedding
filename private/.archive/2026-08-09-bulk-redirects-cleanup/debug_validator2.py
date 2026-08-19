"""Replicate validator exactly, with debug prints."""
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
print(f"DEBUG ROOT: {ROOT}", file=sys.stderr)
print(f"DEBUG ROOT exists: {ROOT.exists()}", file=sys.stderr)
print(f"DEBUG ROOT/images exists: {(ROOT / 'images').exists()}", file=sys.stderr)

HTML = (ROOT / "gallery" / "index.html").read_text(encoding="utf-8")
print(f"DEBUG HTML length: {len(HTML)}", file=sys.stderr)

all_refs = set()
for m in re.findall(r'<img\s[^>]*src="([^"]+)"', HTML):
    all_refs.add(m)
for m in re.findall(r'<source\s[^>]*src="([^"]+)"', HTML):
    all_refs.add(m)
for m in re.findall(r'<video\s[^>]*poster="([^"]+)"', HTML):
    all_refs.add(m)
for m in re.findall(r'srcset="([^"]+)"', HTML):
    for part in m.split(","):
        url = part.strip().split()[0]
        if url:
            all_refs.add(url)

print(f"DEBUG all_refs total: {len(all_refs)}", file=sys.stderr)

# Find one missing file and trace it
ahmed_mp4 = "/images/case-ahmed-layla-broadcast.mp4?v=4.29"
print(f"DEBUG ahmed mp4 in all_refs: {ahmed_mp4 in all_refs}", file=sys.stderr)
if ahmed_mp4 in all_refs:
    rel = ahmed_mp4.split("?", 1)[0].split("#", 1)[0].lstrip("/")
    fp = ROOT / rel
    print(f"DEBUG ahmed mp4 fp: {fp}", file=sys.stderr)
    print(f"DEBUG ahmed mp4 fp.exists(): {fp.exists()}", file=sys.stderr)
