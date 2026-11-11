#!/usr/bin/env python3
"""
Publish the five new tool pages: dictionaries, copies, shards.

THE ORDER MATTERS
-----------------
1. merge every patch into ONE file - each dictionary is 6-17 MB, so one
   write instead of five is the difference between one pass and five,
2. write the dictionaries,
3. sync the tool count (the hub says 14, there are 18 cards),
4. write the 10 language copies of every tool page, from the head
   translations the translation step produced,
5. push the English inline JS into the copies,
6. rebuild the shards - a stale shard set ships the OLD text with a 200
   response, which is the single most likely way a change silently
   fails to appear,
7. verify the shards.

Usage
-----
    python scripts/publish-new-tools.py
    python scripts/publish-new-tools.py --dry-run
"""
import argparse
import json
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
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

PATCHES = [
    ".tmp/wedding-stationery-set-maker-patch.json",
    ".tmp/wedding-photo-contact-sheet-patch.json",
    ".tmp/wedding-pdf-editor-patch.json",
    ".tmp/wedding-photo-to-gif-patch.json",
    ".tmp/wedding-video-editor-patch.json",
    ".tmp/hub-copy-patch.json",
    ".tmp/copy-new-tools.json",
]


def run(args, label):
    print("\n=== %s ===" % label, flush=True)
    proc = subprocess.Popen(args, cwd=str(ROOT))
    proc.wait()
    if proc.returncode != 0:
        raise SystemExit("[FAIL] %s (exit %d)" % (label, proc.returncode))
    return proc.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-shards", action="store_true")
    args = ap.parse_args()

    # --- 1. merge -----------------------------------------------------------
    merged = {}
    for rel in PATCHES:
        path = ROOT / rel
        if not path.exists():
            print("[skip] %s does not exist" % rel)
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for key, entry in data.items():
            if key in merged and merged[key] != entry:
                print("  [warn] %s differs between patches - keeping the first"
                      % key)
                continue
            merged[key] = entry
        print("  %-52s %d keys" % (rel, len(data)))
    print("merged: %d keys" % len(merged))

    merged_path = ROOT / ".tmp" / "merged-new-tools-patch.json"
    merged_path.write_text(json.dumps(merged, ensure_ascii=False, indent=1),
                           encoding="utf-8", newline="\n")

    # --- 2. the dictionaries ------------------------------------------------
    cmd = [PY, str(ROOT / "scripts" / "add-tool-ui-keys.py"),
           str(merged_path)]
    if args.dry_run:
        cmd.append("--dry-run")
    run(cmd, "write the 11 dictionaries")

    # --- 3. the tool count --------------------------------------------------
    #
    # scripts/fix-hub-count.py, NOT scripts/sync-tool-count.py: the count
    # is not a number any more, it is what the page holds. The hub had
    # 32 cards in 5 sections, and three different commits each stated a
    # different number for it. The new script reads the page and rewrites
    # every count from it.
    if not args.dry_run:
        run([PY, str(ROOT / "scripts" / "fix-hub-count.py")],
            "sync the tool count")

    # --- 4. the language copies ---------------------------------------------
    for slug in TOOLS:
        cmd = [PY, str(ROOT / "scripts" / "make-tool-lang-copies.py"),
               "--slug", slug]
        if args.dry_run:
            cmd.append("--dry-run")
        run(cmd, "language copies: %s" % slug)

    # --- 5. the English JS into the copies ----------------------------------
    if not args.dry_run:
        run([PY, str(ROOT / "scripts" / "propagate-tool-js.py"),
             "--tools", ",".join(TOOLS)], "propagate the inline JS")

    # --- 6. the shards ------------------------------------------------------
    if args.skip_shards:
        print("\n[skip] the shard rebuild")
        return 0
    for lang in LANGS:
        t0 = time.time()
        run([PY, str(ROOT / "scripts" / "add-shards-for-keys.py"),
             str(ROOT / "i18n" / ("%s.json" % lang)),
             str(ROOT / "i18n" / ("%s.manifest.json" % lang))],
            "shards: %s" % lang)
        print("    (%.1f s)" % (time.time() - t0))

    run([PY, str(ROOT / "scripts" / "verify-i18n-shards.py")],
        "verify the shards")
    print("\nPUBLISHED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
