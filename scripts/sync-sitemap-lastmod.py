# -*- coding: utf-8 -*-
"""Make sitemap <lastmod> mean something again.

Before this pass, `_refresh_sitemap_lastmod.py` rewrote EVERY entry in all 11
sitemaps to today on every deploy. That tells Google a page changed when it
did not, while the page's own JSON-LD dateModified can be three months older.
It also makes the two signals contradict each other on every single URL.

This script derives each URL's date from the last git commit that actually
touched its backing file (or, for middleware-only pages, the dictionary /
middleware file), falling back to today for files created in the working tree
but not committed yet. `sitemap.xml` (the index) still gets today, which is
what .github/workflows/ci.yml checks with its grep.

Use this instead of `_refresh_sitemap_lastmod.py` for normal deploys.
"""
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
TODAY = datetime.now(timezone.utc).date().isoformat()
GIT_SINCE = "2026-01-01"


def git_file_dates():
    """One git call: map path -> date of its most recent commit."""
    try:
        out = subprocess.run(
            ["git", "log", "--since=" + GIT_SINCE,
             "--format=COMMIT %cs", "--name-only"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
            errors="replace", check=True).stdout
    except Exception as exc:
        print("[warn] git log failed (%s); using today" % exc, file=sys.stderr)
        return {}
    dates, cur = {}, None
    for line in out.splitlines():
        if line.startswith("COMMIT "):
            cur = line[7:].strip()
        elif cur and line.strip():
            p = line.strip().replace("\\", "/")
            if p not in dates:          # git log is newest-first
                dates[p] = cur
    return dates


def date_for(loc, lang, gdates):
    path = urlparse(loc).path.strip("/")
    rel = (path + "/index.html") if path else "index.html"
    candidates = [rel]
    if lang != "en":
        # Middleware-rendered pages have no localised twin: their text comes
        # from the dictionary, so that file's history is the honest date.
        candidates += ["i18n/%s.json" % lang, "functions/_middleware.js"]
        parts = rel.split("/", 1)
        if len(parts) == 2 and parts[0] == lang:
            candidates.append(parts[1])
    found = [gdates[c] for c in candidates if c in gdates]
    # A file edited in the working tree but not committed yet has no git date;
    # its mtime is the honest signal (run this script before committing, or
    # commit first and run it again — both give the same answer).
    local = ROOT / rel
    if local.exists():
        m = datetime.fromtimestamp(local.stat().st_mtime,
                                   timezone.utc).date().isoformat()
        found.append(m)
    if found:
        return max(found)
    # Middleware-only page whose dictionary was not tracked in this window.
    return TODAY


def sync_one(path, lang, gdates):
    s = path.read_text(encoding="utf-8")
    pat = re.compile(r'(<url>\s*<loc>([^<]+)</loc>\s*<lastmod>)'
                     r'\d{4}-\d{2}-\d{2}(</lastmod>)')
    seen = {}

    def repl(m):
        d = date_for(m.group(2), lang, gdates)
        seen[d] = seen.get(d, 0) + 1
        return m.group(1) + d + m.group(3)

    new, n = pat.subn(repl, s)
    if new != s:
        path.write_text(new, encoding="utf-8", newline="")
    print("  %-16s %3d entries, %d distinct dates, newest=%s" %
          (path.name, n, len(seen), max(seen) if seen else "-"))
    return n


def main():
    gdates = git_file_dates()
    print("git file history: %d paths since %s" % (len(gdates), GIT_SINCE))
    total = 0
    for lang in LANGS:
        p = ROOT / ("sitemap-%s.xml" % lang)
        if p.exists():
            total += sync_one(p, lang, gdates)
    index = ROOT / "sitemap.xml"
    if index.exists():
        s = index.read_text(encoding="utf-8")
        s = re.sub(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>",
                   "<lastmod>%s</lastmod>" % TODAY, s)
        index.write_text(s, encoding="utf-8", newline="\n")
        print("  sitemap.xml      index lastmod -> %s (CI requirement)" % TODAY)
    print("\nTotal: %d per-URL lastmod values now reflect real content changes."
          % total)


if __name__ == "__main__":
    main()
