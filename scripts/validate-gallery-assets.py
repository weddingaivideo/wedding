#!/usr/bin/env python3
"""Validate that all assets referenced in the gallery HTML exist on disk."""
import os
import re, sys
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
HTML = (ROOT / "gallery" / "index.html").read_text(encoding="utf-8")

# Match both <img src> and <source src=...> and <source srcset=...> and <video poster>
referenced = set()
referenced.update(re.findall(r'<img\s[^>]*src="([^"]+)"', HTML))
referenced.update(re.findall(r'<source\s[^>]*src="([^"]+)"', HTML))
referenced.update(re.findall(r'<video\s[^>]*poster="([^"]+)"', HTML))
referenced.update(re.findall(r'srcset="([^"]+)"', HTML))

# Also catch source srcset (e.g. <source srcset="...avif 360w, ..."> used in picture)
all_refs = set()
for m in re.findall(r'srcset="([^"]+)"', HTML):
    # parse "url 360w, url2 720w" -> just take urls
    for part in m.split(","):
        url = part.strip().split()[0]
        all_refs.add(url)
for m in re.findall(r'<img\s[^>]*src="([^"]+)"', HTML):
    all_refs.add(m)
for m in re.findall(r'<source\s[^>]*src="([^"]+)"', HTML):
    all_refs.add(m)
for m in re.findall(r'<video\s[^>]*poster="([^"]+)"', HTML):
    all_refs.add(m)

missing = []
ok = []
for url in sorted(all_refs):
    if not url.startswith("/images/"):
        continue
    rel = url.lstrip("/")
    fp = ROOT / rel
    if fp.exists():
        ok.append(url)
    else:
        missing.append(url)

print(f"OK: {len(ok)}")
print(f"MISSING: {len(missing)}")
for m in missing:
    print(f"  MISSING: {m}")
sys.exit(1 if missing else 0)
