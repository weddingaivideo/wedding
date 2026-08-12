#!/usr/bin/env python3
"""Remove .x.HASH placeholder keys from en.json.

These are dead content slots (HTML inner is `---`) that should never have
been in en.json. The 47 that were there came from earlier hand-edits that
back-filled `---` values, but the HTML never reads them — it always shows
the inner `---` (or the key is just dead).

This complements cleanup-i18n-orphans.py which only cleans non-en languages.
en.json is normally never modified, but these placeholders are pure dead
weight (they bloat the deploy artifact and confuse translators).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
EN = ROOT / "i18n" / "en.json"

# A placeholder key has a path segment like `x.HASH` (8 hex chars at end)
# or `.x.HASH` somewhere in the path.
PLACEHOLDER_RE = re.compile(r"\.x\.[a-f0-9]{6,8}$|\bx\.[a-f0-9]{6,8}$")


def main():
    raw_bytes = EN.read_bytes()
    has_crlf = b"\r\n" in raw_bytes
    le = "\r\n" if has_crlf else "\n"

    obj = json.loads(raw_bytes.decode("utf-8"))
    before = len(obj)
    placeholder_keys = [k for k in obj if PLACEHOLDER_RE.search(k)]
    for k in placeholder_keys:
        del obj[k]
    after = len(obj)

    out = json.dumps(obj, indent=2, ensure_ascii=False, separators=(",", ": "))
    if has_crlf:
        out = out.replace("\n", "\r\n")
    if raw_bytes.endswith(b"\n"):
        out += le
    EN.write_text(out, encoding="utf-8", newline="")

    print(f"=== Strip placeholders from en.json ===")
    print(f"  before: {before} keys")
    print(f"  removed: {len(placeholder_keys)} placeholders")
    print(f"  after:  {after} keys")
    print(f"  size: {len(raw_bytes):,} → {EN.stat().st_size:,} bytes")
    if placeholder_keys:
        print()
        print(f"  Removed (sample first 10):")
        for k in placeholder_keys[:10]:
            print(f"    {k}")


if __name__ == "__main__":
    main()
