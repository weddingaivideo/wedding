#!/usr/bin/env python3
"""
Build the dictionary patch for the hub's OWN copy: the five new tool
cards, the four section headings and their descriptions.

WHY THIS IS A SCRIPT AND NOT A HAND EDIT
----------------------------------------
The section headings were machine translated long ago and the result is
wrong in a way that changes the meaning of the page:

    "Makers and generators"  ->  zh "制造商和发电机"
    (a manufacturer and an electrical GENERATOR)

    "Makers and generators"  ->  th "ผู้ผลิตและเครื่องปั่นไฟ"
    (a producer and a BLENDER)

And the five new cards were translated by a model that was writing
garbage, so their Japanese name reads "CONTACTシート作成ツール" where
the brand-ish term had been upper-cased into nonsense.

THE ENGLISH COMES FROM THE HTML, NOT FROM en.json
-------------------------------------------------
The static page is what an English visitor gets - the middleware returns
null for the default language, so the HTML IS the English. en.json is a
copy of it, and the two had drifted:

  * "Makers and generators (3)" in the HTML vs "(5)" in en.json,
  * a gen description that mentions the stationery set in en.json and
    not in the HTML,
  * five cards and a whole section that en.json did not have at all
    (badge/name/tag 16, 17, 18, the docs section, three CTAs).

Reading the English from the HTML fixes the drift and makes the missing
keys translatable in the same pass.

WHAT IT COVERS
--------------
* cards 14, 15, 16, 17 and 18 - badge, name and tag,
* the section heading and description of all four sections,
* the "Try free ->" CTA of the cards that do not have one yet,
* the five card badges that were only ever translated into Russian.

The section heading carries its own count ("Photo editors (6)"), and the
count is NOT translated: the model would rewrite the number. The count
is stripped, the text is translated, and the count is put back.

Usage
-----
    python scripts/build-hub-copy-patch.py .tmp/hub-copy-patch.json
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "ttp", ROOT / "scripts" / "translate-tool-page.py")
ttp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ttp)

out_path = Path(sys.argv[1])
CARD_NUMBERS = ["14", "15", "16", "17", "18"]
SECTIONS = ["edit", "plan", "gen", "docs"]

# The card badges that exist in the page but were only ever translated
# into Russian. They are format names and short labels, so they are
# cheap to translate and they SHOULD be translated - "11 langs" and
# "Drag-drop" are not words an English reader expects to read.
EXTRA_BADGES = ["edit.02", "edit.04", "edit.05", "gen.11", "plan.08"]

hub = (ROOT / "tools" / "index.html").read_text(encoding="utf-8")
en = json.loads((ROOT / "i18n" / "en.json").read_text(encoding="utf-8"))
home = (ROOT / "index.html").read_text(encoding="utf-8")

CARD = re.compile(
    r'<a class="tool-card" href="/tools/[^"]+/">'
    r'(?:(?!</a>).)*?'
    r'data-i18n="tools\.card\.badge\.(\w+)\.(\d+)">(.*?)</span>'
    r'(?:(?!</a>).)*?'
    r'data-i18n="tools\.card\.name\.\w+\.\d+">(.*?)</h3>'
    r'(?:(?!</a>).)*?'
    r'data-i18n="tools\.card\.tag\.\w+\.\d+">(.*?)</p>', re.S)

cards = []
for m in CARD.finditer(hub):
    cards.append({"section": m.group(1), "number": m.group(2),
                  "badge": m.group(3).strip(), "name": m.group(4).strip(),
                  "tag": m.group(5).strip()})
print("cards on the page: %d" % len(cards))

# The CTA of a card that already has one - copied, not translated, so
# all 18 cards say the same thing in the same words.
cta_source = "tools.card.cta.try_free.01"

todo = []          # (key, english, kind, max)
for card in cards:
    if card["number"] not in CARD_NUMBERS:
        continue
    for field, kind in (("badge", "body"), ("name", "title"), ("tag", "body")):
        key = "tools.card.%s.%s.%s" % (field, card["section"], card["number"])
        todo.append((key, card[field], kind, 200 if field == "tag" else 90))
    cta_key = "tools.card.cta.try_free.%s" % card["number"]
    if cta_key not in en:
        todo.append((cta_key, "Try free →", "body", 40))

# The badges that never got a translation.
badge_re = re.compile(
    r'data-i18n="tools\.card\.badge\.(\w+)\.(\d+)">(.*?)</span>', re.S)
badge_text = {}
for m in badge_re.finditer(hub):
    badge_text["%s.%s" % (m.group(1), m.group(2))] = m.group(3).strip()
for ref in EXTRA_BADGES:
    if ref not in badge_text:
        print("  [warn] the badge %s is not on the page - skipped" % ref)
        continue
    key = "tools.card.badge.%s" % ref
    todo.append((key, badge_text[ref], "body", 40))

# The section headings and descriptions. The HTML is the English.
for section in SECTIONS:
    block = re.search(
        r'<section class="tool-section" id="cat-%s">(.*?)</section>' % section,
        hub, re.S)
    if not block:
        continue
    body = block.group(1)
    title_key = "tools.section.title.%s" % section
    m = re.search(r'data-i18n="%s">(.*?)</h2>' % re.escape(title_key), body, re.S)
    raw = m.group(1).strip() if m else (en.get(title_key) or "")
    if raw:
        # The count in parentheses belongs to the grid, not to the
        # translation. Strip it, translate the words, put it back.
        mm = re.match(r"^(.*?)\s*\((\d+)\)\s*$", raw)
        todo.append((title_key, mm.group(1) if mm else raw, "title", 60))
    desc_key = "tools.section.desc.%s" % section
    m = re.search(r'data-i18n="%s">(.*?)</p>' % re.escape(desc_key), body, re.S)
    raw = m.group(1).strip() if m else (en.get(desc_key) or "")
    if raw:
        todo.append((desc_key, raw, "body", 220))

print("keys to translate: %d" % len(todo))

# The page's own promise: the H1 and the hero badge. Both state the
# COUNT, and the count changed on 2026-11-11 (13 -> 32 tools, 3 -> 5
# categories) together with the WORDING - the hub is no longer only a
# photo tool catalogue.
#
# The numbers are load-bearing: llm_verify() checks that every number in
# the English is still in the translation, so a model that rewrites "32"
# as "35" is rejected instead of shipped.
for key, pattern, kind, maxlen in (
        ("tools.h1.13_free_wedding_photo_tools_in_one_catal.7a8b9c0d",
         r'<h1[^>]*data-i18n="tools\.h1\.[^"]*"[^>]*>(.*?)</h1>', "title", 60),
        ("tools.hero_badge.thirteen_tools.7a8b9c0d",
         r'<span class="hero-badge"[^>]*data-i18n="tools\.hero_badge\.'
         r'thirteen_tools[^"]*"[^>]*>(.*?)</span>', "body", 60)):
    m = re.search(pattern, hub, re.S)
    if m:
        todo.append((key, m.group(1).strip(), kind, maxlen))

# The home page's heading and its "Browse all N tools" link. Both are
# bound, and both state the count - and neither key was in en.json at
# all, so the English copy of the home page was the only place the
# number existed.
for key, pattern, kind, maxlen in (
        ("index.h2_text.13_free_wedding_tools_for_2026.q1r2s3t4",
         r'<h2[^>]*data-i18n="index\.h2_text\.13_free_wedding_tools[^"]*"'
         r'[^>]*>(.*?)</h2>', "title", 60),
        ("index.a_text.browse_all_13_free_tools.h1i2j3k4",
         r'<a[^>]*data-i18n="index\.a_text\.browse_all_13_free_tools[^"]*"'
         r'[^>]*>(.*?)</a>', "body", 60)):
    m = re.search(pattern, home, re.S)
    if m:
        todo.append((key, m.group(1).strip(), kind, maxlen))

print("keys to translate: %d" % len(todo))

texts = []
for key, text, kind, maxlen in todo:
    if text not in texts:
        texts.append(text)
kinds = {}
for key, text, kind, maxlen in todo:
    kinds.setdefault(text, (kind, maxlen))

results = {}
for lang in ttp.TARGET_LANGS:
    values, failures = ttp.llm_translate_all(texts, kinds, lang, workers=3,
                                              batch=10)
    results[lang] = values
    if failures:
        print("  [%s] %d failure(s)" % (lang, len(failures)))
        for text, reason in failures:
            print("      %s | %s" % (reason, text[:60]))

patch = {}
for key, text, kind, maxlen in todo:
    if key.startswith("tools.card.cta.") and key in en:
        continue
    entry = {"en": text}
    for lang in ttp.TARGET_LANGS:
        entry[lang] = results.get(lang, {}).get(text, text)
    patch[key] = entry

# The section headings get their count back, in the language's own form.
# The count is a number and the parentheses are ASCII in every language
# the site ships, so the count is put back the same way it was taken
# off.
grids = {}
for section in SECTIONS:
    m = re.search(
        r'<section class="tool-section" id="cat-%s">(.*?)</section>' % section,
        hub, re.S)
    if m:
        grids[section] = len(re.findall(r'<a class="tool-card"', m.group(1)))
for section in SECTIONS:
    key = "tools.section.title.%s" % section
    if key not in patch or section not in grids:
        continue
    for lang in ttp.TARGET_LANGS:
        patch[key][lang] = "%s (%d)" % (patch[key][lang], grids[section])
    # The English of the heading carries the count too, so en.json and
    # the page say the same thing.
    patch[key]["en"] = "%s (%d)" % (patch[key]["en"], grids[section])

# The CTA of a card that already has one is copied from the newest card
# that has one, so all the cards say the same words.
dicts = {lang: json.loads((ROOT / "i18n" / ("%s.json" % lang)).read_text(
    encoding="utf-8")) for lang in ttp.TARGET_LANGS}
for card in cards:
    cta_key = "tools.card.cta.try_free.%s" % card["number"]
    if cta_key in en or cta_key not in patch:
        continue
    for lang in ttp.TARGET_LANGS:
        value = dicts[lang].get(cta_source)
        if value:
            patch[cta_key][lang] = value

out_path.write_text(json.dumps(patch, ensure_ascii=False, indent=1),
                    encoding="utf-8", newline="\n")
print("wrote %s with %d keys" % (out_path.name, len(patch)))
