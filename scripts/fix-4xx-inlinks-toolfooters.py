#!/usr/bin/env python3
"""
fix-4xx-inlinks-toolfooters.py — One-shot script for the 2026-10-16 Screaming Frog
tool-footer 4xx cleanup.

For every (broken_path, correct_path) pair below, rewrites all `href="..."`
occurrences in every HTML file under the project root to point at the correct
path. The 12 broken URLs all come from the tool-pages footer / related-card
sections — the canonical URLs exist but the tool pages still link to the old
short forms.

Affected tool pages (11 langs each):
  - tools/wedding-budget-calculator/index.html        (5 hrefs each)
  - tools/wedding-seating-chart-maker/index.html      (5 hrefs each)
  - tools/wedding-photo-book-planner/index.html       (5 hrefs each)
  - tools/wedding-invitation-maker/index.html         (1 href: /contact/)
  - tools/wedding-hashtag-generator/index.html        (1 href: /contact/)
  - tools/save-the-date-maker/index.html              (1 href: /contact/)
  - tools/wedding-video-invitation-maker/index.html   (1 href: /contact/)

Belt-and-suspenders 301 redirects for the broken paths are added separately to
`_redirects` (12 EN + 12 × 10 lang = 132 entries), so external links / old social
shares / sitemap entries still resolve to a 200 OK page.

Run from project root:
    python scripts/fix-4xx-inlinks-toolfooters.py

The script is idempotent: re-running it on an already-fixed tree is a no-op
(zero replacements reported) because all broken patterns are gone.

Categorization (per Screaming Frog 2026-10-16 20:28 crawl):

  Category E — service-level footer links to short (non-canonical) slugs.
    The site reorganized /services/ into a 3-bucket taxonomy
    (personalization / absence-compensation / video-enhancement) on
    2026-08-04, but the tool-page footer templates still used the old
    flat slugs. These 4 entries fix that.

  Category F — /about-us/  →  /about/.
    Old blog/SEO convention. /about/ is the canonical since 2023.

  Category G — /contact/  →  /order/.
    The site has no /contact/ page — the order form IS the contact entry
    point (24-hour response, free sample, no-obligation). Confirmed by
    user 2026-10-16: 1 认可.

  Category H — blog-level 4xx from removed posts.
    Seven old /blog/ posts were removed in earlier consolidations. Their
    inbound links from the budget calculator / seating chart maker /
    photo book planner footer "related" cards still point at the deleted
    URLs. Each redirects to the closest semantic neighbor or the parent hub.

  Category I — /blog/<old-slug>  →  /tools/<active-tool>/.
    Same as H, but for posts whose content now lives as an active tool.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(".")

# Files we never touch (deploy artifacts, dependencies, source markdown).
SKIP_DIRS = {
    ".git", ".wrangler", "node_modules", "100 blog", "internal-tools",
    "private", "admin", "functions", "i18n", "config", "qa", "tmp",
    "__pycache__",
}

# (broken, correct) — every broken path is the URL the Screaming Frog crawl
# reported as 4xx; every correct path is a verified 200 OK target.
REPLACEMENTS: list[tuple[str, str]] = [
    # ---- Category E: flat service slugs (pre-taxonomy) -> canonical 3-bucket ----
    ("/services/wedding-trailer",
     "/services/personalization/wedding-trailer"),
    ("/services/wedding-video",
     "/services/personalization/ai-video-generator"),
    ("/services/family-tribute",
     "/services/absence-compensation/family-tribute"),

    # ---- Category F: legacy /about-us/ -> /about/ ----
    ("/about-us", "/about"),

    # ---- Category G: legacy /contact/ -> /order/ (user-confirmed 2026-10-16) ----
    ("/contact", "/order"),

    # ---- Category H: removed blog posts -> closest semantic neighbor ----
    ("/blog/wedding-budget-breakdown-2026",
     "/blog/wedding-video-cost-2026"),
    ("/blog/average-wedding-cost-2026",
     "/blog/wedding-video-cost-2026"),
    ("/blog/wedding-vendor-payment-schedule",
     "/blog/wedding-video-cost-2026"),
    ("/blog/wedding-reception-timeline",
     "/blog/wedding-video-timeline"),

    # ---- Category I: removed blog posts -> active tool page ----
    ("/blog/best-wedding-photo-books-2026",
     "/tools/wedding-photo-book-planner"),
    ("/blog/wedding-photo-album-ideas",
     "/tools/wedding-photo-book-planner"),

    # ---- Category J: no semantic equivalent -> blog hub ----
    # /blog/wedding-seating-chart-ideas/ has no replacement post; the tool
    # /tools/wedding-seating-chart-maker/ is a much closer match than the
    # generic blog hub (the user is looking for a seating-chart helper, not
    # blog articles). Use the tool.
    ("/blog/wedding-seating-chart-ideas",
     "/tools/wedding-seating-chart-maker"),
]

# Only rewrite inside href="..." attributes. We allow optional trailing slash
# (matches both /path and /path/), and preserve any subsequent character (")
# so we don't touch the attribute boundary. Anchor and query strings are
# uncommon on these particular inlinks (verified by hand-checking the crawl
# set), but the regex below would still leave them intact.
HREF_PATTERN = re.compile(r'href="({broken}/?)([^"]*)"')


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & SKIP_DIRS)


def rewrite_file(path: Path) -> tuple[int, list[tuple[str, str]]]:
    """Return (count, [(broken, correct) per replacement that fired])."""
    try:
        original = path.read_bytes().decode("utf-8")
    except (UnicodeDecodeError, OSError):
        return 0, []

    total = 0
    new = original
    fired: list[tuple[str, str]] = []
    for broken, correct in REPLACEMENTS:
        pat = HREF_PATTERN.pattern.format(broken=re.escape(broken))
        new, n = re.subn(
            pat, lambda m: f'href="{correct}/{m.group(2)}"', new
        )
        if n:
            total += n
            fired.append((broken, correct))

    if total > 0 and new != original:
        path.write_bytes(new.encode("utf-8"))
    return total, fired


def main() -> int:
    html_files = [
        p for p in ROOT.rglob("*.html")
        if not should_skip(p.relative_to(ROOT))
    ]
    print(f"Scanning {len(html_files)} HTML files for tool-footer 4xx inlinks…")
    grand_total = 0
    changed_files: list[tuple[Path, int]] = []
    by_pair: dict[tuple[str, str], int] = {}
    for f in html_files:
        n, fired = rewrite_file(f)
        if n:
            changed_files.append((f, n))
            grand_total += n
            for pair in fired:
                by_pair[pair] = by_pair.get(pair, 0) + 1
    print(
        f"\nReplaced {grand_total} href occurrences across "
        f"{len(changed_files)} files:"
    )
    for f, n in sorted(changed_files, key=lambda x: -x[1]):
        print(f"  {n:3d}  {f.as_posix()}")
    print("\nBy (broken -> correct) pair:")
    for (b, c), n in sorted(by_pair.items(), key=lambda x: -x[1]):
        print(f"  {n:3d}  {b}  ->  {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
