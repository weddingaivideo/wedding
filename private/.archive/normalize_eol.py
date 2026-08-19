"""Normalize all files modified by today's M-1 + L-2 work to LF line endings.
Per .gitattributes, *.html, *.xml, *.py all use `text eol=lf` — CRLF is
forbidden in the committed repo. Python on Windows in text mode emits
CRLF; we explicitly fix that here so the git diff isn't full of bogus
'CRLF will be replaced by LF' warnings on every file."""
from pathlib import Path

ROOT = Path(".")

# All HTML under blog/, all sitemaps at root, all scripts/py touched today.
TARGETS = list(ROOT.glob("blog/*/index.html"))
TARGETS += [ROOT / "blog" / "index.html"]
TARGETS += [ROOT / "sitemap.xml"]
for lang in ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"]:
    TARGETS.append(ROOT / f"sitemap-{lang}.xml")
TARGETS += [ROOT / "robots.txt"]

fixed = 0
for p in TARGETS:
    if not p.exists():
        continue
    b = p.read_bytes()
    # CRLF -> LF
    if b"\r\n" in b:
        new = b.replace(b"\r\n", b"\n")
        p.write_bytes(new)
        fixed += 1
        print(f"  [LF]   {p}")
    else:
        print(f"  [skip] {p} (already LF)")

print(f"\nNormalized {fixed} files to LF")
