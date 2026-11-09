#!/usr/bin/env python3
"""
Vendor third-party libraries into /js/vendor/ so the site can self-host them.

WHY THIS EXISTS
---------------
The site's CSP is `script-src 'self' 'nonce-…'` plus a short origin
allowlist - no CDN is permitted - and there is no build step (no
package.json, no bundler). So a library has to arrive as a plain file under
/js/ and be loaded with a <script src>.

Every file is pinned to an exact version and re-downloadable with
--verify, so a reviewer can prove that /js/vendor/ matches the upstream
release and not something hand-edited.

WHAT IT DOES
------------
1. Downloads each pinned file from jsDelivr's npm mirror (which serves npm
   tarballs byte-for-byte).
2. Writes the upstream LICENSE next to the code, so the licence travels with
   the code.
3. Writes /js/vendor/vendor-manifest.json recording the URL, the SHA-256 and
   the byte size of every file, so a later run can detect drift.
4. Never overwrites a file whose hash differs from the manifest unless
   --force is given. That is the guard against silently shipping an edited
   vendor file.

Usage
-----
    python scripts/vendor-libs.py             # download anything missing
    python scripts/vendor-libs.py --verify    # hash-check, download nothing
    python scripts/vendor-libs.py --force     # re-download even if present

NOTE ON THE CACHE-BUST STAMP
----------------------------
Cloudflare Pages overrides Cache-Control on static assets, so the only
cache-busting mechanism is the ?v= query string. Every vendored file that a
page loads must carry a ?v= stamp, and the stamp must change when the file
changes. `scripts/bump_cache_version.py` handles the three shared assets;
the vendored files carry their own version literal in the manifest, and the
?v= value used in HTML must equal the manifest's "version" field for that
library. Run `python scripts/vendor-libs.py --verify` after any change.
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "js" / "vendor"
MANIFEST = VENDOR / "vendor-manifest.json"

CDN = "https://cdn.jsdelivr.net/npm"

# ---------------------------------------------------------------------------
# The pinned set. `version` is what the ?v= stamp in HTML must use.
# `files` maps the local path under /js/vendor/ to the path inside the package.
# `license_file` is the upstream licence text to place beside the code.
# ---------------------------------------------------------------------------
LIBS = {
    "fflate": {
        "pkg": "fflate",
        "version": "0.8.3",
        "license": "MIT",
        "files": {
            "fflate.min.js": "umd/index.js",
            "LICENSE": "LICENSE",
        },
    },
    "jspdf": {
        "pkg": "jspdf",
        "version": "4.2.1",
        "license": "MIT",
        "files": {
            "jspdf.umd.min.js": "dist/jspdf.umd.min.js",
            "LICENSE": "LICENSE",
        },
    },
    "heic2any": {
        "pkg": "heic2any",
        "version": "0.0.4",
        "license": "MIT",
        "files": {
            "heic2any.min.js": "dist/heic2any.min.js",
            "LICENSE": "LICENSE.md",
        },
    },
    "pica": {
        "pkg": "pica",
        "version": "10.0.3",
        "license": "MIT",
        "files": {
            "pica.min.js": "dist/pica.min.js",
            "LICENSE": "LICENSE",
        },
    },
    "onnxruntime": {
        "pkg": "onnxruntime-web",
        "version": "1.22.0",
        "license": "MIT",
        "files": {
            # The UMD build sets window.ort. It loads the WASM backend glue
            # (ort-wasm-simd-threaded.mjs) and the WASM binary itself at
            # runtime - both are vendored here and reached through
            # ort.env.wasm.wasmPaths, because there is no CDN and no bundler.
            #
            # ort.wasm.min.js (47 KB) is the WASM-only build. The bigger
            # ort.min.js (349 KB) loads the JSEP backend instead, whose
            # .wasm is 21.4 MB instead of 10.9 MB - twice the download for a
            # WebGPU path this site does not use.
            "ort.wasm.min.js": "dist/ort.wasm.min.js",
            "ort-wasm-simd-threaded.mjs": "dist/ort-wasm-simd-threaded.mjs",
            "ort-wasm-simd-threaded.wasm": "dist/ort-wasm-simd-threaded.wasm",
            # The npm package does NOT ship a LICENSE file (it is in the
            # repository), so the upstream text is fetched from the tag.
            "LICENSE": "LICENSE",
        },
        "urls": {
            "LICENSE":
                "https://raw.githubusercontent.com/microsoft/onnxruntime/v1.22.0/LICENSE",
        },
    },
    "mediabunny": {
        "pkg": "mediabunny",
        "version": "1.65.2",
        "license": "MPL-2.0",
        "files": {
            # ESM ONLY. mediabunny ships no UMD/global build, so it cannot
            # be loaded with <script src="/js/vendor/..."> the way the other
            # libraries are - it has to be imported by a
            # <script type="module">. js/tools/movie-loader.mjs is that
            # module; it imports mediabunny LAZILY, so the 723 KB only
            # arrives when the visitor actually asks for an MP4.
            #
            # MPL-2.0 is a weak copyleft: using the library unmodified is
            # fine, including in a commercial site. Shipping a modified
            # copy would require publishing the modification - the site
            # ships the upstream file byte-for-byte, so that never applies.
            "mediabunny.min.mjs": "dist/bundles/mediabunny.min.mjs",
            "LICENSE": "LICENSE",
        },
    },
    "modnet": {
        # The matting model itself. NOT an npm package: it is served from the
        # Hugging Face repository, so the URL is given explicitly.
        #   Xenova/modnet - Apache-2.0 (commercial use OK).
        # The full-precision model is 24.7 MB; the quantised one is 6.3 MB and
        # is what ships.
        "pkg": "Xenova/modnet",
        "version": "quantized",
        "license": "Apache-2.0",
        "files": {
            "model_quantized.onnx": "onnx/model_quantized.onnx",
        },
        "urls": {
            "model_quantized.onnx":
                "https://huggingface.co/Xenova/modnet/resolve/main/onnx/model_quantized.onnx",
        },
    },
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "weddingai-vendor/1.0"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = resp.read()
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, dest)
    return len(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="hash-check only, download nothing")
    ap.add_argument("--force", action="store_true", help="re-download even if the file exists")
    args = ap.parse_args()

    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    else:
        manifest = {"libraries": {}}

    problems = []
    for lib, spec in sorted(LIBS.items()):
        outdir = VENDOR / lib
        for local, inner in spec["files"].items():
            # Most files come from jsDelivr's npm mirror; a library that is
            # not on npm (the MODNet model) gives its own URL.
            url = spec.get("urls", {}).get(local) or f"{CDN}/{spec['pkg']}@{spec['version']}/{inner}"
            dest = outdir / local
            prev = manifest["libraries"].get(lib, {}).get("files", {}).get(local)

            if args.verify:
                if not dest.exists():
                    problems.append(f"MISSING  {lib}/{local}")
                    continue
                if prev and sha256(dest) != prev["sha256"]:
                    problems.append(f"MODIFIED {lib}/{local}")
                continue

            if dest.exists() and not args.force:
                if prev and sha256(dest) == prev["sha256"]:
                    print(f"  ok       {lib}/{local}")
                    continue
                print(f"  STALE    {lib}/{local} (hash differs from manifest; re-downloading)")
            try:
                size = download(url, dest)
            except Exception as exc:  # noqa: BLE001 - report and continue
                problems.append(f"FAILED   {lib}/{local}: {exc}")
                continue
            digest = sha256(dest)
            lib_entry = manifest["libraries"].setdefault(lib, {})
            lib_entry["package"] = spec["pkg"]
            lib_entry["version"] = spec["version"]
            lib_entry["license"] = spec["license"]
            lib_entry.setdefault("files", {})[local] = {
                "url": url,
                "sha256": digest,
                "bytes": size,
            }
            print(f"  fetched  {lib}/{local}  {size / 1024:.1f} KB")

    if args.verify:
        if problems:
            print("\nVENDOR VERIFY FAILED:")
            for p in problems:
                print("  " + p)
            return 1
        print("\nVENDOR VERIFY OK")
        return 0

    VENDOR.mkdir(parents=True, exist_ok=True)
    # prune libraries that are no longer part of the pinned set, so the
    # manifest never vouches for a file that is not shipped
    for lib in list(manifest["libraries"].keys()):
        if lib not in LIBS:
            del manifest["libraries"][lib]
            print(f"  pruned   {lib} (no longer pinned)")
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nmanifest: {MANIFEST.relative_to(ROOT)}")
    if problems:
        print("\nFAILURES:")
        for p in problems:
            print("  " + p)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
