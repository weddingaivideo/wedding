#!/usr/bin/env python3
"""
Add a tool to the hub: the card, the ItemList entry and the dictionary keys.

WHY A SCRIPT
-------------
The hub lists a tool in THREE places that have to agree:

1. the card in the grid (`tools/index.html`),
2. the `position` in the JSON-LD ItemList,
3. the four `tools.card.*` keys in each of the 11 dictionaries.

Miss one and the card shows its English name in every language, or the
structured data lists 14 tools while the page shows 15. Both are the
kind of drift nobody sees until a reader does.

THE NUMBERING TRAP
------------------
The card numbers are GLOBAL and they are also the KEY NAMES:
`tools.card.name.gen.14`, `tools.card.cta.try_free.14`. The number is
the position of the card in the whole grid, not the position inside
its section - and the key name is part of the contract with the
dictionaries, so the number is NOT renumbered when a card is added.
A new card takes the next free number.

Usage
-----
    python scripts/add-tool-card.py --slug wedding-photo-contact-sheet \
        --section gen --name "Wedding Contact Sheet Maker" \
        --badge "Numbered proof sheet" \
        --tag "Print a numbered contact sheet of your wedding photos" \
        --file .tmp/card-contactsheet.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

CARD_RE = re.compile(r'<a class="tool-card" href="/tools/[^"]+">')
ITEM_RE = re.compile(r'"position":\s*(\d+),\s*\n\s*"item":\s*\{\s*\n\s*"@type":\s*"SoftwareApplication",\s*\n\s*"name":\s*"([^"]*)"')


DOCS_SECTION = """<section class="tool-section" id="cat-docs">
<div class="container">
<header class="section-header">
<h2 data-i18n="tools.section.title.docs">Document tools (0)</h2>
<p data-i18n="tools.section.desc.docs">Merge, split and reorder the PDF files your wedding vendors send you. Browser-side, no signup, nothing uploaded.</p>
</header>
<div class="tool-grid">
</div>
</div>
</section>
"""


def ensure_section(html, section):
    """Create the section if the hub does not have it yet.

    WHERE it goes matters. The document tools sit with the other
    CREATIVE tools - photo editors, makers, generators - so the new
    section goes before the planning section, not after it:

        edit | plan | gen | docs | planning

    The planning section (checklists, vows, speeches, guest counts) is a
    different family of tools and it reads better at the end.
    """
    if re.search(r'id="cat-%s"' % section, html):
        return html
    for anchor in ('<section class="tool-section" id="cat-planning">',
                   '<section class="why-section">'):
        idx = html.find(anchor)
        if idx >= 0:
            return html[:idx] + DOCS_SECTION + html[idx:]
    raise SystemExit("[FAIL] no anchor to insert the new section at")


def insert_card(html, section, slug, badge, name, tag, number):
    """Insert the card at the END of the section's grid."""
    m = re.search(r'(<section class="tool-section" id="cat-%s">(.*?)</section>)' % section,
                  html, re.S)
    if not m:
        raise SystemExit("[FAIL] no section cat-%s in the hub" % section)
    block = m.group(2)
    card = (
        '\n<a class="tool-card" href="/tools/%s/">\n'
        '<div class="tool-card-head">\n'
        '<span class="tool-badge" data-i18n="tools.card.badge.%s.%d">%s</span>\n'
        '<h3 class="tool-name" data-i18n="tools.card.name.%s.%d">%s</h3>\n'
        '</div>\n'
        '<p class="tool-tag" data-i18n="tools.card.tag.%s.%d">%s</p>\n'
        '<div class="tool-card-foot">\n'
        '<span class="tool-cta" data-i18n="tools.card.cta.try_free.%d">Try free →</span>\n'
        '</div>\n'
        '</a>\n' % (slug, section, number, badge, section, number, name,
                    section, number, tag, number))
    cards = list(re.finditer(r'<a class="tool-card" href="[^"]+">.*?</a>', block, re.S))
    if not cards:
        # An empty grid: the card goes straight after the grid opens.
        grid = block.find('<div class="tool-grid">')
        if grid < 0:
            raise SystemExit("[FAIL] the section cat-%s has no grid" % section)
        at = grid + len('<div class="tool-grid">')
        new_block = block[:at] + "\n" + card + block[at:]
        return html[:m.start(2)] + new_block + html[m.end(2):], 0
    last = cards[-1]
    new_block = block[:last.end()] + card + block[last.end():]
    return html[:m.start(2)] + new_block + html[m.end(2):], len(cards)


def insert_itemlist(html, slug, name, position):
    """Insert the ItemList entry after the last one."""
    starts = [m.start() for m in re.finditer(r'"@type": "ListItem"', html)]
    if not starts:
        raise SystemExit("[FAIL] no ItemList entries found")
    # Brace-match the last ListItem object so the new entry lands after
    # it and before the closing bracket of the array.
    #
    # The scan has to start at the object's OPENING brace, not at the
    # `"@type": "ListItem"` inside it: starting inside makes the depth
    # counter hit zero one brace too early, and the new entry lands in
    # the middle of the last item - which breaks the JSON-LD.
    i = html.rindex("{", 0, starts[-1])
    depth = 0
    end = None
    for j in range(i, len(html)):
        if html[j] == "{":
            depth += 1
        elif html[j] == "}":
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    if end is None:
        raise SystemExit("[FAIL] could not find the end of the last ListItem")
    entry = (
        ',\n{\n"@type": "ListItem",\n"position": %d,\n"item": {\n'
        '"@type": "SoftwareApplication",\n"name": "%s",\n'
        '"url": "https://weddingai.video/tools/%s/",\n'
        '"applicationCategory": "MultimediaApplication",\n'
        '"operatingSystem": "Web Browser",\n'
        '"offers": {\n"@type": "Offer",\n"price": "0",\n"priceCurrency": "USD"\n}\n}\n}'
        % (position, name, slug))
    return html[:end] + entry + html[end:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--section", required=True,
                    choices=("edit", "plan", "gen", "docs"))
    ap.add_argument("--name", required=True)
    ap.add_argument("--badge", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--file", required=True,
                    help="where to write the dictionary patch (JSON)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    hub_path = ROOT / "tools" / "index.html"
    html = hub_path.read_text(encoding="utf-8")

    if ('/tools/%s/"' % args.slug) in html:
        raise SystemExit("[FAIL] the hub already lists %s" % args.slug)

    numbers = [int(m) for m in re.findall(r'data-i18n="tools\.card\.name\.\w+\.(\d+)"', html)]
    number = max(numbers) + 1 if numbers else 1

    out, count = insert_card(ensure_section(html, args.section), args.section,
                             args.slug, args.badge, args.name, args.tag, number)

    cards_total = len(re.findall(r'<a class="tool-card"', out))
    print("hub: %d cards in the grids, new number %d" % (cards_total, number))

    if not args.dry_run:
        hub_path.write_text(out, encoding="utf-8", newline="\n")
        # The ItemList is rebuilt from the cards by a separate script:
        # hand-inserting an entry into that array is how it ended up with
        # a duplicate position and a trailing comma (invalid JSON).
        import subprocess
        rc = subprocess.run([sys.executable,
                             str(ROOT / "scripts" / "rebuild-tool-itemlist.py")],
                            cwd=str(ROOT)).returncode
        if rc != 0:
            raise SystemExit("[FAIL] the ItemList could not be rebuilt")

    # The dictionary patch: four keys per language.
    patch = {}
    for lang in LANGS:
        patch["tools.card.badge.%s.%d" % (args.section, number)] = {
            "en": args.badge}
        patch["tools.card.name.%s.%d" % (args.section, number)] = {
            "en": args.name}
        patch["tools.card.tag.%s.%d" % (args.section, number)] = {
            "en": args.tag}
        patch["tools.card.cta.try_free.%d" % number] = {"en": "Try free →"}
    Path(args.file).write_text(json.dumps(patch, ensure_ascii=False, indent=1),
                                encoding="utf-8", newline="\n")
    print("dictionary patch: %s (%d keys, english only - fill in the rest)"
          % (args.file, len(patch)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
