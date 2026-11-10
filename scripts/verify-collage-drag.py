#!/usr/bin/env python3
"""
Verify the collage free-placement feature (§2.3).

WHAT IS ACTUALLY CLAIMED
------------------------
- Click a photo to select it.
- Drag a photo onto another cell: the two photos SWAP.
- Drag inside a cell: the crop is repositioned.
- Scroll over the selected photo: that photo zooms.
- The exported PNG is the preview, not a stale snapshot of it.

HOW IT IS MEASURED
------------------
The four test photos are solid colours with a WHITE STRIPE down their left
quarter. That makes every claim a pixel claim:

- the colour at a cell's centre says WHICH photo is in that cell;
- the white stripe at a cell's left edge says whether the crop is zoomed in
  (zoomed past 100%, the stripe is cropped away) or not.

The stripe is also what makes the zoom measurable: a solid colour cannot
change when you zoom it.

The export is checked against the preview by opening the downloaded PNG and
sampling the same four points. A stale blob - the failure mode where the
canvas moved but the PNG was not re-encoded - shows up as a mismatch.

Usage:  python scripts/verify-collage-drag.py
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
PORT = 8812

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


RECT_JS = """() => {
  var c = document.getElementById('preview-canvas');
  var r = c.getBoundingClientRect();
  return { left: r.left, top: r.top, w: r.width, h: r.height,
           cw: c.width, ch: c.height, hidden: c.hidden };
}"""

SAMPLE_JS = """(pts) => {
  var c = document.getElementById('preview-canvas');
  var ctx = c.getContext('2d');
  return pts.map(function (p) {
    var d = ctx.getImageData(p[0], p[1], 1, 1).data;
    return [d[0], d[1], d[2]];
  });
}"""

COLORS = [(220, 40, 40), (40, 200, 60), (50, 80, 230), (240, 210, 40)]
WHITE = (255, 255, 255)


def make_photo(path: Path, base) -> None:
    """A solid colour with a white stripe down the left quarter."""
    from PIL import Image
    im = Image.new("RGB", (400, 300), base)
    for y in range(300):
        for x in range(100):
            im.putpixel((x, y), WHITE)
    im.save(path, "PNG")


def compute_cells(canvas_w, canvas_h, padding, rows, cols):
    """The same formula the tool uses (computeCells in the page)."""
    edge = padding // 2
    inner_w = canvas_w - edge * 2
    inner_h = canvas_h - edge * 2
    cell_w = (inner_w - padding * (cols - 1)) // cols
    cell_h = (inner_h - padding * (rows - 1)) // rows
    cells = []
    for r in range(rows):
        for c in range(cols):
            cells.append({"x": edge + c * (cell_w + padding),
                          "y": edge + r * (cell_h + padding),
                          "w": cell_w, "h": cell_h})
    return cells


def close(a, b, tol=18):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def main():
    from playwright.sync_api import sync_playwright

    tmpdir = Path(tempfile.mkdtemp(prefix="wa-collage-"))
    photos = []
    for i, col in enumerate(COLORS):
        p = tmpdir / ("photo%d.png" % i)
        make_photo(p, col)
        photos.append(str(p))

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(0.6)
    url = "http://127.0.0.1:%d/tools/wedding-photo-collage/" % PORT
    print("serving on %d with the live CSP" % PORT)

    failures = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(accept_downloads=True,
                                    viewport={"width": 1280, "height": 900})
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))

            page.goto(url, wait_until="load", timeout=60000)
            page.set_input_files("#file-input", photos)
            page.wait_for_timeout(600)
            page.click("#run-btn")
            # NOT page.wait_for_function: that polls with eval(), and the
            # site's CSP has no 'unsafe-eval'. page.evaluate() is fine.
            end = time.time() + 180
            built = False
            while time.time() < end:
                built = page.evaluate(
                    "() => { var b = document.getElementById('download-btn'); return !!(b && !b.disabled); }")
                if built:
                    break
                page.wait_for_timeout(200)
            if not built:
                failures.append("the collage was never built (the download button "
                                "never became enabled)")
            page.wait_for_timeout(400)
            print("the collage was built")

            def scroll_in():
                page.evaluate("""() => {
                  document.getElementById('preview-canvas')
                          .scrollIntoView({block: 'center', behavior: 'instant'});
                }""")
                last = -1
                for _ in range(40):
                    y = page.evaluate("() => window.scrollY")
                    if y == last:
                        break
                    last = y
                    page.wait_for_timeout(50)
                page.wait_for_timeout(150)

            scroll_in()
            rect = page.evaluate(RECT_JS)
            pad = int(page.evaluate("() => document.getElementById('padding').value"))
            cells = compute_cells(rect["cw"], rect["ch"], pad, 2, 2)
            scale_x = rect["cw"] / rect["w"]
            scale_y = rect["ch"] / rect["h"]

            def client(cell, fx=0.5, fy=0.5):
                cx = cell["x"] + cell["w"] * fx
                cy = cell["y"] + cell["h"] * fy
                return (rect["left"] + cx / scale_x, rect["top"] + cy / scale_y)

            def centers():
                pts = [[c["x"] + c["w"] / 2, c["y"] + c["h"] / 2] for c in cells]
                return page.evaluate(SAMPLE_JS, pts)

            def stripe(cell):
                """The pixel just inside the cell's left edge."""
                return page.evaluate(SAMPLE_JS, [[cell["x"] + 5, cell["y"] + cell["h"] / 2]])[0]

            # --- 1. the photos are in the cells ---------------------------
            got = centers()
            print("  cell colours: %s" % got)
            if not all(close(got[i], COLORS[i]) for i in range(4)):
                failures.append("the four photos are not in the four cells: %s" % got)
            else:
                print("  the four photos are in the four cells")

            # --- 2. drag cell 0 onto cell 1: they swap -------------------
            src = client(cells[0])
            dst = client(cells[1])
            page.mouse.move(src[0], src[1])
            page.mouse.down()
            for i in range(1, 9):
                page.mouse.move(src[0] + (dst[0] - src[0]) * i / 8.0,
                                src[1] + (dst[1] - src[1]) * i / 8.0)
                page.wait_for_timeout(35)
            page.mouse.up()
            page.wait_for_timeout(500)

            got = centers()
            print("  after the drag: %s" % got)
            if not (close(got[0], COLORS[1]) and close(got[1], COLORS[0])
                    and close(got[2], COLORS[2]) and close(got[3], COLORS[3])):
                failures.append("the drag did not swap the two photos: %s" % got)
            else:
                print("  the drag swapped the two photos")

            # --- 3. the exported PNG is the preview ----------------------
            with page.expect_download(timeout=120000) as dl:
                page.click("#download-btn")
            out = tmpdir / "collage.png"
            dl.value.save_as(str(out))
            from PIL import Image
            with Image.open(out) as im:
                im = im.convert("RGB")
                exp = [im.getpixel((int(c["x"] + c["w"] / 2), int(c["y"] + c["h"] / 2)))
                       for c in cells]
                exp_size = im.size
            print("  the exported PNG is %dx%d, cell colours: %s" % (exp_size[0], exp_size[1], exp))
            if exp_size != (rect["cw"], rect["ch"]):
                failures.append("the exported PNG is %dx%d but the canvas is %dx%d"
                                % (exp_size[0], exp_size[1], rect["cw"], rect["ch"]))
            elif not all(close(exp[i], got[i]) for i in range(4)):
                failures.append("the export does not match the preview: %s vs %s" % (exp, got))
            else:
                print("  the export matches the preview")

            # --- 4. reset brings the order back --------------------------
            page.click("#reset-layout-btn")
            page.wait_for_timeout(500)
            got = centers()
            if not all(close(got[i], COLORS[i]) for i in range(4)):
                failures.append("the reset button did not restore the order: %s" % got)
            else:
                print("  the reset button restored the order")

            # --- 5. zoom a single photo ----------------------------------
            scroll_in()
            rect = page.evaluate(RECT_JS)
            scale_x = rect["cw"] / rect["w"]
            scale_y = rect["ch"] / rect["h"]
            before = stripe(cells[0])
            print("  the stripe at the cell's left edge is %s" % before)
            if not close(before, WHITE):
                failures.append("the test photo's white stripe is not visible at "
                                "the cell's left edge (%s) - the zoom test would "
                                "prove nothing" % before)
            page.mouse.click(*client(cells[0]))
            page.wait_for_timeout(300)
            page.evaluate("""() => {
              var z = document.getElementById('cell-zoom');
              z.value = 200;
              z.dispatchEvent(new Event('input', { bubbles: true }));
            }""")
            page.wait_for_timeout(600)
            after = stripe(cells[0])
            print("  after zooming to 200%% it is %s" % after)
            if close(after, WHITE):
                failures.append("the zoom did not change the crop - the stripe is "
                                "still at the cell's left edge")
            elif not close(after, COLORS[0]):
                failures.append("after zooming, the cell's left edge is %s, "
                                "expected the base colour %s" % (after, COLORS[0]))
            else:
                print("  the zoom cropped into the photo")

            # --- 6. reset brings the zoom back ---------------------------
            page.click("#reset-layout-btn")
            page.wait_for_timeout(500)
            back = stripe(cells[0])
            if not close(back, WHITE):
                failures.append("the reset button did not bring the zoom back "
                                "(the stripe is %s)" % back)
            else:
                print("  the reset button brought the zoom back")

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
    print("RESULT: OK - the photos swap by drag, the zoom crops into one photo, "
          "the reset restores both, and the export matches the preview")
    return 0


if __name__ == "__main__":
    sys.exit(main())
