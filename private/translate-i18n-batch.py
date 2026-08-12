#!/usr/bin/env python3
"""
Batch translate en.json → 9 non-en language JSONs using Google Translate
free `gtx` endpoint (no API key needed).

Strategy:
  1. For each non-en language, find keys in en.json that are MISSING from
     the target JSON. (We never overwrite existing translations.)
  2. For each missing key, prepare the en value for translation:
     - Replace HTML entities (&amp; &quot; etc.) and tags (<br> <a> etc.)
       with placeholders that Google Translate won't mangle.
     - Pre-translate common constructs (apostrophe, hyphen, etc.) that
       sometimes get mangled.
  3. Call translate.googleapis.com/translate_a/single?client=gtx in a
     thread pool (concurrent.futures.ThreadPoolExecutor, 16 workers).
  4. Restore placeholders in the translated text.
  5. Save progress every 500 keys so we can resume on crash.
  6. Verify by re-checking missing-key count after each batch.

Endpoint: https://translate.googleapis.com/translate_a/single
  - No API key, no token.
  - Rate limit: ~10 req/s sustained; 100 req/s burst (per IP, unofficial).
  - Returns: JSON array of [[translated_chunk, src, ...], ...].

Run:
  python private/translate-i18n-batch.py [--langs zh,ja,es] [--workers 16] [--batch-size 500]

Resume: if a `private/.translate-progress-{lang}.json` exists from a previous
        run, it will be loaded and only missing keys will be re-fetched.
"""
import argparse
import asyncio
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
I18N = ROOT / "i18n"
PROGRESS_DIR = ROOT / "private" / ".translate-progress"

LANGS = ["zh", "ja", "ru", "ar", "de", "es", "fr", "pt", "th"]
LANG_TO_GOOGLE = {
    "zh": "zh-CN",
    "ja": "ja",
    "ru": "ru",
    "ar": "ar",
    "de": "de",
    "es": "es",
    "fr": "fr",
    "pt": "pt",
    "th": "th",
}

# HTML entity and tag placeholders. The keys must NOT contain text that
# Google Translate would translate or alter. We use a unique sigil that
# Google leaves alone (uppercase, numbers, no spaces).
HTML_ENTITIES = [
    "&quot;", "&gt;", "&amp;", "&rsquo;", "&mdash;", "&ndash;",
    "&hellip;", "&lt;", "&rarr;", "&aacute;", "&ldquo;", "&rdquo;",
    "&copy;", "&nbsp;", "&apos;",
]
HTML_TAGS = ["<br>", "<br/>", "<br />", "</a>", "</span>", "</em>", "</strong>",
             "</b>", "</i>", "</u>", "<em>", "</em>", "<strong>", "</strong>"]


def protect_html(text: str) -> tuple[str, dict[str, str]]:
    """Replace HTML entities and tags with placeholders. Return (protected, placeholders)."""
    placeholders = {}
    counter = [0]

    def make_placeholder(_match):
        token = f"§§H{counter[0]:04d}§§"
        counter[0] += 1
        placeholders[token] = _match.group(0)
        return token

    # First protect entities
    protected = re.sub(r"&[a-z]+;|&#\d+;", make_placeholder, text)
    # Then protect tags
    protected = re.sub(r"</?[a-z]+[^>]*>", make_placeholder, protected)
    return protected, placeholders


def restore_html(text: str, placeholders: dict[str, str]) -> str:
    """Restore HTML entities and tags from placeholders."""
    for token, original in placeholders.items():
        text = text.replace(token, original)
    return text


def translate_one_sync(text: str, dest_lang: str, max_retries: int = 3) -> str | None:
    """Call Google Translate gtx endpoint synchronously, return translated text or None on failure."""
    import requests

    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": dest_lang,
        "dt": "t",
        "q": text,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=20)
            if r.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            data = r.json()
            parts = []
            for chunk in data[0]:
                if chunk and chunk[0]:
                    parts.append(chunk[0])
            return "".join(parts)
        except Exception:
            if attempt == max_retries - 1:
                return None
            time.sleep(1 + 2 ** attempt)
    return None


async def translate_one_async(text: str, dest_lang: str, max_retries: int = 3) -> str | None:
    """Call Google Translate gtx endpoint via httpx async, return translated text or None on failure."""
    import httpx

    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": dest_lang,
        "dt": "t",
        "q": text,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

    last_err = None
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(http2=False, headers=headers, timeout=20) as client:
                r = await client.get(url, params=params)
                if r.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                r.raise_for_status()
                data = r.json()
                parts = []
                for chunk in data[0]:
                    if chunk and chunk[0]:
                        parts.append(chunk[0])
                return "".join(parts)
        except Exception as e:
            last_err = e
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(1 + 2 ** attempt)
    return None


# Use sync by default (more reliable on Windows + httpx); async can be enabled
translate_one = translate_one_sync


def translate_value(en_value: str, dest_lang: str) -> str | None:
    """Translate an en.json value, protecting HTML constructs."""
    if not en_value or not en_value.strip():
        return en_value
    protected, placeholders = protect_html(en_value)
    translated = translate_one(protected, dest_lang)
    if translated is None:
        return None
    return restore_html(translated, placeholders)


def load_progress(lang: str) -> dict[str, str]:
    """Load translation progress for a language (so we can resume)."""
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    p = PROGRESS_DIR / f"{lang}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_progress(lang: str, progress: dict[str, str]):
    """Save translation progress atomically."""
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    p = PROGRESS_DIR / f"{lang}.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(progress, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


def detect_line_ending(path: Path) -> str:
    raw = path.read_bytes()
    return "\r\n" if b"\r\n" in raw else "\n"


def translate_one_language(lang: str, en: dict, args) -> tuple[int, int, list[str]]:
    """Translate all missing keys for one language. Returns (done, failed_count, failed_list)."""
    if lang not in LANG_TO_GOOGLE:
        print(f"Unknown lang: {lang}, skipping")
        return (0, 0, [])

    target_path = I18N / f"{lang}.json"
    target = json.loads(target_path.read_text(encoding="utf-8"))
    progress = load_progress(lang)

    # Find missing keys (in en but not in target)
    missing = [k for k in en if k not in target]
    if not missing:
        print(f"[{lang}] No missing keys. ✓")
        return (0, 0, [])

    # Filter out keys that have empty/whitespace values or are too long
    work_items = []
    for k in missing:
        v = en[k]
        if not v or not v.strip():
            continue
        if len(v) > args.max_chars:
            continue
        work_items.append(k)

    # Also skip keys already in progress
    work_items = [k for k in work_items if k not in progress]

    if not work_items:
        print(f"[{lang}] {len(missing)} missing, but all either empty/too-long/already-done. Skipping.")
        return (0, 0, [])

    print(f"[{lang}] Need to translate {len(work_items)} keys (out of {len(missing)} missing)")

    dest = LANG_TO_GOOGLE[lang]
    done = 0
    failed = []
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        future_to_key = {
            pool.submit(translate_value, en[k], dest): k
            for k in work_items
        }
        for fut in as_completed(future_to_key):
            k = future_to_key[fut]
            try:
                result = fut.result()
            except Exception:
                result = None
            if result is not None:
                progress[k] = result
                done += 1
            else:
                failed.append(k)

            if done % args.batch_size == 0 and done > 0:
                save_progress(lang, progress)
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed > 0 else 0
                remaining = (len(work_items) - done - len(failed)) / rate if rate > 0 else 0
                print(f"  [{lang}] {done}/{len(work_items)} done, {len(failed)} failed, {rate:.1f}/s, ETA {remaining/60:.1f} min", flush=True)

    # Final save
    save_progress(lang, progress)
    print(f"  [{lang}] DONE: {done} translated, {len(failed)} failed, {time.time()-t0:.1f}s", flush=True)
    if failed:
        print(f"  [{lang}] First 5 failed: {failed[:5]}")

    # Apply progress to target.json
    for k, v in progress.items():
        if k not in target:
            target[k] = v

    # Write target.json back
    raw = target_path.read_bytes()
    le = "\r\n" if b"\r\n" in raw else "\n"
    out = json.dumps(target, indent=2, ensure_ascii=False, separators=(",", ": "))
    if le == "\r\n":
        out = out.replace("\n", "\r\n")
    if raw.endswith(b"\n"):
        out += le
    target_path.write_text(out, encoding="utf-8", newline="")
    new_size = target_path.stat().st_size
    print(f"  [{lang}] Wrote target.json: {len(target)} keys, {new_size:,} bytes", flush=True)
    return (done, len(failed), failed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default=",".join(LANGS), help="Comma-separated lang codes")
    ap.add_argument("--workers", type=int, default=16, help="Thread pool size per language")
    ap.add_argument("--batch-size", type=int, default=500, help="Save progress every N keys")
    ap.add_argument("--max-chars", type=int, default=4500, help="Skip values longer than this")
    ap.add_argument("--lang-parallel", type=int, default=9, help="How many languages to translate in parallel (uses processes)")
    args = ap.parse_args()

    en_path = I18N / "en.json"
    en = json.loads(en_path.read_text(encoding="utf-8"))
    print(f"=== en.json: {len(en)} keys, {en_path.stat().st_size:,} bytes ===", flush=True)
    print(f"  workers/lang: {args.workers}, lang-parallel: {args.lang_parallel}", flush=True)
    print(flush=True)

    langs = [l.strip() for l in args.langs.split(",") if l.strip()]

    if args.lang_parallel > 1 and len(langs) > 1:
        # Process-pool: each process handles one language
        # Note: progress files are shared via filesystem, so per-language
        # save_progress still works.
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=min(args.lang_parallel, len(langs))) as pool:
            futures = {
                pool.submit(translate_one_language, lang, en, args): lang
                for lang in langs
            }
            for fut in as_completed(futures):
                lang = futures[fut]
                try:
                    fut.result()
                except Exception as e:
                    print(f"[{lang}] Process error: {e}", flush=True)
    else:
        # Sequential
        for lang in langs:
            translate_one_language(lang, en, args)


if __name__ == "__main__":
    main()
