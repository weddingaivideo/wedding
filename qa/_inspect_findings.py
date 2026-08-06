"""Inspect audit findings for a few languages — sample by issue type."""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["zh", "ja", "es", "de", "th"]

for code in LANGS:
    p = ROOT / "qa" / f"i18n_audit_{code}.csv"
    with open(p, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by_kind = defaultdict(list)
    for r in rows:
        kind = r["issue"].split("(")[0]
        by_kind[kind].append(r)

    print(f"\n========== {code} ==========")
    for kind, items in by_kind.items():
        n = len(items)
        print(f"\n--- {kind}: {n} ---")
        for r in items[:3]:
            en = r["en"].replace("\n", " ")[:90]
            tgt = r["tgt"].replace("\n", " ")[:90]
            print(f"  [{r['key']}]")
            print(f"    EN: {en}")
            print(f"    {code.upper()}: {tgt}")
