#!/usr/bin/env python3
"""
Face-aware cropping for the crop tool (§2.11).

WHAT IT DOES
------------
Until now the crop tool's automatic crop was a FIXED heuristic: shift the
crop window 60% down the Y axis for a landscape source, keep the centre for
a portrait source. The page said so honestly ("it is a heuristic, not face
detection"), but it also meant the tool could not keep a couple's faces in
frame when they were not where the convention says they should be.

This patch adds a real, on-device face detector:

  * a new "Face-aware framing" switch in step 2,
  * the detector (face-api.js + the tiny face detector model, ~840 KB)
    downloaded ONLY when the visitor switches it on,
  * every photo's crop frame then follows the actual faces,
  * the faces are drawn on the preview so the frame is not a black box,
  * a photo with no detectable face keeps the old off-center bias.

WHY THE LIBRARY AND NOT FACE-API'S BIGGER SIBLINGS
--------------------------------------------------
Measured on this machine:

    @mediapipe/tasks-vision@1.2.2   156 KB JS + 14.6 MB of WASM + a model
    @mediapipe/face_detection@0.4   5.8 MB of WASM + 229 KB of model
    face-api.js@0.22.2              648 KB of JS + 189 KB of model

face-api.js is the only one of the three that fits this site's rules: the
shipped bundle contains ZERO `eval(`, ZERO `new Function` and ZERO
`WebAssembly`, so it runs under the existing CSP with no policy change, and
it has no UI strings, so it adds no translation debt.

THE LOCALIZED COPIES
---------------------
The eleven pages share one HTML structure but not one prose: the localized
copies carry machine-translated paragraphs, so nothing here matches on
English text. Every anchor below is structural:

  * the off-center control is found by `id="smart-offset"`,
  * the "why off-center" paragraph is found by the "85%" figure it quotes
    (the Arabic copy writes it in Arabic-Indic digits, so the pattern
    accepts both),
  * the HowTo JSON-LD step is found by `"position":3`.

Usage
-----
    python scripts/patch-crop-face-aware.py            # apply
    python scripts/patch-crop-face-aware.py --dry-run

Afterwards ALWAYS run:
    python scripts/propagate-tool-js.py
    python scripts/check-tool-script-syntax.py
    python scripts/build-crop-face-i18n-patch.py
    python scripts/add-tool-ui-keys.py .tmp/patch-crop-face-i18n.json
    python scripts/add-shards-for-keys.py i18n/<lang>.json i18n/<lang>.manifest.json
    python scripts/verify-i18n-shards.py
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = "crop-wedding-photo-for-reels"
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

P = "tools.crop-wedding-photo-for-reels."

# --- the i18n keys ---------------------------------------------------------

K_BIAS_LABEL = P + "label_text.off_center_bias.9a8b7c6d"
K_BIAS_HINT = P + "small_text.a6b24d1f"
K_FACE_LABEL = P + "label_text.face_aware_framing.5d4c3b2a"
K_FACE_HINT = P + "small_text.face_aware_hint.6e7f8091"
K_WHY = P + "p_text.why_off_center_beats_center.1b2c3d4e"
K_FACE_PROSE = P + "p_text.face_aware_framing.2f3e4d5c"

# The detector's own script. Kept in its own file so only the crop tool
# pays for it, and so it has its own cache stamp.
DETECTOR_TAG = '<script defer src="/js/tools/face-detector.js?v=1.0.0"></script>'

# --- the markup ------------------------------------------------------------

# The canonical off-center control + the new face-aware control.
#
# Both are the ENGLISH source text plus a data-i18n key: the static fallback
# is English and the rendered page is the visitor's language. The `<small>`
# sits OUTSIDE the <span> on purpose - a data-i18n element replaces its
# whole inner html, so a nested <small> would be destroyed.
CONTROLS = """<div class="wa-tool-control">
<label class="wa-tool-toggle">
<input type="checkbox" id="smart-offset" checked>
<span data-i18n="{bias_label}">Off-center bias &mdash; automatic starting position</span>
</label>
<small data-i18n="{bias_hint}">Sets where the crop frame starts: 60% down the Y axis for landscape sources (where wedding couples typically stand) and true center for portrait sources. It is a fixed heuristic, not a measurement &mdash; switch on Face-aware framing below to have the crop follow the actual faces. Drag the frame in step 3 to override it for any photo. ON for landscape sources, OFF if your source is already a tight portrait composition.</small>
</div>
<div class="wa-tool-control">
<label class="wa-tool-toggle" for="face-aware">
<input type="checkbox" id="face-aware">
<span data-i18n="{face_label}">Face-aware framing &mdash; optional</span>
</label>
<small data-i18n="{face_hint}">Finds the faces in each photo and moves the crop frame so every face stays inside it. The detector (about 840&nbsp;KB) downloads once, the first time you switch this on, and then runs entirely on your device &mdash; your photos are never uploaded. A photo with no detectable face keeps the off-center bias.</small>
<small id="face-status" class="wa-face-status"></small>
</div>""".format(
    bias_label=K_BIAS_LABEL,
    bias_hint=K_BIAS_HINT,
    face_label=K_FACE_LABEL,
    face_hint=K_FACE_HINT,
)

# The corrected "why off-center" paragraph. The old one said the heuristic
# used "no face detection, no machine learning", which stops being true the
# moment the visitor can switch the detector on.
WHY_PARAGRAPH = (
    '<p data-i18n="' + K_WHY + '">A wedding photo is almost never "subject at exact center." '
    "Composition rules (rule of thirds, leading lines) push the subject off-center "
    "&mdash; usually slightly below center on a horizontal frame. A naive center-crop "
    "system blindly halves the image and ships it, often cutting the bride&rsquo;s face "
    "out of the frame entirely. The off-center heuristic used here is intentionally "
    "simple &mdash; a fixed bias, not a measurement &mdash; but it matches the "
    "photographic convention well enough to handle ~85% of wedding shots correctly "
    "on the first try. When you want the frame to follow the real faces instead of "
    "the convention, switch on Face-aware framing.</p>"
)

# The new paragraph that explains the face-aware mode.
FACE_PROSE = (
    '<p data-i18n="' + K_FACE_PROSE + '">The off-center bias is a guess about where the couple usually '
    "stands. If you would rather the crop followed the actual people in the frame, "
    "switch on <strong>Face-aware framing</strong>: the tool finds the faces in each "
    "photo and slides the crop window so that every face stays inside it, with a "
    "little breathing room around them. The detector is a small model that runs in "
    "your browser &mdash; the photos are read on your device and never uploaded &mdash; "
    "and a photo with no detectable face simply keeps the off-center bias.</p>"
)

# The HowTo step that used to say the tool does no face detection.
STEP3_NAME = "Turn on Off-center bias (recommended ON) and, optionally, Face-aware framing"
STEP3_TEXT = (
    "Off-center bias shifts the crop window toward where wedding couples usually "
    "stand (60% down the Y axis for landscape sources, true center for portrait "
    "sources) - it is a fixed heuristic, not a measurement. Switch on Face-aware "
    "framing to have the crop follow the actual faces in each photo: the detector "
    "runs on your device and never uploads anything. Either way, check the preview "
    "for each photo."
)

# --- matchers --------------------------------------------------------------

# The "85%" figure, in both Western and Arabic-Indic digits.
PCT85 = re.compile("[85٨][5٥]\\s*[%٪]")

COMMON_SCRIPT_RE = re.compile(
    r'(<script defer src="/js/tools/common\.js\?v=[^"]*"></script>)')


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


def find_control(text: str, marker: str):
    """Return (start, end) of the <div class="wa-tool-control"> that holds
    `marker`. The control holds no nested <div>, so the first </div> after
    the marker closes it."""
    i = text.find(marker)
    if i < 0:
        return None
    start = text.rfind('<div class="wa-tool-control">', 0, i)
    if start < 0:
        return None
    end = text.find("</div>", i)
    if end < 0:
        return None
    return start, end + len("</div>")


def find_pct_paragraph(text: str):
    """Return (start, end) of the <p> that quotes the 85% figure."""
    for m in re.finditer(r"<p\b[^>]*>((?:(?!</p>).)*?)</p>", text, re.S):
        if PCT85.search(m.group(1)):
            return m.start(), m.end()
    return None


def replace_paragraph(text: str, span, replacement: str) -> str:
    return text[:span[0]] + replacement + text[span[1]:]


def patch_html(text: str, english: bool) -> tuple:
    changes = 0

    # 1. the detector script
    if DETECTOR_TAG not in text:
        m = COMMON_SCRIPT_RE.search(text)
        if not m:
            raise SystemExit("[FAIL] the common.js script tag was not found")
        text = text[:m.end()] + "\n    " + DETECTOR_TAG + text[m.end():]
        changes += 1

    # 2. the off-center control + the new face-aware control
    span = find_control(text, 'id="smart-offset"')
    if span is None:
        raise SystemExit("[FAIL] the off-center control was not found")
    if 'id="face-aware"' not in text[span[0]:span[1] + 4000]:
        indent = ""
        line_start = text.rfind("\n", 0, span[0]) + 1
        indent = text[line_start:span[0]]
        block = CONTROLS.replace("\n", "\n" + indent)
        text = text[:span[0]] + block + text[span[1]:]
        changes += 1

    # 3. the "why off-center" paragraph + the new face-aware paragraph
    span = find_pct_paragraph(text)
    if span is None:
        raise SystemExit("[FAIL] the 85% paragraph was not found")
    body = text[span[0]:span[1]]
    if K_WHY not in body:
        text = replace_paragraph(text, span, WHY_PARAGRAPH + "\n" + FACE_PROSE)
        changes += 1

    # 4. the HowTo JSON-LD step. Only the ENGLISH page carries the claim
    #    that must change ("it is a heuristic, not face detection"); the
    #    zh / pt / ru pages have their own translated HowTo block that never
    #    said that, and the other seven pages have no HowTo block at all.
    if english:
        m = re.search(r'("position":3,)"name":"[^"]*","text":"[^"]*"', text)
        if m:
            new = m.group(1) + '"name":%s,"text":%s' % (
                json.dumps(STEP3_NAME), json.dumps(STEP3_TEXT))
            text = text[:m.start()] + new + text[m.end():]
            changes += 1

        # The SoftwareApplication description and feature list.
        old_desc = ("with an off-center bias heuristic (lower-center for landscape, "
                    "true-center for portrait).")
        new_desc = ("with an off-center bias heuristic (lower-center for landscape, "
                    "true-center for portrait) and an optional on-device face "
                    "detector that keeps every detected face inside the crop.")
        if old_desc in text:
            text = text.replace(old_desc, new_desc, 1)
            changes += 1
        old_feat = '"Off-center bias heuristic",'
        new_feat = '"Off-center bias heuristic","On-device face detection (optional)",'
        # The guard matters: old_feat is a SUBSTRING of new_feat, so a plain
        # "if old_feat in text" check would append the entry a second time
        # on every re-run.
        if old_feat in text and "On-device face detection (optional)" not in text:
            text = text.replace(old_feat, new_feat, 1)
            changes += 1

    return text, changes


# --- the inline JS (English page only) -------------------------------------

OLD_ELEMENTS = """      var smartEl = document.getElementById('smart-offset');
"""

NEW_ELEMENTS = """      var smartEl = document.getElementById('smart-offset');
      var faceAwareEl = document.getElementById('face-aware');
      var faceStatusEl = document.getElementById('face-status');
"""

OLD_SETTINGS = """          smart: !!smartEl.checked,
"""

NEW_SETTINGS = """          smart: !!smartEl.checked,
          faceAware: !!faceAwareEl.checked,
"""

OLD_CROP_END = """        return { cropX: cropX, cropY: cropY, cropW: cropW, cropH: cropH };
      }

      async function processOne(entry, settings) {
"""

NEW_CROP_END = """        return { cropX: cropX, cropY: cropY, cropW: cropW, cropH: cropH };
      }

      // ---------- face-aware framing (§2.11) --------------------------------
      //
      // computeCrop() picks a FIXED bias (60% down for a landscape source).
      // computeCropWithFaces() keeps the SAME window size - the aspect ratio
      // is locked either way - and only decides WHERE it sits, so that every
      // detected face ends up inside the frame.
      //
      // The faces are placed horizontally centred, and vertically in the
      // upper part of the frame, which is where a 9:16 platform keeps its
      // safe zone. Both axes are then clamped so that no face is cut off.
      function computeCropWithFaces(W, H, targetW, targetH, faces) {
        var tgtAR = targetW / targetH;
        var cropW, cropH;
        if (W / H > tgtAR) {
          cropH = H;
          cropW = H * tgtAR;
        } else {
          cropW = W;
          cropH = W / tgtAR;
        }
        if (!faces || !faces.length) {
          return { cropX: 0, cropY: 0, cropW: Math.round(cropW), cropH: Math.round(cropH) };
        }
        var x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
        for (var i = 0; i < faces.length; i++) {
          var b = faces[i];
          if (b.x < x0) x0 = b.x;
          if (b.y < y0) y0 = b.y;
          if (b.x + b.w > x1) x1 = b.x + b.w;
          if (b.y + b.h > y1) y1 = b.y + b.h;
        }
        // A little breathing room around the faces.
        var m = Math.max(2, cropW * 0.05);
        var faceCx = (x0 + x1) / 2;
        var faceCy = (y0 + y1) / 2;

        var cropX;
        if (x1 - x0 + 2 * m > cropW) {
          // The faces are wider than the locked aspect allows: centre on
          // them and accept the overflow.
          cropX = faceCx - cropW / 2;
        } else {
          var loX = x1 + m - cropW;
          var hiX = x0 - m;
          var wantX = faceCx - cropW / 2;
          cropX = loX > hiX ? wantX : Math.min(Math.max(wantX, loX), hiX);
        }

        var cropY;
        var wantY = faceCy - cropH * 0.40;
        if (y1 - y0 + 2 * m > cropH) {
          cropY = faceCy - cropH / 2;
        } else {
          var loY = y1 + m - cropH;
          var hiY = y0 - m;
          cropY = loY > hiY ? wantY : Math.min(Math.max(wantY, loY), hiY);
        }

        cropX = Math.max(0, Math.min(cropX, W - cropW));
        cropY = Math.max(0, Math.min(cropY, H - cropH));
        cropX = Math.round(cropX);
        cropY = Math.round(cropY);
        cropW = Math.round(cropW);
        cropH = Math.round(cropH);
        if (cropX + cropW > W) cropW = W - cropX;
        if (cropY + cropH > H) cropH = H - cropY;
        return { cropX: cropX, cropY: cropY, cropW: cropW, cropH: cropH };
      }

      // The runtime copy for the face status line. The keys live in the
      // "tools.copy" namespace, which the middleware hands to the client as
      // window.__WA_I18N__ - so the fallback English is only ever shown on
      // an English page.
      var FACE_STATUS_KEYS = {
        off: 'tools.copy.cropFaceOff.1a2b3c4d',
        loading: 'tools.copy.cropFaceLoading.2b3c4d5e',
        ready: 'tools.copy.cropFaceReady.3c4d5e6f',
        found: 'tools.copy.cropFaceFound.4d5e6f70',
        none: 'tools.copy.cropFaceNone.5e6f7081',
        failed: 'tools.copy.cropFaceFailed.6f708192'
      };

      var FACE_STATUS_FALLBACK = {
        off: 'Face detection is off. Switch it on to frame the couple automatically.',
        loading: 'Loading the face detector\\u2026',
        ready: 'Face detector ready \\u2014 it runs on your device, your photos are never uploaded.',
        found: '{n} face(s) found \\u2014 the crop frame keeps them all inside.',
        none: 'No face found in this photo \\u2014 keeping the off-center bias instead.',
        failed: 'Face detection is not available on this device \\u2014 keeping the off-center bias instead.'
      };

      function faceStatusText(kind, params) {
        var T = window.weddingAITool && window.weddingAITool.t;
        var fallback = FACE_STATUS_FALLBACK[kind] || '';
        if (!T) return fallback;
        return T(FACE_STATUS_KEYS[kind], fallback, params);
      }

      function setFaceStatus(text) {
        if (faceStatusEl) faceStatusEl.textContent = text;
      }

      // Run the detector over one photo. The result is cached on the entry,
      // so a photo is only ever scanned once - and a photo with no face is
      // a normal answer, not an error.
      async function detectFacesFor(entry, img) {
        if (!entry) return [];
        if (entry.facesDone) return entry.faces || [];
        var facesApi = window.weddingAIFaces;
        if (!facesApi || !facesApi.detect) {
          entry.faces = [];
          entry.facesDone = true;
          setFaceStatus(faceStatusText('failed'));
          return [];
        }
        setFaceStatus(faceStatusText('loading'));
        var faces = [];
        try {
          faces = (await facesApi.detect(img)) || [];
        } catch (err) {
          faces = [];
        }
        entry.faces = faces;
        entry.facesDone = true;
        setFaceStatus(faces.length
          ? faceStatusText('found', { n: faces.length })
          : faceStatusText('none'));
        return faces;
      }

      // The automatic crop for a photo: the faces when the visitor switched
      // them on, the off-center bias otherwise. `faceScale` converts the
      // cached face boxes from SOURCE pixels into the coordinate space the
      // caller works in (the preview canvas is smaller than the photo).
      function autoCropFor(entry, W, H, aspect, smart, faceAware, faceScale) {
        if (faceAware && entry && entry.faces && entry.faces.length) {
          var boxes = entry.faces;
          if (faceScale && faceScale !== 1) {
            boxes = entry.faces.map(function (b) {
              return {
                x: b.x * faceScale,
                y: b.y * faceScale,
                w: b.w * faceScale,
                h: b.h * faceScale
              };
            });
          }
          return computeCropWithFaces(W, H, aspect.w, aspect.h, boxes);
        }
        return computeCrop(W, H, aspect.w, aspect.h, smart);
      }

      async function processOne(entry, settings) {
"""

OLD_PROCESS = """          if (!crop) {
            crop = computeCrop(W, H, settings.aspect.w, settings.aspect.h, settings.smart);
          }
"""

NEW_PROCESS = """          if (!crop) {
            if (settings.faceAware && !entry.facesDone) {
              await detectFacesFor(entry, img);
            }
            crop = autoCropFor(entry, W, H, settings.aspect, settings.smart, settings.faceAware, 1);
          }
"""

OLD_SHADE = """        ctx.restore();
        // rule of thirds
"""

NEW_SHADE = """        ctx.restore();
        // The detected faces (§2.11). They are stored in SOURCE pixels, so
        // they are scaled into the canvas' own coordinates here.
        var sEntry = stageEntries()[stageIndex];
        if (sEntry && sEntry.faces && sEntry.faces.length) {
          ctx.save();
          ctx.strokeStyle = 'rgba(74,222,128,0.95)';
          ctx.lineWidth = 2;
          for (var fi = 0; fi < sEntry.faces.length; fi++) {
            var fb = sEntry.faces[fi];
            ctx.strokeRect(
              fb.x / stageScale, fb.y / stageScale,
              fb.w / stageScale, fb.h / stageScale);
          }
          ctx.restore();
        }
        // rule of thirds
"""

OLD_STAGE_AUTO = """          } else {
            var auto = computeCrop(cw, ch, getCurrentSettings().aspect.w, getCurrentSettings().aspect.h, !!smartEl.checked);
            stageRect = clampRect({ x: auto.cropX, y: auto.cropY, w: auto.cropW, h: auto.cropH }, stageAspect());
          }
"""

NEW_STAGE_AUTO = """          } else {
            var stageSettings = getCurrentSettings();
            if (stageSettings.faceAware && !entry.facesDone) {
              await detectFacesFor(entry, stageImg);
            }
            var auto = autoCropFor(entry, cw, ch, stageSettings.aspect, stageSettings.smart, stageSettings.faceAware, 1 / stageScale);
            stageRect = clampRect({ x: auto.cropX, y: auto.cropY, w: auto.cropW, h: auto.cropH }, stageAspect());
          }
"""

OLD_TAIL = """      refreshUI();
    });
    </script>
"""

NEW_TAIL = """      // §2.11 - the face-aware switch. Turning it on re-scans the current
      // photo and re-frames it; turning it off goes back to the bias.
      if (faceAwareEl) {
        faceAwareEl.addEventListener('change', function () {
          var entries = stageEntries();
          var entry = entries[stageIndex];
          if (entry) { entry.faces = null; entry.facesDone = false; }
          setFaceStatus(faceStatusText(faceAwareEl.checked ? 'loading' : 'off'));
          showStage();
        });
      }
      setFaceStatus(faceStatusText('off'));

      refreshUI();
    });
    </script>
"""

OLD_DEBUG = """      setFaceStatus(faceStatusText('off'));

      refreshUI();
"""

NEW_DEBUG = """      setFaceStatus(faceStatusText('off'));

      // A small read-only hook so the verification script can see what the
      // page actually computed (which backend answered, where the faces are,
      // where the frame ended up). It exposes nothing a visitor can act on.
      window.__waCropDebug = function () {
        var entries = stageEntries();
        var entry = entries[stageIndex];
        return {
          backend: window.weddingAIFaces ? window.weddingAIFaces.backend() : null,
          faceAware: !!(faceAwareEl && faceAwareEl.checked),
          faces: entry && entry.faces ? entry.faces : null,
          rect: stageRect ? { x: stageRect.x, y: stageRect.y, w: stageRect.w, h: stageRect.h } : null,
          scale: stageScale,
          status: faceStatusEl ? faceStatusEl.textContent : ''
        };
      };

      refreshUI();
"""

JS_PATCHES = [
    (OLD_ELEMENTS, NEW_ELEMENTS, "var faceAwareEl =", "the element handles"),
    (OLD_SETTINGS, NEW_SETTINGS, "faceAware: !!faceAwareEl.checked,", "the settings"),
    (OLD_CROP_END, NEW_CROP_END, "function computeCropWithFaces(", "the face helpers"),
    (OLD_PROCESS, NEW_PROCESS, "autoCropFor(entry, W, H,", "the batch crop"),
    (OLD_SHADE, NEW_SHADE, "sEntry.faces.length", "the face boxes"),
    (OLD_STAGE_AUTO, NEW_STAGE_AUTO, "stageSettings.faceAware", "the stage frame"),
    (OLD_TAIL, NEW_TAIL, "faceAwareEl.addEventListener('change'", "the switch wiring"),
    (OLD_DEBUG, NEW_DEBUG, "window.__waCropDebug", "the debug hook"),
]


def patch_js(text: str) -> tuple:
    changes = 0
    for old, new, marker, what in JS_PATCHES:
        if marker in text:
            continue
        if old not in text:
            raise SystemExit("[FAIL] could not find %s" % what)
        text = text.replace(old, new, 1)
        changes += 1
    return text, changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total = 0
    for lang in LANGS:
        path = page_path(lang)
        if not path.is_file():
            raise SystemExit("[FAIL] missing page: %s" % path)
        text = path.read_text(encoding="utf-8")
        before = text
        text, n = patch_html(text, lang == "en")
        j = 0
        if lang == "en":
            text, j = patch_js(text)
        if text != before and not args.dry_run:
            write_atomic(path, text)
        total += n + j
        print("  %-3s html=%d js=%d" % (lang, n, j))

    if args.dry_run:
        print("\n[DRY RUN] nothing was written")
    else:
        print("\nNow run:")
        print("  python scripts/propagate-tool-js.py")
        print("  python scripts/check-tool-script-syntax.py")
        print("  python scripts/build-crop-face-i18n-patch.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
