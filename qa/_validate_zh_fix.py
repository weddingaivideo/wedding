"""Re-validate the 964 fixed zh translations by reverse-translating them
and comparing similarity to EN.

This shows how much the fix actually improved each translation.
We re-translate only the keys in the backup diff (not all 6534) to be fast.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"
CSV = ROOT / "qa" / "i18n_reverse_google_zh.csv"
OUT = ROOT / "qa" / "i18n_fix_zh_validation.csv"


def call_gtx(q, src="zh-CN", dst="en", retries=3):
    if not q or not q.strip():
        return q
    for attempt in range(retries):
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {"client": "gtx", "sl": src, "tl": dst, "dt": "t", "q": q}
            full = url + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(full, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
            j = json.loads(raw)
            if j and j[0]:
                parts = [seg[0] for seg in j[0] if seg and seg[0]]
                return "".join(parts) if parts else None
            return None
        except Exception:
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            return None
    return None


def normalize(s):
    return "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in s)


def sim(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def main():
    en = json.loads((I18N / "en.json").read_text(encoding="utf-8"))
    zh_new = json.loads((I18N / "zh.json").read_text(encoding="utf-8"))
    zh_old = json.loads((I18N / "zh.json.bak.pre-fix").read_text(encoding="utf-8"))

    # Read the old audit results
    old_rows = {}
    import csv
    for r in csv.DictReader(open(CSV, encoding="utf-8")):
        old_rows[r["key"]] = r

    # Keys that actually changed
    changed = [k for k in zh_new if k in zh_old and zh_new.get(k) != zh_old.get(k) and k != "_meta"]
    print(f"Changed keys: {len(changed)}")
    if not changed:
        return

    # Re-validate only changed keys
    import csv as _csv
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = _csv.writer(f)
        w.writerow(["key", "en", "old_zh", "old_sim", "new_zh", "new_sim", "delta", "verdict"])
        old_total = 0.0
        new_total = 0.0
        for i, k in enumerate(changed, 1):
            en_v = en.get(k, "")
            old_zh = zh_old.get(k, "")
            new_zh = zh_new.get(k, "")
            old_sim = float(old_rows.get(k, {}).get("similarity") or 0)
            new_back = call_gtx(new_zh, "zh-CN", "en")
            new_sim = sim(en_v, new_back) if new_back else 0
            delta = new_sim - old_sim
            old_total += old_sim
            new_total += new_sim
            if new_sim >= 0.85:
                verdict = "fixed"
            elif new_sim > old_sim + 0.1:
                verdict = "improved"
            elif abs(new_sim - old_sim) <= 0.1:
                verdict = "no_change"
            else:
                verdict = "worse"
            w.writerow([k, en_v[:80], old_zh[:80], f"{old_sim:.3f}",
                        new_zh[:80], f"{new_sim:.3f}",
                        f"{delta:+.3f}", verdict])
            if i % 50 == 0 or i == len(changed):
                print(f"  [{i}/{len(changed)}] avg old={old_total/i:.3f} avg new={new_total/i:.3f}",
                      flush=True)

    # Final summary
    import csv as _csv
    rows = list(_csv.DictReader(open(OUT, encoding="utf-8")))
    from collections import Counter
    verdicts = Counter(r["verdict"] for r in rows)
    print(f"\n=== RE-VALIDATION SUMMARY ===")
    for v, c in verdicts.most_common():
        print(f"  {v}: {c}")
    avg_old = sum(float(r["old_sim"]) for r in rows) / max(len(rows), 1)
    avg_new = sum(float(r["new_sim"]) for r in rows) / max(len(rows), 1)
    print(f"  Avg old sim: {avg_old:.3f}")
    print(f"  Avg new sim: {avg_new:.3f}")
    print(f"  Avg delta:   {avg_new - avg_old:+.3f}")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
