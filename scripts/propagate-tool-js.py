#!/usr/bin/env python3
"""
Propagate the English inline script of every tool page to its 10 localized
copies.

WHY THIS EXISTS (found 2026-11-09)
---------------------------------
The localized copies of the tool pages carry a MACHINE-TRANSLATED copy of
the English page's JavaScript. The translator translated the CODE, not only
the strings:

    de/tools/add-text-to-wedding-photo/index.html
      226:  Funktion addFiles(picked) {
      227:    var hinzugefügt = 0;

`function` became `Funktion`, `added` became `hinzugefügt`. The result is a
SyntaxError, so the ENTIRE inline script fails to parse and the tool does
nothing on that page. The page still returns 200, the controls still render,
and the copy still looks fine in a screenshot - the tool is simply dead.

Measured with scripts/check-tool-script-syntax.py: 44 of the 144 tool pages
had a broken inline script, spread over es, fr, de, ar, th, hi (plus every
localized copy of the budget calculator, and fr of the seating chart and
the photo-book planner).

`ru/tools/heic-to-jpg-wedding-photos/index.html` has NO inline script at all
- the tool is dead there too.

THE FIX
-------
JavaScript is language-independent. The English page's inline script becomes
the single source of truth for behaviour, and every localized copy gets it
byte-for-byte.

What this LOSES: the runtime strings that used to be hardcoded in the
translated script (the toasts, the canvas labels) come back in English.
What this GAINS: the tool works in all 11 languages instead of 5.

To get the strings back, every user-facing runtime string in the English
script must go through window.weddingAITool.t('alias', 'English fallback').
The alias table lives in js/tools/common.js and the "tools.copy" namespace
is injected into the page by the middleware as window.__WA_I18N__ - so the
fallback is only ever shown on an English page or if the injection fails.

The static markup of each localized copy is NOT touched: its prose, its
JSON-LD and its data-i18n bindings stay exactly as they are, and the
middleware keeps translating them per language.

Usage
-----
    python scripts/propagate-tool-js.py --dry-run
    python scripts/propagate-tool-js.py

Idempotent: a copy that already holds the English script is left alone.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
TOOLS = sorted(d.name for d in (ROOT / "tools").iterdir() if d.is_dir())

SCRIPT_RE = re.compile(r"(?s)(<script\b[^>]*>)(.*?)(</script>)")


def is_main(attrs, body):
    """True for the page's own behaviour script (not JSON-LD, not a src tag,
    not the Clarity loader, not the Service Worker registration)."""
    if "ld+json" in attrs:
        return False
    if "src=" in attrs:
        return False
    if "serviceWorker" in body:
        return False
    if "clarity" in body and "createElement" in body and len(body) < 600:
        return False
    return len(body) > 400


def find_main(text):
    """Return (start, end, body) of the main inline script, or None."""
    best = None
    for m in SCRIPT_RE.finditer(text):
        attrs, body = m.group(1), m.group(2)
        if not is_main(attrs, body):
            continue
        if best is None or len(body) > len(best[2]):
            best = (m.start(2), m.end(2), body)
    return best


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmpwrite")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tools", default="", help="comma-separated slugs; default = all")
    args = ap.parse_args()

    wanted = [s.strip() for s in args.tools.split(",") if s.strip()]
    slugs = [s for s in TOOLS if not wanted or s in wanted]

    replaced = inserted = unchanged = 0
    problems = []

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "check.js"
        for slug in slugs:
            en_path = ROOT / "tools" / slug / "index.html"
            if not en_path.exists():
                continue
            en_text = en_path.read_text(encoding="utf-8")
            en_main = find_main(en_text)
            if en_main is None:
                problems.append(f"{slug}: the English page has no main inline script")
                continue
            en_body = en_main[2]

            # The English script itself must parse.
            tmp.write_text(en_body, encoding="utf-8")
            r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
            if r.returncode != 0:
                problems.append(f"{slug}: the ENGLISH inline script does not parse:\n{r.stderr[:600]}")
                continue

            for lang in LANGS:
                if lang == "en":
                    continue
                p = ROOT / lang / "tools" / slug / "index.html"
                if not p.exists():
                    continue
                text = p.read_text(encoding="utf-8")
                loc_main = find_main(text)
                if loc_main is None:
                    # No script at all (ru/heic): insert the English one.
                    if "</body>" in text:
                        new_text = text.replace("</body>", "<script>" + en_body + "</script>\n</body>", 1)
                    else:
                        new_text = text + "<script>" + en_body + "</script>"
                    action = "inserted"
                    inserted += 1
                elif loc_main[2] == en_body:
                    unchanged += 1
                    continue
                else:
                    new_text = text[:loc_main[0]] + en_body + text[loc_main[1]:]
                    action = "replaced"
                    replaced += 1

                # The result must parse.
                tmp.write_text(en_body, encoding="utf-8")
                r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
                if r.returncode != 0:
                    problems.append(f"{lang}/{slug}: result does not parse")
                    continue

                if not args.dry_run:
                    write_atomic(p, new_text)
                print(f"  {lang}/{slug}: {action} ({len(loc_main[2]) if loc_main else 0} -> {len(en_body)} bytes)")

    print()
    print(f"replaced: {replaced}   inserted: {inserted}   already identical: {unchanged}")
    if problems:
        print("\nPROBLEMS:")
        for p_ in problems:
            print("  " + p_)
        return 1
    print("all propagated copies parse")
    return 0


if __name__ == "__main__":
    sys.exit(main())
