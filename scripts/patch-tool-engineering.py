#!/usr/bin/env python3
"""
Engineering pass over the tool suite: §2.5 - §2.9.

    2.5  the per-pixel background-removal loop moves into a Web Worker
    2.6  fileToImage() decodes with createImageBitmap (off the main thread)
    2.7  the EXIF orientation is applied EXPLICITLY ('from-image')
    2.8  every decoded image is released - bitmaps closed, URLs revoked
    2.9  the rows show a real percentage instead of an indefinite spinner

WHY A SCRIPT AND NOT A HAND EDIT
--------------------------------
The English page is the single source of truth for the inline script of a
tool page (scripts/propagate-tool-js.py copies it to the 10 localized
copies). So every behavioural change is made HERE, on the English source,
and then propagated. Editing a localized copy directly would be undone by
the next propagation run.

Each edit is an exact-string replacement with an expected hit count, so a
changed upstream file fails loudly instead of silently skipping a fix.

Usage
-----
    python scripts/patch-tool-engineering.py --dry-run
    python scripts/patch-tool-engineering.py
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def atomic_write(path: Path, text: str) -> None:
    """temp file + fsync + os.replace - never leave a half-written file."""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


class Edit:
    def __init__(self, rel, old, new, count=1, note=""):
        self.rel = rel
        self.old = old
        self.new = new
        self.count = count
        self.note = note


def apply_edits(edits, dry_run=False):
    by_file = {}
    for e in edits:
        by_file.setdefault(e.rel, []).append(e)

    touched = 0
    for rel, items in by_file.items():
        path = ROOT / rel
        if not path.exists():
            raise SystemExit("MISSING FILE: %s" % rel)
        text = path.read_text(encoding="utf-8")
        original = text
        for e in items:
            hits = text.count(e.old)
            if hits == e.count:
                text = text.replace(e.old, e.new)
                continue
            # Already applied? The replacement text is present, so the edit
            # is a no-op instead of a hard failure. That keeps the script
            # re-runnable after it has been applied once.
            if hits == 0 and text.count(e.new) >= 1:
                print("      (already applied) %s" % (e.note or rel))
                continue
            raise SystemExit(
                "ANCHOR MISS in %s (expected %d hit(s), found %d)\n--- anchor ---\n%s\n"
                % (rel, e.count, hits, e.old[:400])
            )
        if text == original:
            continue
        touched += 1
        if not dry_run:
            atomic_write(path, text)
        print("  %s  (%d edit(s))" % (rel, len(items)))
    print("  -> %d file(s) %s" % (touched, "would change" if dry_run else "changed"))


# --------------------------------------------------------------------------
# js/tools/common.js
# --------------------------------------------------------------------------

COMMON_RELEASE = r"""    img.src = url;
  }

  // ---------- release a decoded image -----------------------------------------
  //
  // fileToImage() can hand back two different things: an ImageBitmap (the
  // createImageBitmap path) or an <img> backed by an object URL. They need
  // different teardown - bitmap.close() frees GPU memory, revokeObjectURL()
  // frees the blob - and a tool page should not have to know which one it
  // got. releaseImage() is the one teardown call.
  function releaseImage(loaded) {
    if (!loaded) return;
    try {
      if (typeof loaded.release === 'function') { loaded.release(); return; }
      if (loaded.url) URL.revokeObjectURL(loaded.url);
    } catch (e) { /* ignore */ }
  }

  // ---------- pixel loop in a Worker (§2.5) -------------------------------------
  //
  // The colour-key background removal walks every pixel of the photo. On a
  // 12 MP wedding photo that is 12 million iterations of a sqrt - a few
  // hundred milliseconds of blocked main thread during which the tab cannot
  // scroll and the progress bar cannot move.
  //
  // The worker is a same-origin classic worker (/js/tools/pixel-worker.js),
  // which `worker-src 'self' blob:` allows. The pixel buffer is TRANSFERRED
  // in both directions, so nothing is copied, and the worker reports progress
  // while it works so the row can show a real percentage (§2.9).
  //
  // A fresh Worker is created per call and terminated afterwards: the
  // messages of two concurrent runs would otherwise interleave on one
  // worker's onmessage handler.
  function runPixelLoop(payload, onProgress) {
    return new Promise(function (resolve, reject) {
      if (typeof Worker !== 'function') {
        reject(new Error('Worker is not available'));
        return;
      }
      var worker = null;
      try {
        worker = new Worker('/js/tools/pixel-worker.js');
      } catch (e) {
        reject(new Error('Could not start the pixel worker: ' + (e && e.message ? e.message : e)));
        return;
      }
      var settled = false;
      function finish(err, value) {
        if (settled) return;
        settled = true;
        try { worker.terminate(); } catch (e2) { /* ignore */ }
        if (err) reject(err); else resolve(value);
      }
      worker.onmessage = function (e) {
        var m = e.data || {};
        if (typeof m.progress === 'number') {
          if (typeof onProgress === 'function') {
            try { onProgress(m.progress); } catch (e3) { /* ignore */ }
          }
          return;
        }
        if (m.buffer) finish(null, m.buffer);
        else finish(new Error('The pixel worker returned no data'));
      };
      worker.onerror = function (e) {
        finish(new Error(e && e.message ? e.message : 'The pixel worker failed'));
      };
      try {
        worker.postMessage(payload, [payload.buffer]);
      } catch (e4) {
        finish(e4);
      }
    });
  }

  // ---------- canvas → blob (with format + quality) -----------------------------
"""

COMMON_HEIC_PROGRESS = r"""      var options = {
        blob: file,
        toType: opts.toType || 'image/jpeg',
        quality: typeof opts.quality === 'number' ? opts.quality : 0.92,
        multiple: false,
      };
      // heic2any reports 0..1 while it decodes - that is what the row shows
      // instead of an indefinite spinner (§2.9).
      if (typeof opts.onProgress === 'function') {
        options.onProgress = function (p) {
          try { opts.onProgress(typeof p === 'number' ? p : 0); } catch (e) { /* ignore */ }
        };
      }
      return heic2any(options);
"""

# --------------------------------------------------------------------------
# tools/remove-background-wedding-portrait
# --------------------------------------------------------------------------

REMOVE_BG_OLD_LOOP = r"""      // The colour key: strip every pixel that sits close to the sampled
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
"""

REMOVE_BG_NEW_LOOP = r"""      // The per-pixel loop, kept in its own function so that the Worker path
      // and the main-thread fallback run the SAME maths - byte for byte.
      function applyPixelLoop(data, bgR, bgG, bgB, innerT, outerT, bandWidth, mode) {
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
      }

      // The colour key: strip every pixel that sits close to the sampled
      // backdrop colour. Instant and free, but it can only remove a
      // background it was told about - which is why the AI path exists.
      //
      // The loop runs in a Worker so a 12 MP photo does not freeze the tab
      // (§2.5). If the Worker cannot start, the identical loop runs on the
      // main thread instead - the result is the same either way.
      async function colorKeyCanvas(img, w, h, settings, onProgress) {
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

        // The buffer is transferred to the Worker, so it must hold exactly
        // the pixel data - no extra bytes at the end.
        var buffer = data.buffer.byteLength === data.length
          ? data.buffer
          : new Uint8ClampedArray(data).buffer;

        try {
          var outBuffer = await window.weddingAITool.runPixelLoop({
            buffer: buffer,
            bgR: bgR, bgG: bgG, bgB: bgB,
            innerT: innerT, outerT: outerT, bandWidth: bandWidth,
            mode: mode
          }, onProgress);
          var out = new Uint8ClampedArray(outBuffer);
          ctx.putImageData(new ImageData(out, w, h), 0, 0);
        } catch (err) {
          // No Worker, or it failed: run the same maths here instead. The
          // original buffer was transferred away, so read the pixels again.
          var fresh = ctx.getImageData(0, 0, w, h);
          applyPixelLoop(fresh.data, bgR, bgG, bgB, innerT, outerT, bandWidth, mode);
          ctx.putImageData(fresh, 0, 0);
        }

        return canvas;
      }
"""

REMOVE_BG_PROCESS_OLD = r"""        try {
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

          var mime = (mode === 'jpg') ? 'image/jpeg' : 'image/png';
          var quality = (mode === 'jpg') ? 0.92 : undefined;
          var blob = await window.weddingAITool.canvasToBlob(canvas, mime, quality);
"""

REMOVE_BG_PROCESS_NEW = r"""        try {
          entry.percent = 5;
          refreshUI();
          var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
          var img = loaded.img;
          var w = img.naturalWidth, h = img.naturalHeight;

          var mode = settings.mode;
          var canvas;
          entry.percent = 15;
          refreshUI();
          if (settings.method === 'ai') {
            window.weddingAITool.toast(
              window.weddingAITool.t('aiModelLoading', 'Loading the AI model...'),
              'success');
            canvas = await aiMatteCanvas(img, w, h, settings);
          } else {
            canvas = await colorKeyCanvas(img, w, h, settings, function (p) {
              entry.percent = 15 + Math.round(p * 0.75);
              refreshUI();
            });
          }

          entry.percent = 92;
          refreshUI();
          var mime = (mode === 'jpg') ? 'image/jpeg' : 'image/png';
          var quality = (mode === 'jpg') ? 0.92 : undefined;
          var blob = await window.weddingAITool.canvasToBlob(canvas, mime, quality);
"""


# --------------------------------------------------------------------------
# edit list
# --------------------------------------------------------------------------

def build_edits():
    E = []

    # ---- common.js -------------------------------------------------------
    E.append(Edit(
        "js/tools/common.js",
        r"""    img.src = url;
  }

  // ---------- canvas → blob (with format + quality) -----------------------------
""",
        COMMON_RELEASE,
        note="releaseImage() + runPixelLoop()",
    ))
    E.append(Edit(
        "js/tools/common.js",
        r"""      return heic2any({
        blob: file,
        toType: opts.toType || 'image/jpeg',
        quality: typeof opts.quality === 'number' ? opts.quality : 0.92,
        multiple: false,
      });
""",
        COMMON_HEIC_PROGRESS,
        note="heic2any onProgress",
    ))
    E.append(Edit(
        "js/tools/common.js",
        r"""    fileToImage: fileToImage,
    canvasToBlob: canvasToBlob,
""",
        r"""    fileToImage: fileToImage,
    releaseImage: releaseImage,
    runPixelLoop: runPixelLoop,
    canvasToBlob: canvasToBlob,
""",
        note="export the new helpers",
    ))
    E.append(Edit(
        "js/tools/common.js",
        "    version: '1.1.0',",
        "    version: '1.2.0',",
        note="version bump",
    ))

    # ---- remove-background-wedding-portrait --------------------------------
    E.append(Edit(
        "tools/remove-background-wedding-portrait/index.html",
        REMOVE_BG_OLD_LOOP, REMOVE_BG_NEW_LOOP,
        note="§2.5 pixel loop in a Worker",
    ))
    E.append(Edit(
        "tools/remove-background-wedding-portrait/index.html",
        REMOVE_BG_PROCESS_OLD, REMOVE_BG_PROCESS_NEW,
        note="§2.9 progress",
    ))
    E.append(Edit(
        "tools/remove-background-wedding-portrait/index.html",
        r"""          URL.revokeObjectURL(loaded.url);
""",
        r"""          window.weddingAITool.releaseImage(loaded);
""",
        note="§2.8 release",
    ))
    E.append(Edit(
        "tools/remove-background-wedding-portrait/index.html",
        r"""            URL.revokeObjectURL(res.url);
""",
        r"""            window.weddingAITool.releaseImage(res);
""",
        note="§2.8 release",
    ))

    # ---- compress-wedding-photos -------------------------------------------
    E.append(Edit(
        "tools/compress-wedding-photos/index.html",
        r"""          // free the loaded image
          URL.revokeObjectURL(loaded.url);
""",
        r"""          // free the loaded image
          window.weddingAITool.releaseImage(loaded);
""",
        note="§2.8 release",
    ))
    E.append(Edit(
        "tools/compress-wedding-photos/index.html",
        r"""        try {
          var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
          var img = loaded.img;
          var w = img.naturalWidth, h = img.naturalHeight;
""",
        r"""        try {
          entry.percent = 10;
          refreshUI();
          var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
          var img = loaded.img;
          var w = img.naturalWidth, h = img.naturalHeight;
          entry.percent = 30;
          refreshUI();
""",
        note="§2.9 progress",
    ))
    E.append(Edit(
        "tools/compress-wedding-photos/index.html",
        r"""          var canvas = await window.weddingAITool.resizeCanvas(img, tw, th);
""",
        r"""          var canvas = await window.weddingAITool.resizeCanvas(img, tw, th);
          entry.percent = 85;
          refreshUI();
""",
        note="§2.9 progress",
    ))

    # ---- crop-wedding-photo-for-reels --------------------------------------
    E.append(Edit(
        "tools/crop-wedding-photo-for-reels/index.html",
        r"""          URL.revokeObjectURL(loaded.url);
""",
        r"""          window.weddingAITool.releaseImage(loaded);
""",
        note="§2.8 release",
    ))
    E.append(Edit(
        "tools/crop-wedding-photo-for-reels/index.html",
        r"""          if (!entry.stageImg) {
            var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
            entry.stageImg = loaded.img;
            entry.stageUrl = loaded.url;
          }
""",
        r"""          if (!entry.stageImg) {
            var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
            entry.stageImg = loaded.img;
            entry.stageRelease = loaded.release;
          }
""",
        note="§2.8 release",
    ))
    E.append(Edit(
        "tools/crop-wedding-photo-for-reels/index.html",
        r"""        try {
          var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
          var img = loaded.img;
          var W = img.naturalWidth;
""",
        r"""        try {
          entry.percent = 10;
          refreshUI();
          var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
          var img = loaded.img;
          var W = img.naturalWidth;
""",
        note="§2.9 progress",
    ))
    E.append(Edit(
        "tools/crop-wedding-photo-for-reels/index.html",
        r"""          var blob = await window.weddingAITool.canvasToBlob(canvas, 'image/jpeg', settings.quality);
""",
        r"""          entry.percent = 90;
          refreshUI();
          var blob = await window.weddingAITool.canvasToBlob(canvas, 'image/jpeg', settings.quality);
""",
        note="§2.9 progress",
    ))

    # ---- heic-to-jpg-wedding-photos ----------------------------------------
    E.append(Edit(
        "tools/heic-to-jpg-wedding-photos/index.html",
        r"""          return { img: loaded.img, release: function () { URL.revokeObjectURL(loaded.url); } };
""",
        r"""          return { img: loaded.img, release: loaded.release };
""",
        note="§2.8 release",
    ))
    E.append(Edit(
        "tools/heic-to-jpg-wedding-photos/index.html",
        r"""      async function loadDecodableImage(file) {
        try {
          var loaded = await window.weddingAITool.fileToImage(file);
""",
        r"""      async function loadDecodableImage(file, onProgress) {
        try {
          var loaded = await window.weddingAITool.fileToImage(file);
""",
        note="§2.9 progress",
    ))
    E.append(Edit(
        "tools/heic-to-jpg-wedding-photos/index.html",
        r"""          var blob = await window.weddingAITool.decodeHeic(file, { toType: 'image/jpeg', quality: 1 });
""",
        r"""          var blob = await window.weddingAITool.decodeHeic(file, { toType: 'image/jpeg', quality: 1, onProgress: onProgress });
""",
        note="§2.9 progress",
    ))

    # ---- add-text-to-wedding-photo -----------------------------------------
    E.append(Edit(
        "tools/add-text-to-wedding-photo/index.html",
        r"""              files[idx].img = loaded.img;
              URL.revokeObjectURL(loaded.url);
""",
        r"""              files[idx].img = loaded.img;
              files[idx].imgRelease = loaded.release;
""",
        note="§2.8 keep + release later",
    ))
    E.append(Edit(
        "tools/add-text-to-wedding-photo/index.html",
        r"""          if (!entry.img) {
            var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
            entry.img = loaded.img;
            URL.revokeObjectURL(loaded.url);
          }
""",
        r"""          if (!entry.img) {
            var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
            entry.img = loaded.img;
            entry.imgRelease = loaded.release;
          }
""",
        note="§2.8 keep + release later",
    ))
    E.append(Edit(
        "tools/add-text-to-wedding-photo/index.html",
        r"""        try {
          if (!entry.img) {
""",
        r"""        try {
          entry.percent = 10;
          refreshUI();
          if (!entry.img) {
""",
        note="§2.9 progress",
    ))
    E.append(Edit(
        "tools/add-text-to-wedding-photo/index.html",
        r"""          var blob = await window.weddingAITool.canvasToBlob(canvas, mime, quality);
""",
        r"""          entry.percent = 90;
          refreshUI();
          var blob = await window.weddingAITool.canvasToBlob(canvas, mime, quality);
""",
        note="§2.9 progress",
    ))

    # ---- wedding-photo-collage ---------------------------------------------
    E.append(Edit(
        "tools/wedding-photo-collage/index.html",
        r"""          if (entry.img && entry.img.complete) return Promise.resolve(i);
          return window.weddingAITool.fileToImage(entry.inputFile)
            .then(function (loaded) {
              entry.img = loaded.img;
              // We can keep the preview blob URL alive — the file list uses it.
            })
""",
        r"""          // An ImageBitmap has no .complete - the decoded image is simply
          // there once it is set.
          if (entry.img) return Promise.resolve(i);
          return window.weddingAITool.fileToImage(entry.inputFile)
            .then(function (loaded) {
              entry.img = loaded.img;
              entry.imgRelease = loaded.release;
              // The preview blob URL stays alive - the file list uses it.
            })
""",
        note="§2.8 ImageBitmap has no .complete",
    ))

    # ---- the three "one photo" makers --------------------------------------
    for slug in ("save-the-date-maker", "wedding-invitation-maker", "wedding-video-invitation-maker"):
        E.append(Edit(
            "tools/%s/index.html" % slug,
            r"""              if (state.img && state.img._objectUrl) URL.revokeObjectURL(state.img._objectUrl);
              res.img._objectUrl = res.url;
""",
            r"""              if (state.img && state.img._release) state.img._release();
              res.img._release = res.release;
""",
            note="§2.8 release",
        ))
        E.append(Edit(
            "tools/%s/index.html" % slug,
            r"""        if (state.img && state.img._objectUrl) URL.revokeObjectURL(state.img._objectUrl);
""",
            r"""        if (state.img && state.img._release) state.img._release();
""",
            note="§2.8 release",
        ))

    # ---- release the cached decodes when the entry goes away (§2.8) ---------
    #
    # An ImageBitmap is GPU memory. A batch of 12 MP photos that is never
    # closed is a tab that dies. The cached images are released when the
    # entry is removed or the whole list is cleared.
    E.append(Edit(
        "tools/wedding-photo-collage/index.html",
        r"""      function clearAll() {
        files.forEach(function (f) {
          if (f.previewUrl) URL.revokeObjectURL(f.previewUrl);
        });
""",
        r"""      function clearAll() {
        files.forEach(function (f) {
          if (f.previewUrl) URL.revokeObjectURL(f.previewUrl);
          if (f.imgRelease) f.imgRelease();
        });
""",
        note="§2.8 release on clear",
    ))
    E.append(Edit(
        "tools/wedding-photo-collage/index.html",
        r"""        if (f.previewUrl) URL.revokeObjectURL(f.previewUrl);
        files.splice(idx, 1);
""",
        r"""        if (f.previewUrl) URL.revokeObjectURL(f.previewUrl);
        if (f.imgRelease) f.imgRelease();
        files.splice(idx, 1);
""",
        note="§2.8 release on remove",
    ))
    E.append(Edit(
        "tools/add-text-to-wedding-photo/index.html",
        r"""      function clearAll() {
        files.forEach(function (f) {
          if (f.previewUrl) URL.revokeObjectURL(f.previewUrl);
        });
""",
        r"""      function clearAll() {
        files.forEach(function (f) {
          if (f.previewUrl) URL.revokeObjectURL(f.previewUrl);
          if (f.imgRelease) f.imgRelease();
        });
""",
        note="§2.8 release on clear",
    ))
    E.append(Edit(
        "tools/add-text-to-wedding-photo/index.html",
        r"""          if (f && f.previewUrl) URL.revokeObjectURL(f.previewUrl);
          files.splice(idx, 1);
""",
        r"""          if (f && f.previewUrl) URL.revokeObjectURL(f.previewUrl);
          if (f && f.imgRelease) f.imgRelease();
          files.splice(idx, 1);
""",
        note="§2.8 release on remove",
    ))
    E.append(Edit(
        "tools/crop-wedding-photo-for-reels/index.html",
        r"""      function clearAll() {
        files.forEach(function (f) {
          if (f.previewUrl) URL.revokeObjectURL(f.previewUrl);
        });
""",
        r"""      function clearAll() {
        files.forEach(function (f) {
          if (f.previewUrl) URL.revokeObjectURL(f.previewUrl);
          if (f.stageRelease) f.stageRelease();
        });
""",
        note="§2.8 release on clear",
    ))
    E.append(Edit(
        "tools/crop-wedding-photo-for-reels/index.html",
        r"""          if (f && f.previewUrl) URL.revokeObjectURL(f.previewUrl);
          files.splice(idx, 1);
""",
        r"""          if (f && f.previewUrl) URL.revokeObjectURL(f.previewUrl);
          if (f && f.stageRelease) f.stageRelease();
          files.splice(idx, 1);
""",
        note="§2.8 release on remove",
    ))

    # ---- release on the error path too (§2.8) --------------------------------
    #
    # The release used to sit at the end of the try block, so an exception
    # skipped it and the decoded image stayed alive forever. A finally block
    # closes it on every path.
    E.append(Edit(
        "tools/remove-background-wedding-portrait/index.html",
        r"""        try {
          entry.percent = 5;
          refreshUI();
          var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
""",
        r"""        var loaded = null;
        try {
          entry.percent = 5;
          refreshUI();
          loaded = await window.weddingAITool.fileToImage(entry.inputFile);
""",
        note="§2.8 declare loaded outside try",
    ))
    E.append(Edit(
        "tools/remove-background-wedding-portrait/index.html",
        r"""          entry.outputName = window.weddingAITool.safeFileName(entry.name, '-nobg.' + ext);
          window.weddingAITool.releaseImage(loaded);
        } catch (err) {
          entry.status = 'error';
          entry.error = err && err.message ? err.message : String(err);
        }
        refreshUI();
""",
        r"""          entry.outputName = window.weddingAITool.safeFileName(entry.name, '-nobg.' + ext);
        } catch (err) {
          entry.status = 'error';
          entry.error = err && err.message ? err.message : String(err);
        } finally {
          window.weddingAITool.releaseImage(loaded);
        }
        refreshUI();
""",
        note="§2.8 release in finally",
    ))
    E.append(Edit(
        "tools/compress-wedding-photos/index.html",
        r"""        try {
          entry.percent = 10;
          refreshUI();
          var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
""",
        r"""        var loaded = null;
        try {
          entry.percent = 10;
          refreshUI();
          loaded = await window.weddingAITool.fileToImage(entry.inputFile);
""",
        note="§2.8 declare loaded outside try",
    ))
    E.append(Edit(
        "tools/compress-wedding-photos/index.html",
        r"""          // free the loaded image
          window.weddingAITool.releaseImage(loaded);
        } catch (err) {
          entry.status = 'error';
          entry.error = err && err.message ? err.message : String(err);
        }
        refreshUI();
""",
        r"""        } catch (err) {
          entry.status = 'error';
          entry.error = err && err.message ? err.message : String(err);
        } finally {
          // free the loaded image
          window.weddingAITool.releaseImage(loaded);
        }
        refreshUI();
""",
        note="§2.8 release in finally",
    ))
    E.append(Edit(
        "tools/crop-wedding-photo-for-reels/index.html",
        r"""        try {
          entry.percent = 10;
          refreshUI();
          var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
          var img = loaded.img;
          var W = img.naturalWidth;
""",
        r"""        var loaded = null;
        try {
          entry.percent = 10;
          refreshUI();
          loaded = await window.weddingAITool.fileToImage(entry.inputFile);
          var img = loaded.img;
          var W = img.naturalWidth;
""",
        note="§2.8 declare loaded outside try",
    ))
    E.append(Edit(
        "tools/crop-wedding-photo-for-reels/index.html",
        r"""          entry.outputName = window.weddingAITool.safeFileName(entry.name, '-' + slug + ext);
          window.weddingAITool.releaseImage(loaded);
        } catch (err) {
          entry.status = 'error';
          entry.error = err && err.message ? err.message : String(err);
        }
        refreshUI();
""",
        r"""          entry.outputName = window.weddingAITool.safeFileName(entry.name, '-' + slug + ext);
        } catch (err) {
          entry.status = 'error';
          entry.error = err && err.message ? err.message : String(err);
        } finally {
          window.weddingAITool.releaseImage(loaded);
        }
        refreshUI();
""",
        note="§2.8 release in finally",
    ))
    E.append(Edit(
        "tools/heic-to-jpg-wedding-photos/index.html",
        r"""        try {
          var loaded = await loadDecodableImage(entry.inputFile);
          var img = loaded.img;
""",
        r"""        var loaded = null;
        try {
          loaded = await loadDecodableImage(entry.inputFile, function (p) {
            entry.percent = Math.round(p * 90);
            refreshUI();
          });
          var img = loaded.img;
""",
        note="§2.8 + §2.9",
    ))
    E.append(Edit(
        "tools/heic-to-jpg-wedding-photos/index.html",
        r"""          entry.outputName = window.weddingAITool.safeFileName(entry.name, '.jpg');
          // free the loaded image
          loaded.release();
        } catch (err) {
""",
        r"""          entry.outputName = window.weddingAITool.safeFileName(entry.name, '.jpg');
        } catch (err) {
""",
        note="§2.8 move the release",
    ))
    E.append(Edit(
        "tools/heic-to-jpg-wedding-photos/index.html",
        r"""            entry.error = rawMsg;
          }
        }
        refreshUI();
""",
        r"""            entry.error = rawMsg;
          }
        } finally {
          // free the loaded image
          if (loaded && loaded.release) loaded.release();
        }
        refreshUI();
""",
        note="§2.8 release in finally",
    ))

    return E


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("patch-tool-engineering: §2.5-§2.9")
    apply_edits(build_edits(), dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
