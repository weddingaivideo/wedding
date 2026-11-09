#!/usr/bin/env python3
"""
Give the compress tool a target-size mode (§2.14) and EXIF retention
(§2.13), and make the prose match.

WHY
---
§2.14: "Compress to exactly 2 MB" is what people actually ask for. The
quality slider cannot answer it. With a target set, the tool searches for
the highest JPEG quality that still fits under it, and scales the canvas
down only when even the lowest quality is too big.

§2.13: the Canvas API writes raw pixels, so the re-encoded file has NO
EXIF at all - and the page said so. The original file usually does, and
camera / lens / shooting date are worth keeping. The APP1 (Exif) segment
is copied verbatim into the re-encoded JPEG, right after its SOI marker.

THE TRAP INSIDE §2.13
--------------------
The EXIF block carries the Orientation tag. The pixels in the OUTPUT are
already upright (the decoder applied the orientation when it decoded the
source), so carrying Orientation=6 over would make every viewer rotate
them a second time - the photo would end up sideways. The orientation is
therefore reset to 1 ("normal") on the way in.

ROLE-BASED, NOT TEXT-BASED
-------------------------
The eleven language copies have DIFFERENT prose. The two paragraphs that
are being rewritten are found by ROLE: the last two <p> before the third
<h3> of the article body. The two new controls are inserted after the
quality control, which is found by its input id.

Usage
-----
    python scripts/patch-compress-target-exif.py --dry-run
    python scripts/patch-compress-target-exif.py
"""
import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
SLUG = "compress-wedding-photos"

# --------------------------------------------------------------------------
# markup
# --------------------------------------------------------------------------

TARGET_CONTROL = """
                    <div class="wa-tool-control">
                        <label for="target-size" data-i18n="tools.%s.label_text.target_size.5x7y9z1">Target size (MB) &mdash; optional</label>
                        <input type="number" id="target-size" min="0" max="200" step="0.1" value="0" inputmode="decimal" style="width: 130px;">
                        <small data-i18n="tools.%s.small_text.target_size.6a8b0c2d">0 = off. When it is set, the quality slider is ignored and every photo is tuned to land just under this size.</small>
                    </div>
                    <div class="wa-tool-control">
                        <label for="keep-exif"><input type="checkbox" id="keep-exif" checked> <span data-i18n="tools.%s.label_text.keep_exif.9e3f1a2b">Keep EXIF metadata (camera, date)</span></label>
                        <small data-i18n="tools.%s.small_text.keep_exif.0c4d2e3f">Copied from the original file. JPG output only. The orientation is reset, so the photo can never end up sideways.</small>
                    </div>
""" % (SLUG, SLUG, SLUG, SLUG)

P_DOES = (
    '<p data-i18n="tools.%s.p_text.what_it_does.7h2k4m6n">The compressor uses the '
    "browser's built-in <strong>Canvas API</strong> to re-encode each dropped "
    "image at your chosen quality. It supports JPG, PNG, and WebP input and "
    "outputs JPG, WebP, or PNG. Optional &quot;Max longest edge&quot; caps the "
    "longest side &mdash; handy if you know the destination's size limit. A "
    "<strong>target size</strong> in MB replaces the quality slider entirely: "
    "the tool searches for the highest quality that still fits under it, and "
    "scales the photo down only when even the lowest quality is too big.</p>"
    % SLUG
)

P_DOES_NOT = (
    '<p data-i18n="tools.%s.p_text.what_it_does_not.8j3l5n7p">What it does not '
    "do: it cannot reach a target smaller than the photo can be, and it cannot "
    "write PNG metadata. EXIF is copied over from the original file &mdash; "
    "camera, lens, shooting date &mdash; so a compressed photo still says when "
    "and where it was taken. The orientation is deliberately reset, because the "
    "pixels are already upright: keeping the original rotation flag would make "
    "every viewer turn the photo sideways.</p>" % SLUG
)

QUALITY_CONTROL_RE = re.compile(
    r'(?s)(<div class="wa-tool-control">\s*<label for="quality">.*?</div>)')
H3_RE = re.compile(r"(?s)<h3(?![^>]*data-i18n)[^>]*>.*?</h3>")
P_RE = re.compile(r"(?s)<p(?![^>]*data-i18n)[^>]*>.*?</p>")

# --------------------------------------------------------------------------
# script
# --------------------------------------------------------------------------

HELPERS = r"""
      // ---------- EXIF (§2.13) -------------------------------------------------
      //
      // The Canvas API writes raw pixels: the re-encoded file has no EXIF at
      // all. The original usually does, and camera / lens / shooting date are
      // worth keeping - so the APP1 (Exif) segment is copied verbatim into
      // the re-encoded JPEG, right after its SOI marker. That is exactly what
      // an EXIF-aware encoder does.
      //
      // THE TRAP: the EXIF block carries the Orientation tag, and the pixels
      // in the OUTPUT are already upright (the decoder applied the
      // orientation when it read the source). Carrying Orientation=6 over
      // would make every viewer rotate them a second time and the photo
      // would end up sideways. The orientation is reset to 1 on the way in.
      function readExifBytes(file) {
        return new Promise(function (resolve) {
          try {
            // The APP1 segment sits in the first few KB; 128 KB is plenty
            // and avoids reading a 30 MB file into memory.
            file.slice(0, 128 * 1024).arrayBuffer().then(function (buf) {
              resolve(parseExif(new Uint8Array(buf)));
            }).catch(function () { resolve(null); });
          } catch (e) { resolve(null); }
        });
      }

      function parseExif(bytes) {
        if (!bytes || bytes.length < 4) return null;
        if (bytes[0] !== 0xFF || bytes[1] !== 0xD8) return null; // not a JPEG
        var i = 2;
        while (i + 4 <= bytes.length) {
          if (bytes[i] !== 0xFF) { i++; continue; }
          var marker = bytes[i + 1];
          if (marker === 0xD8 || marker === 0x01 || (marker >= 0xD0 && marker <= 0xD7)) {
            i += 2; continue;
          }
          if (marker === 0xDA || marker === 0xD9) return null; // start of scan
          var len = (bytes[i + 2] << 8) | bytes[i + 3];
          if (len < 2) return null;
          if (marker === 0xE1) {
            if (i + 10 > bytes.length) return null;
            var sig = String.fromCharCode(bytes[i + 4], bytes[i + 5], bytes[i + 6],
              bytes[i + 7], bytes[i + 8], bytes[i + 9]);
            if (sig !== 'Exif\0\0') return null;
            var seg = bytes.slice(i, i + 2 + len); // marker + length + payload
            resetOrientation(seg);
            return seg;
          }
          i += 2 + len;
        }
        return null;
      }

      // Set the Orientation tag (0x0112) in IFD0 to 1 ("normal").
      function resetOrientation(seg) {
        try {
          var tiff = 10; // marker(2) + length(2) + "Exif\0\0"(6)
          if (seg.length < tiff + 8) return;
          var le = seg[tiff] === 0x49; // "II" = little endian
          var u16 = function (off) {
            return le ? (seg[off] | (seg[off + 1] << 8)) : ((seg[off] << 8) | seg[off + 1]);
          };
          var u32 = function (off) {
            return le
              ? ((seg[off] | (seg[off + 1] << 8) | (seg[off + 2] << 16) | (seg[off + 3] << 24)) >>> 0)
              : (((seg[off] << 24) | (seg[off + 1] << 16) | (seg[off + 2] << 8) | seg[off + 3]) >>> 0);
          };
          if (u16(tiff + 2) !== 42) return;   // the TIFF magic number
          var ifd0 = tiff + u32(tiff + 4);
          if (ifd0 + 2 > seg.length) return;
          var count = u16(ifd0);
          for (var i = 0; i < count; i++) {
            var e = ifd0 + 2 + i * 12;
            if (e + 12 > seg.length) return;
            if (u16(e) !== 0x0112) continue;   // Orientation
            // type 3 (SHORT), count 1 -> the value is in the first two
            // bytes of the four-byte value field
            if (le) { seg[e + 8] = 1; seg[e + 9] = 0; }
            else { seg[e + 8] = 0; seg[e + 9] = 1; }
            return;
          }
        } catch (err) { /* leave the segment as it is */ }
      }

      // Put the APP1 segment back into a JPEG, right after the SOI marker.
      function spliceExif(jpegBlob, seg) {
        if (!seg) return Promise.resolve(jpegBlob);
        return jpegBlob.arrayBuffer().then(function (buf) {
          var out = new Uint8Array(buf.length + seg.length);
          out.set(new Uint8Array(buf), 0);
          out.set(seg, 2);
          return new Blob([out], { type: 'image/jpeg' });
        });
      }

      // ---------- target size (§2.14) -----------------------------------------
      //
      // "Compress to exactly 2 MB" is what people actually ask for, and a
      // quality slider cannot answer it. So with a target set the tool
      // searches for the HIGHEST quality that still fits under it.
      //
      // At a fixed quality the JPEG size scales roughly with the pixel
      // count, so when even the lowest quality is too big the canvas is
      // scaled by sqrt(target / size) and the search runs again.
      async function encodeToTarget(canvas, mime, targetBytes) {
        var T = window.weddingAITool;
        var LO = 0.3, HI = 0.95;
        var work = canvas;
        for (var round = 0; round < 5; round++) {
          var lo = LO, hi = HI, best = null, bestQ = LO;
          for (var i = 0; i < 7; i++) {
            var mid = (lo + hi) / 2;
            var b = await T.canvasToBlob(work, mime, mid);
            if (!b || b.size === 0) { hi = mid; continue; }
            if (b.size <= targetBytes) { best = b; bestQ = mid; lo = mid; }
            else { hi = mid; }
            if (hi - lo < 0.01) break;
          }
          if (best) return { blob: best, quality: bestQ };
          // Nothing fits at the lowest quality: shrink the canvas.
          var small = await T.canvasToBlob(work, mime, LO);
          if (!small || small.size === 0) break;
          var factor = Math.sqrt(targetBytes / small.size);
          if (factor >= 0.995) break;
          var w = Math.max(16, Math.round(work.width * factor));
          var h = Math.max(16, Math.round(work.height * factor));
          var next = document.createElement('canvas');
          next.width = w; next.height = h;
          var nctx = next.getContext('2d');
          nctx.imageSmoothingEnabled = true;
          nctx.imageSmoothingQuality = 'high';
          nctx.drawImage(work, 0, 0, w, h);
          work = next;
        }
        return { blob: null, quality: LO };
      }

"""

SETTINGS_OLD = """      function getCurrentSettings() {
        return {
          quality: parseInt(qualityEl.value, 10) / 100,
          maxDim: parseInt(maxDimEl.value, 10) || 0,
          format: formatEl.value,
        };
      }
"""

SETTINGS_NEW = """      function getCurrentSettings() {
        var targetEl = document.getElementById('target-size');
        var exifEl = document.getElementById('keep-exif');
        return {
          quality: parseInt(qualityEl.value, 10) / 100,
          maxDim: parseInt(maxDimEl.value, 10) || 0,
          format: formatEl.value,
          // 0 = off. The value is in bytes so the rest of the code never
          // has to think about MB again.
          targetBytes: Math.round((parseFloat(targetEl && targetEl.value) || 0) * 1024 * 1024),
          keepExif: !!(exifEl && exifEl.checked),
        };
      }
"""

ENCODE_OLD = """          var mime = settings.format;
          var quality = settings.quality;
          // PNG is lossless, quality is ignored
          if (mime === 'image/png') quality = undefined;
          var blob = await window.weddingAITool.canvasToBlob(canvas, mime, quality);
          if (!blob || blob.size === 0) throw new Error('Compression returned an empty file. Try a different format.');
"""

ENCODE_NEW = """          var mime = settings.format;
          var quality = settings.quality;
          // PNG is lossless, quality is ignored
          if (mime === 'image/png') quality = undefined;
          var blob;
          if (settings.targetBytes > 0 && mime !== 'image/png') {
            // §2.14 - "compress to exactly 2 MB". The quality slider is
            // replaced by a search for the highest quality that still fits
            // under the target.
            entry.percent = 55;
            refreshUI();
            var res = await encodeToTarget(canvas, mime, settings.targetBytes);
            blob = res.blob;
            if (!blob) {
              // The target is unreachable for this photo: keep the smallest
              // file we could make and say so in the summary.
              blob = await window.weddingAITool.canvasToBlob(canvas, mime, 0.3);
              entry.targetMissed = true;
            } else {
              quality = res.quality;
            }
          } else {
            blob = await window.weddingAITool.canvasToBlob(canvas, mime, quality);
          }
          if (!blob || blob.size === 0) throw new Error('Compression returned an empty file. Try a different format.');
          // §2.13 - carry the EXIF block over from the original file.
          if (settings.keepExif && mime === 'image/jpeg' && entry.inputFile) {
            entry.percent = 92;
            refreshUI();
            var exif = await readExifBytes(entry.inputFile);
            if (exif) blob = await spliceExif(blob, exif);
          }
"""

SUMMARY_OLD = """          (errs.length ? '<div style="color:#b00020"><strong>' + errs.length + ' errored</strong> — remove and retry.</div>' : '');"""

SUMMARY_NEW = """          (missed ? '<div style="color:#b00020"><strong>' + missed + ' could not reach the target size</strong> — the photo is already smaller than the target allows.</div>' : '') +
          (errs.length ? '<div style="color:#b00020"><strong>' + errs.length + ' errored</strong> — remove and retry.</div>' : '');"""

SUMMARY_DECL_OLD = """        var errs = files.filter(function (f) { return f.status === 'error'; });
"""

SUMMARY_DECL_NEW = """        var errs = files.filter(function (f) { return f.status === 'error'; });
        var missed = files.filter(function (f) { return f.targetMissed; }).length;
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


def patch_markup(text: str, label: str, problems: list) -> str:
    # 1. the two new controls, right after the quality control
    if "target-size" in text:
        pass  # already applied
    else:
        m = QUALITY_CONTROL_RE.search(text)
        if not m:
            problems.append("%s: the quality control was not found" % label)
        else:
            text = text[:m.end()] + TARGET_CONTROL + text[m.end():]

    # 2. the two paragraphs
    #
    # The role anchor is the paragraph that talks about EXIF and the canvas:
    # the acronym EXIF survives machine translation in every language, while
    # the surrounding words do not. The paragraph to its left is the
    # "what this tool does" one. (An <h3> count would NOT work: the
    # Japanese copy uses <h2> where the English uses <h3>.)
    if "what_it_does.7h2k4m6n" in text:
        pass  # already applied
    else:
        ps = list(P_RE.finditer(text))
        idx = None
        for i, m in enumerate(ps):
            body = re.sub(r"<[^>]+>", "", m.group(0)).lower()
            if "exif" in body and "canvas" in body:
                idx = i
                break
        if idx is None or idx < 1:
            problems.append("%s: the EXIF paragraph was not found" % label)
        else:
            p1, p2 = ps[idx - 1], ps[idx]
            text = text[:p1.start()] + P_DOES + "\n                " + P_DOES_NOT + text[p2.end():]
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
                (SETTINGS_OLD, SETTINGS_NEW, "getCurrentSettings"),
                (ENCODE_OLD, ENCODE_NEW, "encode + EXIF"),
                (SUMMARY_DECL_OLD, SUMMARY_DECL_NEW, "summary decl"),
                (SUMMARY_OLD, SUMMARY_NEW, "summary html"),
            ):
                if text.count(new) >= 1:
                    continue
                if text.count(old) != 1:
                    problems.append("%s: anchor for '%s' found %d times"
                                    % (rel, note, text.count(old)))
                else:
                    text = text.replace(old, new)

            # the helper functions, before processOne
            if "function encodeToTarget" not in text:
                anchor = "      async function processOne(entry, settings) {\n"
                if text.count(anchor) != 1:
                    problems.append("%s: the processOne anchor was not found" % rel)
                else:
                    text = text.replace(anchor, HELPERS + anchor)

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
