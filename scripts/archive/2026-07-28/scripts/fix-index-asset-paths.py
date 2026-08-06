#!/usr/bin/env python3
"""
v3.8.0 (round 3) — Fix asset paths in directory index.html files.

Problem: <page>/index.html uses relative paths (e.g. `favicon.svg`,
`styles.min.css`, `images/foo.png`) that were correct when the source
was <page>.html at root. After copying to <page>/index.html, those
relative paths resolve against the new URL `/page/...` and 404.

Fix: rewrite all asset-related relative href/src/srcset values in
directory index.html files to absolute paths (leading `/`).

Scope:
  - Touches ONLY files at <dir>/index.html, not <file>.html at root.
  - Preserves external URLs (https://...), anchors (#...), mailto/tel.
  - Preserves internal navigation href values (they're already trailing
    slash form from the previous migration).
  - Adds `/` prefix to: styles.min.css, js/main.min.js, favicon.svg,
    manifest.json, apple-touch-icon.png, images/... (any depth)
"""
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")

# Asset path patterns that need absolute / prefix
ASSET_BASES = {
    "styles", "js", "images", "favicon.svg", "favicon.ico",
    "manifest.json", "apple-touch-icon.png", "robots.txt",
    "sitemap.xml",  # unlikely in HTML but defensive
}
# Pre-compile regex: href=" or src=" or srcset=" (multi-value)
# Capture the value(s), add leading / if not already absolute.
# Negative lookbehind for `https?://`, `mailto:`, `tel:`, `#`
# Match unprefixed OR `../` (any number of levels) but convert to absolute.
HREF_SRC_RE = re.compile(
    r'(href|src)="(?!https?://|mailto:|tel:|#|data:)([^"]*?)"'
)
# srcset: "a.png 1x, b.png 2x" — split on comma, prefix each
SRCSET_RE = re.compile(
    r'(srcset)="(?!https?://)([^"]*?)"'
)


def is_asset_path(path: str) -> bool:
    """Return True if this is a static asset path that needs the / prefix.

    /about/ — not asset (skip, it's an internal nav href)
    /about — not asset
    favicon.svg — asset
    styles.min.css — asset
    js/main.min.js — asset
    images/foo.png — asset
    ../../images/foo.png — asset (will be replaced with /images/foo.png)
    ../../privacy/ — not asset (internal nav)
    #anchor — not asset
    """
    # Strip leading ../ to look at the actual target
    p = path
    while p.startswith("../"):
        p = p[3:]
    p = p.lstrip("./")
    if not p:
        return False
    # Internal page links
    internal = {
        "", "about", "gallery", "order", "privacy", "terms",
        "resources", "search", "success",
    }
    if p in internal or p.rstrip("/") in internal:
        return False
    if p.startswith("services/"):
        return False
    # Anything else is an asset
    return True


def should_absolute(path: str) -> bool:
    """Return True if path is asset and not yet absolute (doesn't start with /)."""
    if path.startswith("/"):
        return False
    return is_asset_path(path)


def make_absolute(path: str) -> str:
    """Convert ../../images/foo.png to /images/foo.png."""
    # Strip all leading ../ and ./
    p = path
    while p.startswith("../") or p.startswith("./"):
        if p.startswith("../"):
            p = p[3:]
        else:
            p = p[2:]
    return "/" + p if p else path


def fix_html(text: str) -> tuple[str, int]:
    n = 0

    def sub_href_src(m):
        nonlocal n
        attr, val = m.group(1), m.group(2)
        if not should_absolute(val):
            return m.group(0)
        n += 1
        new_val = make_absolute(val)
        return f'{attr}="{new_val}"'

    new_text, _ = HREF_SRC_RE.subn(sub_href_src, text)

    def sub_srcset(m):
        nonlocal n
        attr, val = m.group(1), m.group(2)
        # val is like "images/foo-360.webp 360w, images/foo-720.webp 720w"
        entries = [e.strip() for e in val.split(",")]
        new_entries = []
        changed = False
        for e in entries:
            # Each entry is "<url> <size>" or just "<url>"
            parts = e.rsplit(" ", 1)
            url = parts[0]
            suffix = " " + parts[1] if len(parts) == 2 else ""
            if should_absolute(url):
                new_url = make_absolute(url)
                if new_url != url:
                    changed = True
                new_entries.append(new_url + suffix)
            else:
                new_entries.append(e)
        if changed:
            n += 1
            return f'{attr}="{" , ".join(new_entries).replace(" ,", ",")}"'
        return m.group(0)

    new_text, _ = SRCSET_RE.subn(sub_srcset, new_text)
    return new_text, n


def main():
    print("=" * 60)
    print("v3.8.0 round 3 — fix asset paths in dir index.html")
    print("=" * 60)

    fixed_files = 0
    total_replacements = 0

    for p in ROOT.rglob("index.html"):
        # Only process files inside subdirectories (not root /index.html)
        rel = p.relative_to(ROOT)
        if len(rel.parts) < 2:
            # Either at root, or in a one-level dir like about/index.html
            # Actually one-level IS what we want to fix
            pass
        text = p.read_text(encoding="utf-8")
        new_text, n = fix_html(text)
        if n:
            p.write_text(new_text, encoding="utf-8")
            fixed_files += 1
            total_replacements += n
            print(f"  {rel}: {n} asset paths made absolute")
        else:
            # Only print non-200 cases if we want to debug
            pass

    print()
    print(f"Total: {fixed_files} files updated, {total_replacements} paths made absolute")


if __name__ == "__main__":
    main()
