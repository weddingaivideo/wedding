#!/usr/bin/env python3
"""
Fix en.json pollution by reverse-translating non-English values back to English.

For each en.json key whose value contains non-English text (zh/ar/th/ru/ja),
detect the source language and call Google Translate to translate it → English.

Uses the same gtx endpoint as translate-i18n-batch.py (no API key).
"""
import asyncio
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
EN = ROOT / "i18n" / "en.json"
PROGRESS_DIR = ROOT / "private" / ".reverse-progress"

# Reverse translation map: detected lang in value → gtx source code
LANG_TO_GTX_SRC = {
    "ar": "ar",     # Arabic → English
    "zh": "zh-CN",  # Chinese → English
    "ru": "ru",     # Russian → English
    "th": "th",     # Thai → English
    "ja": "ja",     # Japanese → English
}

# Same HTML protection as translate-i18n-batch.py
HTML_ENTITIES = [
    "&quot;", "&gt;", "&amp;", "&rsquo;", "&mdash;", "&ndash;",
    "&hellip;", "&lt;", "&rarr;", "&aacute;", "&ldquo;", "&rdquo;",
    "&copy;", "&nbsp;", "&apos;",
]


def detect_lang(s: str) -> str | None:
    """Return the dominant non-English language in a string, or None."""
    # Order matters: pick the one with most matches
    counts = {
        "ar": len(re.findall(r"[\u0600-\u06FF]", s)),
        "zh": len(re.findall(r"[\u4e00-\u9fff]", s)),
        "ja": len(re.findall(r"[\u3040-\u309f\u30a0-\u30ff]", s)),
        "ru": len(re.findall(r"[\u0400-\u04FF]", s)),
        "th": len(re.findall(r"[\u0e00-\u0e7f]", s)),
    }
    best = max(counts, key=counts.get)
    return best if counts[best] >= 3 else None


def protect_html(text: str) -> tuple[str, dict[str, str]]:
    placeholders = {}
    counter = [0]

    def make_ph(m):
        token = f"§§H{counter[0]:04d}§§"
        counter[0] += 1
        placeholders[token] = m.group(0)
        return token

    protected = re.sub(r"&[a-z]+;|&#\d+;", make_ph, text)
    protected = re.sub(r"</?[a-z]+[^>]*>", make_ph, protected)
    return protected, placeholders


def restore_html(text: str, placeholders: dict[str, str]) -> str:
    for token, original in placeholders.items():
        text = text.replace(token, original)
    return text


def translate_one_sync(text: str, source: str, max_retries: int = 3) -> str | None:
    """Reverse-translate text to English.

    `source` is a hint; we still pass it because it's free signal. But Google
    also auto-detects, so a `sl=ar` value containing mostly Chinese will
    correctly translate from Chinese. (Verified: with `sl=zh-CN` Google
    returns the source unchanged when the text isn't in zh-CN; with `sl=auto`
    Google uses real auto-detection and translates correctly.)
    """
    import requests
    url = "https://translate.googleapis.com/translate_a/single"
    # Prefer "auto" so Google picks the dominant language in the value,
    # even if our `source` hint is wrong.
    params = {
        "client": "gtx",
        "sl": "auto",  # was: source — see note above
        "tl": "en",
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


def load_progress() -> dict[str, str]:
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    p = PROGRESS_DIR / "en-reverse.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_progress(progress: dict[str, str]):
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    p = PROGRESS_DIR / "en-reverse.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(progress, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


def main():
    raw_bytes = EN.read_bytes()
    has_crlf = b"\r\n" in raw_bytes

    en = json.loads(raw_bytes.decode("utf-8"))
    print(f"=== en.json: {len(en)} keys ===")

    # Find polluted keys
    polluted = []
    for k, v in en.items():
        lang = detect_lang(v)
        if lang and lang in LANG_TO_GTX_SRC:
            polluted.append((k, v, lang))

    print(f"  polluted keys to reverse-translate: {len(polluted)}")
    by_lang = {}
    for _, _, l in polluted:
        by_lang[l] = by_lang.get(l, 0) + 1
    for l, n in sorted(by_lang.items(), key=lambda x: -x[1]):
        print(f"    {l}: {n}")
    print()

    if not polluted:
        print("  No pollution. Done.")
        return

    progress = load_progress()
    todo = [(k, v, l) for k, v, l in polluted if k not in progress]
    print(f"  already done: {len(progress)}")
    print(f"  to do: {len(todo)}")
    print()

    if not todo:
        print("  All already translated. Applying to en.json...")
    else:
        done = 0
        failed = []
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=16) as pool:
            future_to_item = {}
            for k, v, l in todo:
                if not v or not v.strip():
                    continue
                if len(v) > 4500:
                    continue
                protected, placeholders = protect_html(v)
                fut = pool.submit(translate_one_sync, protected, LANG_TO_GTX_SRC[l])
                future_to_item[fut] = (k, placeholders)
            for fut in as_completed(future_to_item):
                k, placeholders = future_to_item[fut]
                try:
                    translated = fut.result()
                except Exception:
                    translated = None
                if translated is not None:
                    progress[k] = restore_html(translated, placeholders)
                    done += 1
                else:
                    failed.append(k)
                if done % 100 == 0 and done > 0:
                    save_progress(progress)
                    elapsed = time.time() - t0
                    rate = done / elapsed if elapsed > 0 else 0
                    remaining = (len(todo) - done - len(failed)) / rate if rate > 0 else 0
                    print(f"  {done}/{len(todo)} done, {len(failed)} failed, {rate:.1f}/s, ETA {remaining/60:.1f} min", flush=True)

        save_progress(progress)
        print(f"  DONE: {done} translated, {len(failed)} failed, {time.time()-t0:.1f}s", flush=True)
        if failed:
            print(f"  First 5 failed: {failed[:5]}")

    # Apply to en.json
    for k, v in progress.items():
        en[k] = v
    out = json.dumps(en, indent=2, ensure_ascii=False, separators=(",", ": "))
    if has_crlf:
        out = out.replace("\n", "\r\n")
    if raw_bytes.endswith(b"\n"):
        out += "\r\n" if has_crlf else "\n"
    EN.write_text(out, encoding="utf-8", newline="")
    new_size = EN.stat().st_size
    print(f"  Wrote en.json: {len(en)} keys, {new_size:,} bytes")


if __name__ == "__main__":
    main()
