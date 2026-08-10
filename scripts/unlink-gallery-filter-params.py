#!/usr/bin/env python3
"""
Unlink /gallery/?filter=xxx internal links from service pages.

Why: 11 service pages link to /gallery/?filter=<slug> from their hero "See
real examples" CTA. The gallery page does not read the filter from URL on
load, and the served HTML for any ?filter=... variant is identical to
/gallery/ — so each is a duplicate of the canonical /gallery/ in Google's
eyes. Search Console / Ahrefs flag the 11 URLs as "canonicalised to a
different URL" — warning is correct in that the canonical consolidation is
right (identical content), but the right fix is to stop creating the
parameter URLs internally. Once internal links are removed, Google will
eventually drop them from the index; the canonical on /gallery/ already
consolidates any residual link signals correctly.

Idempotent: re-running is a no-op. Detects the post-fix state (already
points to /gallery/) and skips.

Updates only the 11 EN source service pages. Localized variants are
generated at request time by functions/_middleware.js from these sources
— no per-language index.html exists under */services/.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 11 service pages identified by audit. Each has exactly one
# href="/gallery/?filter=<slug>" in the hero "See real examples" CTA.
SERVICE_FILES = [
    "services/video-enhancement/slow-motion/index.html",
    "services/video-enhancement/vintage-restoration/index.html",
    "services/personalization/ai-video-generator/index.html",
    "services/personalization/wedding-trailer/index.html",
    "services/personalization/pet-wedding/index.html",
    "services/personalization/multilingual/index.html",
    "services/personalization/cartoon-style/index.html",
    "services/personalization/meme-generator/index.html",
    "services/absence-compensation/family-tribute/index.html",
    "services/absence-compensation/family-message/index.html",
]

# Match href="/gallery/?filter=anything" — capture the filter value for
# reporting, replace the whole href with the canonical clean URL.
RE_FILTER_LINK = re.compile(r'href="/gallery/\?filter=([^"]+)"')
REPLACEMENT = 'href="/gallery/"'


def main() -> int:
    total_replaced = 0
    total_already_clean = 0
    total_unexpected = 0

    for rel in SERVICE_FILES:
        path = ROOT / rel
        if not path.exists():
            print(f"  MISSING  {rel}")
            total_unexpected += 1
            continue

        text = path.read_text(encoding="utf-8")
        matches = RE_FILTER_LINK.findall(text)
        if not matches:
            # Idempotent: no filter link present (already fixed, or pattern drifted).
            total_already_clean += 1
            print(f"  OK       {rel}  (no filter link)")
            continue

        if len(matches) != 1:
            # Defensive: should be exactly 1 per page. If more, manual review.
            print(f"  WARN     {rel}  has {len(matches)} filter links, expected 1")
            total_unexpected += 1
            continue

        new_text, n = RE_FILTER_LINK.subn(REPLACEMENT, text)
        if n != 1:
            print(f"  ERROR    {rel}  subn returned {n}")
            total_unexpected += 1
            continue

        path.write_text(new_text, encoding="utf-8")
        total_replaced += 1
        print(f"  FIXED    {rel}  ?filter={matches[0]}  ->  /gallery/")

    print()
    print(f"Replaced: {total_replaced}/{len(SERVICE_FILES)}")
    print(f"Already clean: {total_already_clean}")
    if total_unexpected:
        print(f"Unexpected: {total_unexpected}  (review above)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
