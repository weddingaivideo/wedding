/*!
 * WeddingAI Free Tools — common.js (v1.2.0)
 * Shared utilities for the /tools/* suite (wedding-photo processing).
 * Loaded as a deferred <script src="/js/tools/common.js?v=1.0.2"> on every tool page.
 *
 * Exports a single global `weddingAITool` namespace. No build step. Plain ES2018.
 *
 * Capabilities used across tools:
 *   - File → Image (handles HEIC fallback path with clear error)
 *   - Drag/drop + click-to-pick input + "Add more" multi-file flow
 *   - Format size (KB/MB) and before/after savings ratio
 *   - Download result as a saved file
 *   - Toast notifications (success / error)
 *   - Simple progress UI updates (per-file spinner)
 *
 * What this file deliberately does NOT do:
 *   - Tool-specific logic (compress, collage, crop, etc live in their own pages)
 *   - Heavy AI/ML inference (those are tracked; current suite is canvas-based)
 *   - Network calls (everything runs in-browser; nothing leaves the device)
 *
 * Privacy: by design all processing is client-side. The header mentions this.
 */

// ---------- vendored third-party libraries --------------------------------
//
// WHY THIS FILE LOADS THEM LAZILY
// -------------------------------
// Every library lives under /js/vendor/ and is fetched on FIRST USE, not on
// page load. The tool pages are small and most visitors open exactly one
// tool; making everybody download the PDF writer (410 KB) or the HEIC
// decoder (1.3 MB) to crop a photo would be a waste of their bandwidth.
//
// The `?v=` stamp MUST match js/vendor/vendor-manifest.json. Cloudflare Pages
// overrides Cache-Control on static assets, so the query string is the only
// cache-busting mechanism - a stale stamp serves an old library forever.
// `python scripts/vendor-libs.py --verify` checks the hashes.
//
// CSP: 'self' is in script-src, so a dynamically inserted same-origin
// <script src> loads without a nonce. ('unsafe-inline' is ignored because the
// policy carries a nonce, but that only affects inline code.)
var VENDOR = {
  fflate: { file: 'fflate.min.js', version: '0.8.3', global: 'fflate' },
  jspdf: { file: 'jspdf.umd.min.js', version: '4.2.1', global: 'jspdf' },
  heic2any: { file: 'heic2any.min.js', version: '0.0.4', global: 'heic2any' },
  pica: { file: 'pica.min.js', version: '10.0.3', global: 'pica' },
  onnxruntime: { file: 'ort.wasm.min.js', version: '1.22.0', global: 'ort' },
};

var vendorPromises = {};

// The pixel worker (§2.5) is a separate file, so it needs its own cache
// stamp - the `?v=` on common.js does not bust it. Cloudflare Pages
// overrides Cache-Control on static assets, so the query string is the only
// cache-busting mechanism: a stale stamp serves the OLD worker forever.
//
// Bump this when /js/tools/pixel-worker.js changes.
// `python scripts/bump_cache_version.py --asset pixel-worker.js` does it.
var PIXEL_WORKER_VERSION = '1.0.1';

function loadVendor(lib) {
  if (vendorPromises[lib]) return vendorPromises[lib];
  vendorPromises[lib] = new Promise(function (resolve, reject) {
    var spec = VENDOR[lib];
    if (!spec) { reject(new Error('Unknown vendored library: ' + lib)); return; }
    // Already there (e.g. the page loaded it explicitly).
    if (window[spec.global]) { resolve(window[spec.global]); return; }
    var s = document.createElement('script');
    s.src = '/js/vendor/' + lib + '/' + spec.file + '?v=' + spec.version;
    s.async = true;
    s.onload = function () {
      if (window[spec.global]) resolve(window[spec.global]);
      else reject(new Error('/js/vendor/' + lib + '/' + spec.file + ' loaded but did not define ' + spec.global));
    };
    s.onerror = function () {
      reject(new Error('Could not load /js/vendor/' + lib + '/' + spec.file));
    };
    document.head.appendChild(s);
  });
  return vendorPromises[lib];
}


(function () {
  'use strict';

  // ---------- runtime copy strings -------------------------------------------
  //
  // The middleware translates the STATIC html: an element carrying
  // data-i18n="tools.copy.download.zzzzzzfd45" gets the dictionary value for
  // the page's language. It cannot translate the strings this file creates
  // AFTER the page has loaded - the per-file "Download" / "Remove" buttons,
  // the toasts - because by then the html is already served.
  //
  // So the middleware hands the "tools.copy" namespace to the client as
  // window.__WA_I18N__ (see injectRuntimeI18n in functions/_middleware.js).
  // t() reads from it and falls back to the English source string, which is
  // what an English page (and any page served without the runtime
  // dictionary) needs anyway.
  //
  // The alias table keeps the call sites readable. The keys themselves are
  // flat top-level keys in i18n/<lang>.json, in the "tools.copy" namespace
  // (the first two dotted segments decide the shard).
  var COPY = {
    download: 'tools.copy.download.zzzzzzfd45',
    remove: 'tools.copy.remove.zzzzzz0f69',
    working: 'tools.copy.working.zzzzzzc327',
    preview: 'tools.copy.preview.zzzzzz5ebe',
    noSupportedFiles: 'tools.copy.noSupportedFiles.zzzzzz19c5',
    renderEmpty: 'tools.copy.renderEmpty.zzzzzzbf0d',
    compressEmpty: 'tools.copy.compressEmpty.zzzzzz6fba',
    imageNoDimensions: 'tools.copy.imageNoDimensions.zzzzzz916e',
    invalidOutputDims: 'tools.copy.invalidOutputDims.zzzzzz0828',
    cropEmpty: 'tools.copy.cropEmpty.zzzzzzc76e',
    encodePngFailed: 'tools.copy.encodePngFailed.zzzzzz8e47',
    // added 2026-11-09
    zipFailed: 'tools.copy.zipFailed.zzzzzz4a1b',
    pdfFailed: 'tools.copy.pdfFailed.zzzzzz4b2c',
    pdfReady: 'tools.copy.pdfReady.zzzzzz4c3d',
    heicDecoding: 'tools.copy.heicDecoding.zzzzzz4d4e',
    heicDecodeFailed: 'tools.copy.heicDecodeFailed.zzzzzz4e5f',
    aiModelLoading: 'tools.copy.aiModelLoading.zzzzzz4f6a',
    aiRemoveFailed: 'tools.copy.aiRemoveFailed.zzzzzz4a7b',
    videoEncoding: 'tools.copy.videoEncoding.zzzzzz4b8c',
    videoEncodeFailed: 'tools.copy.videoEncodeFailed.zzzzzz4c9d',
    browserNoWebcodecs: 'tools.copy.browserNoWebcodecs.zzzzzz4d0e',
    cropApply: 'tools.copy.cropApply.zzzzzz4e1f',
    cropReset: 'tools.copy.cropReset.zzzzzz4f2a',
    cropCancel: 'tools.copy.cropCancel.zzzzzz4a3b',
    // seating chart (added 2026-11-09)
    seatTemplateClassic: 'tools.copy.seatTemplateClassic.zzzzzz5a01',
    seatTemplateLong: 'tools.copy.seatTemplateLong.zzzzzz5a02',
    seatTemplateIntimate: 'tools.copy.seatTemplateIntimate.zzzzzz5a03',
    seatTemplateUShape: 'tools.copy.seatTemplateUShape.zzzzzz5a04',
    seatExportPng: 'tools.copy.seatExportPng.zzzzzz5a05',
    seatPrint: 'tools.copy.seatPrint.zzzzzz5a06',
    seatDownloadPdf: 'tools.copy.seatDownloadPdf.zzzzzz5a07',
    seatChartTitle: 'tools.copy.seatChartTitle.zzzzzz5a08',
    seatSavedPng: 'tools.copy.seatSavedPng.zzzzzz5a09',
    seatSavedPdf: 'tools.copy.seatSavedPdf.zzzzzz5a0a',
    // HEIC tool (added 2026-11-09)
    heicComplete: 'tools.copy.heicComplete.zzzzzz6b01',
    noHeicFiles: 'tools.copy.noHeicFiles.zzzzzz6b02',
    heicSaving: 'tools.copy.heicSaving.zzzzzz6b03',
    heicConvertedToJpg: 'tools.copy.heicConvertedToJpg.zzzzzz6b04',
    heicTotalNow: 'tools.copy.heicTotalNow.zzzzzz6b05',
    heicZeroConverted: 'tools.copy.heicZeroConverted.zzzzzz6b06',
    heicErrored: 'tools.copy.heicErrored.zzzzzz6b07',
    // progress bar (added 2026-11-09)
    progress: 'tools.copy.progress.zzzzzz8a01',
    // MP4 export (added 2026-11-11)
    mp4Encoding: 'tools.copy.mp4Encoding.zzzzzz9a02',
    mp4Saved: 'tools.copy.mp4Saved.zzzzzz9a03',
    mp4Failed: 'tools.copy.mp4Failed.zzzzzz9a04',
    mp4Unsupported: 'tools.copy.mp4Unsupported.zzzzzz9a05',
  };

  // Replace {name} placeholders with values from `params`.
  // The runtime dictionary value may contain them too, so the substitution
  // happens on whichever string is returned - translated or English fallback.
  function interpolate(str, params) {
    if (!params || typeof str !== 'string') return str;
    return str.replace(/\{(\w+)\}/g, function (m, k) {
      return Object.prototype.hasOwnProperty.call(params, k) ? String(params[k]) : m;
    });
  }

  function t(alias, fallback, params) {
    try {
      var dict = window.__WA_I18N__;
      if (dict) {
        var key = COPY[alias] || alias;
        var v = dict[key];
        if (typeof v === 'string' && v !== '') return interpolate(v, params);
      }
    } catch (e) { /* ignore */ }
    return interpolate(fallback, params);
  }

  // ---------- format helpers ----------------------------------------------------

  function formatBytes(n) {
    if (typeof n !== 'number' || !isFinite(n) || n < 0) return '—';
    if (n < 1024) return n + ' B';
    if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
    if (n < 1024 * 1024 * 1024) return (n / 1024 / 1024).toFixed(2) + ' MB';
    return (n / 1024 / 1024 / 1024).toFixed(2) + ' GB';
  }

  function formatPercent(num) {
    if (typeof num !== 'number' || !isFinite(num)) return '—';
    const sign = num > 0 ? '−' : num < 0 ? '+' : '';
    return sign + Math.abs(num).toFixed(1) + '%';
  }

  function safeFileName(name, suffix) {
    var base = (name || 'image').replace(/\.[^.]+$/, '');
    base = base.replace(/[^a-zA-Z0-9_\-]/g, '_').slice(0, 60) || 'image';
    return suffix ? (base + suffix) : base;
  }

  // ---------- file → image loader (off-thread decode + explicit EXIF) ------
  //
  // §2.6 wants the decode off the main thread, §2.7 wants the EXIF
  // orientation to be handled EXPLICITLY. Those two pull against each
  // other, so the behaviour was measured instead of guessed
  // (scripts/verify-exif-orientation.py, Chromium, a 200x100 JPEG tagged
  // Orientation=6):
  //
  //   <img>                                   -> 100x200  (rotated)
  //   createImageBitmap(blob)                 -> 100x200  (rotated, this browser)
  //   createImageBitmap(blob, from-image)     -> 100x200  (rotated, ALWAYS)
  //
  // The <img> path has applied the EXIF orientation since Chrome 81 /
  // Safari 13.1 / Firefox 26, so the CURRENT code was already correct -
  // but createImageBitmap did not, and would have turned portrait phone
  // photos sideways. The explicit option is the only guaranteed one.
  //
  // The returned object also carries release(): an ImageBitmap holds GPU
  // memory and has to be closed, an object URL has to be revoked, and the
  // caller should not have to know which one it got.
  function fileToImage(file) {
    return new Promise(function (resolve, reject) {
      var name = (file.name || '').toLowerCase();
      var isHeic = /\.(heic|heif)$/i.test(name);

      if (typeof createImageBitmap === 'function' && !isHeic) {
        createImageBitmap(file, { imageOrientation: 'from-image' }).then(function (bitmap) {
          // The tool pages read img.naturalWidth / img.naturalHeight; an
          // ImageBitmap only has width / height. Mirror them so that no
          // tool page has to change.
          try {
            bitmap.naturalWidth = bitmap.width;
            bitmap.naturalHeight = bitmap.height;
          } catch (e) { /* ignore */ }
          resolve({
            img: bitmap,
            url: null,
            release: function () { if (bitmap.close) bitmap.close(); },
          });
        }).catch(function () {
          loadViaImageElement(file, resolve, reject);
        });
        return;
      }
      loadViaImageElement(file, resolve, reject);
    });
  }

  function loadViaImageElement(file, resolve, reject) {
    var url = URL.createObjectURL(file);
    var img = new Image();
    img.onload = function () {
      resolve({
        img: img,
        url: url,
        release: function () { URL.revokeObjectURL(url); },
      });
    };
    img.onerror = function () {
      URL.revokeObjectURL(url);
      var name = (file.name || '').toLowerCase();
      var isHeic = /\.(heic|heif)$/i.test(name);
      reject(new Error(
        isHeic
          ? 'This browser can\u2019t decode HEIC/HEIF directly. Use the HEIC \u2192 JPG tool, or open this file in Safari/Finder first to convert.'
          : 'Could not decode this file. Try a JPG, PNG, or WebP.'
      ));
    };
    img.src = url;
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
        worker = new Worker('/js/tools/pixel-worker.js?v=' + PIXEL_WORKER_VERSION);
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

  function canvasToBlob(canvas, type, quality) {
    type = type || 'image/jpeg';
    quality = typeof quality === 'number' ? quality : 0.92;
    return new Promise(function (resolve) {
      if (typeof canvas.toBlob === 'function') {
        canvas.toBlob(function (b) { resolve(b); }, type, quality);
      } else {
        // Safari < 14 fallback (should be rare in 2026 browsers)
        var dataUrl = canvas.toDataURL(type, quality);
        var bin = atob(dataUrl.split(',')[1]);
        var arr = new Uint8Array(bin.length);
        for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
        resolve(new Blob([arr], { type: type }));
      }
    });
  }

  // ---------- drag/drop + click-to-pick wiring (with keyboard a11y) -------------

  function bindDropZone(opts) {
    // opts: { dropEl, inputEl, onFiles(fileList|File[]), accept, multiple }
    var dropEl = opts.dropEl;
    var inputEl = opts.inputEl;
    var onFiles = opts.onFiles;
    var accept = opts.accept || '';
    var multiple = opts.multiple !== false;

    if (inputEl) {
      inputEl.setAttribute('accept', accept);
      if (multiple) inputEl.setAttribute('multiple', '');
      inputEl.addEventListener('change', function () {
        if (inputEl.files && inputEl.files.length) {
          onFiles(Array.prototype.slice.call(inputEl.files));
          // reset so re-selecting the same file fires change again
          inputEl.value = '';
        }
      });
    }

    if (!dropEl) return;
    dropEl.addEventListener('click', function (e) {
      // ignore clicks bubbling from the actual <input>/label inside the zone
      if (e.target === dropEl || e.target.closest('[data-no-trigger]') === null) {
        if (e.target.closest('button, a, label, input') && e.target !== dropEl) return;
        if (inputEl) inputEl.click();
      }
    });
    dropEl.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        if (inputEl) inputEl.click();
      }
    });
    dropEl.setAttribute('tabindex', '0');
    dropEl.setAttribute('role', 'button');
    dropEl.setAttribute('aria-label', dropEl.getAttribute('aria-label') || 'Drop files here or click to browse');

    ['dragenter', 'dragover'].forEach(function (ev) {
      dropEl.addEventListener(ev, function (e) {
        e.preventDefault(); e.stopPropagation();
        dropEl.classList.add('is-drag-over');
      });
    });
    ['dragleave', 'dragend'].forEach(function (ev) {
      dropEl.addEventListener(ev, function (e) {
        e.preventDefault(); e.stopPropagation();
        dropEl.classList.remove('is-drag-over');
      });
    });
    dropEl.addEventListener('drop', function (e) {
      e.preventDefault(); e.stopPropagation();
      dropEl.classList.remove('is-drag-over');
      var dt = e.dataTransfer;
      if (!dt || !dt.files || !dt.files.length) return;
      onFiles(Array.prototype.slice.call(dt.files));
    });
  }

  // ---------- file list renderer (reusable) -------------------------------------

  function renderFileList(hostEl, files, renderRow) {
    hostEl.innerHTML = '';
    files.forEach(function (f, i) {
      var row = document.createElement('div');
      row.className = 'wa-tool-file-row';
      row.setAttribute('data-index', String(i));
      hostEl.appendChild(row);
      if (typeof renderRow === 'function') renderRow(row, f, i);
    });
  }

  function updateFileRow(row, state) {
    // state: { status: 'queued'|'working'|'done'|'error', message, previewUrl, name, sizes: {orig, out}, percent, output }
    if (!row) return;
    row.className = 'wa-tool-file-row wa-tool-status-' + (state.status || 'queued');
    row.innerHTML = '';

    if (state.previewUrl) {
      var img = document.createElement('img');
      img.src = state.previewUrl;
      img.alt = state.name || 'preview';
      img.className = 'wa-tool-thumb';
      row.appendChild(img);
    } else {
      var ph = document.createElement('div');
      ph.className = 'wa-tool-thumb wa-tool-thumb-ph';
      ph.textContent = (state.status === 'working') ? '…' : t('preview', 'img');
      row.appendChild(ph);
    }

    var meta = document.createElement('div');
    meta.className = 'wa-tool-meta';
    var title = document.createElement('div');
    title.className = 'wa-tool-name';
    title.textContent = state.name || '—';
    meta.appendChild(title);

    var sub = document.createElement('div');
    sub.className = 'wa-tool-sub';
    if (state.sizes && typeof state.sizes.orig === 'number') {
      sub.textContent = 'Original: ' + formatBytes(state.sizes.orig);
      if (typeof state.sizes.out === 'number' && state.sizes.out > 0) {
        sub.textContent += '  •  Output: ' + formatBytes(state.sizes.out) +
          '  (' + formatPercent((state.sizes.orig - state.sizes.out) / state.sizes.orig * 100) + ')';
      }
    } else if (state.message) {
      sub.textContent = state.message;
    }
    meta.appendChild(sub);

    if (state.status === 'error' && state.error) {
      var err = document.createElement('div');
      err.className = 'wa-tool-err';
      err.textContent = state.error;
      meta.appendChild(err);
    }

    // Real progress instead of a spinner (§2.9). The caller sets
    // state.percent (0-100); the bar is only rendered while the row is
    // working, so a finished row never shows a stale percentage.
    if (state.status === 'working' && typeof state.percent === 'number' && isFinite(state.percent)) {
      var pct = Math.max(0, Math.min(100, Math.round(state.percent)));
      var bar = document.createElement('div');
      bar.className = 'wa-tool-progress';
      bar.setAttribute('role', 'progressbar');
      bar.setAttribute('aria-valuemin', '0');
      bar.setAttribute('aria-valuemax', '100');
      bar.setAttribute('aria-valuenow', String(pct));
      bar.setAttribute('aria-label', t('progress', 'Progress'));
      var fill = document.createElement('div');
      fill.className = 'wa-tool-progress-fill';
      fill.style.width = pct + '%';
      bar.appendChild(fill);
      var pctText = document.createElement('span');
      pctText.className = 'wa-tool-progress-text';
      pctText.textContent = pct + '%';
      meta.appendChild(bar);
      meta.appendChild(pctText);
    }

    row.appendChild(meta);

    var actions = document.createElement('div');
    actions.className = 'wa-tool-actions';
    if (state.status === 'done' && state.output) {
      var dl = document.createElement('button');
      dl.type = 'button';
      dl.className = 'btn btn-primary btn-small';
      dl.textContent = t('download', 'Download');
      dl.addEventListener('click', function () { download(state.output); });
      actions.appendChild(dl);
    } else if (state.status === 'working') {
      var sp = document.createElement('span');
      sp.className = 'wa-tool-spinner';
      sp.setAttribute('aria-label', t('working', 'Working'));
      actions.appendChild(sp);
    } else if (state.status === 'error') {
      var rm = document.createElement('button');
      rm.type = 'button';
      rm.className = 'btn btn-secondary btn-small';
      rm.textContent = t('remove', 'Remove');
      rm.addEventListener('click', function () { row.dispatchEvent(new CustomEvent('wa-row-remove', { detail: row.getAttribute('data-index'), bubbles: true })); });
      actions.appendChild(rm);
    }
    row.appendChild(actions);
  }

  // ---------- download helpers ---------------------------------------------------

  function download(blob, filename) {
    if (!blob) return;
    var name = filename || 'download';
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = name;
    document.body.appendChild(a);
    a.click();
    setTimeout(function () {
      URL.revokeObjectURL(url);
      a.remove();
    }, 1000);
  }

  // ---------- "Save all" as a real ZIP ---------------------------------------
  //
  // Until 2026-11-09 this fired one auto-download per file, 120 ms apart.
  // Browsers block or throttle multiple downloads, so the user got N loose
  // files (or one file and a permission prompt) instead of one archive.
  // It now builds a real .zip with fflate (MIT, 32 KB).
  //
  // Signature is unchanged: downloadZip(blobs, baseName) where each blob is
  // { blob: Blob, name: string }. It returns a Promise; callers that ignore
  // it still work.
  function downloadZip(blobs, baseName) {
    if (!blobs || !blobs.length) return Promise.resolve();
    return loadVendor('fflate').then(function (fflate) {
      return Promise.all(blobs.map(function (entry) {
        return entry.blob.arrayBuffer().then(function (buf) {
          return { buf: new Uint8Array(buf), entry: entry };
        });
      })).then(function (parts) {
        var files = {};
        parts.forEach(function (p, i) {
          // Flat names only: a zip entry may not contain a path separator.
          var name = p.entry.name || (baseName + '_' + (i + 1) + '.jpg');
          name = String(name).replace(/[\/\\]/g, '_');
          files[name] = p.buf;
        });
        return new Promise(function (resolve, reject) {
          fflate.zip(files, { level: 6 }, function (err, data) {
            if (err) { reject(err); return; }
            var blob = new Blob([data], { type: 'application/zip' });
            download(blob, (baseName || 'weddingai') + '.zip');
            resolve(blob);
          });
        });
      });
    }).catch(function (err) {
      toast(t('zipFailed', 'Could not build the ZIP archive') + ': ' + (err && err.message ? err.message : String(err)), 'error');
      throw err;
    });
  }

  // ---------- canvas -> PDF --------------------------------------------------
  //
  // Adds a real "Download PDF" next to the PNG export. jsPDF (MIT, 410 KB)
  // is loaded on first use. The PDF page is exactly the canvas size, so a
  // 1600x1200 seating chart becomes a 1600x1200 pt page - i.e. a print
  // layout with no scaling.
  function downloadPdf(canvas, filename, opts) {
    opts = opts || {};
    return loadVendor('jspdf').then(function (ns) {
      var Ctor = (ns && ns.jsPDF) || (window.jspdf && window.jspdf.jsPDF);
      if (!Ctor) throw new Error('jsPDF did not expose a jsPDF constructor');
      var w = canvas.width, h = canvas.height;
      var landscape = w > h;
      var pdf = new Ctor({
        orientation: landscape ? 'landscape' : 'portrait',
        unit: 'px',
        format: [w, h],
        compress: true,
      });
      var mime = opts.mime || 'image/jpeg';
      var quality = typeof opts.quality === 'number' ? opts.quality : 0.92;
      var dataUrl = canvas.toDataURL(mime, quality);
      pdf.addImage(dataUrl, mime === 'image/png' ? 'PNG' : 'JPEG', 0, 0, w, h, undefined, 'FAST');
      pdf.save(filename || 'weddingai.pdf');
      return true;
    }).catch(function (err) {
      toast(t('pdfFailed', 'Could not create the PDF') + ': ' + (err && err.message ? err.message : String(err)), 'error');
      throw err;
    });
  }

  // Multi-page PDF. `items` is an array of factories, each returning a
  // canvas (or a promise of one); they are rendered ONE AT A TIME and the
  // bitmap is released right after it goes into the PDF, because a 40-page
  // album at 2400x2400 would otherwise hold ~900 MB of canvas.
  //
  // opts.pageWidth / opts.pageHeight are the PDF page size in the pdf's
  // unit. With unit 'in' and an 8x8 inch page, a 2400 px image lands at
  // 300 DPI - i.e. actually print-ready, not a 33-inch poster.
  function downloadPdfPages(items, filename, opts) {
    opts = opts || {};
    if (!items || !items.length) return Promise.reject(new Error('No pages to export'));
    return loadVendor('jspdf').then(function (ns) {
      var Ctor = (ns && ns.jsPDF) || (window.jspdf && window.jspdf.jsPDF);
      if (!Ctor) throw new Error('jsPDF did not expose a jsPDF constructor');
      var unit = opts.unit || 'px';
      var mime = opts.mime || 'image/jpeg';
      var quality = typeof opts.quality === 'number' ? opts.quality : 0.92;
      var pdf = null;
      var pageIndex = 0;
      var chain = Promise.resolve();
      items.forEach(function (make) {
        chain = chain.then(function () {
          return Promise.resolve(make());
        }).then(function (canvas) {
          if (!canvas) return;
          var pw = opts.pageWidth || canvas.width;
          var ph = opts.pageHeight || canvas.height;
          var landscape = pw > ph;
          if (!pdf) {
            pdf = new Ctor({
              orientation: landscape ? 'landscape' : 'portrait',
              unit: unit,
              format: [pw, ph],
              compress: true,
            });
          } else {
            pdf.addPage([pw, ph], landscape ? 'landscape' : 'portrait');
          }
          var dataUrl = canvas.toDataURL(mime, quality);
          pdf.addImage(dataUrl, mime === 'image/png' ? 'PNG' : 'JPEG', 0, 0, pw, ph, undefined, 'FAST');
          pageIndex++;
          // Release the bitmap: only the compressed image stays in the PDF.
          canvas.width = 0;
          canvas.height = 0;
        });
      });
      return chain.then(function () {
        if (!pdf || pageIndex === 0) throw new Error('No pages were rendered');
        pdf.save(filename || 'weddingai.pdf');
        return true;
      });
    }).catch(function (err) {
      toast(t('pdfFailed', 'Could not create the PDF') + ': ' + (err && err.message ? err.message : String(err)), 'error');
      throw err;
    });
  }

  // ---------- HEIC decoding --------------------------------------------------
  //
  // Only Safari decodes HEIC natively; Chrome, Edge and Firefox cannot. The
  // HEIC tool used to rely on the browser's own decoder, which meant it only
  // worked in Safari. heic2any (MIT, 1.3 MB) decodes it in the browser with
  // an asm.js build of libheif - asm.js, not WebAssembly, so it needs no
  // CSP change and no 'wasm-unsafe-eval'.
  //
  // Returns a Blob (JPEG by default). Falls back to the native decoder path
  // if the library cannot handle the file.
  function decodeHeic(file, opts) {
    opts = opts || {};
    return loadVendor('heic2any').then(function (heic2any) {
      var options = {
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
    }).then(function (out) {
      // heic2any returns an array when `multiple` is true.
      if (Array.isArray(out)) {
        if (!out.length) throw new Error('HEIC decoder returned no image');
        return out[0];
      }
      if (!out) throw new Error('HEIC decoder returned no image');
      return out;
    });
  }

  // ---------- high-quality resize -------------------------------------------
  //
  // The canvas drawImage() path resamples with the browser's bilinear filter,
  // which softens a photo noticeably when it is scaled down a lot. pica
  // (MIT) does a proper multi-step resample.
  //
  // pica ships its WASM resampler INLINED in the bundle, so it needs
  // 'wasm-unsafe-eval' in the CSP (added 2026-11-09 in buildCsp() and
  // _headers). If that keyword is ever missing, pica's has_wasm() returns
  // false and it silently falls back to its plain-JS resampler - the page
  // keeps working, the quality quietly drops. We surface that in the console
  // so the failure is visible instead of invisible.
  function resizeCanvas(source, width, height, opts) {
    opts = opts || {};
    var usePica = opts.pica !== false;
    if (!usePica) return drawToCanvas(source, width, height);
    return loadVendor('pica').then(function (pica) {
      if (pica && typeof pica.has_wasm === 'function' && !pica.has_wasm()) {
        if (window.console && console.warn) {
          console.warn('[weddingai] pica has no WASM (check the CSP for ' + "'wasm-unsafe-eval'" + '); falling back to the JS resampler.');
        }
      }
      var out = document.createElement('canvas');
      out.width = width;
      out.height = height;
      return pica().resize(source, out, {
        quality: opts.quality || 3,
        alpha: opts.alpha !== false,
      }).then(function () { return out; });
    }).catch(function () {
      // pica failed for any reason - the plain canvas path always works.
      return drawToCanvas(source, width, height);
    });
  }

  function drawToCanvas(source, width, height) {
    var out = document.createElement('canvas');
    out.width = width;
    out.height = height;
    var ctx = out.getContext('2d');
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(source, 0, 0, width, height);
    return out;
  }

  // ---------- on-device AI background removal (MODNet) --------------------
  //
  // The remove-background tool used a COLOUR KEY: it sampled the backdrop
  // colour from the corners of the photo and stripped every pixel within a
  // tolerance of it. That cannot tell a wall from a wedding dress, and it
  // fails outright on a busy backdrop.
  //
  // MODNet is a real matting network (Apache-2.0, quantised ONNX, 6.3 MB)
  // and ONNX Runtime Web (MIT) runs it in the browser, so the site's
  // promise - the photo never leaves the device - still holds.
  //
  // THE COST, stated plainly: the first run downloads ~11 MB of WASM runtime
  // plus the 6.3 MB model from THIS origin. Nothing is uploaded and no third
  // party is contacted. The browser caches both.
  //
  // CSP: the runtime compiles WebAssembly, so 'wasm-unsafe-eval' has to be
  // in the policy - it is, in functions/_middleware.js buildCsp() and in
  // _headers, both since 2026-11-09.
  var MODNET_SIZE = 512;
  var MODNET_MODEL = '/js/vendor/modnet/model_quantized.onnx?v=quantized';
  var modnetSession = null;

  function removeBackgroundAi(source) {
    return loadVendor('onnxruntime').then(function (ort) {
      if (!ort || !ort.InferenceSession) {
        throw new Error('ONNX Runtime did not expose InferenceSession');
      }
      // The runtime has to find its own backend glue (.mjs) and the WASM
      // binary next to the JS - there is no CDN and no bundler here.
      ort.env.wasm.wasmPaths = '/js/vendor/onnxruntime/';
      // The site is not cross-origin isolated, so SharedArrayBuffer is not
      // available and the threaded build would fail. One thread it is.
      ort.env.wasm.numThreads = 1;
      ort.env.wasm.proxy = false;
      if (modnetSession) return modnetSession;
      return ort.InferenceSession.create(MODNET_MODEL, {
        executionProviders: ['wasm'],
        graphOptimizationLevel: 'all',
      }).then(function (session) {
        modnetSession = session;
        return session;
      });
    }).then(function (session) {
      var w = source.naturalWidth || source.width;
      var h = source.naturalHeight || source.height;
      if (!w || !h) throw new Error('Image has no dimensions. Try a different file.');

      // MODNet's reference implementation resizes to 512x512 WITHOUT keeping
      // the aspect ratio, predicts a matte, and scales the matte back up.
      var small = document.createElement('canvas');
      small.width = MODNET_SIZE;
      small.height = MODNET_SIZE;
      var sctx = small.getContext('2d', { willReadFrequently: true });
      sctx.drawImage(source, 0, 0, MODNET_SIZE, MODNET_SIZE);
      var px = sctx.getImageData(0, 0, MODNET_SIZE, MODNET_SIZE).data;

      // NCHW float32, normalised to [-1, 1] (mean 0.5, std 0.5).
      var plane = MODNET_SIZE * MODNET_SIZE;
      var input = new Float32Array(plane * 3);
      for (var p = 0, i = 0; p < plane; p++, i += 4) {
        input[p] = (px[i] / 255 - 0.5) / 0.5;
        input[p + plane] = (px[i + 1] / 255 - 0.5) / 0.5;
        input[p + plane * 2] = (px[i + 2] / 255 - 0.5) / 0.5;
      }
      var tensor = new ort.Tensor('float32', input, [1, 3, MODNET_SIZE, MODNET_SIZE]);

      return session.run({ input: tensor }).then(function (res) {
        var out = res.output || res[Object.keys(res)[0]];
        if (!out || !out.data) throw new Error('The matting model returned no result.');
        var alpha = out.data;

        var mcanvas = document.createElement('canvas');
        mcanvas.width = MODNET_SIZE;
        mcanvas.height = MODNET_SIZE;
        var mctx = mcanvas.getContext('2d');
        var mdata = mctx.createImageData(MODNET_SIZE, MODNET_SIZE);
        for (var k = 0; k < alpha.length; k++) {
          var v = alpha[k];
          if (v < 0) v = 0; else if (v > 1) v = 1;
          mdata.data[k * 4] = 255;
          mdata.data[k * 4 + 1] = 255;
          mdata.data[k * 4 + 2] = 255;
          mdata.data[k * 4 + 3] = Math.round(v * 255);
        }
        mctx.putImageData(mdata, 0, 0);

        // Keep the original pixels, take the matte as the alpha channel.
        var result = document.createElement('canvas');
        result.width = w;
        result.height = h;
        var rctx = result.getContext('2d');
        rctx.drawImage(source, 0, 0, w, h);
        rctx.globalCompositeOperation = 'destination-in';
        rctx.drawImage(mcanvas, 0, 0, w, h);
        return result;
      });
    });
  }


  // ---------- toast (very small, no deps) ---------------------------------------

  function toast(msg, kind) {
    var host = document.getElementById('wa-tool-toast-host');
    if (!host) {
      host = document.createElement('div');
      host.id = 'wa-tool-toast-host';
      host.setAttribute('aria-live', 'polite');
      host.style.cssText = 'position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:9999;display:flex;flex-direction:column;gap:8px;pointer-events:none;';
      document.body.appendChild(host);
    }
    var t = document.createElement('div');
    t.style.cssText = 'background:' + (kind === 'error' ? '#b00020' : '#222') +
      ';color:#fff;padding:10px 16px;border-radius:8px;font:600 14px/1.4 Inter,sans-serif;' +
      'box-shadow:0 8px 24px rgba(0,0,0,0.18);max-width:90vw;pointer-events:auto;opacity:0;transition:opacity .2s ease;';
    t.textContent = msg;
    host.appendChild(t);
    requestAnimationFrame(function () { t.style.opacity = '1'; });
    setTimeout(function () {
      t.style.opacity = '0';
      setTimeout(function () { t.remove(); }, 250);
    }, 3200);
  }

  // ---------- public namespace --------------------------------------------------

  window.weddingAITool = {
    version: '1.2.0',
    formatBytes: formatBytes,
    formatPercent: formatPercent,
    safeFileName: safeFileName,
    fileToImage: fileToImage,
    releaseImage: releaseImage,
    runPixelLoop: runPixelLoop,
    canvasToBlob: canvasToBlob,
    bindDropZone: bindDropZone,
    renderFileList: renderFileList,
    updateFileRow: updateFileRow,
    download: download,
    downloadZip: downloadZip,
    downloadPdf: downloadPdf,
    downloadPdfPages: downloadPdfPages,
    decodeHeic: decodeHeic,
    resizeCanvas: resizeCanvas,
    removeBackgroundAi: removeBackgroundAi,
    loadVendor: loadVendor,
    t: t,
    toast: toast,
  };
})();
