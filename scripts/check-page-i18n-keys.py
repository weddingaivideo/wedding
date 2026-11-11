#!/usr/bin/env python3
"""
Every data-i18n key a page uses must exist in EVERY dictionary.

WHY THIS IS A GATE
------------------
The middleware swaps a bound element's text for the dictionary value
when it finds the key, and leaves the static English in place when it
does not. So a missing key is invisible: the page renders, the
dictionary looks complete, and one language quietly shows English
where the others show a translation.

Found on the hub (2026-11-11): `tools.card.badge.edit.02` ("HEIC")
existed in RUSSIAN ONLY - nine of the ten translations had no key for
it. Five of the five new cards' badge/name/tag, the whole `docs`
section and three CTAs had no key in en.json at all.

WHAT IT REPORTS
---------------
1. a key the page uses that en.json does not have (the English of a
   page IS the static HTML - en.json is only a copy of it),
2. a key that a translated language does not have,
3. a key that is still the English in a translated language.

(3) is reported, not failed: "JPG/PNG/HEIC" is a format list and
"Try free" is a CTA that many languages keep as it is.

Usage
-----
    python scripts/check-page-i18n-keys.py tools/index.html
    python scripts/check-page-i18n-keys.py tools/index.html --missing-only
"""
import argparse
import io
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

ATTR_RE = re.compile(r'data-i18n(?:-attr)?="([^"]+)"')


def page_keys(html):
    """The dictionary keys a page binds, the way the MIDDLEWARE reads them.

    TRAP: the two spellings carry different things.

        data-i18n="blog.foo.p_text.bar"          -> the key IS the value
        data-i18n-attr="content:blog.foo.meta"   -> "attr:key", and several
                                                   pairs can be separated by "|"

    The middleware splits an attr pair on ":" and uses the part AFTER the
    colon as the key (functions/_middleware.js, applyDataI18nAttr). A
    checker that keeps the whole "title:blog.foo.bar" string looks for a
    key that does not exist in any dictionary - and reports a defect on
    every page that binds an attribute, while the binding is in fact
    perfectly fine.

    So: split on "|", then on the FIRST ":", and keep the key.
    """
    out = set()
    for value in ATTR_RE.findall(html):
        for part in value.split("|"):
            part = part.strip()
            if not part:
                continue
            if ":" in part:
                _attr, _, key = part.partition(":")
                if key.strip():
                    out.add(key.strip())
                    continue
            out.add(part)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page", nargs="+")
    ap.add_argument("--missing-only", action="store_true",
                    help="only report the missing keys, not the English ones")
    ap.add_argument("--negative-control", action="store_true",
                    help="prove the checker can fail")
    args = ap.parse_args()

    if args.negative_control:
        tmp = Path(tempfile.mkdtemp(prefix="i18nkeys-neg-"))
        try:
            bad = tmp / "bad.html"
            bad.write_text(
                '<p data-i18n="tools.card.badge.does.not.exist.zzzzzzzz">x</p>'
                '<a title="t" data-i18n-attr="title:about.a_text.couples_served.ddddddd1">y</a>',
                encoding="utf-8")
            keys = page_keys(bad.read_text(encoding="utf-8"))
            problems = []
            if "tools.card.badge.does.not.exist.zzzzzzzz" not in keys:
                problems.append("the plain key was not read")
            if "about.a_text.couples_served.ddddddd1" not in keys:
                problems.append("the attr:key form was not read")
            if "title:about.a_text.couples_served.ddddddd1" in keys:
                problems.append("the attribute prefix leaked into the key")
            if problems:
                print("[FAIL] negative control: %s" % "; ".join(problems))
                return 1
            print("[OK] negative control: both binding forms are read the way "
                  "the middleware reads them.")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    dicts = {}
    for lang in LANGS:
        path = ROOT / "i18n" / ("%s.json" % lang)
        dicts[lang] = json.loads(path.read_text(encoding="utf-8"))

    failed = False
    for rel in args.page:
        path = ROOT / rel
        if not path.exists():
            print("[FAIL] %s does not exist" % rel)
            failed = True
            continue
        html = path.read_text(encoding="utf-8")
        keys = sorted(page_keys(html))
        print("%s uses %d distinct data-i18n keys" % (rel, len(keys)))

        missing_en = [k for k in keys if k not in dicts["en"]]
        if missing_en:
            print("  [FAIL] %d key(s) are not in en.json:" % len(missing_en))
            for k in missing_en:
                print("       %s" % k)
            failed = True

        for lang in LANGS:
            if lang == "en":
                continue
            miss = [k for k in keys if k not in dicts[lang]]
            if miss:
                print("  [FAIL] %s is missing %d key(s):" % (lang, len(miss)))
                for k in miss[:12]:
                    print("       %s" % k)
                if len(miss) > 12:
                    print("       ... and %d more" % (len(miss) - 12))
                failed = True

        if not args.missing_only:
            for lang in LANGS:
                if lang == "en":
                    continue
                same = [k for k in keys
                        if k in dicts["en"] and k in dicts[lang]
                        and dicts[lang][k] == dicts["en"][k]]
                if same:
                    print("  [note] %s still shows the English for %d key(s):"
                          % (lang, len(same)))
                    for k in same[:8]:
                        print("       %s" % k)
                    if len(same) > 8:
                        print("       ... and %d more" % (len(same) - 8))

    if failed:
        print("\n[FAIL] a dictionary is missing a key the page uses")
        return 1
    print("\n[OK] every dictionary has every key the page uses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
