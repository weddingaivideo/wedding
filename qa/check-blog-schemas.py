#!/usr/bin/env python3
"""Quick post-script sanity check: every blog post should have both
Article and BreadcrumbList JSON-LD schemas."""
import re
from pathlib import Path

root = Path(".")
LANGS = {"zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"}

posts = []
en_blog = root / "blog"
if en_blog.is_dir():
    for sd in en_blog.iterdir():
        if sd.is_dir() and (sd / "index.html").is_file():
            posts.append(sd / "index.html")
for lang in LANGS:
    lang_blog = root / lang / "blog"
    if not lang_blog.is_dir():
        continue
    for sd in lang_blog.iterdir():
        if sd.is_dir() and (sd / "index.html").is_file():
            posts.append(sd / "index.html")

print(f"Total posts: {len(posts)}")
ok_both = missing_a = missing_b = empty = 0
for p in posts:
    txt = p.read_text(encoding="utf-8", errors="replace")
    if not txt.strip():
        empty += 1
        continue
    has_a = bool(re.search(r'"@type"\s*:\s*"Article"', txt))
    has_b = bool(re.search(r'"@type"\s*:\s*"BreadcrumbList"', txt))
    if has_a and has_b:
        ok_both += 1
    elif not has_a:
        missing_a += 1
    elif not has_b:
        missing_b += 1

print(f"With both Article+BreadcrumbList: {ok_both}")
print(f"Empty files: {empty}")
print(f"Missing Article only: {missing_a}")
print(f"Missing BreadcrumbList only: {missing_b}")
