#!/usr/bin/env python3
"""
Make the tool COUNT true everywhere it is stated.

WHY A SCRIPT AND NOT A NUMBER
-----------------------------
The count appeared in five places at once and they drifted apart:

* the hub said "13 Free Wedding Photo Tools" while the page held 27
  cards,
* the hero badge said "27 free tools, 4 categories" while the page held
  four sections of which one was not in the badge's own grid,
* the home page said "14 Free Wedding Tools",
* the dictionaries said a third number,
* the ItemList said a fourth.

Two commits in one day each added tools without touching the others'
counts, and the numbers ended up describing four different catalogues.

THE RULE
--------
The PAGE is the truth. The card count is the number of
`<a class="tool-card">` elements, the category count is the number of
`<section class="tool-section">` blocks, and every number that is
stated anywhere is rewritten from those two.

THE WORDING
-----------
The hub stopped being a PHOTO tool catalogue when the planning tools
landed, so the name changed to "Planning & Photo Tools" - the name the
ItemList already used. The numbers are put back afterwards, so the
wording and the count never drift apart.

WHAT IT TOUCHES
----------------
* tools/index.html - the title, the description, the Open Graph and
  Twitter cards, the H1, the og:image:alt, the hero badge, the ItemList
  name and description, and the count in every section heading,
* index.html - the home page's heading and its "Browse all N tools" link,
* the 11 dictionaries - the same sentences, so the ten other languages
  say the same number as the English.

WHAT IT WILL NOT DO
-------------------
It does not translate. The dictionary values are translated by
scripts/build-hub-copy-patch.py, which reads the ENGLISH from the page -
so the translation always follows the wording, never the other way round.

Usage
-----
    python scripts/fix-hub-count.py
    python scripts/fix-hub-count.py --dry-run
    python scripts/fix-hub-count.py --html-only
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

HUB = ROOT / "tools" / "index.html"
HOME = ROOT / "index.html"

# The wording. %d is the count.
TITLE = "%d Free Wedding Planning & Photo Tools | No Signup"
H1 = "%d Free Wedding Planning & Photo Tools in One Catalog"
DESC = ("%d free browser-side wedding tools: photo editors, invitations, "
        "a PDF editor, checklists, vows, speeches, timelines and guest "
        "tools. No signup.")
BADGE = "✓ %d free tools, %d categories"

# The home page says "Free Wedding Tools" - no "photo", because it never
# claimed to be only about photos.
HOME_H2 = "%d Free Wedding Tools for 2026"
HOME_CTA = "Browse All %d Free Tools →"

# The section headings. A section whose heading is not listed keeps its
# own words - only its COUNT is rewritten.
SECTION_TITLES = {
    "gen": "Makers, generators and converters",
}
SECTION_DESCS = {
    "gen": ("Save-the-date cards, invitations, a full stationery set, a "
            "photo contact sheet, GIFs and invitation video - all in your "
            "browser, nothing uploaded."),
}

# The sentences in the dictionaries that state the count. The value is
# rewritten with the number only - the wording is translated elsewhere.
DICT_COUNT_KEYS = [
    "tools.h1.13_free_wedding_photo_tools_in_one_catal.7a8b9c0d",
    "tools.hero_badge.thirteen_tools.7a8b9c0d",
    "tools.faq.a.02",
    "tools.faq.a.08",
    "tools.why.card4.desc",
    "index.h2_text.13_free_wedding_tools_for_2026.q1r2s3t4",
    "index.a_text.browse_all_13_free_tools.h1i2j3k4",
]


def strip_tags(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text)).strip()


def hub_truth(html):
    """(card count, category count, {section: grid size})."""
    cards = len(re.findall(r'<a class="tool-card"', html))
    grids = {}
    for m in re.finditer(
            r'<section class="tool-section" id="cat-(\w+)">(.*?)</section>',
            html, re.S):
        grids[m.group(1)] = len(re.findall(r'<a class="tool-card"', m.group(2)))
    return cards, len(grids), grids


def set_title(html, text):
    return re.sub(r"<title[^>]*>.*?</title>",
                  lambda m: m.group(0).replace(strip_tags(m.group(0)), text),
                  html, count=1)


def replace_attr(html, pattern, text):
    """Replace the CONTENT="..." value of the first tag that matches.

    A <meta> tag has no closing tag, so a "replace the text between > and
    </" helper does nothing to it - and a helper that reports success
    anyway is worse than one that fails: the description keeps the old
    number and the script says it fixed it.
    """
    m = re.search(pattern, html, re.S)
    if not m:
        return html, False
    tag = m.group(0)
    new_tag, n = re.subn(r'(content=")[^"]*(")',
                         lambda mm: mm.group(1) + text + mm.group(2),
                         tag, count=1)
    if not n or new_tag == tag:
        return html, False
    return html[:m.start()] + new_tag + html[m.end():], True


def replace_inner(html, pattern, text):
    """Replace the TEXT between > and </ of the first tag that matches."""
    m = re.search(pattern, html, re.S)
    if not m:
        return html, False
    tag = m.group(0)
    new_tag, n = re.subn(r">([^<]*)</",
                         lambda mm: ">" + text + "</", tag, count=1)
    if not n or new_tag == tag:
        return html, False
    return html[:m.start()] + new_tag + html[m.end():], True


def replace_json_value(html, pattern, text):
    """Replace the quoted value of a JSON-LD "key": "value" pair."""
    m = re.search(pattern, html, re.S)
    if not m:
        return html, False
    frag = m.group(0)
    new_frag, n = re.subn(r'"[^"]*"', '"%s"' % text.replace('"', '\\"'),
                          frag, count=1)
    if not n or new_frag == frag:
        return html, False
    return html[:m.start()] + new_frag + html[m.end():], True


def fix_hub(html, cards, sections, grids):
    """The hub's own sentences."""
    changed = []

    # <title>
    html2, ok = replace_inner(html, r"<title[^>]*>.*?</title>", TITLE % cards)
    if ok:
        changed.append("title")
    html = html2

    # the meta description and the two cards that repeat it
    for pat, name in (
            (r'<meta\s+name="description"\s+content="[^"]*"\s*/?>', "description"),
            (r'<meta\s+property="og:description"\s+content="[^"]*"\s*/?>',
             "og:description"),
            (r'<meta\s+name="twitter:description"\s+content="[^"]*"\s*/?>',
             "twitter:description")):
        html2, ok = replace_attr(html, pat, DESC % cards)
        if ok:
            changed.append(name)
        html = html2

    # og:title / twitter:title
    for pat, name in (
            (r'<meta\s+property="og:title"\s+content="[^"]*"\s*/?>', "og:title"),
            (r'<meta\s+name="twitter:title"\s+content="[^"]*"\s*/?>',
             "twitter:title")):
        html2, ok = replace_attr(html, pat, TITLE % cards)
        if ok:
            changed.append(name)
        html = html2

    # og:image:alt
    html2, ok = replace_attr(
        html, r'<meta\s+property="og:image:alt"\s+content="[^"]*"\s*/?>',
        H1 % cards)
    if ok:
        changed.append("og:image:alt")
    html = html2

    # the H1
    html2, ok = replace_inner(
        html, r'<h1[^>]*data-i18n="tools\.h1\.[^"]*"[^>]*>.*?</h1>', H1 % cards)
    if ok:
        changed.append("h1")
    html = html2

    # the hero badge: the count AND the category count, and it gets a
    # binding so the ten other languages see it too.
    badge = BADGE % (cards, sections)
    m = re.search(r'<span class="hero-badge">[^<]*free tools[^<]*</span>', html)
    if m:
        old = m.group(0)
        new = ('<span class="hero-badge" data-i18n="tools.hero_badge.'
               'thirteen_tools.7a8b9c0d">%s</span>' % badge)
        html = html[:m.start()] + new + html[m.end():]
        changed.append("hero badge")
    else:
        # already bound: only the text
        html2, ok = replace_inner(
            html,
            r'<span class="hero-badge"[^>]*data-i18n="tools\.hero_badge\.'
            r'thirteen_tools[^"]*"[^>]*>.*?</span>', badge)
        if ok:
            changed.append("hero badge")
        html = html2

    # the ItemList's own name and description
    html2, ok = replace_json_value(
        html, r'"name": "\d+ Free Wedding[^"]*"',
        (TITLE % cards).split(" | ")[0])
    if ok:
        changed.append("ItemList name")
    html = html2
    html2, ok = replace_json_value(
        html, r'"description": "\d+ free[^"]*"', DESC % cards)
    if ok:
        changed.append("ItemList description")
    html = html2

    # the section headings and their descriptions
    for section, size in grids.items():
        m = re.search(
            r'(<section class="tool-section" id="cat-%s">.*?</section>)' % section,
            html, re.S)
        if not m:
            continue
        block = m.group(1)
        words = SECTION_TITLES.get(section)
        if words is None:
            # keep the words, fix the count
            hm = re.search(r'data-i18n="tools\.section\.title\.%s">(.*?)</h2>'
                           % section, block, re.S)
            if hm:
                plain = strip_tags(hm.group(1))
                new_plain = re.sub(r"\(\d+\)\s*$", "(%d)" % size, plain)
                if new_plain != plain:
                    block = block[:hm.start(1)] + new_plain + block[hm.end(1):]
                    changed.append("section %s title" % section)
        else:
            hm = re.search(r'data-i18n="tools\.section\.title\.%s">.*?</h2>'
                           % section, block, re.S)
            if hm:
                new_h2 = ('<h2 data-i18n="tools.section.title.%s">%s (%d)</h2>'
                          % (section, words, size))
                block = block[:hm.start()] + new_h2 + block[hm.end():]
                changed.append("section %s title" % section)
        desc = SECTION_DESCS.get(section)
        if desc:
            dm = re.search(r'data-i18n="tools\.section\.desc\.%s">.*?</p>'
                           % section, block, re.S)
            if dm:
                new_p = ('<p data-i18n="tools.section.desc.%s">%s</p>'
                         % (section, desc))
                block = block[:dm.start()] + new_p + block[dm.end():]
                changed.append("section %s description" % section)
        html = html[:m.start()] + block + html[m.end():]

    return html, changed


def fix_home(html, cards):
    changed = []
    html2, ok = replace_inner(
        html, r'<h2[^>]*data-i18n="index\.h2_text\.13_free_wedding_tools[^"]*"'
        r'[^>]*>.*?</h2>', HOME_H2 % cards)
    if ok:
        changed.append("home h2")
    html = html2
    # the CTA: both the visible text and the title attribute
    m = re.search(r'(<a[^>]*data-i18n="index\.a_text\.browse_all_13_free_tools'
                  r'[^"]*"[^>]*>)([^<]*)(</a>)', html, re.S)
    if m:
        block = m.group(0)
        block = re.sub(r'title="[^"]*"', 'title="Browse all %d free wedding tools"'
                       % cards, block)
        block = block[:m.start(2)] + (HOME_CTA % cards) + block[m.end(2):]
        html = html[:m.start()] + block + html[m.end():]
        changed.append("home cta")
    return html, changed


def fix_dict(lang, cards, sections, write=True):
    """The count in the dictionaries."""
    path = ROOT / "i18n" / ("%s.json" % lang)
    text = path.read_text(encoding="utf-8")
    changed = []
    for key in DICT_COUNT_KEYS:
        pat = re.compile(r'^(?P<pre>\s*)"' + re.escape(key) +
                         r'"\s*:\s*"(?P<val>(?:[^"\\]|\\.)*)"', re.M)
        m = pat.search(text)
        if not m:
            continue
        value = json.loads('"%s"' % m.group("val"))
        new_value = re.sub(r"(?<![\d.])13(?![\d.])", str(cards), value)
        new_value = re.sub(r"(?<![\d.])14(?![\d.])", str(cards), new_value)
        new_value = re.sub(r"(?<![\d.])27(?![\d.])", str(cards), new_value)
        if key == "tools.hero_badge.thirteen_tools.7a8b9c0d":
            # The badge holds TWO numbers: the tool count and the
            # CATEGORY count. The category count is the SECOND number,
            # whatever language it is written in - "✓ 32 个工具，3 个类别"
            # has to become "✓ 32 个工具，5 个类别", and a regex for the
            # English word "categories" would leave the other ten
            # languages saying three.
            numbers = list(re.finditer(r"\d+", new_value))
            if len(numbers) >= 2:
                second = numbers[1]
                new_value = (new_value[:second.start()] + str(sections) +
                             new_value[second.end():])
        if new_value != value:
            line = '%s"%s": %s' % (m.group("pre"), key,
                                   json.dumps(new_value, ensure_ascii=False))
            text = text[:m.start()] + line + text[m.end():]
            changed.append(key)
    if changed and write:
        tmp = path.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--html-only", action="store_true")
    args = ap.parse_args()

    html = HUB.read_text(encoding="utf-8")
    cards, sections, grids = hub_truth(html)
    print("the hub holds %d cards in %d sections: %s"
          % (cards, sections, ", ".join("%s=%d" % kv
                                        for kv in sorted(grids.items()))))
    if cards < 1 or sections < 1:
        raise SystemExit("[FAIL] the hub looks empty - not touching it")

    out, changed = fix_hub(html, cards, sections, grids)
    if out != html and not args.dry_run:
        HUB.write_text(out, encoding="utf-8", newline="")
    print("hub: %s" % (", ".join(changed) if changed else "no change"))

    home = HOME.read_text(encoding="utf-8")
    out2, changed2 = fix_home(home, cards)
    if out2 != home and not args.dry_run:
        HOME.write_text(out2, encoding="utf-8", newline="")
    print("home: %s" % (", ".join(changed2) if changed2 else "no change"))

    if args.html_only:
        return 0

    for lang in LANGS:
        keys = fix_dict(lang, cards, sections, write=not args.dry_run)
        print("  i18n/%-4s %d value(s)" % (lang, len(keys)))

    # The lengths matter: the deploy gate measures them.
    for name, text in (("title", TITLE % cards), ("description", DESC % cards),
                       ("h1", H1 % cards)):
        flag = "OK " if len(text) <= (60 if name != "description" else 160) \
            else "TOO LONG"
        print("  %-12s %3d chars  %s" % (name, len(text), flag))
    return 0


if __name__ == "__main__":
    sys.exit(main())
