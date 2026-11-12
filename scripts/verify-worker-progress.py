#!/usr/bin/env python3
"""
End-to-end verification of the §2.5 - §2.9 engineering pass.

WHY THIS EXISTS
---------------
Three of the four changes cannot be checked by reading the code:

  2.5  the pixel loop moved into a Worker. If the Worker cannot start
       (wrong URL, CSP, syntax) the tool silently falls back to the
       main-thread loop and NOTHING LOOKS BROKEN - the page returns 200,
       the result is correct, and the tab still freezes. Only the network
       log tells the two apart.
  2.8  the release path. If releaseImage() closes a bitmap that is still
       in use, the NEXT drawImage() throws and the tool produces an
       empty file. If it forgets to close one, nothing fails - the memory
       just leaks.
  2.9  the progress bar. If no tool ever sets entry.percent, the bar
       never renders and the "real progress" claim is a lie in a
       stylesheet.

So this script:
  1. serves the repository over HTTP with the EXACT Content-Security-
     Policy from _headers (the policy the live site serves) and injects
     a nonce into every inline <script> the way functions/_middleware.js
     does;
  2. asks common.js to run the pixel loop in the Worker with a synthetic
     buffer and compares the result, byte for byte, against the same
     maths computed on the main thread - the Worker must not change the
     output;
  3. drives the real remove-background page, uploads a photo, presses the
     button, and checks that the Worker was actually fetched, that the
     progress bar appeared with a percentage, and that the row finished;
  4. checks the ImageBitmap contract of fileToImage() and that the
     decoded image is released afterwards.

Usage:  python scripts/verify-worker-progress.py [image.png]
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

# --- the live policy, read from _headers so the test cannot drift from it ----
_headers = (ROOT / "_headers").read_text(encoding="utf-8")
_m = re.search(r"^\s*Content-Security-Policy:\s*(.+)$", _headers, re.M)
if not _m:
    raise SystemExit("[FAIL] no Content-Security-Policy in _headers")
CSP_TEMPLATE = _m.group(1).strip()
NONCE = "weddingaiverify123456"


def build_csp():
    csp = CSP_TEMPLATE.replace("'wasm-unsafe-eval'",
                                f"'nonce-{NONCE}' 'wasm-unsafe-eval'")
    csp = re.sub(r"'nonce-[^']+'", f"'nonce-{NONCE}'", csp)
    if "wasm-unsafe-eval" not in csp:
        raise SystemExit("[FAIL] the policy has no 'wasm-unsafe-eval'")
    if "worker-src" not in csp:
        raise SystemExit("[FAIL] the policy has no worker-src directive")
    return csp


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


# --- the in-page test of the Worker ------------------------------------------
#
# The reference maths is copied from the tool page's applyPixelLoop(). It is
# duplicated on purpose: if the two ever disagree, the Worker changed the
# output and the tool would no longer match what the page claims.
PIXEL_TEST_JS = r"""
async (opts) => {
  const T = window.weddingAITool;
  if (!T) return { error: 'weddingAITool is missing' };
  if (typeof T.runPixelLoop !== 'function') {
    return { error: 'runPixelLoop is not exported' };
  }

  function reference(src, bgR, bgG, bgB, innerT, outerT, bandWidth, mode) {
    const data = new Uint8ClampedArray(src);
    for (let i = 0; i < data.length; i += 4) {
      const dr = data[i] - bgR;
      const dg = data[i + 1] - bgG;
      const db = data[i + 2] - bgB;
      const dist = Math.sqrt(dr * dr + dg * dg + db * db);
      let alpha;
      if (dist <= innerT) alpha = 0;
      else if (dist < outerT) alpha = Math.round(((dist - innerT) / bandWidth) * 255);
      else alpha = 255;
      if (mode === 'png') {
        data[i + 3] = Math.round((data[i + 3] / 255) * alpha);
      } else {
        if (alpha < 255) {
          const k = 1 - (alpha / 255);
          data[i] = Math.round(data[i] * (1 - k) + 255 * k);
          data[i + 1] = Math.round(data[i + 1] * (1 - k) + 255 * k);
          data[i + 2] = Math.round(data[i + 2] * (1 - k) + 255 * k);
        }
        data[i + 3] = 255;
      }
    }
    return data;
  }

  const N = 64 * 64;
  const src = new Uint8ClampedArray(N * 4);
  for (let i = 0; i < src.length; i += 4) {
    src[i] = (i * 7) % 256;
    src[i + 1] = (i * 13) % 256;
    src[i + 2] = (i * 29) % 256;
    src[i + 3] = 255;
  }
  const bgR = 10, bgG = 20, bgB = 30, innerT = 30, outerT = 110, bandWidth = 80;

  const out = {};
  for (const mode of ['png', 'jpg']) {
    const ref = reference(src, bgR, bgG, bgB, innerT, outerT, bandWidth, mode);
    const copy = new Uint8ClampedArray(src);
    const progress = [];
    const buf = await T.runPixelLoop({
      buffer: copy.buffer,
      bgR: bgR, bgG: bgG, bgB: bgB,
      innerT: innerT, outerT: outerT, bandWidth: bandWidth,
      mode: mode
    }, (p) => progress.push(p));
    const got = new Uint8ClampedArray(buf);
    let diff = 0;
    for (let i = 0; i < got.length; i++) {
      if (got[i] !== ref[i]) diff++;
    }
    out[mode] = {
      diff: diff,
      total: got.length,
      progressUpdates: progress.length,
      lastProgress: progress.length ? progress[progress.length - 1] : null
    };
  }
  return out;
}
"""

# --- the fileToImage() contract ----------------------------------------------
FILE_TEST_JS = r"""
async () => {
  const T = window.weddingAITool;
  const canvas = document.createElement('canvas');
  canvas.width = 40; canvas.height = 20;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#3366cc';
  ctx.fillRect(0, 0, 40, 20);
  const blob = await new Promise((res) => canvas.toBlob(res, 'image/png'));
  const file = new File([blob], 'probe.png', { type: 'image/png' });

  const loaded = await T.fileToImage(file);
  const isBitmap = (typeof ImageBitmap !== 'undefined') && (loaded.img instanceof ImageBitmap);
  const info = {
    isBitmap: isBitmap,
    hasRelease: typeof loaded.release === 'function',
    url: loaded.url,
    naturalWidth: loaded.img.naturalWidth,
    naturalHeight: loaded.img.naturalHeight,
    width: loaded.img.width,
    height: loaded.img.height
  };
  // After the release the bitmap must be closed - a closed ImageBitmap
  // has width 0.
  loaded.release();
  info.widthAfterRelease = loaded.img.width;
  return info;
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
            page = browser.new_page()
            console_errors = []
            requests = []
            page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: console_errors.append("pageerror: " + str(e)))
            page.on("request", lambda r: requests.append(r.url))

            url = "http://127.0.0.1:%d/tools/remove-background-wedding-portrait/" % PORT
            page.goto(url, wait_until="load", timeout=60000)
            print("loaded %s" % url)

            # --- 1. the Worker produces the same bytes as the main thread ---
            res = page.evaluate(PIXEL_TEST_JS, None)
            if "error" in res:
                failures.append("pixel loop test: " + res["error"])
            else:
                for mode in ("png", "jpg"):
                    r = res[mode]
                    if r["diff"] != 0:
                        failures.append(
                            "the Worker output differs from the main-thread maths in %s mode "
                            "(%d of %d bytes)" % (mode, r["diff"], r["total"]))
                    else:
                        print("  %s mode: worker output identical to the main thread (%d bytes)"
                              % (mode, r["total"]))
                    if r["progressUpdates"] < 1:
                        failures.append("the Worker never reported progress in %s mode" % mode)
                    else:
                        print("  %s mode: %d progress update(s), last %.0f%%"
                              % (mode, r["progressUpdates"], r["lastProgress"]))

            # --- 2. the fileToImage() contract ------------------------------
            finfo = page.evaluate(FILE_TEST_JS)
            if not finfo.get("isBitmap"):
                failures.append("fileToImage() did not return an ImageBitmap")
            if not finfo.get("hasRelease"):
                failures.append("fileToImage() did not return a release() function")
            if finfo.get("naturalWidth") != finfo.get("width"):
                failures.append("naturalWidth is not mirrored on the ImageBitmap")
            if finfo.get("widthAfterRelease") not in (0, None):
                failures.append("release() did not close the ImageBitmap (width is still %s)"
                                % finfo.get("widthAfterRelease"))
            print("  fileToImage(): bitmap=%s release=%s natural=%sx%s closed_after_release=%s"
                  % (finfo.get("isBitmap"), finfo.get("hasRelease"),
                     finfo.get("naturalWidth"), finfo.get("naturalHeight"),
                     finfo.get("widthAfterRelease")))

            # --- 3. the real page run --------------------------------------
            # Watch for the progress bar for the whole run.
            page.evaluate("""() => {
                window.__sawProgress = 0;
                window.__maxPercent = 0;
                const obs = new MutationObserver(() => {
                  const bars = document.querySelectorAll('.wa-tool-progress');
                  if (bars.length) {
                    window.__sawProgress = bars.length;
                    for (const b of bars) {
                      const v = parseInt(b.getAttribute('aria-valuenow') || '0', 10);
                      if (v > window.__maxPercent) window.__maxPercent = v;
                    }
                  }
                });
                obs.observe(document.body, { childList: true, subtree: true, attributes: true });
            }""")

            page.set_input_files("#file-input", str(img))
            page.wait_for_timeout(500)
            page.click("#run-btn")
            print("clicked the run button; waiting for the worker...")

            page.wait_for_selector(".wa-tool-status-done", timeout=120000)
            print("the row reached the done state")

            saw = page.evaluate("() => ({ n: window.__sawProgress, max: window.__maxPercent })")
            if not saw["n"]:
                failures.append("the progress bar never appeared in the file row")
            else:
                print("  progress bar seen, max %s%%" % saw["max"])

            worker_hits = [u for u in requests if "pixel-worker.js" in u]
            if not worker_hits:
                failures.append("the pixel worker was never fetched - the loop ran on the "
                                "main thread, so the tab still freezes")
            else:
                print("  fetched %s" % worker_hits[0])

            csp_errors = [e for e in console_errors
                          if "Content Security Policy" in e or "Refused to" in e]
            for e in csp_errors:
                failures.append("CSP violation: " + e[:220])
            other = [e for e in console_errors if e not in csp_errors]
            for e in other[:8]:
                print("  console error:", e[:220])

            shot = ROOT / ".tmp" / "worker-progress-verify.png"
            page.screenshot(path=str(shot), full_page=False)
            print("screenshot: %s" % shot)
            browser.close()
    finally:
        httpd.shutdown()

    print()
    if failures:
        print("RESULT: FAIL")
        for f in failures:
            print("  - " + f)
        return 1
    print("RESULT: OK - the worker path, the release path and the progress bar all work")
    return 0


if __name__ == "__main__":
    sys.exit(main())
