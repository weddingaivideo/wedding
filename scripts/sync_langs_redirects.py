#!/usr/bin/env python3
"""
Regenerate the i18n /xx/* → /:splat 200 block in _redirects from js/langs.js.

Looks for the marker:
    # === i18n language-prefix URL rewrite (managed by sync_langs_redirects.py) ===
and replaces the block from that line until the next blank-line-followed-by-#
or end-of-file.

Run from repo root:
    python scripts/sync_langs_redirects.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LANGS_JS = ROOT / "js" / "langs.js"
REDIRECTS = ROOT / "_redirects"

LANGS_RE = re.compile(r'window\.WA_LANGS\s*=\s*\[([^\]]+)\]')

# Marker: lines that begin a "managed" block. Everything from this marker
# (until the next non-rule separator) is replaced.
MANAGED_MARKER = "# === i18n language-prefix URL rewrite (managed by sync_langs_redirects.py) ==="


def parse_langs() -> list[str]:
    src = LANGS_JS.read_text(encoding="utf-8")
    m = LANGS_RE.search(src)
    if not m:
        raise ValueError("Could not find WA_LANGS array in js/langs.js")
    return re.findall(r'"([a-z]{2,3})"', m.group(1))


def build_block(langs: list[str]) -> str:
    lines = [
        MANAGED_MARKER,
        "# /xx/path  →  /path  with 200 (internal rewrite, browser URL stays /xx/path)",
        "# This gives every supported language its own indexable URL.",
        "# Canonical + hreflang alternates are baked into the static HTML files.",
        "# DO NOT edit by hand — run: python scripts/sync_langs_redirects.py",
    ]
    for lang in langs:
        lines.append(f"/{lang}/*    /:splat 200")
    return "\n".join(lines) + "\n"


def main():
    if not LANGS_JS.exists():
        print(f"[FAIL] Missing: {LANGS_JS}", file=sys.stderr)
        return 1
    if not REDIRECTS.exists():
        print(f"[FAIL] Missing: {REDIRECTS}", file=sys.stderr)
        return 1

    langs = parse_langs()
    new_block = build_block(langs)

    text = REDIRECTS.read_text(encoding="utf-8")
    if MANAGED_MARKER in text:
        # Replace existing managed block (marker line + the contiguous rules
        # until the next blank-line-followed-by-# or end of file).
        # Find marker line index, then find next "blank line + # comment" or EOF.
        lines = text.splitlines(keepends=True)
        marker_idx = next(
            (i for i, ln in enumerate(lines) if MANAGED_MARKER in ln), None
        )
        if marker_idx is not None:
            end_idx = len(lines)
            for j in range(marker_idx + 1, len(lines)):
                ln = lines[j]
                # Stop at next managed block: a blank line followed by a
                # comment line that isn't part of the rule list.
                if ln.startswith("\n") and (
                    j + 1 < len(lines) and lines[j + 1].lstrip().startswith("#")
                    and "managed by" not in lines[j + 1]
                ):
                    end_idx = j
                    break
                if ln.startswith("# ===") and MANAGED_MARKER not in ln:
                    end_idx = j
                    break
            new_text = "".join(lines[:marker_idx]) + new_block + "\n" + "".join(lines[end_idx:])
        else:
            new_text = text.rstrip() + "\n\n" + new_block
    else:
        # No managed marker — append a new block at the end.
        new_text = text.rstrip() + "\n\n" + new_block

    REDIRECTS.write_text(new_text, encoding="utf-8")
    print(f"[PASS] Wrote {len(langs)} language rules to _redirects")
    for lang in langs:
        print(f"  /{lang}/*    /:splat 200")
    return 0


if __name__ == "__main__":
    sys.exit(main())
