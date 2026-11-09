#!/usr/bin/env python3
"""
Verify the compress tool's AVIF and lossless-WebP output (§2.12).

WHY THIS EXISTS
---------------
Four claims have to be checked on the BYTES, not on the absence of an
error:

  * "AVIF output" - the produced file has to be a real AVIF. The trap is
    that canvas.toBlob('image/avif') does not fail in a browser that
    cannot encode AVIF: it quietly returns PNG bytes. So the check is the
    magic number - an AVIF file is an ISO-BMFF box whose brand is
    `avif` - and not the blob's MIME type, which a browser is free to
    lie about.
  * "lossless WebP" - the produced file has to decode back to the EXACT
    same pixels AND carry the VP8L chunk. A lossy WebP at quality 1.0
    looks lossless to the eye and is not; the only honest test is a
    pixel-for-pixel comparison.
  * "the browser's own WebP at quality 1.0 is lossless" - measured, not
    assumed. Chromium and Firefox switch to the lossless encoder there.
    If that ever stops being true, this test fails instead of the tool
    quietly shipping lossy files under a lossless label.
  * "the file name matches the file" - Safari cannot write WebP and
    returns a PNG. A tool that names that blob .webp hands the user a
    PNG wearing the wrong extension, so the tool probes the browser
    first and falls back honestly.

The AVIF encoder is WebAssembly and is reached through an import map, so
this test also proves that the import map, the module script and the
nonce injection all work under the LIVE CSP.

Usage:  python scripts/verify-avif-lossless.py
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
PORT = 8803

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


# The in-page proof. It runs against the real encoder module, loaded
# through the real import map, under the real CSP.
ROUNDTRIP_JS = r"""
async () => {
  const out = { errors: [] };
  function compare(a, b) {
    if (a.length !== b.length) return { max: 255, differing: a.length };
    let max = 0, differing = 0;
    for (let i = 0; i < a.length; i++) {
      const d = Math.abs(a[i] - b[i]);
      if (d) { differing++; if (d > max) max = d; }
    }
    return { max: max, differing: differing };
  }
  async function decode(blob) {
    const bmp = await createImageBitmap(blob);
    const c = document.createElement('canvas');
    c.width = bmp.width; c.height = bmp.height;
    c.getContext('2d').drawImage(bmp, 0, 0);
    return c.getContext('2d').getImageData(0, 0, bmp.width, bmp.height);
  }
  // Scan the WHOLE file for the chunk markers. The first 24 bytes only
  // show VP8X (the extended-format header); the image data itself is in
  // a VP8 (lossy) or a VP8L (LOSSLESS) chunk further in.
  async function chunks(blob) {
    const buf = new Uint8Array(await blob.arrayBuffer());
    const s = Array.from(buf).map(b => b >= 32 && b < 127 ? String.fromCharCode(b) : '.').join('');
    return {
      vp8: s.indexOf('VP8 ') >= 0,
      vp8l: s.indexOf('VP8L') >= 0,
      isAvif: s.indexOf('ftypavif') >= 0 || s.indexOf('ftypavis') >= 0,
      isPng: buf[0] === 0x89 && buf[1] === 0x50,
      head: s.slice(0, 20),
      size: buf.length
    };
  }

  // TWO fixtures, because they prove different things:
  //
  //  * NOISY - per-pixel noise. A lossy codec cannot reproduce it
  //    exactly, a lossless one can. Without the noise a smooth
  //    synthetic image can come out of a lossy encoder pixel-identical,
  //    and the "is it really lossless" test would prove nothing.
  //  * SMOOTH - a gradient with flat shapes, i.e. photograph-like. This
  //    is the one the SIZE comparison uses.
  function makeCanvas(withNoise) {
    const c = document.createElement('canvas');
    c.width = 96; c.height = 72;
    const ctx = c.getContext('2d');
    const g = ctx.createLinearGradient(0, 0, 96, 72);
    g.addColorStop(0, '#204080'); g.addColorStop(1, '#e8d8a0');
    ctx.fillStyle = g; ctx.fillRect(0, 0, 96, 72);
    ctx.fillStyle = '#a02040'; ctx.fillRect(12, 10, 24, 18);
    ctx.fillStyle = '#ffffff'; ctx.fillRect(50, 30, 20, 20);
    if (!withNoise) return { canvas: c, data: ctx.getImageData(0, 0, 96, 72) };
    const img = ctx.getImageData(0, 0, 96, 72);
    let seed = 12345;
    const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return (seed >> 16) & 0xff; };
    for (let i = 0; i < img.data.length; i += 4) {
      img.data[i] = (img.data[i] + rnd()) & 0xff;
      img.data[i + 1] = (img.data[i + 1] + rnd()) & 0xff;
      img.data[i + 2] = (img.data[i + 2] + rnd()) & 0xff;
    }
    ctx.putImageData(img, 0, 0);
    return { canvas: c, data: img };
  }
  const noisy = makeCanvas(true);
  const smooth = makeCanvas(false);

  if (!window.weddingAIImageCodecs) { out.errors.push('the encoder module did not load'); return out; }

  // --- the browser's OWN WebP at quality 1.0: lossless? ----------------
  try {
    const wl = await new Promise(r => noisy.canvas.toBlob(b => r(b), 'image/webp', 1.0));
    out.webpQ1Size = wl.size;
    out.webpQ1Type = wl.type;
    out.webpQ1Chunks = await chunks(wl);
    const back = await decode(wl);
    out.webpQ1Diff = compare(noisy.data.data, back.data);
  } catch (e) { out.errors.push('webp q=1.0: ' + e.message); }

  // --- and the same encoder at a normal quality: lossy -----------------
  try {
    const w8 = await new Promise(r => noisy.canvas.toBlob(b => r(b), 'image/webp', 0.8));
    const back = await decode(w8);
    out.webpQ08Diff = compare(noisy.data.data, back.data);
    out.webpQ08Size = w8.size;
  } catch (e) { out.errors.push('webp q=0.8: ' + e.message); }

  // --- AVIF ------------------------------------------------------------
  try {
    const av = await window.weddingAIImageCodecs.encodeAvif(smooth.data, { quality: 60, speed: 6 });
    out.avifSize = av.size;
    out.avifType = av.type;
    out.avifChunks = await chunks(av);
    const back = await decode(av);
    out.avifSize2 = [back.width, back.height];
  } catch (e) { out.errors.push('AVIF: ' + e.message); }

  // --- the sizes, on the photograph-like fixture ----------------------
  const jb = await new Promise(r => smooth.canvas.toBlob(b => r(b), 'image/jpeg', 0.8));
  out.jpegSize = jb ? jb.size : 0;

  // --- what the browser does with an AVIF request: it returns a PNG ---
  const fake = await new Promise(r => smooth.canvas.toBlob(b => r(b), 'image/avif'));
  out.nativeAvif = fake ? { type: fake.type, size: fake.size } : null;
  return out;
}
"""


def make_test_jpeg(path: Path) -> None:
    from PIL import Image
    import numpy as np
    rng = np.random.default_rng(11)
    arr = rng.integers(60, 200, size=(480, 640, 3), dtype=np.uint8)
    Image.fromarray(arr).save(path, "JPEG", quality=90)


def magic(path: Path):
    """(kind, info) from the first bytes of the file."""
    data = path.read_bytes()[:64]
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        full = path.read_bytes()
        s = bytes(full).decode("latin-1")
        return ("webp", {"lossless": "VP8L" in s, "head": data[:20].decode("latin-1")})
    if b"ftypavif" in data or b"ftypavis" in data:
        return ("avif", {"head": data[:20].decode("latin-1")})
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ("png", {"head": data[:20].decode("latin-1")})
    if data[:2] == b"\xff\xd8":
        return ("jpeg", {"head": data[:20].decode("latin-1")})
    return ("unknown", {"head": data[:20].decode("latin-1")})


def main():
    from playwright.sync_api import sync_playwright

    tmpdir = Path(tempfile.mkdtemp(prefix="wa-avif-"))
    photo = tmpdir / "photo.jpg"
    make_test_jpeg(photo)
    print("test photo: %d bytes" % photo.stat().st_size)

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.6)
    url = "http://127.0.0.1:%d/tools/compress-wedding-photos/" % PORT
    print("serving on %d with the live CSP" % PORT)

    failures = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(accept_downloads=True)
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))

            page.goto(url, wait_until="load", timeout=60000)
            print("loaded %s" % url)

            # --- 1. the module and the import map -------------------------
            has = page.evaluate("() => !!window.weddingAIImageCodecs")
            if not has:
                failures.append("window.weddingAIImageCodecs is missing - the import map "
                                "or the module script did not work")
            else:
                print("  the encoder module is mounted")

            # --- 2. the encoders themselves ------------------------------
            res = page.evaluate(ROUNDTRIP_JS, None)
            for e in res.get("errors", []):
                failures.append(e)

            q1 = res.get("webpQ1Chunks") or {}
            print("  browser WebP q=1.0: %s bytes, head=%r, VP8L=%s"
                  % (res.get("webpQ1Size"), q1.get("head"), q1.get("vp8l")))
            print("  browser WebP q=0.8: %s bytes" % res.get("webpQ08Size"))
            av = res.get("avifChunks") or {}
            print("  AVIF:               %s bytes, head=%r" % (res.get("avifSize"), av.get("head")))
            print("  Canvas JPEG:        %s bytes" % res.get("jpegSize"))
            print("  the browser asked for AVIF natively and got: %s"
                  % (res.get("nativeAvif"),))

            if not q1.get("vp8l"):
                failures.append("the browser's WebP at quality 1.0 is not lossless "
                                "(no VP8L chunk) - the lossless option would be a lie")
            diff = res.get("webpQ1Diff") or {}
            if diff.get("max") != 0:
                failures.append("the browser's WebP at quality 1.0 is NOT pixel-exact: "
                                "%s pixels differ, worst delta %s"
                                % (diff.get("differing"), diff.get("max")))
            else:
                print("  the browser's WebP at quality 1.0 is pixel-exact")
            diff08 = res.get("webpQ08Diff") or {}
            if diff08.get("max") == 0 and diff08.get("differing") == 0:
                failures.append("the browser's WebP at quality 0.8 came out pixel-exact - "
                                "the contrast test proves nothing")

            if not av.get("isAvif"):
                failures.append("the AVIF output is not an AVIF file: %r" % av.get("head"))
            if res.get("avifSize2") != [96, 72]:
                failures.append("the AVIF does not decode back to 96x72: %s" % res.get("avifSize2"))
            else:
                print("  the AVIF decodes back to 96x72")

            if res.get("avifSize") and res.get("jpegSize"):
                if res["avifSize"] >= res["jpegSize"]:
                    failures.append("the AVIF (%d bytes) is not smaller than the "
                                    "browser's JPEG (%d bytes) at a comparable quality"
                                    % (res["avifSize"], res["jpegSize"]))
                else:
                    print("  the AVIF is %d%% smaller than the browser's JPEG"
                          % round(100 - res["avifSize"] * 100.0 / res["jpegSize"]))

            # The browser must NOT be able to make an AVIF on its own -
            # that is the whole reason the encoder exists.
            native = res.get("nativeAvif") or {}
            if native.get("type") == "image/avif":
                print("  NOTE: this browser now encodes AVIF natively - the 3.4 MB "
                      "encoder is not needed here")
            elif native.get("type") == "image/png":
                print("  confirmed: asking the browser for AVIF returns PNG bytes "
                      "(no browser encodes AVIF)")
            else:
                failures.append("unexpected answer when asking the browser for AVIF: %s"
                                % native)

            # --- 3. the tool itself --------------------------------------
            print("\n  the tool, end to end:")
            for fmt, expect_kind, expect_lossless in (
                    ("image/avif", "avif", None),
                    ("webp-lossless", "webp", True),
            ):
                page.goto(url, wait_until="load", timeout=60000)
                page.select_option("#format", fmt)
                page.set_input_files("#file-input", str(photo))
                page.wait_for_timeout(700)
                page.click("#run-btn")
                page.wait_for_selector(".wa-tool-status-done, .wa-tool-status-error",
                                       timeout=300000)
                state = page.evaluate("""() => {
                    var row = document.querySelector('#file-list .wa-tool-file-row');
                    var err = document.querySelector('.wa-tool-err');
                    var name = document.querySelector('#file-list .wa-tool-name');
                    return { cls: row ? row.className : '(no row)',
                             err: err ? err.textContent : null,
                             name: name ? name.textContent : null };
                }""")
                if "wa-tool-status-done" not in state["cls"]:
                    failures.append("the %s run ended in %s: %s"
                                    % (fmt, state["cls"], state["err"]))
                    continue
                out = tmpdir / ("out.%s" % fmt.replace("/", "-"))
                with page.expect_download(timeout=120000) as dl:
                    page.click(".wa-tool-status-done .wa-tool-actions button")
                dl.value.save_as(str(out))
                size = out.stat().st_size
                kind, info = magic(out)
                print("    %-14s -> %s, %d bytes, name=%r, head=%r"
                      % (fmt, kind, size, state["name"], info["head"]))
                if kind != expect_kind:
                    failures.append("the %s run produced a %s file - the name and the "
                                    "bytes disagree" % (fmt, kind))
                if expect_lossless and not info.get("lossless"):
                    failures.append("the %s run produced a WebP without a VP8L chunk - "
                                    "it is not lossless" % fmt)

            csp_errors = [e for e in errors if "Content Security Policy" in e or "Refused to" in e]
            for e in csp_errors:
                failures.append("CSP violation: " + e[:220])
            for e in [e for e in errors if e not in csp_errors][:6]:
                print("    console error:", e[:200])

            browser.close()
    finally:
        httpd.shutdown()

    print()
    if failures:
        print("RESULT: FAIL")
        for f in failures:
            print("  - " + f)
        return 1
    print("RESULT: OK - the AVIF is a real AVIF, the lossless WebP is pixel-exact, "
          "the file names match the bytes, and the import map works under the live CSP")
    return 0


if __name__ == "__main__":
    sys.exit(main())
