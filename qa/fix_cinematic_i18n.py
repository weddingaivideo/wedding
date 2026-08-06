"""Fix all truncated 'Won't Tell' in en.json for cinematic-wedding-trailer."""
import json
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
en_path = ROOT / "i18n" / "en.json"
en = json.loads(en_path.read_text(encoding="utf-8"))

updated = 0
for k in list(en.keys()):
    if "cinematic-wedding-trailer" in k and isinstance(en[k], str):
        if "Won't Tell" in en[k] and "You" not in en[k]:
            new_val = en[k].replace("Won't Tell", "Won't Tell You")
            print(f"  {k}")
            print(f"    - {en[k]}")
            print(f"    + {new_val}")
            en[k] = new_val
            updated += 1

en_path.write_text(
    json.dumps(en, ensure_ascii=False, separators=(",", ":")),
    encoding="utf-8",
)
print(f"\nUpdated {updated} keys in en.json")
