#!/usr/bin/env python3
"""
Fix the Service JSON-LD block in index.html.

Changes (Mavis SEO audit 2026-07-28):
  - Remove aggregateRating (Service + self-asserted rating = spam pattern
    that Google has been flagging in 2024-2025 algorithm updates;
    reviewCount=6 is too small to be credible anyway)
  - Remove the 6 hardcoded Review objects (same reasoning)
  - Add provider / serviceType / areaServed / offers so the Service
    schema is structurally complete and eligible for future rich results

The Organization and WebSite blocks already exist as separate JSON-LD
entries; the new provider field references them by @id.

Idempotent: re-running is a no-op.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "index.html"

# Match the entire Service JSON-LD block (open <script> through close </script>).
# We anchor on the opening brace + "@type": "Service" sequence to avoid
# accidentally matching other JSON-LD blocks.
SERVICE_BLOCK_RE = re.compile(
    r'<script type="application/ld\+json">\s*'
    r'(\{\s*"@context":\s*"https://schema\.org",\s*'
    r'"@type":\s*"Service".*?)\s*</script>',
    re.DOTALL,
)

NEW_SERVICE_JSON = """{
        "@context": "https://schema.org",
        "@type": "Service",
        "name": "WeddingAI.video Services",
        "description": "AI-powered wedding video restoration, creation, and personalization services",
        "serviceType": "Wedding Video Production",
        "provider": {
            "@type": "Organization",
            "@id": "https://weddingai.video/#organization",
            "name": "WeddingAI.video",
            "url": "https://weddingai.video"
        },
        "areaServed": [
            { "@type": "Place", "name": "Worldwide" }
        ],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "WeddingAI.video service catalog",
            "itemListElement": [
                { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "AI Wedding Video Generator" } },
                { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "Wedding Video Restoration" } },
                { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "Cinematic Wedding Trailer" } },
                { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "Pet Wedding Video" } },
                { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "Multilingual Wedding Video" } },
                { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "AI Slow Motion Enhancement" } }
            ]
        }
    }"""


def main() -> int:
    if not TARGET.exists():
        print(f"  FAIL: {TARGET} not found")
        return 1
    content = TARGET.read_text(encoding="utf-8")
    original_len = len(content)
    m = SERVICE_BLOCK_RE.search(content)
    if not m:
        print("  FAIL: Service JSON-LD block not found in index.html")
        return 1
    # Replace the entire script tag (open + body + close) with the new block
    old_block = m.group(0)
    new_block = f'<script type="application/ld+json">\n    {NEW_SERVICE_JSON}\n    </script>'
    if old_block == new_block:
        print("  - index.html: Service JSON-LD already matches target — no change")
        return 0
    content = content.replace(old_block, new_block, 1)
    TARGET.write_text(content, encoding="utf-8")
    print(f"  ✓ index.html: Service JSON-LD rewritten ({original_len} -> {len(content)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
