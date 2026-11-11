#!/usr/bin/env python3
"""
Rebuild the hub's JSON-LD ItemList from the cards that are actually on
the page.

WHY
---
The ItemList is the structured data that says "this site has N tools".
It is hand-edited, and hand-editing it has already broken it twice:

* the "Video Invitation Maker" entry was left at position 14 while the
  stationery entry was ALSO 14 - position 13 did not exist at all,
* the stationery entry ended with a trailing comma after its "item"
  object, which is not valid JSON, so the whole JSON-LD block was
  rejected by every consumer.

A parser that never runs against the page it describes cannot catch
that. This script rebuilds the array from the CARDS - the cards are the
truth - and then parses the result, so a broken array can never be
written.

The same is true of the hub's own `<title>`, meta description and the
"14 Free Wedding Photo Tools" name in the JSON-LD: they all state the
count, and scripts/sync-tool-count.py keeps them in step.

Usage
-----
    python scripts/rebuild-tool-itemlist.py
    python scripts/rebuild-tool-itemlist.py --check
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CARD_RE = re.compile(
    r'<a class="tool-card" href="/tools/([^/"]+)/">.*?'
    r'class="tool-name"[^>]*>([^<]*)</h3>', re.S)


def cards(html):
    """The cards on the page, in order: [(slug, name)]."""
    out = []
    for m in CARD_RE.finditer(html):
        out.append((m.group(1), m.group(2).strip()))
    return out


def build_entry(position, slug, name):
    return (
        '{\n"@type": "ListItem",\n"position": %d,\n"item": {\n'
        '"@type": "SoftwareApplication",\n"name": "%s",\n'
        '"url": "https://weddingai.video/tools/%s/",\n'
        '"applicationCategory": "MultimediaApplication",\n'
        '"operatingSystem": "Web Browser",\n'
        '"offers": {\n"@type": "Offer",\n"price": "0",\n"priceCurrency": "USD"\n}\n}\n}'
        % (position, name, slug))


def find_itemlist_block(html):
    """Return (start, end, block) of the ItemList JSON-LD BLOCK CONTENT.

    The boundaries are the CONTENT, not the `<script>` element: replacing
    the element with its content deletes the `<script type="application/
    ld+json">` wrapper, and the schema then disappears from the page
    without any error anywhere. That is what happened the first time
    this script ran.

    Returns None when the page has no ItemList block at all.
    """
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>',
                         html, re.S):
        if '"@type": "ItemList"' in m.group(1):
            return m.start(1), m.end(1), m.group(1)
    return None


def build_block(entries, count):
    """A whole ItemList JSON-LD block."""
    body = ",\n".join(entries)
    return (
        '{\n"@context": "https://schema.org",\n"@type": "ItemList",\n'
        '"name": "%d Free Wedding Planning & Photo Tools",\n'
        '"description": "%d free browser-side wedding tools: photo editing, '
        'invitations, budget and seating, checklists, vows, speeches, '
        'timelines and guest etiquette. No signup, nothing uploaded.",\n'
        '"itemListElement": [\n%s\n]\n}'
        % (count, count, body))


def rebuild_array(block, entries):
    """Replace the itemListElement array with a freshly built one."""
    start = block.index('"itemListElement": [')
    open_bracket = block.index("[", start)
    depth = 0
    close_bracket = None
    for i in range(open_bracket, len(block)):
        if block[i] == "[":
            depth += 1
        elif block[i] == "]":
            depth -= 1
            if depth == 0:
                close_bracket = i
                break
    if close_bracket is None:
        raise SystemExit("[FAIL] the itemListElement array is not closed")
    body = ",\n".join(entries)
    return block[:open_bracket + 1] + "\n" + body + "\n" + block[close_bracket:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report what would change and exit non-zero if the "
                         "page is out of step")
    args = ap.parse_args()

    path = ROOT / "tools" / "index.html"
    html = path.read_text(encoding="utf-8")

    found = cards(html)
    if not found:
        raise SystemExit("[FAIL] no tool cards found in the hub")

    found_block = find_itemlist_block(html)
    entries = [build_entry(i, slug, name)
               for i, (slug, name) in enumerate(found, 1)]

    if found_block is None:
        # The page has no ItemList block. Build one and put it in the head.
        new_block = build_block(entries, len(found))
        try:
            json.loads(new_block)
        except Exception as exc:  # noqa: BLE001
            raise SystemExit("[FAIL] the new JSON-LD does not parse: %s" % exc)
        script = ('<script type="application/ld+json">%s</script>\n'
                  % new_block)
        idx = html.index("</head>")
        out = html[:idx] + script + html[idx:]
        path.write_text(out, encoding="utf-8", newline="\n")
        print("created the ItemList block from the %d cards" % len(found))
        return 0

    start, end, block = found_block
    new_block = rebuild_array(block, entries)

    # The count in the JSON-LD's own name and description.
    #
    # The wording changed on 2026-11-11: the hub stopped being a PHOTO
    # tool catalogue when the planning tools landed, so the name became
    # "N Free Wedding Planning & Photo Tools". A regex pinned to the old
    # wording silently stopped updating the count, and the structured
    # data kept saying 27 while the page said 32.
    count = len(found)
    new_block = re.sub(r'("name": ")\d+( Free Wedding [^"]*Tools")',
                        r'\g<1>%d\g<2>' % count, new_block)
    new_block = re.sub(r'("description": ")\d+( free[^"]{0,80}?tools)',
                        r'\g<1>%d\g<2>' % count, new_block)

    # PROVE it parses before it is written.
    try:
        json.loads(new_block)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit("[FAIL] the rebuilt JSON-LD does not parse: %s" % exc)

    if new_block == block:
        print("OK  the ItemList already matches the %d cards" % count)
        return 0

    out = html[:start] + new_block + html[end:]
    path.write_text(out, encoding="utf-8", newline="\n")
    print("rebuilt the ItemList from the %d cards" % count)
    for i, (slug, name) in enumerate(found, 1):
        print("   %2d %s" % (i, name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
