#!/usr/bin/env python3
"""
Verify that the text can be dragged on the photo (§2.2).

WHY THIS NEEDS PIXELS
--------------------
"The drag handler is wired up" is not a claim. The claim is that the
text ENDS UP WHERE THE USER PUT IT - in the preview AND in the exported
file. So the test measures the text's actual bounding box on the canvas
before and after the drag, and then measures it again in the exported
JPEG.

The test photo is a flat dark rectangle. The text is white, so the
bright pixels ARE the text and its bounding box can be measured exactly
- no guessing about where a glyph ended up.

The preview canvas is FULL SIZE (the photo's natural width) and
DISPLAYED scaled down, so the drag has to be mapped through the display
scale. The test uses a photo that is bigger than the 720px preview cap
on purpose: a drag that ignored the scale would move the text by the
wrong number of pixels and the assertion would catch it.

Usage:  python scripts/verify-add-text-drag.py
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
PORT = 8809

_headers = (ROOT / "_headers").read_text(encoding="utf-8")
_m = re.search(r"^\s*Content-Security-Policy:\s*(.+)$", _headers, re.M)
if not _m:
    raise SystemExit("[FAIL] no Content-Security-Policy in _headers")
CSP_TEMPLATE = _m.group(1).strip()
NONCE = "weddingaiverify123456"


def build_csp():
    csp = CSP_TEMPLATE.replace("'unsafe-inline' 'wasm-unsafe-eval'",
                                f"'nonce-{NONCE}' 'wasm-unsafe-eval'")
    return re.sub(r"'nonce-[^']+'", f"'nonce-{NONCE}'", csp)


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
                    lambda m: (m.group(1) + m.group(2) + f' nonce="{NONCE}"' + ">")
                    if "nonce=" not in m.group(2) else m.group(0),
                    html)
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


# Find the bounding box of the bright (text) pixels on the preview canvas.
BOX_JS = r"""
() => {
  var c = document.getElementById('preview-canvas');
  var ctx = c.getContext('2d');
  var d = ctx.getImageData(0, 0, c.width, c.height).data;
  var minX = 1e9, minY = 1e9, maxX = -1, maxY = -1, n = 0;
  for (var y = 0; y < c.height; y++) {
    for (var x = 0; x < c.width; x++) {
      var i = (y * c.width + x) * 4;
      if (d[i] > 180 && d[i + 1] > 180 && d[i + 2] > 180) {
        n++;
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }
  var r = c.getBoundingClientRect();
  return {
    found: n, minX: minX, minY: minY, maxX: maxX, maxY: maxY,
    canvasW: c.width, canvasH: c.height,
    rectLeft: r.left, rectTop: r.top, rectW: r.width, rectH: r.height,
    scaleX: r.width ? c.width / r.width : 1,
    scaleY: r.height ? c.height / r.height : 1
  };
}
"""


def make_flat_photo(path: Path) -> None:
    """A flat dark photo: the white text is the only bright thing on it."""
    from PIL import Image
    Image.new("RGB", (1200, 900), (16, 16, 16)).save(path, "JPEG", quality=95)


def bright_box_png(path: Path):
    """The bounding box of the bright pixels in an exported image."""
    from PIL import Image
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        px = im.load()
        minX, minY, maxX, maxY, n = 1e9, 1e9, -1, -1, 0
        for y in range(h):
            for x in range(w):
                r, g, b = px[x, y]
                if r > 180 and g > 180 and b > 180:
                    n += 1
                    if x < minX:
                        minX = x
                    if x > maxX:
                        maxX = x
                    if y < minY:
                        minY = y
                    if y > maxY:
                        maxY = y
        return {"found": n, "minX": minX, "minY": minY, "maxX": maxX, "maxY": maxY,
                "w": w, "h": h}


def main():
    from playwright.sync_api import sync_playwright

    tmpdir = Path(tempfile.mkdtemp(prefix="wa-drag-"))
    photo = tmpdir / "flat.jpg"
    make_flat_photo(photo)

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.6)
    url = "http://127.0.0.1:%d/tools/add-text-to-wedding-photo/" % PORT
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
            print("loaded %s" % url)

            page.fill("#primary-text", "Avery & Jordan")
            page.fill("#secondary-text", "Save the Date")
            page.set_input_files("#file-input", str(photo))
            page.wait_for_timeout(1500)

            if page.query_selector("#reset-position-btn") is None:
                failures.append("the reset-position button is missing")

            def aim():
                """Scroll the canvas into view, wait for the scroll to settle,
                and return (box, click_x, click_y) measured FROM THE SCREEN.

                Two traps are closed here:
                  - the site sets `html { scroll-behavior: smooth }`, so a
                    default scrollIntoView ANIMATES; measuring mid-animation
                    gives a rect that no longer matches the screen;
                  - clicking the reset button scrolls the page, so every
                    drag has to re-measure instead of reusing old numbers.
                """
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
                b = page.evaluate(BOX_JS, None)
                if not b["found"]:
                    return b, None, None
                x = b["rectLeft"] + (b["minX"] + b["maxX"]) / 2 / b["scaleX"]
                y = b["rectTop"] + (b["minY"] + b["maxY"]) / 2 / b["scaleY"]
                return b, x, y

            box, cx, cy = aim()
            if not box["found"]:
                failures.append("no text pixels found on the preview canvas")
                print("  no text found: %s" % box)
            else:
                print("  the text starts at (%d,%d)-(%d,%d) in a %dx%d canvas"
                      % (box["minX"], box["minY"], box["maxX"], box["maxY"],
                         box["canvasW"], box["canvasH"]))
                print("  the canvas is displayed at %dx%d (scale %.3f x %.3f)"
                      % (box["rectW"], box["rectH"], box["scaleX"], box["scaleY"]))
                # The preview must not be squashed: the displayed box has to
                # keep the photo's aspect ratio, or the preview shows a
                # different picture than the file that gets exported.
                want = box["canvasW"] / float(box["canvasH"])
                got = box["rectW"] / float(box["rectH"]) if box["rectH"] else 0
                if abs(want - got) > 0.02:
                    failures.append("the preview is squashed: the canvas is %dx%d "
                                    "but it is displayed at %dx%d (ratio %.3f vs "
                                    "%.3f) - the preview does not match the export"
                                    % (box["canvasW"], box["canvasH"],
                                       box["rectW"], box["rectH"], want, got))

            # --- drag the text ------------------------------------------
            # The two axes can have different scales, so each one is mapped
            # separately.
            vp = page.viewport_size
            if cx is not None and not (0 <= cx < vp["width"] and 0 <= cy < vp["height"]):
                failures.append("the text is at (%.1f,%.1f), outside the %dx%d "
                                "viewport - the drag could not have been aimed "
                                "at it" % (cx, cy, vp["width"], vp["height"]))
            # Drag it left and up by a known number of DISPLAY pixels.
            ddx, ddy = -140.0, -90.0
            print("  dragging from (%.1f,%.1f) by (%.0f,%.0f) display px"
                  % (cx, cy, ddx, ddy))
            page.mouse.move(cx, cy)
            page.mouse.down()
            # Move in a few steps so the pointermove handler sees a drag.
            for i in range(1, 6):
                page.mouse.move(cx + ddx * i / 5.0, cy + ddy * i / 5.0)
                page.wait_for_timeout(40)
            page.mouse.up()
            page.wait_for_timeout(400)

            box2 = page.evaluate(BOX_JS, None)
            if not box2["found"]:
                failures.append("the text disappeared from the preview after the drag")
            else:
                print("  the text is now at (%d,%d)-(%d,%d)"
                      % (box2["minX"], box2["minY"], box2["maxX"], box2["maxY"]))
                exp_dx = ddx * box["scaleX"]
                exp_dy = ddy * box["scaleY"]
                got_dx = box2["minX"] - box["minX"]
                got_dy = box2["minY"] - box["minY"]
                print("  moved by (%.1f, %.1f); expected about (%.1f, %.1f)"
                      % (got_dx, got_dy, exp_dx, exp_dy))
                # A tolerance of a few pixels: the glyphs are not a solid
                # rectangle, so the measured edge can move by a pixel.
                if abs(got_dx - exp_dx) > 12 or abs(got_dy - exp_dy) > 12:
                    failures.append("the text moved by (%.1f, %.1f) but the drag was "
                                    "(%.1f, %.1f) in canvas pixels - the display scale "
                                    "is not being applied" % (got_dx, got_dy, exp_dx, exp_dy))

            # --- the reset button ----------------------------------------
            reset = page.query_selector("#reset-position-btn")
            if reset is None:
                failures.append("the reset-position button is missing")
            elif reset.is_disabled():
                # It is only enabled once the text is off its default spot,
                # so a disabled button here means the drag did not register.
                failures.append("the reset button is still disabled after the drag - "
                                "the drag never moved the text")
            else:
                reset.click()
                page.wait_for_timeout(400)
                box3 = page.evaluate(BOX_JS, None)
                if box3["found"] and (abs(box3["minX"] - box["minX"]) > 4 or
                                      abs(box3["minY"] - box["minY"]) > 4):
                    failures.append("the reset button did not put the text back "
                                    "(%d,%d vs %d,%d)" % (box3["minX"], box3["minY"],
                                                           box["minX"], box["minY"]))
                else:
                    print("  the reset button put the text back")

            # --- drag again, then export ---------------------------------
            # The reset click scrolled the page, so re-aim before the second
            # drag - and CHECK that the text actually moved, otherwise the
            # export-vs-preview comparison below would compare two identical
            # positions and prove nothing.
            box4, cx2, cy2 = aim()
            if not box4["found"]:
                failures.append("the text is gone from the preview before the "
                                "second drag")
            else:
                page.mouse.move(cx2, cy2)
                page.mouse.down()
                for i in range(1, 6):
                    page.mouse.move(cx2 + ddx * i / 5.0, cy2 + ddy * i / 5.0)
                    page.wait_for_timeout(40)
                page.mouse.up()
                page.wait_for_timeout(400)
                preview_box = page.evaluate(BOX_JS, None)
                moved = (preview_box["found"] and
                         (abs(preview_box["minX"] - box4["minX"]) > 8 or
                          abs(preview_box["minY"] - box4["minY"]) > 8))
                print("  the second drag moved the text from (%d,%d) to (%d,%d)"
                      % (box4["minX"], box4["minY"],
                         preview_box["minX"], preview_box["minY"]))
                if not moved:
                    failures.append("the second drag did not move the text - "
                                    "the export check would be vacuous")

            page.click("#run-btn")
            page.wait_for_selector(".wa-tool-status-done, .wa-tool-status-error", timeout=300000)
            state = page.evaluate("""() => {
                var row = document.querySelector('#file-list .wa-tool-file-row');
                var err = document.querySelector('.wa-tool-err');
                return { cls: row ? row.className : '(no row)',
                         err: err ? err.textContent : null };
            }""")
            if "wa-tool-status-done" not in state["cls"]:
                failures.append("the export ended in %s: %s" % (state["cls"], state["err"]))
            else:
                out = tmpdir / "exported.jpg"
                with page.expect_download(timeout=120000) as dl:
                    page.click(".wa-tool-status-done .wa-tool-actions button")
                dl.value.save_as(str(out))
                exp = bright_box_png(out)
                print("  the exported file is %dx%d, text at (%d,%d)-(%d,%d)"
                      % (exp["w"], exp["h"], exp["minX"], exp["minY"],
                         exp["maxX"], exp["maxY"]))
                print("  the preview showed the text at (%d,%d)-(%d,%d)"
                      % (preview_box["minX"], preview_box["minY"],
                         preview_box["maxX"], preview_box["maxY"]))
                if not exp["found"]:
                    failures.append("the exported file has no text pixels")
                elif (abs(exp["minX"] - preview_box["minX"]) > 6 or
                      abs(exp["minY"] - preview_box["minY"]) > 6):
                    failures.append("the export does not match the preview: the text is "
                                    "at (%d,%d) in the file but at (%d,%d) on screen"
                                    % (exp["minX"], exp["minY"],
                                       preview_box["minX"], preview_box["minY"]))
                else:
                    print("  the export and the preview agree")

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
    print("RESULT: OK - the text is draggable, the drag respects the display scale, "
          "the reset button works, and the export matches the preview")
    return 0


if __name__ == "__main__":
    sys.exit(main())
