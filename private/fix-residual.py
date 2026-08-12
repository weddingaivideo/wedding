#!/usr/bin/env python3
"""Second-pass reverse translate: force sl=zh-CN for any zh-polluted key.
The first pass used sl=auto which left Chinese phrases in English text.
This time we explicitly say "this is Chinese" so Google translates the
whole thing, not just the English parts.
"""
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
EN = ROOT / "i18n" / "en.json"
PROGRESS_DIR = ROOT / "private" / ".reverse-progress"

# Force mapping: detected non-English script → gtx source
# For mixed-script strings, force the dominant non-English source.
FORCE_SRC = {
    "ar": "ar",
    "zh": "zh-CN",
    "ja": "ja",
    "ru": "ru",
    "th": "th",
}


def detect(s):
    counts = {
        "ar": len(re.findall(r"[\u0600-\u06FF]", s)),
        "zh": len(re.findall(r"[\u4e00-\u9fff]", s)),
        "ja": len(re.findall(r"[\u3040-\u309f\u30a0-\u30ff]", s)),
        "ru": len(re.findall(r"[\u0400-\u04FF]", s)),
        "th": len(re.findall(r"[\u0e00-\u0e7f]", s)),
    }
    best = max(counts, key=counts.get)
    return best if counts[best] >= 1 else None


def protect_html(text):
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


def restore_html(text, placeholders):
    for token, original in placeholders.items():
        text = text.replace(token, original)
    return text


def translate_one(text, source):
    import requests
    url = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": source, "tl": "en", "dt": "t", "q": text}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0"}
    r = requests.get(url, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()
    return "".join(c[0] for c in data[0] if c and c[0])


def main():
    raw_bytes = EN.read_bytes()
    has_crlf = b"\r\n" in raw_bytes
    en = json.loads(raw_bytes.decode("utf-8"))
    print(f"=== en.json: {len(en)} keys ===")

    # Find still-polluted
    polluted = [(k, v, detect(v)) for k, v in en.items() if detect(v)]
    print(f"  still polluted: {len(polluted)}")
    by_lang = {}
    for _, _, l in polluted:
        by_lang[l] = by_lang.get(l, 0) + 1
    for l, n in sorted(by_lang.items(), key=lambda x: -x[1]):
        print(f"    {l}: {n}")
    print()

    if not polluted:
        print("  No pollution. Done.")
        return

    todo = [(k, v, l) for k, v, l in polluted]
    print(f"  to do: {len(todo)}")
    print()

    done = 0
    failed = []
    t0 = time.time()
    results = {}
    with ThreadPoolExecutor(max_workers=16) as pool:
        future_to_item = {}
        for k, v, l in todo:
            if not v or not v.strip():
                continue
            if len(v) > 4500:
                continue
            protected, placeholders = protect_html(v)
            src = FORCE_SRC.get(l, "auto")
            fut = pool.submit(translate_one, protected, src)
            future_to_item[fut] = (k, placeholders)
        for fut in as_completed(future_to_item):
            k, placeholders = future_to_item[fut]
            try:
                translated = fut.result()
            except Exception:
                translated = None
            if translated is not None:
                results[k] = restore_html(translated, placeholders)
                done += 1
            else:
                failed.append(k)
            if done % 50 == 0 and done > 0:
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed > 0 else 0
                remaining = (len(todo) - done - len(failed)) / rate if rate > 0 else 0
                print(f"  {done}/{len(todo)} done, {len(failed)} failed, {rate:.1f}/s, ETA {remaining/60:.1f} min", flush=True)

    print(f"  DONE: {done} translated, {len(failed)} failed, {time.time()-t0:.1f}s")
    if failed:
        print(f"  First 5 failed: {failed[:5]}")

    # Apply to en.json
    for k, v in results.items():
        en[k] = v
    out = json.dumps(en, indent=2, ensure_ascii=False, separators=(",", ": "))
    if has_crlf:
        out = out.replace("\n", "\r\n")
    if raw_bytes.endswith(b"\n"):
        out += "\r\n" if has_crlf else "\n"
    EN.write_text(out, encoding="utf-8", newline="")
    print(f"  Wrote en.json: {len(en)} keys, {EN.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
