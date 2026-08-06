#!/usr/bin/env python3
"""
fix-4xx-inlinks.py — One-shot script for the 2026-08-04 Screaming Frog 4xx cleanup.

For every (broken_path, correct_path) pair below, rewrites all `href="..."` occurrences
in every HTML file under the project root to point at the correct path. Covers 9
languages (en / es / fr / de / ar / th / zh / ja / pt) since i18n reuses the same
inlink patterns.

Run from project root:
    python scripts/fix-4xx-inlinks.py

The script is idempotent: re-running it on an already-fixed tree is a no-op
(zero replacements reported) because all broken patterns are gone.
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
# reported as 4xx; every correct path is a verified 200 OK target. Belt-and-
# suspenders 301 redirects for the broken paths are added separately to
# `_redirects`, so external links / old social shares still resolve.
REPLACEMENTS: list[tuple[str, str]] = [
    # ---- Category A: root-level (missing /blog/) slugs ----
    ("/weddingai-video-guide",          "/blog/weddingai-video-guide"),
    ("/make-first-ai-wedding-video",    "/blog/make-first-ai-wedding-video"),
    ("/wedding-video-music-guide-new",  "/blog/wedding-video-music-guide-new"),
    ("/wedding-video-cost-2026-new",    "/blog/wedding-video-cost-2026-new"),
    ("/weddingai-video-case-studies",   "/blog/weddingai-video-case-studies"),
    ("/how-to-make-wedding-video",      "/blog/how-to-make-wedding-video"),
    ("/wedding-video-captions",         "/blog/wedding-video-captions"),
    ("/wedding-video-photo-checklist",  "/blog/wedding-video-photo-checklist"),
    ("/ai-editor-vs-traditional-editing", "/blog/ai-editor-vs-traditional-editing"),

    # ---- Category B: .md leakage from source markdown (preserve body but strip .md + add /blog/) ----
    ("/diy-wedding-video-phone.md",                "/blog/diy-wedding-video-phone"),
    ("/wedding-highlight-video.md",                "/blog/wedding-highlight-video"),
    ("/couple-slideshow-video.md",                 "/blog/couple-slideshow-video"),
    ("/wedding-video-trends-2026.md",              "/blog/wedding-video-trends-2026"),
    ("/ai-tools-for-photographers.md",             "/blog/ai-tools-for-photographers"),
    ("/photographer-upsell-video.md",              "/blog/photographer-upsell-video"),
    ("/ai-wont-replace-photographers.md",          "/blog/ai-wont-replace-photographers"),
    ("/wedding-slideshow-guide.md",                "/blog/wedding-slideshow-guide"),
    ("/bride-wedding-video-checklist.md",          "/blog/bride-wedding-video-checklist"),
    ("/destination-wedding-video-guide.md",       "/blog/destination-wedding-video"),  # slug also changes
    ("/wedding-video-without-videographer.md",     "/blog/wedding-video-without-videographer"),
    ("/small-wedding-video-ideas.md",              "/blog/micro-wedding-video"),          # slug also changes
    ("/wedding-package-video-upsell.md",           "/blog/photographer-upsell-video"),    # slug also changes
    ("/wedding-video-photo-checklist.md",          "/blog/wedding-video-photo-checklist"),
    # Edge case: es/blog/free-wedding-video-maker had `/blog/weddingai-video-guide/.md` —
    # the original .md was appended to the rewritten /blog/ path. Strip the trailing
    # .md and the leading /blog/ for a clean rewrite.
    ("/blog/weddingai-video-guide/.md",            "/blog/weddingai-video-guide"),

    # ---- Category C: wrong slug / real 404s ----
    ("/blog/destination-wedding-video-guide",  "/blog/destination-wedding-video"),
    ("/blog/wedding-video-under-500",          "/blog/wedding-video-cost-2026"),
    ("/blog/small-wedding-video-ideas",        "/blog/micro-wedding-video"),  # already has /blog/ prefix
    ("/blog/zh/small-wedding-video-ideas",     "/blog/micro-wedding-video"),  # /blog/zh/ bug in i18n
    ("/blog/wedding-package-video-upsell",     "/blog/photographer-upsell-video"),  # already has /blog/ prefix
    ("/small-wedding-video-ideas",             "/blog/micro-wedding-video"),
    ("/wedding-package-video-upsell",          "/blog/photographer-upsell-video"),

    # ---- Category D: missing service / sub-page ----
    ("/services/personalization/wedding-invitation",  "/services/personalization/multilingual"),
    # The ar blog wedding-wishes-video page links to /services/absence-compensation/ which
    # also has no index.html. We add an index.html for it (see scripts/generate-service-category-indexes.py),
    # so the inlink stays correct. No rewrite needed — the new file handles it.
]

# Only rewrite inside href="..." attributes. We allow optional trailing slash
# (matches both /path and /path/), and preserve any subsequent character (") so
# we don't touch the attribute boundary. Anchor and query strings are uncommon
# on these particular inlinks (verified by hand-checking the crawl set), but
# the regex below would still leave them intact.
HREF_PATTERN = re.compile(r'href="({broken}/?)([^"]*)"')


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & SKIP_DIRS)


def rewrite_file(path: Path) -> int:
    """Return count of href rewrites applied in this file."""
    try:
        original = path.read_bytes().decode("utf-8")
    except (UnicodeDecodeError, OSError):
        return 0

    total = 0
    new = original
    for broken, correct in REPLACEMENTS:
        # Regex form: href="<broken>/?<rest>"  →  href="<correct>/?<rest>"
        pat = HREF_PATTERN.pattern.format(broken=re.escape(broken))
        new, n = re.subn(pat, lambda m: f'href="{correct}/{m.group(2)}"', new)
        total += n
        # Also catch the exact-match form (no trailing slash, no anchor) so the
        # rewrite always ends with a canonical trailing slash. This is the
        # common form in this site.
        # HREF_PATTERN above already handles both via the optional /, so the
        # subn above is enough.

    if total > 0 and new != original:
        path.write_bytes(new.encode("utf-8"))
    return total


def main() -> int:
    html_files = [
        p for p in ROOT.rglob("*.html")
        if not should_skip(p.relative_to(ROOT))
    ]
    print(f"Scanning {len(html_files)} HTML files for bad inlinks…")
    grand_total = 0
    changed_files: list[tuple[Path, int]] = []
    for f in html_files:
        n = rewrite_file(f)
        if n:
            changed_files.append((f, n))
            grand_total += n
    print(f"\nReplaced {grand_total} href occurrences across {len(changed_files)} files:")
    for f, n in sorted(changed_files, key=lambda x: -x[1]):
        print(f"  {n:3d}  {f.as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
