"""Bucket too_short findings by EN length to gauge real truncation severity."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["zh", "ja", "th", "es", "de", "fr", "pt", "ru", "ar"]

for code in LANGS:
    csv_p = ROOT / "qa" / f"i18n_audit_{code}.csv"
    with open(csv_p, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["issue"].startswith("too_short")]
    buckets = {"short_en<60": [], "mid_60-150": [], "long_>=150": []}
    for r in rows:
        L = len(r["en"])
        if L < 60:
            buckets["short_en<60"].append(r)
        elif L < 150:
            buckets["mid_60-150"].append(r)
        else:
            buckets["long_>=150"].append(r)
    print(f"\n========= {code} too_short={len(rows)} =========")
    for name, items in buckets.items():
        print(f"\n--- {name} (n={len(items)}) ---")
        for r in items[:2]:
            en = r["en"][:140]
            tgt = r["tgt"][:140]
            ratio = len(r["tgt"]) / max(len(r["en"]), 1)
            print(f"  [{r['key']}] ratio={ratio:.2f}")
            print(f"    EN  ({len(r['en'])}c): {en}")
            print(f"    TGT ({len(r['tgt'])}c): {tgt}")
