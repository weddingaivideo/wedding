#!/usr/bin/env python3
"""
Smoke test every tool that decodes a file through fileToImage().

WHY THIS EXISTS
---------------
On 2026-11-09 fileToImage() stopped returning an <img> backed by an object
URL and started returning an ImageBitmap (§2.6 / §2.7). That is a CONTRACT
CHANGE for every tool that uses it:

    loaded.img      an ImageBitmap, not an HTMLImageElement
    loaded.url      null
    loaded.release  the teardown call (close the bitmap / revoke the URL)

An ImageBitmap has no `.complete`, and `URL.revokeObjectURL(null)` is a
silent no-op - so a tool that was not updated still "works" (the row turns
green) while leaking the decoded image. The bug is invisible in a
screenshot and invisible in a 200 response. Only driving the tool and
looking at the console tells the truth.

This script drives every affected tool in a real browser under the live
Content-Security-Policy, uploads a photo, runs the tool and requires:

  - the row to reach the "done" state (not "error"),
  - no page error and no console error,
  - for the tools that render straight into a canvas, a canvas that
    actually has pixels in it (a broken naturalWidth would draw nothing).

Usage:  python scripts/verify-tool-suite-smoke.py [image.png]
Exit code 0 = all green, 1 = at least one tool is broken.
"""
import http.server
import re
import socketserver
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8795

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


# slug -> (input id, run button id or None, needs a canvas check, file count,
#         the selector that means "this tool finished")
#
# The collage needs at least TWO photos before its build button unlocks
# (runBtn.disabled = files.length < 2) - that is the tool's own rule, not
# a regression. It also builds ONE canvas out of all the photos, so its
# per-file rows never reach "done"; the summary panel appearing is its
# "finished" signal.
TOOLS = [
    ("wedding-photo-collage", "file-input", "run-btn", False, 2, "#summary"),
    ("crop-wedding-photo-for-reels", "file-input", "run-btn", False, 1, ".wa-tool-status-done"),
    ("compress-wedding-photos", "file-input", "run-btn", False, 1, ".wa-tool-status-done"),
    ("add-text-to-wedding-photo", "file-input", "run-btn", False, 1, ".wa-tool-status-done"),
    ("save-the-date-maker", "photo-input", None, True, 1, None),
    ("wedding-invitation-maker", "photo-input", None, True, 1, None),
    ("wedding-video-invitation-maker", "photo-input", None, True, 1, None),
]

CANVAS_PAINTED_JS = r"""
() => {
  const c = document.querySelector('#preview-canvas');
  if (!c) return { found: false };
  const ctx = c.getContext('2d');
  if (!ctx) return { found: true, painted: false, w: c.width, h: c.height };
  const data = ctx.getImageData(0, 0, c.width, c.height).data;
  let painted = 0;
  for (let i = 3; i < data.length; i += 4) {
    if (data[i] > 0) painted++;
  }
  return { found: true, painted: painted, w: c.width, h: c.height };
}
"""


def main():
    img = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "images" / "about-team-editor.png"
    if not img.exists():
        raise SystemExit("[FAIL] test image not found: %s" % img)

    from playwright.sync_api import sync_playwright

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    httpd.allow_reuse_address = True
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.6)
    print("serving %s on http://127.0.0.1:%d with the live CSP" % (ROOT, PORT))

    failures = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for slug, input_id, run_id, needs_canvas, count, done_sel in TOOLS:
                page = browser.new_page()
                errors = []
                page.on("console", lambda m, b=errors: b.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda e, b=errors: b.append("pageerror: " + str(e)))

                url = "http://127.0.0.1:%d/tools/%s/" % (PORT, slug)
                try:
                    page.goto(url, wait_until="load", timeout=60000)
                    page.set_input_files("#" + input_id, [str(img)] * count)
                    page.wait_for_timeout(900)

                    if run_id:
                        page.click("#" + run_id)
                        if done_sel:
                            page.wait_for_selector(done_sel, state="visible", timeout=90000)
                        detail = ""
                        if slug == "wedding-photo-collage":
                            # The summary is shown BEFORE the finally block
                            # re-enables the download button, so wait for the
                            # button itself - that is the real "finished" state.
                            try:
                                # NOTE: a CSS selector, not a JS string -
                                # page.wait_for_function("...") evaluates the
                                # string with eval, and the live CSP has no
                                # 'unsafe-eval', so the browser refuses it.
                                page.wait_for_selector("#download-btn:not([disabled])",
                                                       timeout=30000)
                                detail = "summary shown, download enabled"
                            except Exception:
                                failures.append("%s: the collage built but the download "
                                                "button stayed disabled" % slug)
                    else:
                        page.wait_for_timeout(1500)
                        detail = ""

                    if needs_canvas:
                        info = page.evaluate(CANVAS_PAINTED_JS)
                        if not info.get("found"):
                            failures.append("%s: #preview-canvas is missing" % slug)
                        elif not info.get("painted"):
                            failures.append("%s: the preview canvas is empty (%sx%s) - the "
                                            "decoded image never reached the canvas"
                                            % (slug, info.get("w"), info.get("h")))
                        else:
                            detail = "canvas %sx%s, %d painted pixels" % (
                                info.get("w"), info.get("h"), info.get("painted"))

                    if errors:
                        failures.append("%s: console/page errors -> %s"
                                        % (slug, " | ".join(e[:160] for e in errors[:3])))
                    else:
                        print("  OK  %-32s %s" % (slug, detail))
                except Exception as e:
                    failures.append("%s: %s" % (slug, str(e)[:300]))
                finally:
                    page.close()
            browser.close()
    finally:
        httpd.shutdown()

    print()
    if failures:
        print("RESULT: FAIL")
        for f in failures:
            print("  - " + f)
        return 1
    print("RESULT: OK - every tool that decodes a file still works")
    return 0


if __name__ == "__main__":
    sys.exit(main())
