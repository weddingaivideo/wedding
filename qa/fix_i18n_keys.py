"""
Fix i18n key coverage: extract English source text from HTML for missing keys,
add them to all language JSON files, and clean up orphan keys.

Also fixes the "key" literal typo in private/architecture.html.

Usage: python qa/fix_i18n_keys.py
"""
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
I18N_DIR = ROOT / "i18n"

SKIP_DIRS = {"tmp", ".git", "__pycache__", "node_modules", "qa", "internal-tools", "tools", ".github", "scripts"}


def extract_keys_with_text(filepath: Path) -> dict:
    """Extract i18n keys with their English source text from an HTML file."""
    result = {}
    try:
        text = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return result

    # data-i18n="key">English text</tag>
    for m in re.finditer(r'data-i18n="([^"]+)"[^>]*>([^<]*)', text):
        key = m.group(1)
        en_text = m.group(2).strip()
        if en_text and key not in result:
            result[key] = en_text

    # data-i18n-attr="attrName:key|attrName2:key2"
    for m in re.finditer(r'<[^>]*\bdata-i18n-attr="([^"]+)"[^>]*>', text):
        opening_tag = m.group(0)
        spec = m.group(1)
        for part in spec.split("|"):
            colon_idx = part.index(":") if ":" in part else -1
            if colon_idx <= 0:
                continue
            attr_name = part[:colon_idx]
            key = part[colon_idx + 1:]
            if not key:
                continue
            # Extract the English value from the attribute
            attr_pattern = rf'{attr_name}="([^"]*)"'
            attr_match = re.search(attr_pattern, opening_tag)
            if attr_match and key not in result:
                result[key] = attr_match.group(1)

    return result


def collect_all_keys_and_text() -> tuple:
    """Walk all HTML files and collect keys with their English source text."""
    file_keys = {}
    all_keys_text = {}
    for html_file in ROOT.rglob("**/*.html"):
        parts = set(html_file.relative_to(ROOT).parts)
        if parts & SKIP_DIRS:
            continue
        kv = extract_keys_with_text(html_file)
        if kv:
            rel = str(html_file.relative_to(ROOT))
            file_keys[rel] = set(kv.keys())
            all_keys_text.update(kv)
    return file_keys, all_keys_text


def load_json(lang: str) -> dict:
    """Load a language JSON file, returns empty dict if not found."""
    json_path = I18N_DIR / f"{lang}.json"
    if not json_path.exists():
        return {}
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def save_json(lang: str, data: dict):
    """Save a language JSON file with sorted keys."""
    json_path = I18N_DIR / f"{lang}.json"
    # Sort keys for diff-friendliness
    sorted_data = dict(sorted(data.items()))
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def fix_typo_in_architecture_html():
    """Fix the 'key' literal in private/architecture.html."""
    arch_path = ROOT / "private" / "architecture.html"
    if not arch_path.exists():
        return
    text = arch_path.read_text(encoding="utf-8", errors="ignore")
    if 'data-i18n="key"' in text:
        # Replace with a proper key
        text = text.replace('data-i18n="key"', 'data-i18n="architecture.key_placeholder.00000001"')
        arch_path.write_text(text, encoding="utf-8")
        print(f"  FIXED: {arch_path} — replaced 'key' with proper i18n key")
        return True
    return False


def main():
    print("=" * 70)
    print("WeddingAI.video — i18n Key Fixer")
    print("=" * 70)

    # Step 1: Collect all keys with English source text
    print("\n[1] Extracting English source text from HTML...")
    file_keys, all_keys_text = collect_all_keys_and_text()
    all_html_keys = set(all_keys_text.keys())
    print(f"    Extracted {len(all_keys_text)} keys with source text")

    # Report keys without source text (only the "key" typo or truly empty elements)
    missing_text = all_html_keys - set(all_keys_text.keys())
    if missing_text:
        print(f"    WARNING: {len(missing_text)} keys have no extractable English text:")
        for k in sorted(missing_text):
            print(f"      {k}")
            # Try to find which files
            for f, fk in file_keys.items():
                if k in fk:
                    print(f"        → {f}")

    # Step 2: Load each language's JSON
    print("\n[2] Loading language JSON files...")
    lang_data = {}
    for json_file in sorted(I18N_DIR.glob("*.json")):
        lang = json_file.stem
        data = load_json(lang)
        lang_data[lang] = data
        print(f"    {lang}: {len(data)} keys")

    # Step 3: Fix typo in architecture.html
    print("\n[3] Fixing 'key' typo in private/architecture.html...")
    fixed_typo = fix_typo_in_architecture_html()
    if not fixed_typo:
        print("    No typo found (already fixed, or file doesn't exist)")

    # Step 4: Add missing keys to each non-English language
    print("\n[4] Adding missing keys with English fallback text...")
    stats = {}
    for lang in sorted(lang_data.keys()):
        if lang == "en":
            continue
        data = lang_data[lang]
        existing = set(data.keys())
        missing_keys = all_html_keys - existing
        added = 0
        for key in sorted(missing_keys):
            en_text = all_keys_text.get(key, "[MISSING]")
            data[key] = en_text
            added += 1

        stats[lang] = {"added": added, "existing_before": len(existing)}

        if added > 0:
            print(f"    {lang}: +{added} keys (English fallback)")
            # Show a few examples
            for k in sorted(missing_keys)[:3]:
                print(f"      {k} → \"{all_keys_text.get(k, '?')[:60]}\"")
            if len(missing_keys) > 3:
                print(f"      ... and {len(missing_keys) - 3} more")

        # Step 5: Remove orphan keys (in JSON but NOT in HTML)
        orphan_keys = existing - all_html_keys
        if orphan_keys:
            print(f"    {lang}: -{len(orphan_keys)} orphan keys removed")
            for key in list(data.keys()):
                if key in orphan_keys:
                    del data[key]

        # Save
        save_json(lang, data)
        lang_data[lang] = data

    # Also clean up en.json orphan keys
    en_data = lang_data.get("en", {})
    en_orphan = set(en_data.keys()) - all_html_keys
    if en_orphan:
        print(f"\n    en: -{len(en_orphan)} orphan keys removed")
        for key in list(en_data.keys()):
            if key in en_orphan:
                del en_data[key]
        save_json("en", en_data)

    # Step 6: Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total_added = 0
    total_removed = 0
    for lang in sorted(lang_data.keys()):
        if lang == "en":
            orphan = stats.get("en_orphan", len(en_orphan))
            print(f"  en: cleaned {orphan} orphan keys")
            total_removed += orphan
            continue
        s = stats[lang]
        total_added += s["added"]
        new_count = len(lang_data[lang])
        coverage = len(set(lang_data[lang].keys()) & all_html_keys) / len(all_html_keys) * 100 if all_html_keys else 0
        print(f"  {lang}: +{s['added']} keys added | {new_count} total | coverage={coverage:.1f}%")

    print(f"\n  Total keys added:    {total_added}")
    print(f"  Total orphan removed: {total_removed}")
    print(f"  Typo fixed:           {'yes' if fixed_typo else 'no'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
