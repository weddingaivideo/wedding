#!/usr/bin/env python3
"""
Smoke-test a tool page in a real browser: does it BOOT, and does its
download produce real bytes?

WHY THIS EXISTS
---------------
A tool page can look perfect, render, and still produce a broken file.
The stationery tool shipped a version whose export was a blank sheet
because the drawing function received the wrong object and every
coordinate came out NaN - and per the HTML spec, `fillText` with NaN
coordinates draws NOTHING. The page looked fine. Only the exported
bytes showed it.

So this script loads the page in Chromium, waits for it to settle,
feeds it a real image if it takes files, clicks its download button and
then reads the bytes that come out.

WHAT IT PROVES
--------------
* the page's inline JavaScript boots without an uncaught error,
* the download button exists and is wired,
* the file that comes out is a real file of the right type (PDF, PNG,
  GIF, MP4/WebM/MKV) and not an empty or error response.

WHAT IT DOES NOT PROVE
----------------------
That the output is BEAUTIFUL. It proves the pipeline works end to end.
The byte-level deep checks (the number of distinct colours in a PNG,
the page sizes in a PDF) stay in scripts/verify-tool-export.py for the
pages that have them.

Usage
-----
    python scripts/verify-tool-smoke.py --slug wedding-photo-contact-sheet
    python scripts/verify-tool-smoke.py --slug wedding-pdf-editor --no-files
"""
import argparse
import os
import re
import socket
import socketserver
import struct
import sys
import tempfile
import threading
import zlib
from http.server import SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------- serving

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def translate_path(self, path):
        path = path.split("?", 1)[0].split("#", 1)[0]
        return super().translate_path(path)


def serve(root):
    handler = type("H", (QuietHandler,), {"directory": root})
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port


# ---------------------------------------------------------------- a test PNG

def make_png(width=600, height=400, rgb=(198, 148, 106)):
    """A real PNG, so a decoder has something to decode."""
    raw = b""
    for y in range(height):
        raw += b"\x00"
        for x in range(width):
            raw += bytes(((rgb[0] + x) % 256, (rgb[1] + y) % 256, rgb[2]))
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 6))
    png += chunk(b"IEND", b"")
    return png


def make_webm(browser, tmpdir, seconds=1):
    """A real WebM, recorded by Chromium itself.

    THE VIDEO EDITOR NEEDS A REAL VIDEO
    ----------------------------------
    Its export button only enables when the page has decoded a clip
    (`state.duration > 0`), so feeding it a PNG leaves the button
    disabled and the smoke test reports "no download button found" -
    which reads like a broken page rather than a wrong test input.

    A hand-rolled container is not an option (a broken WebM fails the
    decoder, not the page), so Chromium records one: a canvas, a
    MediaRecorder and a second of moving frames.
    """
    page = browser.new_page()
    page.set_content("<html><body><canvas id='c' width='320' height='240'>"
                      "</canvas></body></html>")
    data = page.evaluate(
        """async (seconds) => {
            const canvas = document.getElementById('c');
            const ctx = canvas.getContext('2d');
            const stream = canvas.captureStream(30);
            const rec = new MediaRecorder(stream,
                {mimeType: 'video/webm;codecs=vp8'});
            const chunks = [];
            rec.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
            const stopped = new Promise((res) => { rec.onstop = res; });
            rec.start();
            const t0 = performance.now();
            await new Promise((resolve) => {
                function draw() {
                    const t = performance.now() - t0;
                    ctx.fillStyle = '#c9946a';
                    ctx.fillRect(0, 0, 320, 240);
                    ctx.fillStyle = '#ffffff';
                    ctx.fillRect((t / 12) % 300, 100, 20, 20);
                    if (t < seconds * 1000) {
                        requestAnimationFrame(draw);
                    } else {
                        resolve();
                    }
                }
                draw();
            });
            rec.stop();
            await stopped;
            const blob = new Blob(chunks, {type: 'video/webm'});
            const buf = new Uint8Array(await blob.arrayBuffer());
            return Array.from(buf);
        }""", seconds)
    page.close()
    path = os.path.join(tmpdir, "clip.webm")
    with open(path, "wb") as fh:
        fh.write(bytes(data))
    return path


def make_pdf():
    """A minimal but valid PDF with one page."""
    objs = []
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] "
                b"/Contents 4 0 R /Resources << >> >>")
    stream = b"1 0 0 RG 4 w 20 20 m 180 180 l S"
    objs.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n" % (len(objs) + 1)
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += (b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objs) + 1, xref))
    return bytes(out)


# ---------------------------------------------------------------- the bytes

def describe(path):
    """Return (kind, detail) for a downloaded file."""
    with open(path, "rb") as fh:
        head = fh.read(64)
        fh.seek(0, os.SEEK_END)
        size = fh.tell()
    if head[:5] == b"%PDF-":
        return "pdf", "%d bytes, %s" % (size, head[:8].decode("latin-1"))
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "png", "%d bytes" % size
    if head[:3] == b"\xff\xd8\xff":
        return "jpeg", "%d bytes" % size
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "gif", "%d bytes" % size
    if b"ftyp" in head[:32]:
        return "mp4", "%d bytes, brand %s" % (size, head[8:12].decode("latin-1", "replace"))
    if head[:4] == b"\x1a\x45\xdf\xa3":
        return "webm", "%d bytes" % size
    if head[:4] == b"RIFF" and head[8:12] == b"AVI ":
        return "avi", "%d bytes" % size
    return "unknown", "%d bytes, starts %r" % (size, head[:16])


# ---------------------------------------------------------------- the test

DOWNLOAD_RE = re.compile(r"(download|export|save|create|generate)", re.I)
# A stronger preference, tried first.
PRIMARY_RE = re.compile(r"(download|export the|save the .*(pdf|gif|mp4)|create the)", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--no-files", action="store_true",
                    help="do not feed the page an image")
    ap.add_argument("--file-type", default="png", choices=("png", "pdf", "webm"),
                    help="what to feed the page")
    ap.add_argument("--timeout", type=int, default=60000)
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("[FAIL] playwright is not installed")

    httpd, port = serve(ROOT)
    base = "http://127.0.0.1:%d" % port
    problems = []
    notes = []

    tmpdir = tempfile.mkdtemp(prefix="tool-smoke-")
    if args.file_type == "pdf":
        png_path = os.path.join(tmpdir, "document.pdf")
        with open(png_path, "wb") as fh:
            fh.write(make_pdf())
    else:
        png_path = os.path.join(tmpdir, "photo.png")
        with open(png_path, "wb") as fh:
            fh.write(make_png())

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            errors = []
            page.on("pageerror", lambda e: errors.append("pageerror: %s" % e))
            page.on("console", lambda m: errors.append("console: %s" % m.text)
                    if m.type == "error" else None)
            page.goto("%s/tools/%s/" % (base, args.slug), wait_until="load")
            page.wait_for_timeout(3000)

            for err in errors[:6]:
                problems.append("the page logged an error: %s" % err)

            # 1. A file input, if the tool takes files.
            inputs = page.query_selector_all("input[type=file]")
            if inputs and not args.no_files:
                if args.file_type == "pdf":
                    # A hand-rolled PDF can be malformed in a way that
                    # only a real parser notices, so the test PDF is
                    # printed by Chromium itself.
                    pdf_page = browser.new_page()
                    pdf_page.set_content(
                        "<html><body><h1>Wedding vendor contract</h1>"
                        "<p>Page one.</p></body></html>")
                    pdf_path = os.path.join(tmpdir, "document.pdf")
                    pdf_page.pdf(path=pdf_path, format="A4")
                    pdf_page.close()
                elif args.file_type == "webm":
                    pdf_path = make_webm(browser, tmpdir)
                else:
                    pdf_path = png_path
                try:
                    inputs[0].set_input_files(pdf_path)
                    page.wait_for_timeout(3000)
                    notes.append("fed a %s into the file input"
                                 % {"pdf": "PDF", "webm": "1 s WebM"}
                                 .get(args.file_type, "600x400 PNG"))
                except Exception as exc:  # noqa: BLE001
                    problems.append("the file input could not be filled: %s" % exc)
            elif inputs:
                notes.append("the page has a file input (skipped)")

            # 2. A download button. DISABLED buttons are skipped: the PDF
            # editor has a "Save a copy without a password" button that
            # stays disabled until a PDF is loaded, and clicking it just
            # times out.
            buttons = page.query_selector_all("button")
            candidates = []
            for b in buttons:
                try:
                    label = (b.inner_text() or "").strip()
                except Exception:  # noqa: BLE001
                    label = ""
                if not DOWNLOAD_RE.search(label):
                    continue
                try:
                    disabled = b.is_disabled()
                except Exception:  # noqa: BLE001
                    disabled = True
                if disabled:
                    notes.append("skipped the disabled button %r" % label[:40])
                    continue
                candidates.append((label, b))
            target = None
            for label, b in candidates:
                if PRIMARY_RE.search(label):
                    target = b
                    break
            if target is None and candidates:
                target = candidates[0][1]
            if target is None:
                problems.append("no download button found")
            else:
                try:
                    label = (target.inner_text() or "").strip()
                except Exception:  # noqa: BLE001
                    label = "?"
                notes.append("clicked the download button %r" % label[:40])
                try:
                    with page.expect_download(timeout=args.timeout) as info:
                        target.click()
                    download = info.value
                    out = os.path.join(tmpdir, download.suggested_filename or "out.bin")
                    download.save_as(out)
                    kind, detail = describe(out)
                    notes.append("downloaded %s: %s" % (kind, detail))
                    if kind == "unknown":
                        problems.append("the download is not a file we recognise")
                    if kind != "unknown" and os.path.getsize(out) < 512:
                        problems.append("the download is only %d bytes"
                                        % os.path.getsize(out))
                except Exception as exc:  # noqa: BLE001
                    problems.append("the download did not happen: %s" % str(exc)[:160])

            browser.close()
    finally:
        httpd.shutdown()

    for n in notes:
        print("   %s" % n)
    if problems:
        print("\n[FAIL] %d problem(s) on %s" % (len(problems), args.slug))
        for p in problems:
            print("   - %s" % p)
        return 1
    print("\n[OK] %s boots and its download produces real bytes" % args.slug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
