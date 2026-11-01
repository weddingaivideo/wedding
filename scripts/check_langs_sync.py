#!/usr/bin/env python3
"""
Check that the two copies of the canonical language list are in sync:

  - js/langs.js                 (browser-side, sets window.WA_LANGS)
  - functions/_lib/langs.js     (CF Pages Functions side, ES module exports)

Also verifies _redirects contains a /xx/* → /:splat 200 rule for every
language in js/langs.js (and only those languages).

Exits non-zero if any of:
  - LANGS array differs between the two files
  - A language in js/langs.js is missing from _redirects
  - _redirects contains a stray /xx/* rule for a language not in js/langs.js

Run from repo root:
    python scripts/check_langs_sync.py

Part of pre-deploy-check.ps1.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Read /js/langs.js and extract WA_LANGS list
LANGS_JS = ROOT / "js" / "langs.js"
LANGS_LIB = ROOT / "functions" / "_lib" / "langs.js"
REDIRECTS = ROOT / "_redirects"

LANGS_RE = re.compile(r'window\.WA_LANGS\s*=\s*\[([^\]]+)\]')
LIB_LANGS_RE = re.compile(r'export\s+const\s+LANGS\s*=\s*\[([^\]]+)\]')
DEFAULT_LANG_RE = re.compile(r'window\.WA_DEFAULT_LANG\s*=\s*"([a-z]{2,3})"')
REDIRECT_RE = re.compile(r'^/(\w+)/\*\s+/:splat\s+200', re.MULTILINE)


def parse_langs_array(src: str, pattern: re.Pattern) -> list[str]:
    m = pattern.search(src)
    if not m:
        raise ValueError(f"Could not find LANGS array in source (pattern: {pattern.pattern})")
    raw = m.group(1)
    # Extract quoted strings
    langs = re.findall(r'"([a-z]{2,3})"', raw)
    return langs


def main():
    errors = []

    if not LANGS_JS.exists():
        errors.append(f"Missing: {LANGS_JS}")
        print("\n".join(errors))
        return 1
    if not LANGS_LIB.exists():
        errors.append(f"Missing: {LANGS_LIB}")
        print("\n".join(errors))
        return 1
    if not REDIRECTS.exists():
        errors.append(f"Missing: {REDIRECTS}")
        print("\n".join(errors))
        return 1

    browser_langs = parse_langs_array(LANGS_JS.read_text(encoding="utf-8"), LANGS_RE)
    fn_langs = parse_langs_array(LANGS_LIB.read_text(encoding="utf-8"), LIB_LANGS_RE)

    dm = DEFAULT_LANG_RE.search(LANGS_JS.read_text(encoding="utf-8"))
    DEFAULT_LANG = dm.group(1) if dm else "en"

    if browser_langs != fn_langs:
        errors.append(
            f"LANGS mismatch: js/langs.js={browser_langs} vs functions/_lib/langs.js={fn_langs}"
        )
    else:
        print(f"[PASS] LANGS arrays match: {browser_langs}")

    # Check _redirects has a rule for every language
    #
    # The DEFAULT language is deliberately EXCLUDED. The rule
    #     /xx/*    /:splat 200
    # is how the middleware reaches the ENGLISH source file for a localized
    # URL: /zh/about/ is rewritten to /about/ and the middleware then serves
    # that file with the zh translation applied. The English site needs no
    # such rule - /about/ IS the English source - and adding one would be
    # actively harmful: it would match /en/blog/01-<old-slug>/ BEFORE the 50
    # blog 301 rules that migrate those slugs, sending visitors to a 404
    # instead of the 301.
    redirects_text = REDIRECTS.read_text(encoding="utf-8")
    redirect_langs = REDIRECT_RE.findall(redirects_text)
    required = [l for l in browser_langs if l != DEFAULT_LANG]
    missing = [l for l in required if l not in redirect_langs]
    extra = [l for l in redirect_langs if l not in browser_langs]
    if missing:
        errors.append(f"_redirects missing /xx/* rules for: {missing}")
    if extra:
        errors.append(f"_redirects has stray /xx/* rules for: {extra}")
    if not missing and not extra:
        print(f"[PASS] _redirects has all {len(required)} lang rules "
              f"(the default '{DEFAULT_LANG}' needs none): {sorted(set(redirect_langs))}")

    if errors:
        print("\n".join("[FAIL] " + e for e in errors))
        print("\nFix: edit js/langs.js, then mirror to functions/_lib/langs.js,")
        print("then run: python scripts/sync_langs_redirects.py")
        return 1

    print("\nAll language-list consistency checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
