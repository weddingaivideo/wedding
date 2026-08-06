#!/usr/bin/env python3
"""Fix relative js/main.min.js to absolute /js/main.min.js"""
import re
from pathlib import Path
ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
RX = re.compile(r'src="(js/main\.min\.js[^"]*)"')
count = 0
for p in ROOT.rglob("*.html"):
    if any(seg in p.parts for seg in ("i18n", "qa", "tmp")):
        continue
    raw = p.read_text(encoding="utf-8")
    new = RX.sub(r'src="/\1"', raw)
    if new != raw:
        p.write_text(new, encoding="utf-8", newline="")
        count += 1
print(f"Fixed {count} main.min.js paths")
