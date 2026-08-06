#!/usr/bin/env python3
"""
B1: Rename blog.NN-xxx namespace labels in i18n JSONs to blog.<new-slug> namespace.

For each language JSON, for each old/new slug mapping, rename:
  blog.01-restore-old-wedding-videos.X -> blog.restore-vhs-wedding-footage.X

For HTML files, do the same in:
  - data-i18n="..." attribute
  - data-i18n-attr="...:blog.01-xxx..." attribute

Then verify keys still match between HTML and JSON.
"""
import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
I18N = ROOT / "i18n"
MAPPING_PATH = ROOT / "scripts" / "blog-slug-mapping.json"

# Load old -> new slug mapping
MAP = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
print(f"Loaded {len(MAP)} slug mappings")

# Sort by length descending so longer slugs are replaced first (avoid partial matches)
SORTED_MAP = sorted(MAP.items(), key=lambda kv: -len(kv[0]))
print(f"Longest old slug: {SORTED_MAP[0][0]} ({len(SORTED_MAP[0][0])} chars)")

# ---------- Phase 1: Rename in JSON files ----------
print("\n=== Phase 1: Rename keys in 10 language JSONs ===")
total_renames_json = 0
files_json = 0
for path in sorted(I18N.glob("*.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    new_data = {}
    file_renames = 0
    for k, v in data.items():
        new_k = k
        for old, new in SORTED_MAP:
            if f"blog.{old}." in new_k:
                new_k = new_k.replace(f"blog.{old}.", f"blog.{new}.")
                file_renames += 1
        new_data[new_k] = v
    if file_renames:
        path.write_text(
            json.dumps(new_data, ensure_ascii=False, indent=1, separators=(",", ": ")),
            encoding="utf-8",
            newline="\n",
        )
        files_json += 1
        total_renames_json += file_renames
        print(f"  {path.name}: {file_renames} keys renamed")
print(f"  Total: {total_renames_json} keys renamed in {files_json} files")

# ---------- Phase 2: Rename in HTML data-i18n and data-i18n-attr attributes ----------
print("\n=== Phase 2: Rename data-i18n attrs in HTML files ===")
# Match just the slug namespace: blog.NN-xxx.
RX_DATA_I18N = re.compile(r'(data-i18n=")blog\.(0\d-[a-z0-9-]+)(\.)([^"]*)(")')
RX_DATA_I18N_ATTR = re.compile(r'(data-i18n-attr="[^"]*?)blog\.(0\d-[a-z0-9-]+)(\.)([^"]*?)(")')

# Pre-build lookup
SLUG_LOOKUP = {f"blog.{old}.": f"blog.{new}." for old, new in SORTED_MAP}

def rename_in_text(text: str) -> tuple[str, int]:
    n = 0
    # data-i18n="blog.0N-xxx.X"
    def repl_i18n(m):
        nonlocal n
        prefix, old_slug, dot, rest, quote = m.groups()
        full_old = f"blog.{old_slug}."
        if full_old in SLUG_LOOKUP:
            n += 1
            return f'{prefix}{SLUG_LOOKUP[full_old][:-1]}{dot}{rest}{quote}'
        return m.group(0)
    text = RX_DATA_I18N.sub(repl_i18n, text)

    # data-i18n-attr="...:blog.0N-xxx.X"
    def repl_attr(m):
        nonlocal n
        prefix_part, old_slug, dot, rest, quote = m.groups()
        full_old = f"blog.{old_slug}."
        if full_old in SLUG_LOOKUP:
            n += 1
            new_part = f"{prefix_part}{SLUG_LOOKUP[full_old][:-1]}{dot}{rest}{quote}"
            return new_part
        return m.group(0)
    text = RX_DATA_I18N_ATTR.sub(repl_attr, text)
    return text, n

total_renames_html = 0
files_html = 0
html_targets = [p for p in ROOT.rglob("*.html") if not any(s in p.parts for s in ("i18n", "qa", "tmp"))]
for p in html_targets:
    raw = p.read_text(encoding="utf-8")
    new, n = rename_in_text(raw)
    if n:
        p.write_text(new, encoding="utf-8", newline="")
        files_html += 1
        total_renames_html += n
print(f"  Renamed {total_renames_html} attrs in {files_html} HTML files")

# ---------- Phase 3: Verify no stale references remain ----------
print("\n=== Phase 3: Verify no stale blog.0N- references ===")
stale_html = 0
for p in html_targets:
    raw = p.read_text(encoding="utf-8")
    if re.search(r'blog\.0\d-[a-z0-9-]+', raw):
        stale_html += 1
        print(f"  STALE: {p.relative_to(ROOT)}")
print(f"  Stale HTML refs: {stale_html}")

stale_json = 0
for path in sorted(I18N.glob("*.json")):
    raw = path.read_text(encoding="utf-8")
    if re.search(r'"blog\.0\d-[a-z0-9-]+', raw):
        stale_json += 1
        print(f"  STALE: {path.name}")
print(f"  Stale JSON keys: {stale_json}")

print(f"\n=== Summary ===")
print(f"  JSON keys renamed: {total_renames_json} in {files_json} files")
print(f"  HTML attrs renamed: {total_renames_html} in {files_html} files")
print(f"  Stale references: {stale_html} HTML + {stale_json} JSON")
