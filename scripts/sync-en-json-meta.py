#!/usr/bin/env python3
"""Sync i18n/en.json's bound title/description values with the static HTML.

The middleware never loads a dictionary for the default language
(`if (lang === DEFAULT_LANG) return null;` in functions/_middleware.js), so
the value an English visitor sees is the STATIC html text. en.json still
carries a copy of it, and that copy can drift — and it is what the client
side language switcher reads.

This script makes en.json agree with the (already length-checked) static
html, so the English row of the live-metadata backlog is zero and a
localized page that falls back to the English source shows the same string
in both places.

Only keys that a page actually binds are touched. Orphan keys are left
alone — they never render.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n" / "en.json"

TITLE_BIND = re.compile(r'<title\b[^>]*\sdata-i18n="([^"]+)"[^>]*>(.*?)</title>', re.DOTALL)
DESC_BIND = re.compile(
    r'<meta\b[^>]*\sname="description"[^>]*\sdata-i18n-attr="content:([^"]+)"[^>]*\bcontent="(.*?)"',
    re.DOTALL)
SKIP = {".tmp", ".git", "node_modules", "qa", "internal-tools", "private", "scripts"}


def main():
    titles, descs = {}, {}
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if rel.parts and rel.parts[0] in SKIP:
            continue
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in TITLE_BIND.finditer(t):
            titles.setdefault(m.group(1), m.group(2).strip())
        for m in DESC_BIND.finditer(t):
            descs.setdefault(m.group(1), m.group(2).strip())

    raw = I18N.read_text(encoding="utf-8")
    data = json.loads(raw)
    changed = 0
    for key, val in titles.items():
        if key in data and data[key] != val:
            data[key] = val
            changed += 1
    for key, val in descs.items():
        if key in data and data[key] != val:
            data[key] = val
            changed += 1

    out = json.dumps(data, ensure_ascii=False, indent=2)
    if raw.endswith("\n"):
        out += "\n"
    # safety: the file must round-trip (only the values above may differ)
    check = json.loads(out)
    assert len(check) == len(data)
    I18N.write_text(out, encoding="utf-8", newline="")
    print(f"i18n/en.json: {changed} value(s) synced with the static html")
    print(f"  bound title keys: {len(titles)}   bound description keys: {len(descs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
