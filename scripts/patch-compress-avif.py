#!/usr/bin/env python3
"""
Patch the compress tool for AVIF and lossless-WebP output (§2.12).

WHY THIS EXISTS
---------------
Measured 2026-11-11 on the bundled Chromium, the installed Chrome and the
installed Edge, all on a secure origin:

  * canvas.toBlob(canvas, 'image/avif') returns a blob whose `.type` is
    image/png. NO browser encodes AVIF through the Canvas API, and it does
    not fail loudly - it silently hands back PNG bytes. A probe that only
    asks "did I get a blob?" is a FALSE POSITIVE.
  * canvas.toBlob(canvas, 'image/webp', 1.0) is LOSSLESS: the file
    carries a VP8L chunk and decodes back pixel-for-pixel (worst channel
    delta 0 on per-pixel noise). Chromium and Firefox both switch to the
    lossless encoder at quality 1, so the browser's OWN encoder is enough
    for lossless WebP.
  * canvas.toBlob(canvas, 'image/webp') in SAFARI returns a PNG. WebKit's
    canvas cannot write WebP at all and says nothing about it.

That last one was a live bug on this site: the compress tool wrote the
blob out under a .webp name, so a Safari visitor received a PNG wearing
the wrong extension. The fix is not a bigger library - it is to ASK the
browser what it can encode, offer only that, and never write a file
under a name it does not match.

WHAT IT CHANGES
---------------
1. The output-format control gains two options and becomes DICTIONARY-BOUND
   in all eleven languages.

   It was in three different states before this pass:
     - en / zh / pt / ru: NOT bound. The inline <option> text was correct
       for that language, but it was hard-coded in the HTML.
     - es / fr / de / ja / ar / th / hi: bound with data-i18n, but the
       INLINE text was CHINESE on every one of them (the machine
       translation had rewritten the markup). The page rendered correctly
       only because the middleware replaced the Chinese with the
       dictionary value; if the shard ever failed to load, a German
       visitor would have read "输出格式".
     - the <label for="format"> was bound in seven languages and not in
       four, with the same Chinese-inline-text defect.

   Now every page carries the SAME English source text and a data-i18n
   key, and every dictionary carries the translation.

2. The page gains an import map and the encoder module.

   jsquash's encode.js imports the BARE specifier 'wasm-feature-detect',
   which only resolves through an import map. The map has to come BEFORE
   any module script, and the middleware's injectScriptNonce() adds a
   nonce to every <script> opening tag - the import map included - so the
   inline map passes `script-src 'self' 'nonce-...'`.

3. The inline JS learns about the two new formats, and stops trusting
   the browser to give it the format it asked for.

Usage
-----
    python scripts/patch-compress-avif.py            # apply
    python scripts/patch-compress-avif.py --dry-run

Afterwards ALWAYS run:
    python scripts/propagate-tool-js.py               # push the JS to the 10 copies
    python scripts/check-tool-script-syntax.py
"""

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = "compress-wedding-photos"
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

# --------------------------------------------------------------------------
# The new i18n keys. The three existing option keys already exist in seven
# dictionaries; the label and the two new options are new everywhere.
# --------------------------------------------------------------------------
K_LABEL = "tools.compress-wedding-photos.label_text.output_format.a4b5c6d7"
K_JPG = "tools.compress-wedding-photos.option_text.c06b8c68"
K_WEBP = "tools.compress-wedding-photos.option_text.1724a385"
K_PNG = "tools.compress-wedding-photos.option_text.babb5986"
K_AVIF = "tools.compress-wedding-photos.option_text.b6c7d8e9"
K_LOSSLESS = "tools.compress-wedding-photos.option_text.c7d8e9f0"

# The English source text. Every page carries exactly this; the dictionary
# carries the translation.
FORMAT_BLOCK = (
    '<label for="format" data-i18n="{label}">Output format</label>\n'
    '{ind}<select id="format">\n'
    '{ind}    <option value="image/jpeg" selected data-i18n="{jpg}">JPG (smaller, recommended for sharing)</option>\n'
    '{ind}    <option value="image/webp" data-i18n="{webp}">WebP (smaller, modern browsers)</option>\n'
    '{ind}    <option value="image/png" data-i18n="{png}">PNG (lossless, biggest files)</option>\n'
    '{ind}    <option value="image/avif" data-i18n="{avif}">AVIF (smallest files &mdash; downloads a 3.4 MB encoder once)</option>\n'
    '{ind}    <option value="webp-lossless" data-i18n="{lossless}">WebP lossless (for graphics &mdash; a photo gets bigger)</option>\n'
    '{ind}</select>'
).format(label=K_LABEL, jpg=K_JPG, webp=K_WEBP, png=K_PNG, avif=K_AVIF,
         lossless=K_LOSSLESS, ind="{ind}")

# The import map + the encoder module.
IMPORT_MAP_LINE = (
    '    <script type="importmap">{"imports":{"wasm-feature-detect":"/js/vendor/jsquash-wfd-1.2.11/index.js"}}</script>\n'
)
MODULE_LINE = '    <script type="module" src="/js/tools/image-codecs.js?v=1.0.0"></script>\n'

MODULE_BLOCK = (
    '    <!-- §2.12: the AVIF encoder is ESM, and its entry point imports the\n'
    '         bare specifier \'wasm-feature-detect\'. A bare specifier only\n'
    '         resolves through an import map, and the map has to come BEFORE\n'
    '         the module script that uses it. The middleware adds a nonce to\n'
    '         every <script> opening tag - this one included - so the inline\n'
    '         map passes `script-src \'self\' \'nonce-...\'`. The encoder itself\n'
    '         (3.4 MB of WASM) is behind a dynamic import inside the module,\n'
    '         so it is only downloaded when a visitor picks AVIF. -->\n'
    + IMPORT_MAP_LINE
    + MODULE_LINE
)

# The anchor for the tool's own inline script. The module block goes right
# before it, which is late enough that no module script precedes the map.
INLINE_ANCHOR = "    <script>\n    document.addEventListener('DOMContentLoaded', function () {"

# --------------------------------------------------------------------------
# The inline JS replacements (English page only - the localized copies get
# the JS from scripts/propagate-tool-js.py).
# --------------------------------------------------------------------------

OLD_SETTINGS_END = """          keepExif: !!(exifEl && exifEl.checked),
        };
      }
"""

NEW_SETTINGS_END = """          keepExif: !!(exifEl && exifEl.checked),
        };
      }

      // ---------- output formats (§2.12) -----------------------------------
      //
      // The Canvas API can encode JPG, PNG and WebP. It cannot encode AVIF
      // at all, and WebKit cannot write WebP - it hands back a PNG and
      // says nothing about it. So the browser is ASKED what it can do
      // before the menu is built, and the menu only offers the truth.
      //
      // `webp-lossless` is this tool's own name for "lossless WebP". The
      // browser's own encoder produces it at quality 1: Chromium and
      // Firefox both switch to the lossless VP8L encoder there, and the
      // result decodes back pixel-for-pixel (measured: worst channel
      // delta 0 on per-pixel noise). No second encoder is needed for it.
      var FORMATS = {
        'image/jpeg': { mime: 'image/jpeg', ext: 'jpg' },
        'image/webp': { mime: 'image/webp', ext: 'webp' },
        'webp-lossless': { mime: 'image/webp', ext: 'webp', lossless: true, fixedQuality: 1.0 },
        'image/png': { mime: 'image/png', ext: 'png' },
        'image/avif': { mime: 'image/avif', ext: 'avif', wasm: 'avif' }
      };

      // What the browser can ACTUALLY encode. The answer is not the spec's
      // answer: Safari returns a PNG when asked for WebP, and every
      // browser returns a PNG when asked for AVIF. The only reliable test
      // is to ask and look at what came back.
      var CAN = { webp: false, avif: false };

      function formatInfo(value) {
        return FORMATS[value] || FORMATS['image/jpeg'];
      }

      function canEncode(mime) {
        return new Promise(function (resolve) {
          try {
            var c = document.createElement('canvas');
            c.width = 2; c.height = 2;
            c.getContext('2d').fillRect(0, 0, 2, 2);
            c.toBlob(function (b) {
              resolve(!!b && b.type === mime);
            }, mime);
          } catch (e) { resolve(false); }
        });
      }

      // Encode one canvas in the chosen format. `quality` is the 0..1
      // slider value. Returns { blob, fmt } - the format can be swapped
      // for JPG when the browser cannot produce what was asked for, and
      // the caller has to be told.
      async function encodeCanvas(canvas, fmt, quality) {
        if (fmt.wasm && !CAN.avif) {
          var codecs = window.weddingAIImageCodecs;
          if (!codecs) {
            throw new Error('The AVIF encoder did not load. Reload the page and try again.');
          }
          var ctx = canvas.getContext('2d');
          var data = ctx.getImageData(0, 0, canvas.width, canvas.height);
          // jsquash uses 0..100, the Canvas slider uses 0..1.
          var avif = await codecs.encodeAvif(data, {
            quality: Math.max(1, Math.round(quality * 100)),
            speed: 6
          });
          return { blob: avif, fmt: fmt };
        }
        var q = fmt.fixedQuality !== undefined ? fmt.fixedQuality
               : (fmt.mime === 'image/png' ? undefined : quality);
        var out = await window.weddingAITool.canvasToBlob(canvas, fmt.mime, q);
        if (!out || out.size === 0) {
          throw new Error('The browser could not encode this photo. Try another format.');
        }
        if (out.type !== fmt.mime) {
          // THE TRAP: a browser that cannot encode the requested format
          // returns a PNG instead of failing. Writing that out under a
          // .webp name would hand the user a PNG wearing the wrong
          // extension, so it is saved as JPG and the row says so.
          var jpg = await window.weddingAITool.canvasToBlob(canvas, 'image/jpeg', 0.85);
          if (jpg && jpg.size) {
            return { blob: jpg, fmt: FORMATS['image/jpeg'], fellBack: true };
          }
          throw new Error('This browser cannot encode ' + fmt.mime + '.');
        }
        return { blob: out, fmt: fmt };
      }

      // §2.12 - find out what this browser can really encode, then offer
      // only that. Safari cannot write WebP and returns a PNG instead of
      // saying so, so the WebP options are removed there.
      async function detectFormatSupport() {
        CAN.webp = await canEncode('image/webp');
        CAN.avif = await canEncode('image/avif');
        var haveAvifEncoder = !!window.weddingAIImageCodecs;
        for (var i = 0; i < formatEl.options.length; i++) {
          var o = formatEl.options[i];
          if (o.value === 'image/webp' || o.value === 'webp-lossless') {
            o.disabled = !CAN.webp;
            if (!CAN.webp) o.title = 'This browser cannot write WebP.';
          } else if (o.value === 'image/avif') {
            o.disabled = !(CAN.avif || haveAvifEncoder);
            if (o.disabled) o.title = 'The AVIF encoder could not be loaded.';
          }
        }
        if (!CAN.webp && (formatEl.value === 'image/webp' || formatEl.value === 'webp-lossless')) {
          formatEl.value = 'image/jpeg';
        }
      }
"""

OLD_ENCODE = """          var mime = settings.format;
          var quality = settings.quality;
          // PNG is lossless, quality is ignored
          if (mime === 'image/png') quality = undefined;
          var blob;
          if (settings.targetBytes > 0 && mime !== 'image/png') {
            // §2.14 - "compress to exactly 2 MB". The quality slider is
            // replaced by a search for the highest quality that still fits
            // under the target.
            entry.percent = 55;
            refreshUI();
            var res = await encodeToTarget(canvas, mime, settings.targetBytes);
            blob = res.blob;
            if (!blob) {
              // The target is unreachable for this photo: keep the smallest
              // file we could make and say so in the summary.
              blob = await window.weddingAITool.canvasToBlob(canvas, mime, 0.3);
              entry.targetMissed = true;
            } else {
              quality = res.quality;
            }
          } else {
            blob = await window.weddingAITool.canvasToBlob(canvas, mime, quality);
          }
"""

NEW_ENCODE = """          var fmt = formatInfo(settings.format);
          var quality = settings.quality;
          var result = null;
          if (settings.targetBytes > 0 && fmt.mime !== 'image/png' && !fmt.lossless) {
            // §2.14 - "compress to exactly 2 MB". The quality slider is
            // replaced by a search for the highest quality that still fits
            // under the target.
            entry.percent = 55;
            refreshUI();
            result = await encodeToTarget(canvas, fmt, settings.targetBytes);
            if (!result.blob) {
              // The target is unreachable for this photo: keep the smallest
              // file we could make and say so in the summary.
              result = await encodeCanvas(canvas, fmt, 0.3);
              entry.targetMissed = true;
            } else {
              quality = result.quality;
            }
          } else {
            result = await encodeCanvas(canvas, fmt, quality);
          }
          var blob = result.blob;
          var usedFmt = result.fmt || fmt;
          if (result.fellBack) entry.fellBack = true;
"""

OLD_TARGET = """      async function encodeToTarget(canvas, mime, targetBytes) {
        var T = window.weddingAITool;
        var LO = 0.3, HI = 0.95;
        var work = canvas;
        for (var round = 0; round < 5; round++) {
          var lo = LO, hi = HI, best = null, bestQ = LO;
          for (var i = 0; i < 7; i++) {
            var mid = (lo + hi) / 2;
            var b = await T.canvasToBlob(work, mime, mid);
            if (!b || b.size === 0) { hi = mid; continue; }
            if (b.size <= targetBytes) { best = b; bestQ = mid; lo = mid; }
            else { hi = mid; }
            if (hi - lo < 0.01) break;
          }
          if (best) return { blob: best, quality: bestQ };
          // Nothing fits at the lowest quality: shrink the canvas.
          var small = await T.canvasToBlob(work, mime, LO);
          if (!small || small.size === 0) break;
"""

NEW_TARGET = """      async function encodeToTarget(canvas, fmt, targetBytes) {
        var LO = 0.3, HI = 0.95;
        var work = canvas;
        for (var round = 0; round < 5; round++) {
          var lo = LO, hi = HI, best = null, bestQ = LO;
          // A lossless encode has no quality dial, so the search is skipped
          // for it - only the downscale can bring the file under the target.
          // A WebAssembly encode is also much slower than a Canvas one, so
          // it gets fewer rounds.
          var rounds = fmt.wasm ? 5 : 7;
          if (!fmt.lossless) {
            for (var i = 0; i < rounds; i++) {
              var mid = (lo + hi) / 2;
              var enc = await encodeCanvas(work, fmt, mid);
              var b = enc.blob;
              if (enc.fellBack) return { blob: null, quality: LO };
              if (!b || b.size === 0) { hi = mid; continue; }
              if (b.size <= targetBytes) { best = b; bestQ = mid; lo = mid; }
              else { hi = mid; }
              if (hi - lo < 0.01) break;
            }
            if (best) return { blob: best, quality: bestQ };
          }
          // Nothing fits at the lowest quality: shrink the canvas.
          var smallEnc = await encodeCanvas(work, fmt, LO);
          var small = smallEnc.blob;
          if (smallEnc.fellBack) return { blob: null, quality: LO };
          if (!small || small.size === 0) break;
"""

OLD_EXIF = """          if (settings.keepExif && mime === 'image/jpeg' && entry.inputFile) {
"""

NEW_EXIF = """          if (settings.keepExif && usedFmt.mime === 'image/jpeg' && entry.inputFile) {
"""

OLD_NAME = """          entry.outputName = window.weddingAITool.safeFileName(entry.name, '-min.' + (mime === 'image/png' ? 'png' : mime === 'image/webp' ? 'webp' : 'jpg'));
"""

NEW_NAME = """          entry.outputName = window.weddingAITool.safeFileName(entry.name, '-min.' + usedFmt.ext);
"""

OLD_READY = """      refreshUI();
    });
    </script>
"""

NEW_READY = """      detectFormatSupport();
      refreshUI();
    });
    </script>
"""

# The format control, matched by role rather than by language.
FORMAT_RE = re.compile(
    r'<label for="format"[^>]*>.*?</label>\s*<select id="format">.*?</select>',
    re.S)

IMPORT_MAP_RE = re.compile(r'<script type="importmap">.*?</script>', re.S)


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmpwrite")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def page_path(lang: str) -> Path:
    sub = "tools/%s" % TOOL if lang == "en" else "%s/tools/%s" % (lang, TOOL)
    return ROOT / sub / "index.html"


def patch_html(path: Path, dry: bool) -> int:
    """The format control + the import map + the module script."""
    text = path.read_text(encoding="utf-8")
    changes = 0

    m = FORMAT_RE.search(text)
    if not m:
        raise SystemExit("[FAIL] %s: no format control found" % path)
    # Keep the indentation of the label line.
    line_start = text.rfind("\n", 0, m.start()) + 1
    indent = text[line_start:m.start()]
    if indent.strip():
        indent = ""
    block = FORMAT_BLOCK.replace("{ind}", indent)
    text = text[:m.start()] + block + text[m.end():]
    changes += 1

    if '<script type="importmap">' in text:
        # The map is already there - refresh it, because the pinned
        # wasm-feature-detect version lives in its URL.
        text, n = IMPORT_MAP_RE.subn(IMPORT_MAP_LINE, text, count=1)
        if not n:
            raise SystemExit("[FAIL] %s: the import map is malformed" % path)
        changes += 1
    else:
        if INLINE_ANCHOR not in text:
            raise SystemExit("[FAIL] %s: the inline script anchor was not found" % path)
        text = text.replace(INLINE_ANCHOR, MODULE_BLOCK + INLINE_ANCHOR, 1)
        changes += 1

    if changes and not dry:
        write_atomic(path, text)
    return changes


def patch_js(path: Path, dry: bool) -> int:
    """The inline JS - English page only."""
    text = path.read_text(encoding="utf-8")
    changes = 0
    # (old, new, marker, what). The MARKER is a string that only exists in
    # the NEW text - `new in text` cannot be used for that, because the new
    # text starts with the old text and a second run would insert the
    # block twice.
    for old, new, marker, what in (
            (OLD_SETTINGS_END, NEW_SETTINGS_END,
             "var CAN = { webp: false, avif: false };", "the format table"),
            (OLD_ENCODE, NEW_ENCODE,
             "var usedFmt = result.fmt || fmt;", "the encode dispatch"),
            (OLD_TARGET, NEW_TARGET,
             "async function encodeToTarget(canvas, fmt, targetBytes) {", "encodeToTarget"),
            (OLD_EXIF, NEW_EXIF,
             "settings.keepExif && usedFmt.mime === 'image/jpeg'", "the EXIF copy"),
            (OLD_NAME, NEW_NAME,
             "'-min.' + usedFmt.ext", "the output file name"),
            (OLD_READY, NEW_READY,
             "detectFormatSupport();", "the readiness hook"),
    ):
        if marker in text:
            continue  # already patched
        if old not in text:
            raise SystemExit("[FAIL] %s: could not find %s" % (path, what))
        text = text.replace(old, new, 1)
        changes += 1
    if changes and not dry:
        write_atomic(path, text)
    return changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for lang in LANGS:
        path = page_path(lang)
        if not path.is_file():
            raise SystemExit("[FAIL] missing page: %s" % path)
        n = patch_html(path, args.dry_run)
        j = 0
        if lang == "en":
            j = patch_js(path, args.dry_run)
        print("  %-3s html=%d js=%d" % (lang, n, j))

    if args.dry_run:
        print("\n[DRY RUN] nothing was written")
    else:
        print("\nNow run:")
        print("  python scripts/propagate-tool-js.py")
        print("  python scripts/check-tool-script-syntax.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
