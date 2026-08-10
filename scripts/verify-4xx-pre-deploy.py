#!/usr/bin/env python3
"""
Pre-push HTTP verification for _redirects and structural-data changes.

Per project memory (2026-08-09 rule):
  Before commit/push touching _redirects/Bulk/middleware, MUST run HTTP
  verification. Don't trust file review.

24-probe matrix:
  - 5 EN top-level pages (home, gallery, pricing, about, blog)
  - 9 i18n mirrors (zh, es, fr, de, pt, ja, ru, ar, th) of home
  - 10 EN service detail pages

Each probe checks:
  - HTTP status (200 / 301 / 308)
  - Location header for 30x responses

IWR is preferred (PowerShell 7+); fall back to curl.exe.
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

SITE = "https://weddingai.video"

# 24 probes — keep aligned with memory's matrix.
EN_TOP = [
    "/",
    "/gallery/",
    "/pricing/",
    "/about/",
    "/blog/",
]
I18N = [f"/{lang}/" for lang in ("zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th")]
SERVICE = [
    "/services/",
    "/services/personalization/ai-video-generator/",
    "/services/personalization/cartoon-style/",
    "/services/personalization/meme-generator/",
    "/services/personalization/multilingual/",
    "/services/personalization/pet-wedding/",
    "/services/personalization/wedding-trailer/",
    "/services/video-enhancement/slow-motion/",
    "/services/video-enhancement/vintage-restoration/",
    "/services/absence-compensation/family-message/",
]

# Known 1:1 301 redirects (from _redirects). The 5+9 probes above should
# return 200 directly (no redirect); only sample historical 301s to confirm
# the redirect engine itself still works.
SAMPLE_301s = [
    # Historical slug-migration 301s that exist in _redirects. Probing these
    # confirms the redirect engine still works after our schema changes.
    ("/blog/02-vhs-to-digital-wedding-cost",   f"{SITE}/blog/vhs-to-digital-wedding-cost/"),
    ("/blog/02-vhs-to-digital-wedding-cost/",  f"{SITE}/blog/vhs-to-digital-wedding-cost/"),
    ("/en/blog/02-vhs-to-digital-wedding-cost/", f"{SITE}/blog/vhs-to-digital-wedding-cost/"),
    ("/zh/blog/02-vhs-to-digital-wedding-cost/", f"{SITE}/zh/blog/vhs-to-digital-wedding-cost/"),
    ("/es/blog/02-vhs-to-digital-wedding-cost/", f"{SITE}/es/blog/vhs-to-digital-wedding-cost/"),
    ("/fr/blog/02-vhs-to-digital-wedding-cost/", f"{SITE}/fr/blog/vhs-to-digital-wedding-cost/"),
    ("/de/blog/02-vhs-to-digital-wedding-cost/", f"{SITE}/de/blog/vhs-to-digital-wedding-cost/"),
    ("/pt/blog/02-vhs-to-digital-wedding-cost/", f"{SITE}/pt/blog/vhs-to-digital-wedding-cost/"),
    ("/ja/blog/02-vhs-to-digital-wedding-cost/", f"{SITE}/ja/blog/vhs-to-digital-wedding-cost/"),
    ("/ru/blog/02-vhs-to-digital-wedding-cost/", f"{SITE}/ru/blog/vhs-to-digital-wedding-cost/"),
]


def probe(url: str, max_redirects: int = 0) -> tuple[int, str, str]:
    """Return (status, location, error)."""
    try:
        r = subprocess.run(
            ["curl.exe", "-s", "-o", "NUL", "-D", "-",
             "-w", "%{http_code}", "--max-redirs", str(max_redirects), url],
            capture_output=True, text=True, timeout=15,
        )
        out = r.stdout
        # split headers from body (last line is the status)
        lines = out.strip().splitlines()
        if not lines:
            return 0, "", "empty response"
        status_line = lines[-1].strip()
        try:
            status = int(status_line)
        except ValueError:
            return 0, "", f"bad status: {status_line!r}"
        loc = ""
        for ln in lines[:-1]:
            if ln.lower().startswith("location:"):
                loc = ln.split(":", 1)[1].strip()
                break
        return status, loc, ""
    except subprocess.TimeoutExpired:
        return 0, "", "timeout"
    except FileNotFoundError:
        return 0, "", "curl.exe not found"
    except Exception as e:
        return 0, "", str(e)


def main():
    all_urls = [(u, 200) for u in EN_TOP + I18N + SERVICE] + [(u, 301) for u, _ in SAMPLE_301s]
    # map expected 301 -> expected Location
    expected_301 = {u: loc for u, loc in SAMPLE_301s}

    results = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(probe, SITE + u, 0): (u, exp) for u, exp in all_urls}
        for fut in as_completed(futs):
            url, exp = futs[fut]
            try:
                status, loc, err = fut.result()
            except Exception as e:
                status, loc, err = 0, "", str(e)
            results.append((url, exp, status, loc, err))

    # sort by expected, then URL
    results.sort(key=lambda r: (r[1], r[0]))

    ok = 0
    fail = 0
    for url, exp, status, loc, err in results:
        if err:
            mark = "ERR "
            fail += 1
        elif exp == 200 and status == 200:
            mark = "OK  "
            ok += 1
        elif exp == 301 and status in (301, 308):
            # CF Pages sometimes returns relative Location ("/blog/...") and
            # sometimes absolute ("https://weddingai.video/blog/..."). Compare
            # on the path component only, not the full URL.
            exp_loc = expected_301.get(url, "")
            exp_path = urlparse(exp_loc).path
            loc_path = urlparse(loc).path if loc.startswith("http") else loc
            if exp_loc and exp_path != loc_path:
                mark = "LOC "
                fail += 1
            else:
                mark = "OK  "
                ok += 1
        else:
            mark = "FAIL"
            fail += 1
        print(f"  {mark}  {status:>3}  exp={exp}  {url}  ->  {loc or err}")

    total = ok + fail
    print(f"\n{ok}/{total} probes passed.")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
