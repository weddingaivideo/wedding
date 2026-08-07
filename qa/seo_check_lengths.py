#!/usr/bin/env python3
"""检查 i18n 文件中所有 title 和 meta_description 的字符长度。

Limits: title < 60, description < 160 (Google SEO recommendations, including punctuation).
"""
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
I18N_DIR = ROOT / "i18n"

TITLE_MAX = 60
DESC_MAX = 160

LANGS = ["en", "zh", "es", "fr", "de", "ja", "pt", "ar", "ru", "th"]


def main():
    print(f"Checking i18n files in: {I18N_DIR}")
    print(f"Languages: {', '.join(LANGS)}")
    print(f"Limits: title < {TITLE_MAX}, description < {DESC_MAX}")
    print("=" * 100)

    violations = []
    total_titles = 0
    total_descs = 0
    empty_titles = 0
    empty_desc_count = 0

    for lang in LANGS:
        f = I18N_DIR / f"{lang}.json"
        if not f.exists():
            print(f"  ⚠️ Missing file: {f.name}")
            continue
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON error in {f.name}: {e}")
            continue

        for k, v in data.items():
            if ".title_text." in k:
                total_titles += 1
                if not v:
                    empty_titles += 1
                    continue
                if len(v) > TITLE_MAX:
                    violations.append((lang, "title", k, len(v), v))
            elif ".meta_description." in k:
                total_descs += 1
                if not v:
                    empty_desc_count += 1
                    continue
                if len(v) > DESC_MAX:
                    violations.append((lang, "desc", k, len(v), v))

    print(f"\nTotal: {total_titles} titles, {total_descs} descriptions across {len(LANGS)} languages")
    print(f"Empty titles: {empty_titles}, empty descriptions: {empty_desc_count}")
    print()

    if not violations:
        print("✅ All titles and descriptions are within limits!")
        return 0

    print(f"❌ Found {len(violations)} violations")
    for lang, type_, k, L, v in violations[:50]:
        print(f"  [{lang}] {type_} [{L}]: {k}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
