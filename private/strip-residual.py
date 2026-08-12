#!/usr/bin/env python3
"""Strip the remaining 135 polluted keys from en.json AND all 9 non-en languages.

The middleware falls back to the HTML inner when the key is absent from the
target language JSON. Since the 135 polluted keys came from non-English
HTML, each language's own HTML has the correct inner text — so the fallback
is the right answer for them.

Why we strip en.json too: if en.json has the key, the 9-language JSON
inherits the pollution (Google translates the mixed-script value into
another mixed-script value). Removing en.json source means future
translations won't have the key to translate.
"""
import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
LANGS = ["zh", "ja", "ru", "ar", "de", "es", "fr", "pt", "th"]


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


def strip(path: Path, polluted_keys: set[str]) -> tuple[int, int]:
    raw_bytes = path.read_bytes()
    has_crlf = b"\r\n" in raw_bytes
    obj = json.loads(raw_bytes.decode("utf-8"))
    before = len(obj)
    for k in polluted_keys:
        obj.pop(k, None)
    after = len(obj)
    out = json.dumps(obj, indent=2, ensure_ascii=False, separators=(",", ": "))
    if has_crlf:
        out = out.replace("\n", "\r\n")
    if raw_bytes.endswith(b"\n"):
        out += "\r\n" if has_crlf else "\n"
    path.write_text(out, encoding="utf-8", newline="")
    return (before - after, after)


def main():
    # First, identify the 135 polluted keys from en.json
    en_path = ROOT / "i18n" / "en.json"
    en = json.loads(en_path.read_text(encoding="utf-8"))
    polluted = {k for k, v in en.items() if detect(v)}
    print(f"=== Identified {len(polluted)} polluted keys in en.json ===")
    print()

    # Strip from each language
    print("  lang  removed  remaining_keys")
    for lang in ["en"] + LANGS:
        path = ROOT / "i18n" / f"{lang}.json"
        if not path.exists():
            continue
        removed, remaining = strip(path, polluted)
        print(f"  {lang:<4}  {removed:>5}     {remaining}")


if __name__ == "__main__":
    main()
