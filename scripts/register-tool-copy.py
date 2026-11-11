#!/usr/bin/env python3
"""
Register the runtime-copy aliases a new tool page uses.

WHY THIS IS A STEP AND NOT A ONE-LINER
--------------------------------------
A string that JavaScript creates AFTER the page has loaded cannot be
translated by the middleware - the html is already served by then. The
repo's mechanism for those strings is the `tools.copy` namespace:

* `js/tools/common.js` holds an alias table that maps a readable alias
  to the dictionary key,
* `i18n/<lang>.json` holds the key with its value in every language,
* the middleware hands the `tools.copy` namespace to the client.

Both halves must exist. An alias that is in the COPY table but not in
the dictionary falls back to English silently - and an alias that is in
the dictionary but not in the COPY table is never looked up at all.

So this script:
1. reads the `t('alias', 'English fallback')` calls out of the tool
   pages,
2. adds the missing aliases to the COPY table,
3. translates the fallbacks into the ten other languages and writes a
   dictionary patch.

The key suffix is derived from the alias name, so the same alias always
gets the same key - a key that changes between runs breaks every
language copy that already has it.

Usage
-----
    python scripts/register-tool-copy.py --slug wedding-video-editor \
        --slug wedding-photo-to-gif --file .tmp/copy-new-tools.json
"""
import argparse
import hashlib
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

CALL_RE = re.compile(r"(?<![A-Za-z0-9_])t\(\s*'([a-zA-Z0-9_]+)'\s*,\s*'((?:[^'\\]|\\.)*)'")
COPY_RE = re.compile(r"^(\s{4})([a-zA-Z0-9_]+):\s*'tools\.copy\.([a-zA-Z0-9_]+)\.([a-z0-9]+)',\s*$",
                     re.M)


def suffix(alias):
    return "zzzzzz" + hashlib.md5(alias.encode("utf-8")).hexdigest()[:5]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", action="append", required=True)
    ap.add_argument("--file", required=True)
    args = ap.parse_args()

    # 1. The aliases the pages use, with their English fallbacks.
    wanted = {}
    for slug in args.slug:
        path = ROOT / "tools" / slug / "index.html"
        html = path.read_text(encoding="utf-8")
        for m in CALL_RE.finditer(html):
            alias = m.group(1)
            fallback = m.group(2).replace("\\'", "'")
            if alias not in wanted:
                wanted[alias] = fallback
            elif wanted[alias] != fallback:
                print("  [warn] %s: two different fallbacks" % alias)

    # 2. The COPY table.
    common_path = ROOT / "js" / "tools" / "common.js"
    common = common_path.read_text(encoding="utf-8")
    known = {}
    for m in COPY_RE.finditer(common):
        known[m.group(2)] = m.group(3) + "." + m.group(4)

    missing = [a for a in wanted if a not in known]
    if missing:
        lines = []
        for alias in missing:
            lines.append("    %s: 'tools.copy.%s.%s',"
                         % (alias, alias, suffix(alias)))
        block = ("\n    // added %s\n%s\n"
                 % ("2026-11-10 (new tool pages)", "\n".join(lines)))
        marker = "  };\n"
        idx = common.index("var COPY = {")
        end = common.index(marker, idx)
        common = common[:end] + block.rstrip("\n") + "\n" + common[end:]
        common_path.write_text(common, encoding="utf-8", newline="\n")
        print("COPY table: added %d alias(es): %s"
              % (len(missing), ", ".join(missing)))
    else:
        print("COPY table: every alias is already registered")

    # 3. The dictionary patch.
    texts = [wanted[a] for a in wanted]
    kinds = {t: ("body", None) for t in texts}
    results = {}
    for lang in ttp.TARGET_LANGS:
        values, failures = ttp.llm_translate_all(texts, kinds, lang, workers=3, batch=20)
        results[lang] = values
        if failures:
            print("  [%s] %d failure(s)" % (lang, len(failures)))
            for text, reason in failures:
                print("      %s | %s" % (reason, text[:60]))

    # 4. The dictionary patch: only the keys the dictionaries do NOT have
    # yet. An alias that is in the COPY table but whose key is missing
    # from the dictionary falls back to English silently - that is the
    # case this has to catch.
    en_dict = json.loads((ROOT / "i18n" / "en.json").read_text(encoding="utf-8"))
    patch = {}
    for alias, fallback in wanted.items():
        key = ("tools.copy.%s" % known[alias]
               if alias in known else
               "tools.copy.%s.%s" % (alias, suffix(alias)))
        if key in en_dict:
            continue
        entry = {"en": fallback}
        for lang in ttp.TARGET_LANGS:
            entry[lang] = results.get(lang, {}).get(fallback, fallback)
        patch[key] = entry

    Path(args.file).write_text(json.dumps(patch, ensure_ascii=False, indent=1),
                                encoding="utf-8", newline="\n")
    print("dictionary patch: %s (%d keys)" % (args.file, len(patch)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
