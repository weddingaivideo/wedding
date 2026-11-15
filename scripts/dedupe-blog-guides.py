# -*- coding: utf-8 -*-
"""Retire four pairs of near-duplicate blog URLs without moving a single URL.

The scan in research/内容重复度扫描-2026-11-14.md found four slug twins that
are all 200, all in all 11 sitemaps and all self-canonical — classic query
cannibalisation. Two are plural duplicates, two are `-new` leftovers.

Moving them with a 301 would require deleting 22 files AND teaching
functions/_middleware.js about the old paths, because the middleware rewrites
`<link rel=canonical>` for every non-English page (so a canonical merge would
silently be undone at runtime). Keeping the URLs live and instead doing this
is both safer and effective:

  1. noindex,follow on the weak twins -> Google drops them from the index but
     still follows their internal links.
  2. the strong twin's canonical on the ENGLISH weak page (the only one served
     as a plain static file) -> consolidates the signal for the main market.
  3. remove the weak URLs from all 11 sitemaps -> stop re-submitting them.
  4. repoint every internal link at the strong twin -> concentrate link equity.

No file is deleted, no URL changes status, no 301 is added, and the existing
hreflang graph is left intact for the gate.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
PAIRS = [
    ("multilingual-wedding-videos", "multilingual-wedding-video"),
    ("pet-wedding-videos", "pet-wedding-video"),
    ("wedding-video-cost-2026-new", "wedding-video-cost-2026"),
    ("wedding-video-music-guide-new", "wedding-video-music-guide"),
]
WEAK = [w for w, _ in PAIRS]
STRONG = {w: s for w, s in PAIRS}


def html_files():
    for p in ROOT.rglob("index.html"):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith((".git/", ".tmp/", "node_modules/", "internal-tools/")):
            continue
        yield p


def add_robots_meta():
    n = 0
    weak_paths = []
    for weak in WEAK:
        for lang in [""] + LANGS:
            p = (ROOT / lang / "blog" / weak / "index.html") if lang else \
                (ROOT / "blog" / weak / "index.html")
            if not p.exists():
                continue
            weak_paths.append(p)
            s = p.read_text(encoding="utf-8")
            if "noindex" in s:
                continue
            marker = '<meta name="viewport"'
            i = s.find(marker)
            if i < 0:
                continue
            eol = s.find("\n", i)
            s = (s[:eol + 1] +
                 '<meta name="robots" content="noindex,follow">\n' + s[eol + 1:])
            # Only the English static twin keeps its own canonical handling;
            # the middleware rewrites canonical on every /<lang>/ request.
            if not lang:
                base = "https://weddingai.video/blog/%s/" % STRONG[weak]
                s = re.sub(r'<link rel="canonical" href="[^"]+">',
                           '<link rel="canonical" href="%s">' % base, s, count=1)
                s = re.sub(r'<meta property="og:url" content="[^"]+">',
                           '<meta property="og:url" content="%s">' % base, s, count=1)
            p.write_text(s, encoding="utf-8", newline="")
            n += 1
    print("weak pages marked noindex,follow: %d (of %d found)" %
          (n, len(weak_paths)))
    return n


def remove_from_sitemaps():
    total = 0
    for lang in ["en"] + LANGS:
        p = ROOT / ("sitemap-%s.xml" % lang)
        s = p.read_text(encoding="utf-8")
        before = s.count("<url>")
        for weak in WEAK:
            pat = re.compile(r'\n?[ \t]*<url>\s*<loc>[^<]*/blog/' + re.escape(weak) +
                             r'/</loc>[\s\S]*?</url>')
            s, k = pat.subn("", s)
        after = s.count("<url>")
        if after != before:
            p.write_text(s, encoding="utf-8", newline="\n")
        total += before - after
        print("  %-16s %3d -> %3d" % (p.name, before, after))
    print("sitemap entries removed: %d" % total)


def repoint_internal_links():
    files = changed = hits = 0
    for p in list(html_files()) + list((ROOT / "i18n").glob("*.json")):
        try:
            s = p.read_text(encoding="utf-8")
        except Exception:
            continue
        files += 1
        orig = s
        # hreflang blocks must keep pointing at their OWN language/URL. Shield
        # those lines before the blanket path replacement, then put them back.
        shielded, saved = [], []

        def shield(line):
            if 'rel="alternate"' in line and "hreflang" in line:
                saved.append(line)
                return "\x00HREFLANG%d\x00" % (len(saved) - 1)
            return line

        s = "".join(shield(l) for l in s.splitlines(keepends=True))
        for weak in WEAK:
            pat = re.compile(r'(href=\\"?(?:/[a-z]{2})?/blog/)' + re.escape(weak) + r'(/)')
            s, k1 = pat.subn(lambda m: m.group(1) + STRONG[weak] + m.group(2), s)
            # JSON-escaped links in i18n dictionaries
            pat2 = re.compile(r'((?:/[a-z]{2})?/blog/)' + re.escape(weak) + r'(/)')
            s, k2 = pat2.subn(lambda m: m.group(1) + STRONG[weak] + m.group(2), s)
            hits += k1 + k2
        if saved:
            s = re.sub(r'\x00HREFLANG(\d+)\x00',
                       lambda m: saved[int(m.group(1))], s)
        if s != orig:
            p.write_text(s, encoding="utf-8", newline="")
            changed += 1
    print("internal links scanned %d files, %d replacements in %d files" %
          (files, hits, changed))


def update_verifier_expectations():
    """Keep scripts/verify-sitemaps.py usable instead of leaving it stale.

    It already drifted (expected 139 while the shipped files had 160); this
    pass brings it to the new total: 160 + 33 new /guides/ - 4 retired twins.
    """
    p = ROOT / "scripts" / "verify-sitemaps.py"
    if not p.exists():
        return
    s = p.read_text(encoding="utf-8")
    s = re.sub(r'EXPECTED_URLS = \{[^}]*\}',
               'EXPECTED_URLS = {"sitemap.xml": 11, "sitemap-en.xml": 189}', s, count=1)
    # The per-language default had already drifted (139 vs 160 shipped); keep
    # it in sync with the new 160 + 33 - 4 = 189 URL set.
    s = s.replace('EXPECTED_URLS.get(name, 139)', 'EXPECTED_URLS.get(name, 189)')
    old = 'INTENTIONAL_REMOVALS = ("/private/architecture/",)'
    new = ('INTENTIONAL_REMOVALS = ("/private/architecture/",\n'
           '                         "/blog/' + '", "/blog/'.join(WEAK) + '",)')
    if old in s:
        s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8", newline="")
    print("verify-sitemaps.py expectations updated to 189")


def main():
    add_robots_meta()
    remove_from_sitemaps()
    repoint_internal_links()
    update_verifier_expectations()
    print("done. Weak URLs stay 200; no 301, no file deletion, no hreflang change.")


if __name__ == "__main__":
    main()
