#!/usr/bin/env python3
"""
Verify the MP4 export and the 1080x1920 PNG export of the video invitation
maker.

WHY THIS EXISTS
---------------
Two claims are being tested, and neither can be checked by reading the
code:

  1. "Download 5 PNG frames (1080x1920)". The layout is a 540x960 DESIGN
     space; the export sets BASE_W/BASE_H to 1080/1920 and re-renders.
     Because the coordinates are absolute pixels, that drew the 540x960
     layout into the TOP-LEFT QUARTER of a 1080x1920 canvas - the frames
     were the right pixel count and the wrong picture. The test compares
     the exported PNG against the on-screen preview: they must be the
     same image.

  2. "Download a 5-second MP4". The encoder (mediabunny) is 706 KB and is
     fetched on demand; the test has to prove that the file really is an
     MP4 of about five seconds, which is done by reading the produced
     file back with mediabunny itself (it runs in Node too).

Usage:  python scripts/verify-mp4-export.py
Exit code 0 = verified, 1 = failed.
"""
import base64
import http.server
import json
import re
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8796

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


PROBE_JS = r"""
import { Input, ALL_FORMATS, BlobSource } from '%MEDIABUNNY%';
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const file = process.argv[2];
const buf = readFileSync(file);
const blob = new Blob([buf]);
const input = new Input({ source: new BlobSource(blob), formats: ALL_FORMATS });
const duration = await input.computeDuration();
const track = await input.getPrimaryVideoTrack();
const out = {
  duration: duration,
  width: await track.getDisplayWidth(),
  height: await track.getDisplayHeight(),
  codec: track.codec,
  bytes: buf.length
};
console.log(JSON.stringify(out));
"""


def main():
    from playwright.sync_api import sync_playwright

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    httpd.allow_reuse_address = True
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.6)
    print("serving %s on http://127.0.0.1:%d with the live CSP" % (ROOT, PORT))

    failures = []
    tmpdir = Path(tempfile.mkdtemp(prefix="wa-mp4-"))

    try:
        with sync_playwright() as p:
            # The bundled Playwright Chromium is built WITHOUT the
            # proprietary codecs, so it has no H.264 ENCODER at all
            # (measured 2026-11-11: every avc level is unsupported there).
            # Real Chrome and Edge do have it - but only from H.264 level
            # 4.0 up, because 1080x1920 does not fit into level 3.1.
            # The test therefore runs in the INSTALLED Chrome.
            try:
                browser = p.chromium.launch(channel="chrome")
                print("  using the installed Chrome")
            except Exception as exc:  # noqa: BLE001
                print("  [FAIL] the installed Chrome could not be launched: %s"
                      % str(exc).splitlines()[0][:160])
                return 1
            page = browser.new_page(accept_downloads=True)
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))

            url = "http://127.0.0.1:%d/tools/wedding-video-invitation-maker/" % PORT
            page.goto(url, wait_until="load", timeout=60000)
            print("loaded %s" % url)

            # --- 1. the MP4 button must be offered where an encoder exists ---
            #
            # The button is revealed by an ASYNC native probe
            # (VideoEncoder.isConfigSupported), so wait for it instead of
            # asking immediately.
            if page.query_selector("#download-mp4-btn") is None:
                failures.append("the MP4 button is missing")
            else:
                try:
                    page.wait_for_selector("#download-mp4-btn", state="visible",
                                           timeout=15000)
                    print("  the MP4 button is offered")
                except Exception:
                    failures.append("the MP4 button stays hidden in a browser "
                                    "that can encode H.264")

            # --- 2. the preview, for the layout comparison ------------------
            preview_png = tmpdir / "preview.png"
            data_url = page.evaluate(
                "() => document.querySelector('#preview-canvas').toDataURL('image/png')")
            preview_png.write_bytes(base64.b64decode(data_url.split(",", 1)[1]))
            print("  preview captured (%d bytes)" % preview_png.stat().st_size)

            # --- 3. the MP4 export ------------------------------------------
            #
            # The MP4 FIRST: the PNG export fires five downloads in a row,
            # and a later expect_download() would catch one of those
            # instead of the MP4.
            with page.expect_download(timeout=300000) as mp4_info:
                page.click("#download-mp4-btn")
            mp4 = tmpdir / "invite.mp4"
            mp4_info.value.save_as(str(mp4))
            print("  MP4: %d bytes" % mp4.stat().st_size)
            if mp4.stat().st_size < 20000:
                failures.append("the MP4 is only %d bytes - it is probably empty"
                                % mp4.stat().st_size)
            head = mp4.read_bytes()[:64]
            print("  first bytes: %s" % head[:32].hex())
            if b"ftyp" not in head and b"moov" not in head:
                failures.append("the downloaded file is not an MP4 (no ftyp/moov box)")

            # --- 4. the PNG export ------------------------------------------
            with page.expect_download(timeout=120000) as dl_info:
                page.click("#download-btn")
            first = tmpdir / "frame1.png"
            dl_info.value.save_as(str(first))
            time.sleep(2.0)
            print("  first exported frame: %d bytes" % first.stat().st_size)
            if first.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                failures.append("the exported frame is not a PNG")

            browser.close()

        # --- 5. read the MP4 back with mediabunny (it runs in Node) -------
        probe = tmpdir / "probe.mjs"
        mb = (ROOT / "js" / "vendor" / "mediabunny" / "mediabunny.min.mjs")
        # On Windows an absolute path is not a valid ESM specifier - it has
        # to be a file:// URL.
        probe.write_text(
            PROBE_JS.replace("%MEDIABUNNY%", mb.resolve().as_uri()),
            encoding="utf-8")
        res = subprocess.run(["node", str(probe), str(mp4)],
                             capture_output=True, text=True, timeout=180)
        if res.returncode != 0:
            failures.append("mediabunny could not read the MP4 back: %s"
                            % (res.stderr.strip()[:300] or res.stdout.strip()[:300]))
        else:
            info = json.loads(res.stdout.strip().splitlines()[-1])
            print("  mediabunny read it back: %.2f s, %sx%s, %s, %d bytes"
                  % (info["duration"], info["width"], info["height"],
                     info["codec"], info["bytes"]))
            if not (4.0 <= info["duration"] <= 6.0):
                failures.append("the MP4 is %.2f s long, expected about 5 s"
                                % info["duration"])
            if info["width"] != 1080 or info["height"] != 1920:
                failures.append("the MP4 is %sx%s, expected 1080x1920"
                                % (info["width"], info["height"]))

        # --- 6. the exported PNG must be the SAME picture as the preview ---
        try:
            from PIL import Image
            import numpy as np
            prev = Image.open(preview_png).convert("RGB")
            exported = Image.open(first).convert("RGB")
            if exported.size != (1080, 1920):
                failures.append("the exported frame is %sx%s, expected 1080x1920"
                                % exported.size)
            else:
                small = exported.resize(prev.size, Image.LANCZOS)
                a = np.asarray(prev, dtype=np.int16)
                b = np.asarray(small, dtype=np.int16)
                diff = float(np.abs(a - b).mean())
                print("  mean |preview - export| = %.2f / 255" % diff)
                if diff > 12.0:
                    failures.append(
                        "the exported frame does not match the preview "
                        "(mean difference %.2f/255) - the 1080x1920 render is "
                        "still drawing the 540x960 layout in the wrong place"
                        % diff)
        except ImportError:
            print("  (PIL/numpy missing - skipping the layout comparison)")

        csp_errors = [e for e in errors if "Content Security Policy" in e or "Refused to" in e]
        for e in csp_errors:
            failures.append("CSP violation: " + e[:220])
        other = [e for e in errors if e not in csp_errors]
        for e in other[:8]:
            print("  console error:", e[:220])
    finally:
        httpd.shutdown()

    print()
    if failures:
        print("RESULT: FAIL")
        for f in failures:
            print("  - " + f)
        return 1
    print("RESULT: OK - the MP4 is a real 5-second 1080x1920 file and the PNG "
          "export matches the preview")
    return 0


if __name__ == "__main__":
    sys.exit(main())
