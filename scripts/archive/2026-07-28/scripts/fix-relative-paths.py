#!/usr/bin/env python3
"""Fix all relative <script src> paths to absolute (handle ../../, ../, etc.)"""
import re
from pathlib import Path
ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
# Match any src="..." that doesn't start with /, http://, https://, or #
RX = re.compile(r'src="((?:\.\./|\./|)(?:js|css)/[^"]+)"')
# Build absolute replacement
def to_absolute(rel: str) -> str:
    if rel.startswith("/"):
        return rel
    # Compute absolute path from root
    # rel like "../../js/main.min.js?v=3.18"
    parts = rel.split("/")
    # Pop while parts start with ../
    while parts and parts[0] in (".", ".."):
        parts.pop(0)
    return "/" + "/".join(parts)
count = 0
for p in ROOT.rglob("*.html"):
    if any(seg in p.parts for seg in ("i18n", "qa", "tmp")):
        continue
    raw = p.read_text(encoding="utf-8")
    matches = list(RX.finditer(raw))
    if not matches:
        continue
    new = raw
    for m in matches:
        old_rel = m.group(1)
        new_rel = to_absolute(old_rel)
        new = new.replace(f'src="{old_rel}"', f'src="{new_rel}"', 1)
    if new != raw:
        p.write_text(new, encoding="utf-8", newline="")
        count += 1
print(f"Fixed {count} files")
