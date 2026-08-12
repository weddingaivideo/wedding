#!/usr/bin/env python3
"""
Cleanup i18n orphan keys.

Problem: zh.json, ja.json, etc. contain keys that don't exist in en.json
(source of truth). These orphan keys:
  - Are never referenced by any HTML's data-i18n="<key>" attribute
  - Bloat the JSON files (e.g. zh.json is 30% larger than en.json)
  - Are a sync bug from earlier i18n translation runs

This script:
  1. Reads en.json keys as the source of truth
  2. For each non-en language, removes any top-level key NOT in en.json
  3. Preserves the original formatting (key order, 2-space indent, CRLF, UTF-8 no-BOM)
  4. Reports before/after stats

Backup: .i18n-backup/ (call before running)
Restore: cp .i18n-backup/*.json i18n/
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
I18N = ROOT / "i18n"
EN_JSON = I18N / "en.json"

LANGS = ["zh", "ja", "ru", "ar", "de", "es", "fr", "pt", "th"]


def load_keys(path: Path) -> list[str]:
    """Load JSON and return top-level keys in order."""
    text = path.read_text(encoding="utf-8")
    obj = json.loads(text)
    return list(obj.keys())


def clean_one(lang: str, en_keys: set[str]) -> tuple[int, int, int, int]:
    """
    Clean one language file.
    Returns (before_count, after_count, removed_count, size_before, size_after).
    """
    path = I18N / f"{lang}.json"
    raw_bytes = path.read_bytes()
    size_before = len(raw_bytes)

    # Detect line ending
    has_crlf = b"\r\n" in raw_bytes
    le = "\r\n" if has_crlf else "\n"

    text = path.read_text(encoding="utf-8")
    obj = json.loads(text)
    keys = list(obj.keys())
    before_count = len(keys)

    # Remove orphans
    new_obj = {k: v for k, v in obj.items() if k in en_keys}
    after_count = len(new_obj)
    removed = before_count - after_count

    # Serialize with same key order, 2-space indent, no ASCII escape
    out = json.dumps(new_obj, indent=2, ensure_ascii=False, separators=(",", ": "))

    # Python json.dumps uses \n; convert to CRLF if original was CRLF
    if has_crlf:
        out = out.replace("\n", "\r\n")

    # Preserve trailing newline if original had one
    if raw_bytes.endswith(b"\n"):
        out += "\r\n" if has_crlf else "\n"

    path.write_text(out, encoding="utf-8", newline="")
    size_after = path.stat().st_size
    return before_count, after_count, removed, size_before, size_after


def main():
    if not EN_JSON.exists():
        print(f"ERROR: {EN_JSON} not found", file=sys.stderr)
        sys.exit(1)

    print(f"=== Loading en.json (source of truth) ===")
    en_keys_list = load_keys(EN_JSON)
    en_keys = set(en_keys_list)
    en_size = EN_JSON.stat().st_size
    print(f"  en.json: {len(en_keys_list)} keys, {en_size:,} bytes")
    print()

    print(f"=== Cleaning {len(LANGS)} non-en languages ===")
    print()
    print(f"  {'lang':<6} {'before':>8} {'after':>8} {'removed':>9} {'size_before':>12} {'size_after':>12} {'savings':>10}")
    print("  " + "-" * 75)

    total_before = 0
    total_after = 0
    total_removed = 0
    total_size_before = 0
    total_size_after = 0

    for lang in LANGS:
        path = I18N / f"{lang}.json"
        if not path.exists():
            print(f"  {lang:<6} (file not found)")
            continue
        before, after, removed, sb, sa = clean_one(lang, en_keys)
        total_before += before
        total_after += after
        total_removed += removed
        total_size_before += sb
        total_size_after += sa
        savings_pct = 100.0 * (sb - sa) / sb if sb else 0
        print(f"  {lang:<6} {before:>8} {after:>8} {removed:>9} {sb:>12,} {sa:>12,} {savings_pct:>9.1f}%")

    print("  " + "-" * 75)
    total_savings_pct = 100.0 * (total_size_before - total_size_after) / total_size_before if total_size_before else 0
    print(f"  {'TOTAL':<6} {total_before:>8} {total_after:>8} {total_removed:>9} {total_size_before:>12,} {total_size_after:>12,} {total_savings_pct:>9.1f}%")
    print()
    print(f"Total orphan keys removed: {total_removed:,}")
    print(f"Total bytes saved: {total_size_before - total_size_after:,} ({total_savings_pct:.1f}%)")
    print(f"Backup at: .i18n-backup/  (restore with: cp .i18n-backup/*.json i18n/)")


if __name__ == "__main__":
    main()
