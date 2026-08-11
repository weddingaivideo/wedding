#!/usr/bin/env python3
"""
Add type="button" to all <button> tags missing a type attribute.

Why: best practice — without type, a <button> inside a <form> defaults to
"submit", which can trigger unintended form submission. mobile-menu-toggle
in particular is in the site header on every page (526+ occurrences).

Idempotent: only adds type where missing. Skip files in /private/.
"""
import re
import sys
from pathlib import Path

ROOT = Path(".")
EXCLUDE_DIRS = {"private", "node_modules", ".git", "__pycache__", "qa", "scripts", ".archive"}

# Match <button ...> with negative lookahead to ensure no type= present.
BUTTON_RE = re.compile(
    r'<button\b((?![\s>][^>]*type=)[^>]*)>',
    re.IGNORECASE
)


def main() -> int:
    files = [p for p in ROOT.rglob("*.html")
             if not any(part in EXCLUDE_DIRS for part in p.relative_to(ROOT).parts)]
    print(f"Scanning {len(files)} HTML files...")

    total_fixed = 0
    files_changed = 0
    for path in sorted(files):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if not text.strip():
            continue

        count_holder = [0]
        def repl(m):
            count_holder[0] += 1
            return f'<button type="button"{m.group(1)}>'

        new_text = BUTTON_RE.sub(repl, text)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            files_changed += 1
            total_fixed += count_holder[0]

    print(f"Done: {total_fixed} buttons fixed across {files_changed} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
