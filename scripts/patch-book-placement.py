#!/usr/bin/env python3
"""
Free placement for the wedding photo-book planner (§2.4).

WHAT WAS WRONG
---------------
The album planner had one way to put a photo on a page: click a slot, and a
window.prompt() lists the photos you could put there. That is a native dialog
with no translation, no touch support, and no way to arrange a page - you
could not swap two photos, and the crop of a photo was always dead centre.

WHAT THIS PATCH DOES
--------------------
- Drag a photo from the library onto a slot: it is placed there.
- Drag a photo from one slot onto another: the two SWAP.
- Drag inside a slot: the crop of that photo is repositioned.
- Scroll over a slot: that photo is zoomed (1x - 4x).
- A zoom slider for the selected slot, and a "Reset crop" button.

The crop is stored as a ZOOM plus a pan measured as a FRACTION of the visible
source window, not in pixels. That makes it independent of the size of the
preview and of the size of the export: the slot preview and the exported page
crop identically because they run the same drawing code over the same numbers.

NO LIBRARY, for the same reason as the collage (§2.3): the interaction is
constrained, the drawing is already canvas, and a scene-graph library would
have to take over the caption, the cover page and the export path.

The old click-to-assign prompt stays as the fallback for a click without a
drag - so nothing that worked before stops working.

Usage
-----
    python scripts/patch-book-placement.py --dry-run
    python scripts/patch-book-placement.py

The JS goes into the ENGLISH page only; the localized copies get it from
scripts/propagate-tool-js.py. The markup and the CSS go into all 11 pages.
"""
import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUG = "wedding-photo-book-planner"
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

MARKER = "WA_BOOK_FREE_PLACEMENT_V1"


# ---------------------------------------------------------------- markup ----

MARKUP_ANCHOR = '<div class="pb-slots" id="editor-slots"></div>'

BUTTON_RE_CURRENT = re.compile(
    r'<button type="button" class="pb-btn primary" id="download-current-btn"[^>]*>.*?</button>',
    re.DOTALL)

BUTTON_RE_ALL = re.compile(
    r'<button type="button" class="pb-btn" id="download-all-btn"[^>]*>.*?</button>',
    re.DOTALL)

BUTTON_CURRENT_NEW = ('<button type="button" class="pb-btn primary" id="download-current-btn" '
                      'data-i18n="tools.wedding-photo-book-planner.button_text.download_page_png.7y2c5v8n">'
                      'Download this page (300 DPI PNG)</button>')

BUTTON_ALL_NEW = ('<button type="button" class="pb-btn" id="download-all-btn" '
                  'data-i18n="tools.wedding-photo-book-planner.button_text.download_all_pdf.3m8k1w6r">'
                  'Download all pages (print-ready PDF)</button>')

MARKUP_NEW = MARKUP_ANCHOR + """
                    <div class="pb-placement" id="book-placement" hidden>
                        <p class="pb-placement-hint" id="book-placement-hint" data-i18n="tools.wedding-photo-book-planner.small_text.free_placement_hint.6b3n8q5x">Drag a photo from the library onto a slot, or drag one slot onto another to swap them. Drag inside a slot to reposition the crop, and scroll over a slot to zoom it.</p>
                        <div class="pb-placement-row">
                            <label class="pb-placement-label" for="slot-zoom" data-i18n="tools.wedding-photo-book-planner.label_text.zoom_selected.9k2v7m4w">Zoom selected photo</label>
                            <input type="range" id="slot-zoom" min="100" max="400" step="5" value="100" disabled>
                            <span class="pb-placement-value" id="slot-zoom-val">100%</span>
                            <button type="button" class="pb-btn small" id="reset-page-crop-btn" data-i18n="tools.wedding-photo-book-planner.button_text.reset_crop.4t6y1u8s">Reset crop</button>
                        </div>
                    </div>"""

CSS_ANCHOR = "        .pb-slot img { max-width: 100%; max-height: 60px; object-fit: cover; border-radius: 2px; }"

CSS_NEW = CSS_ANCHOR + """

        /* §2.4 free placement. */
        .pb-placement { margin-top: 0.6rem; border-top: 1px solid var(--color-border); padding-top: 0.5rem; }
        .pb-placement[hidden] { display: none; }
        .pb-placement-hint { color: var(--color-text-light); font-size: 0.75rem; margin: 0 0 0.45rem; line-height: 1.5; }
        .pb-placement-row { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
        .pb-placement-label { font-weight: 600; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.03em; color: var(--color-text-light); }
        .pb-placement-row input[type="range"] { flex: 1 1 140px; min-width: 110px; }
        .pb-placement-value { font-size: 0.75rem; min-width: 3.2em; font-variant-numeric: tabular-nums; }
        .pb-slot { touch-action: none; }
        .pb-slot canvas { display: block; max-width: 100%; height: auto; border-radius: 2px; background: #eee; }
        .pb-slot.drop-target { outline: 2px solid var(--color-primary); outline-offset: 1px; }
        .pb-slot.selected { box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.5); }
        .pb-photo-item { touch-action: pan-y; }
        .pb-drag-ghost { position: fixed; z-index: 9999; pointer-events: none; width: 56px; height: 56px; border-radius: 6px; object-fit: cover; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35); border: 2px solid var(--color-primary); opacity: 0.92; transform: translate(-50%, -50%); }"""

CSS_CANVAS_OLD = "        .pb-page-canvas { width: 100%; aspect-ratio: 1; background: #fafafa; border-radius: 4px; display: block; }"

CSS_CANVAS_NEW = "        .pb-page-canvas { width: 100%; height: auto; background: #fafafa; border-radius: 4px; display: block; }"

# The comparison paragraph said the planner fills the grid "in upload order".
# That is still the default, but the user can now arrange the page, and the
# album really does export as print-ready 300 DPI pages.
PARA_OLD = ("WeddingAI.video’s planner auto-fills the grid page by page in upload order, places captions in 11 "
            "languages, Export print-ready 300 DPI pages for any print shop.")

PARA_NEW = ("WeddingAI.video’s planner auto-fills the grid page by page — and then lets you drag the photos into "
            "the slots you want, crop each one and zoom it — places captions in 11 languages, and exports the whole "
            "album as print-ready 300 DPI pages for any print shop.")


# -------------------------------------------------------------------- js ----

JS_STATE_OLD = """  var DEFAULT_LAYOUT = '1photo';
  var state = loadState() || defaultState();"""

JS_STATE_NEW = """  var DEFAULT_LAYOUT = '1photo';
  var state = loadState() || defaultState();

  // ---------- §2.4 free placement -------------------------------------
  // %s
  var bookDrag = null;
  var selectedSlot = -1;
  var suppressNextClick = false;""" % MARKER


JS_DOM_OLD = """  var templatePick = document.querySelectorAll('.pb-tem"""

JS_DOM_NEW = """  var bookPlacement = document.getElementById('book-placement');
  var slotZoomInput = document.getElementById('slot-zoom');
  var slotZoomVal = document.getElementById('slot-zoom-val');
  var resetCropBtn = document.getElementById('reset-page-crop-btn');
  var templatePick = document.querySelectorAll('.pb-tem"""


JS_COVER_OLD = """  function drawCover(ctx, img, x, y, w, h) {
    var imgAspect = img.width / img.height;
    var boxAspect = w / h;
    var dx, dy, dw, dh;
    if (imgAspect > boxAspect) {
      dh = h; dw = h * imgAspect;
      dx = x - (dw - w) / 2; dy = y;
    } else {
      dw = w; dh = w / imgAspect;
      dx = x; dy = y - (dh - h) / 2;
    }
    ctx.save();
    ctx.beginPath();
    ctx.rect(x, y, w, h);
    ctx.clip();
    ctx.drawImage(img, dx, dy, dw, dh);
    ctx.restore();
  }"""

JS_COVER_NEW = """  // Cover-crop drawImage: fill the (x,y,w,h) box by cropping the source.
  // §2.4 - the crop can be zoomed (zoom) and slid (panU/panV). The pan is a
  // FRACTION of the visible source window, not a number of pixels, so the
  // same values produce the same crop in the small slot preview and in the
  // full-size export.
  function drawCover(ctx, img, x, y, w, h, zoom, panU, panV) {
    var iw = img.width || img.naturalWidth;
    var ih = img.height || img.naturalHeight;
    if (!iw || !ih) return;
    var z = zoom || 1;
    var scale = Math.max(w / iw, h / ih) * z;
    var sw = w / scale;
    var sh = h / scale;
    var sx = (iw - sw) / 2 + (panU || 0) * sw;
    var sy = (ih - sh) / 2 + (panV || 0) * sh;
    // The crop window slides INSIDE the photo; it never runs off it.
    if (sw < iw) sx = Math.min(iw - sw, Math.max(0, sx));
    if (sh < ih) sy = Math.min(ih - sh, Math.max(0, sy));
    ctx.save();
    ctx.beginPath();
    ctx.rect(x, y, w, h);
    ctx.clip();
    ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h);
    ctx.restore();
  }"""


JS_GRID_OLD = """      html += '<div class="pb-page-thumb' + activeClass + '" data-page-idx="' + idx + '">'
            + '<canvas class="pb-page-canvas" data-canvas-idx="' + idx + '" width="200" height="200"></canvas>'"""

JS_GRID_NEW = """      html += '<div class="pb-page-thumb' + activeClass + '" data-page-idx="' + idx + '">'
            + '<canvas class="pb-page-canvas" data-canvas-idx="' + idx + '" width="' + thumbW + '" height="' + thumbH + '"></canvas>'"""

JS_GRID_PRE_OLD = """  function renderPagesGrid() {
    var html = '';
    state.pages_data.forEach(function (p, idx) {"""

JS_GRID_PRE_NEW = """  function renderPagesGrid() {
    var html = '';
    // The thumbnail keeps the page's aspect ratio, so a crop that looks
    // right in the thumbnail is the crop the export produces.
    var pageSize = SIZES[state.size] || SIZES['8x8'];
    var thumbW = 200;
    var thumbH = Math.max(40, Math.round(thumbW * pageSize.h / pageSize.w));
    state.pages_data.forEach(function (p, idx) {"""


JS_PAGE_DRAW_OLD = """      if (photo) {
        var img = new Image();
        img.onload = function () {
          drawCover(ctx, img, sp.x, sp.y, sp.w, sp.h);
        };
        img.src = photo.url;
      } else {"""

JS_PAGE_DRAW_NEW = """      if (photo) {
        var img = new Image();
        var adj = slotAdjust(page, i);
        img.onload = function () {
          drawCover(ctx, img, sp.x, sp.y, sp.w, sp.h, adj.zoom, adj.panU, adj.panV);
        };
        img.src = photo.url;
      } else {"""


JS_EXPORT_DRAW_OLD = """        if (photo) {
          var img = new Image();
          img.onload = function () {
            drawCover(ctx, img, sp.x, sp.y, sp.w, sp.h);
            pending--;"""

JS_EXPORT_DRAW_NEW = """        if (photo) {
          var img = new Image();
          var adj = slotAdjust(p, i);
          img.onload = function () {
            drawCover(ctx, img, sp.x, sp.y, sp.w, sp.h, adj.zoom, adj.panU, adj.panV);
            pending--;"""


JS_EDITOR_OLD = """    var html = '';
    for (var i = 0; i < layout.slots; i++) {
      var pid = (p.slots || [])[i];
      var photo = pid ? state.photos.find(function (x) { return x.id === pid; }) : null;
      var hasClass = photo ? ' has-photo' : '';
      var imgTag = photo ? '<img src="' + photo.url + '" alt="">' : '';
      var lbl = photo ? escapeHtml(photo.name.slice(0, 20)) : ('Slot ' + (i+1));
      html += '<div class="pb-slot' + hasClass + '" data-slot-idx="' + i + '">' + imgTag + '<span>' + lbl + '</span></div>';
    }
    editorSlots.innerHTML = html;
    // Click to assign
    editorSlots.querySelectorAll('.pb-slot').forEach(function (el) {
      el.addEventListener('click', function () {
        var sIdx = parseInt(el.getAttribute('data-slot-idx'), 10);
        assignPhotoToSlot(sIdx);
      });
    });
  }"""

JS_EDITOR_NEW = """    // §2.4 - the slot preview is a CANVAS, drawn with the same function the
    // export uses, so what the user arranges is what the file contains.
    var pageSize = SIZES[state.size] || SIZES['8x8'];
    var slotPositions = computeSlotPositions(layout.slots, pageSize.w, pageSize.h);
    var html = '';
    for (var i = 0; i < layout.slots; i++) {
      var pid = (p.slots || [])[i];
      var photo = pid ? state.photos.find(function (x) { return x.id === pid; }) : null;
      var hasClass = photo ? ' has-photo' : '';
      var sp = slotPositions[i];
      var cw = 200;
      var ch = Math.max(40, Math.round(cw * sp.h / sp.w));
      var imgTag = photo ? '<canvas class="pb-slot-canvas" data-slot-canvas="' + i + '" width="' + cw + '" height="' + ch + '"></canvas>' : '';
      var lbl = photo ? escapeHtml(photo.name.slice(0, 20)) : ('Slot ' + (i+1));
      html += '<div class="pb-slot' + hasClass + '" data-slot-idx="' + i + '">' + imgTag + '<span>' + lbl + '</span></div>';
    }
    editorSlots.innerHTML = html;
    // Draw the previews.
    for (var k = 0; k < layout.slots; k++) {
      var cv = editorSlots.querySelector('canvas[data-slot-canvas="' + k + '"]');
      var pid2 = (p.slots || [])[k];
      var ph2 = pid2 ? state.photos.find(function (x) { return x.id === pid2; }) : null;
      if (cv && ph2) drawSlotPreview(cv, ph2, p, k);
    }
    // Click to assign (kept as the fallback for a click without a drag)
    editorSlots.querySelectorAll('.pb-slot').forEach(function (el) {
      el.addEventListener('click', function () {
        if (suppressNextClick) { suppressNextClick = false; return; }
        var sIdx = parseInt(el.getAttribute('data-slot-idx'), 10);
        assignPhotoToSlot(sIdx);
      });
    });
    updateSlotZoomUi();
  }"""


JS_EDITOR_COVER_OLD = """    if (layout.slots === 0) {
      editorSlots.innerHTML = '<div class="pb-photo-empty">Cover page — uses the title, date, and tagline.</div>';
      return;
    }"""

JS_EDITOR_COVER_NEW = """    if (layout.slots === 0) {
      editorSlots.innerHTML = '<div class="pb-photo-empty">Cover page — uses the title, date, and tagline.</div>';
      if (bookPlacement) bookPlacement.hidden = true;
      return;
    }
    if (bookPlacement) bookPlacement.hidden = false;"""


JS_FREE_PLACEMENT = """  // ---------- §2.4 free placement -----------------------------------------

  function slotAdjust(page, i) {
    if (!page.slotAdjust) page.slotAdjust = [];
    if (!page.slotAdjust[i]) page.slotAdjust[i] = { zoom: 1, panU: 0, panV: 0 };
    return page.slotAdjust[i];
  }

  function activePage() {
    return currentPageIdx >= 0 ? state.pages_data[currentPageIdx] : null;
  }

  function photoInSlot(page, i) {
    var pid = (page.slots || [])[i];
    if (!pid) return null;
    return state.photos.find(function (x) { return x.id === pid; }) || null;
  }

  function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }

  function drawSlotPreview(canvas, photo, page, slotIdx) {
    var ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    var img = new Image();
    img.onload = function () {
      var adj = slotAdjust(page, slotIdx);
      drawCover(ctx, img, 0, 0, canvas.width, canvas.height, adj.zoom, adj.panU, adj.panV);
    };
    img.src = photo.url;
  }

  function redrawSlotPreview(slotIdx) {
    var page = activePage();
    if (!page) return;
    var cv = editorSlots.querySelector('canvas[data-slot-canvas="' + slotIdx + '"]');
    var photo = photoInSlot(page, slotIdx);
    if (cv && photo) drawSlotPreview(cv, photo, page, slotIdx);
  }

  function updateSlotZoomUi() {
    if (!slotZoomInput || !slotZoomVal) return;
    var page = activePage();
    var photo = page && selectedSlot >= 0 ? photoInSlot(page, selectedSlot) : null;
    if (!photo) {
      slotZoomInput.disabled = true;
      slotZoomVal.textContent = '100%';
      return;
    }
    var adj = slotAdjust(page, selectedSlot);
    slotZoomInput.disabled = false;
    slotZoomInput.value = Math.round(adj.zoom * 100);
    slotZoomVal.textContent = Math.round(adj.zoom * 100) + '%';
  }

  function selectSlot(i) {
    selectedSlot = i;
    if (!editorSlots) return;
    Array.prototype.forEach.call(editorSlots.querySelectorAll('.pb-slot'), function (el) {
      el.classList.toggle('selected', parseInt(el.getAttribute('data-slot-idx'), 10) === i);
    });
    updateSlotZoomUi();
  }

  function makeGhost(src) {
    var g = document.createElement('img');
    g.className = 'pb-drag-ghost';
    g.alt = '';
    g.src = src;
    document.body.appendChild(g);
    return g;
  }

  function onBookPointerDown(ev) {
    if (currentPageIdx < 0) return;
    if (ev.button !== undefined && ev.button !== 0) return;
    var t = ev.target;
    if (!t || !t.closest) return;
    if (t.closest('[data-del-photo]')) return;
    var slotEl = t.closest('.pb-slot');
    var libEl = t.closest('.pb-photo-item');
    if (!slotEl && !libEl) return;
    var page = activePage();
    if (!page) return;
    bookDrag = {
      kind: slotEl ? 'slot' : 'library',
      slotIdx: slotEl ? parseInt(slotEl.getAttribute('data-slot-idx'), 10) : -1,
      photoId: libEl ? libEl.getAttribute('data-photo-id') : null,
      startX: ev.clientX,
      startY: ev.clientY,
      active: false,
      mode: slotEl ? 'pan' : 'assign',
      ghost: null,
      targetEl: null,
      panU0: 0,
      panV0: 0
    };
    if (bookDrag.kind === 'slot') {
      var adj = slotAdjust(page, bookDrag.slotIdx);
      bookDrag.panU0 = adj.panU;
      bookDrag.panV0 = adj.panV;
      selectSlot(bookDrag.slotIdx);
    }
    document.addEventListener('pointermove', onBookPointerMove, { passive: false });
    document.addEventListener('pointerup', onBookPointerUp);
    document.addEventListener('pointercancel', onBookPointerUp);
  }

  function onBookPointerMove(ev) {
    if (!bookDrag) return;
    if (!bookDrag.active) {
      var dx = ev.clientX - bookDrag.startX;
      var dy = ev.clientY - bookDrag.startY;
      if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return;
      bookDrag.active = true;
      if (bookDrag.kind === 'library') {
        var libPhoto = state.photos.find(function (x) { return x.id === bookDrag.photoId; });
        if (libPhoto) bookDrag.ghost = makeGhost(libPhoto.url);
      }
    }
    ev.preventDefault();
    var page = activePage();
    if (!page) return;

    var el = document.elementFromPoint(ev.clientX, ev.clientY);
    var slotEl = el && el.closest ? el.closest('.pb-slot') : null;
    var targetIdx = slotEl ? parseInt(slotEl.getAttribute('data-slot-idx'), 10) : -1;

    if (bookDrag.kind === 'slot' && targetIdx >= 0 && targetIdx !== bookDrag.slotIdx) {
      // Reaching another slot turns the drag into a move. The nudge the
      // drag made on the way is undone - a move is not a pan.
      if (bookDrag.mode !== 'move') {
        bookDrag.mode = 'move';
        var adj0 = slotAdjust(page, bookDrag.slotIdx);
        adj0.panU = bookDrag.panU0;
        adj0.panV = bookDrag.panV0;
        var moved = photoInSlot(page, bookDrag.slotIdx);
        if (moved && !bookDrag.ghost) bookDrag.ghost = makeGhost(moved.url);
        redrawSlotPreview(bookDrag.slotIdx);
      }
      bookDrag.dstIdx = targetIdx;
    }

    if (bookDrag.kind === 'slot' && bookDrag.mode === 'pan') {
      var slotEl0 = editorSlots.querySelector('.pb-slot[data-slot-idx="' + bookDrag.slotIdx + '"]');
      var canvas = slotEl0 ? slotEl0.querySelector('canvas') : null;
      if (canvas) {
        var rect = canvas.getBoundingClientRect();
        if (rect.width) {
          var scale = canvas.width / rect.width;
          var dCx = (ev.clientX - bookDrag.startX) * scale;
          var dCy = (ev.clientY - bookDrag.startY) * scale;
          var adj = slotAdjust(page, bookDrag.slotIdx);
          // The pan is a fraction of the visible window, so the drag moves
          // the photo by the same amount whatever the preview's size is.
          adj.panU = clamp(bookDrag.panU0 - dCx / canvas.width, -0.5, 0.5);
          adj.panV = clamp(bookDrag.panV0 - dCy / canvas.height, -0.5, 0.5);
          redrawSlotPreview(bookDrag.slotIdx);
        }
      }
    }

    if (bookDrag.ghost) {
      bookDrag.ghost.style.left = ev.clientX + 'px';
      bookDrag.ghost.style.top = ev.clientY + 'px';
    }

    if (bookDrag.targetEl !== slotEl) {
      if (bookDrag.targetEl) bookDrag.targetEl.classList.remove('drop-target');
      if (slotEl) slotEl.classList.add('drop-target');
      bookDrag.targetEl = slotEl;
    }
  }

  function onBookPointerUp(ev) {
    document.removeEventListener('pointermove', onBookPointerMove);
    document.removeEventListener('pointerup', onBookPointerUp);
    document.removeEventListener('pointercancel', onBookPointerUp);
    if (!bookDrag) return;
    var d = bookDrag;
    bookDrag = null;
    if (d.ghost && d.ghost.parentNode) d.ghost.parentNode.removeChild(d.ghost);
    if (d.targetEl) d.targetEl.classList.remove('drop-target');
    if (!d.active) return;
    // A drag is not a click: the click-to-assign prompt must not open.
    suppressNextClick = true;
    setTimeout(function () { suppressNextClick = false; }, 0);

    var page = activePage();
    if (!page) return;
    var el = document.elementFromPoint(ev.clientX, ev.clientY);
    var slotEl = el && el.closest ? el.closest('.pb-slot') : null;
    if (!slotEl) { saveState(); renderAll(); renderEditorSlots(); return; }
    var targetIdx = parseInt(slotEl.getAttribute('data-slot-idx'), 10);

    if (d.kind === 'library') {
      if (!page.slots) page.slots = [];
      page.slots[targetIdx] = d.photoId;
      // The crop belonged to the photo that was there; the new one starts
      // at the default crop.
      var adj = slotAdjust(page, targetIdx);
      adj.zoom = 1; adj.panU = 0; adj.panV = 0;
      selectSlot(targetIdx);
    } else if (d.mode === 'move' && targetIdx !== d.slotIdx) {
      if (!page.slots) page.slots = [];
      var tmp = page.slots[d.slotIdx];
      page.slots[d.slotIdx] = page.slots[targetIdx];
      page.slots[targetIdx] = tmp;
      // The crop belongs to the PHOTO, not to the slot, so it travels along.
      if (!page.slotAdjust) page.slotAdjust = [];
      var a = page.slotAdjust[d.slotIdx];
      var b = page.slotAdjust[targetIdx];
      page.slotAdjust[d.slotIdx] = b || { zoom: 1, panU: 0, panV: 0 };
      page.slotAdjust[targetIdx] = a || { zoom: 1, panU: 0, panV: 0 };
      selectSlot(targetIdx);
    }
    saveState();
    renderAll();
    renderEditorSlots();
  }

  function onBookWheel(ev) {
    if (currentPageIdx < 0) return;
    var t = ev.target;
    var slotEl = t && t.closest ? t.closest('.pb-slot') : null;
    if (!slotEl) return;
    var idx = parseInt(slotEl.getAttribute('data-slot-idx'), 10);
    var page = activePage();
    if (!page) return;
    if (!photoInSlot(page, idx)) return;
    ev.preventDefault();
    var adj = slotAdjust(page, idx);
    var f = ev.deltaY < 0 ? 1.12 : 1 / 1.12;
    adj.zoom = clamp(Math.round(adj.zoom * f * 100) / 100, 1, 4);
    selectSlot(idx);
    redrawSlotPreview(idx);
    renderPagesGrid();
    saveState();
  }

  function resetPageCrops() {
    var page = activePage();
    if (!page) return;
    page.slotAdjust = [];
    for (var i = 0; i < (page.slots || []).length; i++) {
      slotAdjust(page, i);
    }
    saveState();
    renderAll();
    renderEditorSlots();
  }

  document.addEventListener('pointerdown', onBookPointerDown);
  document.addEventListener('wheel', onBookWheel, { passive: false });

  // An <img> is natively draggable, and the browser's image drag SWALLOWS
  // the pointermove events - the drag then dies after the first move and
  // nothing is dropped. draggable="false" on the thumbnail handles the
  // image; this handles the text selection and anything else inside a
  // slot or a library row.
  document.addEventListener('dragstart', function (ev) {
    var t = ev.target;
    if (t && t.closest && (t.closest('.pb-photo-item') || t.closest('.pb-slot'))) {
      ev.preventDefault();
    }
  });
  if (slotZoomInput) {
    slotZoomInput.addEventListener('input', function () {
      var page = activePage();
      if (!page || selectedSlot < 0) return;
      var adj = slotAdjust(page, selectedSlot);
      adj.zoom = parseInt(slotZoomInput.value, 10) / 100;
      slotZoomVal.textContent = slotZoomInput.value + '%';
      redrawSlotPreview(selectedSlot);
      renderPagesGrid();
      saveState();
    });
  }
  if (resetCropBtn) resetCropBtn.addEventListener('click', resetPageCrops);

"""


JS_EXPORTPAGE_OLD = """  function exportPage(idx) {
    var size = SIZES[state.size];
    var p = state.pages_data[idx];
    var c = document.createElement('canvas');
    c.width = size.w; c.height = size.h;
    var ctx = c.getContext('2d');
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, size.w, size.h);
    var layout = LAYOUTS[p.layout] || LAYOUTS[DEFAULT_LAYOUT];
    if (layout.slots === 0) {
      // cover
      ctx.fillStyle = '#2c2c2c';
      var titleSize = fitSize(ctx, state.title || 'Wedding', size.w * 0.18, 'Georgia, serif', size.w * 0.85, size.w * 0.05);
      ctx.font = '700 ' + titleSize + 'px Georgia, serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(state.title || 'Wedding', size.w/2, size.h * 0.42);
      var dateSize = titleSize * 0.4;
      ctx.font = '300 ' + dateSize + 'px Georgia, serif';
      ctx.fillStyle = '#7a7a7a';
      ctx.fillText(state.date || '', size.w/2, size.h * 0.55);
      if (state.tag) {
        ctx.fillStyle = '#d4af37';
        ctx.font = '300 ' + (dateSize * 0.7) + 'px Georgia, serif';
        ctx.fillText(state.tag, size.w/2, size.h * 0.62);
      }
    } else {
      var slotPositions = computeSlotPositions(layout.slots, size.w, size.h);
      var pending = layout.slots;
      slotPositions.forEach(function (sp, i) {
        var pid = (p.slots || [])[i];
        var photo = pid ? state.photos.find(function (x) { return x.id === pid; }) : null;
        if (photo) {
          var img = new Image();
          var adj = slotAdjust(p, i);
          img.onload = function () {
            drawCover(ctx, img, sp.x, sp.y, sp.w, sp.h, adj.zoom, adj.panU, adj.panV);
            pending--;
            if (pending === 0) finalizePageExport(c, idx);
          };
          img.onerror = function () { pending--; if (pending === 0) finalizePageExport(c, idx); };
          img.src = photo.url;
        } else {
          ctx.fillStyle = '#fafafa';
          ctx.fillRect(sp.x, sp.y, sp.w, sp.h);
          pending--;
          if (pending === 0) finalizePageExport(c, idx);
        }
      });
      if (pending === 0) finalizePageExport(c, idx);
    }
    if (p.caption) {
      ctx.fillStyle = '#2c2c2c';
      ctx.font = '300 ' + (size.w * 0.025) + 'px Georgia, serif';
      ctx.textAlign = 'center';
      ctx.fillText(p.caption, size.w/2, size.h - size.w * 0.04);
    }
    if (layout.slots === 0) finalizePageExport(c, idx);
  }"""

JS_EXPORTPAGE_NEW = """  function drawCoverPage(ctx, size) {
    ctx.fillStyle = '#2c2c2c';
    var titleSize = fitSize(ctx, state.title || 'Wedding', size.w * 0.18, 'Georgia, serif', size.w * 0.85, size.w * 0.05);
    ctx.font = '700 ' + titleSize + 'px Georgia, serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(state.title || 'Wedding', size.w/2, size.h * 0.42);
    var dateSize = titleSize * 0.4;
    ctx.font = '300 ' + dateSize + 'px Georgia, serif';
    ctx.fillStyle = '#7a7a7a';
    ctx.fillText(state.date || '', size.w/2, size.h * 0.55);
    if (state.tag) {
      ctx.fillStyle = '#d4af37';
      ctx.font = '300 ' + (dateSize * 0.7) + 'px Georgia, serif';
      ctx.fillText(state.tag, size.w/2, size.h * 0.62);
    }
  }

  function drawPageCaption(ctx, size, p) {
    if (!p.caption) return;
    ctx.fillStyle = '#2c2c2c';
    ctx.font = '300 ' + (size.w * 0.025) + 'px Georgia, serif';
    ctx.textAlign = 'center';
    ctx.fillText(p.caption, size.w/2, size.h - size.w * 0.04);
  }

  // Render one page to a canvas. Resolves once every photo is drawn.
  //
  // The caption is drawn BEFORE the canvas is handed over. The old code
  // started the export first and drew the caption afterwards, which only
  // worked because toBlob() happens to be asynchronous - and a page whose
  // slots were all empty exported WITHOUT its caption.
  function renderPageCanvas(idx) {
    return new Promise(function (resolve) {
      var size = SIZES[state.size];
      var p = state.pages_data[idx];
      var c = document.createElement('canvas');
      c.width = size.w; c.height = size.h;
      var ctx = c.getContext('2d');
      ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, size.w, size.h);
      var layout = LAYOUTS[p.layout] || LAYOUTS[DEFAULT_LAYOUT];
      if (layout.slots === 0) {
        drawCoverPage(ctx, size);
        drawPageCaption(ctx, size, p);
        resolve(c);
        return;
      }
      var slotPositions = computeSlotPositions(layout.slots, size.w, size.h);
      var pending = layout.slots;
      var settled = false;
      function finish() {
        if (settled) return;
        settled = true;
        drawPageCaption(ctx, size, p);
        resolve(c);
      }
      slotPositions.forEach(function (sp, i) {
        var pid = (p.slots || [])[i];
        var photo = pid ? state.photos.find(function (x) { return x.id === pid; }) : null;
        if (photo) {
          var img = new Image();
          var adj = slotAdjust(p, i);
          img.onload = function () {
            drawCover(ctx, img, sp.x, sp.y, sp.w, sp.h, adj.zoom, adj.panU, adj.panV);
            pending--;
            if (pending <= 0) finish();
          };
          img.onerror = function () { pending--; if (pending <= 0) finish(); };
          img.src = photo.url;
        } else {
          ctx.fillStyle = '#fafafa';
          ctx.fillRect(sp.x, sp.y, sp.w, sp.h);
          pending--;
          if (pending <= 0) finish();
        }
      });
    });
  }

  function exportPage(idx) {
    renderPageCanvas(idx).then(function (canvas) {
      finalizePageExport(canvas, idx);
    });
  }"""


JS_EXPORTALL_OLD = """  function exportAll() {
    if (!window.confirm('Download all ' + state.pages_data.length + ' pages? Browsers may queue multiple downloads.')) return;
    state.pages_data.forEach(function (p, idx) {
      setTimeout(function () { exportPage(idx); }, idx * 400);
    });
  }"""

JS_EXPORTALL_NEW = """  // The PDF page is the BOOK size in inches, so a 2400 px page lands at
  // 300 DPI - a real print file, not a 33-inch poster.
  //
  // The page used to promise a print-ready PDF and exported N separate PNGs
  // instead ("Browsers may queue multiple downloads"). This is the PDF.
  function exportAlbumPdf() {
    if (!window.weddingAITool || !window.weddingAITool.downloadPdfPages) {
      if (window.weddingAITool && window.weddingAITool.toast) {
        window.weddingAITool.toast('PDF export is not available in this browser.', 'error');
      }
      return;
    }
    var size = SIZES[state.size];
    var inches = { w: size.w / 300, h: size.h / 300 };
    var makers = state.pages_data.map(function (p, i) {
      return function () { return renderPageCanvas(i); };
    });
    var btn = downloadAllBtn;
    var label = btn ? btn.textContent : '';
    if (btn) { btn.disabled = true; btn.textContent = 'Building PDF...'; }
    window.weddingAITool.downloadPdfPages(makers, 'wedding-photo-book.pdf', {
      unit: 'in',
      pageWidth: inches.w,
      pageHeight: inches.h,
      mime: 'image/jpeg',
      quality: 0.92
    }).then(function () {
      if (window.weddingAITool.toast) {
        window.weddingAITool.toast('PDF ready - ' + state.pages_data.length + ' pages', 'success');
      }
    }).catch(function () {
      // downloadPdfPages already raised the localized error toast.
    }).then(function () {
      if (btn) { btn.disabled = false; btn.textContent = label; }
    });
  }"""


JS_EXPORTALL_HANDLER_OLD = """  downloadAllBtn.addEventListener('click', function () {
    exportAll();
  });"""

JS_EXPORTALL_HANDLER_NEW = """  downloadAllBtn.addEventListener('click', function () {
    exportAlbumPdf();
  });"""


JS_EXPORTPAGE_RE = re.compile(r"  function exportPage\(idx\) \{.*?\n  \}\n", re.DOTALL)

JS_EXPORTALL_RE = re.compile(r"  function exportAll\(\) \{.*?\n  \}\n", re.DOTALL)


JS_PHOTOLIST_OLD = """      html += '<div class="pb-photo-item" data-photo-id="' + p.id + '">'
            + '<img class="pb-photo-thumb" src="' + p.url + '" alt="">'"""

JS_PHOTOLIST_NEW = """      html += '<div class="pb-photo-item" data-photo-id="' + p.id + '">'
            + '<img class="pb-photo-thumb" src="' + p.url + '" alt="" draggable="false">'"""


JS_REPLACEMENTS = [
    (JS_STATE_OLD, JS_STATE_NEW),
    (JS_DOM_OLD, JS_DOM_NEW),
    (JS_COVER_OLD, JS_COVER_NEW),
    (JS_GRID_PRE_OLD, JS_GRID_PRE_NEW),
    (JS_GRID_OLD, JS_GRID_NEW),
    (JS_PAGE_DRAW_OLD, JS_PAGE_DRAW_NEW),
    (JS_EDITOR_COVER_OLD, JS_EDITOR_COVER_NEW),
    (JS_EDITOR_OLD, JS_EDITOR_NEW),
    (JS_EXPORTALL_HANDLER_OLD, JS_EXPORTALL_HANDLER_NEW),
    (JS_PHOTOLIST_OLD, JS_PHOTOLIST_NEW),
]

# The two export functions are replaced by pattern: they are long blocks
# whose exact text is easy to get wrong, and the pattern cannot match twice.
JS_REGEX_REPLACEMENTS = [
    (JS_EXPORTPAGE_RE, JS_EXPORTPAGE_NEW + "\n"),
    (JS_EXPORTALL_RE, JS_EXPORTALL_NEW + "\n"),
]


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmpwrite")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def patch_html(text: str):
    """Markup + CSS, for every language."""
    changes = 0
    if 'id="book-placement"' not in text:
        for anchor in (MARKUP_ANCHOR, CSS_ANCHOR):
            if text.count(anchor) != 1:
                raise SystemExit("html anchor is not unique:\n" + anchor[:120])
        text = text.replace(MARKUP_ANCHOR, MARKUP_NEW)
        text = text.replace(CSS_ANCHOR, CSS_NEW)
        changes += 2
    else:
        print("    html: already patched")
    # The export buttons. The localized pages carry their OWN translated
    # label inline, so the button is matched by id, not by its text, and
    # every page gets the English source plus a data-i18n binding.
    text, k1 = BUTTON_RE_CURRENT.subn(lambda m: BUTTON_CURRENT_NEW, text, count=1)
    text, k2 = BUTTON_RE_ALL.subn(lambda m: BUTTON_ALL_NEW, text, count=1)
    if k1 != 1 or k2 != 1:
        raise SystemExit("the export buttons were not found (current=%d all=%d)" % (k1, k2))
    changes += 2
    # The page thumbnail was forced square, so an A4 page was previewed in
    # the wrong shape.
    if CSS_CANVAS_OLD in text:
        text = text.replace(CSS_CANVAS_OLD, CSS_CANVAS_NEW)
        changes += 1
    # The comparison paragraph.
    if PARA_OLD in text:
        text = text.replace(PARA_OLD, PARA_NEW)
        changes += 1
    return text, changes


def patch_js(text: str):
    """The behaviour script, English source only."""
    if MARKER in text:
        print("    js: already patched")
        return text, 0
    n = 0
    for old, new in JS_REPLACEMENTS:
        if text.count(old) != 1:
            raise SystemExit("js anchor is not unique:\n" + old[:200])
        text = text.replace(old, new)
        n += 1
    for pattern, new in JS_REGEX_REPLACEMENTS:
        text, k = pattern.subn(lambda m: new, text, count=1)
        if k != 1:
            raise SystemExit("js pattern did not match:\n" + pattern.pattern)
        n += 1
    anchor = "  // --- export"
    if text.count(anchor) != 1:
        raise SystemExit("export anchor is not unique")
    text = text.replace(anchor, JS_FREE_PLACEMENT + anchor)
    n += 1
    return text, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for lang in LANGS:
        p = (ROOT / "tools" / SLUG / "index.html" if lang == "en"
             else ROOT / lang / "tools" / SLUG / "index.html")
        if not p.exists():
            print("  %-3s MISSING %s" % (lang, p))
            continue
        text = p.read_text(encoding="utf-8")
        before = text
        text, html_n = patch_html(text)
        js_n = 0
        if lang == "en":
            text, js_n = patch_js(text)
        if text != before and not args.dry_run:
            write_atomic(p, text)
        print("  %-3s html=%d js=%d" % (lang, html_n, js_n))

    print()
    if args.dry_run:
        print("dry run - nothing written")
        return 0
    print("now run: python scripts/propagate-tool-js.py --tools %s" % SLUG)
    return 0


if __name__ == "__main__":
    sys.exit(main())
