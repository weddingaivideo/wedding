#!/usr/bin/env python3
"""
End-to-end verification of the on-device AI background removal.

WHY THIS EXISTS
---------------
The MODNet path is the one thing in this whole batch that CANNOT be checked
by reading the code: it needs a browser, a WebAssembly runtime, a 10.9 MB
.wasm file and a 6.3 MB model to be fetched from the right place under the
site's Content-Security-Policy. If any of those is wrong, the page still
returns 200 and the tool still renders - it just quietly does nothing.

So this script:
  1. serves the repository over HTTP with the EXACT Content-Security-Policy
     from _headers (the policy the live site serves), and injects a nonce
     into every inline <script> the same way functions/_middleware.js does;
  2. drives the real remove-background page with Playwright: pick the AI
     method, upload a photo, press the button;
  3. asserts that the ONNX runtime and the model were fetched from
     /js/vendor/, that the file row reached the "done" state, and that the
     console carries no CSP violation.

Usage:  python scripts/verify-ai-background.py [image.png]
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
PORT = 8791

# --- the live policy, read from _headers so the test cannot drift from it ----
_headers = (ROOT / "_headers").read_text(encoding="utf-8")
_m = re.search(r"^\s*Content-Security-Policy:\s*(.+)$", _headers, re.M)
if not _m:
    raise SystemExit("[FAIL] no Content-Security-Policy in _headers")
CSP_TEMPLATE = _m.group(1).strip()
NONCE = "weddingaiverify123456"


def build_csp():
    # The live policy carries a per-request nonce. The test page is served
    # statically, so the same nonce is used for the policy and the markup.
    csp = CSP_TEMPLATE.replace("'unsafe-inline' 'wasm-unsafe-eval'",
                                f"'nonce-{NONCE}' 'wasm-unsafe-eval'")
    csp = re.sub(r"'nonce-[^']+'", f"'nonce-{NONCE}'", csp)
    if "wasm-unsafe-eval" not in csp:
        raise SystemExit("[FAIL] the policy has no 'wasm-unsafe-eval' - the ORT runtime "
                         "cannot compile WebAssembly under it")
    if "worker-src" not in csp:
        raise SystemExit("[FAIL] the policy has no worker-src directive")
    return csp


CSP = build_csp()

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
        if path.endswith(".html") or path.endswith("/"):
            target = ROOT / path.lstrip("/")
            if target.is_dir():
                target = target / "index.html"
            if target.exists() and target.is_file():
                html = target.read_text(encoding="utf-8", errors="ignore")
                # same trick as functions/_middleware.js injectScriptNonce()
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


def main():
    img = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "images" / "about-team-editor.png"
    if not img.exists():
        raise SystemExit(f"[FAIL] test image not found: {img}")

    from playwright.sync_api import sync_playwright

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    httpd.allow_reuse_address = True
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.6)
    print(f"serving {ROOT} on http://127.0.0.1:{PORT} with the live CSP")

    failures = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            console_errors = []
            requests = []
            page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: console_errors.append("pageerror: " + str(e)))
            page.on("request", lambda r: requests.append(r.url))

            url = f"http://127.0.0.1:{PORT}/tools/remove-background-wedding-portrait/"
            page.goto(url, wait_until="load", timeout=60000)
            print(f"loaded {url}")

            # The method picker must exist.
            if page.query_selector("#method") is None:
                failures.append("the #method picker is missing from the page")
            else:
                page.select_option("#method", "ai")

            page.set_input_files("#file-input", str(img))
            page.wait_for_timeout(600)
            page.click("#run-btn")
            print("clicked the run button; waiting for the model + inference...")

            page.wait_for_selector(".wa-tool-status-done", timeout=300000)
            print("the row reached the done state")

            vendor_hits = [u for u in requests if "/js/vendor/" in u]
            for want in ("onnxruntime/ort.wasm.min.js",
                         "onnxruntime/ort-wasm-simd-threaded.mjs",
                         "onnxruntime/ort-wasm-simd-threaded.wasm",
                         "modnet/model_quantized.onnx"):
                if not any(want in u for u in vendor_hits):
                    failures.append(f"never fetched {want}")
                else:
                    print(f"  fetched {want}")

            csp_errors = [e for e in console_errors
                          if "Content Security Policy" in e or "Refused to" in e]
            for e in csp_errors:
                failures.append("CSP violation: " + e[:220])
            other = [e for e in console_errors if e not in csp_errors]
            for e in other[:8]:
                print("  console error:", e[:220])

            shot = ROOT / ".tmp" / "ai-bg-verify.png"
            page.screenshot(path=str(shot), full_page=False)
            print(f"screenshot: {shot}")
            browser.close()
    finally:
        httpd.shutdown()

    print()
    if failures:
        print("RESULT: FAIL")
        for f in failures:
            print("  - " + f)
        return 1
    print("RESULT: OK - the AI path runs under the production CSP")
    return 0


if __name__ == "__main__":
    sys.exit(main())
