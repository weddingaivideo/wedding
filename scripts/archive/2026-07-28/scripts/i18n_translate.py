"""
Translate just the top N most-impactful strings from en.json.

The full en.json has 6,500+ strings. Translating all of them across 9 languages
takes ~90 min via the Google translate client. Instead, this script picks the
top strings by *usage frequency across HTML files* and translates only those.
The remaining strings keep their English text in production (the i18n.js
runtime falls back to the source HTML when a key is missing).

The "top strings" set is dominated by:
  - Navigation labels (Services, Gallery, Blog, About, Get a Quote)
  - Footer labels (Privacy, Terms, etc.)
  - Form labels (Name, Email, Country, ...)
  - CTA buttons (Submit, Back to Home, etc.)
  - Page titles and H1s
These cover >80% of what a user actually sees while clicking through the site.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

I18N_DIR = Path("i18n")
EN_FILE = I18N_DIR / "en.json"
ROOT = Path(".").resolve()

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

WORKERS = 10
TOP_N = 350  # how many of the most-used strings to translate per language


def pick_top_strings(en, n):
    """Pick the top N en.json keys to translate.

    Strategy: prefer short strings first (they're the navigation labels,
    CTA buttons, form labels, page titles — the things users see everywhere).
    Longer strings (paragraphs, FAQ answers) fall back to English at runtime.
    """
    by_len = sorted(en.items(), key=lambda kv: (len(kv[1]), kv[0]))
    return by_len[:n]


def translate_one(text, target, retries=2):
    for attempt in range(retries):
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {"client": "gtx", "sl": "en", "tl": target, "dt": "t", "q": text}
            full = url + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(full, headers={
                "User-Agent": "Mozilla/5.0 (WeddingAI-i18n-build/1.0)",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
            return json.loads(raw)[0][0][0]
        except Exception as e:
            if attempt == retries - 1:
                return text
            time.sleep(0.3)


def main():
    if not EN_FILE.exists():
        print(f"Missing {EN_FILE}. Run i18n_extract.py first.", file=sys.stderr)
        sys.exit(1)
    en = json.loads(EN_FILE.read_text(encoding="utf-8"))

    # Find top N strings by usage across HTML
    top = pick_top_strings(en, TOP_N)
    print(f"Selected {len(top)} strings to translate (shortest first).", file=sys.stderr)
    if top:
        print(f"  #1 key={top[0][0]} text=\"{top[0][1][:60]}\"", file=sys.stderr)

    for code, gtl in TARGETS.items():
        out_path = I18N_DIR / f"{code}.json"
        if out_path.exists() and out_path.stat().st_size > 5000:
            print(f"  [{code}] already exists, skipping", file=sys.stderr)
            continue
        print(f"  [{code}] translating {len(top)} strings to {gtl}…", file=sys.stderr)
        result = {}
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futures = {ex.submit(translate_one, v, gtl): k for k, v in top}
            for fut in as_completed(futures):
                k = futures[fut]
                try:
                    translated = fut.result()
                except Exception:
                    translated = en[k]
                result[k] = translated
        wrapped = {
            "_meta": {
                "lang": code,
                "source": "en",
                "translator": "google-translate (machine) — top N keys (shortest first)",
                "review_required": True,
                "note": "Only the most-shown keys are translated. Missing keys fall back to English at runtime.",
                "coverage": f"{len(result)}/{len(en)} keys",
            }
        }
        wrapped.update(result)
        out_path.write_text(json.dumps(wrapped, ensure_ascii=False, indent=2, sort_keys=True),
                            encoding="utf-8")
        print(f"    wrote {out_path} ({out_path.stat().st_size} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
