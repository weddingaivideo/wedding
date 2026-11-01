#!/usr/bin/env python3
"""
Verify that the i18n shards are in sync with the dictionaries they were built
from.

WHY THIS CHECK EXISTS
---------------------
The 503 storm on 2026-10-30 was caused by the middleware parsing a 10-17 MB
dictionary per request (Cloudflare Pages Free allows 50 ms of CPU). The fix is
the namespace shards under i18n/shards/<lang>/, loaded by
functions/_lib/i18n-shards.js.

The shards are a DERIVED artefact. If somebody edits i18n/<lang>.json and
forgets to rebuild them, the middleware serves STALE TRANSLATIONS from the
shards - and the failure is silent, because the shard path still returns 200
and the page still renders. Nothing in the old gate could see it.

So this check proves three things:

  1. COVERAGE   every namespace of every dictionary has a manifest entry
  2. FRESHNESS  the shards, merged, are byte-for-byte the dictionary - the
                same key set and the same values. This is the real staleness
                test: an edited dictionary whose shards were not rebuilt
                fails here.
  3. PARITY     the JS namespace rule in functions/_lib/i18n-shards.js agrees
                with the Python rule in qa/build-i18n-shards.py. If they drift,
                the middleware asks for shard files that do not exist, every
                lookup misses, and the page falls back to English silently.

It also reports, per page, how many shards the page would need, so a page that
exceeds the middleware's MAX_SHARDS budget (and therefore falls back to the
full dictionary, i.e. stays 503-prone) is visible instead of silent.

Exit code 0 = all checks pass.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
I18N = REPO / "i18n"
SHARD_ROOT = I18N / "shards"

LANGS = ["ar", "de", "en", "es", "fr", "hi", "ja", "pt", "ru", "th", "zh"]

# Must equal MAX_SHARDS in functions/_lib/i18n-shards.js.
MAX_SHARDS = 40

# A single shard bigger than this is a sign the namespace is too coarse.
MAX_SHARD_BYTES = 512 * 1024

# The manifest's bundle section lives under this key; it is NOT a namespace.
BUNDLES_KEY = "__bundles__"

# Keys the middleware looks up by a fixed name rather than through a
# data-i18n attribute. A bundle has to carry them too.
EXTRA_KEY_PREFIXES = ("index.og_title", "index.og_description",
                      "index.twitter_title", "index.twitter_description",
                      "pricing.meta_description", "pricing.og_title",
                      "pricing.og_description")
EXTRA_KEY_PREFIXES_FAQ = ("homepage_faq.q", "pricing_faq.q")

failures = []
warnings = []


def fail(msg):
    failures.append(msg)
    print("  FAIL  " + msg)


def warn(msg):
    warnings.append(msg)
    print("  WARN  " + msg)


def ns_of(key):
    """The namespace a key belongs to.

    MUST stay identical to namespaceOf() in functions/_lib/i18n-shards.js and
    to ns_of() in qa/build-i18n-shards.py.
    """
    p = key.split(".")
    if len(p) <= 1:
        return "_root"
    if len(p) == 2:
        return p[0]
    return p[0] + "." + p[1]


def keys_in_html(html):
    """Every dictionary key an html file binds (both attribute spellings).

    MUST match keys_in_html() in qa/build-i18n-shards.py and
    namespacesInHtml() in functions/_lib/i18n-shards.js.
    """
    out = []
    for m in re.finditer(r'data-i18n(?:-attr)?="([^"]+)"', html):
        spec = m.group(1)
        parts = spec.split("|") if "|" in spec else [spec]
        for part in parts:
            c = part.find(":")
            key = (part if c == -1 else part[c + 1:]).strip()
            if key:
                out.append(key)
    return out


def namespace_set_id(ns_list):
    """Stable id for a set of namespaces.

    MUST match namespaceSetId() in functions/_lib/i18n-shards.js.
    """
    joined = "\n".join(sorted(ns_list))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------- js parity
JS_PROBE = r"""
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { pathToFileURL } from "node:url";

// argv[2] = repo root (for i18n/<lang>.json)
// argv[3] = staged module dir (for functions/_lib/i18n-shards.js)
// argv[4] = lang
const repo = process.argv[2];
const moduleDir = process.argv[3];
const lang = process.argv[4];

// A dynamic import() needs a file:// URL. A bare Windows path
// ("C:\\...") fails with ERR_UNSUPPORTED_ESM_URL_SCHEME.
const { namespaceOf } = await import(
    pathToFileURL(path.join(moduleDir, "i18n-shards.js")).href);

const dict = JSON.parse(
    fs.readFileSync(path.join(repo, "i18n", lang + ".json"), "utf8"));

const lines = [];
for (const key of Object.keys(dict).sort()) {
    lines.push(namespaceOf(key) + "\t" + key);
}
process.stdout.write(crypto.createHash("sha256")
    .update(lines.join("\n")).digest("hex"));
"""


def js_namespace_hash(lang):
    """SHA-256 over "ns\\tkey" lines computed by the real JS implementation."""
    if not shutil.which("node"):
        return None
    tmp = Path(tempfile.mkdtemp(prefix="wa-ns-"))
    try:
        (tmp / "package.json").write_text('{"type":"module"}', encoding="utf-8")
        # The middleware is ESM but the repo has no package.json, so node would
        # treat .js as CommonJS. Stage the one file we need next to a
        # {"type":"module"} marker. The dictionary itself is read from the real
        # repo - copying 17 MB per language would be pointless.
        lib_dir = tmp / "lib"
        lib_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / "functions" / "_lib" / "i18n-shards.js",
                     lib_dir / "i18n-shards.js")
        probe = tmp / "probe.mjs"
        probe.write_text(JS_PROBE, encoding="utf-8")
        r = subprocess.run(
            ["node", str(probe), str(REPO), str(lib_dir), lang],
            capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            err = (r.stderr or "").strip().splitlines()
            detail = "\n        ".join(err[-6:]) if err else "?"
            fail(f"node probe failed for {lang}:\n        {detail}")
            return None
        return r.stdout.strip()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def py_namespace_hash(dict_obj):
    lines = []
    for key in sorted(dict_obj.keys()):
        lines.append(ns_of(key) + "\t" + key)
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


# ------------------------------------------------------------------- page survey
DATA_I18N_RE = re.compile(r'data-i18n(?:-attr)?="([^"]+)"')


def page_shard_need():
    """How many shards each html page would ask for, and the bundles it needs."""
    need = defaultdict(int)
    pages = []
    heavy = defaultdict(list)       # namespace-set id -> pages
    heavy_keys = defaultdict(set)   # namespace-set id -> bound keys
    for path in sorted(REPO.rglob("*.html")):
        rel = path.relative_to(REPO).as_posix()
        if rel.startswith(("private/", "i18n/", ".tmp/", "qa/")):
            continue
        try:
            html = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        keys = keys_in_html(html)
        if not keys:
            continue
        ns = set(ns_of(k) for k in keys)
        pages.append(rel)
        if len(ns) > need["max"]:
            need["max"] = len(ns)
            need["max_page"] = rel
        if len(ns) > MAX_SHARDS:
            bid = namespace_set_id(ns)
            heavy[bid].append(rel)
            heavy_keys[bid] |= set(keys)
    return need, pages, heavy, heavy_keys


# ------------------------------------------------------------------------- main
def main():
    # --probe <lang> : run only the node namespace-parity probe and print the
    # full stderr. Used when the probe fails, to see the real cause.
    if len(sys.argv) >= 3 and sys.argv[1] == "--probe":
        lang = sys.argv[2]
        h = js_namespace_hash(lang)
        print("js hash :", h)
        print("py hash :", py_namespace_hash(
            json.loads((I18N / f"{lang}.json").read_text(encoding="utf-8"))))
        for f in failures:
            print("  - " + f)
        return 0 if h else 1

    print("=" * 100)
    print("I18N SHARD FRESHNESS VERIFICATION")
    print("=" * 100)

    print("\n--- per-language shard vs dictionary ---")
    hdr = (f"{'lang':<5} {'dict keys':>10} {'shard keys':>11} {'ns':>5} "
           f"{'files':>7} {'max KB':>8} {'total MB':>9} {'bundle':>8}  status")
    print(hdr)
    print("-" * 100)

    # The page survey runs FIRST: the bundle check below needs to know which
    # keys each bundle is supposed to carry.
    need, pages, heavy, heavy_keys = page_shard_need()

    for lang in LANGS:
        dict_path = I18N / f"{lang}.json"
        manifest_path = I18N / f"{lang}.manifest.json"
        lang_dir = SHARD_ROOT / lang

        if not dict_path.exists():
            fail(f"{lang}: i18n/{lang}.json is missing")
            continue
        if not manifest_path.exists():
            fail(f"{lang}: i18n/{lang}.manifest.json is missing "
                 f"(the middleware cannot load shards without it)")
            continue
        if not lang_dir.is_dir():
            fail(f"{lang}: i18n/shards/{lang}/ is missing")
            continue

        try:
            dict_obj = json.loads(dict_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            fail(f"{lang}: cannot parse dictionary or manifest: {exc}")
            continue

        # --- 1. COVERAGE: the manifest must describe every namespace
        expected_ns = defaultdict(set)
        for key in dict_obj:
            expected_ns[ns_of(key)].add(key)

        bundles = manifest.get(BUNDLES_KEY) or {}
        ns_entries = {k: v for k, v in manifest.items() if k != BUNDLES_KEY}

        missing_ns = sorted(set(expected_ns) - set(ns_entries))
        extra_ns = sorted(set(ns_entries) - set(expected_ns))
        if missing_ns:
            fail(f"{lang}: {len(missing_ns)} namespace(s) in the dictionary have "
                 f"no manifest entry: {missing_ns[:6]}")
        if extra_ns:
            fail(f"{lang}: {len(extra_ns)} manifest namespace(s) are not in the "
                 f"dictionary: {extra_ns[:6]}")

        # --- 2. FRESHNESS: the shards must merge back into the dictionary
        merged = {}
        shard_files = []
        for ns, files in ns_entries.items():
            if not isinstance(files, list):
                fail(f"{lang}: manifest entry for '{ns}' is not a list")
                continue
            for fname in files:
                shard_files.append(fname)
                sp = lang_dir / fname
                if not sp.exists():
                    fail(f"{lang}: shard file missing on disk: {fname}")
                    continue
                try:
                    part = json.loads(sp.read_text(encoding="utf-8"))
                except ValueError as exc:
                    fail(f"{lang}: shard {fname} is not valid JSON: {exc}")
                    continue
                for k, v in part.items():
                    if k in merged:
                        fail(f"{lang}: key '{k}' appears in more than one shard")
                    merged[k] = v

        dict_keys = set(dict_obj)
        shard_keys = set(merged)
        lost = sorted(dict_keys - shard_keys)
        gained = sorted(shard_keys - dict_keys)
        if lost:
            fail(f"{lang}: {len(lost)} key(s) are in the dictionary but NOT in "
                 f"any shard (stale shards - rebuild with qa/build-i18n-shards.py): "
                 f"{lost[:5]}")
        if gained:
            fail(f"{lang}: {len(gained)} key(s) are in a shard but NOT in the "
                 f"dictionary (orphaned shard): {gained[:5]}")
        differing = [k for k in (dict_keys & shard_keys)
                     if dict_obj[k] != merged[k]]
        if differing:
            fail(f"{lang}: {len(differing)} key(s) have a DIFFERENT value in the "
                 f"shard than in the dictionary (stale shards): {differing[:5]}")

        # --- orphan files on disk that the manifest does not mention
        on_disk = {p.name for p in lang_dir.glob("*.json")}
        orphans = sorted(on_disk - set(shard_files) - set(bundles.values()))
        if orphans:
            warn(f"{lang}: {len(orphans)} shard file(s) on disk are not in the "
                 f"manifest (wasted upload): {orphans[:4]}")

        # --- 2b. BUNDLES: a page that needs more shards than the runtime can
        # fetch gets one bundle file with exactly its own keys. Verify the
        # bundle exists, is keyed by the right namespace-set id, and carries
        # every key the page binds.
        for bid, fname in bundles.items():
            bp = lang_dir / fname
            if not bp.exists():
                fail(f"{lang}: bundle file missing on disk: {fname}")
                continue
            try:
                payload = json.loads(bp.read_text(encoding="utf-8"))
            except ValueError as exc:
                fail(f"{lang}: bundle {fname} is not valid JSON: {exc}")
                continue
            wanted = heavy_keys.get(bid)
            if wanted is None:
                fail(f"{lang}: manifest advertises bundle {fname} ({bid}) but no "
                     f"page in the repo needs that namespace set - it is dead "
                     f"weight in the upload")
                continue
            missing = sorted(k for k in wanted if k in dict_obj and k not in payload)
            if missing:
                fail(f"{lang}: bundle {fname} is missing {len(missing)} key(s) the "
                     f"page binds: {missing[:5]}")
            stale = [k for k, v in payload.items()
                     if k in dict_obj and dict_obj[k] != v]
            if stale:
                fail(f"{lang}: bundle {fname} has {len(stale)} key(s) whose value "
                     f"differs from the dictionary (stale bundle): {stale[:5]}")
            extra_missing = [k for k in EXTRA_KEY_PREFIXES
                             if k in dict_obj and k not in payload]
            if extra_missing:
                fail(f"{lang}: bundle {fname} is missing the fixed-name keys the "
                     f"middleware looks up: {extra_missing}")
            bundle_bytes = bp.stat().st_size
            if bundle_bytes > MAX_SHARD_BYTES:
                fail(f"{lang}: bundle {fname} is {bundle_bytes/1024:.0f} KB "
                     f"(limit {MAX_SHARD_BYTES/1024:.0f} KB)")

        # --- 3. PARITY: the JS namespace rule must agree with the Python one
        py_hash = py_namespace_hash(dict_obj)
        js_hash = js_namespace_hash(lang)
        if js_hash is None:
            warn(f"{lang}: node not available - skipped the JS/Python namespace "
                 f"parity check for this language")
        elif js_hash != py_hash:
            fail(f"{lang}: functions/_lib/i18n-shards.js derives a different "
                 f"namespace for at least one key than qa/build-i18n-shards.py "
                 f"(js={js_hash[:12]} py={py_hash[:12]}). The middleware would "
                 f"request shard files that do not exist.")

        sizes = [(lang_dir / f).stat().st_size for f in shard_files
                 if (lang_dir / f).exists()]
        max_bytes = max(sizes) if sizes else 0
        total_bytes = sum(sizes)
        if max_bytes > MAX_SHARD_BYTES:
            fail(f"{lang}: the biggest shard is {max_bytes/1024:.0f} KB "
                 f"(limit {MAX_SHARD_BYTES/1024:.0f} KB)")
        bundle_kb = 0
        if bundles:
            bundle_kb = max((lang_dir / f).stat().st_size
                            for f in bundles.values()) / 1024

        status = "ok" if not failures else "see above"
        print(f"{lang:<5} {len(dict_obj):>10} {len(merged):>11} "
              f"{len(ns_entries):>5} {len(shard_files):>7} "
              f"{max_bytes/1024:>8.0f} {total_bytes/1024/1024:>9.1f} "
              f"{bundle_kb:>7.0f}K  {status}")

    # ------------------------------------------------------- page shard budget
    print("\n--- per-page shard budget (MAX_SHARDS = %d) ---" % MAX_SHARDS)
    print(f"  pages scanned: {len(pages)}")
    print(f"  heaviest page: {need.get('max_page', '?')} needs "
          f"{need.get('max', 0)} shards")
    if heavy:
        print(f"  {sum(len(v) for v in heavy.values())} page(s) exceed the budget; "
              f"they are served from a BUNDLE instead of the namespace shards:")
        for bid, rels in sorted(heavy.items()):
            print(f"      bundle {bid}  <- {', '.join(sorted(rels)[:3])}"
                  f"{' ...' if len(rels) > 3 else ''}")
        missing_bundles = set(heavy) - set(
            bid for lang in LANGS
            for bid in ((json.loads((I18N / f'{lang}.manifest.json')
                                    .read_text(encoding='utf-8'))
                         .get(BUNDLES_KEY) or {}).keys()))
        if missing_bundles:
            fail(f"no bundle was built for namespace set(s) "
                 f"{sorted(missing_bundles)}")
        else:
            print("  every over-budget page has a bundle")
    else:
        print("  every page fits inside the shard budget")

    print()
    print(f"RESULT: {len(failures)} FAILURE(S), {len(warnings)} WARNING(S)")
    for f in failures:
        print("  - " + f)
    for w in warnings:
        print("  - " + w)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
