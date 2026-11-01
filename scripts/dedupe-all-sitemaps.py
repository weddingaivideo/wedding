#!/usr/bin/env python3
"""
Dedupe every sitemap XML at the repo root (index + 11 language files).

Semantics (generalised from scripts/_dedup_sitemap.py, which only handled
sitemap-en.xml):

  1. Remove duplicate <url> blocks -- for each repeated <loc>, keep the FIRST
     occurrence and delete the later duplicates entirely (whole <url>...</url>
     block including children).
  2. Remove duplicate xhtml:link alternates INSIDE a surviving <url> block --
     keep the first occurrence of each (hreflang, href) pair.  The same href
     under a different hreflang is a legitimate, distinct link and is kept.
  3. Nothing else changes: no reformatting, no reordering, no change to
     <lastmod>/<changefreq>/<priority>/<loc>/<image:image> content and no
     change to the namespace declarations on the root <urlset>.

Parsing uses xml.etree.ElementTree with the same namespace registrations as
scripts/_dedup_sitemap.py, so prefix handling (sm default ns, xhtml, image) is
identical.  The edit itself is performed as text surgery on the raw source so
that every byte outside the removed lines survives untouched -- a full
ET re-serialization would rewrite the whitespace/attribute style of the files.

Usage:
    python scripts/dedupe-all-sitemaps.py --dry-run   # analyse only
    python scripts/dedupe-all-sitemaps.py             # rewrite in place
    python scripts/dedupe-all-sitemaps.py --audit     # raw-text cross-check
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "xhtml": "http://www.w3.org/1999/xhtml",
    "image": "http://www.google.com/schemas/sitemap-image/1.1",
}
for _prefix, _uri in NS.items():
    ET.register_namespace("" if _prefix == "sm" else _prefix, _uri)

SM = "{%s}" % NS["sm"]
XHTML = "{%s}" % NS["xhtml"]

LANGUAGES = ["ar", "de", "en", "es", "fr", "hi", "ja", "pt", "ru", "th", "zh"]
FILES = ["sitemap.xml"] + [f"sitemap-{lang}.xml" for lang in LANGUAGES]

PRIVATE_PATH = "/private/architecture/"

URL_BLOCK_RE = re.compile(r"<url\b[^>]*>.*?</url>", re.DOTALL)
LINK_RE = re.compile(r"<xhtml:link\b[^>]*/>")


# --------------------------------------------------------------------------- #
# analysis
# --------------------------------------------------------------------------- #
def analyse(path):
    """Parse a sitemap and return the facts we need to act on and to report."""
    raw = path.read_text(encoding="utf-8")
    root = ET.fromstring(raw)

    urls = [c for c in root if c.tag == SM + "url"]
    locs = []
    links_per_block = []
    for u in urls:
        loc_el = u.find(SM + "loc")
        locs.append(loc_el.text.strip() if loc_el is not None and loc_el.text else None)
        links_per_block.append(
            [(el.get("hreflang"), el.get("href"))
             for el in u.findall(XHTML + "link")]
        )

    all_links = [p for blk in links_per_block for p in blk]
    uniq_links = []
    seen = set()
    for p in all_links:
        if p not in seen:
            seen.add(p)
            uniq_links.append(p)

    return {
        "path": path,
        "raw": raw,
        "root": root,
        "urls": urls,
        "locs": locs,
        "links_per_block": links_per_block,
        "url_count": len(urls),
        "uniq_loc_count": len(set(locs)),
        "dup_locs": sorted({l for l in locs if locs.count(l) > 1}),
        "link_count": len(all_links),
        "uniq_link_count": len(uniq_links),
        "has_private": any(l and PRIVATE_PATH in l for l in locs),
    }


def dup_pairs_per_block(links_per_block):
    """Number of (hreflang, href) pairs that repeat inside a single <url>."""
    dups = 0
    for blk in links_per_block:
        seen = set()
        for p in blk:
            if p in seen:
                dups += 1
            seen.add(p)
    return dups


# --------------------------------------------------------------------------- #
# text surgery
# --------------------------------------------------------------------------- #
def _cut_span(raw, start, end):
    """Return the span to cut for removing raw[start:end].

    If the element sits alone on its line(s) the whole line is removed so no
    blank line is left behind.  When the element shares a line with other
    content (e.g. sitemap-en.xml has "<urlset ...><url>" on one line) only the
    element itself is removed, and the trailing part of that line is dropped
    with it when nothing else follows.
    """
    ls = raw.rfind("\n", 0, start) + 1
    le = raw.find("\n", end)
    le = len(raw) if le == -1 else le + 1
    prefix = raw[ls:start]
    suffix = raw[end:le]
    p_blank = not prefix.strip()
    s_blank = not suffix.strip()
    if p_blank and s_blank:
        return ls, le
    if p_blank and not s_blank:
        return ls, end
    if not p_blank and s_blank:
        return start, le
    return start, end


def compute_new_text(info):
    """Return (new_text, removed_url_blocks, removed_link_pairs)."""
    raw = info["raw"]
    blocks = list(URL_BLOCK_RE.finditer(raw))
    if len(blocks) != info["url_count"]:
        raise SystemExit(
            f"[ABORT] {info['path'].name}: found {len(blocks)} <url> blocks in the "
            f"text but {info['url_count']} in the parsed tree"
        )

    removals = []          # (start, end) spans to cut out of raw
    seen_loc = set()
    removed_blocks = []
    removed_links = []

    for idx, (blk, loc) in enumerate(zip(blocks, info["locs"])):
        if loc is None:
            continue
        if loc in seen_loc:
            removals.append(_cut_span(raw, blk.start(), blk.end()))
            removed_blocks.append((idx, loc))
            continue
        seen_loc.add(loc)

        # dedupe alternates inside the surviving block
        blk_text = blk.group(0)
        link_matches = list(LINK_RE.finditer(blk_text))
        pairs = info["links_per_block"][idx]
        if len(link_matches) != len(pairs):
            raise SystemExit(
                f"[ABORT] {info['path'].name}: block {idx} has {len(link_matches)} "
                f"xhtml:link elements in the text but {len(pairs)} in the tree"
            )

        seen_pair = set()
        for m, pair in zip(link_matches, pairs):
            if pair in seen_pair:
                s = blk.start() + m.start()
                e = blk.start() + m.end()
                removals.append(_cut_span(raw, s, e))
                removed_links.append((idx, pair))
            else:
                seen_pair.add(pair)

    removals.sort(key=lambda t: t[0])
    out = raw
    for s, e in reversed(removals):
        out = out[:s] + out[e:]
    return out, removed_blocks, removed_links


# --------------------------------------------------------------------------- #
# verification
# --------------------------------------------------------------------------- #
def ns_decls_from_text(text):
    """Namespace prefix -> uri as declared on the root element of `text`."""
    m = re.search(r"<urlset\b[^>]*>", text)
    head = m.group(0) if m else text[:text.index(">") + 1]
    return {mm.group(1) or "": mm.group(2) for mm in
            re.finditer(r'xmlns(?::([A-Za-z0-9_.-]+))?\s*=\s*"([^"]*)"', head)}


def root_ns_decls(path):
    """Namespace prefix -> uri as declared on the root element."""
    return ns_decls_from_text(path.read_text(encoding="utf-8"))


def verify(path, expect_urls=None):
    """Re-parse a written file and prove the invariants hold."""
    raw = path.read_text(encoding="utf-8")
    root = ET.fromstring(raw)
    urls = [c for c in root if c.tag == SM + "url"]

    locs = [u.find(SM + "loc").text.strip() for u in urls if u.find(SM + "loc") is not None]
    uniq_locs = set(locs)

    total_links = 0
    dup_in_block = 0
    for u in urls:
        pairs = [(el.get("hreflang"), el.get("href")) for el in u.findall(XHTML + "link")]
        total_links += len(pairs)
        seen = set()
        for p in pairs:
            if p in seen:
                dup_in_block += 1
            seen.add(p)

    decls = root_ns_decls(path)
    return {
        "url_count": len(urls),
        "uniq_loc": len(uniq_locs),
        "dup_locs": len(locs) - len(uniq_locs),
        "link_count": total_links,
        "dup_links_in_block": dup_in_block,
        "ns": decls,
        "locs": locs,
    }


def raw_text_audit(path):
    """Independent raw-text measurement, deliberately NOT using ElementTree.

    Used to cross-check the ET-based numbers: a duplicate that only one of the
    two methods can see is a bug in the method, not in the file.
    """
    raw = path.read_text(encoding="utf-8")
    blocks = list(URL_BLOCK_RE.finditer(raw))
    attr_re = re.compile(r'hreflang="([^"]*)"\s+href="([^"]*)"')

    total = 0
    within_block_dup = 0
    pair_counts = {}
    href_counts = {}
    per_block = {}
    for b in blocks:
        pairs = []
        for m in LINK_RE.finditer(b.group(0)):
            hit = attr_re.search(m.group(0))
            if hit:
                pairs.append(hit.groups())
        per_block[len(pairs)] = per_block.get(len(pairs), 0) + 1
        total += len(pairs)
        seen = set()
        for p in pairs:
            if p in seen:
                within_block_dup += 1
            seen.add(p)
            pair_counts[p] = pair_counts.get(p, 0) + 1
            href_counts[p[1]] = href_counts.get(p[1], 0) + 1
    return {
        "blocks": len(blocks),
        "total_links": total,
        "within_block_dup_pairs": within_block_dup,
        "global_unique_pairs": len(pair_counts),
        "global_unique_hrefs": len(href_counts),
        "per_block_counts": dict(sorted(per_block.items())),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--audit", action="store_true")
    args = ap.parse_args()

    if args.audit:
        print("raw-text audit (no ElementTree)")
        print(f"{'file':<18} {'blocks':>7} {'links':>7} {'uniq_pair':>10} "
              f"{'uniq_href':>10} {'dup_in_blk':>11}  links-per-block")
        print("-" * 100)
        for name in FILES:
            a = raw_text_audit(REPO / name)
            print(f"{name:<18} {a['blocks']:>7} {a['total_links']:>7} "
                  f"{a['global_unique_pairs']:>10} {a['global_unique_hrefs']:>10} "
                  f"{a['within_block_dup_pairs']:>11}  {a['per_block_counts']}")
        print("\n/private/architecture/ occurrences:")
        for name in FILES:
            raw = (REPO / name).read_text(encoding="utf-8")
            hits = re.findall(r"<loc>([^<]*private/architecture[^<]*)</loc>", raw)
            if hits:
                print(f"  {name}: {len(hits)} -> {sorted(set(hits))}")

        print("\nblocks whose xhtml:link count != the modal count:")
        for name in FILES:
            raw = (REPO / name).read_text(encoding="utf-8")
            blocks = list(URL_BLOCK_RE.finditer(raw))
            counts = [len(LINK_RE.findall(b.group(0))) for b in blocks]
            if not counts:
                continue
            modal = max(set(counts), key=counts.count)
            for i, (b, c) in enumerate(zip(blocks, counts)):
                if c != modal:
                    loc = re.search(r"<loc>([^<]*)</loc>", b.group(0))
                    print(f"  {name} block {i}: links={c} (modal {modal}) "
                          f"loc={loc.group(1) if loc else '?'}")
        return 0

    print(f"{'file':<18} {'urls':>5} {'uniq_loc':>9} {'dup_loc':>7} "
          f"{'links':>6} {'uniq_lnk':>8} {'dup_lnk_blk':>11}  private")
    print("-" * 84)
    for name in FILES:
        path = REPO / name
        info = analyse(path)
        dlb = dup_pairs_per_block(info["links_per_block"])
        print(f"{name:<18} {info['url_count']:>5} {info['uniq_loc_count']:>9} "
              f"{info['url_count'] - info['uniq_loc_count']:>7} "
              f"{info['link_count']:>6} {info['uniq_link_count']:>8} "
              f"{dlb:>11}  {'YES' if info['has_private'] else 'no'}")

    if args.dry_run:
        print("\n[dry-run] nothing written")
        return 0

    for name in FILES:
        path = REPO / name
        info = analyse(path)
        if info["url_count"] == 0:
            print(f"\n{name}: no <url> blocks (index file) - left untouched")
            continue
        new_text, removed_blocks, removed_links = compute_new_text(info)
        if new_text == info["raw"]:
            print(f"\n{name}: already clean - left untouched")
            continue

        # sanity: the result must parse and keep the same unique loc set
        try:
            new_root = ET.fromstring(new_text)
        except ET.ParseError as exc:
            raise SystemExit(f"[ABORT] {name}: rewritten XML does not parse: {exc}")

        new_locs = [c.find(SM + "loc").text.strip()
                    for c in new_root if c.tag == SM + "url"]
        if set(new_locs) != set(info["locs"]):
            raise SystemExit(f"[ABORT] {name}: unique <loc> set changed")

        # the namespace declarations on the root must be byte-identical
        old_ns = root_ns_decls(path)
        new_ns = ns_decls_from_text(new_text)
        if old_ns != new_ns:
            raise SystemExit(
                f"[ABORT] {name}: namespace declarations changed\n"
                f"        before: {old_ns}\n        after:  {new_ns}")

        # only whole lines may have been removed -- the new text's lines must be
        # a subsequence of the old text's lines (nothing rewritten, only deleted)
        old_lines = info["raw"].splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        it = iter(old_lines)
        if not all(any(ol == nl for ol in it) for nl in new_lines):
            raise SystemExit(
                f"[ABORT] {name}: rewritten text is not a pure line-deletion of the original")

        tmp = path.with_suffix(".xml.tmp")
        tmp.write_text(new_text, encoding="utf-8", newline="")
        tmp.replace(path)
        print(f"\n{name}: removed {len(removed_blocks)} duplicate <url> blocks, "
              f"{len(removed_links)} duplicate xhtml:link alternates "
              f"({info['url_count']} -> {len(new_locs)} urls, "
              f"{info['link_count']} -> {info['link_count'] - len(removed_links)} links)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
