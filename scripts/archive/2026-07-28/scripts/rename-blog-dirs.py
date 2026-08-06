#!/usr/bin/env python3
"""
Phase 1: Rename /blog/NN-xxx/ directories to /blog/<semantic-slug>/.
Phase 2: Scan all HTML files for references to old paths and rewrite to new paths.
Phase 3: Add 301 redirects to _redirects.
"""
import csv
import re
import shutil
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
BLOG = ROOT / "blog"

# Load mapping from CSV written by analyze_blog_slugs.py
MAP = {}
with (ROOT / "blog_slug_map.csv").open(encoding="utf-8", newline="") as f:
    r = csv.DictReader(f)
    for row in r:
        MAP[row["old_slug"]] = row["new_slug"]

print(f"=== Phase 1: Rename {len(MAP)} blog directories ===")
renamed = 0
for old_slug, new_slug in MAP.items():
    src = BLOG / old_slug
    dst = BLOG / new_slug
    if not src.exists():
        print(f"  SKIP (not found): {old_slug}")
        continue
    if dst.exists():
        print(f"  SKIP (target exists): {new_slug}")
        continue
    shutil.move(str(src), str(dst))
    renamed += 1
    if renamed <= 5 or renamed % 10 == 0:
        print(f"  {old_slug:50s} -> {new_slug}")
print(f"\nRenamed: {renamed}/{len(MAP)}\n")

print(f"=== Phase 2: Rewrite old URL references in all HTML files ===")
HTML_GLOB = list(ROOT.rglob("*.html"))
HTML_GLOB = [p for p in HTML_GLOB if not any(seg in p.parts for seg in ("i18n", "qa", "tmp"))]

# Pattern: any reference to /blog/NN-xxx/ or /blog/NN-xxx (no trailing slash)
RX = re.compile(r"/blog/(\d{2}-[a-z0-9-]+)")

total_rewrites = 0
files_touched = 0
for p in HTML_GLOB:
    raw = p.read_text(encoding="utf-8")
    matches = list(RX.finditer(raw))
    if not matches:
        continue
    rewrites_in_file = [0]  # mutable container for closure

    def repl(m, counter=rewrites_in_file):
        old_slug = m.group(1)
        if old_slug in MAP:
            counter[0] += 1
            return f"/blog/{MAP[old_slug]}"
        return m.group(0)

    new = RX.sub(repl, raw)
    if new != raw:
        p.write_text(new, encoding="utf-8", newline="")
        files_touched += 1
        total_rewrites += rewrites_in_file[0]
        if files_touched <= 5:
            print(f"  {p.relative_to(ROOT)}: {rewrites_in_file[0]} rewrites")

print(f"\n  Files touched: {files_touched}")
print(f"  Total URL rewrites: {total_rewrites}\n")

print(f"=== Phase 3: Add 301 redirects to _redirects ===")
REDIRECTS = ROOT / "_redirects"
existing = REDIRECTS.read_text(encoding="utf-8") if REDIRECTS.exists() else ""

# Build new redirect lines (sorted for stable order)
new_lines = []
for old_slug, new_slug in sorted(MAP.items()):
    line = f"/blog/{old_slug}/  /blog/{new_slug}/  301"
    if line not in existing:
        new_lines.append(line)

# Add a section comment
if new_lines:
    block = (
        "\n\n# === Blog 01-50 -> semantic-slug migration (auto-generated) ===\n"
        + "\n".join(new_lines)
        + "\n"
    )
    with REDIRECTS.open("a", encoding="utf-8", newline="") as f:
        f.write(block)
    print(f"  Added {len(new_lines)} redirect rules to _redirects")
else:
    print(f"  _redirects already has all 50 blog redirects")

print("\n=== Done ===")
