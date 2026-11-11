#!/usr/bin/env python3
"""Add or refresh the shards for a dictionary, without rebuilding every
language.

`qa/build-i18n-shards.py --lang <lang>` rebuilds one language but still
rewrites every shard of that language. When a dictionary change adds only a
handful of keys, that is a lot of churn for a small edit, and the full
rebuild is slow enough that it gets interrupted.

This script does the same thing, narrowly:

  * a namespace whose shards already carry all of its keys is left ALONE;
  * a namespace that is missing keys is rebuilt with the builder's own rules;
  * a page BUNDLE (for a page over the shard budget) is rebuilt with the
    builder's own rules too.

It imports the builder's own constants and functions so the two cannot
drift: `ns_of`, `namespace_set_id`, `extra_keys`, `MAX_SHARD`, `MAX_SHARDS`,
`EXTRA_KEY_PREFIXES*`, and the atomic write.

Run:  python scripts/add-shards-for-keys.py i18n/ru.json i18n/ru.manifest.json

Always follow it with `python scripts/verify-i18n-shards.py` - that is the
gate, and it checks the bundles as well as the namespace shards.

WHY THE BUNDLE PART MATTERS
----------------------------
A page over the shard budget (the blog hub needs 111 namespaces) is served
from ONE bundle file, not from the namespace shards. So a new key on such a
page has to land in the bundle as well - otherwise the namespace shards are
up to date and the page still serves the OLD text, with a 200 response. The
first version of this script only handled namespaces and the shard gate
caught exactly that.
"""
import glob
import importlib.util
import json
import os
import sys
import tempfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_builder():
    """Import qa/build-i18n-shards.py by path.

    The file name has a hyphen, so it cannot be imported as a module - it
    has to be loaded from its file path.
    """
    path = os.path.join(ROOT, "qa", "build-i18n-shards.py")
    spec = importlib.util.spec_from_file_location("build_i18n_shards", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_i18n_shards"] = mod
    spec.loader.exec_module(mod)
    return mod


B = _load_builder()


def write_json_atomic(path, obj):
    """Same write the builder uses: temp file + fsync + atomic replace.

    A plain open(path, "w") truncates first, so a crash mid-write leaves a
    0-byte file and a later read sees "the dictionary is empty" instead of
    "the write failed". os.replace is atomic on Windows.
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


def split_parts(kv):
    """Split one namespace into shard-sized parts, exactly like the builder."""
    parts = []
    cur, cur_len = {}, 0
    for k, v in kv.items():
        approx = len(json.dumps(v, ensure_ascii=False)) + len(k) + 4
        if cur and cur_len + approx > B.MAX_SHARD:
            parts.append(cur)
            cur, cur_len = {}, 0
        cur[k] = v
        cur_len += approx
    if cur:
        parts.append(cur)
    return parts


def main(dict_path, manifest_path):
    lang = os.path.splitext(os.path.basename(dict_path))[0]
    full = json.load(open(dict_path, encoding="utf-8"))
    manifest = json.load(open(manifest_path, encoding="utf-8"))
    shard_dir = os.path.join(ROOT, "i18n", "shards", lang)

    by_ns = defaultdict(dict)
    for k, v in full.items():
        by_ns[B.ns_of(k)][k] = v

    written = []

    # ---------------------------------------------------------- namespaces
    for ns, kv in sorted(by_ns.items()):
        current = manifest.get(ns)
        if current:
            have = {}
            for fname in current:
                p = os.path.join(shard_dir, fname)
                if os.path.exists(p):
                    have.update(json.load(open(p, encoding="utf-8")))
            # A namespace is up to date only if it has every key AND every
            # value matches. Checking only the KEY SET is not enough: a value
            # edit leaves the key set identical, so the shard would keep
            # serving the OLD text while the dictionary carries the new one.
            # That is the same "stale shard, 200 response" failure as a
            # missing key, so it has to be caught here.
            if set(kv).issubset(have) and all(have.get(k) == v for k, v in kv.items()):
                continue

        parts = split_parts(kv)
        if len(parts) == 1:
            fname = f"{ns}.json"
            write_json_atomic(os.path.join(shard_dir, fname), parts[0])
            manifest[ns] = [fname]
            written.append((fname, len(parts[0])))
        else:
            names = []
            for i, part in enumerate(parts):
                fname = f"{ns}.part{i}.json"
                write_json_atomic(os.path.join(shard_dir, fname), part)
                names.append(fname)
                written.append((fname, len(part)))
            manifest[ns] = names

    # ------------------------------------------------------------- bundles
    # A page over the shard budget is served from a bundle keyed by the hash
    # of its namespace set. The bundle must carry every key that page binds,
    # plus the fixed-name keys the middleware looks up directly.
    page_ns = defaultdict(set)
    page_keys = defaultdict(set)
    for f in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        rel = f.replace(os.sep, "/")
        if any(x in rel for x in B.SKIP):
            continue
        try:
            t = open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        ks = B.keys_in_html(t)
        if not ks:
            continue
        page_ns[rel].update(B.ns_of(k) for k in ks)
        page_keys[rel].update(ks)

    heavy = defaultdict(list)
    for rel, ns in page_ns.items():
        if len(ns) > B.MAX_SHARDS:
            heavy[B.namespace_set_id(ns)].append(rel)

    bundles = manifest.get("__bundles__", {})
    for bid, pages in heavy.items():
        wanted = set()
        for rel in pages:
            wanted |= page_keys[rel]
        payload = {k: full[k] for k in wanted if k in full}
        payload.update(B.extra_keys(full))
        fname = f"bundle.{bid}.json"
        write_json_atomic(os.path.join(shard_dir, fname), payload)
        bundles[bid] = fname
        written.append((fname, len(payload)))
    if bundles:
        manifest["__bundles__"] = bundles

    write_json_atomic(os.path.join(ROOT, manifest_path), manifest)

    print(f"language      : {lang}")
    print(f"namespaces    : {len(by_ns)}")
    print(f"bundles       : {len(heavy)}")
    print(f"files written : {len(written)}")
    for fname, n in written:
        print(f"  + {fname:52s} {n} key(s)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
