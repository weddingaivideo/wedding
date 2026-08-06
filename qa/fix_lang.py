"""
Generic language fixer. Parameterized by --lang.

Re-translates sim<0.9 keys in i18n/{lang}.json using gtx.
V1: translate + sanity check, write i18n/{lang}.json (skipping failed checks)
V2: N=3 reverse-translate, decide keep/rollback/ambiguous per key

Usage:
  python qa/fix_lang.py --lang ja --threshold 0.9
  python qa/fix_lang.py --lang ja --phase fix
  python qa/fix_lang.py --lang ja --phase revalidate
  python qa/fix_lang.py --lang ja --phase rollback
"""
import argparse
import csv
import json
import re
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
QA = ROOT / "qa"

LANG_TO_GTX = {
    "zh": "zh-CN", "ja": "ja", "th": "th", "es": "es", "de": "de",
    "fr": "fr", "pt": "pt", "ru": "ru", "ar": "ar",
}

PH_RE = re.compile(r"\{\{[^}]+\}\}|\{[a-zA-Z_][\w]*\}|%[sdif]")


def call_gtx(q, src="en", dst="zh-CN", retries=3):
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


def placeholders(s):
    return set(PH_RE.findall(s))


def sanity_check(en_v, old_t, new_t):
    if not new_t or not new_t.strip():
        return False, "empty"
    if new_t == en_v:
        return False, "verbatim_en"
    if new_t == old_t:
        return False, "no_change"
    if len(en_v) > 50 and len(new_t) < len(en_v) * 0.3:
        return False, f"too_short({len(new_t)}/{len(en_v)})"
    old_ph = placeholders(old_t)
    new_ph = placeholders(new_t)
    if old_ph and not old_ph.issubset(new_ph):
        return False, f"ph_missing({old_ph - new_ph})"
    return True, "ok"


# ---------- Phase 1: fix ----------
def phase_fix(lang, threshold, workers):
    gtx_dst = LANG_TO_GTX[lang]
    en = json.loads((I18N / "en.json").read_text(encoding="utf-8"))
    tgt = json.loads((I18N / f"{lang}.json").read_text(encoding="utf-8"))
    rev_csv = QA / f"i18n_reverse_google_{lang}.csv"
    if not rev_csv.exists():
        print(f"ERROR: {rev_csv} not found. Run i18n_reverse_google.py first.")
        return

    candidates = []
    for r in csv.DictReader(open(rev_csv, encoding="utf-8")):
        if r["flag"] in ("SUSPICIOUS", "review"):
            if r["en"] and r["tgt"]:
                candidates.append((r["key"], float(r["similarity"]), r["en"], r["tgt"]))
    candidates.sort(key=lambda x: x[1])
    print(f"[{lang}] candidates: {len(candidates)}, workers: {workers}", flush=True)

    # Parallel translate
    fixes = []
    skipped = []
    t0 = time.time()

    def translate_one(item):
        k, sim_v, en_v, old_t = item
        new_t = call_gtx(en_v, "en", gtx_dst)
        ok, reason = sanity_check(en_v, old_t, new_t) if new_t else (False, "api_fail")
        if ok:
            return ("fixed", (k, en_v, old_t, new_t, sim_v))
        else:
            return ("skipped", (k, en_v, old_t, new_t, sim_v, reason))

    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(translate_one, c): c for c in candidates}
        for fut in as_completed(futs):
            kind, payload = fut.result()
            if kind == "fixed":
                fixes.append(payload)
            else:
                skipped.append(payload)
            completed += 1
            if completed % 50 == 0 or completed == len(futs):
                elapsed = time.time() - t0
                rate = completed / max(elapsed, 0.0001)
                eta = (len(futs) - completed) / max(rate, 0.0001) / 60
                print(f"  [{completed}/{len(futs)}] fixed={len(fixes)} skip={len(skipped)} "
                      f"rate={rate:.2f}/s ETA={eta:.1f}min", flush=True)

    by_reason = {}
    for _, _, _, _, _, r in skipped:
        by_reason[r] = by_reason.get(r, 0) + 1
    print(f"\n=== FIX SUMMARY ===")
    print(f"Fixed: {len(fixes)}, Skipped: {len(skipped)}")
    for k, v in sorted(by_reason.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    # Save fixes for v2 phase
    v1_path = QA / f"i18n_fix_{lang}_v1.csv"
    with open(v1_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["key", "en", "old_t", "new_t", "old_sim"])
        for k, en_v, old_t, new_t, sim_v in fixes:
            w.writerow([k, en_v, old_t, new_t, f"{sim_v:.3f}"])
    print(f"Wrote {v1_path}")

    # Apply fixes
    for k, _, _, new_t, _ in fixes:
        tgt[k] = new_t
    out = I18N / f"{lang}.json"
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(tgt, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(out)
    print(f"Applied {len(fixes)} fixes to {out}  ({out.stat().st_size/1024:.1f}KB)")


# ---------- Phase 2: revalidate (N=3) ----------
def phase_revalidate(lang, samples, workers):
    gtx_src = LANG_TO_GTX[lang]
    v1_path = QA / f"i18n_fix_{lang}_v1.csv"
    if not v1_path.exists():
        print(f"ERROR: {v1_path} not found. Run --phase fix first.")
        return

    en = json.loads((I18N / "en.json").read_text(encoding="utf-8"))
    tgt = json.loads((I18N / f"{lang}.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader(open(v1_path, encoding="utf-8")))
    print(f"[{lang}] revalidating {len(rows)} keys with N={samples}...", flush=True)

    out_csv = QA / f"i18n_fix_{lang}_v2.csv"
    out_rows = []

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {}
        for r in rows:
            k = r["key"]
            new_t = r["new_t"]
            if not new_t or not tgt.get(k):
                continue
            futs[ex.submit(_multi_back, new_t, gtx_src, samples)] = r
        for i, fut in enumerate(as_completed(futs), 1):
            r = futs[fut]
            try:
                backs = fut.result()
            except Exception:
                backs = []
            en_v = en.get(r["key"], "")
            sims = [sim(en_v, b) for b in backs]
            sim_max = max(sims) if sims else 0
            sim_med = statistics.median(sims) if sims else 0
            sim_avg = sum(sims) / max(len(sims), 1)
            old_sim = float(r["old_sim"])
            out_rows.append({
                "key": r["key"], "en": r["en"], "old_t": r["old_t"],
                "new_t": r["new_t"], "old_sim": old_sim,
                "v2_sim_max": sim_max, "v2_sim_med": sim_med,
                "v2_sim_avg": sim_avg, "v2_n": len(backs),
            })
            if i % 50 == 0 or i == len(futs):
                print(f"  [{i}/{len(futs)}] done", flush=True)

    # Decide verdict
    for r in out_rows:
        med = r["v2_sim_med"]
        old = r["old_sim"]
        if med >= old - 0.05:
            r["v2_verdict"] = "keep"
        elif med < old - 0.15:
            r["v2_verdict"] = "rollback"
        else:
            r["v2_verdict"] = "ambiguous"

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    from collections import Counter
    counts = Counter(r["v2_verdict"] for r in out_rows)
    print(f"=== V2 VERDICT ===")
    for v, c in counts.most_common():
        print(f"  {v}: {c}")
    print(f"Wrote {out_csv}")


def _multi_back(q, src, n):
    backs = []
    for _ in range(n):
        b = call_gtx(q, src, "en")
        if b and len(b) > 5:
            backs.append(b)
    return backs


# ---------- Phase 3: rollback ----------
def phase_rollback(lang):
    v2_path = QA / f"i18n_fix_{lang}_v2.csv"
    v1_path = QA / f"i18n_fix_{lang}_v1.csv"
    if not v2_path.exists() or not v1_path.exists():
        print(f"ERROR: {v2_path} or {v1_path} not found")
        return

    v1_old = {r["key"]: r["old_t"] for r in csv.DictReader(open(v1_path, encoding="utf-8"))}
    tgt = json.loads((I18N / f"{lang}.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader(open(v2_path, encoding="utf-8")))

    counts = {"rolled_back": 0, "kept": 0, "ambiguous_kept": 0, "key_missing": 0}
    for r in rows:
        v = r["v2_verdict"]
        k = r["key"]
        if v == "rollback":
            if k in v1_old:
                tgt[k] = v1_old[k]
                counts["rolled_back"] += 1
            else:
                counts["key_missing"] += 1
        elif v == "keep":
            counts["kept"] += 1
        elif v == "ambiguous":
            counts["ambiguous_kept"] += 1

    out = I18N / f"{lang}.json"
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(tgt, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(out)
    print(f"=== ROLLBACK {lang} ===")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"Wrote {out}  ({out.stat().st_size/1024:.1f}KB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True, choices=list(LANG_TO_GTX.keys()))
    ap.add_argument("--phase", default="fix", choices=["fix", "revalidate", "rollback"])
    ap.add_argument("--threshold", type=float, default=0.9)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--samples", type=int, default=3)
    args = ap.parse_args()

    if args.phase == "fix":
        phase_fix(args.lang, args.threshold, args.workers)
    elif args.phase == "revalidate":
        phase_revalidate(args.lang, args.samples, args.workers)
    elif args.phase == "rollback":
        phase_rollback(args.lang)


if __name__ == "__main__":
    main()
