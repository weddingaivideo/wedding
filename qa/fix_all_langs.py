"""
Run fix_lang.py for all non-zh languages through all 3 phases.
Orchestrates the full pipeline: fix -> revalidate -> rollback.

Usage: python qa/fix_all_langs.py
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LANGS = ["ja", "th", "es", "de", "fr", "pt", "ru", "ar"]


def run(cmd, timeout):
    print(f"\n$ {' '.join(cmd)}")
    t0 = time.time()
    r = subprocess.run(cmd, cwd=ROOT, timeout=timeout, capture_output=False)
    elapsed = time.time() - t0
    if r.returncode != 0:
        print(f"  FAILED after {elapsed:.0f}s")
    return r.returncode


def main():
    for lang in LANGS:
        print(f"\n{'='*60}")
        print(f"LANG: {lang}")
        print('='*60)
        # Phase 1: fix (4 worker parallel translate, ~15-20 min for 2000-3000 keys)
        rc = run(["python", "qa/fix_lang.py", "--lang", lang, "--phase", "fix",
                  "--workers", "4"], timeout=5400)
        if rc != 0:
            print(f"fix {lang} FAILED, skipping revalidate/rollback")
            continue
        # Phase 2: revalidate (4 worker, ~10-15 min)
        rc = run(["python", "qa/fix_lang.py", "--lang", lang, "--phase", "revalidate",
                  "--workers", "4", "--samples", "3"], timeout=2400)
        if rc != 0:
            print(f"revalidate {lang} FAILED, skipping rollback")
            continue
        # Phase 3: rollback
        rc = run(["python", "qa/fix_lang.py", "--lang", lang, "--phase", "rollback"],
                  timeout=60)
        if rc != 0:
            print(f"rollback {lang} FAILED")
    print("\n=== ALL LANGUAGES DONE ===")


if __name__ == "__main__":
    main()
