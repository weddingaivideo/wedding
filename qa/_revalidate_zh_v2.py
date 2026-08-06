"""Re-validate zh fix with N=3 samples per translation for stability.

For each of the 964 changed keys:
  - Run gtx back-translate 3 times
  - Take the MAX similarity (best-case gtx sample)
  - Take the MEDIAN similarity (typical case)
  - Compare to old sim (single sample)
  - Decide: keep fix if median_new >= old_sim - 0.05 (allow small noise)

Output: qa/i18n_fix_zh_v2_validation.csv with detailed stats.
"""
import csv
import json
import statistics
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"
IN_CSV = ROOT / "qa" / "i18n_fix_zh_validation.csv"
OUT_CSV = ROOT / "qa" / "i18n_fix_zh_v2_validation.csv"

SAMPLES = 3
WORKERS = 4


def call_gtx(q, src="zh-CN", dst="en", retries=2):
    if not q or not q.strip():
        return None
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
                return "".join(seg[0] for seg in j[0] if seg and seg[0])
            return None
        except Exception:
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))
    return None


def normalize(s):
    return "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in s)


def sim(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def multi_sample(q, src, dst, n):
    """Run gtx n times, return list of valid back-translations."""
    results = []
    for _ in range(n):
        b = call_gtx(q, src, dst)
        if b and len(b) > 5:
            results.append(b)
    return results


def main():
    en = json.loads((I18N / "en.json").read_text(encoding="utf-8"))
    zh_new = json.loads((I18N / "zh.json").read_text(encoding="utf-8"))

    # Read v1 validation to get the 964 changed keys
    v1_rows = list(csv.DictReader(open(IN_CSV, encoding="utf-8")))
    keys = [r["key"] for r in v1_rows]
    print(f"Re-validating {len(keys)} keys with N={SAMPLES} samples, workers={WORKERS}...")

    # For each key, run SAMPLES reverse-translates
    t0 = time.time()
    results = {}
    work = []
    skipped = 0
    for k in keys:
        if k not in en or k not in zh_new:
            skipped += 1
            continue
        work.append((k, en[k], zh_new[k]))
    if skipped:
        print(f"  Skipped {skipped} keys (missing in EN or ZH)")

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(multi_sample, zh_new[k], "zh-CN", "en", SAMPLES): k
                for k, _, zh_v in work if zh_v}
        for i, fut in enumerate(as_completed(futs), 1):
            k = futs[fut]
            try:
                backs = fut.result()
            except Exception:
                backs = []
            en_v = en.get(k, "")
            if not en_v:
                continue
            sims = [sim(en_v, b) for b in backs] if backs else []
            sim_max = max(sims) if sims else 0.0
            sim_med = statistics.median(sims) if sims else 0.0
            sim_avg = sum(sims) / len(sims) if sims else 0.0
            results[k] = {
                "backs_n": len(backs),
                "sim_max": sim_max,
                "sim_med": sim_med,
                "sim_avg": sim_avg,
                "best_back": backs[sims.index(sim_max)] if sims else "",
            }
            if i % 50 == 0 or i == len(futs):
                elapsed = time.time() - t0
                rate = i / elapsed
                eta = (len(futs) - i) / max(rate, 0.0001) / 60
                print(f"  [{i}/{len(futs)}] elapsed={elapsed:.0f}s rate={rate:.2f}/s ETA={eta:.1f}min",
                      flush=True)

    # Build output CSV
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["key", "en", "new_zh", "old_sim", "v1_new_sim",
                    "v2_sim_max", "v2_sim_med", "v2_sim_avg", "v2_n",
                    "v2_verdict"])
        counts = {"keep": 0, "rollback": 0, "ambiguous": 0}
        for r in v1_rows:
            k = r["key"]
            v2 = results.get(k, {"sim_max": 0, "sim_med": 0, "sim_avg": 0, "backs_n": 0, "best_back": ""})
            old_sim = float(r["old_sim"])
            v1_sim = float(r["new_sim"])
            sim_med = v2["sim_med"]
            # Decision: keep if v2 median >= old_sim - 0.05 (allow small noise)
            if sim_med >= old_sim - 0.05:
                verdict = "keep"
                counts["keep"] += 1
            elif sim_med < old_sim - 0.15:
                verdict = "rollback"
                counts["rollback"] += 1
            else:
                verdict = "ambiguous"
                counts["ambiguous"] += 1
            w.writerow([k, r["en"], r["new_zh"], f"{old_sim:.3f}",
                        f"{v1_sim:.3f}", f"{v2['sim_max']:.3f}",
                        f"{v2['sim_med']:.3f}", f"{v2['sim_avg']:.3f}",
                        v2["backs_n"], verdict])
    print(f"\n=== V2 VERDICT ===")
    for v, c in counts.items():
        print(f"  {v}: {c}")
    print(f"\nWrote {OUT_CSV}")


if __name__ == "__main__":
    main()
