"""
i18n reverse-translation audit via Baidu Translate API.

For each (lang, key) in {zh, ja, th, es, de, fr, pt, ru, ar}:
  1. Load translation value V from i18n/{lang}.json
  2. Call Baidu API to translate V from {lang} to English
  3. Compute similarity between back-translated E' and original EN
  4. If similarity < threshold, mark as suspicious

Similarity = SequenceMatcher ratio on lowercased alphanumeric tokens.

Output:
  - qa/.baidu_reverse_cache.json     — raw cache, persisted after every batch
  - qa/i18n_reverse_{lang}.csv       — full per-key audit results
  - qa/REPORT_I18N_REVERSE.md        — summary report

Resume-safe: any key already in the cache is skipped on re-run.
Rate-limited: configurable QPS (default 1) via simple sleep between calls.
"""
import argparse
import csv
import hashlib
import json
import random
import string
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"
QA = ROOT / "qa"
CACHE = QA / ".baidu_reverse_cache.json"

APPID = "20260728002654885"
SECRET = "yoUb_d9kaju0hciln8mqrjqqg"
ENDPOINT = "https://fanyi-api.baidu.com/api/trans/vip/translate"

LANGS = {
    "zh": "zh", "ja": "jp", "th": "th", "es": "es", "de": "de",
    "fr": "fr", "pt": "pt", "ru": "ru", "ar": "ara",
}

# Threshold: similarity below this is flagged suspicious.
THRESHOLD_DEFAULT = 0.65
# Very short strings are not meaningful to score.
MIN_LEN_FOR_SIM = 12


def load_cache() -> dict:
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_cache(c: dict) -> None:
    tmp = CACHE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CACHE)


def normalize(s: str) -> str:
    """Lowercase + keep alphanumerics + spaces."""
    return "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in s)


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


_last_call = 0.0


def call_baidu(q: str, src: str, dst: str = "en", qps: float = 1.0, retries: int = 3) -> str | None:
    """Call Baidu translate. Returns translated string or None on failure."""
    global _last_call
    if not q or not q.strip():
        return q
    # rate limit
    wait = 1.0 / max(qps, 0.1) if qps else 0
    elapsed = time.time() - _last_call
    if elapsed < wait:
        time.sleep(wait - elapsed)
    _last_call = time.time()

    for attempt in range(retries):
        salt = "".join(random.choices(string.ascii_letters + string.digits, k=10))
        sign_src = APPID + q + salt + SECRET
        sign = hashlib.md5(sign_src.encode("utf-8")).hexdigest()
        params = {"q": q, "from": src, "to": dst, "appid": APPID, "salt": salt, "sign": sign}
        url = ENDPOINT + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "WeddingAI-i18n-audit/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8")
            j = json.loads(body)
            if "trans_result" in j and j["trans_result"]:
                return j["trans_result"][0]["dst"]
            # error
            err = j.get("error_code", "")
            if err in ("54003", "54005"):  # rate-limited / long query too frequent
                time.sleep(2 * (attempt + 1))
                continue
            if err == "54001":
                # sign invalid — likely IP whitelist; bail
                return f"__ERR_54001__"
            # any other error: log and return None
            print(f"      [err] {err} {j.get('error_msg','')} q={q[:40]!r}", file=sys.stderr)
            return None
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < retries - 1:
                time.sleep(1.0 * (attempt + 1))
                continue
            print(f"      [net] {type(e).__name__}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"      [exc] {type(e).__name__}: {e}", file=sys.stderr)
            return None
    return None


def audit_lang(code: str, en: dict, tgt: dict, qps: float, threshold: float) -> list:
    """Return list of (key, en_v, tgt_v, back_v, sim) tuples for one language."""
    cache = load_cache()
    lang_cache_key = f"lang:{code}"
    done = cache.get(lang_cache_key, {})

    baidu_src = LANGS[code]
    items = []
    todo = []
    for k in en:
        if k == "_meta":
            continue
        en_v = en[k]
        if not isinstance(en_v, str):
            continue
        if k in done:
            items.append((k, en_v, tgt.get(k, ""), done[k]["back"], done[k]["sim"]))
            continue
        tgt_v = tgt.get(k)
        if not isinstance(tgt_v, str) or not tgt_v.strip():
            continue
        todo.append((k, en_v, tgt_v))

    print(f"\n[{code}] total={len(en)-1}  cached={len(done)}  todo={len(todo)}", flush=True)

    SAVE_EVERY = 50
    t0 = time.time()
    for i, (k, en_v, tgt_v) in enumerate(todo, 1):
        if len(tgt_v) < MIN_LEN_FOR_SIM or len(en_v) < MIN_LEN_FOR_SIM:
            # Too short to score meaningfully; record as N/A but don't translate.
            done[k] = {"back": "", "sim": None}
            items.append((k, en_v, tgt_v, "", None))
        else:
            back = call_baidu(tgt_v, baidu_src, "en", qps=qps)
            if back == "__ERR_54001__":
                print(f"\n  [{code}] Bail: 54001 Invalid Sign — likely IP whitelist", flush=True)
                cache[lang_cache_key] = done
                save_cache(cache)
                return items
            if back is None:
                # fail to translate; record no score
                done[k] = {"back": None, "sim": None}
                items.append((k, en_v, tgt_v, None, None))
            else:
                sim = similarity(en_v, back)
                done[k] = {"back": back, "sim": sim}
                items.append((k, en_v, tgt_v, back, sim))
        if i % SAVE_EVERY == 0:
            cache[lang_cache_key] = done
            save_cache(cache)
            rate = i / (time.time() - t0)
            eta = (len(todo) - i) / max(rate, 0.0001) / 60
            sus = sum(1 for it in items if it[4] is not None and it[4] < threshold)
            print(f"    [{code}] {i}/{len(todo)}  rate={rate:.2f}/s  ETA={eta:.1f}min  suspicious={sus}",
                  flush=True)
    cache[lang_cache_key] = done
    save_cache(cache)
    return items


def write_csv(code: str, items: list, threshold: float) -> int:
    """Write per-language CSV. Returns count of suspicious (sim < threshold)."""
    p = QA / f"i18n_reverse_{code}.csv"
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
            w.writerow([k, en_v, tgt_v, back or "", f"{sim:.3f}" if sim is not None else "", flag])
    return sus_count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default="", help="comma-separated, e.g. zh,ja")
    ap.add_argument("--qps", type=float, default=1.0, help="queries per second (default 1)")
    ap.add_argument("--threshold", type=float, default=THRESHOLD_DEFAULT)
    ap.add_argument("--workers", type=int, default=1, help="concurrent API workers (default 1)")
    args = ap.parse_args()

    en = json.loads((I18N / "en.json").read_text(encoding="utf-8"))
    all_langs = list(LANGS.keys())
    if args.langs:
        wanted = set(s.strip() for s in args.langs.split(",") if s.strip())
        langs = [c for c in all_langs if c in wanted]
    else:
        langs = all_langs

    overall_sus = 0
    overall_total_scored = 0
    overall_t0 = time.time()
    for code in langs:
        tgt = json.loads((I18N / f"{code}.json").read_text(encoding="utf-8"))
        items = audit_lang(code, en, tgt, args.qps, args.threshold)
        sus = write_csv(code, items, args.threshold)
        scored = sum(1 for it in items if it[4] is not None)
        overall_sus += sus
        overall_total_scored += scored
        print(f"  [{code}] done: scored={scored}  suspicious={sus}  "
              f"({sus/max(scored,1)*100:.1f}%)", flush=True)
        if any(it[3] is None and it[2] and len(it[2]) >= MIN_LEN_FOR_SIM for it in items):
            # bail signal
            pass

    overall = time.time() - overall_t0
    print(f"\n=== TOTAL: {overall_total_scored} scored, {overall_sus} suspicious "
          f"({overall_sus/max(overall_total_scored,1)*100:.1f}%) in {overall/60:.1f}min ===", flush=True)


if __name__ == "__main__":
    main()
