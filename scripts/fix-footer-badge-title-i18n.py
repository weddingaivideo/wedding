#!/usr/bin/env python3
"""Bind the site-wide footer badge tooltip to the i18n dictionary.

The trust badge in the footer of every page is:

    <a class="footer-badge footer-badge-secondary" href="/about/"
       title="500+ couples served, 4.9/5 rating"
       data-i18n="about.a_text.couples_served.ddddddd1" ...>⭐ 4.9/5 · 500+ couples</a>

The visible text IS bound (data-i18n), but the title attribute is not. On a
localized page the tooltip therefore stays English: "500+ couples served,
4.9/5 rating" - which is how the audit found a residual "500" on the Spanish
homepage and on /es/services/video-enhancement/vintage-restoration/.

The fix adds data-i18n-attr="title:<key>" to the badge. The middleware's
applyDataI18nAttr() pass then rewrites the title attribute from the
dictionary. The key itself was added to all 11 dictionaries by
scripts/fix-trust-key-binding.py.

This script also repairs ONE damaged copy of the title: tools/index.html
carries "500+ couples served, /5 rating" - a digit-stripping pass ate the
"4.9" and left the sentence broken.

Run from the repo root:  python scripts/fix-footer-badge-title-i18n.py [--apply]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

TITLE_KEY = "about.a_text.couples_served_title.ddddddd3"
BADGE_I18N_KEY = "about.a_text.couples_served.ddddddd1"
GOOD_TITLE = "500+ couples served, 4.9/5 rating"
DAMAGED_TITLE = "500+ couples served, /5 rating"

SKIP_DIRS = {".git", ".tmp", ".en-backup", "node_modules", "__pycache__",
              ".wrangler", "i18n", "qa", "scripts", "internal-tools",
              "private", "functions", ".well-known", ".github", "tests"}

# The badge anchor: <a ... class="footer-badge..." ... data-i18n="<key>" ...>
BADGE_RE = re.compile(
    r'<a\b[^>]*\bclass="footer-badge[^"]*"[^>]*\bdata-i18n="'
    + re.escape(BADGE_I18N_KEY) + r'"[^>]*>',
    re.IGNORECASE,
)


def patch(text):
    """Return (new_text, n_bound, n_already, n_title_repaired)."""
    n_bound = 0
    n_already = 0
    n_title_repaired = 0

    def repl(m):
        nonlocal n_bound, n_already
        tag = m.group(0)
        if "data-i18n-attr=" in tag:
            n_already += 1
            return tag
        # Insert the attribute right after the data-i18n pair.
        out = tag.replace(
            'data-i18n="%s"' % BADGE_I18N_KEY,
            'data-i18n="%s" data-i18n-attr="title:%s"' % (BADGE_I18N_KEY, TITLE_KEY),
            1)
        if out == tag:
            return tag
        n_bound += 1
        return out

    text = BADGE_RE.sub(repl, text)
    if DAMAGED_TITLE in text:
        n_title_repaired = text.count(DAMAGED_TITLE)
        text = text.replace(DAMAGED_TITLE, GOOD_TITLE)
    return text, n_bound, n_already, n_title_repaired


def html_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".html"):
                yield os.path.join(dirpath, fn)


def main():
    apply = "--apply" in sys.argv
    print("=== fix-footer-badge-title-i18n ===")
    print(f"mode: {'APPLY' if apply else 'DRY RUN (add --apply to write)'}")
    print()

    total_bound = total_already = total_repaired = 0
    changed_files = 0
    for path in html_files():
        rel = os.path.relpath(path, ROOT)
        # newline="" keeps the file's own line endings verbatim.
        with open(path, "r", encoding="utf-8", newline="") as fh:
            original = fh.read()
        new, n_bound, n_already, n_repaired = patch(original)
        total_bound += n_bound
        total_already += n_already
        total_repaired += n_repaired
        if new != original:
            changed_files += 1
            if apply:
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8", newline="") as fh:
                    fh.write(new)
                os.replace(tmp, path)
            elif changed_files <= 5:
                print(f"  would change: {rel} "
                      f"(bound={n_bound} repaired={n_repaired})")

    print()
    print(f"  badges newly bound        : {total_bound}")
    print(f"  badges already bound      : {total_already}")
    print(f"  damaged titles repaired   : {total_repaired}")
    print(f"  files affected            : {changed_files}")
    print()
    print("done." if apply else "dry run - nothing written.")


if __name__ == "__main__":
    main()
