"""
i18n reverse-translation audit via Google translate (gtx endpoint).

For each (lang, key) in {zh, ja, th, es, de, fr, pt, ru, ar}:
  1. Load translation value V from i18n/{lang}.json
  2. Call gtx to translate V from {lang} to English
  3. Compute similarity between back-translated E' and original EN
  4. If similarity < threshold, mark as suspicious

Similarity = SequenceMatcher ratio on lowercased alphanumeric tokens.

Output:
  - qa/.google_reverse_cache.json     — raw cache, persisted after every batch
  - qa/i18n_reverse_google_{lang}.csv — full per-key audit results
  - qa/REPORT_I18N_REVERSE.md         — summary report

Resume-safe: any key already in the cache is skipped on re-run.
Parallel: 8 workers (gtx tolerates ~20 concurrent before throttling).
"""
import argparse
import csv
import json
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
CACHE = QA / ".google_reverse_cache.json"

LANGS = {
    "zh": "zh-CN", "ja": "ja", "th": "th", "es": "es", "de": "de",
    "fr": "fr", "pt": "pt", "ru": "ru", "ar": "ar",
}

THRESHOLD_DEFAULT = 0.65
MIN_LEN_FOR_SIM = 12
WORKERS_DEFAULT = 8


def load_cache() -> dict:
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_cache(c: dict) -> None:
    """Atomic-ish write with retry on Windows file-lock issues."""
    import os
    import time as _t
    for attempt in range(3):
        try:
            data = json.dumps(c, ensure_ascii=False)
            with open(CACHE, "w", encoding="utf-8") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            return
        except (FileNotFoundError, PermissionError, OSError) as e:
            if attempt < 2:
                _t.sleep(1.0 * (attempt + 1))
                continue
            print(f"      [save_cache] failed after 3 retries: {e}", file=__import__('sys').stderr)


def normalize(s: str) -> str:
    return "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in s)


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def call_gtx(q: str, src: str, retries: int = 3) -> str | None:
    """Call Google gtx translate. Returns translated string or None on failure."""
    if not q or not q.strip():
        return q
    for attempt in range(retries):
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": src,
                "tl": "en",
                "dt": "t",
                "q": q,
            }
            full = url + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(
                full,
                headers={"User-Agent": "Mozilla/5.0 (WeddingAI-i18n-audit/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
            j = json.loads(raw)
            if j and j[0]:
                # j[0] is list of [trans_chunk, src, ...]
                parts = [seg[0] for seg in j[0] if seg and seg[0]]
                return "".join(parts) if parts else None
            return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            print(f"      [err] {type(e).__name__}: {str(e)[:100]}", file=sys.stderr)
            return None
    return None


def audit_lang(code: str, en: dict, tgt: dict, workers: int, threshold: float) -> list:
    cache = load_cache()
    lang_cache_key = f"lang:{code}"
    done = cache.get(lang_cache_key, {})

    gtx_src = LANGS[code]
    items = []
    todo = []
    for k in en:
        if k == "_meta":
            continue
        en_v = en[k]
        if not isinstance(en_v, str):
            continue
        if k in done:
            d = done[k]
            items.append((k, en_v, tgt.get(k, ""), d.get("back"), d.get("sim")))
            continue
        tgt_v = tgt.get(k)
        if not isinstance(tgt_v, str) or not tgt_v.strip():
            continue
        todo.append((k, en_v, tgt_v))

    print(f"\n[{code}] total={len(en)-1}  cached={len(done)}  todo={len(todo)}", flush=True)

    SAVE_EVERY = 100
    t0 = time.time()
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {}
        for k, en_v, tgt_v in todo:
            if len(tgt_v) < MIN_LEN_FOR_SIM or len(en_v) < MIN_LEN_FOR_SIM:
                done[k] = {"back": "", "sim": None}
                items.append((k, en_v, tgt_v, "", None))
                continue
            fut = ex.submit(call_gtx, tgt_v, gtx_src)
            futures[fut] = (k, en_v, tgt_v)

        for fut in as_completed(futures):
            k, en_v, tgt_v = futures[fut]
            try:
                back = fut.result()
            except Exception as e:
                back = None
            if back is None:
                done[k] = {"back": None, "sim": None}
                items.append((k, en_v, tgt_v, None, None))
            else:
                sim = similarity(en_v, back)
                done[k] = {"back": back, "sim": sim}
                items.append((k, en_v, tgt_v, back, sim))
            completed += 1
            if completed % SAVE_EVERY == 0 or completed == len(futures):
                cache[lang_cache_key] = done
                save_cache(cache)
                rate = completed / (time.time() - t0)
                eta = (len(todo) - completed) / max(rate, 0.0001) / 60
                sus = sum(1 for it in items if it[4] is not None and it[4] < threshold)
                print(f"    [{code}] {completed}/{len(todo)}  rate={rate:.1f}/s  "
                      f"ETA={eta:.1f}min  suspicious={sus}", flush=True)

    cache[lang_cache_key] = done
    save_cache(cache)
    return items


def write_csv(code: str, items: list, threshold: float) -> int:
    p = QA / f"i18n_reverse_google_{code}.csv"
    sus_count = 0
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["key", "en", "tgt", "back_to_en", "similarity", "flag"])
        for k, en_v, tgt_v, back, sim in items:
            flag = ""
            if sim is None:
                flag = "no_score"
            elif sim < threshold:
                flag = "SUSPICIOUS"
                sus_count += 1
            elif sim >= 0.9:
                flag = "ok"
            else:
                flag = "review"
            w.writerow([k, en_v, tgt_v, back or "",
                        f"{sim:.3f}" if sim is not None else "", flag])
    return sus_count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default="")
    ap.add_argument("--workers", type=int, default=WORKERS_DEFAULT)
    ap.add_argument("--threshold", type=float, default=THRESHOLD_DEFAULT)
    args = ap.parse_args()

    en = json.loads((I18N / "en.json").read_text(encoding="utf-8"))
    all_langs = list(LANGS.keys())
    if args.langs:
        wanted = set(s.strip() for s in args.langs.split(",") if s.strip())
        langs = [c for c in all_langs if c in wanted]
    else:
        langs = all_langs

    overall_sus = 0
    overall_scored = 0
    overall_t0 = time.time()
    for code in langs:
        tgt = json.loads((I18N / f"{code}.json").read_text(encoding="utf-8"))
        items = audit_lang(code, en, tgt, args.workers, args.threshold)
        sus = write_csv(code, items, args.threshold)
        scored = sum(1 for it in items if it[4] is not None)
        overall_sus += sus
        overall_scored += scored
        print(f"  [{code}] done: scored={scored}  suspicious={sus}  "
              f"({sus/max(scored,1)*100:.1f}%)", flush=True)
    overall = time.time() - overall_t0
    print(f"\n=== TOTAL: {overall_scored} scored, {overall_sus} suspicious "
          f"({overall_sus/max(overall_scored,1)*100:.1f}%) in {overall/60:.1f}min ===", flush=True)


if __name__ == "__main__":
    main()
