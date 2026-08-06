"""
Identify keys that still have English fallback text (not yet translated)
in each language JSON file.

Usage: python qa/find_untranslated.py
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
I18N_DIR = ROOT / "i18n"

def main():
    # Load en.json as source of truth for English values
    with open(I18N_DIR / "en.json", encoding="utf-8") as f:
        en_data = json.load(f)

    print("Keys with untranslated English fallback:\n")

    for json_file in sorted(I18N_DIR.glob("*.json")):
        lang = json_file.stem
        if lang == "en":
            continue

        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        untranslated = []
        for key, en_val in en_data.items():
            if key in data and data[key] == en_val:
                untranslated.append(key)

        if untranslated:
            print(f"--- {lang} ({len(untranslated)} keys) ---")
            # Group by page
            by_page = defaultdict(list)
            for k in untranslated:
                page = k.split(".")[0]
                by_page[page].append((k, data[k]))

            for page, keys in sorted(by_page.items()):
                for k, v in keys:
                    short = v[:80] + "..." if len(v) > 80 else v
                    print(f"  {page} | {k}")
                    print(f"    EN: {short}")
            print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
