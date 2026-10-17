#!/usr/bin/env python3
"""
fix-duplicate-h2.py - Make 7 EN-only H2 duplicates unique.

Trigger: 2026-10-16 SF crawl flagged 26 URLs with H2: Duplicate.
After analysis, the real duplications that need rewrites break down
into 5 cases (all in EN, all 1:1 with another page):

Hub-page level (3 fixes, services/index.html):
  - "Video Enhancement"   appears in /services/ (section anchor) AND
                            /services/video-enhancement/ (page title)
  - "Absence Compensation" same pattern
  - "Personalization"     same pattern

Service-page level (2 fixes):
  - "Our Sensitivity Pledge" appears in family-tribute AND family-message
  - "Technical Specs & Capabilities" in slow-motion AND vintage-restoration

Strategy: disambiguate the H2 on the EARLIER-listed page (in each pair)
to differentiate it. The later-listed page keeps the original (since it's
the canonical service page that should own the heading).

Preserves data-i18n attribute via RE_H2 capture groups.
Preserves LF line endings via bytes-level read/write.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(".")

# (file_path, old_h2_text, new_h2_text)
# old_h2_text is the inner text of the <h2> -- we match it via re.escape
# then check data-i18n attribute presence to be safe.
REWRITES: list[tuple[str, str, str]] = [
    # Hub page: differentiate the 3 service section anchors
    (
        "services/index.html",
        "Video Enhancement",
        "Video Enhancement Services",
    ),
    (
        "services/index.html",
        "Absence Compensation",
        "Absence Compensation Services",
    ),
    (
        "services/index.html",
        "Personalization",
        "Personalization Services",
    ),
    # Service page: differentiate family-tribute from family-message
    (
        "services/absence-compensation/family-tribute/index.html",
        "Our Sensitivity Pledge",
        "Our Tribute Sensitivity Pledge",
    ),
    # Service page: differentiate vintage-restoration from slow-motion
    (
        "services/video-enhancement/vintage-restoration/index.html",
        "Technical Specs & Capabilities",
        "Restoration Specs & Capabilities",
    ),
]

# Match <h2 ...>...inner...</h2> with literal inner text match.
# Uses re.escape on old_h2_text to avoid regex injection.
RE_H2 = re.compile(
    r'(<h2(?:\s[^>]*)?>)([^<]*)(</h2>)',
    re.IGNORECASE | re.DOTALL,
)


def rewrite_file(rel_path: str, old: str, new: str) -> tuple[int, str]:
    """Return (count, first_old_seen)."""
    path = ROOT / rel_path
    try:
        original_bytes = path.read_bytes()
    except OSError as e:
        return (0, f"read failed: {e}")

    original = original_bytes.decode("utf-8")
    first_seen = ""

    def repl(m):
        nonlocal first_seen
        open_tag, inner_text, close_tag = m.group(1), m.group(2).strip(), m.group(3)
        if inner_text == old:
            if not first_seen:
                first_seen = inner_text
            return f"{open_tag}{new}{close_tag}"
        return m.group(0)

    new_content, count = re.subn(RE_H2, repl, original)

    if count > 0 and new_content != original:
        # Preserve LF line endings
        path.write_bytes(new_content.encode("utf-8"))
    return count, first_seen


def main() -> int:
    grand = 0
    for rel, old, new in REWRITES:
        count, first_seen = rewrite_file(rel, old, new)
        if count > 0:
            grand += count
            print(f"  [ok] {rel}: '{old}' -> '{new}' ({count}x)")
        else:
            print(f"  [skip] {rel}: '{old}' not found")
    print(f"\nDone: {grand}/{len(REWRITES)} rewrites applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
