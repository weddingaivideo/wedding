#!/usr/bin/env python3
"""
Give the crop tool a real, draggable crop frame.

WHY THIS EXISTS (found 2026-11-09)
---------------------------------
The crop tool could only ever cut a FIXED rectangle: computeCrop() took the
source size and the target aspect ratio and returned the largest matching
window, biased toward an off-centre "subject centroid" heuristic. The page
even admitted it in its own FAQ:

    "Not in this tool - it's a batch one-click cropper designed for the
     common case. For full manual control with draggable crop boxes, we
     recommend using the source image's photo editor."

For a wedding photo that is the wrong answer. The couple wants THEIR
subject in the frame - the bride's hands, the groom's face, the bouquet -
and the heuristic cannot know where that is.

WHY THIS IS NOT CROPPER.JS
--------------------------
Cropper.js v2 (the version that would have been used) is a Web Components
rewrite: its UI lives in shadow DOM, the package ships NO stylesheet, and
the bundle contains ZERO aria-label / Reset / Confirm / Cancel strings -
so its drag handles would have no accessible name and could not be
translated into the 11 languages this site ships.

So the frame is implemented natively: a canvas, a shaded overlay, four
corner handles and a pointer-driven drag. It adds ZERO bytes to the page,
is fully localisable through the existing data-i18n mechanism, and works
with mouse, touch and pen through Pointer Events.

THE BEHAVIOUR
-------------
* A crop stage appears once photos are loaded. It shows one photo at a
  time with Previous / Next.
* The frame always matches the selected aspect ratio. Dragging a corner
  keeps the ratio; dragging inside the frame moves it.
* A photo the user did not touch keeps the old automatic crop, so the
  batch flow still works exactly as before.
* The manual crop is stored in SOURCE pixel coordinates and is applied at
  the same resolution as the automatic one.
* If the aspect ratio is changed after a manual crop was made, that crop
  is ignored (it would distort the photo) and the automatic crop is used.

The inline JavaScript is changed in the ENGLISH SOURCE only; the localized
copies receive it through scripts/propagate-tool-js.py.

Usage:  python scripts/patch-crop-tool.py [--dry-run]
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
SLUG = "crop-wedding-photo-for-reels"

# ---------------------------------------------------------------------------
# 1. The new stage markup. Identical in every language: every user-visible
#    string is a data-i18n binding, so the middleware translates it.
# ---------------------------------------------------------------------------

STAGE_MARKUP = """
                <div class="wa-tool-card wa-crop-stage-card" id="crop-stage-card" hidden>
                    <h2 data-i18n="tools.copy.cropStageTitle.zzzzzz6c01">Adjust the crop</h2>
                    <p class="wa-crop-stage-hint" data-i18n="tools.copy.cropStageHint.zzzzzz6c02">Drag the corners to frame the shot. Photos you leave untouched keep the automatic centre crop.</p>
                    <div class="wa-crop-stage" id="crop-stage">
                        <canvas id="crop-canvas" width="8" height="8" role="img" aria-label="Crop area" data-i18n-attr="aria-label:tools.copy.cropStageHint.zzzzzz6c02"></canvas>
                    </div>
                    <div class="wa-crop-stage-bar">
                        <button type="button" class="btn btn-secondary btn-small" id="crop-prev-btn" data-i18n="tools.copy.cropPrev.zzzzzz6c03">Previous photo</button>
                        <span class="wa-crop-stage-pos" id="crop-stage-pos" aria-live="polite"></span>
                        <button type="button" class="btn btn-secondary btn-small" id="crop-next-btn" data-i18n="tools.copy.cropNext.zzzzzz6c04">Next photo</button>
                        <button type="button" class="btn btn-secondary btn-small" id="crop-reset-btn" data-i18n="tools.copy.cropReset.zzzzzz4f2a">Reset</button>
                    </div>
                </div>
"""

# ---------------------------------------------------------------------------
# 2. The FAQ answer that used to say a manual crop was impossible.
# ---------------------------------------------------------------------------

FAQ = {
    "en": "<p>Yes. The Crop step now opens a drag-and-drop frame: drag the corners to frame the shot yourself, then press Crop. Every photo you did not touch keeps the automatic centre crop, so the batch flow still works.</p>",
    "zh": "<p>可以。现在「裁剪」这一步会打开一个可拖拽的取景框：自己拖动四角框住想保留的画面，然后点击裁剪。没有动过的照片仍使用自动居中裁剪，批量流程照旧。</p>",
    "es": "<p>Sí. El paso Recortar ahora abre un marco que puedes arrastrar: mueve las esquinas para encuadrar la foto tú mismo y pulsa Recortar. Las fotos que no toques siguen usando el recorte automático centrado, así que el flujo por lotes funciona igual.</p>",
    "fr": "<p>Oui. L'étape Recadrer ouvre désormais un cadre glissable : déplacez les coins pour cadrer la photo vous-même, puis cliquez sur Recadrer. Les photos que vous ne touchez pas conservent le recadrage automatique centré, donc le traitement par lots fonctionne comme avant.</p>",
    "de": "<p>Ja. Der Schritt Zuschneiden öffnet jetzt einen ziehbaren Rahmen: Verschieben Sie die Ecken, um das Motiv selbst einzufassen, und klicken Sie dann auf Zuschneiden. Fotos, die Sie nicht anfassen, behalten den automatischen mittigen Beschnitt, der Stapelablauf funktioniert also wie bisher.</p>",
    "pt": "<p>Sim. A etapa Recortar agora abre uma moldura que você pode arrastar: mova os cantos para enquadrar a foto como quiser e clique em Recortar. As fotos que você não mexer continuam com o recorte automático centralizado, então o fluxo em lote continua igual.</p>",
    "ja": "<p>できます。「クロップ」の手順でドラッグできる枠が開くようになりました。四隅をドラッグして自分で構図を決めてから「クロップ」を押してください。触らなかった写真は自動中央クロップのままなので、一括処理の流れは変わりません。</p>",
    "ru": "<p>Да. На шаге «Обрезать» теперь открывается рамка, которую можно перетаскивать: сдвиньте углы, чтобы самим выбрать кадр, затем нажмите «Обрезать». Фото, к которым вы не прикасались, по-прежнему обрезаются автоматически по центру, так что пакетная обработка работает как раньше.</p>",
    "ar": "<p>نعم. تفتح خطوة «القص» الآن إطارًا يمكن سحبه: اسحب الزوايا لتأطير الصورة بنفسك ثم اضغط «قص». أما الصور التي لم تلمسها فتبقى بالقص التلقائي المتمركز، لذا يظل الدفع على دفعات يعمل كما هو.</p>",
    "th": "<p>ได้ครับ ขั้นตอน «ครอป» จะเปิดกรอบที่ลากได้: ลากมุมเพื่อเลือกส่วนที่ต้องการเอง แล้วกด «ครอป» ส่วนรูปที่คุณไม่ได้แตะจะยังใช้การครอปอัตโนมัติแบบกึ่งกลาง ดังนั้นขั้นตอนแบบทำทีละหลายรูปยังทำงานเหมือนเดิม</p>",
    "hi": "<p>हाँ। अब “क्रॉप” चरण में खींचकर घुमाने योग्य फ़्रेम खुलता है: कोने खींचकर फ़ोटो का फ्रेम खुद तय करें, फिर “क्रॉप” दबाएँ। जिन फ़ाइलों को आपने छुआ नहीं, वे स्वतः केंद्रित क्रॉप ही रहती हैं, इसलिए बैच प्रवाह पहले जैसा ही चलता है।</p>",
}

# ---------------------------------------------------------------------------
# 3. The English inline script: the pieces that change.
# ---------------------------------------------------------------------------

JS_OLD_VARS = """      var summaryEl = document.getElementById('summary');

      var files = [];
"""
JS_NEW_VARS = """      var summaryEl = document.getElementById('summary');

      var files = [];

      // ---------- interactive crop stage -----------------------------------
      var stageCard = document.getElementById('crop-stage-card');
      var stageCanvas = document.getElementById('crop-canvas');
      var stagePos = document.getElementById('crop-stage-pos');
      var stagePrevBtn = document.getElementById('crop-prev-btn');
      var stageNextBtn = document.getElementById('crop-next-btn');
      var stageResetBtn = document.getElementById('crop-reset-btn');
      var stageIndex = 0;
      var stageImg = null;      // the photo currently on the stage
      var stageRect = null;      // {x,y,w,h} in CANVAS pixels
      var stageScale = 1;         // source pixels per canvas pixel
      var dragMode = null;        // 'move' | 'nw' | 'ne' | 'sw' | 'se' | 'new'
      var dragStart = null;
      var HANDLE = 16;            // corner handle hit radius, canvas px
"""

JS_OLD_REFRESH = """        if (window.weddingAITool && window.weddingAITool.renderFileList) {
          window.weddingAITool.renderFileList(list, files, function () {});
          Array.prototype.forEach.call(list.children, function (row, i) {
            window.weddingAITool.updateFileRow(row, files[i]);
          });
        }
      }
"""
JS_NEW_REFRESH = """        if (window.weddingAITool && window.weddingAITool.renderFileList) {
          window.weddingAITool.renderFileList(list, files, function () {});
          Array.prototype.forEach.call(list.children, function (row, i) {
            window.weddingAITool.updateFileRow(row, files[i]);
          });
        }
        updateStageBar();
      }
"""

JS_OLD_ADD = """        if (files.length === 0) { window.weddingAITool.toast('No supported files. Try a JPG, PNG, or WebP.', 'error'); return; }
        files.forEach(function (entry, idx) {
          if (entry.previewUrl) return;
          entry.previewUrl = URL.createObjectURL(entry.inputFile);
        });
        refreshUI();
      }
"""
JS_NEW_ADD = """        if (files.length === 0) { window.weddingAITool.toast('No supported files. Try a JPG, PNG, or WebP.', 'error'); return; }
        files.forEach(function (entry, idx) {
          if (entry.previewUrl) return;
          entry.previewUrl = URL.createObjectURL(entry.inputFile);
        });
        refreshUI();
        showStage();
      }
"""

JS_OLD_CLEAR = """        files = [];
        summaryEl.hidden = true;
        refreshUI();
      }
"""
JS_NEW_CLEAR = """        files = [];
        summaryEl.hidden = true;
        stageIndex = 0;
        stageRect = null;
        refreshUI();
        showStage();
      }
"""

JS_OLD_CROP = """          var crop = computeCrop(W, H, settings.aspect.w, settings.aspect.h, settings.smart);
"""
JS_NEW_CROP = """          // A manual crop wins, but only when it still matches the aspect
          // ratio that is selected now - otherwise the photo would be
          // stretched, so the automatic crop is used instead.
          var crop = null;
          if (entry.crop && Math.abs(entry.cropAr - settings.aspect.w / settings.aspect.h) < 0.0001) {
            crop = entry.crop;
          }
          if (!crop) {
            crop = computeCrop(W, H, settings.aspect.w, settings.aspect.h, settings.smart);
          }
"""

JS_OLD_REMOVE = """          if (f && f.previewUrl) URL.revokeObjectURL(f.previewUrl);
          files.splice(idx, 1);
          refreshUI();
        }
      });
"""
JS_NEW_REMOVE = """          if (f && f.previewUrl) URL.revokeObjectURL(f.previewUrl);
          files.splice(idx, 1);
          refreshUI();
          showStage();
        }
      });
"""

JS_OLD_WIRE = """      qualityEl.addEventListener('input', function () { qualityVal.textContent = qualityEl.value; });
"""
JS_NEW_WIRE = """      // ---------- the crop stage implementation ----------------------------
      //
      // A canvas, a shaded overlay, four corner handles and pointer drag.
      // The frame always matches the selected aspect ratio; a photo the user
      // did not touch keeps the automatic crop.
      function stageEntries() {
        return files.filter(function (f) { return f.inputFile; });
      }

      function stageAspect() {
        var a = getCurrentSettings().aspect;
        return a.w / a.h;
      }

      function clampRect(r, ar) {
        var cw = stageCanvas.width, ch = stageCanvas.height;
        var w = Math.min(Math.max(r.w, 24), cw);
        var h = w / ar;
        if (h > ch) { h = ch; w = h * ar; }
        var x = Math.min(Math.max(r.x, 0), cw - w);
        var y = Math.min(Math.max(r.y, 0), ch - h);
        return { x: x, y: y, w: w, h: h };
      }

      function pointerPos(e) {
        var rect = stageCanvas.getBoundingClientRect();
        if (!rect.width || !rect.height) return { x: 0, y: 0 };
        return {
          x: (e.clientX - rect.left) * (stageCanvas.width / rect.width),
          y: (e.clientY - rect.top) * (stageCanvas.height / rect.height)
        };
      }

      function hitTest(p) {
        if (!stageRect) return 'new';
        var r = stageRect;
        var near = function (x, y, hx, hy) {
          return Math.abs(p.x - hx) <= HANDLE && Math.abs(p.y - hy) <= HANDLE;
        };
        if (near(p.x, p.y, r.x, r.y)) return 'nw';
        if (near(p.x, p.y, r.x + r.w, r.y)) return 'ne';
        if (near(p.x, p.y, r.x, r.y + r.h)) return 'sw';
        if (near(p.x, p.y, r.x + r.w, r.y + r.h)) return 'se';
        if (p.x >= r.x && p.x <= r.x + r.w && p.y >= r.y && p.y <= r.y + r.h) return 'move';
        return 'new';
      }

      function anchorFor(mode, r) {
        if (mode === 'nw') return { x: r.x + r.w, y: r.y + r.h };
        if (mode === 'ne') return { x: r.x, y: r.y + r.h };
        if (mode === 'sw') return { x: r.x + r.w, y: r.y };
        return { x: r.x, y: r.y };
      }

      function rectFromAnchor(anchor, p, ar) {
        var dx = Math.abs(p.x - anchor.x);
        var dy = Math.abs(p.y - anchor.y);
        var w, h;
        if (dx > dy * ar) { w = dx; h = w / ar; }
        else { h = dy; w = h * ar; }
        w = Math.max(w, 24);
        h = Math.max(h, 24);
        var x = (p.x < anchor.x) ? anchor.x - w : anchor.x;
        var y = (p.y < anchor.y) ? anchor.y - h : anchor.y;
        return clampRect({ x: x, y: y, w: w, h: h }, ar);
      }

      function drawStage() {
        var ctx = stageCanvas.getContext('2d');
        var cw = stageCanvas.width, ch = stageCanvas.height;
        ctx.clearRect(0, 0, cw, ch);
        var img = stageImg;
        if (!img) return;
        ctx.drawImage(img, 0, 0, cw, ch);
        if (!stageRect) return;
        var r = stageRect;
        // shade everything OUTSIDE the frame
        ctx.save();
        ctx.fillStyle = 'rgba(0,0,0,0.55)';
        ctx.beginPath();
        ctx.rect(0, 0, cw, ch);
        ctx.rect(r.x, r.y, r.w, r.h);
        ctx.fill('evenodd');
        ctx.restore();
        // rule of thirds
        ctx.strokeStyle = 'rgba(255,255,255,0.45)';
        ctx.lineWidth = 1;
        for (var i = 1; i <= 2; i++) {
          ctx.beginPath();
          ctx.moveTo(r.x + r.w * i / 3, r.y);
          ctx.lineTo(r.x + r.w * i / 3, r.y + r.h);
          ctx.moveTo(r.x, r.y + r.h * i / 3);
          ctx.lineTo(r.x + r.w, r.y + r.h * i / 3);
          ctx.stroke();
        }
        // frame
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.strokeRect(r.x + 1, r.y + 1, r.w - 2, r.h - 2);
        // corner handles
        ctx.fillStyle = '#ffffff';
        var corners = [[r.x, r.y], [r.x + r.w, r.y], [r.x, r.y + r.h], [r.x + r.w, r.y + r.h]];
        for (var c = 0; c < corners.length; c++) {
          ctx.fillRect(corners[c][0] - 6, corners[c][1] - 6, 12, 12);
        }
      }

      function updateStageBar() {
        var entries = stageEntries();
        if (!stagePos) return;
        var T = window.weddingAITool.t;
        if (entries.length === 0) {
          stagePos.textContent = '';
          return;
        }
        var entry = entries[stageIndex];
        var manual = !!(entry && entry.crop);
        var txt = manual
          ? T('cropPosManual', 'Photo {n} of {m} - manual crop')
          : T('cropPos', 'Photo {n} of {m}');
        stagePos.textContent = T
          ? String(txt).replace(/\\{(\\w+)\\}/g, function (m0, k) {
              return k === 'n' ? String(stageIndex + 1) : k === 'm' ? String(entries.length) : m0;
            })
          : '';
        if (stagePrevBtn) stagePrevBtn.disabled = stageIndex <= 0;
        if (stageNextBtn) stageNextBtn.disabled = stageIndex >= entries.length - 1;
      }

      function saveStageCrop() {
        var entries = stageEntries();
        var entry = entries[stageIndex];
        if (!entry || !stageRect) return;
        // store the frame in SOURCE pixels so the batch crop is pixel-exact
        entry.crop = {
          x: Math.round(stageRect.x * stageScale),
          y: Math.round(stageRect.y * stageScale),
          w: Math.round(stageRect.w * stageScale),
          h: Math.round(stageRect.h * stageScale)
        };
        entry.cropAr = stageAspect();
        updateStageBar();
      }

      async function showStage() {
        if (!stageCard || !stageCanvas) return;
        var entries = stageEntries();
        if (entries.length === 0) {
          stageCard.hidden = true;
          stageImg = null;
          stageRect = null;
          updateStageBar();
          return;
        }
        stageCard.hidden = false;
        if (stageIndex > entries.length - 1) stageIndex = entries.length - 1;
        if (stageIndex < 0) stageIndex = 0;
        var entry = entries[stageIndex];
        try {
          if (!entry.stageImg) {
            var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
            entry.stageImg = loaded.img;
            entry.stageUrl = loaded.url;
          }
          stageImg = entry.stageImg;
          var w = stageImg.naturalWidth, h = stageImg.naturalHeight;
          if (!w || !h) { stageCard.hidden = true; return; }
          var cw = Math.min(w, 1400);
          var ch = Math.round(h * cw / w);
          stageCanvas.width = cw;
          stageCanvas.height = ch;
          stageScale = w / cw;
          if (entry.crop) {
            stageRect = {
              x: entry.crop.x / stageScale,
              y: entry.crop.y / stageScale,
              w: entry.crop.w / stageScale,
              h: entry.crop.h / stageScale
            };
          } else {
            var auto = computeCrop(cw, ch, getCurrentSettings().aspect.w, getCurrentSettings().aspect.h, !!smartEl.checked);
            stageRect = clampRect({ x: auto.cropX, y: auto.cropY, w: auto.cropW, h: auto.cropH }, stageAspect());
          }
          drawStage();
        } catch (err) {
          stageCard.hidden = true;
        }
        updateStageBar();
      }

      stageCanvas.addEventListener('pointerdown', function (e) {
        if (!stageRect) return;
        e.preventDefault();
        try { stageCanvas.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
        var p = pointerPos(e);
        dragMode = hitTest(p);
        dragStart = { p: p, rect: { x: stageRect.x, y: stageRect.y, w: stageRect.w, h: stageRect.h } };
        if (dragMode === 'new') {
          dragStart.rect = { x: p.x, y: p.y, w: 24, h: 24 };
        }
      });

      stageCanvas.addEventListener('pointermove', function (e) {
        if (!dragMode) return;
        var p = pointerPos(e);
        var ar = stageAspect();
        if (dragMode === 'move') {
          var dx = p.x - dragStart.p.x;
          var dy = p.y - dragStart.p.y;
          var r = dragStart.rect;
          stageRect = clampRect({ x: r.x + dx, y: r.y + dy, w: r.w, h: r.h }, ar);
        } else if (dragMode === 'new') {
          stageRect = rectFromAnchor(dragStart.p, p, ar);
        } else {
          stageRect = rectFromAnchor(anchorFor(dragMode, dragStart.rect), p, ar);
        }
        drawStage();
      });

      function endDrag(e) {
        if (!dragMode) return;
        dragMode = null;
        try { stageCanvas.releasePointerCapture(e.pointerId); } catch (err) { /* ignore */ }
        saveStageCrop();
      }
      stageCanvas.addEventListener('pointerup', endDrag);
      stageCanvas.addEventListener('pointercancel', endDrag);

      if (stagePrevBtn) {
        stagePrevBtn.addEventListener('click', function () {
          if (stageIndex > 0) { stageIndex--; showStage(); }
        });
      }
      if (stageNextBtn) {
        stageNextBtn.addEventListener('click', function () {
          var entries = stageEntries();
          if (stageIndex < entries.length - 1) { stageIndex++; showStage(); }
        });
      }
      if (stageResetBtn) {
        stageResetBtn.addEventListener('click', function () {
          var entries = stageEntries();
          var entry = entries[stageIndex];
          if (entry) { entry.crop = null; entry.cropAr = 0; }
          showStage();
        });
      }
      // changing the aspect re-frames the current photo
      aspectEl.addEventListener('change', function () {
        var entries = stageEntries();
        var entry = entries[stageIndex];
        if (entry && entry.crop) { entry.crop = null; entry.cropAr = 0; }
        showStage();
      });

      qualityEl.addEventListener('input', function () { qualityVal.textContent = qualityEl.value; });
"""

JS_REPLACEMENTS = [
    (JS_OLD_VARS, JS_NEW_VARS),
    (JS_OLD_REFRESH, JS_NEW_REFRESH),
    (JS_OLD_ADD, JS_NEW_ADD),
    (JS_OLD_CLEAR, JS_NEW_CLEAR),
    (JS_OLD_CROP, JS_NEW_CROP),
    (JS_OLD_REMOVE, JS_NEW_REMOVE),
    (JS_OLD_WIRE, JS_NEW_WIRE),
]

# the stage image cache lives next to the other per-file state
JS_OLD_FILES = "      var stageIndex = 0;"
JS_NEW_FILES = "      var stageImg = null;      // the photo currently on the stage\n      var stageIndex = 0;"


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmpwrite")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def patch_markup(text: str, lang: str):
    """Insert the crop stage markup after the file list."""
    if 'id="crop-stage-card"' in text:
        return text, 0
    anchor = '<div class="wa-tool-file-list" id="file-list" hidden></div>'
    if anchor not in text:
        raise SystemExit(f"[FAIL] {lang}: the file-list anchor was not found")
    return text.replace(anchor, anchor + STAGE_MARKUP, 1), 1


def patch_faq(text: str, lang: str):
    """Replace the answer of the LAST <details> (the manual-crop question)."""
    details = list(re.finditer(r"(?s)<details\b[^>]*>.*?</details>", text))
    if not details:
        raise SystemExit(f"[FAIL] {lang}: no <details> found")
    d = details[-1]
    body = d.group(0)
    m = re.search(r"(?s)(<details\b[^>]*>)(.*?)(</details>)", body)
    inner = m.group(2)
    pm = re.search(r"(?s)<p\b[^>]*>.*?</p>", inner)
    if not pm:
        raise SystemExit(f"[FAIL] {lang}: the last FAQ has no <p>")
    new_inner = inner[:pm.start()] + FAQ[lang] + inner[pm.end():]
    new_body = m.group(1) + new_inner + m.group(3)
    return text[:d.start()] + new_body + text[d.end():], 1


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
        new, nmarkup = patch_markup(original, lang)
        new, nfaq = patch_faq(new, lang)
        changes = [f"markup x{nmarkup}", f"faq x{nfaq}"]

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
        tmp = Path(os.environ.get("TEMP", ".")) / "crop_inline_check.js"
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
