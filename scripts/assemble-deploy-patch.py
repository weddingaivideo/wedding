#!/usr/bin/env python3
"""
Assemble a publishable patch + head for the five new tools out of EVERY
source that exists, keeping only the translations that pass the quality
gate.

WHY THIS EXISTS
---------------
The five tools have translations in four different places, none of them
complete:

| source | what it holds |
|---|---|
| `.tmp/<slug>-patch.json` | the CURRENT run (good model + gate) |
| `.tmp/backup-<slug>-patch.json` | the 2026-11-10 run (bad model: English fragments) |
| `.tmp/<slug>-patch.json` (old) | the 2026-10-30 run (good model, 7 languages) |
| `i18n/<lang>.json` | what the last publish wrote, including the bad values |

Shipping any ONE of them ships the bad values with it. Shipping none of
them ships English everywhere. So the rule is: **for every key and every
language, take the best value that exists and that passes the gate; fall
back to the English source when there is none.**

THE GATE
--------
`foreign_spans()` from the translator, with the technical terms the site's
own copy keeps verbatim (Ctrl, Mac, CMD, ICC, CMYK, 8x10 ...) added to the
allow list, plus `english_ngram_leak()` for the Latin-script languages.
A value that fails is replaced by the English source, never left broken.

WHAT IT WRITES
--------------
    .tmp/deploy1/<slug>-patch.json   the dictionary patch (11 languages)
    .tmp/deploy1/<slug>-head.json    the head patch (11 languages)

Both are written to a SEPARATE directory so a running translation never
sees them and never overwrites them.

Usage
-----
    python scripts/assemble-deploy-patch.py --dry-run
    python scripts/assemble-deploy-patch.py --apply
"""
import argparse
import importlib.util
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, ".tmp", "deploy1")
LANGS = ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

TOOLS = [
    "wedding-stationery-set-maker",
    "wedding-photo-contact-sheet",
    "wedding-pdf-editor",
    "wedding-photo-to-gif",
    "wedding-video-editor",
]

# Technical terms the site's own copy keeps in Latin inside a translated
# sentence. The translator's own LATIN_KEEP already covers the units; these
# are the ones that show up in THIS copy.
EXTRA_KEEP = {
    "ctrl", "mac", "cmd", "alt", "shift", "windows", "icc", "cmyk", "rgb",
    "8x10", "8x8", "4x6", "5x7", "3x5", "4x4", "browserrgb", "printsize",
    "actualsize", "fitto",
}

TITLE = re.compile(r"<title>(.*?)</title>", re.S)
HEAD_FIELDS = [
    ("description", r'<meta\s+name="description"\s+content="([^"]*)"'),
    ("og_title", r'<meta\s+property="og:title"\s+content="([^"]*)"'),
    ("og_description", r'<meta\s+property="og:description"\s+content="([^"]*)"'),
    ("twitter_title", r'<meta\s+name="twitter:title"\s+content="([^"]*)"'),
    ("twitter_description", r'<meta\s+name="twitter:description"\s+content="([^"]*)"'),
    ("og_image_alt", r'<meta\s+property="og:image:alt"\s+content="([^"]*)"'),
    ("app_title", r'<meta\s+name="apple-mobile-web-app-title"\s+content="([^"]*)"'),
]


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ttp = load_module(os.path.join(ROOT, "scripts", "translate-tool-page.py"), "ttp")


def run_allowed(run):
    """True when a Latin run inside a translated sentence is legitimate."""
    if ttp._run_is_allowed(run):
        return True
    norm = re.sub(r"\s+", " ", run.strip(" .-/")).lower()
    words = re.findall(r"[A-Za-z0-9]+", norm)
    return bool(words) and all(w in EXTRA_KEEP for w in words)


def broken(value, source, lang):
    """True when the value must not be published."""
    if not isinstance(value, str) or not value.strip():
        return True
    if source and value == source:
        return False           # untranslated on purpose: the English source
    if lang in ttp.LATIN_TARGETS:
        if ttp.english_ngram_leak(source or "", value):
            return True
        return False
    for run in ttp.LATIN_RUN_RE.findall(value):
        if not run_allowed(run):
            return True
    return False


def read_json(path):
    if not os.path.exists(path):
        return None
    with io.open(path, encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except ValueError:
            return None


def english_head(page_html):
    out = {}
    m = TITLE.search(page_html)
    out["title"] = m.group(1).strip() if m else ""
    for name, rx in HEAD_FIELDS:
        mm = re.search(rx, page_html)
        out[name] = mm.group(1).strip() if mm else ""
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.apply and not args.dry_run:
        ap.error("pass --dry-run or --apply")

    en = read_json(os.path.join(ROOT, "i18n", "en.json"))
    dicts = {l: read_json(os.path.join(ROOT, "i18n", "%s.json" % l))
             for l in LANGS}
    os.makedirs(OUT_DIR, exist_ok=True)

    total_kept = 0
    total_english = 0
    for slug in TOOLS:
        prefix = "tools.%s." % slug
        page_path = os.path.join(ROOT, "tools", slug, "index.html")
        page_html = io.open(page_path, encoding="utf-8").read()

        # Every candidate source, best first.
        patches = []
        for rel in (".tmp/%s-patch.json" % slug,
                    ".tmp/backup-%s-patch.json" % slug):
            data = read_json(os.path.join(ROOT, rel))
            if data:
                patches.append((rel, data))

        # The key set and the English source come from the i18n map, which is
        # built from the PAGE's own data-i18n bindings. en.json cannot be
        # used for that: three of the five tools have no key in it at all,
        # because the last English sync ran before those pages existed.
        page_map = read_json(os.path.join(ROOT, ".tmp",
                                          "%s-i18n-map.json" % slug)) or {}
        map_keys = page_map.get("keys") or {}
        map_order = page_map.get("order") or []
        if map_order:
            keys = list(map_order)
        else:
            keys = [k for k in en if k.startswith(prefix)]

        patch = {}
        kept = 0
        eng = 0
        for key in keys:
            source = map_keys.get(key) or en.get(key)
            if not source:
                continue
            entry = {"en": source}
            for lang in LANGS:
                value = None
                for rel, data in patches:
                    rec = data.get(key)
                    if isinstance(rec, dict):
                        cand = rec.get(lang)
                        if cand and cand != source and not broken(cand, source, lang):
                            value = cand
                            break
                if value is None:
                    d = dicts[lang] or {}
                    cand = d.get(key)
                    if isinstance(cand, str) and cand != source \
                            and not broken(cand, source, lang):
                        value = cand
                if value is None:
                    value = source
                    eng += 1
                else:
                    kept += 1
                entry[lang] = value
            patch[key] = entry
        total_kept += kept
        total_english += eng

        # --- the head --------------------------------------------------------
        heads = {}
        for rel in (".tmp/%s-head.json" % slug,
                    ".tmp/backup-%s-head.json" % slug):
            data = read_json(os.path.join(ROOT, rel))
            if not data:
                continue
            for lang, fields in data.items():
                if lang == "en" or lang == "jsonld" or not isinstance(fields, dict):
                    continue
                if lang not in heads:
                    heads[lang] = fields
        jsonld = {}
        for rel in (".tmp/%s-head.json" % slug,
                    ".tmp/backup-%s-head.json" % slug):
            data = read_json(os.path.join(ROOT, rel))
            if data and isinstance(data.get("jsonld"), dict):
                for lang, blob in data["jsonld"].items():
                    if lang not in jsonld:
                        jsonld[lang] = blob

        en_head = english_head(page_html)
        out_head = {"en": en_head, "jsonld": {}}
        en_jsonld = jsonld.get("en") or {}
        for lang in LANGS:
            fields = heads.get(lang)
            if fields:
                clean = {}
                for name, value in fields.items():
                    if isinstance(value, str) and broken(value, en_head.get(name), lang):
                        clean[name] = en_head.get(name, value)
                    else:
                        clean[name] = value
                out_head[lang] = clean
            else:
                out_head[lang] = dict(en_head)
            out_head["jsonld"][lang] = jsonld.get(lang) or en_jsonld
        out_head["jsonld"]["en"] = en_jsonld

        print("%-32s keys=%-4d kept=%-5d english=%-5d head langs=%d"
              % (slug, len(keys), kept, eng, len(heads)))
        if args.apply:
            with io.open(os.path.join(OUT_DIR, "%s-patch.json" % slug),
                         "w", encoding="utf-8", newline="\n") as fh:
                json.dump(patch, fh, ensure_ascii=False, indent=1)
            with io.open(os.path.join(OUT_DIR, "%s-head.json" % slug),
                         "w", encoding="utf-8", newline="\n") as fh:
                json.dump(out_head, fh, ensure_ascii=False, indent=1)

    print("\ntotal: %d translation(s) kept, %d fell back to the English source"
          % (total_kept, total_english))
    if not args.apply:
        return 0

    # --- the one merged patch ----------------------------------------------
    # The dictionaries are 6-17 MB, so one write beats five. The runtime
    # copy aliases (tools.copy.*) ride along: they are the strings the tool
    # pages create in JavaScript, which the middleware cannot translate.
    merged = {}
    for slug in TOOLS:
        part = read_json(os.path.join(OUT_DIR, "%s-patch.json" % slug)) or {}
        for key, entry in part.items():
            merged[key] = entry
    aliases = read_json(os.path.join(ROOT, ".tmp", "copy-new-tools.json")) or {}
    for key, entry in aliases.items():
        merged.setdefault(key, entry)
    # The hub copy is already in the dictionaries; the patch is only a
    # re-translation, so it is NOT merged in here.
    out = os.path.join(OUT_DIR, "merged-patch.json")
    with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(merged, fh, ensure_ascii=False, indent=1)
    print("merged patch: %d keys -> %s" % (len(merged), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
