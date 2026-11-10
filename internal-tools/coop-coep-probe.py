#!/usr/bin/env python3
"""
MEASURE what cross-origin isolation (COOP + COEP) costs this site.

WHY THIS EXISTS
---------------
Any "do the video editing in the browser with ffmpeg.wasm" proposal needs
SharedArrayBuffer, and SharedArrayBuffer needs a cross-origin isolated
document:

    Cross-Origin-Opener-Policy: same-origin
    Cross-Origin-Embedder-Policy: require-corp

Those are DOCUMENT-WIDE headers, not a per-tool switch: every page of the
site gets them, and every third-party frame on every page is then subject
to the embedder policy.

This site carries two third-party scripts that are not optional:

  - Google AdSense  (pagead2.googlesyndication.com)  -> the revenue product
  - Microsoft Clarity (clarity.ms/tag/ywxiu97hg8.js) -> the only analytics
    left after GA4 and Baidu Tongji were removed (2026-11-28)

The question is not "can the browser be isolated" (it can) but "what does
isolation cost". This script answers it by MEASURING it: the same page is
served three times - plain, require-corp and credentialless - and the load
result of every third-party resource is compared.

The result (2026-11-12) is the reason ffmpeg.wasm is rejected here:

  * require-corp: the top-level scripts still load, so `window.adsbygoogle`
    and `window.clarity` are both truthy and the page LOOKS fine - but
    AdSense's ad frame transfers ZERO bytes and Clarity's collector never
    runs. Both die SILENTLY.
  * credentialless: keeps the third-party resources alive, but Safari does
    not support the directive at all (MDN: Safari "No support"), so a
    Safari visitor is not cross-origin isolated and SharedArrayBuffer is
    unavailable there anyway.

This script needs the network (it loads the real AdSense and Clarity
scripts), so it is a MEASUREMENT, not a deploy gate. Re-run it before
revisiting the decision.

Usage:  python internal-tools/coop-coep-probe.py
"""

import http.server
import socketserver
import sys
import threading
import time
from pathlib import Path

PORT = 8796

ADSENSE_CLIENT = "ca-pub-1670381960525419"
CLARITY_ID = "ywxiu97hg8"

# The probe page mirrors what the real site does:
#  - AdSense is loaded with crossOrigin='anonymous' (CORS mode)
#  - Clarity is loaded as a classic script (no-cors mode)
#  - a cross-origin iframe stands in for the ad/analytics frames
PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>coop coep probe</title>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=%s" crossorigin="anonymous"></script>
<script>
  (function(c,l,a,r,i,t,y){
    c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
    t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
    y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
  })(window, document, "clarity", "script", "%s");
</script>
</head><body>
<h1>coop coep probe</h1>
<ins class="adsbygoogle" style="display:block" data-ad-client="%s"></ins>
<iframe id="third" src="https://www.clarity.ms/" width="200" height="100"></iframe>
</body></html>
""" % (ADSENSE_CLIENT, CLARITY_ID, ADSENSE_CLIENT)

VARIANTS = {
    "/plain": {},
    "/isolated": {"Cross-Origin-Opener-Policy": "same-origin",
                  "Cross-Origin-Embedder-Policy": "require-corp"},
    "/credentialless": {"Cross-Origin-Opener-Policy": "same-origin",
                        "Cross-Origin-Embedder-Policy": "credentialless"},
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(Path(__file__).resolve().parent), **kw)

    def end_headers(self):
        path = self.path.split("?")[0]
        for header, value in VARIANTS.get(path, {}).items():
            self.send_header(header, value)
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in VARIANTS:
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def log_message(self, *a):
        pass


PROBE_JS = """() => {
  var res = performance.getEntriesByType('resource').map(function (e) {
    var host = '';
    try { host = new URL(e.name).host; } catch (err) { host = e.name; }
    return { host: host, name: e.name, status: e.responseStatus,
             type: e.initiatorType, size: e.transferSize };
  });
  return {
    isolated: !!window.crossOriginIsolated,
    sab: typeof SharedArrayBuffer !== 'undefined',
    resources: res,
    frames: Array.prototype.map.call(document.querySelectorAll('iframe'),
      function (f) { return f.src; }),
    adsLoaded: !!(window.adsbygoogle),
    clarityLoaded: !!window.clarity
  };
}"""


def sum_bytes(res, needle, kinds=None):
    total = 0
    hits = 0
    for r in res:
        if needle in r["host"]:
            if kinds and r["type"] not in kinds:
                continue
            total += r["size"]
            hits += 1
    return hits, total


def run(page, url, label):
    logs = []
    page.on("console", lambda m: logs.append((m.type, m.text)))
    page.goto(url, wait_until="load", timeout=60000)
    page.wait_for_timeout(7000)
    data = page.evaluate(PROBE_JS)
    res = data["resources"]

    ads_hits, ads_bytes = sum_bytes(res, "googleads.g.doubleclick.net")
    clar_hits, clar_bytes = sum_bytes(res, "clarity.ms")
    clar_sess_hits, clar_sess_bytes = sum_bytes(res, "scripts.clarity.ms")
    clar_ping_hits, clar_ping_bytes = sum_bytes(res, "q.clarity.ms")
    clar_frame_hits, clar_frame_bytes = sum_bytes(res, "c.clarity.ms")

    print("=" * 72)
    print(label)
    print("=" * 72)
    print("  crossOriginIsolated            : %s" % data["isolated"])
    print("  SharedArrayBuffer available    : %s" % data["sab"])
    print("  window.adsbygoogle             : %s   <- the LOOKS-OK signal" % data["adsLoaded"])
    print("  window.clarity                 : %s   <- the LOOKS-OK signal" % data["clarityLoaded"])
    print("  -- what actually happened --")
    print("  AdSense ad frame (doubleclick) : %d entries, %d bytes" % (ads_hits, ads_bytes))
    print("  Clarity total                   : %d entries, %d bytes" % (clar_hits, clar_bytes))
    print("     session script (scripts.)    : %d entries, %d bytes" % (clar_sess_hits, clar_sess_bytes))
    print("     collector ping (q.)           : %d entries, %d bytes" % (clar_ping_hits, clar_ping_bytes))
    print("     collection frame (c.)        : %d entries, %d bytes" % (clar_frame_hits, clar_frame_bytes))
    print("  iframes in the DOM              : %d" % len(data["frames"]))
    for f in data["frames"]:
        print("     %s" % f[:90])
    policy = [t for ty, t in logs if ("Cross-Origin" in t or "Refused" in t
                                      or "embedder" in t.lower())]
    print("  console policy messages        : %d" % len(policy))
    for t in policy[:6]:
        print("     - " + t[:200])
    print()
    return {"isolated": data["isolated"], "sab": data["sab"],
            "ads_script": data["adsLoaded"], "clarity_script": data["clarityLoaded"],
            "ad_frame_bytes": ads_bytes, "clarity_bytes": clar_bytes,
            "clarity_session_bytes": clar_sess_bytes,
            "clarity_ping_entries": clar_ping_hits}


def main():
    from playwright.sync_api import sync_playwright

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(0.6)
    print("serving on http://127.0.0.1:%d\n" % PORT)

    out = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for path, label in [
                    ("/plain", "A) TODAY - no cross-origin isolation"),
                    ("/isolated", "B) COOP: same-origin + COEP: require-corp"),
                    ("/credentialless", "C) COOP: same-origin + COEP: credentialless")]:
                ctx = browser.new_context()
                page = ctx.new_page()
                out[path] = run(page, "http://127.0.0.1:%d%s" % (PORT, path), label)
                ctx.close()
            browser.close()
    finally:
        httpd.shutdown()

    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    a = out["/plain"]
    b = out["/isolated"]
    c = out["/credentialless"]
    print("  isolation works technically      : require-corp %s / credentialless %s"
          % (b["isolated"], c["isolated"]))
    print("  SharedArrayBuffer appears        : require-corp %s / credentialless %s"
          % (b["sab"], c["sab"]))
    print("  AdSense ad frame bytes           : plain %d / require-corp %d / credentialless %d"
          % (a["ad_frame_bytes"], b["ad_frame_bytes"], c["ad_frame_bytes"]))
    print("  Clarity collector bytes          : plain %d / require-corp %d / credentialless %d"
          % (a["clarity_bytes"], b["clarity_bytes"], c["clarity_bytes"]))
    print("  Clarity collector pings          : plain %d / require-corp %d / credentialless %d"
          % (a["clarity_ping_entries"], b["clarity_ping_entries"], c["clarity_ping_entries"]))
    print()
    print("  Read this as: require-corp keeps every top-level script alive, so")
    print("  window.adsbygoogle and window.clarity are still truthy and NOTHING")
    print("  looks broken - while the ad frame and the whole Clarity collector")
    print("  are blocked. Safari does not implement COEP credentialless at all,")
    print("  so variant C is not an option for Safari visitors either.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
