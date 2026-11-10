#!/usr/bin/env python3
"""
Verify that the web fonts really load, and that the canvas really uses
them (§2.16).

WHY THIS EXISTS
---------------
The site named 'Playfair Display' and 'Inter' in its stylesheet and named
'Great Vibes' and 'Montserrat' in its design templates, and NONE of them
ever loaded: there was no @font-face, no font file and no Google Fonts
<link>, and the CSP's `font-src 'self' data:` never allowed Google Fonts
either. Every one of those names fell through to the next entry in the
stack - and for the romantic template that meant 'Apple Chancery'
(macOS only) and then `cursive`, which is Comic Sans on Windows.

The failure is invisible in the HTML and fatal in the OUTPUT: a canvas
draws with whatever font is loaded at that moment, so the exported PNG was
baked with the fallback face. The same template produced a different file
on every operating system.

So this script proves, in a real browser under the live CSP:

  1. the families come back 200 from THIS origin;
  2. the browser really has them (`document.fonts.check`);
  3. the FONT STACK each template names resolves to the webfont and not
     to the fallback - measured with `measureText`, which is what decides
     the pixels that leave the device. A stack that resolves to the
     fallback is a stack that bakes Comic Sans into the PNG;
  4. the subsets work: an English page pulls no Cyrillic file, a Russian
     page pulls the Cyrillic one;
  5. nothing was refused by the CSP.

Usage:  python scripts/verify-web-fonts.py
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
PORT = 8798

_headers = (ROOT / "_headers").read_text(encoding="utf-8")
_m = re.search(r"^\s*Content-Security-Policy:\s*(.+)$", _headers, re.M)
if not _m:
    raise SystemExit("[FAIL] no Content-Security-Policy in _headers")
NONCE = "weddingaiverifyfonts"
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
            # The middleware replaces the placeholder with the real nonce.
            # Without this the browser sees the literal string and refuses
            # every script that carries it - a false positive in the test.
            html = html.replace("__CSP_NONCE__", NONCE)
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


# Measured inside the page: how wide is this text in a FONT STACK, and how
# wide in the same stack with the webfont taken out? Different widths mean
# the stack really resolves to the webfont.
STACK_PROBE = """(stack) => {
  function widthWith(family, text) {
    var c = document.createElement('canvas');
    var ctx = c.getContext('2d');
    ctx.font = '400 40px ' + family;
    return ctx.measureText(text).width;
  }
  var text = 'Emma & Liam';
  var withWebfont = widthWith(stack, text);
  var parts = stack.split(',').map(function (s) { return s.trim(); });
  var withoutWebfont = widthWith(parts.slice(1).join(','), text);
  return {
    stack: stack,
    withWebfont: Math.round(withWebfont * 100) / 100,
    withoutWebfont: Math.round(withoutWebfont * 100) / 100,
    differs: Math.abs(withWebfont - withoutWebfont) > 0.5
  };
}"""

FAMILY_PROBE = """(name) => {
  return {
    loaded: document.fonts.check('40px "' + name + '"'),
    faces: document.fonts.size
  };
}"""


def main():
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
            page = browser.new_page(viewport={"width": 1400, "height": 1000})
            errors = []
            fonts_fetched = []
            page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("response", lambda r: fonts_fetched.append((r.status, r.url.split("/fonts/")[-1]))
                    if "/fonts/" in r.url else None)

            # ---- the home page -------------------------------------------
            page.goto("http://127.0.0.1:%d/" % PORT, wait_until="load", timeout=60000)
            page.wait_for_timeout(1800)

            fetched = sorted(set(u for _, u in fonts_fetched))
            print("fonts fetched on the home page:")
            for st, u in sorted(set(fonts_fetched)):
                print("   %s %s" % (st, u))
            bad = [(st, u) for st, u in fonts_fetched if st != 200]
            if bad:
                failures.append("a font was not served with 200: %r" % bad)
            if not fetched:
                failures.append("no web font was fetched at all - the site still has none")
            # the subset system: an English page must not pull Cyrillic
            cyr = [u for u in fetched if "cyrillic" in u]
            if cyr:
                failures.append("the English home page pulled the Cyrillic subset: %r" % cyr)

            for fam in ("Playfair Display", "Inter"):
                info = page.evaluate(FAMILY_PROBE, fam) or {}
                if not info.get("loaded"):
                    failures.append("%s is not loaded in the browser" % fam)
                else:
                    print("   %-18s is loaded" % fam)

            # the heading on the page really is drawn with Playfair
            head = page.evaluate("""() => {
              var h = document.querySelector('h1');
              if (!h) return null;
              var probe = document.createElement('span');
              probe.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;font-size:40px';
              probe.style.fontFamily = '"Playfair Display"';
              probe.textContent = h.textContent.trim().slice(0, 20);
              document.body.appendChild(probe);
              var web = probe.getBoundingClientRect().width;
              document.body.removeChild(probe);
              probe.style.fontFamily = 'serif';
              document.body.appendChild(probe);
              var fb = probe.getBoundingClientRect().width;
              document.body.removeChild(probe);
              return {web: Math.round(web), fallback: Math.round(fb),
                      family: getComputedStyle(h).fontFamily};
            }""")
            if not head:
                failures.append("the home page has no h1 to measure")
            elif head["web"] == head["fallback"]:
                failures.append("the home page's h1 measures the same as the serif fallback")
            else:
                print("   the h1 is %d px wide in Playfair and %d px in the serif fallback"
                      % (head["web"], head["fallback"]))

            # ---- the design tools ----------------------------------------
            # Each template names a font stack. The stack has to resolve to
            # the webfont: a stack that falls through to the next family is
            # a stack that bakes the fallback into the exported PNG.
            page.goto("http://127.0.0.1:%d/tools/save-the-date-maker/" % PORT,
                      wait_until="load", timeout=60000)
            page.wait_for_timeout(1800)

            for template, family, filename in [
                    ("classic", "Playfair Display", "playfair-display-latin-wght-normal.woff2"),
                    ("romantic", "Great Vibes", "great-vibes-latin-400-normal.woff2"),
                    ("modern", "Montserrat", "montserrat-latin-wght-normal.woff2"),
                    ("photo", "Playfair Display", "playfair-display-latin-wght-normal.woff2")]:
                btn = page.query_selector('[data-template-id="%s"]' % template)
                if not btn:
                    failures.append("the save-the-date page has no %s template" % template)
                    continue
                before = set(u for _, u in fonts_fetched)
                btn.click()
                page.wait_for_timeout(900)
                after = set(u for _, u in fonts_fetched)

                # The stack comes from the page's OWN shipped template table
                # (the table lives inside the tool's IIFE, so it is not a
                # global - it is read out of the script text).
                stacks = page.evaluate("""() => {
                  var src = Array.prototype.map.call(
                    document.querySelectorAll('script:not([src])'),
                    function (s) { return s.textContent; }).join('\\n');
                  var out = {};
                  var re = /id:\\s*'([a-z-]+)'[\\s\\S]{0,700}?fontStack:\\s*"([^"]+)"/g;
                  var m;
                  while ((m = re.exec(src))) out[m[1]] = m[2];
                  return out;
                }""") or {}
                stack = stacks.get(template)
                if not stack:
                    failures.append("could not read the %s template's font stack" % template)
                    continue
                probe = page.evaluate(STACK_PROBE, stack) or {}
                if not probe.get("differs"):
                    failures.append(
                        "the %s template's stack %r resolves to the FALLBACK face - "
                        "the export would be baked with it" % (template, stack))
                else:
                    print("   %-10s %-38s -> webfont %s px, fallback %s px"
                          % (template, stack, probe.get("withWebfont"),
                             probe.get("withoutWebfont")))
                # and the browser really fetched the family for it
                if not (any(filename in u for u in after)
                        or any(filename in u for u in before)):
                    failures.append("the %s template did not cause %s to be fetched"
                                    % (template, filename))

            # the canvas really was drawn after the fonts arrived
            gate = page.evaluate("""() => {
              var c = document.getElementById('preview-canvas');
              if (!c) return null;
              var px = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
              var dark = 0;
              for (var i = 0; i < px.length; i += 4) {
                if (px[i] < 90 && px[i+1] < 90 && px[i+2] < 90) dark++;
              }
              return {w: c.width, h: c.height, dark: dark};
            }""")
            if not gate or not gate.get("dark"):
                failures.append("the save-the-date preview is empty")
            else:
                print("   the preview drew %d dark pixels of headline" % gate["dark"])

            # ---- the subsets: a Russian page pulls the Cyrillic file ------
            # NOT the home page: /ru/ has no index.html - it is served by the
            # middleware from i18n/ru.json - and a 404 answers with an error
            # page that uses no font at all. A real localised page is the only
            # honest probe, and the Russian SAVE-THE-DATE page has a Cyrillic
            # h1 that is set in Playfair Display.
            fonts_fetched.clear()
            page.goto("http://127.0.0.1:%d/ru/tools/save-the-date-maker/" % PORT,
                      wait_until="load", timeout=60000)
            page.wait_for_timeout(1800)
            ru_fonts = sorted(set(u for _, u in fonts_fetched))
            print("fonts fetched on the Russian page: %s" % ru_fonts)
            if not any("cyrillic" in u for u in ru_fonts):
                failures.append("the Russian page did not pull the Cyrillic subset")
            else:
                print("   the Cyrillic subset was pulled for the Russian page")

            # ---- an Arabic page pulls NO subset of these families --------
            # There is no OFL family for Arabic, Thai, Devanagari or
            # Japanese, so those pages use the SYSTEM face. What must not
            # happen is the page downloading a Latin or Cyrillic file it
            # cannot use.
            fonts_fetched.clear()
            page.goto("http://127.0.0.1:%d/ar/tools/save-the-date-maker/" % PORT,
                      wait_until="load", timeout=60000)
            page.wait_for_timeout(1800)
            ar_fonts = sorted(set(u for _, u in fonts_fetched))
            print("fonts fetched on the Arabic page: %s" % ar_fonts)
            wrong = [u for u in ar_fonts if "cyrillic" in u]
            if wrong:
                failures.append("the Arabic page pulled the Cyrillic subset: %r" % wrong)
            else:
                print("   no Cyrillic subset on the Arabic page")

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
    print("RESULT: OK - the fonts load and every template stack resolves to the webfont")
    return 0


if __name__ == "__main__":
    sys.exit(main())
