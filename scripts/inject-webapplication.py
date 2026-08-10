#!/usr/bin/env python3
"""
Inject a WebApplication JSON-LD block into index.html (homepage only). The
homepage describes an end-to-end SaaS-style workflow (upload photos/video
-> AI processes -> delivery). Marking it as WebApplication alongside the
existing Service and WebSite blocks helps Google identify it as a runnable
tool rather than a content page.

Idempotent.

Run:
    python scripts/inject-webapplication.py         # dry-run
    python scripts/inject-webapplication.py --apply # write
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://weddingai.video"
TARGET = ROOT / "index.html"

COMMENT_OPEN = "<!-- P0-INJECTED: index WebApplication -->"
COMMENT_END  = "<!-- /P0-INJECTED -->"
BLOCK_RE = re.compile(rf"{re.escape(COMMENT_OPEN)}.*?{re.escape(COMMENT_END)}", re.DOTALL)
BODY_END_RE = re.compile(r"</body>")


def build_block() -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "@id": f"{SITE}/#web-application",
        "name": "WeddingAI.video \u2014 AI Wedding Video Service",
        "alternateName": "WeddingAI",
        "url": SITE,
        "description": "Browser-based AI service that restores, generates, and personalizes wedding videos. Upload photos or footage, get a cinematic film back in 3-7 business days.",
        "applicationCategory": "MultimediaApplication",
        "applicationSubCategory": "Wedding Video Production",
        "operatingSystem": "Any modern browser (Chrome, Safari, Firefox, Edge); mobile iOS 15+ and Android 10+",
        "browserRequirements": "Requires JavaScript, WebGL 2.0 for in-browser preview",
        "inLanguage": ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"],
        "isAccessibleForFree": False,  # paid service; quotes are free
        "offers": {
            "@type": "AggregateOffer",
            "priceCurrency": "USD",
            "lowPrice": "9.90",
            "highPrice": "599.00",
            "offerCount": "10",
            "availability": "https://schema.org/InStock",
            "url": f"{SITE}/pricing/",
        },
        "featureList": [
            "AI wedding film generation from photos",
            "VHS / 8mm / Hi8 restoration to 4K",
            "AI slow motion up to 240fps",
            "Multilingual dubbing in 20+ languages",
            "Cartoon / Ghibli / Pixar style transfer",
            "Family tribute video from photos and audio",
            "Family message integration for remote guests",
            "Wedding trailer (16:9 / 9:16 / 1:1 social formats)",
            "Pet wedding videos",
            "Custom wedding memes and GIFs",
        ],
        "screenshot": {
            "@type": "ImageObject",
            "url": f"{SITE}/images/og-home-1200x630.jpg",
            "width": 1200,
            "height": 630,
        },
        "author": {"@id": f"{SITE}/#organization"},
        "publisher": {"@id": f"{SITE}/#organization"},
        "provider": {"@id": f"{SITE}/#organization"},
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.9",
            "bestRating": "5",
            "worstRating": "1",
            "ratingCount": "6",
            "reviewCount": "6",
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
        sys.exit(f"ERROR: {TARGET} not found")

    text = TARGET.read_text(encoding="utf-8")
    new_block = build_block()
    if BLOCK_RE.search(text):
        new_text = BLOCK_RE.sub(new_block, text)
        action = "REPLACED"
    else:
        m = BODY_END_RE.search(text)
        if not m:
            sys.exit("  ERR : no </body>")
        new_text = text[: m.start()] + new_block + "\n" + text[m.start():]
        action = "INJECTED"

    if dry_run:
        print(f"  DRY  : index.html -> {action} ({len(new_block)} bytes)")
    else:
        TARGET.write_text(new_text, encoding="utf-8")
        print(f"  WROTE: index.html -> {action}")


if __name__ == "__main__":
    main()
