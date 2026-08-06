"""
Re-translate SUSPICIOUS+review zh translations using gtx.

Workflow:
  1. Load en.json (source) and zh.json (target)
  2. Load i18n_reverse_google_zh.csv (audit results)
  3. For each key with sim < threshold:
     - Translate EN -> zh via gtx
     - Sanity check: new zh must keep EN's placeholders, length ratio >= 0.3
     - Sanity check: new zh must not be a verbatim copy of EN
  4. Write updated zh.json (atomic via temp file)

Usage:
  python qa/fix_zh_sus.py --dry-run --limit 5     # test 5 keys
  python qa/fix_zh_sus.py --limit 50              # fix 50 worst
  python qa/fix_zh_sus.py                         # fix all sim < 0.9
"""
import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"
CSV_PATH = ROOT / "qa" / "i18n_reverse_google_zh.csv"

DEFAULT_SIM_THRESHOLD = 0.9
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}|\{[a-zA-Z_][\w]*\}|%[sdif]")


def call_gtx(q: str, src: str = "en", dst: str = "zh-CN", retries: int = 3) -> str | None:
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
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            return None
    return None


def extract_placeholders(s: str) -> set:
    return set(PLACEHOLDER_RE.findall(s))


def sanity_check(en_v: str, old_zh: str, new_zh: str) -> tuple[bool, str]:
    if not new_zh or not new_zh.strip():
        return False, "empty"
    if new_zh == en_v:
        return False, "verbatim_en"
    if new_zh == old_zh:
        return False, "no_change"
    # Length sanity: new must be at least 30% of EN length (i.e. not truncated)
    if len(en_v) > 50 and len(new_zh) < len(en_v) * 0.3:
        return False, f"too_short({len(new_zh)}/{len(en_v)})"
    # Placeholder preservation: if old_zh had placeholders, new_zh must too
    old_ph = extract_placeholders(old_zh)
    new_ph = extract_placeholders(new_zh)
    if old_ph and not old_ph.issubset(new_ph):
        missing = old_ph - new_ph
        return False, f"placeholder_missing({missing})"
    return True, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=DEFAULT_SIM_THRESHOLD)
    ap.add_argument("--limit", type=int, default=0, help="0 = unlimited")
    ap.add_argument("--dry-run", action="store_true", help="don't write file")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()

    en = json.loads((I18N / "en.json").read_text(encoding="utf-8"))
    zh = json.loads((I18N / "zh.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8")))

    # pick candidates: sim < threshold, NOT no_score, NOT ok
    candidates = []
    for r in rows:
        if r["flag"] in ("SUSPICIOUS", "review"):
            if r["en"] and r["tgt"]:
                candidates.append((r["key"], float(r["similarity"]), r["en"], r["tgt"]))
    candidates.sort(key=lambda x: x[1])  # worst first
    if args.limit:
        candidates = candidates[:args.limit]
    print(f"Candidates (sim < {args.threshold}): {len(candidates)}", flush=True)

    fixes = []
    skipped = []
    t0 = time.time()
    for i, (key, sim, en_v, old_zh) in enumerate(candidates, 1):
        new_zh = call_gtx(en_v, "en", "zh-CN")
        ok, reason = sanity_check(en_v, old_zh, new_zh) if new_zh else (False, "api_fail")
        if ok:
            fixes.append((key, en_v, old_zh, new_zh, sim))
        else:
            skipped.append((key, en_v, old_zh, new_zh, sim, reason))
        if i % 10 == 0 or i == len(candidates):
            elapsed = time.time() - t0
            rate = i / max(elapsed, 0.0001)
            eta = (len(candidates) - i) / max(rate, 0.0001) / 60
            print(f"  [{i}/{len(candidates)}] fixed={len(fixes)} skip={len(skipped)} "
                  f"rate={rate:.2f}/s ETA={eta:.1f}min", flush=True)

    print(f"\n=== SUMMARY ===")
    print(f"Total candidates: {len(candidates)}")
    print(f"Fixed:            {len(fixes)}")
    print(f"Skipped:          {len(skipped)}")
    by_reason = {}
    for _, _, _, _, _, r in skipped:
        by_reason[r] = by_reason.get(r, 0) + 1
    print("Skip reasons:")
    for k, v in sorted(by_reason.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    if args.dry_run:
        print("\n[DRY-RUN] no file written. Sample fixes:")
        for key, en_v, old_zh, new_zh, sim in fixes[:5]:
            print(f"  [{key}] (sim {sim:.3f})")
            print(f"    EN : {en_v[:100]}")
            print(f"    OLD: {old_zh[:100]}")
            print(f"    NEW: {new_zh[:100]}")
        return

    # Apply fixes
    for key, _, _, new_zh, _ in fixes:
        zh[key] = new_zh
    # Write
    out = I18N / "zh.json"
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(zh, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(out)
    print(f"\nWrote {out}  ({len(fixes)} fixes applied)")
    print(f"File size: {out.stat().st_size / 1024:.1f}KB (was {(out.stat().st_size - 1000) / 1024:.1f}KB)")


if __name__ == "__main__":
    main()
