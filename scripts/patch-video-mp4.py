#!/usr/bin/env python3
"""
Add a real MP4 export to the wedding video invitation maker (§3.2), and fix
the 1080x1920 export that was drawing the wrong picture.

WHY A SCRIPT
------------
Eleven pages have to change in the same way, and the machine-translated
copies have DIFFERENT prose in them. So the patch is role-based:

  * the download button is found by its id, not by its label;
  * the "Why 5 frames and not a real video?" section is found by its
    heading, which the machine translator left in English in every one of
    the eleven languages (verified 2026-11-11);
  * every replacement is data-i18n bound, so the runtime text comes from
    the dictionary and is correct in all eleven languages.

THE BUG THIS ALSO FIXES
-----------------------
`renderFrameAt()` laid everything out in a 540x960 DESIGN space with
absolute pixel coordinates (y = 360, font sizes in px, ...). The PNG
export set BASE_W/BASE_H to 1080/1920 and re-rendered - which drew the
540x960 layout into the TOP-LEFT CORNER of a 1080x1920 canvas. The
"Download 5 PNG frames (1080x1920)" button therefore produced 1080x1920
files whose design occupied a quarter of the frame and was not what the
preview showed.

The fix is one `ctx.scale()` at the top of renderFrameAt() and
`ctx.restore()` at the end: the design stays in 540x960 units and is
scaled to whatever canvas it is rendered into.

Usage
-----
    python scripts/patch-video-mp4.py --dry-run
    python scripts/patch-video-mp4.py
"""
import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
SLUG = "wedding-video-invitation-maker"

# --------------------------------------------------------------------------
# the markup that goes into all eleven pages
# --------------------------------------------------------------------------

MP4_BUTTON = (
    '<button type="button" class="btn btn-primary" id="download-mp4-btn" '
    'data-i18n="tools.%s.btn_text.download_mp4.8k3m1p7q" hidden>'
    "Download a 5-second MP4</button>" % SLUG
)

MP4_NOTE = (
    '<p id="mp4-note" data-i18n="tools.%s.p_text.mp4_note.4r6t8v0w" hidden '
    'style="margin-top: 12px;">Your browser can also encode a real MP4 '
    "here &mdash; 5 seconds, 1080&times;1920, 30 fps, with the motion "
    "interpolated between the five key frames. It takes about 15 seconds "
    "and nothing leaves your device. The PNG frames stay available either "
    "way.</p>" % SLUG
)

WHY_BLOCK = (
    '<h2 data-i18n="tools.%s.h2_text.why_frames.2s5d7f1g">'
    "Why 5 key frames, and where the MP4 comes from</h2>\n"
    '                <p data-i18n="tools.%s.p_text.why_frames_1.6h9j2k3l">'
    "The tool draws its motion in <strong>5 key frames</strong> "
    "(1080&times;1920, 9:16). Two downloads come out of that: the five PNG "
    "frames, and &mdash; when your browser can encode video &mdash; a real "
    "5-second MP4 with the motion interpolated between the key frames at "
    "30 fps.</p>\n"
    '                <p data-i18n="tools.%s.p_text.why_frames_2.0m4n6p8q">'
    "The MP4 is encoded on your own device with the WebCodecs API. Nothing "
    "is uploaded, and there is no 30 MB ffmpeg.wasm to download. A browser "
    "that cannot encode H.264 simply keeps the PNG frames &mdash; you never "
    "lose the download either way.</p>" % (SLUG, SLUG, SLUG)
)

MODULE_TAG = (
    '    <script type="module" src="/js/tools/movie-loader.js?v=1.0.0">'
    "</script>\n"
)

# The actions block: the download button, the reset button, and (new) the
# MP4 button. Found by id, so the machine-translated labels do not matter.
ACTIONS_RE = re.compile(
    r'(?s)(<div class="wa-tool-actions">\s*'
    r'<button[^>]*id="download-btn"[^>]*>.*?</button>\s*'
    r'<button[^>]*id="reset-btn"[^>]*>.*?</button>\s*'
    r"</div>)"
)

# The "Why 5 frames and not a real video?" section. The heading was left in
# English by the machine translator in every language, so it is a reliable
# role anchor.
WHY_RE = re.compile(
    r'(?s)<h2>Why 5 frames and not a "real" video\?</h2>\s*'
    r"<p>.*?</p>\s*<p>.*?</p>"
)

BODY_END_RE = re.compile(r"(?s)\n    </script>\n</body>")


# --------------------------------------------------------------------------
# the inline script (English source only - the localized copies are
# overwritten by scripts/propagate-tool-js.py)
# --------------------------------------------------------------------------

RENDER_OLD = """      function renderFrameAt(ctx, t, frame, txt) {
        // frame: 0..4
        // choreograph
        var p = frame / (NUM_FRAMES - 1); // 0..1
        ctx.clearRect(0, 0, BASE_W, BASE_H);
        fillGradient(ctx, BASE_W, BASE_H, t.bg[0], t.bg[1]);
"""

RENDER_NEW = """      function renderFrameAt(ctx, t, frame, txt) {
        // frame: 0..4 - it may be FRACTIONAL, which is how the MP4 export
        // interpolates the motion between the five key frames.
        //
        // EVERYTHING below is laid out in a 540x960 DESIGN space (absolute
        // pixel coordinates, font sizes in px). The canvas can be any size
        // - the preview is 540x960, the exports are 1080x1920 - so the
        // context is scaled to fit it.
        //
        // Before this, the export set BASE_W/BASE_H to 1080/1920 and
        // re-rendered, which drew the 540x960 layout into the TOP-LEFT
        // CORNER of a 1080x1920 canvas: the "1080x1920 frames" were
        // 1080x1920 files with the design squeezed into a quarter of them.
        var p = frame / (NUM_FRAMES - 1); // 0..1
        var cw = ctx.canvas.width, ch = ctx.canvas.height;
        ctx.save();
        ctx.scale(cw / BASE_W, ch / BASE_H);
        ctx.clearRect(0, 0, BASE_W, BASE_H);
        fillGradient(ctx, BASE_W, BASE_H, t.bg[0], t.bg[1]);
"""

RENDER_END_OLD = """            ctx.fillText('\U0001F3B5 ' + (txt.music || 'Acoustic guitar'), BASE_W/2, BASE_H - 60);
          }
        }
      }
"""

RENDER_END_NEW = """            ctx.fillText('\U0001F3B5 ' + (txt.music || 'Acoustic guitar'), BASE_W/2, BASE_H - 60);
          }
        }
        ctx.restore();
      }
"""

FRAMES_OLD = """        var origW = BASE_W, origH = BASE_H;
        BASE_W = 1080; BASE_H = 1920;
        var octx = off.getContext('2d');
"""

FRAMES_NEW = """        // The layout is a 540x960 design space; renderFrameAt() scales it to
        // whatever canvas it is given, so the export is the SAME picture as
        // the preview - just at twice the resolution.
        var octx = off.getContext('2d');
"""

FRAMES_END_OLD = """          if (i >= NUM_FRAMES) {
            BASE_W = origW; BASE_H = origH;
            T.toast('Saved 5 frames — assemble in CapCut / iMovie', 'success');
"""

FRAMES_END_NEW = """          if (i >= NUM_FRAMES) {
            T.toast('Saved 5 frames — assemble in CapCut / iMovie', 'success');
"""

MP4_DETECT_OLD = """      if (mp4Btn) {
        mp4Btn.addEventListener('click', downloadMp4);
        // Only offer the MP4 where an encoder can exist at all.
        showMp4(typeof window.VideoEncoder !== 'undefined');
      }
"""

MP4_DETECT_NEW = """      if (mp4Btn) {
        mp4Btn.addEventListener('click', downloadMp4);
        // Offer the MP4 only where an H.264 encoder can actually produce
        // one. VideoEncoder.isConfigSupported() is a NATIVE call, so this
        // check is free - it does not fetch the 706 KB encoder.
        //
        // Level 4.0 is the lowest that fits 1080x1920: level 3.1 caps out
        // at 1280x720, and a browser asked for 1080x1920 at level 3.1
        // simply reports "not supported" (measured 2026-11-11 in Chrome).
        if (typeof window.VideoEncoder !== 'undefined' &&
            typeof window.VideoEncoder.isConfigSupported === 'function') {
          window.VideoEncoder.isConfigSupported({
            codec: 'avc1.420028',
            width: 1080, height: 1920,
            bitrate: 4000000, framerate: 30
          }).then(function (info) {
            showMp4(!!(info && info.supported));
          }).catch(function () {
            showMp4(false);
          });
        } else {
          showMp4(false);
        }
      }
"""

MP4_JS = """
      // ---------- MP4 export (mediabunny, loaded on demand) -------------------
      //
      // WHY THE PNG FRAMES STAY
      // -----------------------
      // The MP4 needs an H.264 encoder, which only some browsers have
      // (WebCodecs). So the MP4 button is only shown when
      // `window.VideoEncoder` exists, and the PNG frames are always there.
      // NO BROWSER LOSES A FEATURE: a browser without an encoder simply
      // keeps the PNG sequence it has always had.
      //
      // The encoder (mediabunny, MPL-2.0) is 706 KB and is fetched ONLY
      // when the visitor asks for the MP4 - see js/tools/movie-loader.mjs.
      var mp4Btn = document.getElementById('download-mp4-btn');
      var mp4Note = document.getElementById('mp4-note');
      var mp4Busy = false;

      function mp4Ready() {
        if (window.weddingAIMovie) return Promise.resolve(window.weddingAIMovie);
        // The loader module is deferred, so it may not have run yet.
        return new Promise(function (resolve, reject) {
          var timer = setTimeout(function () {
            reject(new Error('The MP4 encoder did not load'));
          }, 15000);
          window.addEventListener('weddingai-movie-ready', function () {
            clearTimeout(timer);
            resolve(window.weddingAIMovie);
          });
        });
      }

      function showMp4(visible) {
        if (mp4Btn) mp4Btn.hidden = !visible;
        if (mp4Note) mp4Note.hidden = !visible;
      }

      async function downloadMp4() {
        if (mp4Busy) return;
        var T = window.weddingAITool;
        if (!T) return;
        mp4Busy = true;
        var label = mp4Btn ? mp4Btn.textContent : '';
        try {
          var M = await mp4Ready();
          var M2 = await M.load();
          var canAvc = await M2.canEncodeVideo('avc');
          if (!canAvc) {
            showMp4(false);
            T.toast(T.t('mp4Unsupported',
              'This browser cannot encode MP4. The PNG frames still work.'), 'error');
            return;
          }
          if (mp4Btn) mp4Btn.disabled = true;
          var W = 1080, H = 1920, FPS = 30, SECONDS = 5;
          var total = FPS * SECONDS;
          var canvas = document.createElement('canvas');
          canvas.width = W; canvas.height = H;
          var ctx = canvas.getContext('2d');
          var t = getTemplate(state.templateId);
          var txt = getText();

          var output = new M2.Output({
            format: new M2.Mp4OutputFormat(),
            target: new M2.BufferTarget()
          });
          var source = new M2.CanvasSource(canvas, {
            codec: 'avc',
            quality: new M2.Quality('high')
          });
          output.addVideoTrack(source);
          await output.start();

          for (var i = 0; i < total; i++) {
            // A fractional key frame: the motion between the five key
            // frames is interpolated instead of stepped.
            renderFrameAt(ctx, t, (i / (total - 1)) * (NUM_FRAMES - 1), txt);
            await source.add(i / FPS, 1 / FPS);
            if (i % 5 === 0) {
              var pct = Math.round(((i + 1) / total) * 100);
              if (mp4Btn) mp4Btn.textContent = T.t('mp4Encoding', 'Encoding… {pct}%', { pct: pct });
              await new Promise(function (r) { setTimeout(r, 0); });
            }
          }
          await output.finalize();
          var blob = new Blob([output.target.buffer], { type: 'video/mp4' });
          var baseName = 'wedding-invitation-' +
            (txt.couple || 'card').replace(/[^a-zA-Z0-9]+/g, '-').toLowerCase().slice(0, 40);
          T.download(blob, baseName + '.mp4');
          T.toast(T.t('mp4Saved', 'Saved the 5-second MP4.'), 'success');
        } catch (err) {
          T.toast(T.t('mp4Failed',
            'Could not make the MP4. The PNG frames still work.'), 'error');
          if (window.console && console.warn) console.warn('[weddingai] MP4 export failed', err);
        } finally {
          mp4Busy = false;
          if (mp4Btn) {
            mp4Btn.disabled = false;
            mp4Btn.textContent = label;
          }
        }
      }

      if (mp4Btn) {
        mp4Btn.addEventListener('click', downloadMp4);
        // Only offer the MP4 where an encoder can exist at all.
        showMp4(typeof window.VideoEncoder !== 'undefined');
      }

"""


def atomic_write(path: Path, text: str) -> None:
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


def patch_markup(text: str, path_label: str, problems: list) -> str:
    # 1. the MP4 button + the note, right after the existing actions block
    m = ACTIONS_RE.search(text)
    if not m:
        problems.append("%s: the download/reset button block was not found" % path_label)
    elif "download-mp4-btn" in text:
        pass  # already applied
    else:
        block = m.group(1)
        # the MP4 button goes INSIDE the actions row, the note after it
        new_block = block.replace(
            '<button type="button" class="btn btn-secondary" id="reset-btn"',
            MP4_BUTTON + '\n                    <button type="button" class="btn btn-secondary" id="reset-btn"')
        new_block = new_block + "\n                " + MP4_NOTE
        text = text[:m.start()] + new_block + text[m.end():]

    # 2. the "Why 5 frames" section
    if "why_frames.2s5d7f1g" in text:
        pass  # already applied
    else:
        m = WHY_RE.search(text)
        if not m:
            problems.append("%s: the 'Why 5 frames' section was not found" % path_label)
        else:
            text = text[:m.start()] + WHY_BLOCK + text[m.end():]

    # 3. the module loader
    #
    # It has to sit AFTER the main inline script's closing tag. An earlier
    # version of this script inserted it BEFORE that tag, which put the
    # markup inside the JavaScript and broke the whole page (the script no
    # longer parsed). The repair branch below fixes a file that already has
    # the tag in the wrong place.
    misplaced = MODULE_TAG.strip() + "\n    </script>\n</body>"
    if misplaced in text:
        text = text.replace(
            misplaced,
            "    </script>\n" + MODULE_TAG + "</body>")
    elif "movie-loader.js" not in text:
        m = BODY_END_RE.search(text)
        if not m:
            problems.append("%s: the end of the body was not found" % path_label)
        else:
            text = (text[:m.start()] + "    </script>\n" + MODULE_TAG
                    + "</body>" + text[m.end():])
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    problems = []
    changed = []

    for lang in LANGS:
        rel = ("tools/%s/index.html" % SLUG) if lang == "en" else (
            "%s/tools/%s/index.html" % (lang, SLUG))
        path = ROOT / rel
        if not path.exists():
            problems.append("MISSING %s" % rel)
            continue
        text = path.read_text(encoding="utf-8")
        before = text
        text = patch_markup(text, rel, problems)

        if lang == "en":
            for old, new, note in (
                (RENDER_OLD, RENDER_NEW, "renderFrameAt scale"),
                (RENDER_END_OLD, RENDER_END_NEW, "renderFrameAt restore"),
                (FRAMES_OLD, FRAMES_NEW, "downloadFrames no BASE_W hack"),
                (FRAMES_END_OLD, FRAMES_END_NEW, "downloadFrames restore BASE_W"),
                (MP4_DETECT_OLD, MP4_DETECT_NEW, "native H.264 support probe"),
            ):
                if text.count(new) >= 1:
                    continue  # already applied
                if text.count(old) != 1:
                    problems.append("%s: anchor for '%s' found %d times"
                                    % (rel, note, text.count(old)))
                else:
                    text = text.replace(old, new)

            # the MP4 encoder, inserted before the wiring block
            if "async function downloadMp4" not in text:
                anchor = "      // ---------- wire\n"
                if text.count(anchor) != 1:
                    problems.append("%s: the wiring anchor was not found" % rel)
                else:
                    text = text.replace(anchor, MP4_JS + anchor)

        if text != before:
            changed.append(rel)
            if not args.dry_run:
                atomic_write(path, text)

    for p in problems:
        print("PROBLEM: " + p)
    print("  %d file(s) %s" % (len(changed), "would change" if args.dry_run else "changed"))
    if problems:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
