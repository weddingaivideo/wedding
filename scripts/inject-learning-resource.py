#!/usr/bin/env python3
"""
Inject a LearningResource JSON-LD block into resources/index.html (English only
— no i18n mirror exists for /resources/).

The block uses schema.org Course-like LearningResource with hasPart pointing
to the five sub-guides listed on the page. The existing Article block stays
untouched so we don't fight the Article upgrade.

Idempotent.

Run:
    python scripts/inject-learning-resource.py         # dry-run
    python scripts/inject-learning-resource.py --apply # write
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://weddingai.video"
TARGET = ROOT / "resources" / "index.html"

# The five in-depth sub-guides in order, with H2 text + a slug derived from
# the title (each is a self-contained guide).
PARTS = [
    {
        "name": "How to Choose a Wedding Videographer: Complete Buyer's Guide",
        "url":  f"{SITE}/blog/choose-wedding-videographer/",
        "position": 1,
    },
    {
        "name": "AI Wedding Videos: What They Can (and Can't) Do \u2014 An Honest Guide",
        "url":  f"{SITE}/blog/ai-wedding-video-industry/",
        "position": 2,
    },
    {
        "name": "How to Restore Old Wedding Footage: VHS, Film, and Beyond",
        "url":  f"{SITE}/services/video-enhancement/vintage-restoration/",
        "position": 3,
    },
    {
        "name": "Wedding Video Costs Explained: What You're Really Paying For",
        "url":  f"{SITE}/blog/wedding-video-cost-2026-new/",
        "position": 4,
    },
    {
        "name": "15 Things to Do With Your Wedding Footage (That Aren't Just 'Save It')",
        "url":  f"{SITE}/blog/raw-wedding-footage-ideas/",
        "position": 5,
    },
]

MARKER_COMMENT = "<!-- P0-INJECTED: resources LearningResource -->"
MARKER_JSON    = "/* P0-INJECTED: resources LearningResource */"
END_COMMENT    = "<!-- /P0-INJECTED -->"
BLOCK_RE = re.compile(
    rf"{re.escape(MARKER_COMMENT)}.*?{re.escape(END_COMMENT)}",
    re.DOTALL,
)
BODY_END_RE = re.compile(r"</body>")


def build_block() -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "LearningResource",
        "@id": f"{SITE}/resources/#learning-resource",
        "name": "WeddingAI.video Guide: 5 In-Depth Wedding Video Resources",
        "description": "Five in-depth wedding video guides covering videographer selection, AI capabilities, restoration, pricing, and creative use of footage.",
        "url": f"{SITE}/resources/",
        "inLanguage": "en",
        "isPartOf": {"@id": f"{SITE}/#website"},
        "educationalLevel": "Beginner",
        "learningResourceType": "Guide",
        "audience": {
            "@type": "PeopleAudience",
            "audienceType": "Engaged couples planning a wedding",
            "suggestedMinAge": 18,
        },
        "author": {"@type": "Organization", "@id": f"{SITE}/#organization"},
        "publisher": {
            "@type": "Organization",
            "@id": f"{SITE}/#organization",
            "name": "WeddingAI.video",
        },
        "provider": {"@id": f"{SITE}/#organization"},
        "datePublished": "2026-07-21",
        "dateModified": "2026-08-10",
        "inLanguage": "en",
        "availableLanguage": ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"],
        "isAccessibleForFree": True,
        "hasPart": [
            {
                "@type": "LearningResource",
                "name": p["name"],
                "url": p["url"],
                "position": p["position"],
                "isAccessibleForFree": True,
                "learningResourceType": "Article",
            }
            for p in PARTS
        ],
    }
    # drop duplicates
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return (
        f"{MARKER_COMMENT}\n"
        f'<script type="application/ld+json">\n{body}\n</script>\n'
        f"{END_COMMENT}"
    )


def main():
    dry_run = "--apply" not in sys.argv
    if dry_run:
        print("DRY-RUN mode. Pass --apply to write changes.\n")
    if not TARGET.exists():
        print(f"ERROR: {TARGET} not found")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")
    new_block = build_block()
    if BLOCK_RE.search(text):
        new_text = BLOCK_RE.sub(new_block, text)
        action = "REPLACED"
    else:
        m = BODY_END_RE.search(text)
        if not m:
            print(f"  ERR : no </body>")
            sys.exit(1)
        new_text = text[: m.start()] + new_block + "\n" + text[m.start():]
        action = "INJECTED"

    if dry_run:
        print(f"  DRY  : resources/index.html -> {action} ({len(new_block)} bytes)")
    else:
        TARGET.write_text(new_text, encoding="utf-8")
        print(f"  WROTE: resources/index.html -> {action}")


if __name__ == "__main__":
    main()
