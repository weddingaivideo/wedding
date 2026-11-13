#!/usr/bin/env python3
r"""Repair the two small leftovers on the /tools/ hub.

1. The hero badge's English source says "32 free tools, 4 categories" while
   the ten translated dictionaries said only "32 tools". The project's own
   scripts/fix-hub-count.py defines BADGE = "✓ %d free tools, %d categories",
   so the correct fix is to restore the "free" claim in the translations,
   not to weaken the English copy. The key lives in its own tiny
   i18n/shards/<lang>/tools.hero_badge.json namespace (4 keys), so the
   dictionaries and shards can be patched in place - no full shard rebuild.

2. The ItemList JSON-LD carried two properties whose *keys* were whole
   sentences (an artifact of a past data-i18n dump). scripts/fix-hub-count.py
   already looks for `"name": "\d+ Free Wedding..."` and
   `"description": "\d+ free..."`; because they were missing, its ItemList
   name/description maintenance has been a silent no-op. Replace them with
   the canonical schema.org properties.

Idempotent: re-running makes no changes.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUB = ROOT / "tools" / "index.html"
KEY = "tools.hero_badge.thirteen_tools.7a8b9c0d"

NAME = "32 Free Wedding Planning & Photo Tools"
DESC = ("32 free browser-side wedding tools: photo editors, invitations, "
        "a PDF editor, checklists, vows, speeches, timelines and guest "
        "tools. No signup.")

BADGES = {
    "en": "✓ 32 free tools, 4 categories",
    "de": "✓ 32 kostenlose Tools, 4 Kategorien",
    "es": "✓ 32 herramientas gratuitas, 4 categorías",
    "fr": "✓ 32 outils gratuits, 4 catégories",
    "pt": "✓ 32 ferramentas gratuitas, 4 categorias",
    "ja": "✓ 32 種類の無料ツール、4 カテゴリ",
    "ru": "✓ 32 бесплатных инструмента, 4 категории",
    "ar": "✓ 32 أداة مجانية، 4 فئات",
    "th": "✓ 32 เครื่องมือฟรี 4 หมวดหมู่",
    "hi": "✓ 32 मुफ़्त उपकरण, 4 श्रेणियाँ",
    "zh": "✓ 32 个免费工具，4 个类别",
}


def fix_itemlist(html):
    """Turn the two sentence-as-key JSON-LD properties into name/description."""
    if ('"name": "%s"' % NAME) in html and ('"description": "%s"' % DESC) in html:
        return html, 0

    pat = re.compile(
        r'^(?P<indent>[ \t]*)"'
        r'(?:32 Free Wedding Planning|32 free browser-side wedding tools)'
        r'[^"]*"\s*:\s*"[^"]*",[ \t]*$', re.M)
    matches = list(pat.finditer(html))
    if len(matches) != 2:
        raise SystemExit(
            "[FAIL] expected 2 sentence-as-key ItemList properties, found %d"
            % len(matches))

    repl = [
        '%s"name": "%s",' % (matches[0].group("indent"), NAME),
        '%s"description": "%s",' % (matches[1].group("indent"), DESC),
    ]
    out = html
    for m, new in reversed(list(zip(matches, repl))):
        out = out[:m.start()] + new + out[m.end():]

    # A malformed JSON-LD block would be worse than the junk fields.
    block = re.search(
        r'<script type="application/ld\+json">(\{.*?\})</script>', out, re.S)
    if not block or json.loads(block.group(1)).get("@type") != "ItemList":
        raise SystemExit("[FAIL] ItemList JSON-LD no longer parses")
    return out, 2


def fix_dictionary(lang):
    """Patch exactly one line, preserving the dictionary's formatting."""
    path = ROOT / "i18n" / ("%s.json" % lang)
    text = path.read_text(encoding="utf-8")
    if json.loads(text).get(KEY) == BADGES[lang]:
        return 0

    head = re.compile(r'^(\s*"%s"\s*:\s*)"(?:[^"\\]|\\.)*"(.*)$'
                      % re.escape(KEY))
    lines = text.splitlines(keepends=True)
    hits = 0
    for i, line in enumerate(lines):
        if not re.match(r'^\s*"%s"\s*:' % re.escape(KEY), line):
            continue
        eol = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
        m = head.match(line.rstrip("\r\n"))
        if not m:
            raise SystemExit("[FAIL] cannot parse badge line in %s" % path)
        lines[i] = (m.group(1)
                    + json.dumps(BADGES[lang], ensure_ascii=False)
                    + m.group(2) + eol)
        hits += 1
    if hits != 1:
        raise SystemExit("[FAIL] %s: expected 1 badge key, found %d" % (path, hits))

    out = "".join(lines)
    if json.loads(out).get(KEY) != BADGES[lang]:
        raise SystemExit("[FAIL] %s: value did not round-trip" % path)
    path.write_text(out, encoding="utf-8", newline="")
    return 1


def fix_shard(lang):
    path = ROOT / "i18n" / "shards" / lang / "tools.hero_badge.json"
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if KEY not in data or len(data) != 4:
        raise SystemExit("[FAIL] unexpected hero_badge shard shape: %s" % path)
    if data[KEY] == BADGES[lang]:
        return 0
    data[KEY] = BADGES[lang]
    out = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if raw.endswith("\n"):
        out += "\n"
    path.write_text(out, encoding="utf-8", newline="")
    return 1


def main():
    html = HUB.read_text(encoding="utf-8")
    fixed_html, n_jsonld = fix_itemlist(html)
    if n_jsonld:
        HUB.write_text(fixed_html, encoding="utf-8", newline="")
    n_dict = n_shard = 0
    for lang in BADGES:
        n_dict += fix_dictionary(lang)
        n_shard += fix_shard(lang)
    print("ItemList properties repaired : %d" % n_jsonld)
    print("dictionaries updated         : %d / 11" % n_dict)
    print("hero_badge shards updated    : %d / 11" % n_shard)


if __name__ == "__main__":
    sys.exit(main())
