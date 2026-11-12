#!/usr/bin/env python3
"""
Verify the face-aware crop (§2.11) end-to-end in a real browser.

WHY THIS EXISTS
---------------
A face detector is the kind of feature that fails SILENTLY. The library can
fail to load, the model can 404, the CSP can refuse the script, the detector
can return nothing, and the crop frame can quietly stay on the old off-center
bias - the page would still look perfect and the promise would be a lie.

So this script:
  1. serves the repository with the live Content-Security-Policy from
     _headers (nonce injected into the inline scripts, exactly like
     functions/_middleware.js does);
  2. opens the crop tool, uploads a photo with a clearly visible face, and
     checks that the face-aware switch is there;
  3. switches the detector ON and checks that the library AND the model
     weights were actually fetched, with a 200, from this origin;
  4. checks that the detector really found the face;
  5. checks that the crop frame now CONTAINS the face - the whole point of
     the feature - and that the face box is drawn on the preview;
  6. presses Crop and checks that a file row reaches the "done" state;
  7. checks that nothing was refused by the CSP.

Usage:  python scripts/verify-crop-face-aware.py [image.png]
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
PORT = 8794

_headers = (ROOT / "_headers").read_text(encoding="utf-8")
_m = re.search(r"^\s*Content-Security-Policy:\s*(.+)$", _headers, re.M)
if not _m:
    raise SystemExit("[FAIL] no Content-Security-Policy in _headers")
NONCE = "weddingaiverify123456"
CSP = re.sub(r"'nonce-[^']+'", f"'nonce-{NONCE}'", _m.group(1).strip())
CSP = CSP.replace("'wasm-unsafe-eval'",
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


def wait_for(page, expr, timeout_ms=90000, label=""):
    """Poll a JS expression with page.evaluate (wait_for_function would use
    eval, which the CSP refuses)."""
    deadline = time.time() + timeout_ms / 1000.0
    last = None
    while time.time() < deadline:
        last = page.evaluate(expr)
        if last:
            return last
        page.wait_for_timeout(250)
    return last


def main():
    img = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "images" / "testimonial-mr-720.png"
    if not img.exists():
        raise SystemExit("[FAIL] test image not found: %s" % img)

    from playwright.sync_api import sync_playwright

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(0.6)
    print("serving on http://127.0.0.1:%d with the live CSP" % PORT)

    failures = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            errors = []
            requests = []

            page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

            def on_response(resp):
                u = resp.url
                if "face-api" in u:
                    requests.append((resp.status, u.split("/js/vendor/")[-1]))

            page.on("response", on_response)

            page.goto("http://127.0.0.1:%d/tools/crop-wedding-photo-for-reels/" % PORT,
                      wait_until="load", timeout=60000)

            if page.query_selector("#face-aware") is None:
                failures.append("the face-aware switch is missing")
            else:
                print("the face-aware switch is there")

            page.set_input_files("#file-input", str(img))
            page.wait_for_timeout(1500)

            # With the switch OFF nothing may be downloaded: the detector is
            # opt-in, and the page must not cost 840 KB before the visitor
            # asks for it.
            before = len(requests)
            page.wait_for_timeout(600)
            if len(requests) != before:
                failures.append("the detector was fetched before the visitor asked for it")

            off = page.evaluate("() => window.__waCropDebug && window.__waCropDebug()")
            if not off:
                failures.append("the debug hook is missing")
            else:
                print("switch off: backend=%r status=%r" % (off.get("backend"), off.get("status")[:60]))
                if off.get("backend"):
                    failures.append("a backend was loaded even though the switch is off")

            # Switch it on.
            page.check("#face-aware")
            print("switched the face-aware framing on")

            got = wait_for(page,
                           "() => { const d = window.__waCropDebug && window.__waCropDebug(); "
                           "return d && d.faces ? d : null; }",
                           120000)
            if not got or not got.get("faces"):
                failures.append("the detector did not report any face")
                print("no face was reported: %r" % (got,))
            else:
                print("backend=%r faces=%d status=%r"
                      % (got.get("backend"), len(got["faces"]), (got.get("status") or "")[:70]))

            # The library and BOTH model files must have come from this origin.
            names = " ".join(n for _, n in requests)
            for needed in ("face-api.min.js", "tiny_face_detector_model-weights_manifest.json",
                           "tiny_face_detector_model-shard1"):
                if needed not in names:
                    failures.append("%s was never fetched" % needed)
            bad = [(s, n) for s, n in requests if s != 200]
            if bad:
                failures.append("a detector asset was not served with 200: %r" % bad)
            print("detector assets fetched: %r" % (requests,))

            # THE POINT: the crop frame must now contain the face.
            check = page.evaluate("""() => {
                const d = window.__waCropDebug && window.__waCropDebug();
                if (!d || !d.faces || !d.faces.length || !d.rect) return null;
                const s = d.scale;
                const out = [];
                for (const f of d.faces) {
                    out.push({x: f.x / s, y: f.y / s, w: f.w / s, h: f.h / s});
                }
                return {rect: d.rect, faces: out};
            }""")
            if not check:
                failures.append("could not read the frame and the faces")
            else:
                r = check["rect"]
                inside = []
                for f in check["faces"]:
                    inside.append(
                        f["x"] >= r["x"] - 0.5 and
                        f["y"] >= r["y"] - 0.5 and
                        f["x"] + f["w"] <= r["x"] + r["w"] + 0.5 and
                        f["y"] + f["h"] <= r["y"] + r["h"] + 0.5)
                print("frame %r" % r)
                print("faces in canvas px %r" % check["faces"])
                if not all(inside):
                    failures.append("the crop frame does NOT contain every face")
                else:
                    print("every face is inside the crop frame")

            # The face box must be visible on the preview (the green box).
            green = page.evaluate("""() => {
                const c = document.getElementById('crop-canvas');
                const ctx = c.getContext('2d');
                const d = ctx.getImageData(0, 0, c.width, c.height).data;
                let n = 0;
                for (let i = 0; i < d.length; i += 4) {
                    if (d[i + 1] > 180 && d[i] < 140 && d[i + 2] < 160) n++;
                }
                return n;
            }""")
            if not green or green < 50:
                failures.append("the face boxes are not drawn on the preview (%r green pixels)" % green)
            else:
                print("the preview draws %d green pixels of face box" % green)

            shot = ROOT / ".tmp" / "crop-face-verify.png"
            stage = page.query_selector("#crop-stage-card")
            if stage:
                stage.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                stage.screenshot(path=str(shot))
                print("screenshot: %s" % shot)

            page.click("#run-btn")
            page.wait_for_selector(".wa-tool-status-done", timeout=180000)
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
    print("RESULT: OK - the detector loads, finds the face and the frame follows it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
