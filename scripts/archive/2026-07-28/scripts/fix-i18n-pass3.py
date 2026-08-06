#!/usr/bin/env python3
"""
B10: Add 3 missing i18n keys (NEW001, NEW002, NEW003) to 9 non-English JSON files.
For now, copy the English text — proper translations can be done later.
"""
import json
from pathlib import Path

I18N = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai\i18n")
EN = I18N / "en.json"

en = json.loads(EN.read_text(encoding="utf-8"))
KEYS_TO_PROPAGATE = {
    "index.p_text.mike_rachel_first_dance_slow_motion.NEW003": en["index.p_text.mike_rachel_first_dance_slow_motion.NEW003"],
    "index.h2_text.real_weddings_real_stories.NEW001": en["index.h2_text.real_weddings_real_stories.NEW001"],
    "index.p_text.real_weddings_intro.NEW002": en["index.p_text.real_weddings_intro.NEW002"],
}

added = 0
for path in I18N.glob("*.json"):
    if path.name == "en.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    for k, v in KEYS_TO_PROPAGATE.items():
        if k not in data:
            data[k] = v
            added += 1
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=1, separators=(",", ": ")),
        encoding="utf-8",
        newline="\n",
    )

print(f"Added {added} keys across non-English JSONs")
