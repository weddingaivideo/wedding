#!/usr/bin/env python3
"""
Verify the compress tool's target-size mode (§2.14) and EXIF retention
(§2.13).

WHY THIS EXISTS
---------------
§2.14 and §2.13 both make a promise the page states in 11 languages:

  * "every photo is tuned to land just under this size" - a promise about
    a NUMBER, so it has to be measured on the produced file;
  * "EXIF is copied over from the original file ... the orientation is
    deliberately reset, so the photo can never end up sideways" - a
    promise about the BYTES of the output, and about its orientation.

The orientation half is the one that can go wrong silently: the source
carries Orientation=6, the pixels in the output are already upright, and
copying the EXIF verbatim would make every viewer rotate them a second
time. The test image is therefore a 200x100 JPEG tagged Orientation=6:
after the round trip the output must be 100x200 (upright) AND its EXIF
Orientation tag must read 1.

Usage:  python scripts/verify-compress-target-exif.py
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
PORT = 8798

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


def make_test_jpeg(path: Path) -> None:
    """A 200x100 JPEG tagged Orientation=6, with Make/Model/DateTime.

    Orientation=6 means "rotate 90 degrees clockwise when displaying", so
    a viewer shows it as 100x200. The pixels in the file are landscape.
    """
    from PIL import Image
    img = Image.new("RGB", (200, 100), (30, 60, 120))
    for x in range(200):
        for y in range(0, 100, 20):
            for xx in range(x, min(200, x + 4)):
                img.putpixel((xx, y), (250, 240, 210))
    exif = img.getexif()
    exif[0x0112] = 6          # Orientation
    exif[0x010F] = "WeddingAI"  # Make
    exif[0x0110] = "TestCam"    # Model
    exif[0x0132] = "2026:06:14 12:00:00"  # DateTime
    img.save(path, "JPEG", quality=92, exif=exif.tobytes())


def make_noise_jpeg(path: Path) -> None:
    """A big, noisy photo - noise does not compress, so a small target
    really does force the quality search AND the downscale."""
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(7)
    w, h = 1600, 1200
    arr = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
    Image.fromarray(arr).save(path, "JPEG", quality=95)


def read_exif_orientation(path: Path):
    """Return (has_app1, orientation) for a JPEG file."""
    data = path.read_bytes()
    if data[:2] != b"\xff\xd8":
        return (False, None)
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        if marker in (0xDA, 0xD9):
            return (False, None)
        length = (data[i + 2] << 8) | data[i + 3]
        if length < 2:
            return (False, None)
        if marker == 0xE1:
            if data[i + 4:i + 10] != b"Exif\x00\x00":
                return (False, None)
            seg = data[i:i + 2 + length]
            tiff = 10
            le = seg[tiff] == 0x49
            def u16(off):
                return (seg[off] | (seg[off + 1] << 8)) if le else ((seg[off] << 8) | seg[off + 1])
            def u32(off):
                # NOTE: `return (x) >>> 0` is a SyntaxError in Python -
                # the parenthesised form is parsed as a tuple. Assign first.
                if le:
                    v = seg[off] | (seg[off + 1] << 8) | (seg[off + 2] << 16) | (seg[off + 3] << 24)
                else:
                    v = (seg[off] << 24) | (seg[off + 1] << 16) | (seg[off + 2] << 8) | seg[off + 3]
                return v & 0xFFFFFFFF
            if u16(tiff + 2) != 42:
                return (True, None)
            ifd0 = tiff + u32(tiff + 4)
            count = u16(ifd0)
            for k in range(count):
                e = ifd0 + 2 + k * 12
                if u16(e) == 0x0112:
                    val = seg[e + 8] if le else seg[e + 9]
                    return (True, val)
            return (True, None)
        i += 2 + length
    return (False, None)


def jpeg_size(path: Path):
    """(width, height) of a JPEG, straight from the SOF marker."""
    data = path.read_bytes()
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        if marker in (0xDA, 0xD9):
            return (None, None)
        length = (data[i + 2] << 8) | data[i + 3]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h = (data[i + 5] << 8) | data[i + 6]
            w = (data[i + 7] << 8) | data[i + 8]
            return (w, h)
        i += 2 + length
    return (None, None)


def main():
    from playwright.sync_api import sync_playwright

    tmpdir = Path(tempfile.mkdtemp(prefix="wa-compress-"))
    small = tmpdir / "small.jpg"
    big = tmpdir / "big.jpg"
    make_test_jpeg(small)
    make_noise_jpeg(big)
    print("small test image: %d bytes, %s" % (small.stat().st_size, jpeg_size(small)))
    print("big test image:   %d bytes, %s" % (big.stat().st_size, jpeg_size(big)))

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    httpd.allow_reuse_address = True
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.6)
    print("serving %s on http://127.0.0.1:%d with the live CSP" % (ROOT, PORT))

    failures = []
    TARGET_MB = 0.05          # 50 KB
    TARGET_BYTES = int(TARGET_MB * 1024 * 1024)

    def run_and_download(page, image, out_path, target_mb):
        """Upload one photo, compress it, download the row's result."""
        page.goto("http://127.0.0.1:%d/tools/compress-wedding-photos/" % PORT,
                  wait_until="load", timeout=60000)
        page.fill("#target-size", str(target_mb))
        page.set_input_files("#file-input", str(image))
        page.wait_for_timeout(700)
        page.click("#run-btn")
        # Wait for EITHER state. Waiting only for "done" hides a failure
        # behind a full timeout - a row that went to "error" looks exactly
        # like a row that is still working.
        page.wait_for_selector(".wa-tool-status-done, .wa-tool-status-error",
                               timeout=120000)
        state = page.evaluate("""() => {
            var row = document.querySelector('#file-list .wa-tool-file-row');
            var err = document.querySelector('.wa-tool-err');
            return { cls: row ? row.className : '(no row)',
                     err: err ? err.textContent : null };
        }""")
        if "wa-tool-status-done" not in state["cls"]:
            raise AssertionError("the row ended in %s: %s"
                                 % (state["cls"], state["err"]))
        # The tool does NOT download on its own - the finished row gets its
        # own Download button.
        with page.expect_download(timeout=120000) as dl_info:
            page.click(".wa-tool-status-done .wa-tool-actions button")
        dl_info.value.save_as(str(out_path))
        return out_path.stat().st_size

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(accept_downloads=True)
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))

            url = "http://127.0.0.1:%d/tools/compress-wedding-photos/" % PORT
            page.goto(url, wait_until="load", timeout=60000)
            print("loaded %s" % url)

            if page.query_selector("#target-size") is None:
                failures.append("the target-size control is missing")
            if page.query_selector("#keep-exif") is None:
                failures.append("the keep-exif control is missing")

            # --- scenario A: EXIF kept, orientation reset -----------------
            print("\nA. EXIF + orientation (small photo, no target)")
            out_a = tmpdir / "exif.jpg"
            size_a = run_and_download(page, small, out_a, 0)
            print("  output: %d bytes, frame %s" % (size_a, jpeg_size(out_a)))

            has_app1, orientation = read_exif_orientation(out_a)
            print("  output EXIF: app1=%s orientation=%s" % (has_app1, orientation))
            if not has_app1:
                failures.append("the output carries no EXIF - the APP1 segment "
                                "was not copied")
            if orientation != 1:
                failures.append("the output EXIF Orientation is %s, expected 1 - "
                                "a viewer would rotate the photo a second time"
                                % orientation)
            w, h = jpeg_size(out_a)
            if (w, h) != (100, 200):
                failures.append("the output frame is %sx%s, expected 100x200 - "
                                "the photo was not re-oriented" % (w, h))
            try:
                from PIL import Image
                with Image.open(out_a) as im:
                    im.load()
                    print("  the output decodes: %sx%s" % im.size)
            except Exception as exc:
                failures.append("the output is not a decodable JPEG: %s" % exc)

            # --- scenario B: the size promise ------------------------------
            print("\nB. target size (noisy photo, target %.2f MB)" % TARGET_MB)
            out_b = tmpdir / "target.jpg"
            size_b = run_and_download(page, big, out_b, TARGET_MB)
            print("  output: %d bytes (target %d)" % (size_b, TARGET_BYTES))
            if size_b == 0:
                failures.append("the target-mode output file is empty")
            if size_b > TARGET_BYTES:
                failures.append("the output is %d bytes, above the %d byte target"
                                % (size_b, TARGET_BYTES))
            try:
                from PIL import Image
                with Image.open(out_b) as im:
                    im.load()
                    print("  the output decodes: %sx%s" % im.size)
            except Exception as exc:
                failures.append("the target-mode output is not a decodable JPEG: %s"
                                % exc)

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
    print("RESULT: OK - the target size is met, the EXIF is kept and the "
          "orientation is reset")
    return 0


if __name__ == "__main__":
    sys.exit(main())
