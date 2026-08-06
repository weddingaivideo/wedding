#!/usr/bin/env python3
"""Find any remaining og:image WebP references (after the JPEG migration)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {"_pre_restore_backup", "tmp", "__pycache__", "node_modules", ".git", ".wrangler", "tools", "internal-tools", "scripts"}
OG_RE = re.compile(r'og:image"?\s+content="([^"]+)"', re.IGNORECASE)
OG_URL_RE = re.compile(r'og:image:url"?\s+content="([^"]+)"', re.IGNORECASE)


def is_live(p: Path) -> bool:
    return not (set(p.relative_to(ROOT).parts) & SKIP_PARTS)


def main():
    issues = 0
    for p in ROOT.rglob("*.html"):
        if not is_live(p):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in OG_RE.findall(text) + OG_URL_RE.findall(text):
            if ".webp" in m and "/hero-" not in m and "/og-" not in m:
                # Skip references that point to hero video poster
                print(f"WARN {p.relative_to(ROOT)} -> {m}")
                issues += 1
    print(f"Remaining non-hero WebP og:image: {issues}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
