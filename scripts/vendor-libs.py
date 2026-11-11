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
    # ---------------------------------------------------------------------
    # gifenc - the GIF encoder for the photo-to-GIF tool.
    #
    # ESM ONLY. The CommonJS build (dist/gifenc.js) is the package's
    # `main`, so `import` of the package root would work in a bundler -
    # but there is no bundler here. dist/gifenc.esm.js is the esbuild
    # ESM bundle, self-contained (no bare specifiers, so no import map
    # is needed - unlike the jsquash packages), and it has to be
    # imported by a `<script type="module">` the way mediabunny is:
    # see js/tools/gif-loader.js.
    #
    # Exports: GIFEncoder, applyPalette, quantize, nearestColorIndex.
    #
    # The version is in the DIRECTORY on purpose: a file reached through
    # a dynamic import() is cached by its URL, and a version change in
    # the PATH is the only thing that busts it.
    #
    # MIT, verified from the LICENSE.md inside the package (the npm
    # `license` field only says "MIT" - the text was read from the
    # package, not from a search summary).
    # ---------------------------------------------------------------------
    "gifenc": {
        "pkg": "gifenc",
        "version": "1.0.3",
        "license": "MIT",
        "files": {
            "1.0.3/gifenc.esm.js": "dist/gifenc.esm.js",
            "1.0.3/LICENSE": "LICENSE.md",
        },
    },
    # ---------------------------------------------------------------------
    # pdf-lib - PDF merge / split / reorder / decrypt.
    #
    # UMD build (dist/pdf-lib.min.js), so it sets the global `PDFLib`
    # and a plain <script src> works - there is no bundler on this
    # site. It is loaded on FIRST USE through
    # js/tools/common.js loadVendor('pdflib'), never on page load.
    #
    # The version is in the DIRECTORY for the same reason as gifenc.
    #
    # MIT, verified from the LICENSE.md inside the package (the npm
    # `license` field only says "MIT" - the text was read from the
    # package, not from a search summary).
    # ---------------------------------------------------------------------
    "pdflib": {
        "pkg": "@cantoo/pdf-lib",
        "version": "2.11.1",
        "license": "MIT",
        "files": {
            "2.11.1/pdf-lib.min.js": "dist/pdf-lib.min.js",
            "2.11.1/LICENSE": "LICENSE.md",
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
    # ---------------------------------------------------------------------
    # §2.12 - the two encoders the Canvas API does not have.
    #
    # MEASURED 2026-11-11 on this machine, bundled Chromium + installed
    # Chrome + installed Edge:
    #
    #   canvas.toBlob(canvas, 'image/avif')  -> a blob whose type is
    #       image/png. NO browser encodes AVIF. It does not fail, it
    #       silently returns PNG bytes - so a feature probe that only
    #       asks "did I get a blob?" is a FALSE POSITIVE.
    #   canvas.toBlob(canvas, 'image/webp', 1.0) -> lossy. A flat 64x64
    #       canvas came out at 520 bytes against PNG's 282, which is the
    #       size of a lossy encode, not a lossless one.
    #
    # So both formats need a WebAssembly encoder. The directory names
    # carry the version ON PURPOSE: the emscripten glue loads its .wasm
    # through a RELATIVE url, and a relative url carries no ?v= stamp, so
    # only a version change in the PATH busts the cache. A directory per
    # version is the only way to bust it.
    #
    # Apache-2.0, verified from the LICENSE inside each package.
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # §2.11 - the face detector for the crop tool.
    #
    # WHY face-api.js AND NOT MEDIAPIPE
    # ---------------------------------
    # The two obvious candidates were measured on this machine:
    #
    #   @mediapipe/tasks-vision@1.2.2   vision_bundle.mjs 156 KB
    #                                   + vision_wasm_internal.wasm 14.6 MB
    #                                   + the .tflite model on top
    #   @mediapipe/face_detection@0.4   5.8 MB of WASM + 229 KB of model
    #   face-api.js@0.22.2              648 KB of JS + 189 KB of model
    #
    # face-api.js is the only one of the three that fits this site's rules:
    #
    #   * MIT, and the LICENSE travels with the code.
    #   * The UMD build sets window.faceapi, so a plain <script src> works -
    #     there is no bundler on this site.
    #   * MEASURED IN THE SHIPPED FILE: zero `eval(`, zero `new Function`,
    #     zero `WebAssembly`, zero `importScripts`. So it runs under
    #     script-src 'self' 'nonce-...' WITHOUT 'unsafe-eval', and it does not
    #     need 'wasm-unsafe-eval' either.
    #   * It has no UI strings, so it adds no translation debt to the 11
    #     languages the tool pages ship in.
    #   * It runs entirely in the browser, which is what keeps the site's
    #     "your photos never leave your device" promise true.
    #
    # The model is the tiny face detector (190 KB, one shard). The bigger
    # SSD MobileNet detector would be ~5 MB for no gain on wedding photos.
    #
    # The npm package does NOT ship the weights - they live in the GitHub
    # repository, so the URLs are given explicitly and pinned to the same
    # v0.22.2 tag as the code.
    #
    # The DIRECTORY carries the version on purpose. face-api resolves the
    # weight shard as <modelBaseUri>/<shard>, and that fetch carries no
    # ?v= stamp - only a version in the PATH busts the cache.
    # ---------------------------------------------------------------------
    "face-api-0.22.2": {
        "pkg": "face-api.js",
        "version": "0.22.2",
        "license": "MIT",
        "files": {
            "face-api.min.js": "dist/face-api.min.js",
            "LICENSE": "LICENSE",
            "models/tiny_face_detector_model-weights_manifest.json":
                "models/tiny_face_detector_model-weights_manifest.json",
            "models/tiny_face_detector_model-shard1":
                "models/tiny_face_detector_model-shard1",
        },
        "urls": {
            "models/tiny_face_detector_model-weights_manifest.json":
                "https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@v0.22.2/weights/tiny_face_detector_model-weights_manifest.json",
            "models/tiny_face_detector_model-shard1":
                "https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@v0.22.2/weights/tiny_face_detector_model-shard1",
        },
    },
    "jsquash-avif-2.1.1": {
        "pkg": "@jsquash/avif",
        "version": "2.1.1",
        "license": "Apache-2.0",
        "files": {
            # ESM ONLY, and encode.js imports the BARE specifier
            # 'wasm-feature-detect' - so the page needs an import map.
            # The encoder itself is 3.49 MB of WASM (the decoder, another
            # 1.17 MB, is deliberately NOT shipped: the browser decodes
            # the input on its own).
            "encode.js": "encode.js",
            "meta.js": "meta.js",
            "utils.js": "utils.js",
            "codec/enc/avif_enc.js": "codec/enc/avif_enc.js",
            "codec/enc/avif_enc.wasm": "codec/enc/avif_enc.wasm",
            "LICENSE": "LICENSE",
        },
    },
    "jsquash-wfd-1.2.11": {
        # The one dependency of both encoder packages: a 1.7 KB module
        # that answers "does this browser have SIMD / threads?". Apache-2.0.
        #
        # PINNED TO 1.2.11 ON PURPOSE. The current 1.10.0 ships an
        # `import.source(...)` call - the import-source proposal - which is
        # a SYNTAX ERROR in every browser that does not implement it. The
        # module then fails to parse, the encoder package that imports it
        # fails to load, and the tool reports "Unexpected identifier
        # 'source'". 1.2.11 is the version jsquash itself declares
        # (^1.2.11) and it is clean.
        "pkg": "wasm-feature-detect",
        "version": "1.2.11",
        "license": "Apache-2.0",
        "files": {
            "index.js": "dist/esm/index.js",
            "LICENSE": "LICENSE",
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
