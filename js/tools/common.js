/*!
 * WeddingAI Free Tools — common.js (v1.0.0)
 * Shared utilities for the /tools/* suite (wedding-photo processing).
 * Loaded as a deferred <script src="/js/tools/common.js?v=1.0.0"> on every tool page.
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

(function () {
  'use strict';

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

  // ---------- file → image loader (with HEIC fallback notice) -------------------

  function fileToImage(file) {
    return new Promise(function (resolve, reject) {
      var url = URL.createObjectURL(file);
      var img = new Image();
      img.onload = function () { resolve({ img: img, url: url, file: file }); };
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
      ph.textContent = (state.status === 'working') ? '…' : 'img';
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

    row.appendChild(meta);

    var actions = document.createElement('div');
    actions.className = 'wa-tool-actions';
    if (state.status === 'done' && state.output) {
      var dl = document.createElement('button');
      dl.type = 'button';
      dl.className = 'btn btn-primary btn-small';
      dl.textContent = 'Download';
      dl.addEventListener('click', function () { download(state.output); });
      actions.appendChild(dl);
    } else if (state.status === 'working') {
      var sp = document.createElement('span');
      sp.className = 'wa-tool-spinner';
      sp.setAttribute('aria-label', 'Working');
      actions.appendChild(sp);
    } else if (state.status === 'error') {
      var rm = document.createElement('button');
      rm.type = 'button';
      rm.className = 'btn btn-secondary btn-small';
      rm.textContent = 'Remove';
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

  function downloadZip(blobs, baseName) {
    // Minimal "save all" — if a real zip lib isn't loaded, fall back to auto-downloads.
    // Avoids pulling in JSZip just for a one-line save.
    blobs.forEach(function (entry, i) {
      setTimeout(function () { download(entry.blob, entry.name || (baseName + '_' + (i + 1) + '.jpg')); }, i * 120);
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
    version: '1.0.0',
    formatBytes: formatBytes,
    formatPercent: formatPercent,
    safeFileName: safeFileName,
    fileToImage: fileToImage,
    canvasToBlob: canvasToBlob,
    bindDropZone: bindDropZone,
    renderFileList: renderFileList,
    updateFileRow: updateFileRow,
    download: download,
    downloadZip: downloadZip,
    toast: toast,
  };
})();
