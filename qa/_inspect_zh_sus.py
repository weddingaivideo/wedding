"""Inspect zh SUSPICIOUS distribution and top offenders."""
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(".")
rows = list(csv.DictReader(open(ROOT / "qa/i18n_reverse_google_zh.csv", encoding="utf-8")))
sus = [r for r in rows if r["flag"] == "SUSPICIOUS"]
print(f"Total SUSPICIOUS: {len(sus)}")
print(f"Total review:     {sum(1 for r in rows if r['flag'] == 'review')}")
print(f"Total ok:         {sum(1 for r in rows if r['flag'] == 'ok')}")
print(f"Total no_score:   {sum(1 for r in rows if r['flag'] == 'no_score')}")
print()

print("Distribution by sim bucket:")
buckets = Counter()
for r in sus:
    s = float(r["similarity"])
    if s < 0.1:
        buckets["<0.1 (severe)"] += 1
    elif s < 0.2:
        buckets["0.1-0.2"] += 1
    elif s < 0.3:
        buckets["0.2-0.3"] += 1
    elif s < 0.4:
        buckets["0.3-0.4"] += 1
    elif s < 0.5:
        buckets["0.4-0.5"] += 1
    else:
        buckets["0.5-0.65"] += 1
for k, v in sorted(buckets.items()):
    print(f"  {k:18s} : {v}")

print()
print("Top 15 worst:")
sus.sort(key=lambda r: float(r["similarity"]))
for r in sus[:15]:
    s = r["similarity"]
    k = r["key"]
    en = r["en"][:90]
    zh = r["tgt"][:90]
    bk = r["back_to_en"][:90]
    print(f"  sim={s}  {k}")
    print(f"    EN  : {en}")
    print(f"    ZH  : {zh}")
    print(f"    back: {bk}")
    print()
