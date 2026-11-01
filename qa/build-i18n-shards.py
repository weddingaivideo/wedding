"""Split the i18n dictionaries by key namespace, and bundle the pages that
need more shards than the runtime can fetch.

PART 1 - WHY (revised)
----------------------
The first attempt sharded per page, but a key used by several pages (common
footer/header keys) was duplicated in each of those shards, so the total
payload grew (en 6.2 MB -> 9.7 MB) instead of shrinking.

Sharding by KEY NAMESPACE stores every key exactly once. A page then loads
the few namespaces it needs:
    i18n/{lang}.json              -> the manifest: namespace -> shard file
    i18n/shards/{lang}/{ns}.json   -> the keys of one namespace

Namespaces are the first two dotted segments of a key (e.g.
"blog.wedding-video-photo-checklist", "index.p_text", "services.common"),
which matches how the dictionaries were authored. The biggest namespace will
be a few MB, so those are split further into numbered parts if needed.

PART 2 - THE BUNDLE ESCAPE HATCH
--------------------------------
Namespace granularity is too coarse for ONE page: blog/index.html binds the
title and the meta description of ~100 articles, but each of those articles
lives in its own namespace that holds the ENTIRE article body (~1000-1400
keys, 170-370 KB each). So the hub needed 111 namespaces - over both the
40-shard budget of functions/_lib/i18n-shards.js and the 50-subrequest
limit of the CF Pages Free plan - and the union of those namespaces is
85-87% of the whole dictionary (9-15 MB). The hub therefore fell back to
the full dictionary and stayed 503-prone.

Re-bundling by prefix does NOT help: the payload would be the same 9-15 MB
and parsing it is exactly what blows the CPU limit.

What DOES help is a page bundle: a single file holding exactly the keys that
ONE page binds (plus the few keys the middleware looks up by a fixed name).
For the blog hub that is ~190 card strings plus ~47 fixed keys - about 60 KB
instead of 9-15 MB - fetched with ONE subrequest instead of 111.

A bundle is keyed by the hash of the page's NAMESPACE SET, because that is
what the runtime can compute from the html it is about to serve. The runtime
looks the hash up in the manifest and, if it finds a bundle, fetches that one
file instead of the namespace shards. No bundle -> the old namespace path,
so the behaviour degrades instead of breaking.

PART 3 - THE KEY PARSER
-----------------------
The parser below must agree EXACTLY with namespaceOf() in
functions/_lib/i18n-shards.js and with the runtime's own extraction of
data-i18n / data-i18n-attr bindings. The previous version of this builder
only understood `data-i18n="key"` and `data-i18n-attr="content:key"`:

  * `data-i18n-attr="title:key"`      -> parsed as the key "title:key",
                                          whose namespace came out as
                                          "_root" - the shard was never
                                          built and the binding silently
                                          stayed English.
  * `data-i18n-attr="content:a|b"`     -> parsed as the single key
                                          "a|b", so only one of the two
                                          namespaces was ever requested.

Both bugs made the runtime miss shards, which shows up as untranslated text
rather than as an error. scripts/verify-i18n-shards.py now cross-checks the
Python and the JavaScript namespace rules against each other, so the two
cannot drift apart silently again.

PART 4 - THE WRITE PATH MUST NOT BE DESTRUCTIVE
-----------------------------------------------
This builder used to start with

    shutil.rmtree(i18n/shards)

and then rebuild every language from scratch. That makes the WHOLE tree
invalid for the whole duration of the run: an interruption (a killed agent,
a token limit, a concurrent run) leaves six of the eleven languages missing
from disk, and the live site serves them with the English source. That
happened on 2026-11-01 - the tree was left with `en` only.

The build is now per language and transactional:

    1. build the language into .tmp/shards-staging/<lang>/   (never the live tree)
    2. validate every file in it parses as JSON
    3. move the live .tmp/shards-trash/<lang>.<ts>/ out of the way
    4. rename staging -> i18n/shards/<lang>       (one atomic move)
    5. delete the trash copy

A crash therefore loses at most ONE language, and the freshness gate
(scripts/verify-i18n-shards.py) reports exactly which one. A run that is
killed between steps 3 and 4 is recovered on the next run: the trash copy
is put back if the live directory is missing.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
from collections import defaultdict

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"
os.chdir(ROOT)

LANGS = ["en", "zh", "ja", "ar", "es", "fr", "de", "pt", "ru", "th", "hi"]
PAT = re.compile(r'data-i18n(?:-attr)?="([^"]+)"')
SKIP = ("node_modules", "qa/", "private/", ".tmp/", ".git/", "i18n/",
        "internal-tools/", "scripts/")
MAX_SHARD = 700 * 1024      # 700 KB

# Must equal MAX_SHARDS in functions/_lib/i18n-shards.js. A page that needs
# more shards than this cannot be served shard-by-shard inside the CF Pages
# Free subrequest budget, so it gets a bundle instead.
MAX_SHARDS = 40

# Keys the middleware looks up by a FIXED name, not through a data-i18n
# attribute. A bundle has to carry them too, or the page would lose its
# social-card copy or its localized FAQ.
#   index.*    -> replaceOgTwitterMeta()   (homepage only)
#   pricing.*  -> replacePricingMeta()     (/pricing/ only)
#   *_faq.qN.* -> replaceFaqJsonLd()       (any page with a FAQPage schema)
EXTRA_KEY_PREFIXES = ("index.og_title", "index.og_description",
                      "index.twitter_title", "index.twitter_description",
                      "pricing.meta_description", "pricing.og_title",
                      "pricing.og_description")
EXTRA_KEY_PREFIXES_FAQ = ("homepage_faq.q", "pricing_faq.q")

# ---- the write path -------------------------------------------------------
# The live tree is i18n/shards/<lang>/. It is never built into directly.
# Everything is assembled under .tmp/ (gitignored AND in .assetsignore), so
# a staging directory can never end up deployed.
SHARD_ROOT = os.path.join(ROOT, "i18n", "shards")
STAGE_ROOT = os.path.join(ROOT, ".tmp", "shards-staging")
TRASH_ROOT = os.path.join(ROOT, ".tmp", "shards-trash")


def write_json_atomic(path, obj):
    """Write JSON through a temp file + fsync + os.replace.

    A plain open(path, "w") truncates the target first: a crash mid-write
    leaves a 0-byte file, and a later read sees "the dictionary is empty"
    instead of "the write failed". i18n/<lang>.json was truncated to 0 bytes
    exactly that way once already. os.replace is atomic on Windows too.
    """
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-write-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def stage_dir(lang):
    return os.path.join(STAGE_ROOT, lang)


def recover_trash():
    """Recover from a run that was killed between 'move live aside' and
    'move staging in': the live language directory is missing and the copy
    that was moved aside is still around. Put it back."""
    if not os.path.isdir(TRASH_ROOT):
        return
    for name in sorted(os.listdir(TRASH_ROOT)):
        lang = name.rsplit(".", 1)[0]
        live = os.path.join(SHARD_ROOT, lang)
        if os.path.isdir(live):
            shutil.rmtree(os.path.join(TRASH_ROOT, name), ignore_errors=True)
            continue
        os.makedirs(SHARD_ROOT, exist_ok=True)
        os.replace(os.path.join(TRASH_ROOT, name), live)
        print(f"  recovered {lang} from {name}")


def swap_in(lang, staged):
    """Replace the live language directory with the staged one.

    Two renames: the live directory is moved aside first (os.replace cannot
    overwrite a directory on Windows), then the staged directory is moved in.
    The window in which i18n/shards/<lang> does not exist is a single
    rename wide, and the freshness gate reports it if a run dies there.
    """
    live = os.path.join(SHARD_ROOT, lang)
    ts = str(int(time.time() * 1000))
    trash = os.path.join(TRASH_ROOT, f"{lang}.{ts}")
    os.makedirs(TRASH_ROOT, exist_ok=True)
    if os.path.isdir(live):
        os.replace(live, trash)
    os.replace(staged, live)
    shutil.rmtree(trash, ignore_errors=True)


def ns_of(key):
    """The namespace of a key: its first two dotted segments."""
    p = key.split(".")
    if len(p) == 1:
        return "_root"
    if len(p) == 2:
        return p[0]
    return f"{p[0]}.{p[1]}"


def keys_in_html(text):
    """Every dictionary key an html file binds.

    Handles both spellings:
        data-i18n="blog.foo.title_text.bar"
        data-i18n-attr="content:blog.foo.meta|title:blog.bar.baz"
    The attribute form carries "attr:key" pairs separated by "|", and each
    part may itself use a different namespace.
    """
    out = []
    for m in PAT.finditer(text):
        spec = m.group(1)
        parts = spec.split("|") if "|" in spec else [spec]
        for part in parts:
            c = part.find(":")
            key = part if c == -1 else part[c + 1:]
            key = key.strip()
            if key:
                out.append(key)
    return out


def namespace_set_id(ns_list):
    """Stable id for a set of namespaces.

    SHA-256 over the sorted, newline-joined namespace names, truncated to 16
    hex characters. Both the builder and the runtime must compute the SAME
    value, so the runtime uses the same construction.
    """
    joined = "\n".join(sorted(ns_list))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def extra_keys(full):
    """The fixed-name keys a bundle must carry."""
    out = {}
    for k, v in full.items():
        if k in EXTRA_KEY_PREFIXES:
            out[k] = v
            continue
        if any(k.startswith(p) for p in EXTRA_KEY_PREFIXES_FAQ):
            out[k] = v
    return out


def main():
    # which namespaces and which keys does each page reference?
    page_ns = defaultdict(set)
    page_keys = defaultdict(set)
    for f in glob.glob("**/*.html", recursive=True):
        rel = f.replace(os.sep, "/")
        if any(x in rel for x in SKIP):
            continue
        try:
            t = open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        ks = keys_in_html(t)
        if not ks:
            continue
        page_ns[rel].update(ns_of(k) for k in ks)
        page_keys[rel].update(ks)
    print(f"pages with data-i18n: {len(page_ns)}")

    # pages that need more shards than the runtime can fetch
    heavy = defaultdict(list)
    for rel, ns in page_ns.items():
        if len(ns) > MAX_SHARDS:
            heavy[namespace_set_id(ns)].append(rel)
    print(f"pages over the {MAX_SHARDS}-shard budget: "
          f"{sum(len(v) for v in heavy.values())} "
          f"({len(heavy)} distinct bundle(s))")

    os.makedirs(SHARD_ROOT, exist_ok=True)
    os.makedirs(STAGE_ROOT, exist_ok=True)
    os.makedirs(TRASH_ROOT, exist_ok=True)
    recover_trash()

    langs = args.lang or LANGS
    for lang in langs:
        dpath = os.path.join(ROOT, "i18n", f"{lang}.json")
        if not os.path.exists(dpath):
            print(f"  {lang}: no dictionary, skipped")
            continue
        full = json.load(open(dpath, encoding="utf-8"))

        # build into the staging area, never into the live tree
        lang_dir = stage_dir(lang)
        if os.path.isdir(lang_dir):
            shutil.rmtree(lang_dir, ignore_errors=True)
        os.makedirs(lang_dir, exist_ok=True)

        by_ns = defaultdict(dict)
        for k, v in full.items():
            by_ns[ns_of(k)][k] = v

        manifest = {}
        total = 0
        for ns, kv in by_ns.items():
            # split oversized namespaces into numbered parts
            parts = []
            cur, cur_len = {}, 0
            for k, v in kv.items():
                approx = len(json.dumps(v, ensure_ascii=False)) + len(k) + 4
                if cur and cur_len + approx > MAX_SHARD:
                    parts.append(cur)
                    cur, cur_len = {}, 0
                cur[k] = v
                cur_len += approx
            if cur:
                parts.append(cur)
            if len(parts) == 1:
                fname = f"{ns}.json"
            else:
                fname = f"{ns}.part{n}.json"
                for i, part in enumerate(parts):
                    p = os.path.join(lang_dir, f"{ns}.part{i}.json")
                    write_json_atomic(p, part)
                    total += os.path.getsize(p)
                manifest[ns] = [f"{ns}.part{i}.json" for i in range(len(parts))]
                continue
            p = os.path.join(lang_dir, fname)
            write_json_atomic(p, parts[0])
            total += os.path.getsize(p)
            manifest[ns] = [fname]

        # ---- page bundles -------------------------------------------------
        bundles = {}
        for bid, pages in heavy.items():
            wanted = set()
            for rel in pages:
                wanted |= page_keys[rel]
            payload = {k: full[k] for k in wanted if k in full}
            payload.update(extra_keys(full))
            fname = f"bundle.{bid}.json"
            p = os.path.join(lang_dir, fname)
            write_json_atomic(p, payload)
            total += os.path.getsize(p)
            bundles[bid] = fname
        if bundles:
            manifest["__bundles__"] = bundles

        # ---- validate, then swap the whole language in --------------------
        # Every file must parse. A truncated shard would otherwise become a
        # 500 at request time, long after the build looked fine.
        staged_files = sorted(os.listdir(lang_dir))
        for f in staged_files:
            with open(os.path.join(lang_dir, f), encoding="utf-8") as fh:
                json.load(fh)

        # the manifest is written AFTER the shards are in place, so a manifest
        # never points at a shard file that is not on disk yet
        write_json_atomic(os.path.join(ROOT, "i18n", f"{lang}.manifest.json"),
                          manifest)
        swap_in(lang, lang_dir)

        sizes = [os.path.getsize(os.path.join(SHARD_ROOT, lang, f))
                 for f in staged_files]
        biggest = max(sizes) if sizes else 0
        binfo = ""
        if bundles:
            bs = [os.path.getsize(os.path.join(SHARD_ROOT, lang, f))
                  for f in bundles.values()]
            binfo = (f", {len(bundles)} bundle(s) biggest "
                     f"{max(bs)/1024:.0f} KB")
        print(f"  {lang}: {len(manifest) - len(bundles)} namespaces, "
              f"{len(sizes)} shards, total {total/1e6:.1f} MB, "
              f"biggest {biggest/1024:.0f} KB{binfo}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", action="append",
                    help="rebuild only this language (repeatable)")
    args = ap.parse_args()
    main()
