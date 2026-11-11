#!/usr/bin/env python3
"""Append the 14 planning/wording tool URLs to the 11 shipped sitemaps.

Unlike scripts/add-tools-to-sitemap.py (which belongs to a different batch of
tools and restores the sitemaps from HEAD), this script is purely additive:
it never checks out, never rewrites existing blocks, and skips any <loc>
already present. Safe to run on a dirty working tree.

qa/gen_sitemap.py is deliberately NOT used — see the warning in its docstring.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORIGIN = "https://weddingai.video"
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
TODAY = datetime.now(timezone.utc).date().isoformat()

SLUGS = [
    "wedding-checklist-generator",
    "wedding-alcohol-calculator",
    "wedding-vow-writer",
    "wedding-speech-writer",
    "wedding-guest-count-calculator",
    "wedding-day-timeline-generator",
    "wedding-gift-calculator",
    "name-change-checklist",
    "wedding-thank-you-note-generator",
    "wedding-cake-serving-calculator",
    "wedding-dress-code-decoder",
    "wedding-vendor-tipping-calculator",
    "wedding-countdown-widget",
    "wedding-vendor-questions-checklist",
]


def lang_url(lang: str, slug: str) -> str:
    rest = f"/tools/{slug}/"
    return f"{ORIGIN}{rest}" if lang == "en" else f"{ORIGIN}/{lang}{rest}"


def url_block(lang: str, slug: str) -> str:
    links = [f'        <xhtml:link rel="alternate" hreflang="en" href="{lang_url("en", slug)}" />']
    for other in LANGS:
        if other != "en":
            links.append(f'        <xhtml:link rel="alternate" hreflang="{other}" href="{lang_url(other, slug)}" />')
    links.append(f'        <xhtml:link rel="alternate" hreflang="x-default" href="{lang_url("en", slug)}" />')
    return "\n".join([
        "    <url>",
        f"        <loc>{lang_url(lang, slug)}</loc>",
        f"        <lastmod>{TODAY}</lastmod>",
        "        <changefreq>monthly</changefreq>",
        "        <priority>0.7</priority>",
        *links,
        "        <image:image>",
        f"            <image:loc>{ORIGIN}/images/og-image-1200x630.jpg</image:loc>",
        f"            <image:title>{slug.replace('-', ' ').title()} — WeddingAI.video</image:title>",
        "        </image:image>",
        "    </url>",
    ])


def main() -> None:
    for lang in LANGS:
        path = ROOT / f"sitemap-{lang}.xml"
        text = path.read_text(encoding="utf-8")
        missing = [s for s in SLUGS if f"<loc>{lang_url(lang, s)}</loc>" not in text]
        if not missing:
            print(f"{path.name}: already complete")
            continue
        marker = "</urlset>"
        if marker not in text:
            raise RuntimeError(f"{path.name}: missing {marker}")
        blocks = "\n".join(url_block(lang, s) for s in missing)
        path.write_text(text.replace(marker, blocks + "\n" + marker), encoding="utf-8", newline="\n")
        print(f"{path.name}: +{len(missing)} URLs")


if __name__ == "__main__":
    main()
