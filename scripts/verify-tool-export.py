#!/usr/bin/env python3
"""
Export a tool page's file for real and check the bytes that come out.

WHY THIS EXISTS
---------------
A tool page can look perfect and still produce a broken file. Two real
defects on the wedding stationery page (2026-11-10) were invisible in the
source, invisible in the DOM, and invisible in every screenshot:

  1. The draw functions were handed the STYLE object instead of the piece,
     so every coordinate was NaN. Per the HTML spec a NaN coordinate makes
     fillText draw NOTHING - so every exported PNG was a single flat
     colour. The page still showed the right size ("1500 x 2100 px"), the
     buttons still worked, and the PDF still had six pages of the right
     dimensions. Only the artwork was missing.
  2. The font gate never fired. js/tools/common.js is a DEFERRED script,
     so window.weddingAITool is undefined while the inline script runs;
     the guard `if (window.weddingAITool && ...)` was simply false. The
     exported file therefore baked whichever fallback face happened to be
     installed - Georgia on one machine, Comic Sans on another.

Both are invisible to a static check. Both are visible in the exported
bytes. So the check exports the file and looks at the bytes.

THE CHECKS (each one fails against the code it was written for)
----------------------------------------------------------------
  A. the preview canvas contains more than one colour
     -> against the NaN bug: 1 colour (a flat background).
  B. the exported PNG contains more than one colour
     -> against the NaN bug: 1 colour.
  C. the exported PNG contains the INK colour of the chosen style
     -> against a "drawn but in the wrong colour" bug.
  D. the exported PDF has one page per selected piece and every page keeps
     its own size in inches
     -> against a "every page is the canvas pixel size" bug.
  E. document.fonts.load was called for the three design families
     -> against the never-fired font gate: zero calls.

Usage
-----
    python scripts/verify-tool-export.py --slug wedding-stationery-set-maker
    python scripts/verify-tool-export.py --slug <slug> --keep-artifacts DIR
"""

import argparse
import collections
import http.server
import os
import re
import shutil
import socketserver
import struct
import sys
import tempfile
import threading
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The piece sizes the stationery set promises, in inches.
EXPECTED_PAGES = [
    (5.0, 7.0),
    (3.5, 5.0),
    (3.5, 2.0),
    (3.5, 2.0),
    (4.25, 5.5),
    (18.0, 24.0),
]


# --------------------------------------------------------------------------
# PNG decoding (no third-party imaging library)
# --------------------------------------------------------------------------
def png_colors(path, step=None):
    """Return (width, height, Counter of sampled RGB tuples)."""
    data = Path(path).read_bytes()
    pos, idat = 8, b""
    w = h = bd = ct = None
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT":
            idat += body
        pos += 12 + ln
    if w is None:
        raise ValueError("not a PNG")
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    bpp = ch * (bd // 8)
    stride = w * bpp
    out = bytearray()
    prev = bytearray(stride)
    i = 0
    for _ in range(h):
        f = raw[i]
        i += 1
        line = bytearray(raw[i:i + stride])
        i += stride
        if f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + (a + prev[x]) // 2) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                c = prev[x - bpp] if x >= bpp else 0
                b = prev[x]
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out += line
        prev = line
    cols = collections.Counter()
    ys = max(1, h // 400)
    xs = max(1, w // 400)
    for y in range(0, h, ys):
        row = out[y * stride:(y + 1) * stride]
        for x in range(0, w, xs):
            cols[tuple(row[x * bpp:(x + 1) * bpp][:3])] += 1
    return w, h, cols


def pdf_page_sizes(path):
    """Return the page sizes in inches, from the /MediaBox entries."""
    raw = Path(path).read_bytes()
    sizes = []
    for m in re.finditer(rb"/MediaBox\s*\[\s*([\d.+-]+)\s+([\d.+-]+)\s+"
                         rb"([\d.+-]+)\s+([\d.+-]+)\s*\]", raw):
        x0, y0, x1, y1 = (float(g) for g in m.groups())
        sizes.append((round((x1 - x0) / 72.0, 3), round((y1 - y0) / 72.0, 3)))
    return sizes


# --------------------------------------------------------------------------
# a throwaway static server
# --------------------------------------------------------------------------
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    # When the negative control is on, the served HTML has the NaN bug
    # put back. That is how the checker proves it is not a checker that
    # always passes.
    bug = None

    def log_message(self, *args):
        pass

    def translate_path(self, path):
        path = path.split("?", 1)[0].split("#", 1)[0]
        return super().translate_path(path)

    def do_GET(self):
        if self.bug and self.path.rstrip("/").endswith("/" + self.bug):
            body = self._serve_body()
            if body:
                text = body.decode("utf-8", "replace")
                patched = text.replace(
                    "DRAW[piece.id](c, spec, scale);",
                    "DRAW[piece.id](c, style, scale);")
                if patched == text:
                    print("[negative-control] the bug marker was not found - "
                          "the control did not actually reintroduce the bug")
                data = patched.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
        super().do_GET()

    def _serve_body(self):
        path = self.translate_path(self.path)
        # translate_path() returns the DIRECTORY for a directory URL, and
        # opening a directory fails - so the page was served unmodified and
        # the negative control silently did nothing.
        if os.path.isdir(path):
            path = os.path.join(path, "index.html")
        try:
            with open(path, "rb") as fh:
                return fh.read()
        except OSError:
            return None


def serve(root):
    handler = type("H", (QuietHandler,), {"directory": str(root)})
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--keep-artifacts", default=None)
    ap.add_argument("--negative-control", action="store_true",
                    help="reintroduce the NaN bug in the served HTML and "
                         "require the checker to FAIL on it")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("[FAIL] playwright is not installed - pip install playwright "
                         "&& playwright install chromium")

    outdir = Path(args.keep_artifacts) if args.keep_artifacts else Path(tempfile.mkdtemp(prefix="tool-export-"))
    outdir.mkdir(parents=True, exist_ok=True)

    httpd, port = serve(ROOT)
    base = "http://127.0.0.1:%d" % port
    if args.negative_control:
        QuietHandler.bug = args.slug
        print("[negative-control] the NaN bug is being put back into the "
              "served HTML; the checker MUST report a failure")
    problems = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append("console:" + m.text)
                    if m.type == "error" else None)

            # Instrument the font gate BEFORE any script runs.
            page.add_init_script(
                "window.__FONT_CALLS__ = [];"
                "const orig = document.fonts && document.fonts.load;"
                "if (orig) { document.fonts.load = function (f, t) "
                "{ window.__FONT_CALLS__.push(String(f)); return orig.call(document.fonts, f, t); }; }"
            )

            page.goto("%s/tools/%s/" % (base, args.slug), wait_until="load")
            page.wait_for_timeout(2500)

            # Fill the form so the artwork has something to draw.
            fields = {
                "#partner-one": "Emma",
                "#partner-two": "Liam",
                "#wedding-date": "June 14, 2026",
                "#wedding-time": "4:30 PM",
                "#venue": "The Old Mill Barn",
                "#city": "Hudson, NY",
                "#rsvp-by": "May 1, 2026",
                "#guest-name": "Alex Rivera",
                "#table-number": "4",
            }
            for sel, value in fields.items():
                el = page.query_selector(sel)
                if el:
                    el.fill(value)
            page.wait_for_timeout(1500)

            # --- A. the preview canvas ------------------------------------
            info = page.evaluate("""() => {
                const c = document.getElementById('preview-canvas');
                if (!c) return null;
                const ctx = c.getContext('2d');
                const d = ctx.getImageData(0, 0, c.width, c.height).data;
                const seen = new Set();
                for (let i = 0; i < d.length; i += 4 * 97) {
                    seen.add(d[i] + ',' + d[i+1] + ',' + d[i+2]);
                }
                return { w: c.width, h: c.height, colours: seen.size };
            }""")
            if not info:
                problems.append("A. no #preview-canvas on the page")
            elif info["colours"] <= 1:
                problems.append("A. the preview canvas is ONE colour (%s) - nothing was drawn"
                                % info)

            # --- B/C. the exported PNG -------------------------------------
            png_path = outdir / "piece.png"
            try:
                with page.expect_download(timeout=60000) as dl:
                    page.click("#download-piece-btn")
                dl.value.save_as(str(png_path))
            except Exception as exc:  # noqa: BLE001
                problems.append("B. the PNG download never happened: %s" % exc)
                png_path = None

            if png_path and png_path.exists() and png_path.stat().st_size > 0:
                w, h, cols = png_colors(png_path)
                if len(cols) <= 1:
                    problems.append("B. the exported PNG is ONE colour - the artwork is missing")
                else:
                    print("   PNG %dx%d, %d distinct colours" % (w, h, len(cols)))
                ink = (43, 43, 43)          # styles.classic.ink
                if ink not in cols:
                    problems.append("C. the exported PNG has no ink colour %s - "
                                    "the text was not drawn" % (ink,))
            elif png_path is not None:
                problems.append("B. the exported PNG is empty")

            # --- D. the exported PDF --------------------------------------
            pdf_path = outdir / "set.pdf"
            try:
                with page.expect_download(timeout=180000) as dl:
                    page.click("#download-set-btn")
                dl.value.save_as(str(pdf_path))
            except Exception as exc:  # noqa: BLE001
                problems.append("D. the PDF download never happened: %s" % exc)
                pdf_path = None

            if pdf_path and pdf_path.exists() and pdf_path.stat().st_size > 0:
                sizes = pdf_page_sizes(pdf_path)
                print("   PDF %.1f KB, %d pages" % (pdf_path.stat().st_size / 1024.0, len(sizes)))
                if len(sizes) != len(EXPECTED_PAGES):
                    problems.append("D. the PDF has %d pages, expected %d"
                                    % (len(sizes), len(EXPECTED_PAGES)))
                for i, (got, want) in enumerate(zip(sizes, EXPECTED_PAGES)):
                    if abs(got[0] - want[0]) > 0.02 or abs(got[1] - want[1]) > 0.02:
                        problems.append("D. page %d is %s in, expected %s in"
                                        % (i + 1, got, want))
            elif pdf_path is not None:
                problems.append("D. the exported PDF is empty")

            # --- E. the font gate -----------------------------------------
            calls = page.evaluate("() => window.__FONT_CALLS__ || []")
            families = " ".join(calls)
            for family in ("Playfair Display", "Great Vibes", "Inter"):
                if family not in families:
                    problems.append("E. document.fonts.load was never called for %r "
                                    "- the font gate never fires" % family)

            if errors:
                problems.append("page errors: %s" % "; ".join(errors[:5]))

            browser.close()
    finally:
        httpd.shutdown()

    if problems:
        print("\n[FAIL] %d problem(s):" % len(problems))
        for p in problems:
            print("  - %s" % p)
        print("\nartifacts: %s" % outdir)
        if args.negative_control:
            print("\n[OK] the negative control did its job: the checker "
                  "detected the bug it was given.")
            return 0
        return 1
    if args.negative_control:
        print("\n[FAIL] the negative control was NOT detected - the checker "
              "cannot see the bug it was given, so it proves nothing.")
        return 1
    print("\n[OK] the export produces real artwork, a mixed-size PDF and a live font gate")
    print("artifacts: %s" % outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
