"""
Fill in the missing 6,182 translations per language.

Differs from i18n_translate.py in three ways:
  1. Idempotent — translates only keys missing from the target file.
     Preserves existing translations (including the 24 critical fixes
     from i18n_fix_critical.py and the original 350-string set).
  2. Full coverage — does not stop at 350. Translates everything in
     en.json that isn't already in the target.
  3. Resumable — partial writes are not done mid-run; if the script
     is killed, simply re-run it; it will pick up where it left off
     (whatever keys have been written so far are skipped next time).

Sister to: i18n_translate.py (which only seeds the initial top-350 set).

Run from project root:
    python scripts/i18n_translate_missing.py

ETA: ~6-8 hours for all 9 languages with 16 workers (Google's
unofficial API tolerates ~20 concurrent requests before throttling).
"""
import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

I18N_DIR = Path("i18n")
EN_FILE = I18N_DIR / "en.json"

TARGETS = {
    "zh": "zh-CN",
    "es": "es",
    "fr": "fr",
    "de": "de",
    "pt": "pt",
    "ja": "ja",
    "ru": "ru",
    "ar": "ar",
    "th": "th",
}

WORKERS = 16          # bumped from 10 — Google unofficial API tolerates ~20
PROGRESS_EVERY = 200  # log every N translations per language


def translate_one(text, target, retries=3):
    """Translate a single string via the unofficial Google API.

    Returns the translated string, or None on total failure.
    """
    for attempt in range(retries):
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "en",
                "tl": target,
                "dt": "t",
                "q": text,
            }
            full = url + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(
                full,
                headers={"User-Agent": "Mozilla/5.0 (WeddingAI-i18n-build/2.0)"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
            return json.loads(raw)[0][0][0]
        except Exception as e:
            if attempt == retries - 1:
                print(f"      [warn] translate failed: {type(e).__name__}: {str(e)[:100]}",
                      file=sys.stderr, flush=True)
                return None
            time.sleep(0.5 * (attempt + 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--langs",
        default="",
        help="Comma-separated subset of TARGETS to process. "
             "Default = all 9 languages. Example: --langs pt,ja",
    )
    args = ap.parse_args()

    if not EN_FILE.exists():
        print(f"Missing {EN_FILE}. Run i18n_extract.py first.", file=sys.stderr)
        sys.exit(1)

    en = json.loads(EN_FILE.read_text(encoding="utf-8"))
    en_keys = list(en.keys())
    print(f"Total en.json keys: {len(en_keys)}", flush=True)

    overall_t0 = time.time()
    grand_total_new = 0

    if args.langs:
        wanted = set(s.strip() for s in args.langs.split(",") if s.strip())
        targets = {k: v for k, v in TARGETS.items() if k in wanted}
        if not targets:
            print(f"--langs {args.langs!r} matched no languages in TARGETS",
                  file=sys.stderr)
            sys.exit(1)
        print(f"Filtering to: {sorted(targets.keys())}", file=sys.stderr)
    else:
        targets = TARGETS

    for code, gtl in targets.items():
        out_path = I18N_DIR / f"{code}.json"
        if not out_path.exists():
            print(f"\n[{code}] no existing file, creating from scratch",
                  file=sys.stderr, flush=True)
            data: dict = {}
        else:
            data = json.loads(out_path.read_text(encoding="utf-8"))

        existing_count = sum(1 for k in data if k != "_meta")
        missing = [k for k in en_keys if k not in data]
        print(f"\n[{code}] existing={existing_count} missing={len(missing)}",
              file=sys.stderr, flush=True)

        if not missing:
            print(f"  [{code}] all keys present, nothing to do",
                  file=sys.stderr, flush=True)
            continue

        # Translate missing keys in parallel
        translated: dict = {}
        failed: list = []
        lang_t0 = time.time()
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futures = {ex.submit(translate_one, en[k], gtl): k for k in missing}
            for i, fut in enumerate(as_completed(futures), 1):
                k = futures[fut]
                try:
                    v = fut.result()
                except Exception:
                    v = None
                if v is None or v == en[k] and len(en[k]) > 30:
                    # Either failed or returned English for a long string
                    # (likely an untranslatable proper noun).
                    failed.append(k)
                    v = en[k]
                translated[k] = v
                if i % PROGRESS_EVERY == 0 or i == len(missing):
                    elapsed = time.time() - lang_t0
                    rate = i / elapsed if elapsed > 0 else 0
                    remaining = (len(missing) - i) / rate if rate > 0 else 0
                    print(
                        f"    [{code}] {i}/{len(missing)} "
                        f"({rate:.1f}/s, ETA {remaining/60:.1f}min, "
                        f"failed={len(failed)})",
                        file=sys.stderr, flush=True,
                    )

        # Merge: keep existing + add new
        data.update(translated)

        # Update _meta to reflect new coverage
        data["_meta"] = {
            "lang": code,
            "source": "en",
            "translator": "google-translate (machine)",
            "review_required": True,
            "note": (
                f"Full coverage: {len(data) - 1}/{len(en_keys)} keys translated. "
                "Machine translation; technical terms, proper nouns, and "
                "marketing copy may need manual review."
            ),
            "coverage": f"{len(data) - 1}/{len(en_keys)} keys",
            "failed_translations": len(failed),
            "build": "i18n_translate_missing.py v1.0",
        }

        # Atomic-ish write: write to temp then rename
        tmp = out_path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp.replace(out_path)

        lang_elapsed = time.time() - lang_t0
        size_kb = out_path.stat().st_size / 1024
        grand_total_new += len(translated)
        print(
            f"  [{code}] DONE in {lang_elapsed/60:.1f}min, "
            f"{len(translated)} new, {len(failed)} failed-fallback, "
            f"file={size_kb:.1f}KB",
            file=sys.stderr, flush=True,
        )

    overall = time.time() - overall_t0
    print(
        f"\n=== ALL DONE in {overall/60:.1f}min, "
        f"{grand_total_new} new translations across {len(TARGETS)} languages ===",
        file=sys.stderr, flush=True,
    )


if __name__ == "__main__":
    main()
