"""Inspect the 'worse' translations to understand regression pattern."""
import csv
from pathlib import Path

ROOT = Path(".")
rows = list(csv.DictReader(open(ROOT / "qa/i18n_fix_zh_validation.csv", encoding="utf-8")))
worse = [r for r in rows if r["verdict"] == "worse"]
worse.sort(key=lambda r: float(r["new_sim"]) - float(r["old_sim"]))
print(f"Worse count: {len(worse)}")
print()
for r in worse[:10]:
    print(f"  delta={r['delta']}  {r['key']}")
    print(f"    EN  : {r['en']}")
    print(f"    OLD ({r['old_sim']}): {r['old_zh']}")
    print(f"    NEW ({r['new_sim']}): {r['new_zh']}")
    print()
