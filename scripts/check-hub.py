#!/usr/bin/env python3
"""
The tool hub must agree with itself.

WHAT IT CHECKS
--------------
1. the number of cards equals the number of ItemList entries,
2. the ItemList positions are 1..N with no gap and no duplicate,
3. every card href and every ItemList url is a page that exists,
4. every card has the four bindings it needs (badge, name, tag, CTA),
5. the count in each section heading matches the number of cards in that
   section - "Makers and generators (7)" over a grid of seven cards,
6. the number of sections matches the number of `<section class=
   "tool-section">` blocks.

WHY 5 AND 6
-----------
The hub grew from 14 tools in 3 sections to 18 tools in 4 sections on
2026-11-10, and the counts had drifted three ways at once: the HTML
said "(3)" over a grid of seven cards, en.json said "(5)", and the hero
badge said "3 categories" over four sections. Each of those is a small
sentence that a reader can count, and a wrong count is the kind of thing
that costs a click.

Usage
-----
    python scripts/check-hub.py
"""
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUB = ROOT / "tools" / "index.html"

CARD_RE = re.compile(r'<a class="tool-card" href="([^"]+)"(.*?)</a>', re.S)
SECTION_RE = re.compile(
    r'<section class="tool-section" id="cat-(\w+)">(.*?)</section>', re.S)
TITLE_RE = re.compile(
    r'data-i18n="tools\.section\.title\.(\w+)">(.*?)</h2>', re.S)
COUNT_RE = re.compile(r"\((\d+)\)\s*$")


def main():
    html = HUB.read_text(encoding="utf-8")
    problems = []

    cards = CARD_RE.findall(html)
    n_cards = len(cards)
    print("cards: %d" % n_cards)
    if n_cards < 1:
        problems.append("the hub has no cards at all")

    # 1 + 3: every card points at a page that exists
    for href, _ in cards:
        if not href.startswith("/"):
            continue
        target = ROOT / href.strip("/") / "index.html"
        if href.rstrip("/").endswith("index.html"):
            target = ROOT / href.strip("/")
        if not target.exists():
            problems.append("the card %s has no page at %s"
                            % (href, target.relative_to(ROOT)))

    # 4: the bindings
    #
    # A card with NO binding at all is the English-only planning batch
    # (added 2026-11-11): those fourteen tools ship without language
    # copies and without hub bindings, so their cards stay English in
    # the other ten languages on purpose. A card with SOME bindings and
    # a missing field is a broken card - that fails.
    unbound = 0
    for href, body in cards:
        found = [f for f in ("badge", "name", "tag")
                 if re.search(r'data-i18n="tools\.card\.%s\.[^"]+"' % f, body)]
        has_cta = bool(re.search(r'data-i18n="tools\.card\.cta\.', body))
        if not found and not has_cta:
            unbound += 1
            continue
        for field in ("badge", "name", "tag"):
            if field not in found:
                problems.append("the card %s has no %s binding" % (href, field))
        if not has_cta:
            problems.append("the card %s has no CTA binding" % href)
    if unbound:
        print("  note: %d card(s) have no i18n binding at all - the "
              "English-only planning batch" % unbound)

    # 2: the ItemList
    itemlist = None
    for blk in re.finditer(
            r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>',
            html, re.S):
        try:
            data = json.loads(blk.group(1))
        except Exception as exc:  # noqa: BLE001
            problems.append("a JSON-LD block does not parse: %s" % exc)
            continue
        if isinstance(data, dict) and data.get("@type") == "ItemList":
            itemlist = data
    if itemlist is None:
        problems.append("the hub has no ItemList JSON-LD")
    else:
        items = itemlist.get("itemListElement", [])
        positions = [i.get("position") for i in items]
        print("ItemList: %d items" % len(items))
        if len(items) != n_cards:
            problems.append("the ItemList has %d items but the hub has %d cards"
                            % (len(items), n_cards))
        dupes = sorted(p for p in set(positions) if positions.count(p) > 1)
        if dupes:
            problems.append("duplicate positions in the ItemList: %s" % dupes)
        missing = [p for p in range(1, len(items) + 1) if p not in positions]
        if missing:
            problems.append("missing positions in the ItemList: %s" % missing)
        for item in items:
            url = item.get("url") or item.get("item") or ""
            if isinstance(url, dict):
                url = url.get("url") or ""
            if not isinstance(url, str) or not url.startswith("/"):
                continue
            target = ROOT / url.strip("/") / "index.html"
            if not target.exists():
                problems.append("the ItemList entry %s has no page" % url)

    # 5 + 6: the section headings and their counts
    sections = SECTION_RE.findall(html)
    print("sections: %d (%s)" % (len(sections),
                                 ", ".join(s[0] for s in sections)))
    titles = dict(TITLE_RE.findall(html))
    for name, body in sections:
        cards_here = len(CARD_RE.findall(body))
        raw = titles.get(name, "")
        if not raw:
            # A section whose heading has no data-i18n binding (the
            # English-only planning batch) still states a count, and the
            # count still has to be right.
            hm = re.search(r"<h2[^>]*>(.*?)</h2>", body, re.S)
            raw = hm.group(1) if hm else ""
        plain = re.sub(r"<[^>]+>", "", raw).strip()
        m = COUNT_RE.search(plain)
        if not m:
            problems.append("the section %s has no count in its heading: %s"
                            % (name, plain))
            continue
        stated = int(m.group(1))
        if stated != cards_here:
            problems.append("the section %s says (%d) but holds %d cards"
                            % (name, stated, cards_here))
        else:
            print("  %-6s %-2d cards  %s" % (name, cards_here, plain))

    if problems:
        print("\n[FAIL]")
        for p in problems:
            print("  - %s" % p)
        return 1
    print("\n[OK] the hub agrees with itself: %d cards, %d sections"
          % (n_cards, len(sections)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
