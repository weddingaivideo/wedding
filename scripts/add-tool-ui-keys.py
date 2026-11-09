#!/usr/bin/env python3
"""
Add or update tool-UI i18n keys in all 11 language dictionaries, atomically.

WHY THIS EXISTS
---------------
The tool pages are localized into 11 languages through flat top-level keys
in i18n/<lang>.json:

    "tools.copy.download.zzzzzzfd45": "Download"

The key namespace is the first TWO dotted segments, so `tools.copy.*` is a
namespace shared by every tool and `tools.<slug>.*` belongs to one tool.
A page only needs the namespaces its own data-i18n keys live in, and the
middleware fetches exactly those shards (functions/_lib/i18n-shards.js).

Adding a key means touching 11 files. Doing that by hand is how a
half-translated dictionary happens, and it is also how a 10 MB file gets
truncated (open(path, "w") truncates before it writes - that is how
i18n/ja.json was reduced to 0 bytes on 2026-10-30).

WHAT IT DOES
------------
1. Reads a patch file: {"<i18n key>": {"en": "...", "zh": "...", ...}}.
   Every language MUST be present for every key - a missing translation is
   an error, not a silently skipped line.
2. For each language: adds the key if it is absent, replaces the value if
   it is present. Never reorders or reformats the rest of the file.
3. Writes atomically (temp file + fsync + os.replace).
4. Re-reads and validates the result with json.loads before it is trusted.

Usage
-----
    python scripts/add-tool-ui-keys.py patch.json
    python scripts/add-tool-ui-keys.py patch.json --dry-run

Afterwards ALWAYS run:
    python scripts/add-shards-for-keys.py i18n/<lang>.json i18n/<lang>.manifest.json
    python scripts/verify-i18n-shards.py          # the fatal pre-deploy gate

A stale shard set ships the OLD text with a 200 response - the change looks
like it did nothing. That is the single most likely way a tool improvement
silently fails to appear.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N_DIR = ROOT / "i18n"

LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]


def write_atomic(path: Path, text: str) -> None:
    """Write via temp file + fsync + os.replace.

    A plain open(path, "w") truncates the target BEFORE the write, so an
    interrupted run leaves a 0-byte file. os.replace() is atomic on Windows:
    the destination is either the old content or the new content, never a
    half-written one.
    """
    tmp = path.with_name(f".{path.name}.tmpwrite")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def esc(value: str) -> str:
    """JSON-escape a value for embedding in a JSON source file."""
    return json.dumps(value, ensure_ascii=False)


def apply_key(text: str, key: str, value: str) -> tuple[str, str]:
    """Insert or replace one flat key. Returns (new_text, action)."""
    # Match the key as a whole JSON string member at the start of a line.
    pat = re.compile(r'^(?P<pre>\s*)"' + re.escape(key) + r'"\s*:\s*"(?:[^"\\]|\\.)*"(?P<post>,?)\s*$',
                     re.MULTILINE)
    m = pat.search(text)
    if m:
        new_line = f'{m.group("pre")}"{key}": {esc(value)}{m.group("post")}'
        return text[:m.start()] + new_line + text[m.end():], "updated"

    # Not present -> insert before the final closing brace of the object.
    idx = text.rstrip().rfind("}")
    if idx < 0:
        raise SystemExit(f"[FAIL] {key}: no JSON object found")
    head = text[:idx].rstrip()
    tail = text[idx:]
    if head.endswith(","):
        insert_at = idx
        prefix = ""
    elif head.endswith("{"):
        insert_at = idx
        prefix = ""
    else:
        insert_at = idx
        prefix = ","
    new_line = f'{prefix}\n  "{key}": {esc(value)}\n'
    return text[:insert_at] + new_line + text[insert_at:], "added"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("patch", help="JSON file: {key: {lang: value}}")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    patch = json.loads(Path(args.patch).read_text(encoding="utf-8"))
    if not isinstance(patch, dict) or not patch:
        raise SystemExit("[FAIL] patch file must be a non-empty object")

    # Validate the patch shape BEFORE touching anything.
    problems = []
    for key, values in patch.items():
        if not isinstance(values, dict):
            problems.append(f"{key}: value must be an object of lang -> text")
            continue
        missing = [l for l in LANGS if l not in values]
        extra = [l for l in values if l not in LANGS]
        if missing:
            problems.append(f"{key}: missing languages {missing}")
        if extra:
            problems.append(f"{key}: unknown languages {extra}")
        # A key is <namespace>.<segment>...<segment>.<hash>. The namespace
        # is the first TWO dotted segments (see namespaceOf() in
        # functions/_lib/i18n-shards.js), so the key must have at least three
        # segments. Middle segments are camelCase in the existing dictionary
        # (tools.copy.noSupportedFiles.zzzzzz19c5), so they are not
        # restricted to lowercase.
        #
        # Hyphens are allowed in a segment because the per-tool namespace is
        # the tool's SLUG, and a slug contains hyphens:
        # tools.wedding-seating-chart-maker.td_text.<name>.<hash>.
        if not re.match(r"^[a-z][a-zA-Z0-9_-]*(\.[a-zA-Z0-9_-]+){2,}$", key):
            problems.append(f"{key}: key must be namespace.segment.segment (camelCase and hyphens allowed)")
    if problems:
        raise SystemExit("[FAIL] patch validation:\n  " + "\n  ".join(problems))

    for lang in LANGS:
        path = I18N_DIR / f"{lang}.json"
        if not path.exists():
            raise SystemExit(f"[FAIL] missing dictionary: {path}")
        original = path.read_text(encoding="utf-8")
        text = original
        actions = []
        for key, values in patch.items():
            text, action = apply_key(text, key, values[lang])
            actions.append(action)
        # Validate before writing.
        try:
            json.loads(text)
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(f"[FAIL] {lang}.json would become invalid JSON: {exc}")

        added = actions.count("added")
        updated = actions.count("updated")
        if added == 0 and updated == 0:
            print(f"  {lang}: no change")
            continue
        if args.dry_run:
            print(f"  {lang}: would add {added}, update {updated}")
            continue
        write_atomic(path, text)
        # Re-read and re-validate what actually landed on disk.
        check = json.loads(path.read_text(encoding="utf-8"))
        for key, values in patch.items():
            if key not in check:
                raise SystemExit(f"[FAIL] {lang}.json: key {key} missing after write")
            if check[key] != values[lang]:
                raise SystemExit(f"[FAIL] {lang}.json: key {key} has the wrong value after write")
        print(f"  {lang}: added {added}, updated {updated}")

    if not args.dry_run:
        print("\nNow run for every language:")
        print("  python scripts/add-shards-for-keys.py i18n/<lang>.json i18n/<lang>.manifest.json")
        print("  python scripts/verify-i18n-shards.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
