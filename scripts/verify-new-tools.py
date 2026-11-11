#!/usr/bin/env python3
"""
Run every gate that covers the five new tool pages, in one command.

THE ORDER MATTERS
-----------------
* the page checks before the dictionary checks - a broken page makes
  the dictionary checks meaningless,
* the export checks before the deploy gate - the deploy gate looks at
  markup, and markup does not tell you whether the download produces
  real bytes,
* the shard check LAST, because it is the one that says whether the
  text the site SERVES is the text the dictionary holds.

WHAT IT DOES NOT DO
-------------------
It does not check the translation quality. That is the gate in
scripts/translate-tool-page.py (foreign_spans + english_ngram_leak), and
its own negative control is .tmp/test-foreign-gate.py.

Usage
-----
    python scripts/verify-new-tools.py
    python scripts/verify-new-tools.py --fast     # skip the browser work
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

TOOLS = [
    "wedding-stationery-set-maker",
    "wedding-photo-contact-sheet",
    "wedding-pdf-editor",
    "wedding-photo-to-gif",
    "wedding-video-editor",
]
LANGS = ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

results = []


def step(label, args, allow_fail=False):
    print("\n" + "=" * 72)
    print("== " + label)
    print("=" * 72, flush=True)
    t0 = time.time()
    proc = subprocess.run(args, cwd=str(ROOT))
    ok = proc.returncode == 0
    print("-- %s (%.1f s)" % ("PASS" if ok else "FAIL", time.time() - t0))
    results.append((label, ok))
    if not ok and not allow_fail:
        print("\n[STOP] %s failed - the rest of the gates would be noise"
              % label)
        summary()
        sys.exit(1)
    return ok


def summary():
    print("\n" + "=" * 72)
    bad = [label for label, ok in results if not ok]
    for label, ok in results:
        print("  %-4s %s" % ("PASS" if ok else "FAIL", label))
    print("=" * 72)
    if bad:
        print("%d gate(s) failed" % len(bad))
        sys.exit(1)
    print("every gate passed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true",
                    help="skip the browser-driven export checks")
    args = ap.parse_args()

    # --- 1. the pages ------------------------------------------------------
    for slug in TOOLS:
        step("page check: %s" % slug,
             [PY, str(ROOT / "scripts" / "check-tool-page.py"),
              str(ROOT / "tools" / slug / "index.html")])
    for slug in TOOLS:
        for lang in LANGS:
            path = ROOT / lang / "tools" / slug / "index.html"
            if not path.exists():
                print("\n[skip] %s has no copy yet" % lang)
                continue
            step("page check: %s/%s" % (lang, slug),
                 [PY, str(ROOT / "scripts" / "check-tool-page.py"),
                  str(path), "--skip-faq-parity"])

    step("the inline scripts parse",
         [PY, str(ROOT / "scripts" / "check-tool-script-syntax.py")])

    # --- 2. the export -----------------------------------------------------
    if not args.fast:
        step("the stationery export produces real artwork",
             [PY, str(ROOT / "scripts" / "verify-tool-export.py"),
              "--slug", "wedding-stationery-set-maker"])
        for slug, file_type in (("wedding-photo-contact-sheet", "png"),
                                ("wedding-pdf-editor", "pdf"),
                                ("wedding-photo-to-gif", "png"),
                                ("wedding-video-editor", "webm")):
            step("the download produces real bytes: %s" % slug,
                 [PY, str(ROOT / "scripts" / "verify-tool-smoke.py"),
                  "--slug", slug, "--file-type", file_type])

    # --- 3. the metadata ---------------------------------------------------
    step("the title and description lengths",
         [PY, str(ROOT / "scripts" / "check-seo-lengths.py")])

    # --- 4. the hub --------------------------------------------------------
    # FATAL. It used to be allow_fail=True, which is how the hub shipped
    # with three different tool counts (13 in the title, 27 in the
    # ItemList, 14 on the home page) while every gate stayed green.
    step("the hub agrees with itself",
         [PY, str(ROOT / "scripts" / "check-hub.py")])

    step("the hub's i18n keys exist in every dictionary",
         [PY, str(ROOT / "scripts" / "check-page-i18n-keys.py"),
          str(ROOT / "tools" / "index.html")])

    # --- 4b. the SERP rules -------------------------------------------------
    # The script knows the five tool pages itself; it takes no page argument.
    step("the SERP rules: all five tool pages",
         [PY, str(ROOT / "scripts" / "check-tool-serp-rules.py")])

    # --- 4c. the python %-format integrity ---------------------------------
    step("the python %-format calls",
         [PY, str(ROOT / "scripts" / "check-py-format-strings.py"),
          "--negative-control"])

    # --- 5. the deploy gate ------------------------------------------------
    step("the pre-deploy gate",
         ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
          str(ROOT / "internal-tools" / "pre-deploy-check.ps1")])

    summary()


if __name__ == "__main__":
    main()
