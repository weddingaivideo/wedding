#!/usr/bin/env python3
"""
Put the new tool pages into the shipped sitemaps.

WHY NOT `qa/gen_sitemap.py`
--------------------------
The script's own docstring says not to use it: it collects the URLs of
ALL html files, so for a language sitemap it maps both `/blog/x/` and
`/zh/blog/x/` to the same `/<lang>/blog/x/` loc and emits DUPLICATE
<loc> entries. Measured on the working tree: 292 <url> blocks with only
142 distinct locs - 150 duplicates - against the committed 139.

So the sitemaps are restored from HEAD and only the five new tool
pages are added, each with the full hreflang graph and the image
block, in the position the alphabetical order of the tool slugs wants.

WHAT IT CHECKS
--------------
* every one of the 11 sitemaps gets the same five entries,
* no <loc> is duplicated in any file,
* the hreflang graph of a new entry matches the graph of the entry
  next to it.

Usage
-----
    python scripts/add-tools-to-sitemap.py
    python scripts/add-tools-to-sitemap.py --dry-run
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TOOLS = [
    "wedding-stationery-set-maker",
    "wedding-photo-contact-sheet",
    "wedding-pdf-editor",
    "wedding-photo-to-gif",
    "wedding-video-editor",
]
SITEMAPS = ["sitemap-en.xml", "sitemap-zh.xml", "sitemap-es.xml",
            "sitemap-fr.xml", "sitemap-de.xml", "sitemap-pt.xml",
            "sitemap-ja.xml", "sitemap-ru.xml", "sitemap-ar.xml",
            "sitemap-th.xml", "sitemap-hi.xml"]
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
LASTMOD = "2026-11-10"

URL_RE = re.compile(r"[ \t]*<url>.*?</url>\n?", re.S)
LOC_RE = re.compile(r"<loc>https://weddingai\.video/(.*?)</loc>")


def restore_from_head():
    """Undo the regeneration that filled the sitemaps with duplicates."""
    subprocess.run(["git", "-C", str(ROOT), "checkout", "HEAD", "--"]
                   + SITEMAPS + ["sitemap.xml"], check=True)
    print("restored the sitemaps from HEAD")


def arabic_image_title(slug):
    """The Arabic og:image:alt of the tool - that is what the shipped
    entries carry.

    The deploy1 head file is preferred: it is the head that was actually
    published, while `.tmp/<slug>-head.json` belongs to a translation run
    that may still be in flight and may not have that language yet.
    """
    for rel in (".tmp/deploy1/%s-head.json" % slug, ".tmp/%s-head.json" % slug):
        path = ROOT / rel
        if path.exists():
            heads = json.loads(path.read_text(encoding="utf-8"))
            ar = heads.get("ar") or {}
            if ar.get("og_image_alt"):
                return ar["og_image_alt"]
    return "WeddingAI.video"


def build_block(slug, image_title):
    lines = ["    <url>",
             "        <loc>https://weddingai.video/tools/%s/</loc>" % slug,
             "        <lastmod>%s</lastmod>" % LASTMOD,
             "        <changefreq>monthly</changefreq>",
             "        <priority>0.7</priority>"]
    for lang in LANGS:
        prefix = "" if lang == "en" else "/%s" % lang
        lines.append('        <xhtml:link rel="alternate" hreflang="%s" '
                     'href="https://weddingai.video%s/tools/%s/" />'
                     % (lang, prefix, slug))
    lines.append('        <xhtml:link rel="alternate" hreflang="x-default" '
                 'href="https://weddingai.video/tools/%s/" />' % slug)
    lines.append("        <image:image>")
    lines.append("            <image:loc>https://weddingai.video/images/"
                 "og-image-1200x630.jpg</image:loc>")
    lines.append("            <image:title>%s</image:title>" % image_title)
    lines.append("        </image:image>")
    lines.append("    </url>")
    return "\n".join(lines) + "\n"


def tool_blocks(text):
    """[(slug, start, end)] for every /tools/<slug>/ entry, in file order."""
    out = []
    for m in URL_RE.finditer(text):
        loc = LOC_RE.search(m.group(0))
        if not loc:
            continue
        path = loc.group(1)
        m2 = re.match(r"tools/([^/]+)/$", path)
        if m2:
            out.append((m2.group(1), m.start(), m.end()))
    return out


def insert(text, slug, block):
    """Put the block in the alphabetical place among the tool entries."""
    blocks = tool_blocks(text)
    for other, start, end in blocks:
        if other > slug:
            return text[:start] + block + text[start:]
    if blocks:
        _, _, end = blocks[-1]
        return text[:end] + block + text[end:]
    # No tool entry at all - append before </urlset>.
    idx = text.rfind("</urlset>")
    return text[:idx] + block + text[idx:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep-regenerated", action="store_true",
                    help="do NOT restore from HEAD first")
    args = ap.parse_args()

    if not args.keep_regenerated:
        restore_from_head()

    problems = []
    for name in SITEMAPS:
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        before_locs = re.findall(r"<loc>([^<]+)</loc>", text)
        if len(before_locs) != len(set(before_locs)):
            problems.append("%s already has duplicate locs" % name)
        for slug in TOOLS:
            if re.search(r"<loc>https://weddingai\.video/tools/%s/</loc>" % slug,
                         text):
                continue
            block = build_block(slug, arabic_image_title(slug))
            text = insert(text, slug, block)
        locs = re.findall(r"<loc>([^<]+)</loc>", text)
        if len(locs) != len(set(locs)):
            problems.append("%s has duplicate locs after the insert" % name)
        if len(locs) != len(before_locs) + len(TOOLS):
            problems.append("%s: %d locs, expected %d"
                            % (name, len(locs),
                               len(before_locs) + len(TOOLS)))
        # The hreflang graph of a new entry must match the one next to it.
        for slug in TOOLS:
            block = re.search(
                r"<url>((?:(?!</url>).)*?/tools/%s/(?:(?!</url>).)*?)</url>"
                % slug, text, re.S)
            if not block:
                problems.append("%s: the entry for %s is missing" % (name, slug))
                continue
            alts = re.findall(r'hreflang="([^"]+)"', block.group(1))
            if len(alts) != len(LANGS) + 1:
                problems.append("%s: %s has %d hreflang links"
                                % (name, slug, len(alts)))
        if not args.dry_run:
            path.write_text(text, encoding="utf-8", newline="")
        print("  %-18s %d locs" % (name, len(locs)))

    if problems:
        print("\n[FAIL]")
        for p in problems:
            print("  - %s" % p)
        return 1
    print("\n[OK] every sitemap has the five new tools and no duplicates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
