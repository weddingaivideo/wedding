#!/usr/bin/env python3
"""
Verify the photo-book free placement and the print-ready PDF (§2.4).

WHAT IS ACTUALLY CLAIMED
------------------------
- Drag a photo from the library onto a slot: it is placed there.
- Drag a photo from one slot onto another: the two SWAP.
- Scroll over a slot: that photo is zoomed, and the crop follows.
- "Download all pages (print-ready PDF)" produces ONE PDF whose page is the
  book size in INCHES - an 8x8 book gives an 8x8 inch page, so a 2400 px
  image lands at 300 DPI. The page promised a print-ready PDF and used to
  export N loose PNGs, so the PDF itself is part of the claim.

HOW IT IS MEASURED
------------------
Each test photo is solid colour with a WHITE band across its top quarter.
That makes every claim a pixel claim:

- the colour at 75% of a slot's height says WHICH photo is in that slot;
- the pixel at 25% of the height says whether the crop is zoomed in - under
  a centred zoom the white band moves up, and the pixel below it changes
  from white to the photo's own colour.

A solid photo cannot show a zoom, which is why the band is there.

The PDF is opened as bytes and its MediaBox is read: 8 inches at 72 pt per
inch is 576. A PDF whose page is 2400 pt would be a 33-inch poster, not a
print file.

Usage:  python scripts/verify-book-placement.py
Exit code 0 = verified, 1 = failed.
"""
import http.server
import re
import socketserver
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8813

_headers = (ROOT / "_headers").read_text(encoding="utf-8")
_m = re.search(r"^\s*Content-Security-Policy:\s*(.+)$", _headers, re.M)
if not _m:
    raise SystemExit("[FAIL] no Content-Security-Policy in _headers")
CSP_TEMPLATE = _m.group(1).strip()
NONCE = "weddingaiverify123456"


def build_csp():
    csp = CSP_TEMPLATE.replace("'unsafe-inline' 'wasm-unsafe-eval'",
                                "'nonce-%s' 'wasm-unsafe-eval'" % NONCE)
    return re.sub(r"'nonce-[^']+'", "'nonce-%s'" % NONCE, csp)


CSP = build_csp()
SCRIPT_RE = re.compile(r"(<script\b)([^>]*)>", re.I)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw, directory=str(ROOT))

    def end_headers(self):
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.endswith(".html") or path.endswith("/"):
            target = ROOT / path.lstrip("/")
            if target.is_dir():
                target = target / "index.html"
            if target.exists() and target.is_file():
                html = target.read_text(encoding="utf-8", errors="ignore")
                html = SCRIPT_RE.sub(
                    lambda m: (m.group(1) + m.group(2) + ' nonce="%s"' % NONCE + ">")
                    if "nonce=" not in m.group(2) else m.group(0), html)
                body = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        return super().do_GET()

    def log_message(self, *a):
        pass

    def handle_error(self, *a):
        pass


COLORS = [(220, 40, 40), (40, 200, 60)]
WHITE = (255, 255, 255)


def make_photo(path: Path, base) -> None:
    """Solid colour with a WHITE band across the top quarter."""
    from PIL import Image
    im = Image.new("RGB", (400, 300), base)
    for y in range(0, 100):
        for x in range(400):
            im.putpixel((x, y), WHITE)
    im.save(path, "PNG")


RECT_JS = """(sel) => {
  var el = document.querySelector(sel);
  if (!el) return null;
  var r = el.getBoundingClientRect();
  return { left: r.left, top: r.top, w: r.width, h: r.height };
}"""

SLOT_PIXEL_JS = """(args) => {
  var el = document.querySelector('.pb-slot[data-slot-idx="' + args.idx + '"]');
  if (!el) return null;
  var c = el.querySelector('canvas');
  if (!c) return null;
  var ctx = c.getContext('2d');
  var d = ctx.getImageData(Math.floor(c.width * args.fx), Math.floor(c.height * args.fy), 1, 1).data;
  return [d[0], d[1], d[2]];
}"""

SLOT_COUNT_JS = """() => document.querySelectorAll('#editor-slots .pb-slot').length"""


def close(a, b, tol=18):
    if a is None or b is None:
        return False
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def main():
    from playwright.sync_api import sync_playwright

    tmpdir = Path(tempfile.mkdtemp(prefix="wa-book-"))
    photos = []
    for i, col in enumerate(COLORS):
        p = tmpdir / ("photo%d.png" % i)
        make_photo(p, col)
        photos.append(str(p))

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(0.6)
    url = "http://127.0.0.1:%d/tools/wedding-photo-book-planner/" % PORT
    print("serving on %d with the live CSP" % PORT)

    failures = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(accept_downloads=True,
                                    viewport={"width": 1400, "height": 1500})
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))

            page.goto(url, wait_until="load", timeout=60000)
            # The album size is a select with 20/40/60 pages; 20 is the
            # smallest, so the PDF is 20 pages.
            page.select_option("#book-pages", "20")
            page.wait_for_timeout(400)
            page.set_input_files("#photo-input", photos)
            page.wait_for_timeout(1200)
            print("two photos in the library")

            # Open page 1 and make it a two-photo layout.
            page.click(".pb-page-thumb[data-page-idx='0']")
            page.wait_for_timeout(600)
            page.evaluate("""() => {
              var el = document.getElementById('editor-layout');
              el.value = '2photo';
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }""")
            page.wait_for_timeout(600)

            def settle():
                last = -1
                for _ in range(40):
                    y = page.evaluate("() => window.scrollY")
                    if y == last:
                        break
                    last = y
                    page.wait_for_timeout(50)
                page.wait_for_timeout(150)

            settle()
            n = page.evaluate(SLOT_COUNT_JS)
            print("  the editor shows %s slot(s)" % n)
            if n != 2:
                failures.append("the editor shows %s slots, expected 2" % n)

            def slot_pixel(idx, fy):
                return page.evaluate(SLOT_PIXEL_JS, {"idx": idx, "fx": 0.5, "fy": fy})

            def library_rect(i):
                return page.evaluate(RECT_JS, ".pb-photo-item[data-photo-id]:nth-of-type(%d)" % (i + 1))

            def slot_rect(i):
                return page.evaluate(RECT_JS, ".pb-slot[data-slot-idx='%d']" % i)

            def drag(src, dst, steps=10):
                page.mouse.move(src[0], src[1])
                page.mouse.down()
                for k in range(1, steps + 1):
                    page.mouse.move(src[0] + (dst[0] - src[0]) * k / steps,
                                    src[1] + (dst[1] - src[1]) * k / steps)
                    page.wait_for_timeout(30)
                page.mouse.up()
                page.wait_for_timeout(400)

            # --- 1. drag a library photo onto a slot --------------------
            lib = library_rect(0)
            slot0 = slot_rect(0)
            if not lib or not slot0:
                failures.append("the library item or the slot has no box")
            else:
                print("  library item at (%.0f,%.0f), slot 0 at (%.0f,%.0f)"
                      % (lib["left"], lib["top"], slot0["left"], slot0["top"]))
                drag((lib["left"] + 30, lib["top"] + lib["h"] / 2),
                     (slot0["left"] + slot0["w"] / 2, slot0["top"] + slot0["h"] / 2))
                got = slot_pixel(0, 0.75)
                print("  slot 0 now shows %s" % got)
                if not close(got, COLORS[0]):
                    failures.append("the drag did not put the library photo into the "
                                    "slot (slot 0 shows %s, expected %s)" % (got, COLORS[0]))
                else:
                    print("  the library photo landed in the slot")

            # --- 2. drag the second library photo into slot 1 -----------
            lib2 = library_rect(1)
            slot1 = slot_rect(1)
            if lib2 and slot1:
                drag((lib2["left"] + 30, lib2["top"] + lib2["h"] / 2),
                     (slot1["left"] + slot1["w"] / 2, slot1["top"] + slot1["h"] / 2))
                got1 = slot_pixel(1, 0.75)
                print("  slot 1 now shows %s" % got1)
                if not close(got1, COLORS[1]):
                    failures.append("the second drag did not land (slot 1 shows %s, "
                                    "expected %s)" % (got1, COLORS[1]))
                else:
                    print("  the second photo landed in the second slot")

            # --- 3. drag slot 0 onto slot 1: they swap -------------------
            s0 = slot_rect(0)
            s1 = slot_rect(1)
            if s0 and s1:
                drag((s0["left"] + s0["w"] / 2, s0["top"] + s0["h"] / 2),
                     (s1["left"] + s1["w"] / 2, s1["top"] + s1["h"] / 2))
                a = slot_pixel(0, 0.75)
                b = slot_pixel(1, 0.75)
                print("  after the swap: slot 0 = %s, slot 1 = %s" % (a, b))
                if not (close(a, COLORS[1]) and close(b, COLORS[0])):
                    failures.append("the slots did not swap (%s / %s)" % (a, b))
                else:
                    print("  the two slots swapped")

            # --- 4. zoom one slot ----------------------------------------
            # The zoom applies to the SELECTED slot, so select slot 0
            # first. (The click also opens the old pick-a-photo prompt,
            # which the browser dismisses.)
            s0 = slot_rect(0)
            if s0:
                page.mouse.click(s0["left"] + s0["w"] / 2, s0["top"] + s0["h"] / 2)
                page.wait_for_timeout(500)
            top_before = slot_pixel(0, 0.25)
            print("  slot 0 at 25%% height is %s" % top_before)
            if not close(top_before, WHITE):
                failures.append("the white band is not where the test expects it "
                                "(%s) - the zoom test would prove nothing" % top_before)
            page.evaluate("""() => {
              var el = document.getElementById('slot-zoom');
              el.value = '200';
              el.dispatchEvent(new Event('input', { bubbles: true }));
            }""")
            page.wait_for_timeout(600)
            top_after = slot_pixel(0, 0.25)
            print("  after zooming to 200%% it is %s" % top_after)
            if close(top_after, WHITE):
                failures.append("the zoom did not change the crop")
            elif not close(top_after, COLORS[1]):
                failures.append("after zooming, slot 0 at 25%% height is %s, expected "
                                "the photo's own colour %s" % (top_after, COLORS[1]))
            else:
                print("  the zoom cropped into the photo")

            # --- 5. the print-ready PDF ---------------------------------
            with page.expect_download(timeout=300000) as dl:
                page.click("#download-all-btn")
            pdf_path = tmpdir / "album.pdf"
            dl.value.save_as(str(pdf_path))
            data = pdf_path.read_bytes()
            print("  the album PDF is %d bytes" % len(data))
            if not data.startswith(b"%PDF"):
                failures.append("the download is not a PDF (%r)" % data[:12])
            else:
                box = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]", data)
                if not box:
                    failures.append("the PDF has no readable MediaBox")
                else:
                    w = float(box.group(1))
                    h = float(box.group(2))
                    print("  the PDF page is %.0f x %.0f pt = %.2f x %.2f inch"
                          % (w, h, w / 72.0, h / 72.0))
                    if abs(w - 576) > 2 or abs(h - 576) > 2:
                        failures.append("the PDF page is %.0fx%.0f pt; an 8x8 inch "
                                        "book must be 576x576 pt (300 DPI), not a "
                                        "%.0f-inch poster" % (w, h, w / 72.0))
                    else:
                        print("  the PDF page is the book size in inches - 300 DPI")
                pages = len(re.findall(rb"/Type\s*/Page[^s]", data))
                print("  the PDF has %d page(s)" % pages)
                if pages != 20:
                    failures.append("the PDF has %d pages, expected 20" % pages)

            csp_errors = [e for e in errors if "Content Security Policy" in e or "Refused to" in e]
            for e in csp_errors:
                failures.append("CSP violation: " + e[:220])
            for e in [e for e in errors if e not in csp_errors][:6]:
                print("  console error:", e[:200])

            browser.close()
    finally:
        httpd.shutdown()

    print()
    if failures:
        print("RESULT: FAIL")
        for f in failures:
            print("  - " + f)
        return 1
    print("RESULT: OK - the photos are placed and swapped by drag, the zoom "
          "crops into one photo, and the album exports as one print-ready PDF")
    return 0


if __name__ == "__main__":
    sys.exit(main())
