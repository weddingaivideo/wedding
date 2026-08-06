#!/usr/bin/env python3
"""Fix og:image WebP → JPEG across all live HTML files.

Audit finding 2026-08-04: og:image WebP causes fallback to generic icon on
Facebook, LinkedIn, and other social scrapers that don't decode WebP.

Approach:
  1. Find all live HTML files (skip tmp/_pre_restore_backup folders).
  2. For each file with og:image ending in .webp AND og:image:type="image/webp"
     within ~500 chars after, change .webp → .jpg and image/webp → image/jpeg.
  3. Only touch the og:image (NOT hero poster, etc.).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Skip these folders (backups + tooling).
SKIP_PARTS = {
    "_pre_restore_backup",
    "tmp",
    "__pycache__",
    "node_modules",
    ".git",
    ".wrangler",
    "tools",
    "internal-tools",
    "scripts",
}

# Match the og:image meta + og:image:type meta within 500 chars after.
WEBP_OG_RE = re.compile(
    r'(<meta\s+property="og:image"\s+content="[^"]+\.webp"[^>]*>)'
    r'([\s\S]{0,500}?)'
    r'(<meta\s+property="og:image:type"\s+content="image/webp"[^>]*>)',
    re.IGNORECASE,
)


def is_live_file(p: Path) -> bool:
    parts = set(p.relative_to(ROOT).parts)
    return not (parts & SKIP_PARTS)


def fix_one(p: Path) -> bool:
    text = p.read_text(encoding="utf-8")
    if not WEBP_OG_RE.search(text):
        return False
    new = WEBP_OG_RE.sub(
        lambda m: m.group(1).replace(".webp", ".jpg")
        + m.group(2)
        + m.group(3).replace("image/webp", "image/jpeg"),
        text,
    )
    if new == text:
        return False
    p.write_text(new, encoding="utf-8")
    return True


def main():
    htmls = [p for p in ROOT.rglob("*.html") if is_live_file(p)]
    changed = [p for p in htmls if fix_one(p)]
    print(f"Scanned {len(htmls)} live HTML files.")
    print(f"Updated {len(changed)} files:")
    for p in changed:
        try:
            rel = p.relative_to(ROOT)
        except ValueError:
            rel = p
        print(f"  {rel}")
    return 0 if len(changed) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
