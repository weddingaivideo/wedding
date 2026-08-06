"""
Check i18n key coverage: extract all data-i18n / data-i18n-attr keys from HTML files,
compare against each language's JSON file, and report missing keys.

Usage: python qa/check_i18n_keys.py
"""
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
I18N_DIR = ROOT / "i18n"

# Directories to skip when scanning HTML
SKIP_DIRS = {"tmp", ".git", "__pycache__", "node_modules", "qa", "internal-tools", "tools", ".github", "scripts"}


def extract_keys_from_html(filepath: Path) -> set:
    """Extract all i18n keys from a single HTML file."""
    keys = set()
    try:
        text = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return keys

    # data-i18n="key"
    for m in re.finditer(r'data-i18n="([^"]+)"', text):
        keys.add(m.group(1))

    # data-i18n-attr="attrName:key|attrName2:key2"
    for m in re.finditer(r'data-i18n-attr="([^"]+)"', text):
        spec = m.group(1)
        for part in spec.split("|"):
            colon_idx = part.index(":") if ":" in part else -1
            if colon_idx > 0:
                key = part[colon_idx + 1:]
                if key:
                    keys.add(key)

    return keys


def collect_all_keys() -> dict:
    """Walk all HTML files and collect keys, grouped by file path."""
    file_keys = {}
    all_keys = set()
    for html_file in ROOT.rglob("**/*.html"):
        # Skip excluded directories
        parts = set(html_file.relative_to(ROOT).parts)
        if parts & SKIP_DIRS:
            continue
        keys = extract_keys_from_html(html_file)
        if keys:
            rel = str(html_file.relative_to(ROOT))
            file_keys[rel] = keys
            all_keys |= keys
    return file_keys, all_keys


def load_json_keys(lang: str) -> set:
    """Load all keys from a language JSON file."""
    json_path = I18N_DIR / f"{lang}.json"
    if not json_path.exists():
        print(f"  WARNING: {json_path} does not exist")
        return set()
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        return set(data.keys())
    except Exception as e:
        print(f"  ERROR loading {json_path}: {e}")
        return set()


def main():
    print("=" * 70)
    print("WeddingAI.video — i18n Key Coverage Check")
    print("=" * 70)

    # Step 1: Collect all keys from HTML
    print("\n[1] Scanning HTML files for i18n keys...")
    file_keys, all_html_keys = collect_all_keys()
    print(f"    Found {len(all_html_keys)} unique keys across {len(file_keys)} HTML files.")

    # Step 2: Load each language's keys
    print("\n[2] Loading translation JSON files...")
    lang_keys = {}
    for json_file in sorted(I18N_DIR.glob("*.json")):
        lang = json_file.stem
        keys = load_json_keys(lang)
        lang_keys[lang] = keys
        print(f"    {lang}: {len(keys)} keys")

    # Step 3: Compare — missing keys per language
    print("\n[3] Missing keys (in HTML but NOT in language JSON):")
    print("-" * 70)
    total_issues = 0
    for lang in sorted(lang_keys.keys()):
        if lang == "en":
            continue  # English is source language, skip
        missing = all_html_keys - lang_keys[lang]
        if missing:
            total_issues += len(missing)
            print(f"\n  {lang} — {len(missing)} missing keys:")
            # Group by page prefix for readability
            by_page = defaultdict(list)
            for k in sorted(missing):
                prefix = k.split(".")[0]
                by_page[prefix].append(k)
            for page, keys in sorted(by_page.items()):
                print(f"    [{page}] ({len(keys)} keys)")
                for k in keys[:10]:  # Show first 10 per page
                    # Show which files use this key
                    files = [f for f, fk in file_keys.items() if k in fk]
                    print(f"      {k}")
                    if len(files) <= 3:
                        for f in files:
                            print(f"        → {f}")
                if len(keys) > 10:
                    print(f"      ... and {len(keys) - 10} more")
        else:
            print(f"  {lang}: ALL KEYS PRESENT")

    if total_issues == 0:
        print("\n  All non-English languages have complete key coverage!")

    # Step 4: Orphan keys (in JSON but NOT in any HTML)
    print("\n[4] Orphan keys (in language JSON but NOT in any HTML):")
    print("-" * 70)
    orphan_total = 0
    for lang in sorted(lang_keys.keys()):
        orphan = lang_keys[lang] - all_html_keys
        if orphan:
            orphan_total += len(orphan)
            print(f"\n  {lang} — {len(orphan)} orphan keys (safe to delete):")
            for k in sorted(orphan)[:20]:
                print(f"    {k}")
            if len(orphan) > 20:
                print(f"    ... and {len(orphan) - 20} more")
    if orphan_total == 0:
        print("  No orphan keys found.")

    # Step 5: Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  HTML key count:          {len(all_html_keys)}")
    for lang in sorted(lang_keys.keys()):
        missing = len(all_html_keys - lang_keys[lang])
        extra = len(lang_keys[lang] - all_html_keys)
        coverage = (len(all_html_keys & lang_keys[lang]) / len(all_html_keys) * 100) if all_html_keys else 0
        print(f"  {lang}: {len(lang_keys[lang])} keys | missing={missing} | orphan={extra} | coverage={coverage:.1f}%")

    print(f"\n  Total missing translations: {total_issues}")
    if total_issues > 0:
        print("  Run with --fix flag to generate stub translations for missing keys.")
        print("  Example stub format: copy English value as placeholder.")

    # Step 6: Also check for keys that exist only in some languages
    print("\n[5] Keys present in some languages but missing in others:")
    print("-" * 70)
    all_langs = sorted(lang_keys.keys())
    for key in sorted(all_html_keys):
        present_in = [l for l in all_langs if key in lang_keys[l]]
        missing_in = [l for l in all_langs if l != "en" and key not in lang_keys[l]]
        if missing_in and len(present_in) < len(all_langs) and len(present_in) > 1:
            print(f"  {key}")
            print(f"    Present: {present_in}")
            print(f"    Missing: {missing_in}")

    return 0 if total_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
