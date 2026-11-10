#!/usr/bin/env python3
"""
Make the preview and the export draw the same thing (§2.15).

WHAT THIS DOES
--------------
The audit behind §2.15 proposed a DOM->PNG renderer (`modern-screenshot`)
so that "the HTML/CSS is the single source of truth". Checking the four
tools it named showed that the premise only holds for two of them:

  * `save-the-date-maker`, `wedding-invitation-maker` and
    `wedding-video-invitation-maker` already render their preview INTO the
    same canvas they export - the preview IS the export, WYSIWYG holds.
  * `wedding-photo-book-planner` drew the page thumbnail and the exported
    page with TWO different functions: the cover was drawn twice, the
    caption was drawn twice, and an empty slot was a bordered box labelled
    "Slot 3" in the thumbnail but a plain grey box in the export.
  * `wedding-seating-chart-maker` previews the floor plan as DOM (it has
    to: the visitor clicks a seat to assign a guest) and exports a canvas
    drawn by a second implementation - which had drifted: a 6 px seat with
    a grey border on #f5f5f5 versus a 4 px seat with a warm border on
    #f5f0ea, a different font, and no "N/M seated" line under the tables.

So instead of a DOM rasteriser, this patch removes the duplication:

  * THE ALBUM: the thumbnail calls the SAME `drawCoverPage()` and
    `drawPageCaption()` the export calls, and the same `drawEmptySlot()`.
    One renderer, two sizes - and because every measurement in those
    helpers is a fraction of the page size, the thumbnail is the export at
    1/12 scale, not a lookalike.

  * THE SEATING CHART: one `CHART` object holds every visual value. The
    preview writes them into the DOM as inline styles and the canvas draws
    them, so the two cannot disagree.

WHY NOT modern-screenshot
-------------------------
The seating chart's preview has to stay DOM - it is interactive. Rasterising
it would also lose the print chrome (title, date, legend) that only makes
sense on the exported sheet, and it would make the export depend on the
browser's foreignObject support. Zero bytes is the right price here.

Usage
-----
    python scripts/patch-render-parity.py            # apply
    python scripts/patch-render-parity.py --dry-run

Afterwards ALWAYS run:
    python scripts/propagate-tool-js.py
    python scripts/check-tool-script-syntax.py
"""

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

BOOK = "wedding-photo-book-planner"
SEATS = "wedding-seating-chart-maker"


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmpwrite")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def page_path(lang: str, tool: str) -> Path:
    sub = "tools/%s" % tool if lang == "en" else "%s/tools/%s" % (lang, tool)
    return ROOT / sub / "index.html"


# ===========================================================================
# THE ALBUM - the thumbnail and the export share one renderer
# ===========================================================================

OLD_DRAW_PAGE = """  function drawPageCanvas(canvas, page) {
    var ctx = canvas.getContext('2d');
    var W = canvas.width, H = canvas.height;
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, W, H);
    var layout = LAYOUTS[page.layout] || LAYOUTS[DEFAULT_LAYOUT];
    if (layout.slots === 0) {
      // cover/title
      ctx.fillStyle = '#2c2c2c';
      ctx.font = '600 16px Georgia, serif';
      ctx.textAlign = 'center';
      ctx.fillText(state.title || 'Wedding', W/2, H/2 - 14);
      ctx.font = '300 11px Georgia, serif';
      ctx.fillStyle = '#7a7a7a';
      ctx.fillText(state.date || '', W/2, H/2 + 4);
      if (state.tag) {
        ctx.fillStyle = '#d4af37';
        ctx.font = '300 9px Georgia, serif';
        ctx.fillText(state.tag, W/2, H/2 + 22);
      }
      return;
    }
    var slotPositions = computeSlotPositions(layout.slots, W, H);
    slotPositions.forEach(function (sp, i) {
      var pid = (page.slots || [])[i];
      var photo = pid ? state.photos.find(function (p) { return p.id === pid; }) : null;
      if (photo) {
        var img = new Image();
        var adj = slotAdjust(page, i);
        img.onload = function () {
          drawCover(ctx, img, sp.x, sp.y, sp.w, sp.h, adj.zoom, adj.panU, adj.panV);
        };
        img.src = photo.url;
      } else {
        ctx.fillStyle = '#f5f5f5';
        ctx.strokeStyle = '#cccccc';
        ctx.lineWidth = 1;
        ctx.fillRect(sp.x, sp.y, sp.w, sp.h);
        ctx.strokeRect(sp.x, sp.y, sp.w, sp.h);
        ctx.fillStyle = '#999';
        ctx.font = '300 9px Georgia, serif';
        ctx.textAlign = 'center';
        ctx.fillText('Slot ' + (i+1), sp.x + sp.w/2, sp.y + sp.h/2);
      }
    });
    if (page.caption) {
      ctx.fillStyle = '#2c2c2c';
      ctx.font = '300 9px Georgia, serif';
      ctx.textAlign = 'center';
      ctx.fillText(page.caption, W/2, H - 12);
    }
  }
"""

NEW_DRAW_PAGE = """  // §2.15 - the page thumbnail and the exported page are now drawn by the
  // SAME functions. Before this the thumbnail had its own copy of the cover
  // and its own copy of the caption, and an empty slot was a bordered box
  // labelled "Slot 3" in the thumbnail but a plain box in the export - so
  // the grid showed a page the visitor never got.
  //
  // Every measurement below is a fraction of the page size, which is what
  // makes the thumbnail the export at 1/12 scale rather than a lookalike.
  function drawPageCanvas(canvas, page) {
    var ctx = canvas.getContext('2d');
    var size = { w: canvas.width, h: canvas.height };
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, size.w, size.h);
    var layout = LAYOUTS[page.layout] || LAYOUTS[DEFAULT_LAYOUT];
    if (layout.slots === 0) {
      drawCoverPage(ctx, size);
      drawPageCaption(ctx, size, page);
      return;
    }
    var slotPositions = computeSlotPositions(layout.slots, size.w, size.h);
    slotPositions.forEach(function (sp, i) {
      var pid = (page.slots || [])[i];
      var photo = pid ? state.photos.find(function (p) { return p.id === pid; }) : null;
      if (photo) {
        var img = new Image();
        var adj = slotAdjust(page, i);
        img.onload = function () {
          drawCover(ctx, img, sp.x, sp.y, sp.w, sp.h, adj.zoom, adj.panU, adj.panV);
        };
        img.src = photo.url;
      } else {
        drawEmptySlot(ctx, sp.x, sp.y, sp.w, sp.h);
      }
    });
    drawPageCaption(ctx, size, page);
  }

  // An empty slot. One function, so the thumbnail and the export draw the
  // same empty slot. It is deliberately blank: an album page that is printed
  // with "Slot 3" written on it is not what anybody wants.
  function drawEmptySlot(ctx, x, y, w, h) {
    ctx.fillStyle = '#fafafa';
    ctx.fillRect(x, y, w, h);
  }
"""

OLD_EXPORT_EMPTY = """        } else {
          ctx.fillStyle = '#fafafa';
          ctx.fillRect(sp.x, sp.y, sp.w, sp.h);
          pending--;
          if (pending <= 0) finish();
        }
"""

NEW_EXPORT_EMPTY = """        } else {
          drawEmptySlot(ctx, sp.x, sp.y, sp.w, sp.h);
          pending--;
          if (pending <= 0) finish();
        }
"""

OLD_BOOK_TAIL = """  init();
})();
"""

NEW_BOOK_TAIL = """  // §2.15 - a small read-only hook so the verification script can compare
  // the page THUMBNAIL with the exported page. It returns the mean
  // difference between the two, and that number is what has to be small:
  // the thumbnail has to BE the export, at 1/12 scale.
  window.__waBookDebug = {
    compare: function (idx) {
      var small = pagesGridEl.querySelector('canvas[data-canvas-idx="' + idx + '"]');
      if (!small) return Promise.resolve(null);
      return renderPageCanvas(idx).then(function (big) {
        var tmp = document.createElement('canvas');
        tmp.width = small.width;
        tmp.height = small.height;
        var tctx = tmp.getContext('2d');
        tctx.drawImage(big, 0, 0, small.width, small.height);
        var a = small.getContext('2d').getImageData(0, 0, small.width, small.height).data;
        var b = tctx.getImageData(0, 0, small.width, small.height).data;
        var sum = 0;
        var n = a.length / 4;
        for (var i = 0; i < a.length; i += 4) {
          sum += Math.abs(a[i] - b[i]) + Math.abs(a[i + 1] - b[i + 1]) + Math.abs(a[i + 2] - b[i + 2]);
        }
        return { diff: sum / n / 3, w: small.width, h: small.height, bigW: big.width, bigH: big.height };
      });
    },
    thumbs: function () {
      return pagesGridEl.querySelectorAll('canvas.pb-page-canvas').length;
    }
  };

  init();
})();
"""

# --- §2.15b: the gutters have to be a FRACTION of the page ----------------
#
# `computeSlotPositions` used a FIXED 6 px of gutter at every size. The
# export is 2400 px and the thumbnail is 200 px, so the thumbnail's gutters
# were twelve times too thick: the grid in the editor showed a page the
# visitor never got. A fraction of the page is also exactly what makes the
# thumbnail the export at 1/12 scale.
#
# At the export sizes the numbers do not change - 2400/400 = 6 px of gutter
# and 2400/600 = 4 px between two slots - so the printed file stays as it
# was.

OLD_SLOT_POS = """  function computeSlotPositions(n, W, H) {
    var pad = 6;
    if (n === 1) return [{ x: pad, y: pad, w: W - 2*pad, h: H - 2*pad }];
    if (n === 2) return [
      { x: pad, y: pad, w: W/2 - pad - 2, h: H - 2*pad },
      { x: W/2 + 2, y: pad, w: W/2 - pad - 2, h: H - 2*pad }
    ];
    if (n === 3) return [
      { x: pad, y: pad, w: W - 2*pad, h: H*0.55 },
      { x: pad, y: H*0.55 + 4, w: W/2 - pad - 2, h: H*0.45 - pad - 4 },
      { x: W/2 + 2, y: H*0.55 + 4, w: W/2 - pad - 2, h: H*0.45 - pad - 4 }
    ];
    if (n === 4) {
      var half = (H - 2*pad - 4) / 2;
      var halfW = (W - 2*pad - 4) / 2;
      return [
        { x: pad, y: pad, w: halfW, h: half },
        { x: pad + halfW + 4, y: pad, w: halfW, h: half },
        { x: pad, y: pad + half + 4, w: halfW, h: half },
        { x: pad + halfW + 4, y: pad + half + 4, w: halfW, h: half }
      ];
    }
    return [];
  }
"""

NEW_SLOT_POS = """  // §2.15 - the gutters are a FRACTION of the page, not a fixed number of
  // pixels.
  //
  // They used to be 6 px at every size, which meant the 200 px thumbnail
  // had gutters twelve times too thick relative to the 2400 px export: the
  // grid showed a page the visitor never got. A fraction of the page is
  // also what makes the thumbnail the export at 1/12 scale.
  //
  // At the export sizes the numbers are unchanged - 2400/400 = 6 px of
  // gutter, 2400/600 = 4 px between two slots - so the printed file does
  // not change.
  function computeSlotPositions(n, W, H) {
    var unit = Math.min(W, H);
    var pad = unit / 400;
    var gap = unit / 600;
    if (n === 1) return [{ x: pad, y: pad, w: W - 2*pad, h: H - 2*pad }];
    if (n === 2) return [
      { x: pad, y: pad, w: W/2 - pad - gap/2, h: H - 2*pad },
      { x: W/2 + gap/2, y: pad, w: W/2 - pad - gap/2, h: H - 2*pad }
    ];
    if (n === 3) return [
      { x: pad, y: pad, w: W - 2*pad, h: H*0.55 },
      { x: pad, y: H*0.55 + gap, w: W/2 - pad - gap/2, h: H*0.45 - pad - gap },
      { x: W/2 + gap/2, y: H*0.55 + gap, w: W/2 - pad - gap/2, h: H*0.45 - pad - gap }
    ];
    if (n === 4) {
      var half = (H - 2*pad - gap) / 2;
      var halfW = (W - 2*pad - gap) / 2;
      return [
        { x: pad, y: pad, w: halfW, h: half },
        { x: pad + halfW + gap, y: pad, w: halfW, h: half },
        { x: pad, y: pad + half + gap, w: halfW, h: half },
        { x: pad + halfW + gap, y: pad + half + gap, w: halfW, h: half }
      ];
    }
    return [];
  }
"""

# The export may be rendered at a size other than the print size. That is
# what lets the verification render the exported page at the thumbnail's
# size and compare the two canvases directly.
OLD_RENDER_SIG = """  function renderPageCanvas(idx) {
    return new Promise(function (resolve) {
      var size = SIZES[state.size];
"""

NEW_RENDER_SIG = """  function renderPageCanvas(idx, sizeOverride) {
    return new Promise(function (resolve) {
      var size = sizeOverride || SIZES[state.size];
"""

BOOK_JS = [
    (OLD_DRAW_PAGE, NEW_DRAW_PAGE, "function drawEmptySlot(", "the page thumbnail"),
    # The marker has to be the WHOLE call plus the line after it: the bare
    # call also appears in the thumbnail, so a marker of just the call would
    # report "already applied" while the export still had its own copy.
    (OLD_EXPORT_EMPTY, NEW_EXPORT_EMPTY,
     "drawEmptySlot(ctx, sp.x, sp.y, sp.w, sp.h);\n          pending--;", "the exported empty slot"),
    (OLD_BOOK_TAIL, NEW_BOOK_TAIL, "window.__waBookDebug", "the album debug hook"),
]

BOOK_EXTRA = [
    (OLD_SLOT_POS, NEW_SLOT_POS, "var gap = unit / 600;", "the proportional gutters"),
    (OLD_RENDER_SIG, NEW_RENDER_SIG, "renderPageCanvas(idx, sizeOverride)", "the export at any size"),
]


# ===========================================================================
# THE SEATING CHART - one set of constants for the DOM and the canvas
# ===========================================================================

OLD_CONSTANTS_ANCHOR = """var SEAT_RADIUS = 56;       // px offset from table center
"""

NEW_CONSTANTS_ANCHOR = """var SEAT_RADIUS = 56;       // px offset from table center

  // §2.15 - ONE source of truth for the chart's look.
  //
  // The preview is DOM (it has to be: the visitor clicks a seat to assign a
  // guest) and the export is a canvas. Before this pass the two had drifted
  // apart: the export drew a 6 px seat with a grey border on #f5f5f5 while
  // the preview drew a 4 px seat with a warm border on #f5f0ea, both in a
  // different font, and the export dropped the "N/M seated" line the preview
  // shows under every table.
  //
  // renderFloor() writes these values into the DOM as inline styles and
  // buildChartCanvas() draws them, so the preview and the export cannot
  // disagree. The CSS in the page carries the same values as the default
  // before the script runs; scripts/verify-chart-parity.py compares the
  // preview's computed style with the exported pixels and fails if they
  // ever drift again.
  var CHART = {
    font: 'Georgia, "Times New Roman", serif',
    ink: '#2c2c2c',
    muted: '#6b6b6b',
    tableFill: '#ffffff',
    tableBorder: '#d4af37',
    tableBorderWidth: 2,
    tableRadius: 12,
    tableNameSize: 14,
    tableCountSize: 11,
    tableShadow: 'rgba(0,0,0,0.06)',
    tableShadowBlur: 8,
    tableShadowY: 2,
    seatBorder: '#e5e0d8',
    seatBorderWidth: 1,
    seatEmpty: '#f5f0ea',
    seatRadius: 4,
    seatFontSize: 11,
    seatInk: '#2c2c2c',
    seatInkOccupied: '#ffffff',
    canvasBg: '#fcfaf6'
  };

  // The inline style for a piece of chart text.
  function chartFont(size, weight) {
    return 'font-family:' + CHART.font + ';font-size:' + size + 'px;font-weight:' + weight + ';';
  }

  // CSS ellipsis, in canvas. The preview truncates a long guest name with
  // "text-overflow: ellipsis"; the export used to cut it at 9 characters
  // instead, so the two showed different names.
  function ellipsize(ctx, text, maxWidth) {
    if (ctx.measureText(text).width <= maxWidth) return text;
    var s = text;
    while (s.length > 1 && ctx.measureText(s + '\\u2026').width > maxWidth) {
      s = s.slice(0, -1);
    }
    return s + '\\u2026';
  }
"""

OLD_TABLES = """      html += '<div class="seating-table ' + t.type + '" data-table-id="' + t.id + '" '
            + 'style="left:' + (t.cx - tw/2) + 'px; top:' + (t.cy - th/2) + 'px; width:' + tw + 'px; height:' + th + 'px;">'
            + '<div class="seating-table-name">' + escapeHtml(t.name) + '</div>'
            + '<div class="seating-table-count">' + countOccupied(t) + '/' + t.seats + ' seated</div>'
            + '</div>';
"""

NEW_TABLES = """      var radius = t.type === 'round' ? '50%' : (CHART.tableRadius + 'px');
      html += '<div class="seating-table ' + t.type + '" data-table-id="' + t.id + '" '
            + 'style="left:' + (t.cx - tw/2) + 'px; top:' + (t.cy - th/2) + 'px; width:' + tw + 'px; height:' + th + 'px;'
            + 'background:' + CHART.tableFill + ';'
            + 'border:' + CHART.tableBorderWidth + 'px solid ' + CHART.tableBorder + ';'
            + 'border-radius:' + radius + ';'
            + 'box-shadow:0 ' + CHART.tableShadowY + 'px ' + CHART.tableShadowBlur + 'px ' + CHART.tableShadow + ';">'
            + '<div class="seating-table-name" style="' + chartFont(CHART.tableNameSize, 700) + 'color:' + CHART.ink + ';">' + escapeHtml(t.name) + '</div>'
            + '<div class="seating-table-count" style="' + chartFont(CHART.tableCountSize, 400) + 'color:' + CHART.muted + ';">' + countOccupied(t) + '/' + t.seats + ' seated</div>'
            + '</div>';
"""

OLD_SEAT_STYLE = """        var style = 'left:' + sp.x + 'px; top:' + sp.y + 'px;';
        if (guest) style += 'background:' + bgColor + ';border-color:' + bgColor + ';';
"""

NEW_SEAT_STYLE = """        var style = 'left:' + sp.x + 'px; top:' + sp.y + 'px;';
        // The size is written inline too. Ten of the eleven localized copies
        // carried a CSS rule of 64x36 (the machine translator had "improved"
        // it) while the geometry positions the seats for 36x24 - so those
        // ten languages drew the seats too big and off their tables. The
        // inline width and height make the CSS unable to override the
        // geometry.
        style += 'width:' + SEAT_W + 'px; height:' + SEAT_H + 'px;';
        style += chartFont(CHART.seatFontSize, guest ? 600 : 400);
        style += 'border-radius:' + CHART.seatRadius + 'px;';
        style += 'border:' + CHART.seatBorderWidth + 'px solid ' + CHART.seatBorder + ';';
        style += 'color:' + (guest ? CHART.seatInkOccupied : CHART.seatInk) + ';';
        if (guest) style += 'background:' + bgColor + ';border-color:' + bgColor + ';';
"""

OLD_CANVAS_TABLE = """      ctx.fillStyle = '#fff';
      ctx.strokeStyle = '#d4af37';
      ctx.lineWidth = 2;
      if (t.type === 'round') {
        ctx.beginPath();
        ctx.arc(t.cx, t.cy, TABLE_R, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      } else {
        roundRect(ctx, t.cx - tw/2, t.cy - th/2, tw, th, 12);
        ctx.fill();
        ctx.stroke();
      }
      ctx.fillStyle = '#2c2c2c';
      ctx.font = '700 14px Georgia, serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(t.name, t.cx, t.cy);
"""

NEW_CANVAS_TABLE = """      ctx.fillStyle = CHART.tableFill;
      ctx.strokeStyle = CHART.tableBorder;
      ctx.lineWidth = CHART.tableBorderWidth;
      // The same soft shadow the preview has (--shadow-sm).
      ctx.shadowColor = CHART.tableShadow;
      ctx.shadowBlur = CHART.tableShadowBlur;
      ctx.shadowOffsetY = CHART.tableShadowY;
      if (t.type === 'round') {
        ctx.beginPath();
        ctx.arc(t.cx, t.cy, TABLE_R, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      } else {
        roundRect(ctx, t.cx - tw/2, t.cy - th/2, tw, th, CHART.tableRadius);
        ctx.fill();
        ctx.stroke();
      }
      ctx.shadowColor = 'rgba(0,0,0,0)';
      ctx.shadowBlur = 0;
      ctx.shadowOffsetY = 0;
      ctx.fillStyle = CHART.ink;
      ctx.font = '700 ' + CHART.tableNameSize + 'px ' + CHART.font;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(t.name, t.cx, t.cy);
      // The "N/M seated" line under the table. The preview has always shown
      // it; the export did not.
      ctx.fillStyle = CHART.muted;
      ctx.font = '400 ' + CHART.tableCountSize + 'px ' + CHART.font;
      ctx.fillText(countOccupied(t) + '/' + t.seats + ' seated', t.cx, t.cy + th / 2 + 16);
"""

OLD_CANVAS_SEAT = """        if (guest) {
          ctx.fillStyle = (GROUPS[guest.group] || GROUPS.other).color;
        } else {
          ctx.fillStyle = '#f5f5f5';
        }
        ctx.strokeStyle = '#cccccc';
        ctx.lineWidth = 1;
        roundRect(ctx, sp.x, sp.y, SEAT_W, SEAT_H, 6);
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = guest ? '#fff' : '#7a7a7a';
        ctx.font = (guest ? '600 ' : '400 ') + '11px Georgia, serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        var txt = guest ? guest.name : (i + 1);
        if (txt.length > 9) txt = txt.slice(0, 8) + '…';
        ctx.fillText(txt, sp.x + SEAT_W / 2, sp.y + SEAT_H / 2);
"""

NEW_CANVAS_SEAT = """        if (guest) {
          ctx.fillStyle = (GROUPS[guest.group] || GROUPS.other).color;
        } else {
          ctx.fillStyle = CHART.seatEmpty;
        }
        ctx.strokeStyle = CHART.seatBorder;
        ctx.lineWidth = CHART.seatBorderWidth;
        roundRect(ctx, sp.x, sp.y, SEAT_W, SEAT_H, CHART.seatRadius);
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = guest ? CHART.seatInkOccupied : CHART.seatInk;
        ctx.font = (guest ? '600 ' : '400 ') + CHART.seatFontSize + 'px ' + CHART.font;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        var txt = guest ? guest.name : String(i + 1);
        // The preview truncates with CSS ellipsis; the export has to do the
        // same or the two show different names.
        ctx.fillText(ellipsize(ctx, txt, SEAT_W - 6), sp.x + SEAT_W / 2, sp.y + SEAT_H / 2);
"""

OLD_CANVAS_BG = """    ctx.fillStyle = '#fcfaf6';
    ctx.fillRect(0, 0, W, H);
"""

NEW_CANVAS_BG = """    ctx.fillStyle = CHART.canvasBg;
    ctx.fillRect(0, 0, W, H);
"""

OLD_SEAT_TAIL = """  render();
})();
"""

NEW_SEAT_TAIL = """  // §2.15 - a small read-only hook so the verification script can compare
  // the PREVIEW with the exported PNG: the preview's computed style
  // against the pixels the export actually draws.
  window.__waSeatDebug = function () {
    var W = 1600, H = 1200;
    var c = buildChartCanvas();
    var ctx = c.getContext('2d');
    var floorW = maxFloorX() + 80, floorH = maxFloorY() + 80;
    var scale = Math.min((W - 80) / floorW, (H - 140) / floorH);
    var offX = (W - floorW * scale) / 2;
    var offY = 120;
    var seats = [];
    var nodes = floorEl.querySelectorAll('.seating-seat');
    for (var i = 0; i < nodes.length && i < 8; i++) {
      var el = nodes[i];
      var cs = getComputedStyle(el);
      var px = Math.round(offX + (parseFloat(el.style.left) + SEAT_W / 2) * scale);
      var py = Math.round(offY + (parseFloat(el.style.top) + SEAT_H / 2) * scale);
      var d = ctx.getImageData(px, py, 1, 1).data;
      seats.push({
        bg: cs.backgroundColor,
        border: cs.borderTopColor,
        radius: cs.borderRadius,
        fontSize: cs.fontSize,
        font: cs.fontFamily,
        width: cs.width,
        height: cs.height,
        px: [d[0], d[1], d[2]]
      });
    }
    var tables = [];
    var tnodes = floorEl.querySelectorAll('.seating-table');
    for (var j = 0; j < tnodes.length && j < 3; j++) {
      var tn = tnodes[j];
      var tcs = getComputedStyle(tn);
      var nameEl = tn.querySelector('.seating-table-name');
      var countEl = tn.querySelector('.seating-table-count');
      tables.push({
        border: tcs.borderTopColor,
        borderWidth: tcs.borderTopWidth,
        nameSize: nameEl ? getComputedStyle(nameEl).fontSize : null,
        nameColor: nameEl ? getComputedStyle(nameEl).color : null,
        countSize: countEl ? getComputedStyle(countEl).fontSize : null,
        countColor: countEl ? getComputedStyle(countEl).color : null
      });
    }
    // How many pixels of the "N/M seated" colour are in the band UNDER the
    // first table? Zero means the export dropped the line the preview shows.
    var muted = 0;
    if (tnodes.length && state.tables.length) {
      var t0 = state.tables[0];
      var tw0 = (t0.type === 'long' || t0.type === 'sweetheart') ? 220 : (TABLE_R * 2);
      var th0 = (t0.type === 'long' || t0.type === 'sweetheart') ? 80 : (TABLE_R * 2);
      var x0 = Math.max(0, Math.round(offX + (t0.cx - tw0 / 2 - 30) * scale));
      var y0 = Math.max(0, Math.round(offY + (t0.cy + th0 / 2) * scale));
      var w0 = Math.round((tw0 + 60) * scale);
      var h0 = Math.round(26 * scale);
      if (h0 > 0 && w0 > 0 && x0 + w0 <= W && y0 + h0 <= H) {
        var band = ctx.getImageData(x0, y0, w0, h0).data;
        for (var p = 0; p < band.length; p += 4) {
          if (Math.abs(band[p] - 0x6b) < 34 && Math.abs(band[p + 1] - 0x6b) < 34 && Math.abs(band[p + 2] - 0x6b) < 34) muted++;
        }
      }
    }
    return { chart: CHART, scale: scale, offX: offX, offY: offY, seats: seats, tables: tables, mutedPixels: muted };
  };

  render();
})();
"""

SEATS_JS = [
    (OLD_CONSTANTS_ANCHOR, NEW_CONSTANTS_ANCHOR, "var CHART = {", "the chart constants"),
    (OLD_TABLES, NEW_TABLES, "var radius = t.type === 'round'", "the preview tables"),
    (OLD_SEAT_STYLE, NEW_SEAT_STYLE, "style += chartFont(CHART.seatFontSize", "the preview seats"),
    (OLD_CANVAS_BG, NEW_CANVAS_BG, "ctx.fillStyle = CHART.canvasBg;", "the export background"),
    (OLD_CANVAS_TABLE, NEW_CANVAS_TABLE, "ctx.fillText(countOccupied(t)", "the exported tables"),
    (OLD_CANVAS_SEAT, NEW_CANVAS_SEAT, "ellipsize(ctx, txt, SEAT_W - 6)", "the exported seats"),
    (OLD_SEAT_TAIL, NEW_SEAT_TAIL, "window.__waSeatDebug", "the seating chart debug hook"),
]

# The occupied seat is a solid block of its group colour in the PREVIEW -
# the border takes the group colour too - while the export stroked it with
# the soft border colour. The two disagreed at the edge of every occupied
# seat.

OLD_SEAT_PAINT = """        if (guest) {
          ctx.fillStyle = (GROUPS[guest.group] || GROUPS.other).color;
        } else {
          ctx.fillStyle = CHART.seatEmpty;
        }
        ctx.strokeStyle = CHART.seatBorder;
        ctx.lineWidth = CHART.seatBorderWidth;
"""

NEW_SEAT_PAINT = """        var seatFill = guest ? (GROUPS[guest.group] || GROUPS.other).color : CHART.seatEmpty;
        ctx.fillStyle = seatFill;
        // An occupied seat is a solid block of its group colour in the
        // preview - the border takes the group colour as well - so the
        // export strokes it the same way. An empty seat keeps the soft
        // border.
        ctx.strokeStyle = guest ? seatFill : CHART.seatBorder;
        ctx.lineWidth = CHART.seatBorderWidth;
"""

SEATS_EXTRA = [
    (OLD_SEAT_PAINT, NEW_SEAT_PAINT, "ctx.strokeStyle = guest ? seatFill : CHART.seatBorder;", "the occupied seat border"),
]

# --- the seating chart's CSS -----------------------------------------------
#
# The values below are the DEFAULT, before the script writes the inline
# styles from CHART. They are kept in step with CHART on purpose: the
# preview must look like the export even for the split second before the
# script runs.
#
# The rules are matched with a REGEX, not with the English text, because ten
# of the eleven localized copies carried a DIFFERENT rule: the machine
# translator had "improved" .seating-seat to 64x36 with a 6 px radius while
# the English page said 36x24 with a 4 px radius - and the geometry in the
# script positions the seats for 36x24. So in those ten languages the seats
# were drawn too big and offset from the tables they belong to. The script
# now writes the seat's width and height inline as well, so the CSS cannot
# override the geometry any more.

CSS_TABLE = """        /* §2.15 - the chart's look lives in CHART (in the script below); these
           are the same values, so the preview matches the export. */
        .seating-table { position: absolute; background: #ffffff; border: 2px solid #d4af37; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: Georgia, "Times New Roman", serif; font-size: 14px; color: #2c2c2c; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
"""

CSS_NAME = """        .seating-table-name { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-family: Georgia, "Times New Roman", serif; font-size: 14px; font-weight: 700; color: #2c2c2c; pointer-events: none; text-align: center; line-height: 1.1; }
"""

CSS_COUNT = """        .seating-table-count { position: absolute; bottom: -22px; left: 50%; transform: translateX(-50%); font-family: Georgia, "Times New Roman", serif; font-size: 11px; font-weight: 400; color: #6b6b6b; white-space: nowrap; }
"""

CSS_SEAT = """        .seating-seat { position: absolute; width: 36px; height: 24px; background: #f5f0ea; border: 1px solid #e5e0d8; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-family: Georgia, "Times New Roman", serif; font-size: 11px; color: #2c2c2c; text-align: center; padding: 1px 2px; line-height: 1.05; cursor: pointer; transition: background .15s ease, border-color .15s ease, transform .15s ease; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
"""

# (regex, replacement, marker that proves it is already applied)
SEATS_CSS = [
    (re.compile(r"^([ \t]*)\.seating-table \{.*$", re.M), CSS_TABLE,
     ".seating-table { position: absolute; background: #ffffff;"),
    (re.compile(r"^([ \t]*)\.seating-table-name \{.*$", re.M), CSS_NAME,
     ".seating-table-name { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-family: Georgia,"),
    (re.compile(r"^([ \t]*)\.seating-table-count \{.*$", re.M), CSS_COUNT,
     ".seating-table-count { position: absolute; bottom: -22px; left: 50%; transform: translateX(-50%); font-family: Georgia,"),
    (re.compile(r"^([ \t]*)\.seating-seat \{.*$", re.M), CSS_SEAT,
     ".seating-seat { position: absolute; width: 36px; height: 24px; background: #f5f0ea;"),
]


# --- the debug hooks, v2 --------------------------------------------------
#
# The first version of each hook was too weak to be worth anything:
#   * the album one compared the thumbnail with the export DOWNSCALED to
#     the thumbnail, which mixes the renderer with the resampler and can
#     never be 0;
#   * the seating one sampled the middle pixel of a seat, which is where
#     the seat's NUMBER is drawn - it read the text, not the seat.
#
# v2 compares the preview with the export directly: the album renders the
# exported page AT THE THUMBNAIL'S SIZE with the same renderer (the
# difference has to be exactly 0), and the seating chart reads the MODE
# colour of a small window (the fill wins over the glyph).

# The hooks are replaced as a BLOCK, found by the comment that starts them
# and by the line that follows them.
BOOK_HOOK_START = "  // §2.15 - a small read-only hook"
BOOK_HOOK_END = "\n  init();"

NEW_BOOK_HOOK = """  // §2.15 - a small read-only hook so the verification script can compare
  // the page THUMBNAIL with the exported page.
  //
  // compare() renders the exported page AT THE THUMBNAIL'S SIZE with the
  // very same renderer and returns the mean difference between the two
  // canvases. It has to be 0: the thumbnail and the export are not two
  // drawings that happen to look alike, they are the same drawing.
  //
  // layout() returns the slot rectangles as FRACTIONS of the page, for the
  // thumbnail's size and for the export's size. The two lists have to be
  // the same: that is what makes the thumbnail the export at 1/12 scale.
  window.__waBookDebug = {
    compare: function (idx) {
      var small = pagesGridEl.querySelector('canvas[data-canvas-idx="' + idx + '"]');
      if (!small) return Promise.resolve(null);
      return renderPageCanvas(idx, { w: small.width, h: small.height }).then(function (same) {
        var a = small.getContext('2d').getImageData(0, 0, small.width, small.height).data;
        var b = same.getContext('2d').getImageData(0, 0, small.width, small.height).data;
        var sum = 0;
        var n = a.length / 4;
        for (var i = 0; i < a.length; i += 4) {
          sum += Math.abs(a[i] - b[i]) + Math.abs(a[i + 1] - b[i + 1]) + Math.abs(a[i + 2] - b[i + 2]);
        }
        return { diff: sum / n / 3, w: small.width, h: small.height };
      });
    },
    layout: function (idx) {
      var p = state.pages_data[idx];
      var layout = LAYOUTS[p.layout] || LAYOUTS[DEFAULT_LAYOUT];
      var size = SIZES[state.size];
      var thumbW = 200;
      var thumbH = Math.max(40, Math.round(thumbW * size.h / size.w));
      function frac(list, w, h) {
        return list.map(function (sp) {
          return [sp.x / w, sp.y / h, sp.w / w, sp.h / h];
        });
      }
      return {
        slots: layout.slots,
        big: frac(computeSlotPositions(layout.slots, size.w, size.h), size.w, size.h),
        small: frac(computeSlotPositions(layout.slots, thumbW, thumbH), thumbW, thumbH)
      };
    },
    thumbs: function () {
      return pagesGridEl.querySelectorAll('canvas.pb-page-canvas').length;
    }
  };
"""

SEAT_HOOK_START = "  // §2.15 - a small read-only hook"
SEAT_HOOK_END = "\n  render();\n})();"

NEW_SEAT_HOOK = """  // §2.15 - a small read-only hook so the verification script can compare
  // the PREVIEW with the exported PNG: the preview's computed style
  // against the pixels the export actually draws.
  window.__waSeatDebug = function () {
    var W = 1600, H = 1200;
    var c = buildChartCanvas();
    var ctx = c.getContext('2d');
    var floorW = maxFloorX() + 80, floorH = maxFloorY() + 80;
    var scale = Math.min((W - 80) / floorW, (H - 140) / floorH);
    var offX = (W - floorW * scale) / 2;
    var offY = 120;

    // Every colour the export contains, counted. The one that matters is
    // the muted colour of the "N/M seated" line: the export used to drop
    // that line entirely, and nothing else on the sheet is this colour.
    var counts = {};
    var data = ctx.getImageData(0, 0, W, H).data;
    for (var i = 0; i < data.length; i += 4) {
      var key = data[i] + ',' + data[i + 1] + ',' + data[i + 2];
      counts[key] = (counts[key] || 0) + 1;
    }

    // The seats of the preview, each with the colour the EXPORT draws in
    // the same place. The mode of a small window is used, not a single
    // pixel: the middle of a seat holds its number.
    var seats = [];
    var nodes = floorEl.querySelectorAll('.seating-seat');
    for (var s = 0; s < nodes.length && s < 8; s++) {
      var el = nodes[s];
      var cs = getComputedStyle(el);
      var cx = Math.round(offX + (parseFloat(el.style.left) + SEAT_W / 2) * scale);
      var cy = Math.round(offY + (parseFloat(el.style.top) + SEAT_H / 2) * scale);
      seats.push({
        bg: cs.backgroundColor,
        border: cs.borderTopColor,
        radius: cs.borderRadius,
        fontSize: cs.fontSize,
        font: cs.fontFamily,
        fontWeight: cs.fontWeight,
        color: cs.color,
        width: cs.width,
        height: cs.height,
        exportColor: modeColor(ctx, cx, cy, Math.max(1, Math.round(SEAT_H * scale / 4)))
      });
    }

    var tables = [];
    var tnodes = floorEl.querySelectorAll('.seating-table');
    for (var j = 0; j < tnodes.length && j < 3; j++) {
      var tn = tnodes[j];
      var tcs = getComputedStyle(tn);
      var nameEl = tn.querySelector('.seating-table-name');
      var countEl = tn.querySelector('.seating-table-count');
      tables.push({
        border: tcs.borderTopColor,
        borderWidth: tcs.borderTopWidth,
        radius: tcs.borderRadius,
        bg: tcs.backgroundColor,
        nameSize: nameEl ? getComputedStyle(nameEl).fontSize : null,
        nameColor: nameEl ? getComputedStyle(nameEl).color : null,
        countSize: countEl ? getComputedStyle(countEl).fontSize : null,
        countColor: countEl ? getComputedStyle(countEl).color : null,
        countText: countEl ? countEl.textContent : null,
        countVisible: countEl ? !!countEl.offsetParent : false
      });
    }

    // The width the CSS leaves for the text inside a seat: the box is 36 px
    // wide, the border takes 1 px on each side and the padding 2 px on each
    // side, so 30 px are left for the name.
    var seatTextWidth = null;
    if (nodes.length) {
      var cs0 = getComputedStyle(nodes[0]);
      seatTextWidth = nodes[0].clientWidth
        - parseFloat(cs0.paddingLeft) - parseFloat(cs0.paddingRight);
    }

    return {
      chart: CHART,
      scale: scale,
      offX: offX,
      offY: offY,
      seats: seats,
      tables: tables,
      // The width the CSS leaves for a seat's text. The export truncates a
      // long name with the SAME width, so the preview and the export show
      // the same name - the preview with CSS ellipsis, the export with
      // ellipsize().
      seatTextWidth: seatTextWidth,
      truncate: function (name) {
        var c = document.createElement('canvas');
        var cx = c.getContext('2d');
        cx.font = '400 ' + CHART.seatFontSize + 'px ' + CHART.font;
        return ellipsize(cx, name, SEAT_W - 6);
      },
      mutedPixels: counts['107,107,107'] || 0,
      goldPixels: counts['212,175,55'] || 0,
      seatEmptyPixels: counts['245,240,234'] || 0,
      seatBorderPixels: counts['229,224,216'] || 0,
      canvasBgPixels: counts['252,250,246'] || 0
    };
  };

  // The most common colour in a small window of the export. A single pixel
  // would be useless: the middle of a seat is where its number is drawn.
  function modeColor(ctx, cx, cy, r) {
    var x0 = Math.max(0, cx - r);
    var y0 = Math.max(0, cy - r);
    var w = Math.min(ctx.canvas.width - x0, r * 2 + 1);
    var h = Math.min(ctx.canvas.height - y0, r * 2 + 1);
    if (w <= 0 || h <= 0) return null;
    var d = ctx.getImageData(x0, y0, w, h).data;
    var counts = {};
    var best = null;
    var bestN = 0;
    for (var i = 0; i < d.length; i += 4) {
      var key = d[i] + ',' + d[i + 1] + ',' + d[i + 2];
      counts[key] = (counts[key] || 0) + 1;
      if (counts[key] > bestN) { bestN = counts[key]; best = key; }
    }
    return best;
  }
"""


def patch_css(text: str) -> tuple:
    changes = 0
    for pattern, replacement, marker in SEATS_CSS:
        if marker in text:
            continue
        m = pattern.search(text)
        if not m:
            raise SystemExit("[FAIL] could not find the CSS rule %s" % pattern.pattern)
        indent = m.group(1)
        block = replacement.replace("\n", "\n" + indent)
        text = text[:m.start()] + block + text[m.end():]
        changes += 1
    return text, changes


def apply_blocks(text: str, blocks, what: str) -> tuple:
    changes = 0
    for old, new, marker, label in blocks:
        if marker in text:
            continue
        if old not in text:
            raise SystemExit("[FAIL] could not find %s (%s)" % (label, what))
        text = text.replace(old, new, 1)
        changes += 1
    return text, changes


def replace_block(text: str, start_marker: str, end_marker: str,
                  new: str, label: str) -> tuple:
    """Replace a whole block, found by its start and its end.

    A marker inside the block cannot be used here: the marker would be
    INSIDE the text that gets replaced, so the check "is it already
    applied?" could never be true and every run would patch again.
    """
    i = text.find(start_marker)
    if i < 0:
        raise SystemExit("[FAIL] could not find %s" % label)
    j = text.find(end_marker, i)
    if j < 0:
        raise SystemExit("[FAIL] could not find the end of %s" % label)
    old = text[i:j]
    if old == new:
        return text, 0
    return text[:i] + new + text[j:], 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total = 0
    for lang in LANGS:
        # --- the album -----------------------------------------------------
        p = page_path(lang, BOOK)
        if not p.is_file():
            raise SystemExit("[FAIL] missing page: %s" % p)
        text = p.read_text(encoding="utf-8")
        before = text
        if lang == "en":
            text, n = apply_blocks(text, BOOK_JS, "album")
            text, n2 = apply_blocks(text, BOOK_EXTRA, "album extra")
            text, n3 = replace_block(text, BOOK_HOOK_START, BOOK_HOOK_END,
                                     NEW_BOOK_HOOK, "the album debug hook")
            n += n2 + n3
        else:
            n = 0
        if text != before and not args.dry_run:
            write_atomic(p, text)
        total += n
        print("  %-3s album js=%d" % (lang, n))

        # --- the seating chart ---------------------------------------------
        p = page_path(lang, SEATS)
        if not p.is_file():
            raise SystemExit("[FAIL] missing page: %s" % p)
        text = p.read_text(encoding="utf-8")
        before = text
        text, c = patch_css(text)
        j = 0
        if lang == "en":
            text, j = apply_blocks(text, SEATS_JS, "seating chart JS")
            text, j2 = apply_blocks(text, SEATS_EXTRA, "seating chart extra")
            text, j3 = replace_block(text, SEAT_HOOK_START, SEAT_HOOK_END,
                                     NEW_SEAT_HOOK, "the seating chart debug hook")
            j += j2 + j3
        if text != before and not args.dry_run:
            write_atomic(p, text)
        total += c + j
        print("  %-3s seating css=%d js=%d" % (lang, c, j))

    if args.dry_run:
        print("\n[DRY RUN] nothing was written")
    else:
        print("\nNow run:")
        print("  python scripts/propagate-tool-js.py")
        print("  python scripts/check-tool-script-syntax.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
