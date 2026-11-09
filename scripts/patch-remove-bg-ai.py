#!/usr/bin/env python3
"""
Add real AI background removal (MODNet) to the remove-background tool.

WHY THIS EXISTS (found 2026-11-09)
----------------------------------
The tool's "background removal" was a COLOUR KEY: it sampled the backdrop
colour from the four corners of the photo and then stripped every pixel
within a tolerance of it. That is not background removal - it cannot tell a
wall from a dress, it eats a white veil against a pale wall, and it fails
completely when the backdrop is busy (a hedge, a crowd, a patterned
tablecloth).

MODNet is an actual matting network. It runs ON THE DEVICE through ONNX
Runtime Web, so the promise of the site - nothing is ever uploaded - holds.

THE COST (this is the "$0 but carries a cost" case)
----------------------------------------------------
* js/vendor/onnxruntime/  11.0 MB WASM runtime + 350 KB glue
* js/vendor/modnet/         6.3 MB quantised model
  -> ~17.5 MB, downloaded ONCE from this origin and then cached by the
     browser. Nothing is uploaded and no third party is contacted.
* 'wasm-unsafe-eval' has to be in the CSP. It already is
  (functions/_middleware.js buildCsp() and _headers, both 2026-11-09).
* Apache-2.0 (the model) and MIT (the runtime), so commercial use is fine.
  The alternative RMBG-1.4 is NON-COMMERCIAL and is therefore not used.

THE UX
------
The colour key stays as the default so that nobody gets a surprise 17 MB
download. AI matting is one dropdown away and says what it costs. When the
model is loading the page says so, because the first run is slow.

The colour key and the matte then feed the SAME output stage (PNG with
transparency, or JPG filled with the chosen backdrop colour), so the two
methods are interchangeable.

Usage:  python scripts/patch-remove-bg-ai.py [--dry-run]
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
SLUG = "remove-background-wedding-portrait"

# The method picker. The strings live in the dictionary so the middleware
# translates them; the English text below is the static fallback.
METHOD_MARKUP = """                    <div class="wa-tool-control">
                        <label for="method" data-i18n="tools.copy.bgMethod.zzzzzz7a01">Background removal method</label>
                        <select id="method">
                            <option value="key" selected data-i18n="tools.copy.bgMethodColor.zzzzzz7a02">Smart colour key (instant, no download)</option>
                            <option value="ai" data-i18n="tools.copy.bgMethodAi.zzzzzz7a03">AI matting (MODNet - one-time ~17 MB download, runs on your device)</option>
                        </select>
                        <small data-i18n="tools.copy.aiModelNotice.zzzzzz4c5d">The first AI run downloads the model (~17 MB) once and then works offline.</small>
                    </div>
"""

JS_OLD_VARS = """      var outputModeEl = document.getElementById('output-mode');
"""
JS_NEW_VARS = """      var outputModeEl = document.getElementById('output-mode');
      var methodEl = document.getElementById('method');
"""

JS_OLD_SETTINGS = """      function getCurrentSettings() {
        var bg = hexToRgb(bgColorEl.value);
        return {
          bg: bg,
          tolerance: parseInt(toleranceEl.value, 10),
          feather: parseInt(featherEl.value, 10),
          mode: outputModeEl.value, // 'png' or 'jpg'
        };
      }
"""
JS_NEW_SETTINGS = """      function getCurrentSettings() {
        var bg = hexToRgb(bgColorEl.value);
        return {
          bg: bg,
          bgHex: bgColorEl.value,
          method: methodEl ? methodEl.value : 'key',
          tolerance: parseInt(toleranceEl.value, 10),
          feather: parseInt(featherEl.value, 10),
          mode: outputModeEl.value, // 'png' or 'jpg'
        };
      }

      // The colour key: strip every pixel that sits close to the sampled
      // backdrop colour. Instant and free, but it can only remove a
      // background it was told about - which is why the AI path exists.
      function colorKeyCanvas(img, w, h, settings) {
        var canvas = document.createElement('canvas');
        canvas.width = w;
        canvas.height = h;
        var ctx = canvas.getContext('2d', { willReadFrequently: true });
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.clearRect(0, 0, w, h);
        ctx.drawImage(img, 0, 0);

        var imageData = ctx.getImageData(0, 0, w, h);
        var data = imageData.data;
        var bgR = settings.bg.r, bgG = settings.bg.g, bgB = settings.bg.b;
        var tol = settings.tolerance;
        var feather = settings.feather;
        var innerT = tol;
        // Feather band width: ~8 RGB units per 1 px of feathering (tunable constant)
        var outerT = tol + feather * 8;
        var bandWidth = outerT - innerT;
        var mode = settings.mode;

        // Single-pass pixel loop. Math.sqrt is the only expensive op here.
        for (var i = 0; i < data.length; i += 4) {
          var dr = data[i]     - bgR;
          var dg = data[i + 1] - bgG;
          var db = data[i + 2] - bgB;
          var dist = Math.sqrt(dr * dr + dg * dg + db * db);
          var alpha;
          if (dist <= innerT) {
            alpha = 0;
          } else if (dist < outerT) {
            alpha = Math.round(((dist - innerT) / bandWidth) * 255);
          } else {
            alpha = 255;
          }
          if (mode === 'png') {
            // Multiply alpha into existing alpha (preserve any pre-existing transparency in source)
            var prevA = data[i + 3];
            data[i + 3] = Math.round((prevA / 255) * alpha);
          } else {
            // JPG mode: where we'd be transparent, fill with white
            if (alpha < 255) {
              // partial fade: blend toward white by (1 - alpha/255)
              var k = 1 - (alpha / 255);
              data[i]     = Math.round(data[i]     * (1 - k) + 255 * k);
              data[i + 1] = Math.round(data[i + 1] * (1 - k) + 255 * k);
              data[i + 2] = Math.round(data[i + 2] * (1 - k) + 255 * k);
            }
            data[i + 3] = 255;
          }
        }

        ctx.putImageData(imageData, 0, 0);
        return canvas;
      }

      // The AI path: MODNet predicts a matte for the subject, and the matte
      // becomes the alpha channel. The backdrop colour is only used to fill
      // the JPG output - PNG keeps the transparency.
      async function aiMatteCanvas(img, w, h, settings) {
        if (!window.weddingAITool.removeBackgroundAi) {
          throw new Error(window.weddingAITool.t
            ? window.weddingAITool.t('aiRemoveFailed', 'Could not remove the background')
            : 'Could not remove the background');
        }
        var matte = await window.weddingAITool.removeBackgroundAi(img);
        var canvas = document.createElement('canvas');
        canvas.width = w;
        canvas.height = h;
        var ctx = canvas.getContext('2d');
        if (settings.mode === 'jpg') {
          ctx.fillStyle = settings.bgHex;
          ctx.fillRect(0, 0, w, h);
        }
        ctx.drawImage(matte, 0, 0);
        return canvas;
      }
"""

JS_OLD_PROCESS = """        try {
          var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
          var img = loaded.img;
          var w = img.naturalWidth, h = img.naturalHeight;

          // Paint the original image (with its own alpha) onto the working canvas
          var canvas = document.createElement('canvas');
          canvas.width = w;
          canvas.height = h;
          var ctx = canvas.getContext('2d', { willReadFrequently: true });
          ctx.imageSmoothingEnabled = true;
          ctx.imageSmoothingQuality = 'high';
          ctx.clearRect(0, 0, w, h);
          ctx.drawImage(img, 0, 0);

          var imageData = ctx.getImageData(0, 0, w, h);
          var data = imageData.data;
          var bgR = settings.bg.r, bgG = settings.bg.g, bgB = settings.bg.b;
          var tol = settings.tolerance;
          var feather = settings.feather;
          var innerT = tol;
          // Feather band width: ~8 RGB units per 1 px of feathering (tunable constant)
          var outerT = tol + feather * 8;
          var bandWidth = outerT - innerT;
          var mode = settings.mode;

          // Single-pass pixel loop. Math.sqrt is the only expensive op here.
          for (var i = 0; i < data.length; i += 4) {
            var dr = data[i]     - bgR;
            var dg = data[i + 1] - bgG;
            var db = data[i + 2] - bgB;
            var dist = Math.sqrt(dr * dr + dg * dg + db * db);
            var alpha;
            if (dist <= innerT) {
              alpha = 0;
            } else if (dist < outerT) {
              alpha = Math.round(((dist - innerT) / bandWidth) * 255);
            } else {
              alpha = 255;
            }
            if (mode === 'png') {
              // Multiply alpha into existing alpha (preserve any pre-existing transparency in source)
              var prevA = data[i + 3];
              data[i + 3] = Math.round((prevA / 255) * alpha);
            } else {
              // JPG mode: where we'd be transparent, fill with white
              if (alpha < 255) {
                // partial fade: blend toward white by (1 - alpha/255)
                var k = 1 - (alpha / 255);
                data[i]     = Math.round(data[i]     * (1 - k) + 255 * k);
                data[i + 1] = Math.round(data[i + 1] * (1 - k) + 255 * k);
                data[i + 2] = Math.round(data[i + 2] * (1 - k) + 255 * k);
              }
              data[i + 3] = 255;
            }
          }

          ctx.putImageData(imageData, 0, 0);

          var mime = (mode === 'jpg') ? 'image/jpeg' : 'image/png';"""

JS_NEW_PROCESS = """        try {
          var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
          var img = loaded.img;
          var w = img.naturalWidth, h = img.naturalHeight;

          var mode = settings.mode;
          var canvas;
          if (settings.method === 'ai') {
            window.weddingAITool.toast(
              window.weddingAITool.t('aiModelLoading', 'Loading the AI model...'),
              'success');
            canvas = await aiMatteCanvas(img, w, h, settings);
          } else {
            canvas = colorKeyCanvas(img, w, h, settings);
          }

          var mime = (mode === 'jpg') ? 'image/jpeg' : 'image/png';"""

JS_OLD_WIRE = """      toleranceEl.addEventListener('input', function () { toleranceVal.textContent = toleranceEl.value; });
"""
JS_NEW_WIRE = """      // The tolerance and feather sliders only drive the colour key.
      function syncMethodControls() {
        var isAi = methodEl && methodEl.value === 'ai';
        toleranceEl.disabled = isAi;
        featherEl.disabled = isAi;
        toleranceEl.parentNode.style.opacity = isAi ? '0.45' : '1';
        featherEl.parentNode.style.opacity = isAi ? '0.45' : '1';
      }
      if (methodEl) {
        methodEl.addEventListener('change', syncMethodControls);
        syncMethodControls();
      }

      toleranceEl.addEventListener('input', function () { toleranceVal.textContent = toleranceEl.value; });
"""

JS_REPLACEMENTS = [
    (JS_OLD_VARS, JS_NEW_VARS),
    (JS_OLD_SETTINGS, JS_NEW_SETTINGS),
    (JS_OLD_PROCESS, JS_NEW_PROCESS),
    (JS_OLD_WIRE, JS_NEW_WIRE),
]


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmpwrite")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def patch_markup(text: str):
    """Insert the method picker before the control that holds the backdrop
    colour input.

    The label text is TRANSLATED in the localized copies ("Backdrop color"
    is English only), so the anchor cannot be prose. The id and the CSS class
    are the stable part.
    """
    if 'id="method"' in text:
        return text, 0
    pos = text.find('id="bg-color"')
    if pos < 0:
        raise SystemExit("[FAIL] the backdrop-colour input was not found")
    start = text.rfind('<div class="wa-tool-control">', 0, pos)
    if start < 0:
        raise SystemExit("[FAIL] the backdrop-colour control container was not found")
    return text[:start] + METHOD_MARKUP + text[start:], 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total = 0
    for lang in LANGS:
        p = ROOT / "tools" / SLUG / "index.html" if lang == "en" else ROOT / lang / "tools" / SLUG / "index.html"
        if not p.exists():
            print(f"  {lang}: MISSING")
            continue
        original = p.read_text(encoding="utf-8")
        new, nmarkup = patch_markup(original)
        changes = [f"markup x{nmarkup}"]

        if lang == "en":
            for old, rep in JS_REPLACEMENTS:
                if old not in new:
                    raise SystemExit("[FAIL] the English inline script anchor did not match:\n" + old[:200])
                new = new.replace(old, rep, 1)
            changes.append("js x%d" % len(JS_REPLACEMENTS))

        if new == original:
            print(f"  {lang}: no change")
            continue

        scripts = re.findall(r"(?s)<script\b[^>]*>(.*?)</script>", new)
        biggest = max(scripts, key=len) if scripts else ""
        tmp = Path(os.environ.get("TEMP", ".")) / "rmbg_inline_check.js"
        tmp.write_text(biggest, encoding="utf-8")
        r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"[FAIL] {lang}: inline script does not parse:\n{r.stderr}")

        if not args.dry_run:
            write_atomic(p, new)
        print(f"  {lang}: {', '.join(changes)}")
        total += 1

    print(f"\npatched copies: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
