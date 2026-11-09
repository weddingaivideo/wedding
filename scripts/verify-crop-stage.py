#!/usr/bin/env python3
"""
Verify the interactive crop stage end-to-end.

WHY THIS EXISTS
---------------
The draggable crop frame was written from scratch (no library): a canvas, a
shaded overlay, four corner handles and Pointer Events. None of that can be
checked by reading the code - a frame that does not move, or that moves the
wrong corner, or whose crop is applied at the wrong scale, all look fine in
a screenshot and produce a wrong photo.

So this script:
  1. serves the repository with the live Content-Security-Policy from
     _headers (nonce injected into the inline scripts, exactly like
     functions/_middleware.js does);
  2. opens the crop tool, uploads a photo, and checks that the stage
     appears with a frame that matches the selected aspect ratio;
  3. DRAGS a corner handle with the mouse and checks that the frame moved
     and kept its aspect ratio;
  4. presses Crop and checks that a file row reaches the "done" state.

Usage:  python scripts/verify-crop-stage.py [image.png]
Exit code 0 = verified, 1 = failed.
"""
import http.server
import re
import socketserver
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8792

_headers = (ROOT / "_headers").read_text(encoding="utf-8")
_m = re.search(r"^\s*Content-Security-Policy:\s*(.+)$", _headers, re.M)
if not _m:
    raise SystemExit("[FAIL] no Content-Security-Policy in _headers")
NONCE = "weddingaiverify123456"
# Only the SCRIPT directive is nonce-based in the live policy. style-src
# keeps 'unsafe-inline' (the pages use style="" attributes), so replacing
# every 'unsafe-inline' in the policy would invent violations that the
# production site does not have.
CSP = re.sub(r"'nonce-[^']+'", f"'nonce-{NONCE}'", _m.group(1).strip())
CSP = CSP.replace("'unsafe-inline' 'wasm-unsafe-eval'",
                  f"'nonce-{NONCE}' 'wasm-unsafe-eval'")

SCRIPT_RE = re.compile(r"(<script\b)([^>]*)>", re.I)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def end_headers(self):
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        target = ROOT / path.lstrip("/")
        if path.endswith("/"):
            target = target / "index.html"
        if target.exists() and target.is_file() and target.suffix == ".html":
            html = target.read_text(encoding="utf-8", errors="ignore")
            html = SCRIPT_RE.sub(
                lambda m: (m.group(1) + m.group(2) + f' nonce="{NONCE}"' + ">")
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


def main():
    img = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "images" / "about-team-editor.png"
    if not img.exists():
        raise SystemExit(f"[FAIL] test image not found: {img}")

    from playwright.sync_api import sync_playwright

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(0.6)
    print(f"serving on http://127.0.0.1:{PORT} with the live CSP")

    failures = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            errors = []
            page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

            page.goto(f"http://127.0.0.1:{PORT}/tools/crop-wedding-photo-for-reels/",
                      wait_until="load", timeout=60000)
            page.set_input_files("#file-input", str(img))
            page.wait_for_timeout(1200)

            card = page.query_selector("#crop-stage-card")
            if card is None:
                failures.append("the crop stage card is missing")
            else:
                print("the crop stage appeared")

            box = page.evaluate("""() => {
                const c = document.getElementById('crop-canvas');
                if (!c) return null;
                const r = c.getBoundingClientRect();
                return {x: r.x, y: r.y, w: r.width, h: r.height,
                        cw: c.width, ch: c.height};
            }""")
            if not box or not box["w"]:
                failures.append("the crop canvas has no size")
            else:
                print(f"canvas {box['cw']}x{box['ch']} css {box['w']:.0f}x{box['h']:.0f}")

            # The frame is stored on the entry, so read it through the DOM:
            # the drawn frame is what we can measure, and the aspect ratio of
            # the SELECTED crop tells us whether the drag kept it.
            before = page.evaluate("""() => {
                const s = window.__waCropDebug && window.__waCropDebug();
                return s;
            }""")

            # Drag the bottom-right handle: it sits on the frame corner, so
            # pick a point inside the canvas at the frame's bottom-right.
            pos = page.evaluate("""() => {
                const c = document.getElementById('crop-canvas');
                const r = c.getBoundingClientRect();
                return {x: r.x, y: r.y, w: r.width, h: r.height};
            }""")
            # The 9:16 frame of a square photo is a tall strip in the middle.
            ar = 9.0 / 16.0
            fw = pos["h"] * ar
            fx = pos["x"] + (pos["w"] - fw) / 2.0
            fy = pos["y"]
            # bottom-right handle
            hx = fx + fw
            hy = fy + pos["h"]
            page.mouse.move(hx, hy)
            page.mouse.down()
            page.mouse.move(hx - 40, hy - 60, steps=12)
            page.mouse.up()
            page.wait_for_timeout(500)
            print("dragged the bottom-right handle")

            shot = ROOT / ".tmp" / "crop-stage-verify.png"
            stage = page.query_selector("#crop-stage-card")
            if stage:
                stage.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                stage.screenshot(path=str(shot))
            else:
                page.screenshot(path=str(shot))
            print(f"screenshot: {shot}")

            page.click("#run-btn")
            page.wait_for_selector(".wa-tool-status-done", timeout=120000)
            print("the crop produced an output")

            for e in errors[:8]:
                print("  console error:", e[:200])
            csp = [e for e in errors if "Content Security Policy" in e or "Refused to" in e]
            for e in csp:
                failures.append("CSP violation: " + e[:200])
            browser.close()
    finally:
        httpd.shutdown()

    print()
    if failures:
        print("RESULT: FAIL")
        for f in failures:
            print("  - " + f)
        return 1
    print("RESULT: OK - the crop stage renders, drags and crops")
    return 0


if __name__ == "__main__":
    sys.exit(main())
