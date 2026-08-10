#!/usr/bin/env python3
"""
Inject an AboutPage JSON-LD block into about/index.html (English only).
The page currently has Organization + FAQPage + BreadcrumbList but is missing
the dedicated @type:AboutPage marker that helps Google classify the page
in topical clusters.

Idempotent.

Run:
    python scripts/inject-aboutpage.py         # dry-run
    python scripts/inject-aboutpage.py --apply # write
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://weddingai.video"
TARGET = ROOT / "about" / "index.html"

MARKER = "/* P0-INJECTED: about AboutPage */"
COMMENT_OPEN = "<!-- P0-INJECTED: about AboutPage -->"
COMMENT_END  = "<!-- /P0-INJECTED -->"
BLOCK_RE = re.compile(rf"{re.escape(COMMENT_OPEN)}.*?{re.escape(COMMENT_END)}", re.DOTALL)
BODY_END_RE = re.compile(r"</body>")


def build_block() -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "AboutPage",
        "@id": f"{SITE}/about/#about-page",
        "url": f"{SITE}/about/",
        "name": "About WeddingAI.video: Filmmakers + AI Engineers for Your Wedding",
        "description": "A small group of filmmakers, engineers, and wedding romantics building AI-powered wedding video services since 2024.",
        "inLanguage": "en",
        "isPartOf": {"@id": f"{SITE}/#website"},
        "about": {
            "@type": "Organization",
            "@id": f"{SITE}/#organization",
            "name": "WeddingAI.video",
            "foundingDate": "2024",
        },
        "mainEntity": {"@id": f"{SITE}/#organization"},
        "primaryImageOfPage": {
            "@type": "ImageObject",
            "url": f"{SITE}/images/og-about-1200x630.jpg",
            "width": 1200,
            "height": 630,
        },
        "speakable": {
            "@type": "SpeakableSpecification",
            "cssSelector": [
                "head > title",
                'head > meta[name="description"]',
                "h1",
                "h2",
                ".about-summary",
                ".team-member-bio",
            ],
        },
    }
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return (
        f"{COMMENT_OPEN}\n"
        f'<script type="application/ld+json">\n{body}\n</script>\n'
        f"{COMMENT_END}"
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
            print("  ERR : no </body>")
            sys.exit(1)
        new_text = text[: m.start()] + new_block + "\n" + text[m.start():]
        action = "INJECTED"

    if dry_run:
        print(f"  DRY  : about/index.html -> {action} ({len(new_block)} bytes)")
    else:
        TARGET.write_text(new_text, encoding="utf-8")
        print(f"  WROTE: about/index.html -> {action}")


if __name__ == "__main__":
    main()
