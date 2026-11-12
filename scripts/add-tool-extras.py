#!/usr/bin/env python3
"""Idempotently add the v1 extras to the 14 planning tools and their 10
language copies:

  * Save .pdf (real file, js/tools/extras.js)
  * Add to calendar (.ics) + editable timeline (day-timeline only)
  * Wedding-date field + countdown-week view (checklist + timeline)
  * US-only region notice (name-change / tipping / gift)
  * Sources & further reading (the six pages with no visible citations)

Every new visible string is a data-i18n key so the middleware can translate
it. Run AFTER gen-free-tools.py / add-tool-i18n-bindings.py.

    python scripts/add-tool-extras.py              # apply
    python scripts/add-tool-extras.py --dry-run   # report only

New English strings are written to .tmp/extras-keys.json for translation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
SLUGS = [
    "wedding-checklist-generator", "wedding-alcohol-calculator",
    "wedding-vow-writer", "wedding-speech-writer",
    "wedding-guest-count-calculator", "wedding-day-timeline-generator",
    "wedding-gift-calculator", "name-change-checklist",
    "wedding-thank-you-note-generator", "wedding-cake-serving-calculator",
    "wedding-dress-code-decoder", "wedding-vendor-tipping-calculator",
    "wedding-countdown-widget", "wedding-vendor-questions-checklist",
]
TIMELINE = "wedding-day-timeline-generator"
CHECKLIST = "wedding-checklist-generator"
US_ONLY = {
    "name-change-checklist": (
        "US-only guidance. This checklist follows the US order (Social Security first, then DMV, "
        "passport, bank and employer). Post-marriage name-change law is different in Europe, and "
        "in many countries a name change is not expected at all."
    ),
    "wedding-vendor-tipping-calculator": (
        "US-only etiquette. Tipping every wedding vendor at this scale is a US convention. In most "
        "European countries a tip is optional, modest, or already included in the quoted price."
    ),
    "wedding-gift-calculator": (
        "US cash-gift etiquette. The 'cover your plate' range is an American custom. Across much of "
        "Europe a registry gift or a smaller cash amount is the norm, and some couples state 'no gifts'."
    ),
}
# Every URL below was verified against live search results on 2026-11-11.
# The descriptions quote figures those pages actually publish.
SOURCES = {
    "wedding-speech-writer": [
        ("Zola", "https://www.zola.com/expert-advice/how-long-should-the-best-man-speech-be",
         "Zola's ranked guide puts a best-man speech at two to five minutes, the ceiling this tool's word budget is built around."),
        ("Zola", "https://www.zola.com/expert-advice/wedding-planning-101/wedding-day/how-to-give-a-great-wedding-toast",
         "Ranked US toast guides converge on an introduction, two or three anecdotes, then a wish for the couple and the raise of a glass."),
    ],
    "wedding-guest-count-calculator": [
        ("The Knot", "https://www.theknot.com/content/how-many-people-rsvp-no",
         "The Knot's senior editor puts RSVP acceptance near 80% and the decline rule of thumb at 20%, before last-minute drop-outs."),
        ("The Knot", "https://www.theknot.com/content/average-wedding-guest-list-size",
         "The 2025 Real Weddings Study (10,474 US couples) reports 123 guests for hometown weddings versus 92 for domestic destination ones."),
    ],
    "name-change-checklist": [
        ("USA.gov", "https://www.usa.gov/name-change",
         "The official US government list says to notify Social Security early because other agencies learn of name changes through the SSA."),
        ("Social Security Administration", "https://www.ssa.gov/blog/en/posts/2026-10-22.html",
         "SSA's 2026 guidance: update your Social Security record before visiting the motor vehicle office, and bring certified documents."),
    ],
    "wedding-cake-serving-calculator": [
        ("Wilton", "https://www.wilton.com/wedding-cake-guide",
         "Wilton's published chart is the US bakery standard behind the 1 x 2 inch wedding serving used in this calculator."),
        ("Wilton", "https://wilton.com/baking-inspiration/cake-baking-serving-guide/",
         "Wilton distinguishes a 1 x 2 inch wedding slice from a 1.5 x 2 inch party slice; the same tier yields different counts."),
    ],
    "wedding-countdown-widget": [
        ("The Knot", "https://www.theknot.com/content/average-engagement-length",
         "The Knot 2025 Real Weddings Study surveyed nearly 17,000 couples and reports a 15-month average US engagement."),
        ("Brides", "https://www.brides.com/story/how-long-should-you-be-engaged-before-marriage",
         "Brides' planner panel puts the typical US engagement at 12 to 18 months, the window this countdown is designed for."),
    ],
    "wedding-vendor-questions-checklist": [
        ("The Knot", "https://www.theknot.com/content/wedding-vendor-checklist",
         "The Knot's vendor checklist breaks interview questions down by supplier category, from catering and DJs to transport and stationery."),
        ("The Knot", "https://www.theknot.com/content/questions-to-ask-your-wedding-caterer",
         "Its 40-question caterer guide starts with availability, liability insurance, venue experience and client references."),
    ],
}
MARK = "<!-- ft-extras:v1 -->"
TEXT: dict[str, str] = {}


def key(slug: str, tag: str, text: str) -> str:
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    snippet = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:36].strip("_")
    k = f"tools.{slug}.{tag}.{snippet}.{digest}"
    TEXT[k] = text
    return k


def bound(slug: str, tag: str, text: str, ident: str, cls: str = "ft-btn", extra: str = "") -> str:
    k = key(slug, tag, text)
    return f'<button type="button" class="{cls}" id="{ident}" data-i18n="{k}" {extra}>{text}</button>'


def span(slug: str, tag: str, text: str, cls: str = "") -> str:
    k = key(slug, tag, text)
    c = f' class="{cls}"' if cls else ""
    return f'<span{c} data-i18n="{k}">{text}</span>'


def date_field(slug: str) -> str:
    lab = "Wedding date (for calendar export and countdown weeks)"
    k = key(slug, "label_text", lab)
    return ('<div class="ft-field ft-export-field">'
            f'<label for="ft-date" data-i18n="{k}">{lab}</label>'
            '<input class="ft-input" type="date" id="ft-date" data-ft="date">'
            '</div>')


def region_note(slug: str) -> str:
    body = US_ONLY[slug]
    k = key(slug, "p_text", body)
    return ('<div class="ft-region-note" id="ft-region-note" role="note">'
            f'<span data-i18n="{k}">{body}</span>'
            '<button type="button" class="ft-region-dismiss" aria-label="Dismiss">×</button>'
            '</div>')


def sources_block(slug: str) -> str:
    head = "Sources & further reading"
    hk = key(slug, "h2_text", head)
    items = []
    for name, url, desc in SOURCES[slug]:
        dk = key(slug, "li_text", desc)
        items.append(
            f'<li><a href="{url}" rel="nofollow noopener" target="_blank">{name}</a> '
            f'<span data-i18n="{dk}">— {desc}</span></li>'
        )
    return ('<div class="ft-serp-sources">'
            f'<h2 data-i18n="{hk}">{head}</h2><ul>' + "".join(items) + '</ul></div>')


def extras_cfg(slug: str) -> str:
    cfg = {"slug": slug, "pdf": True}
    if slug == TIMELINE:
        cfg.update({"ics": True, "editable": True, "eventTitle": "Wedding day timeline"})
    if slug == CHECKLIST:
        cfg.update({"weekView": True, "weekMap": [52, 40, 28, 16, 8, 4, 1]})
    return "window.FT_EXTRAS = " + json.dumps(cfg, ensure_ascii=False) + ";"


def inject(html: str, slug: str) -> str:
    if MARK in html:
        return html

    # 1. enhancement runtime, after free-tools.js
    m = re.search(r'(<script[^>]*src="/js/tools/free-tools\.js[^"]*"[^>]*>\s*</script>)', html)
    if not m:
        raise RuntimeError(f"{slug}: free-tools.js tag not found")
    html = html.replace(m.group(1), m.group(1) + '\n<script defer src="/js/tools/extras.js?v=1.0.0"></script>', 1)

    # 2. per-page config inside the existing inline script (nonce-safe)
    i = html.find("window.FT_CONFIG")
    if i < 0:
        raise RuntimeError(f"{slug}: FT_CONFIG not found")
    j = html.find("</script>", i)
    if j < 0:
        raise RuntimeError(f"{slug}: inline script end not found")
    html = html[:j] + "\n" + extras_cfg(slug) + "\n" + html[j:]

    # 3. buttons inside .ft-actions
    m = re.search(r'<div class="ft-actions">([\s\S]*?)</div>', html)
    if not m:
        raise RuntimeError(f"{slug}: .ft-actions not found")
    btns = [bound(slug, "button_text", "Save .pdf", "ft-pdf")]
    if slug == TIMELINE:
        btns.append(bound(slug, "button_text", "Add to calendar (.ics)", "ft-ics"))
    block = m.group(0)[:-len("</div>")] + "\n                    " + "\n                    ".join(btns) + "\n                </div>"
    html = html.replace(m.group(0), block, 1)

    # 4. controls before .ft-actions
    pre = ""
    if slug in (TIMELINE, CHECKLIST):
        pre += date_field(slug)
    if slug == CHECKLIST:
        toggle = bound(slug, "button_text", "View by countdown week", "ft-week-toggle",
                       cls="ft-week-toggle", extra='aria-pressed="false"')
        hint1 = span(slug, "p_text", "Add your wedding date to highlight the current week.")
        hint2 = span(slug, "p_text", "Your current countdown block is highlighted below.")
        pre += ('<div class="ft-week-controls">' + toggle +
                '<p class="ft-week-hint" id="ft-week-hint" style="display:none;">'
                f'<span id="ft-week-hint-nodate">{hint1}</span>'
                f'<span id="ft-week-hint-yesdate" style="display:none;">{hint2}</span>'
                '</p></div>')
    if slug == TIMELINE:
        tip = "Drag rows to reorder, or use the arrows. Edit a time directly; every export stays in sync."
        pre += '<p class="ft-hint">' + span(slug, "p_text", tip) + '</p>'
    if pre:
        html = html.replace('<div class="ft-actions">', pre + '\n                <div class="ft-actions">', 1)

    # 5. US-only notice near the top of the tool grid
    if slug in US_ONLY:
        anchor = re.search(r'<div class="ft-grid"[^>]*>', html)
        if anchor:
            html = html.replace(anchor.group(0), region_note(slug) + "\n            " + anchor.group(0), 1)

    # 6. sources before the closing main (or footer)
    if slug in SOURCES:
        for pat in (r'</main>', r'<footer'):
            m2 = re.search(pat, html)
            if m2:
                html = html[:m2.start()] + sources_block(slug) + "\n" + html[m2.start():]
                break

    # 7. marker (comment, so no attributes or SEO tags are touched)
    html = html.replace("</head>", "    " + MARK + "\n</head>", 1) if "</head>" in html else MARK + html
    return html


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    targets = []
    for slug in SLUGS:
        targets.append(ROOT / "tools" / slug / "index.html")
        for lang in LANGS:
            p = ROOT / lang / "tools" / slug / "index.html"
            if p.exists():
                targets.append(p)

    changed = skipped = 0
    for p in targets:
        slug = p.parent.name
        html = p.read_text(encoding="utf-8")
        if MARK in html:
            skipped += 1
            continue
        out = inject(html, slug)
        changed += 1
        if not args.dry_run:
            p.write_text(out, encoding="utf-8")

    keys_path = ROOT / ".tmp" / "extras-keys.json"
    keys_path.parent.mkdir(exist_ok=True)
    keys_path.write_text(json.dumps(TEXT, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"targets={len(targets)} changed={changed} already-done={skipped}")
    print(f"new English keys={len(TEXT)} -> {keys_path.relative_to(ROOT)}")
    if args.dry_run:
        print("(dry run: no files written except the key list)")


if __name__ == "__main__":
    main()
