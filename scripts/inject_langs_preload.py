#!/usr/bin/env python3
"""
Inject <script src="/js/langs.js" defer></script> before every
<script src="/js/i18n.js" defer></script> in HTML files.

Idempotent: skips files that already have a /js/langs.js reference.

Run from repo root:
    python scripts/inject_langs_preload.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {"admin", "qa", "scripts", "__pycache__", "i18n", "js"}

LANGS_SCRIPT = '<script src="/js/langs.js" defer></script>'
I18N_RE = re.compile(
    r'(\s*)<script\s+src="/js/i18n\.js[^"]*"\s+defer\s*></script>',
    re.IGNORECASE,
)


def should_skip(p: Path) -> bool:
    parts = set(p.parts)
    return bool(parts & EXCLUDE_DIRS) or p.name in ("google-site-verification.html",)


def process(p: Path) -> tuple[bool, str]:
    text = p.read_text(encoding="utf-8")
    if "/js/langs.js" in text:
        return (False, "already has langs.js")
    new_text, n = I18N_RE.subn(rf"\1{LANGS_SCRIPT}\1<script src=", text, count=1)
    # The above produces two "<script src=" openings back-to-back which
    # is invalid HTML. Rewrite the I18N script tag with a more specific
    # match that leaves it intact.
    if n == 0:
        return (False, "no i18n.js script tag found")
    # Re-run with a simpler substitution: just inject the langs line
    # immediately before each i18n.js line, preserving indentation.
    text2 = p.read_text(encoding="utf-8")
    new_text, n = I18N_RE.subn(
        lambda m: f"{m.group(1)}{LANGS_SCRIPT}{m.group(1)}{m.group(0).lstrip()}",
        text2,
    )
    if n == 0:
        return (False, "no i18n.js script tag found")
    p.write_text(new_text, encoding="utf-8")
    return (True, f"injected (n={n})")


def main():
    files = [p for p in ROOT.rglob("*.html") if not should_skip(p)]
    print(f"Scanning {len(files)} HTML files")
    injected = 0
    skipped = 0
    issues = []
    for f in files:
        try:
            changed, msg = process(f)
            if changed:
                injected += 1
            else:
                skipped += 1
        except Exception as e:
            issues.append((f, str(e)))
    print(f"\nInjected: {injected}")
    print(f"Skipped:  {skipped}")
    if issues:
        print(f"\nIssues ({len(issues)}):")
        for f, err in issues[:5]:
            print(f"  {f.relative_to(ROOT)}: {err}")
    if issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
