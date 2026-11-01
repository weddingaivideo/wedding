#!/usr/bin/env python3
"""
Verify the sitemap XML files after the dedupe pass.

Checks, for every sitemap at the repo root:
  * the file still parses with xml.etree.ElementTree
  * total <url> entries == number of unique <loc> values   (zero duplicates)
  * total xhtml:link entries == number of unique (hreflang, href) pairs
    counted inside each <url> block                          (zero duplicates)
  * the root element still declares the sm / xhtml / image namespaces with the
    same prefixes as the pre-edit version
  * the unique <loc> set is unchanged, EXCEPT for the one intentional removal
    of /private/architecture/ (see scripts/strip-private-from-sitemaps.py)
  * encoding (UTF-8, no BOM) and line endings (LF) are unchanged

The "before" state is read from git HEAD, which is authoritative here because
the working tree was clean for these files before the edit.

Exit code 0 = all checks pass.
"""
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "xhtml": "http://www.w3.org/1999/xhtml",
    "image": "http://www.google.com/schemas/sitemap-image/1.1",
}
SM = "{%s}" % NS["sm"]
XHTML = "{%s}" % NS["xhtml"]

LANGUAGES = ["ar", "de", "en", "es", "fr", "hi", "ja", "pt", "ru", "th", "zh"]
FILES = ["sitemap.xml"] + [f"sitemap-{lang}.xml" for lang in LANGUAGES]

EXPECTED_URLS = {"sitemap.xml": 11, "sitemap-en.xml": 139}

# The one <loc> that was deliberately removed from the 10 language sitemaps:
# /private/architecture/ is a LOCAL TOOLING directory in this repo, it has no
# html source, it answers 404 live, and robots.txt disallows /private/.
# Anything else that differs from HEAD is an accidental loss and still fails.
INTENTIONAL_REMOVALS = ("/private/architecture/",)

failures = []


def fail(msg):
    failures.append(msg)
    print("  FAIL  " + msg)


def git_head(path):
    """Pre-edit content of `path` from git HEAD (None if not tracked)."""
    r = subprocess.run(["git", "show", f"HEAD:{path.name}"], cwd=REPO,
                       capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8")


def ns_decls(text):
    """Namespace prefix -> uri declared on the root element."""
    m = re.search(r"<(urlset|sitemapindex)\b[^>]*>", text)
    head = m.group(0) if m else text[:text.index(">") + 1]
    return {mm.group(1) or "": mm.group(2) for mm in
            re.finditer(r'xmlns(?::([A-Za-z0-9_.-]+))?\s*=\s*"([^"]*)"', head)}


def stats(text):
    """Counts for a sitemap (or sitemap index) document."""
    root = ET.fromstring(text)
    urls = [c for c in root if c.tag == SM + "url"]
    index_entries = [c for c in root if c.tag == SM + "sitemap"]

    locs = []
    for u in urls:
        el = u.find(SM + "loc")
        locs.append(el.text.strip() if el is not None and el.text else None)
    index_locs = []
    for s in index_entries:
        el = s.find(SM + "loc")
        index_locs.append(el.text.strip() if el is not None and el.text else None)

    total_links = 0
    dup_pair_in_block = 0
    for u in urls:
        pairs = [(e.get("hreflang"), e.get("href")) for e in u.findall(XHTML + "link")]
        total_links += len(pairs)
        seen = set()
        for p in pairs:
            if p in seen:
                dup_pair_in_block += 1
            seen.add(p)

    return {
        "root_tag": root.tag,
        "url_count": len(urls),
        "index_count": len(index_entries),
        "locs": locs,
        "index_locs": index_locs,
        "unique_locs": sorted(set(l for l in locs if l is not None)),
        "dup_loc_count": len(locs) - len(set(locs)),
        "link_count": total_links,
        "dup_pair_in_block": dup_pair_in_block,
        "ns": ns_decls(text),
    }


def main():
    print("=" * 100)
    print("SITEMAP VERIFICATION")
    print("=" * 100)

    print("\n--- per-file counts (after edit) ---")
    hdr = (f"{'file':<18} {'urls':>5} {'uniq_loc':>9} {'dup_loc':>8} "
           f"{'links':>6} {'dup_pair':>9}  parses  ns")
    print(hdr)
    print("-" * 100)

    for name in FILES:
        path = REPO / name
        raw_bytes = path.read_bytes()
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            fail(f"{name}: not valid UTF-8: {e}")
            continue
        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            fail(f"{name}: unexpected UTF-8 BOM")
        if b"\r\n" in raw_bytes:
            fail(f"{name}: CRLF line endings introduced")
        try:
            s = stats(text)
        except ET.ParseError as e:
            fail(f"{name}: XML parse error: {e}")
            continue

        dup_loc = s["dup_loc_count"]
        dup_pair = s["dup_pair_in_block"]
        ok = (dup_loc == 0 and dup_pair == 0)
        print(f"{name:<18} {s['url_count']:>5} {len(s['unique_locs']):>9} "
              f"{dup_loc:>8} {s['link_count']:>6} {dup_pair:>9}  "
              f"{'yes':<5}  {'ok' if s['ns'] else 'MISSING'}")

        if dup_loc != 0:
            fail(f"{name}: {dup_loc} duplicate <loc> entries remain")
        if dup_pair != 0:
            fail(f"{name}: {dup_pair} duplicate (hreflang, href) pairs remain in a <url> block")
        if s["url_count"] != len(s["unique_locs"]):
            fail(f"{name}: <url> count {s['url_count']} != unique <loc> {len(s['unique_locs'])}")

        is_index = s["root_tag"] == SM + "sitemapindex"
        if is_index:
            # the index is a <sitemapindex>: it holds <sitemap> entries, not
            # <url> blocks, and it never declared the xhtml/image namespaces.
            if len(s["index_locs"]) != len(set(s["index_locs"])):
                fail(f"{name}: duplicate <loc> in the sitemap index")
            if s["ns"].get("") != NS["sm"]:
                fail(f"{name}: index does not declare the default sitemap namespace")
            continue

        # namespace declarations must match the pre-edit file
        before = git_head(path)
        if before is None:
            fail(f"{name}: not in git HEAD, cannot compare against pre-edit state")
        else:
            b = stats(before)
            if b["ns"] != s["ns"]:
                fail(f"{name}: namespace declarations changed\n"
                     f"        before: {b['ns']}\n        after:  {s['ns']}")
            for prefix, uri in (("", NS["sm"]), ("xhtml", NS["xhtml"]),
                                ("image", NS["image"])):
                if s["ns"].get(prefix) != uri:
                    fail(f"{name}: root does not declare "
                         f"{prefix or 'sm'}={uri} (got {s['ns'].get(prefix)!r})")
            # The unique <loc> set may differ from HEAD only by the one
            # intentional removal.  Anything else that disappeared is an
            # accidental loss and must fail the gate.
            if b["unique_locs"] != s["unique_locs"]:
                lost = set(b["unique_locs"]) - set(s["unique_locs"])
                gained = set(s["unique_locs"]) - set(b["unique_locs"])
                unexpected_lost = {u for u in lost
                                   if not any(m in u for m in INTENTIONAL_REMOVALS)}
                if gained:
                    fail(f"{name}: <loc> entries GAINED vs HEAD "
                         f"(gained={sorted(gained)})")
                if unexpected_lost:
                    fail(f"{name}: <loc> entries LOST vs HEAD "
                         f"(lost={sorted(unexpected_lost)})")
                intentional_lost = sorted(lost - unexpected_lost)
                if intentional_lost:
                    print(f"        (intentional removal: "
                          f"{', '.join(intentional_lost)})")

        # no sitemap may advertise a robots-disallowed, 404 path
        for loc in s["unique_locs"]:
            if "/private/" in loc:
                fail(f"{name}: still lists a /private/ URL: {loc}")

        # expected url count
        expected = EXPECTED_URLS.get(name, 139)
        if s["url_count"] != expected:
            fail(f"{name}: expected {expected} <url> entries, found {s['url_count']}")

    print("\n--- before -> after summary ---")
    print(f"{'file':<18} {'urls':>12} {'uniq_loc':>13} {'xhtml:link':>13}")
    print("-" * 60)
    for name in FILES:
        path = REPO / name
        after = stats(path.read_text(encoding="utf-8"))
        before = git_head(path)
        if before is None:
            print(f"{name:<18} {'?':>12} {'?':>13} {'?':>13}")
            continue
        b = stats(before)
        print(f"{name:<18} {b['url_count']:>5} -> {after['url_count']:<4} "
              f"{len(b['unique_locs']):>5} -> {len(after['unique_locs']):<5} "
              f"{b['link_count']:>5} -> {after['link_count']:<5}")

    print("\n--- index file (sitemap.xml) ---")
    idx = stats((REPO / "sitemap.xml").read_text(encoding="utf-8"))
    b_idx = stats(git_head(REPO / "sitemap.xml"))
    if idx["index_locs"] == b_idx["index_locs"]:
        print(f"  sitemap.xml: UNCHANGED ({idx['index_count']} sitemap entries, "
              f"{len(set(idx['index_locs']))} unique <loc>, 0 duplicates)")
    else:
        print(f"  sitemap.xml: CHANGED -> {idx['index_locs']}")

    print()
    if failures:
        print(f"RESULT: {len(failures)} FAILURE(S)")
        for f in failures:
            print("  - " + f)
        return 1
    print("RESULT: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
