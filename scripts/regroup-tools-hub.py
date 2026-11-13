#!/usr/bin/env python3
"""Regroup the /tools/ catalog from 5 mixed-dimension sections into 4 task-based ones.

Confirmed IA (32 tools, 4 groups):
  Photo & video editing (8) / Invitations & printables (7)
  Planning & numbers (10)  / Words & etiquette (7)

Design constraints that make this low-risk:
  * Every tool card keeps its existing data-i18n keys verbatim. Only its DOM
    position changes, so all 11 dictionaries and every tools.card.* shard stay
    byte-identical. Keys are namespaced, not positional.
  * Section ids have no inbound anchors anywhere in the repo and no CSS hooks.
  * The ItemList JSON-LD is left alone: position is an ordinal, not a group.
  * Idempotent: writes a marker comment and refuses to run twice.

Emits .tmp/regroup-keys.json -> {key: english text} for the translation step.
Titles are emitted WITHOUT the trailing "(N)" so machine translation cannot
eat or rewrite the count; the apply step appends it.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUB = ROOT / "tools" / "index.html"
OUT_KEYS = ROOT / ".tmp" / "regroup-keys.json"
MARKER = "<!-- ft-regroup:v1 -->"

NEW_GROUPS = [
    dict(
        id="cat-photo", key="photo",
        title="Photo & video editing",
        desc=("Compress, convert, collage, crop and retouch wedding photos, add "
              "text, make GIFs or edit a video. All in your browser, nothing "
              "uploaded."),
        slugs=[
            "compress-wedding-photos",
            "heic-to-jpg-wedding-photos",
            "wedding-photo-collage",
            "crop-wedding-photo-for-reels",
            "remove-background-wedding-portrait",
            "add-text-to-wedding-photo",
            "wedding-photo-to-gif",
            "wedding-video-editor",
        ],
    ),
    dict(
        id="cat-invites", key="invites",
        title="Invitations & printables",
        desc=("Design invitations, date cards, a video invite, a matching "
              "stationery set, photo contact sheets and a photo book plan. "
              "Plus a PDF editor for vendor files."),
        slugs=[
            "save-the-date-maker",
            "wedding-invitation-maker",
            "wedding-video-invitation-maker",
            "wedding-stationery-set-maker",
            "wedding-photo-contact-sheet",
            "wedding-photo-book-planner",
            "wedding-pdf-editor",
        ],
    ),
    dict(
        id="cat-numbers", key="numbers",
        title="Planning & numbers",
        desc=("Work out guest numbers, budget, drinks, cake and seating. Build "
              "a checklist, a day timeline, vendor questions, a name-change "
              "list and a countdown."),
        slugs=[
            "wedding-checklist-generator",
            "wedding-budget-calculator",
            "wedding-seating-chart-maker",
            "wedding-guest-count-calculator",
            "wedding-alcohol-calculator",
            "wedding-cake-serving-calculator",
            "wedding-day-timeline-generator",
            "wedding-vendor-questions-checklist",
            "name-change-checklist",
            "wedding-countdown-widget",
        ],
    ),
    dict(
        id="cat-words", key="words",
        title="Words & etiquette",
        desc=("Write vows, speeches and thank-you notes. Decode dress codes, "
              "make a wedding hashtag, and work out gift amounts and vendor "
              "gratuities."),
        slugs=[
            "wedding-vow-writer",
            "wedding-speech-writer",
            "wedding-thank-you-note-generator",
            "wedding-dress-code-decoder",
            "wedding-hashtag-generator",
            "wedding-gift-calculator",
            "wedding-vendor-tipping-calculator",
        ],
    ),
]

OPEN = re.compile(r"^<(a|div|span|h3|p)\b")


def normalize_card(block: str) -> str:
    """Give every card one consistent 2-space nesting style.

    Guards itself: after all whitespace is stripped the result must equal the
    input, so no attribute, text or tag can be lost.
    """
    lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
    out, depth = [], 0
    for ln in lines:
        if ln.startswith("</"):
            depth = max(0, depth - 1)
        out.append("      " + "  " * depth + ln)
        m = OPEN.match(ln)
        if m and not re.search(r"</%s>" % m.group(1), ln):
            depth += 1
    result = "\n".join(out)
    squash = lambda t: re.sub(r"\s+", "", t)
    if squash(result) != squash(block):
        raise RuntimeError("card normalization changed content: " + block[:120])
    return result


def esc(text: str) -> str:
    """HTML-escape for source markup; dictionaries keep the bare '&'."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> int:
    html = HUB.read_text(encoding="utf-8")
    if MARKER in html:
        print("already regrouped (marker present) - nothing to do")
        return 0

    # --- collect the 5 existing tool sections and every card ----------------
    starts = [m.start() for m in re.finditer(r'<section class="tool-section"', html)]
    if len(starts) != 5:
        raise RuntimeError("expected 5 tool sections, found %d" % len(starts))
    blocks = []
    for i, a in enumerate(starts):
        b = starts[i + 1] if i + 1 < len(starts) else html.find('<section class="why-section"', a)
        if b < 0:
            raise RuntimeError("cannot find end of last tool section")
        blocks.append(html[a:b])
    first_start = starts[0]
    # the last tool section ends where the why-section begins
    last_end = html.find('<section class="why-section"', starts[-1])
    if last_end < 0:
        raise RuntimeError("why-section not found")

    cards = {}
    for block in blocks:
        for m in re.finditer(r'<a class="tool-card"[^>]*href="/tools/([^/]+)/"[^>]*>.*?</a>',
                             block, re.S):
            slug = m.group(1)
            if slug in cards:
                raise RuntimeError("duplicate card slug: " + slug)
            cards[slug] = m.group(0)
    if len(cards) != 32:
        raise RuntimeError("expected 32 cards, found %d" % len(cards))

    planned = [s for g in NEW_GROUPS for s in g["slugs"]]
    if len(planned) != 32 or len(set(planned)) != 32:
        raise RuntimeError("new IA is not 32 unique slugs")
    if set(planned) != set(cards):
        raise RuntimeError("IA slug mismatch: missing=%s extra=%s" % (
            sorted(set(cards) - set(planned)), sorted(set(planned) - set(cards))))

    # --- rebuild -----------------------------------------------------------
    sections = []
    for g in NEW_GROUPS:
        n = len(g["slugs"])
        assert n == len(g["slugs"])
        title_key = "tools.section.title.%s" % g["key"]
        desc_key = "tools.section.desc.%s" % g["key"]
        body = "\n".join(normalize_card(cards[s]) for s in g["slugs"])
        sections.append(
            '<section class="tool-section" id="{id}">\n'
            '  <div class="container">\n'
            '    <header class="section-header">\n'
            '      <h2 data-i18n="{tk}">{title} ({n})</h2>\n'
            '      <p data-i18n="{dk}">{desc}</p>\n'
            '    </header>\n'
            '    <div class="tool-grid">\n'
            '{body}\n'
            '    </div>\n'
            '  </div>\n'
            '</section>\n'.format(
                id=g["id"], tk=title_key, title=esc(g["title"]), n=n,
                dk=desc_key, desc=esc(g["desc"]), body=body,
            )
        )
    replacement = MARKER + "\n" + "\n".join(sections)

    new_html = html[:first_start] + replacement + html[last_end:]

    # hero badge: 5 -> 4 categories (source English only; dictionaries are
    # updated by the apply step)
    n_badge = new_html.count("✓ 32 free tools, 5 categories")
    if n_badge != 1:
        raise RuntimeError("expected 1 hero badge to update, found %d" % n_badge)
    new_html = new_html.replace("✓ 32 free tools, 5 categories",
                                "✓ 32 free tools, 4 categories")

    # --- invariants --------------------------------------------------------
    if len(re.findall(r'<section class="tool-section"', new_html)) != 4:
        raise RuntimeError("rebuilt hub does not have 4 sections")
    if len(re.findall(r'<a class="tool-card"', new_html)) != 32:
        raise RuntimeError("rebuilt hub does not have 32 cards")
    if "ft-extras" in html and "ft-extras" not in new_html:
        raise RuntimeError("lost extras marker")
    old_bindings = sorted(re.findall(r'data-i18n="([^"]+)"', html))
    new_bindings = sorted(re.findall(r'data-i18n="([^"]+)"', new_html))
    lost = sorted(set(old_bindings) - set(new_bindings))
    added = sorted(set(new_bindings) - set(old_bindings))
    expected_lost = sorted("tools.section.%s.%s" % (kind, old)
                           for kind in ("title", "desc")
                           for old in ("edit", "plan", "gen", "docs", "planning"))
    if lost != expected_lost:
        raise RuntimeError("unexpected lost bindings: %s" % lost)
    expected_added = sorted("tools.section.%s.%s" % (kind, g["key"])
                            for kind in ("title", "desc") for g in NEW_GROUPS)
    if added != expected_added:
        raise RuntimeError("unexpected added bindings: %s" % added)

    HUB.write_text(new_html, encoding="utf-8", newline="")

    keys = {}
    for g in NEW_GROUPS:
        keys["tools.section.title.%s" % g["key"]] = g["title"]
        keys["tools.section.desc.%s" % g["key"]] = g["desc"]
    OUT_KEYS.write_text(json.dumps(keys, ensure_ascii=False, indent=2), encoding="utf-8")

    counts = {g["key"]: len(g["slugs"]) for g in NEW_GROUPS}
    (ROOT / ".tmp" / "regroup-counts.json").write_text(
        json.dumps(counts, ensure_ascii=False, indent=2), encoding="utf-8")

    print("regrouped 5 sections -> 4, 32 cards preserved verbatim")
    for g in NEW_GROUPS:
        print("  %-12s %-30s %2d cards" % (g["id"], g["title"], len(g["slugs"])))
    print("new keys: %d -> %s" % (len(keys), OUT_KEYS))
    print("lost old section keys: %d / added: %d" % (len(lost), len(added)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
