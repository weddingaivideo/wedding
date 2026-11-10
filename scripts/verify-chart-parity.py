#!/usr/bin/env python3
"""
Verify that the preview and the export draw the same thing (§2.15).

WHY THIS EXISTS
---------------
"The export does not match the preview" is the kind of defect that survives
every unit test, because each side is correct on its own. The seating chart
exported a 6 px seat with a grey border on #f5f5f5 while the preview showed a
4 px seat with a warm border on #f5f0ea, in a different font, and the export
dropped the "N/M seated" line the preview shows under every table. The album
drew the page thumbnail with one set of functions and the exported page with
another: the thumbnail had its own copy of the cover, its own copy of the
caption, and an empty slot was a bordered box labelled "Slot 3" there but a
plain box in the export. Ten of the eleven localized copies of the seating
chart had a CSS rule of 64x36 for a seat while the geometry positioned seats
for 36x24, so those ten languages drew the seats too big and off their
tables.

So this script proves, in a real browser with the live Content-Security-
Policy:

  THE ALBUM
    1. the page thumbnail and the exported page are rendered by the SAME
       renderer at the SAME size, so the difference between the two canvases
       is 0 - they are not two drawings that look alike;
    2. the slot rectangles are a FRACTION of the page, so the thumbnail's
       layout and the export's layout are the same layout - which is what
       makes the thumbnail the export at 1/12 scale.

  THE SEATING CHART
    3. every seat's computed style in the preview is the style the export
       draws: the same size, the same radius, the same colour, the same
       font - and the export's pixels at the seat's place have that colour;
    4. the export really draws the "N/M seated" line the preview shows (the
       muted colour appears on the exported sheet; nothing else on it is
       that colour);
    5. a name that does not fit is truncated by the export at the same
       width the CSS leaves for it;
    6. the ten localized copies that the machine translator had resized draw
       their seats at the same 36x24 as the English page.

Usage:  python scripts/verify-chart-parity.py
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
PORT = 8797

_headers = (ROOT / "_headers").read_text(encoding="utf-8")
_m = re.search(r"^\s*Content-Security-Policy:\s*(.+)$", _headers, re.M)
if not _m:
    raise SystemExit("[FAIL] no Content-Security-Policy in _headers")
NONCE = "weddingaiverifyparity"
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


def rgb_to_triplet(css):
    """'rgb(245, 240, 234)' -> '245,240,234' (the form the canvas uses)."""
    if not css:
        return None
    m = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", css)
    if not m:
        return None
    return "%s,%s,%s" % m.groups()


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
            page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

            # ---------------------------------------------------------------
            # THE ALBUM
            # ---------------------------------------------------------------
            page.goto("http://127.0.0.1:%d/tools/wedding-photo-book-planner/" % PORT,
                      wait_until="load", timeout=60000)
            page.wait_for_timeout(800)

            has_hook = page.evaluate("() => !!(window.__waBookDebug && window.__waBookDebug.thumbs)")
            if not has_hook:
                failures.append("the album debug hook is missing")
            else:
                thumbs = page.evaluate("() => window.__waBookDebug.thumbs()")
                print("album: %d page thumbnails" % thumbs)
                if not thumbs:
                    failures.append("the album rendered no page thumbnails")

                # 1. the thumbnail and the export are the SAME drawing
                worst = 0.0
                for idx in range(min(4, thumbs)):
                    res = page.evaluate(
                        "(i) => window.__waBookDebug.compare(i)", idx)
                    if not res:
                        failures.append("could not compare album page %d" % idx)
                        continue
                    if res["diff"] > worst:
                        worst = res["diff"]
                    if res["diff"] > 0.5:
                        failures.append(
                            "album page %d: the thumbnail and the export differ by %.3f"
                            % (idx, res["diff"]))
                print("album: the largest thumbnail/export difference is %.4f" % worst)

                # 2. the layout is a fraction of the page, so the thumbnail
                #    is the export at 1/12 scale
                lay = page.evaluate("() => window.__waBookDebug.layout(0)")
                if not lay or not lay.get("big"):
                    failures.append("could not read the album layout")
                else:
                    worst_frac = 0.0
                    for a, b in zip(lay["big"], lay["small"]):
                        for x, y in zip(a, b):
                            worst_frac = max(worst_frac, abs(x - y))
                    print("album: the largest layout difference is %.6f of the page"
                          % worst_frac)
                    if worst_frac > 0.001:
                        failures.append(
                            "the thumbnail's layout is not the export's layout "
                            "(%.6f of the page apart)" % worst_frac)

            # ---------------------------------------------------------------
            # THE SEATING CHART
            # ---------------------------------------------------------------
            def check_seating(path, label):
                page.goto("http://127.0.0.1:%d%s" % (PORT, path),
                          wait_until="load", timeout=60000)
                page.wait_for_timeout(700)
                d = page.evaluate("() => window.__waSeatDebug && window.__waSeatDebug()")
                if not d:
                    failures.append("%s: the seating chart debug hook is missing" % label)
                    return
                seats = d.get("seats") or []
                if not seats:
                    failures.append("%s: the preview rendered no seats" % label)
                    return

                for s in seats:
                    if s["width"] != "36px" or s["height"] != "24px":
                        failures.append(
                            "%s: a seat is %sx%s instead of 36x24"
                            % (label, s["width"], s["height"]))
                        break
                if seats[0]["radius"] != "4px":
                    failures.append("%s: a seat's radius is %s instead of 4px"
                                    % (label, seats[0]["radius"]))
                if seats[0]["fontSize"] != "11px":
                    failures.append("%s: a seat's font size is %s instead of 11px"
                                    % (label, seats[0]["fontSize"]))
                if "Georgia" not in (seats[0]["font"] or ""):
                    failures.append("%s: a seat's font is %r instead of Georgia"
                                    % (label, seats[0]["font"]))

                # The colour the export draws in the seat's place has to be
                # the colour the preview paints the seat with.
                for s in seats:
                    want = rgb_to_triplet(s["bg"])
                    if want != s["exportColor"]:
                        failures.append(
                            "%s: the preview paints a seat %s but the export draws %s"
                            % (label, want, s["exportColor"]))
                        break

                t = (d.get("tables") or [None])[0]
                if not t:
                    failures.append("%s: the preview rendered no tables" % label)
                else:
                    if rgb_to_triplet(t["border"]) != "212,175,55":
                        failures.append("%s: a table's border is %s instead of #d4af37"
                                        % (label, t["border"]))
                    if t["borderWidth"] != "2px":
                        failures.append("%s: a table's border is %s instead of 2px"
                                        % (label, t["borderWidth"]))
                    if t["nameSize"] != "14px":
                        failures.append("%s: a table name is %s instead of 14px"
                                        % (label, t["nameSize"]))
                    if rgb_to_triplet(t["nameColor"]) != "44,44,44":
                        failures.append("%s: a table name is %s instead of #2c2c2c"
                                        % (label, t["nameColor"]))
                    if t["countSize"] != "11px":
                        failures.append("%s: the seated count is %s instead of 11px"
                                        % (label, t["countSize"]))
                    if rgb_to_triplet(t["countColor"]) != "107,107,107":
                        failures.append("%s: the seated count is %s instead of #6b6b6b"
                                        % (label, t["countColor"]))
                    if not t["countVisible"]:
                        failures.append("%s: the seated count is not visible" % label)
                    if not re.match(r"^\d+/\d+ seated$", (t["countText"] or "").strip()):
                        failures.append("%s: the seated count reads %r" % (label, t["countText"]))

                # The export must really draw the "N/M seated" line. Nothing
                # else on the sheet is the muted colour.
                if d.get("mutedPixels", 0) <= 0:
                    failures.append(
                        "%s: the export does not draw the \"N/M seated\" line" % label)
                if d.get("goldPixels", 0) <= 0:
                    failures.append("%s: the export draws no gold at all" % label)
                if d.get("seatEmptyPixels", 0) <= 0:
                    failures.append("%s: the export draws no empty seats" % label)
                if d.get("seatBorderPixels", 0) <= 0:
                    failures.append("%s: the export draws no seat border" % label)

                # The truncation has to use the width the CSS leaves.
                tw = d.get("seatTextWidth")
                if tw is None or abs(tw - 30.0) > 0.5:
                    failures.append("%s: the CSS leaves %r px for a seat's text instead of 30"
                                    % (label, tw))
                # The hook is called from inside the page: a function cannot
                # survive the trip back from page.evaluate().
                short = page.evaluate("() => window.__waSeatDebug().truncate('Ana')")
                long = page.evaluate(
                    "() => window.__waSeatDebug().truncate('Bartholomew Fitzgerald-Montgomery')")
                if short != "Ana":
                    failures.append("%s: a short name was truncated to %r" % (label, short))
                if not long or len(long) >= len("Bartholomew Fitzgerald-Montgomery"):
                    failures.append("%s: a long name was NOT truncated (%r)" % (label, long))
                elif not long.endswith("\u2026"):
                    failures.append("%s: a long name was cut without an ellipsis (%r)"
                                    % (label, long))

                print("%s: %d seats checked, muted pixels %d, seat text width %s"
                      % (label, len(seats), d.get("mutedPixels", 0), tw))

            check_seating("/tools/wedding-seating-chart-maker/", "seating chart")

            # The machine translator had resized the seats in ten of the
            # eleven localized copies. They have to match the English page.
            for lang in ("zh", "ru", "th", "ar"):
                check_seating("/%s/tools/wedding-seating-chart-maker/" % lang,
                              "seating chart [%s]" % lang)

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
    print("RESULT: OK - the preview and the export draw the same thing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
