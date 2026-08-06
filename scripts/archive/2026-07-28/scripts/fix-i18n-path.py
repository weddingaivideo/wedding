#!/usr/bin/env python3
"""
Fix: change all <script src="js/i18n.js?v=..."> to absolute path <script src="/js/i18n.js?v=...">
so that the i18n system doesn't break on /xx/<subdir>/ pages.

Reason: When a user has a non-English language cookie, the i18n.js redirects
to /xx/<subdir>/. The relative script src then resolves to /xx/<subdir>/js/i18n.js
which is a 404, so the i18n system fails and the nav text is never populated.
"""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
RX = re.compile(r'src="(js/i18n\.js[^"]*)"')

count = 0
files = 0
for p in ROOT.rglob("*.html"):
    if any(seg in p.parts for seg in ("i18n", "qa", "tmp")):
        continue
    raw = p.read_text(encoding="utf-8")
    new = RX.sub(r'src="/\1"', raw)
    if new != raw:
        p.write_text(new, encoding="utf-8", newline="")
        files += 1
        count += 1
        if files <= 3:
            print(f"  fixed: {p.relative_to(ROOT)}")
print(f"\nTotal: {count} scripts fixed in {files} files")
