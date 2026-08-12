#!/usr/bin/env python3
"""Normalize i18n/*.json to LF line endings (per .gitattributes eol=lf).

This is a one-time fix for the pre-existing CRLF inconsistency. The
.gitattributes file mandates LF for *.json but the original files were
CRLF. Each `git add` then warns "CRLF will be replaced by LF the next
time Git touches it" because git's index stores LF but the working
tree has CRLF.

After running this script, working tree == git index == LF.
"""
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
I18N = ROOT / "i18n"

count = 0
total_saved = 0
for p in sorted(I18N.glob("*.json")):
    raw = p.read_bytes()
    if b"\r\n" not in raw:
        continue
    lf = raw.replace(b"\r\n", b"\n")
    p.write_bytes(lf)
    count += 1
    total_saved += len(raw) - len(lf)
    print(f"  {p.name}: {len(raw):,} → {len(lf):,} bytes (-{len(raw) - len(lf):,})")

print(f"\nNormalized {count} files, saved {total_saved:,} bytes")
