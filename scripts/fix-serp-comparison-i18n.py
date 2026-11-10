#!/usr/bin/env python3
"""Fix for the SERP comparison sections (containers + missing English text).

Two defects, one root cause family:

1. `<section ... data-i18n="<page>.serp_comparison.section">` -- the
   middleware's applyDataI18n regex replaces the element's ENTIRE inner HTML
   with the dictionary value (a one-line title). Every non-English page
   therefore lost the whole comparison table. The dictionary key DOES exist
   in all 11 languages, so the wipe is what happens on every translated page.

2. `<table ... data-i18n="<page>.serp_comparison.table">` -- that key does not
   exist in 10 of 11 dictionaries (in ru.json it is a single "?"), but its
   mere presence makes the regex consume the whole table, so the per-cell
   data-i18n keys inside it are never reached. ru.json additionally holds 4889
   per-cell keys that were therefore dead.

Fix: drop the data-i18n attribute from those <section> and <table> elements.
The inner <h2>/<p>/<th>/<td> already carry their own keys, so the middleware
now translates them one by one.

Then: the default language is never server-translated
(functions/_middleware.js returns null for DEFAULT_LANG), so the English
static HTML must carry the English text. Every element whose data-i18n body
is empty is filled from i18n/en.json -- except the 404 page's popular links,
which are listed per language and come from each language's own dictionary.
"""
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

# <tag ... data-i18n="key" ...></tag>  (empty body, whitespace allowed)
EMPTY_EL = re.compile(r'(<(\w+)\b[^>]*?\bdata-i18n="([^"]+)"[^>]*?>)(\s*</\2>)')
# the two offending attributes
SECTION_ATTR = re.compile(r'\s*data-i18n="[^"]*serp_comparison\.section"')
TABLE_ATTR = re.compile(r'\s*data-i18n="[^"]*serp_comparison\.table"')
POPULAR_LANG = re.compile(r"serp_comparison\.popular\.([a-z]{2})\.")


def strip_container_keys(html):
    html, n1 = SECTION_ATTR.subn("", html)
    html, n2 = TABLE_ATTR.subn("", html)
    return html, n1 + n2


def fill_english(html, dict_):
    filled = 0
    missing = []

    def repl(m):
        nonlocal filled
        key = m.group(3)
        val = dict_.get(key)
        if not isinstance(val, str):
            missing.append(key)
            return m.group(0)
        filled += 1
        return m.group(1) + val + m.group(4)

    out = EMPTY_EL.sub(repl, html)
    return out, filled, missing


def lang_dict(lang, cache):
    """Load i18n/<lang>.json once per language."""
    if lang not in cache:
        path = ROOT / "i18n" / f"{lang}.json"
        try:
            cache[lang] = json.load(open(path, encoding="utf-8"))
        except Exception:
            cache[lang] = {}
    return cache[lang]


def fill_localized(html, cache):
    """404.html lists the popular links of ALL 11 languages; those keys live
    in each language's own dictionary, not in en.json."""
    filled = 0
    missing = []

    def repl(m):
        nonlocal filled
        key = m.group(3)
        lm = POPULAR_LANG.search(key)
        if not lm:
            missing.append(key)
            return m.group(0)
        val = lang_dict(lm.group(1), cache).get(key)
        if not isinstance(val, str):
            missing.append(key)
            return m.group(0)
        filled += 1
        return m.group(1) + val + m.group(4)

    out = EMPTY_EL.sub(repl, html)
    return out, filled, missing


def main():
    os.chdir(ROOT)
    dict_ = json.load(open("i18n/en.json", encoding="utf-8"))
    files = subprocess.run(["git", "ls-files", "*.html"], capture_output=True,
                           text=True, check=True).stdout.splitlines()
    tot_strip = tot_fill = 0
    all_missing = {}
    touched = 0
    cache = {}
    for rel in files:
        p = pathlib.Path(rel)
        html = p.read_bytes().decode("utf-8")
        html, n_strip = strip_container_keys(html)
        html, n_fill, missing = fill_english(html, dict_)
        html, n_fill2, missing2 = fill_localized(html, cache)
        n_fill += n_fill2
        missing += missing2
        if n_strip or n_fill:
            p.write_bytes(html.encode("utf-8"))
            touched += 1
        tot_strip += n_strip
        tot_fill += n_fill
        for k in missing:
            all_missing[k] = all_missing.get(k, 0) + 1
    print(f"files touched: {touched}")
    print(f"container data-i18n attributes removed: {tot_strip}")
    print(f"empty elements filled with English: {tot_fill}")
    print(f"keys still empty (not in any dictionary): {len(all_missing)} "
          f"({sum(all_missing.values())} occurrences)")
    for k, v in list(all_missing.items())[:10]:
        print(f"   {k}  x{v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
