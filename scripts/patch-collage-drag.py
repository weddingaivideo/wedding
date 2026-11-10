#!/usr/bin/env python3
"""
Give the wedding-photo-collage tool free placement (§2.3).

WHAT WAS WRONG
---------------
Six fixed grids, auto-placed. The photos went where the layout put them and
the user could not change a thing - not the order, not the crop inside a
cell, not the zoom of a single photo. The page even said so, proudly:

    "Most collage makers require you to manually drag each photo into a grid
     cell. WeddingAI.video fills the grid for you - no dragging"

That sentence is the claim/implementation mismatch this whole pass is about.
After this patch the sentence is true in a better way: the grid IS filled for
you, AND you can drag.

WHAT THIS PATCH DOES
--------------------
- Click a cell to select it.
- Drag a photo onto another cell: the two photos SWAP.
- Drag inside a cell: the photo's crop is repositioned.
- Scroll over the selected cell: that photo zooms (1x - 4x).
- A zoom slider and a "Reset layout" button next to the preview.

WHY NO LIBRARY
--------------
The audit suggested fabric (292 KB) or konva (193 KB). This does not need
either:

- The interaction is CONSTRAINED - a grid of cells, one photo per cell, a
  swap, a pan and a zoom. It is not a free-form scene graph, so most of what
  those libraries exist for is unused.
- The export IS the preview canvas: the PNG is canvasToBlob(previewCanvas)
  and the PDF is downloadPdf(previewCanvas). With konva the caption, the
  background and the empty cells would all have to move into the scene
  graph, and the stage would have to be blitted back onto previewCanvas for
  the export. That is a rewrite of drawCollage() with a real chance of
  breaking the caption or the PDF.
- The site's own rule is that a library has to earn its bytes. This one does
  not.

The state is kept in CANVAS pixels, not display pixels, so the arrangement the
user makes is exactly the arrangement that gets exported.

Usage
-----
    python scripts/patch-collage-drag.py --dry-run
    python scripts/patch-collage-drag.py

The JS goes into the ENGLISH page only; the localized copies get it from
scripts/propagate-tool-js.py. The markup and the CSS go into all 11 pages.
"""
import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUG = "wedding-photo-collage"
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

MARKER = "WA_COLLAGE_FREE_PLACEMENT_V1"


# ---------------------------------------------------------------- markup ----

MARKUP_ANCHOR = '<canvas id="preview-canvas" hidden></canvas>'

MARKUP_NEW = '<canvas id="preview-canvas" hidden style="touch-action:none"></canvas>' + """
                    <div class="wa-collage-edit" id="collage-edit" hidden>
                        <p class="wa-collage-edit-hint" id="collage-edit-hint" data-i18n="tools.wedding-photo-collage.small_text.free_placement_hint.7q4v2m8x">Click a photo to select it. Drag it onto another cell to swap the two, drag inside a cell to reposition the crop, and scroll over the selected photo to zoom it.</p>
                        <div class="wa-collage-edit-row">
                            <label class="wa-collage-edit-label" for="cell-zoom" data-i18n="tools.wedding-photo-collage.label_text.zoom_selected.4n8k6p1w">Zoom selected photo</label>
                            <input type="range" id="cell-zoom" min="100" max="400" step="5" value="100" disabled>
                            <span class="wa-collage-edit-value" id="cell-zoom-val">100%</span>
                            <button type="button" class="btn btn-secondary btn-small" id="reset-layout-btn" data-i18n="tools.wedding-photo-collage.button_text.reset_layout.2r9t5y7u">Reset layout</button>
                        </div>
                    </div>"""

CSS_ANCHOR = "        .wa-collage-preview-empty { color: var(--color-text-light); text-align: center; padding: var(--spacing-xl) var(--spacing-md); font-size: 0.9375rem; }"

CSS_NEW = CSS_ANCHOR + """

        /* §2.3 free placement. */
        .wa-collage-edit { margin-top: var(--spacing-sm); border-top: 1px solid var(--color-border); padding-top: var(--spacing-sm); }
        .wa-collage-edit[hidden] { display: none; }
        .wa-collage-edit-hint { color: var(--color-text-light); font-size: 0.875rem; margin: 0 0 var(--spacing-sm); }
        .wa-collage-edit-row { display: flex; align-items: center; gap: var(--spacing-sm); flex-wrap: wrap; }
        .wa-collage-edit-label { font-weight: 600; font-size: 0.875rem; }
        .wa-collage-edit-row input[type="range"] { flex: 1 1 160px; min-width: 120px; }
        .wa-collage-edit-value { font-size: 0.875rem; min-width: 3.5em; font-variant-numeric: tabular-nums; }"""


# The comparison paragraph claimed "no dragging". After this patch the user
# CAN drag, so the sentence has to change - a claim that contradicts the
# tool is the exact defect class this pass is about.
PARA_OLD = ("WeddingAI.video fills the grid for you — no dragging — and lays the photos "
            "out in 6 ready-made layouts (2×2, 2×3, 3×3, 3×4, horizontal strip, vertical "
            "strip). Same collage also doubles as a chapter cover in the AI wedding video "
            "— in print or on screen, your photos stay organized.")

PARA_NEW = ("WeddingAI.video fills the grid for you in 6 ready-made layouts (2×2, 2×3, "
            "3×3, 3×4, horizontal strip, vertical strip) — and you can still drag: drop a "
            "photo onto another cell to swap the two, drag inside a cell to reposition the "
            "crop, and zoom one photo without touching the others. The same collage also "
            "doubles as a chapter cover in the AI wedding video — in print or on screen, "
            "your photos stay organized.")


# -------------------------------------------------------------------- js ----

JS_STATE_OLD = """      var files = []; // { name, inputFile, img (HTMLImageElement|null), previewUrl, status, error, sizes:{orig,out} }
      var lastBlob = null;
      var lastOutputName = 'wedding-collage.png';"""

JS_STATE_NEW = """      var files = []; // { name, inputFile, img (HTMLImageElement|null), previewUrl, status, error, sizes:{orig,out} }
      var lastBlob = null;
      var lastOutputName = 'wedding-collage.png';

      // ---------- §2.3 free placement -------------------------------------
      // %s
      //
      // The collage used to be six fixed grids, auto-placed: the photos went
      // where the layout put them and the user could not change the order,
      // the crop inside a cell, or the zoom of one photo.
      //
      // The state is kept in CANVAS pixels, not display pixels. The preview
      // canvas IS the export canvas (the PNG is canvasToBlob(previewCanvas),
      // the PDF is downloadPdf(previewCanvas)), so the arrangement the user
      // makes is exactly the arrangement that gets exported.
      var cellOrder = null;    // cell index -> photo index
      var photoState = [];     // photo index -> { zoom, panX, panY }
      var lastCells = [];      // the cells of the current render, canvas px
      var lastBuild = null;    // the arguments of the current render
      var selectedCell = -1;
      var collageDrag = null;
      var encodeTimer = null;
      var outputDirty = false;""" % MARKER


JS_COVER_OLD = """      // Cover-crop drawImage: fill the (dx,dy,dw,dh) box by cropping the source symmetrically.
      function drawCover(ctx, img, dx, dy, dw, dh) {
        var iw = img.naturalWidth, ih = img.naturalHeight;
        if (!iw || !ih) return;
        var scale = Math.max(dw / iw, dh / ih);
        var sw = dw / scale;
        var sh = dh / scale;
        var sx = (iw - sw) / 2;
        var sy = (ih - sh) / 2;
        ctx.drawImage(img, sx, sy, sw, sh, dx, dy, dw, dh);
      }"""

JS_COVER_NEW = """      // Cover-crop drawImage: fill the (dx,dy,dw,dh) box by cropping the source.
      // §2.3 - the crop window can be slid (panX/panY) and scaled (zoom).
      // The window never runs off the photo: it slides INSIDE the image.
      function drawCover(ctx, img, dx, dy, dw, dh, zoom, panX, panY) {
        var iw = img.naturalWidth, ih = img.naturalHeight;
        if (!iw || !ih) return;
        var z = zoom || 1;
        var scale = Math.max(dw / iw, dh / ih) * z;
        var sw = dw / scale;
        var sh = dh / scale;
        var sx = (iw - sw) / 2 + (panX || 0);
        var sy = (ih - sh) / 2 + (panY || 0);
        if (sw < iw) sx = Math.min(iw - sw, Math.max(0, sx));
        if (sh < ih) sy = Math.min(ih - sh, Math.max(0, sy));
        ctx.drawImage(img, sx, sy, sw, sh, dx, dy, dw, dh);
      }"""


JS_DRAW_OLD = """        var cells = computeCells(canvas.width, canvas.height, padding, layout.rows, layout.cols);
        var used = Math.min(images.length, cells.length);
        for (var i = 0; i < used; i++) {
          drawCover(ctx, images[i], cells[i].x, cells[i].y, cells[i].w, cells[i].h);
        }"""

JS_DRAW_NEW = """        var cells = computeCells(canvas.width, canvas.height, padding, layout.rows, layout.cols);
        lastCells = cells;
        // The order the photos sit in. A layout with a different number of
        // cells starts from the default order again.
        if (!cellOrder || cellOrder.length !== cells.length) {
          cellOrder = [];
          for (var q = 0; q < cells.length; q++) cellOrder.push(q);
        }
        var used = Math.min(images.length, cells.length);
        for (var i = 0; i < used; i++) {
          var photoIdx = cellOrder[i];
          var st = photoState[photoIdx] || { zoom: 1, panX: 0, panY: 0 };
          drawCover(ctx, images[photoIdx], cells[i].x, cells[i].y, cells[i].w, cells[i].h,
                    st.zoom, st.panX, st.panY);
        }"""


JS_RUN_OLD = """          await ensureFontLoaded(captionFontEl.value);

          drawCollage(
            previewCanvas,
            images,
            key,
            aspectEl.value,
            parseInt(paddingEl.value, 10),
            bgEl.value,
            (captionEl.value || '').trim(),
            captionFontEl.value
          );

          previewCanvas.hidden = false;
          previewEmpty.hidden = true;

          // Output PNG. PNG is lossless and preserves the typography exactly.
          var blob = await window.weddingAITool.canvasToBlob(previewCanvas, 'image/png');
          if (!blob || blob.size === 0) throw new Error('Could not encode PNG output.');
          lastBlob = blob;
          var layoutSlug = key.replace(/[^a-z0-9]+/gi, '-').toLowerCase();
          var aspectSlug = aspectEl.value.replace(':', 'x');
          lastOutputName = 'wedding-collage-' + layoutSlug + '-' + aspectSlug + '.png';

          summaryEl.hidden = false;
          summaryEl.innerHTML =
            '<div><strong>' + used + '</strong> photos used</div>' +
            '<div><strong>Layout:</strong> ' + layout.count + ' cells · ' + aspectEl.value + '</div>' +
            '<div><strong>Output size:</strong> ' + previewCanvas.width + ' × ' + previewCanvas.height + ' px · ' +
              window.weddingAITool.formatBytes(blob.size) + ' (PNG)</div>' +
            (errCount ? '<div style="color:#b00020"><strong>' + errCount + '</strong> skipped (could not decode).</div>' : '');

          window.weddingAITool.toast('Collage built. Click Download PNG to save.');"""

JS_RUN_NEW = """          await ensureFontLoaded(captionFontEl.value);

          lastBuild = {
            images: images,
            key: key,
            aspect: aspectEl.value,
            padding: parseInt(paddingEl.value, 10),
            bg: bgEl.value,
            caption: (captionEl.value || '').trim(),
            captionFont: captionFontEl.value,
            used: used,
            errCount: errCount
          };
          // A rebuild keeps the arrangement the user made - only a layout
          // with a different number of cells resets it.
          renderCollage();

          previewCanvas.hidden = false;
          previewEmpty.hidden = true;
          editPanel.hidden = false;

          // Output PNG. PNG is lossless and preserves the typography exactly.
          await encodeOutput();
          var layoutSlug = key.replace(/[^a-z0-9]+/gi, '-').toLowerCase();
          var aspectSlug = aspectEl.value.replace(':', 'x');
          lastOutputName = 'wedding-collage-' + layoutSlug + '-' + aspectSlug + '.png';

          renderSummary();

          window.weddingAITool.toast('Collage built. Click Download PNG to save.');"""


JS_DOWNLOAD_OLD = """      function downloadCollage() {
        if (!lastBlob) return;
        window.weddingAITool.download(lastBlob, lastOutputName);
        window.weddingAITool.toast('Saving ' + lastOutputName + '…');
      }"""

JS_DOWNLOAD_NEW = """      async function downloadCollage() {
        // §2.3 - the PNG is a snapshot of the canvas. If the user rearranged
        // the collage since the last encode, the snapshot is stale, so it is
        // re-encoded first. Otherwise the download would not match the
        // preview.
        if (outputDirty) {
          try {
            await encodeOutput();
            renderSummary();
          } catch (err) {
            window.weddingAITool.toast((err && err.message) ? err.message : 'Could not encode PNG output.', 'error');
            return;
          }
        }
        if (!lastBlob) return;
        window.weddingAITool.download(lastBlob, lastOutputName);
        window.weddingAITool.toast('Saving ' + lastOutputName + '…');
      }"""


JS_CLEAR_OLD = """        files = [];
        lastBlob = null;
        lastOutputName = 'wedding-collage.png';
        summaryEl.hidden = true;
        previewCanvas.hidden = true;
        previewEmpty.hidden = false;"""

JS_CLEAR_NEW = """        files = [];
        lastBlob = null;
        lastOutputName = 'wedding-collage.png';
        summaryEl.hidden = true;
        previewCanvas.hidden = true;
        previewEmpty.hidden = false;
        // §2.3 - a cleared tool has no arrangement to keep.
        cellOrder = null;
        photoState = [];
        lastCells = [];
        lastBuild = null;
        selectedCell = -1;
        collageDrag = null;
        outputDirty = false;
        if (editPanel) editPanel.hidden = true;"""


# The free-placement block. Inserted before the wiring section.
JS_FREE_PLACEMENT = """      // ---------- §2.3 free placement -----------------------------------------

      function renderCollage() {
        if (!lastBuild) return;
        drawCollage(
          previewCanvas,
          lastBuild.images,
          lastBuild.key,
          lastBuild.aspect,
          lastBuild.padding,
          lastBuild.bg,
          lastBuild.caption,
          lastBuild.captionFont
        );
        drawOverlay();
      }

      async function encodeOutput() {
        var blob = await window.weddingAITool.canvasToBlob(previewCanvas, 'image/png');
        if (!blob || blob.size === 0) throw new Error('Could not encode PNG output.');
        lastBlob = blob;
        outputDirty = false;
        return blob;
      }

      function renderSummary() {
        if (!lastBuild || !lastBlob) return;
        var layout = LAYOUTS[lastBuild.key] || LAYOUTS['grid-2x2'];
        summaryEl.hidden = false;
        summaryEl.innerHTML =
          '<div><strong>' + lastBuild.used + '</strong> photos used</div>' +
          '<div><strong>Layout:</strong> ' + layout.count + ' cells · ' + lastBuild.aspect + '</div>' +
          '<div><strong>Output size:</strong> ' + previewCanvas.width + ' × ' + previewCanvas.height + ' px · ' +
            window.weddingAITool.formatBytes(lastBlob.size) + ' (PNG)</div>' +
          (lastBuild.errCount ? '<div style="color:#b00020"><strong>' + lastBuild.errCount + '</strong> skipped (could not decode).</div>' : '');
      }

      function scheduleEncode() {
        outputDirty = true;
        if (encodeTimer) clearTimeout(encodeTimer);
        encodeTimer = setTimeout(function () {
          encodeTimer = null;
          encodeOutput().then(renderSummary).catch(function () { /* nothing to report */ });
        }, 400);
      }

      function stateFor(photoIdx) {
        if (!photoState[photoIdx]) photoState[photoIdx] = { zoom: 1, panX: 0, panY: 0 };
        return photoState[photoIdx];
      }

      function collagePoint(ev) {
        var rect = previewCanvas.getBoundingClientRect();
        if (!rect.width || !rect.height) return null;
        return {
          x: (ev.clientX - rect.left) * (previewCanvas.width / rect.width),
          y: (ev.clientY - rect.top) * (previewCanvas.height / rect.height)
        };
      }

      function cellIndexAt(p) {
        for (var i = 0; i < lastCells.length; i++) {
          var c = lastCells[i];
          if (p.x >= c.x && p.x <= c.x + c.w && p.y >= c.y && p.y <= c.y + c.h) return i;
        }
        return -1;
      }

      function updateZoomUi() {
        if (!zoomInput || !zoomVal) return;
        var st = selectedCell >= 0 ? photoState[cellOrder[selectedCell]] : null;
        if (!st) {
          zoomInput.disabled = true;
          zoomVal.textContent = '100%';
          return;
        }
        zoomInput.disabled = false;
        zoomInput.value = Math.round(st.zoom * 100);
        zoomVal.textContent = Math.round(st.zoom * 100) + '%';
      }

      function selectCell(i) {
        selectedCell = i;
        updateZoomUi();
        renderCollage();
      }

      // The selection outline and the photo that follows the pointer.
      function drawOverlay() {
        var ctx = previewCanvas.getContext('2d');
        if (!ctx) return;
        var lw = Math.max(3, Math.round(previewCanvas.width / 400));
        if (selectedCell >= 0 && lastCells[selectedCell]) {
          var c = lastCells[selectedCell];
          ctx.save();
          ctx.strokeStyle = '#D4AF37';
          ctx.lineWidth = lw;
          ctx.setLineDash([Math.round(previewCanvas.width / 120), Math.round(previewCanvas.width / 120)]);
          ctx.strokeRect(c.x + lw, c.y + lw, c.w - lw * 2, c.h - lw * 2);
          ctx.restore();
        }
        if (collageDrag && collageDrag.mode === 'move' && collageDrag.ghost) {
          var g = collageDrag.ghost;
          ctx.save();
          ctx.globalAlpha = 0.65;
          drawCover(ctx, g.img, g.x, g.y, g.w, g.h, g.zoom, g.panX, g.panY);
          ctx.restore();
          if (collageDrag.dstCell >= 0 && lastCells[collageDrag.dstCell]) {
            var t = lastCells[collageDrag.dstCell];
            ctx.save();
            ctx.strokeStyle = '#2C5F5D';
            ctx.lineWidth = lw;
            ctx.strokeRect(t.x + lw, t.y + lw, t.w - lw * 2, t.h - lw * 2);
            ctx.restore();
          }
        }
      }

      // Keep the crop window inside the photo.
      function clampPan(pan, imgSize, winSize) {
        var maxOff = Math.max(0, (imgSize - winSize) / 2);
        return Math.min(maxOff, Math.max(-maxOff, pan));
      }

      function onCollagePointerDown(ev) {
        if (!lastCells.length || !lastBuild) return;
        var p = collagePoint(ev);
        if (!p) return;
        var idx = cellIndexAt(p);
        if (idx < 0) return;
        selectedCell = idx;
        updateZoomUi();
        var photoIdx = cellOrder[idx];
        var st = stateFor(photoIdx);
        var cell = lastCells[idx];
        var img = lastBuild.images[photoIdx];
        var scale = Math.max(cell.w / img.naturalWidth, cell.h / img.naturalHeight) * st.zoom;
        collageDrag = {
          srcCell: idx,
          photoIdx: photoIdx,
          startX: p.x,
          startY: p.y,
          panX: st.panX,
          panY: st.panY,
          scale: scale,
          mode: 'pan',
          dstCell: idx,
          img: img,
          cell: cell,
          ghost: null
        };
        if (previewCanvas.setPointerCapture) {
          try { previewCanvas.setPointerCapture(ev.pointerId); } catch (e) { /* ignore */ }
        }
        ev.preventDefault();
      }

      function onCollagePointerMove(ev) {
        if (!collageDrag) return;
        var p = collagePoint(ev);
        if (!p) return;
        var dst = cellIndexAt(p);
        if (dst >= 0 && dst !== collageDrag.srcCell) {
          // Leaving the source cell turns the drag into a move: the two
          // photos swap when the pointer is released. The flip only happens
          // over ANOTHER cell - drifting over the gap between cells is not
          // an intent to move the photo.
          collageDrag.mode = 'move';
          collageDrag.dstCell = dst;
          // The drag started as a pan, so the photo may already have been
          // nudged. A move is not a pan: the nudge is undone, or the photo
          // would arrive at the new cell shifted.
          var st0 = stateFor(collageDrag.photoIdx);
          st0.panX = collageDrag.panX;
          st0.panY = collageDrag.panY;
        }
        if (collageDrag.mode === 'pan') {
          var st = stateFor(collageDrag.photoIdx);
          var img = collageDrag.img;
          var cell = collageDrag.cell;
          var winW = cell.w / collageDrag.scale;
          var winH = cell.h / collageDrag.scale;
          // Dragging the photo right shows more of the left of the photo,
          // so the crop window moves the other way.
          st.panX = clampPan(collageDrag.panX - (p.x - collageDrag.startX) / collageDrag.scale,
                             img.naturalWidth, winW);
          st.panY = clampPan(collageDrag.panY - (p.y - collageDrag.startY) / collageDrag.scale,
                             img.naturalHeight, winH);
          collageDrag.ghost = null;
        } else {
          var st2 = stateFor(collageDrag.photoIdx);
          var c = collageDrag.cell;
          collageDrag.ghost = {
            img: collageDrag.img,
            x: p.x - c.w / 2,
            y: p.y - c.h / 2,
            w: c.w,
            h: c.h,
            zoom: st2.zoom,
            panX: st2.panX,
            panY: st2.panY
          };
        }
        renderCollage();
      }

      function onCollagePointerUp(ev) {
        if (!collageDrag) return;
        var d = collageDrag;
        collageDrag = null;
        if (previewCanvas.releasePointerCapture && ev.pointerId !== undefined) {
          try { previewCanvas.releasePointerCapture(ev.pointerId); } catch (e) { /* ignore */ }
        }
        if (d.mode === 'move' && d.dstCell >= 0 && d.dstCell !== d.srcCell) {
          var tmp = cellOrder[d.srcCell];
          cellOrder[d.srcCell] = cellOrder[d.dstCell];
          cellOrder[d.dstCell] = tmp;
          // The selection follows the photo that was dragged.
          selectedCell = d.dstCell;
          updateZoomUi();
        }
        renderCollage();
        scheduleEncode();
      }

      function onCollageWheel(ev) {
        if (!lastCells.length || !lastBuild || selectedCell < 0) return;
        var p = collagePoint(ev);
        if (!p) return;
        // Only the SELECTED cell reacts, so scrolling the page with the
        // pointer over the canvas is not hijacked.
        if (cellIndexAt(p) !== selectedCell) return;
        ev.preventDefault();
        var st = stateFor(cellOrder[selectedCell]);
        var factor = ev.deltaY < 0 ? 1.12 : 1 / 1.12;
        st.zoom = Math.min(4, Math.max(1, Math.round(st.zoom * factor * 100) / 100));
        updateZoomUi();
        renderCollage();
        scheduleEncode();
      }

      function resetArrangement() {
        cellOrder = null;
        photoState = [];
        selectedCell = -1;
        updateZoomUi();
        renderCollage();
        scheduleEncode();
      }

"""


JS_WIRING_OLD = """      paddingEl.addEventListener('input', function () { paddingVal.textContent = paddingEl.value; });
      runBtn.addEventListener('click', runBuild);
      downloadBtn.addEventListener('click', downloadCollage);
      downloadPdfBtn.addEventListener('click', downloadCollagePdf);
      clearBtn.addEventListener('click', clearAll);"""

JS_WIRING_NEW = """      paddingEl.addEventListener('input', function () { paddingVal.textContent = paddingEl.value; });
      runBtn.addEventListener('click', runBuild);
      downloadBtn.addEventListener('click', downloadCollage);
      downloadPdfBtn.addEventListener('click', downloadCollagePdf);
      clearBtn.addEventListener('click', clearAll);

      // §2.3 free placement.
      previewCanvas.addEventListener('pointerdown', onCollagePointerDown);
      previewCanvas.addEventListener('pointermove', onCollagePointerMove);
      previewCanvas.addEventListener('pointerup', onCollagePointerUp);
      previewCanvas.addEventListener('pointercancel', onCollagePointerUp);
      previewCanvas.addEventListener('wheel', onCollageWheel, { passive: false });
      if (zoomInput) {
        zoomInput.addEventListener('input', function () {
          if (selectedCell < 0) return;
          var st = stateFor(cellOrder[selectedCell]);
          st.zoom = parseInt(zoomInput.value, 10) / 100;
          zoomVal.textContent = zoomInput.value + '%';
          renderCollage();
          scheduleEncode();
        });
      }
      if (resetLayoutBtn) resetLayoutBtn.addEventListener('click', resetArrangement);"""


JS_ROWREMOVE_OLD = """        files.splice(idx, 1);
        refreshUI();
      });"""

JS_ROWREMOVE_NEW = """        files.splice(idx, 1);
        // §2.3 - removing a photo renumbers the others, so the arrangement
        // (which is keyed by photo index) cannot be trusted any more.
        cellOrder = null;
        photoState = [];
        selectedCell = -1;
        updateZoomUi();
        refreshUI();
      });"""


JS_DOM_OLD = """      var previewEmpty = document.getElementById('preview-empty');
      var previewCanvas = document.getElementById('preview-canvas');"""

JS_DOM_NEW = """      var previewEmpty = document.getElementById('preview-empty');
      var previewCanvas = document.getElementById('preview-canvas');
      var editPanel = document.getElementById('collage-edit');
      var zoomInput = document.getElementById('cell-zoom');
      var zoomVal = document.getElementById('cell-zoom-val');
      var resetLayoutBtn = document.getElementById('reset-layout-btn');"""


JS_REPLACEMENTS = [
    (JS_DOM_OLD, JS_DOM_NEW),
    (JS_STATE_OLD, JS_STATE_NEW),
    (JS_COVER_OLD, JS_COVER_NEW),
    (JS_DRAW_OLD, JS_DRAW_NEW),
    (JS_RUN_OLD, JS_RUN_NEW),
    (JS_DOWNLOAD_OLD, JS_DOWNLOAD_NEW),
    (JS_CLEAR_OLD, JS_CLEAR_NEW),
    (JS_ROWREMOVE_OLD, JS_ROWREMOVE_NEW),
    (JS_WIRING_OLD, JS_WIRING_NEW),
]


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmpwrite")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def patch_html(text: str, dry: bool):
    """Markup + CSS, for every language.

    The HTML marker is the element id, NOT the JS marker: the localized
    copies get the JS from propagate-tool-js.py, so the JS marker only
    appears there later. Without a separate marker the markup would be
    inserted twice if the patch ran again before the propagation.
    """
    changes = 0
    if 'id="collage-edit"' not in text:
        if text.count(MARKUP_ANCHOR) != 1:
            raise SystemExit("markup anchor is not unique")
        if text.count(CSS_ANCHOR) != 1:
            raise SystemExit("css anchor is not unique")
        text = text.replace(MARKUP_ANCHOR, MARKUP_NEW)
        text = text.replace(CSS_ANCHOR, CSS_NEW)
        changes += 2
    else:
        print("    html: already patched")
    # The "no dragging" sentence has to go, in every language's page.
    if PARA_OLD in text:
        text = text.replace(PARA_OLD, PARA_NEW)
        changes += 1
    return text, changes


def patch_js(text: str, dry: bool):
    """The behaviour script, English source only."""
    if MARKER in text:
        print("    js: already patched")
        return text, 0
    n = 0
    for old, new in JS_REPLACEMENTS:
        if text.count(old) != 1:
            raise SystemExit("js anchor is not unique:\n" + old[:160])
        text = text.replace(old, new)
        n += 1
    # The free-placement block goes in front of the wiring section.
    anchor = "      // ---------- wiring --------------------------------------------------------"
    if text.count(anchor) != 1:
        raise SystemExit("wiring anchor is not unique")
    text = text.replace(anchor, JS_FREE_PLACEMENT + anchor)
    n += 1
    return text, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for lang in LANGS:
        # The English source lives at tools/<slug>/, the copies under
        # <lang>/tools/<slug>/.
        p = (ROOT / "tools" / SLUG / "index.html" if lang == "en"
             else ROOT / lang / "tools" / SLUG / "index.html")
        if not p.exists():
            print("  %-3s MISSING %s" % (lang, p))
            continue
        text = p.read_text(encoding="utf-8")
        before = text
        text, html_n = patch_html(text, args.dry_run)
        js_n = 0
        if lang == "en":
            text, js_n = patch_js(text, args.dry_run)
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
