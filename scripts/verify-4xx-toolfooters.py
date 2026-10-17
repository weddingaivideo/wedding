"""Verify the tool-footer 4xx cleanup removed every broken href target.

Companion to scripts/fix-4xx-inlinks-toolfooters.py. Exits non-zero if any
leftover broken inlinks are found anywhere under the project root (excluding
deploy / dependency / config dirs).

Run from project root:
    python scripts/verify-4xx-toolfooters.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(".")
SKIP = {".git", ".wrangler", "node_modules", "internal-tools", "private",
        "admin", "functions", "i18n", "config", "qa", "tmp", "__pycache__"}

# All bad href patterns combined into a single alternation. This lets us do
# ONE findall pass per file instead of 12 findall passes (12x faster on
# 700-file scan).
BAD_PATTERNS = [
    r"/services/wedding-trailer/?(?=[#\"\'\s?]|$)",
    r"/services/wedding-video/?(?=[#\"\'\s?]|$)",
    r"/services/family-tribute/?(?=[#\"\'\s?]|$)",
    r"/about-us/?(?=[#\"\'\s?]|$)",
    r"/contact/?(?=[#\"\'\s?]|$)",
    r"/blog/wedding-budget-breakdown-2026/?(?=[#\"\'\s?]|$)",
    r"/blog/average-wedding-cost-2026/?(?=[#\"\'\s?]|$)",
    r"/blog/wedding-vendor-payment-schedule/?(?=[#\"\'\s?]|$)",
    r"/blog/wedding-reception-timeline/?(?=[#\"\'\s?]|$)",
    r"/blog/wedding-seating-chart-ideas/?(?=[#\"\'\s?]|$)",
    r"/blog/best-wedding-photo-books-2026/?(?=[#\"\'\s?]|$)",
    r"/blog/wedding-photo-album-ideas/?(?=[#\"\'\s?]|$)",
]

# Anchored to href=" to skip path-in-text and path-in-srcset false positives.
HREF_RE = re.compile(
    r'href="[^"]*(?:' + "|".join(BAD_PATTERNS) + r')[^"]*"'
)

LABELS = {
    "/services/wedding-trailer/": "Category E",
    "/services/wedding-video/": "Category E",
    "/services/family-tribute/": "Category E",
    "/about-us/": "Category F",
    "/contact/": "Category G",
    "/blog/wedding-budget-breakdown-2026/": "Category H",
    "/blog/average-wedding-cost-2026/": "Category H",
    "/blog/wedding-vendor-payment-schedule/": "Category H",
    "/blog/wedding-reception-timeline/": "Category H",
    "/blog/wedding-seating-chart-ideas/": "Category J",
    "/blog/best-wedding-photo-books-2026/": "Category I",
    "/blog/wedding-photo-album-ideas/": "Category I",
}


def label_for(href: str) -> str:
    for path, label in LABELS.items():
        if path in href:
            return f"{label} ({path})"
    return "UNKNOWN"


def main() -> int:
    total = 0
    files_with_issues = 0
    issues_by_label: dict[str, list[tuple[Path, int]]] = {}

    html_files = [
        p for p in ROOT.rglob("*.html")
        if not (SKIP & set(p.parts))
    ]
    print(f"Scanning {len(html_files)} HTML files for leftover broken hrefs…")

    for p in html_files:
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:
            continue
        matches = HREF_RE.findall(t)
        if matches:
            total += len(matches)
            files_with_issues += 1
            for m in matches:
                print(f"  {p}  -- {label_for(m)}  -- {m[:120]}")
            issues_by_label.setdefault("mixed", []).append((p, len(matches)))

    print(f"\n{'=' * 60}")
    print(f"Total leftover broken href occurrences: {total}")
    print(f"Files with issues: {files_with_issues}")
    if total == 0:
        print("CLEAN — every bad inlink was rewritten by "
              "fix-4xx-inlinks-toolfooters.py")
        return 0
    print("\nBreakdown:")
    for path, hits in issues_by_label.items():
        files = sum(n for _, n in hits)
        print(f"  {files:3d}  {path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
