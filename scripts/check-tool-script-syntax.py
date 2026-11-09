#!/usr/bin/env python3
"""
Check that the inline script of EVERY tool page parses.

A single unescaped apostrophe inside a JS string literal ('l'instant')
terminates the literal and turns the rest of the line into garbage - the
whole tool silently stops working in that language. This is invisible in a
diff and invisible to the i18n shard gate, because the page still returns
200 and still looks fine on screen (the controls render, the script just
dies).

Found 2026-11-09 in fr/tools/wedding-seating-chart-maker/index.html.

WHAT IT EXCLUDES
----------------
* <script type="application/ld+json"> blocks - they are JSON, not JS.
* <script src="..."> tags - no inline body.
* The Clarity analytics loader (it is a fixed snippet, always valid).

Exit code 1 when anything is broken, so it can be a fatal pre-deploy step.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
TOOLS = sorted(d.name for d in (ROOT / "tools").iterdir() if d.is_dir())

SCRIPT_RE = re.compile(r"(?s)<script\b([^>]*)>(.*?)</script>")


def inline_bodies(text):
    """Yield the inline (non-JSON-LD, non-src) script bodies."""
    for m in SCRIPT_RE.finditer(text):
        attrs, body = m.group(1), m.group(2)
        if "ld+json" in attrs:
            continue
        if "src=" in attrs:
            continue
        if not body.strip():
            continue
        # The Clarity loader is a fixed, known-good snippet.
        if "clarity" in body and "createElement" in body and len(body) < 600:
            continue
        yield body


def check_one(body):
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "check.js"
        tmp.write_text(body, encoding="utf-8")
        r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
    return r


def main():
    broken = []
    checked = 0
    for slug in TOOLS:
        for lang in LANGS:
            p = ((ROOT / "tools" / slug / "index.html") if lang == "en"
                 else (ROOT / lang / "tools" / slug / "index.html"))
            if not p.exists():
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            for body in inline_bodies(text):
                if "function" not in body and "var " not in body:
                    continue
                checked += 1
                r = check_one(body)
                if r.returncode != 0:
                    line_no = ""
                    src = ""
                    m = re.search(r"check\.js:(\d+)", r.stderr)
                    lines = body.splitlines()
                    if m:
                        n = int(m.group(1))
                        if 0 < n <= len(lines):
                            line_no = str(n)
                            src = lines[n - 1].strip()[:120]
                    msg = ""
                    mm = re.search(r"(SyntaxError.*)", r.stderr)
                    if mm:
                        msg = mm.group(1)
                    broken.append((slug, lang, line_no, src, msg))
                    print("BROKEN  %-42s %-3s line %-5s %s" % (slug[:42], lang, line_no, msg))
                    if src:
                        print("        %s" % src)

    print()
    print("inline scripts checked: %d   broken: %d" % (checked, len(broken)))
    if broken:
        print("\nAffected pages:")
        seen = []
        for slug, lang, *_ in broken:
            key = (slug, lang)
            if key not in seen:
                seen.append(key)
        for slug, lang in seen:
            print("  %s/tools/%s/index.html" % (lang, slug))
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
