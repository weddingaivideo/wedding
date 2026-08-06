"""Rollback the 130 translations marked 'rollback' in v2 validation.

Restores the original (pre-fix) translation for those keys using v1 csv's
old_zh column (since the file backup was lost).
"""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"
V2_CSV = ROOT / "qa" / "i18n_fix_zh_v2_validation.csv"
V1_CSV = ROOT / "qa" / "i18n_fix_zh_validation.csv"

# Build old_zh lookup from v1
v1_old = {}
for r in csv.DictReader(open(V1_CSV, encoding="utf-8")):
    v1_old[r["key"]] = r["old_zh"]

zh_new = json.loads((I18N / "zh.json").read_text(encoding="utf-8"))

rows = list(csv.DictReader(open(V2_CSV, encoding="utf-8")))
counts = Counter()
for r in rows:
    verdict = r["v2_verdict"]
    k = r["key"]
    if verdict == "rollback":
        if k in v1_old:
            zh_new[k] = v1_old[k]
            counts["rolled_back"] += 1
        else:
            counts["key_missing_in_v1"] += 1
    elif verdict == "keep":
        counts["kept"] += 1
    elif verdict == "ambiguous":
        counts["ambiguous_kept"] += 1

# Write back
out = I18N / "zh.json"
tmp = out.with_suffix(".json.tmp")
tmp.write_text(json.dumps(zh_new, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
tmp.replace(out)

print(f"=== ROLLBACK SUMMARY ===")
for k, v in counts.most_common():
    print(f"  {k}: {v}")
print(f"\nWrote {out}")
print(f"New size: {out.stat().st_size / 1024:.1f} KB")
