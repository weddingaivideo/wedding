#!/usr/bin/env python3
"""
Let the visitor drag the text on the photo (§2.2).

WHAT IT DOES
------------
The add-text tool had a POSITION dropdown - top, centre, bottom - and
nothing else. That is not what people want: they want the text where
they put it. This patch makes the text block draggable straight on the
preview, and the drag applies to every photo in the batch.

THE GEOMETRY THAT MATTERS
-------------------------
The preview canvas is FULL SIZE (canvas.width = the photo's natural
width) and is DISPLAYED scaled down (style.width = 720px). So a
pointer position has to be mapped through the display scale:

    canvasX = (clientX - rect.left) * (canvas.width / rect.width)

The offset itself is stored in CANVAS pixels, not display pixels. That
is what makes the same number work for the preview AND for the export:
processOne() renders onto a second canvas of the same natural size and
calls the SAME drawTextBlock().

The block is hit-tested against its measured bounding box, so the drag
starts where the user actually clicked - not anywhere on the photo.
The offset is clamped so the block can never be dragged out of the
frame and lost.

Usage
-----
    python scripts/patch-add-text-drag.py            # apply
    python scripts/patch-add-text-drag.py --dry-run

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
TOOL = "add-text-to-wedding-photo"
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

K_HINT = "tools.add-text-to-wedding-photo.small_text.drag_to_move.k7m2n4p6"
K_RESET = "tools.add-text-to-wedding-photo.button_text.reset_position.r9s3t5v7"

# The keys the position control ALREADY used in the seven languages that
# had it bound. The other four (en/zh/pt/ru) had the text inline and
# unbound; they get the same keys so all eleven pages are identical.
P = "tools.add-text-to-wedding-photo."
K_LABEL = P + "label_text.d4d2a668"
K_TOP = P + "option_text.c949729c"
K_TOPC = P + "option_text.f620edd1"
K_CENTER = P + "option_text.c646a231"
K_BOTC = P + "option_text.879e6d08"
K_BOTTOM = P + "option_text.12c4c5e8"
K_SAVEDATE = P + "small_text.943ad5ab"

# --- the markup -----------------------------------------------------------

# The canonical position control. Every page ends up with exactly this:
# the ENGLISH source text plus a data-i18n key, so the static fallback is
# English and the rendered page is the visitor's language.
#
# Before this pass the control was in three different states across the
# eleven pages: en/zh/pt/ru were not bound at all (correct inline
# translations, but hard-coded), and es/fr/de/ja/ar/th/hi were bound but
# their INLINE text was Chinese on every one of them.
POSITION_BLOCK = """<div class="wa-tool-control">
<label for="position" data-i18n="{label}">Position</label>
<select id="position">
<option value="top" data-i18n="{top}">Top</option>
<option value="top-center" selected data-i18n="{topc}">Top-Center</option>
<option value="center" data-i18n="{center}">Center</option>
<option value="bottom-center" data-i18n="{botc}">Bottom-Center</option>
<option value="bottom" data-i18n="{bottom}">Bottom</option>
</select>
<small data-i18n="{savedate}">Bottom-Center is the classic save-the-date spot.</small>
<small data-i18n="{hint}">Drag the text straight on the photo to move it &mdash; the position applies to every photo in the batch.</small>
<button type="button" class="btn btn-secondary btn-small" id="reset-position-btn" data-i18n="{reset}">Reset position</button>
</div>
""".format(label=K_LABEL, top=K_TOP, topc=K_TOPC, center=K_CENTER, botc=K_BOTC,
           bottom=K_BOTTOM, savedate=K_SAVEDATE, hint=K_HINT, reset=K_RESET)

# Matched by ROLE, because the eleven pages spell the control differently.
POSITION_RE = re.compile(
    r'<div class="wa-tool-control">\s*<label for="position".*?</div>', re.S)

# The canvas needs touch-action:none, otherwise a touch drag scrolls the
# page instead of moving the text.
CANVAS_RE = re.compile(r'(<canvas id="preview-canvas"[^>]*?)(>)(?=</canvas>)', re.S)


def patch_canvas(text: str) -> tuple:
    m = CANVAS_RE.search(text)
    if not m:
        raise SystemExit("[FAIL] the preview canvas was not found")
    if "touch-action" in m.group(1):
        return text, 0
    text = text[:m.end(1)] + ' style="touch-action:none"' + text[m.end(1):]
    return text, 1


# --- the inline JS (English page only) ------------------------------------

OLD_SETTINGS = """      function getSettings() {
        return {
          primary: primaryTextEl.value || '',
          secondary: secondaryTextEl.value || '',
          fontName: fontEl.value || 'Playfair Display',
          position: positionEl.value || 'bottom-center',
          primarySize: parseInt(primarySizeEl.value, 10),
          secondarySize: parseInt(secondarySizeEl.value, 10),
          color: colorEl.value || '#FFFFFF',
          shadow: !!shadowToggleEl.checked,
          shadowOffset: parseInt(shadowOffsetEl.value, 10) || 0,
          format: formatEl.value || 'image/png'
        };
      }
"""

NEW_SETTINGS = """      function getSettings() {
        return {
          primary: primaryTextEl.value || '',
          secondary: secondaryTextEl.value || '',
          fontName: fontEl.value || 'Playfair Display',
          position: positionEl.value || 'bottom-center',
          primarySize: parseInt(primarySizeEl.value, 10),
          secondarySize: parseInt(secondarySizeEl.value, 10),
          color: colorEl.value || '#FFFFFF',
          shadow: !!shadowToggleEl.checked,
          shadowOffset: parseInt(shadowOffsetEl.value, 10) || 0,
          format: formatEl.value || 'image/png',
          // §2.2 - the drag offset, in CANVAS pixels. Canvas pixels (not
          // display pixels) are what makes the preview and the exported
          // full-size image agree: processOne() renders onto a canvas of
          // the same natural size and calls the same drawTextBlock().
          textX: textOffsetX,
          textY: textOffsetY
        };
      }
"""

OLD_DRAW = """        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'alphabetic';
        if (settings.shadow) {
          ctx.shadowColor = 'rgba(0,0,0,0.5)';
          ctx.shadowBlur = 4;
          ctx.shadowOffsetX = settings.shadowOffset;
          ctx.shadowOffsetY = settings.shadowOffset;
        }

        if (primary) {
          ctx.font = primarySize + 'px ' + family;
          ctx.fillStyle = settings.color;
          ctx.fillText(primary, Math.round(canvasW / 2), primaryY);
        }
        if (secondary) {
          ctx.font = secondarySize + 'px ' + family;
          ctx.fillStyle = settings.color;
          ctx.fillText(secondary, Math.round(canvasW / 2), secondaryY);
        }
        ctx.restore();
      }
"""

NEW_DRAW = """        // The block's measured width, so the drag can hit-test it and
        // clamp it to the frame.
        var blockW = 0;
        if (primary) blockW = Math.max(blockW, measureText(ctx, primary, primarySize, family).width);
        if (secondary) blockW = Math.max(blockW, measureText(ctx, secondary, secondarySize, family).width);

        // Natural (un-dragged) geometry.
        var natCenterX = Math.round(canvasW / 2);
        var natTop = primary ? primaryY - primarySize : secondaryY - secondarySize;
        var natBottom = secondary ? secondaryY + Math.round(secondarySize * 0.3)
                                  : primaryY + Math.round(primarySize * 0.3);

        // §2.2 - apply the drag offset.
        var ox = settings.textX || 0;
        var oy = settings.textY || 0;
        var centerX = natCenterX + ox;
        primaryY += oy;
        secondaryY += oy;

        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'alphabetic';
        if (settings.shadow) {
          ctx.shadowColor = 'rgba(0,0,0,0.5)';
          ctx.shadowBlur = 4;
          ctx.shadowOffsetX = settings.shadowOffset;
          ctx.shadowOffsetY = settings.shadowOffset;
        }

        if (primary) {
          ctx.font = primarySize + 'px ' + family;
          ctx.fillStyle = settings.color;
          ctx.fillText(primary, centerX, primaryY);
        }
        if (secondary) {
          ctx.font = secondarySize + 'px ' + family;
          ctx.fillStyle = settings.color;
          ctx.fillText(secondary, centerX, secondaryY);
        }
        ctx.restore();

        // The block's bounding box, with and without the offset. The drag
        // uses it to hit-test and to clamp.
        return {
          left: centerX - blockW / 2,
          right: centerX + blockW / 2,
          top: primary ? primaryY - primarySize : secondaryY - secondarySize,
          bottom: secondary ? secondaryY + Math.round(secondarySize * 0.3)
                            : primaryY + Math.round(primarySize * 0.3),
          natLeft: natCenterX - blockW / 2,
          natRight: natCenterX + blockW / 2,
          natTop: natTop,
          natBottom: natBottom
        };
      }

      // ---------- dragging the text (§2.2) ---------------------------------
      //
      // The preview canvas is FULL SIZE and DISPLAYED scaled down, so a
      // pointer position has to be mapped through the display scale.
      var textOffsetX = 0;
      var textOffsetY = 0;
      var lastBlock = null;
      var dragState = null;

      function canvasPoint(ev) {
        var rect = previewCanvas.getBoundingClientRect();
        if (!rect.width || !rect.height) return null;
        return {
          x: (ev.clientX - rect.left) * (previewCanvas.width / rect.width),
          y: (ev.clientY - rect.top) * (previewCanvas.height / rect.height)
        };
      }

      function hitBlock(p) {
        if (!lastBlock) return false;
        var rect = previewCanvas.getBoundingClientRect();
        if (!rect.width) return false;
        // A little slack, in canvas pixels.
        var pad = 10 * (previewCanvas.width / rect.width);
        return p.x >= lastBlock.left - pad && p.x <= lastBlock.right + pad &&
               p.y >= lastBlock.top - pad && p.y <= lastBlock.bottom + pad;
      }

      function onPointerDown(ev) {
        var p = canvasPoint(ev);
        if (!p || !hitBlock(p)) return;
        dragState = { startX: p.x, startY: p.y, offX: textOffsetX, offY: textOffsetY };
        previewCanvas.style.cursor = 'grabbing';
        if (previewCanvas.setPointerCapture) {
          try { previewCanvas.setPointerCapture(ev.pointerId); } catch (e) { /* ignore */ }
        }
        ev.preventDefault();
      }

      function onPointerMove(ev) {
        var p = canvasPoint(ev);
        if (!p) return;
        if (!dragState) {
          previewCanvas.style.cursor = hitBlock(p) ? 'grab' : 'default';
          return;
        }
        var nx = dragState.offX + (p.x - dragState.startX);
        var ny = dragState.offY + (p.y - dragState.startY);
        if (lastBlock) {
          // Never let the block leave the frame - a dragged-away text is
          // a lost text.
          nx = Math.min(previewCanvas.width - lastBlock.natRight,
                        Math.max(-lastBlock.natLeft, nx));
          ny = Math.min(previewCanvas.height - lastBlock.natBottom,
                        Math.max(-lastBlock.natTop, ny));
        }
        textOffsetX = Math.round(nx);
        textOffsetY = Math.round(ny);
        renderPreview();
      }

      function onPointerUp(ev) {
        if (!dragState) return;
        dragState = null;
        previewCanvas.style.cursor = 'default';
        if (previewCanvas.releasePointerCapture && ev.pointerId !== undefined) {
          try { previewCanvas.releasePointerCapture(ev.pointerId); } catch (e) { /* ignore */ }
        }
      }

      function resetTextPosition() {
        textOffsetX = 0;
        textOffsetY = 0;
        renderPreview();
      }
"""

OLD_RENDER = """        drawTextBlock(ctx, getSettings(), previewCanvas.width, previewCanvas.height);
      }
"""

NEW_RENDER = """        lastBlock = drawTextBlock(ctx, getSettings(), previewCanvas.width, previewCanvas.height);
        if (resetPositionBtn) {
          resetPositionBtn.disabled = (textOffsetX === 0 && textOffsetY === 0);
        }
      }
"""

OLD_ELEMENTS = """      var previewCanvas = document.getElementById('preview-canvas');
"""

NEW_ELEMENTS = """      var previewCanvas = document.getElementById('preview-canvas');
      var resetPositionBtn = document.getElementById('reset-position-btn');
"""

OLD_TAIL = """      refreshUI();
    });
    </script>
"""

NEW_TAIL = """      // §2.2 - drag the text straight on the photo.
      previewCanvas.addEventListener('pointerdown', onPointerDown);
      previewCanvas.addEventListener('pointermove', onPointerMove);
      previewCanvas.addEventListener('pointerup', onPointerUp);
      previewCanvas.addEventListener('pointercancel', onPointerUp);
      previewCanvas.addEventListener('pointerleave', function () {
        if (!dragState) previewCanvas.style.cursor = 'default';
      });
      if (resetPositionBtn) {
        resetPositionBtn.addEventListener('click', resetTextPosition);
      }

      refreshUI();
    });
    </script>
"""


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
    text = path.read_text(encoding="utf-8")
    changes = 0
    m = POSITION_RE.search(text)
    if m:
        # Keep the indentation of the opening line.
        line_start = text.rfind("\n", 0, m.start()) + 1
        indent = text[line_start:m.start()]
        block = POSITION_BLOCK.replace("\n", "\n" + indent)
        text = text[:m.start()] + block + text[m.end():]
        changes += 1
    elif K_HINT not in text:
        raise SystemExit("[FAIL] %s: the position control was not found" % path)
    text, n = patch_canvas(text)
    changes += n
    if changes and not dry:
        write_atomic(path, text)
    return changes


def patch_js(path: Path, dry: bool) -> int:
    text = path.read_text(encoding="utf-8")
    changes = 0
    for old, new, marker, what in (
            (OLD_SETTINGS, NEW_SETTINGS, "textX: textOffsetX,", "the settings"),
            (OLD_DRAW, NEW_DRAW, "function resetTextPosition()", "drawTextBlock"),
            (OLD_RENDER, NEW_RENDER, "lastBlock = drawTextBlock(", "the preview render"),
            (OLD_ELEMENTS, NEW_ELEMENTS, "var resetPositionBtn =", "the element handles"),
            (OLD_TAIL, NEW_TAIL, "previewCanvas.addEventListener('pointerdown'", "the drag wiring"),
    ):
        if marker in text:
            continue
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
