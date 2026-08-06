"""
Fix all relative-path bugs in service pages.

Two bug categories fixed:
1. <link rel="icon" href="../../../favicon.svg"> in depth-2 service pages
   should be ../../favicon.svg
2. <img src="../../images/foo.jpeg"> in services/index.html (depth 1)
   should be ../images/foo.jpeg
3. <a href="../../privacy.html"> / ../../terms.html may have wrong depth

Strategy: for each HTML file, compute its depth from project root, then
rebuild every relative path that should be a sibling of the file's dir.
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
files = list(ROOT.rglob("*.html"))
files = [p for p in files if p.name != "google-site-verification.html"]

# Patterns we need to rewrite
REWRITES = [
    # <link rel="icon" type="image/svg+xml" href="...">favicon.svg
    (re.compile(r'(<link\s+rel="icon"[^>]*href=")(?:\.\./)+favicon\.svg(")'),
     lambda m, prefix: m.group(1) + prefix + "favicon.svg" + m.group(2)),
    # <a href=".../privacy.html">
    (re.compile(r'(href=")(?:\.\./)+privacy\.html(")'),
     lambda m, prefix: m.group(1) + prefix + "privacy.html" + m.group(2)),
    # <a href=".../terms.html">
    (re.compile(r'(href=")(?:\.\./)+terms\.html(")'),
     lambda m, prefix: m.group(1) + prefix + "terms.html" + m.group(2)),
    # <img src=".../images/foo.{jpg,png,jpeg,webp,avif}">  (for ANY ../ depth)
    (re.compile(r'(<img\s+[^>]*src=")(?:\.\./)+images/'),
     lambda m, prefix: m.group(1) + prefix + "images/"),
    # <source srcset=".../images/...">  (for any depth)
    (re.compile(r'(<source\s+[^>]*srcset=")(?:\.\./)+images/'),
     lambda m, prefix: m.group(1) + prefix + "images/"),
]

def file_depth(p: Path) -> int:
    rel = str(p.relative_to(ROOT))
    if rel == p.name:  # root file
        return 0
    # depth = number of directory components
    return rel.count("\\") + rel.count("/")

def correct_prefix(depth: int) -> str:
    if depth == 0:
        return ""
    return "../" * depth

n = 0
for f in sorted(files):
    depth = file_depth(f)
    prefix = correct_prefix(depth)
    text = f.read_text(encoding="utf-8")
    original = text
    for pat, repl in REWRITES:
        text = pat.sub(lambda m, r=repl, p=prefix: r(m, p), text)
    if text != original:
        f.write_text(text, encoding="utf-8")
        n += 1
        print(f"[fixed] {f.relative_to(ROOT)} (depth={depth}, prefix='{prefix}')")

print(f"\nDone. {n} file(s) fixed")
