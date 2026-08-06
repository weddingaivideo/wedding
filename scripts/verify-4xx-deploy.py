"""Verify the 31 originally-4xx URLs after deploy. Reuses the user's request list."""
import urllib.request
import urllib.error
import time

URLS = [
    "services/video-enhancement/vintage-restoration/gallery/",
    "services/video-enhancement/vintage-restoration/about/",
    "diy-wedding-video-phone.md",
    "wedding-video-cost-2026-new/",
    "weddingai-video-guide/",
    "make-first-ai-wedding-video/",
    "wedding-video-music-guide-new/",
    "blog/wedding-video-under-500/",
    "wedding-highlight-video.md",
    "couple-slideshow-video.md",
    "services/personalization/wedding-invitation/",
    "wedding-video-trends-2026.md",
    "ai-tools-for-photographers.md",
    "photographer-upsell-video.md",
    "weddingai-video-case-studies",
    "ai-wont-replace-photographers.md",
    "wedding-slideshow-guide.md",
    "blog/destination-wedding-video-guide/",
    "ai-editor-vs-traditional-editing/",
    "how-to-make-wedding-video",
    "wedding-video-captions",
    "wedding-video-music-guide-new",
    "weddingai-video-case-studies/",
    "services/video-enhancement/",
    "bride-wedding-video-checklist.md",
    "destination-wedding-video-guide.md",
    "wedding-video-without-videographer.md",
    "small-wedding-video-ideas.md",
    "wedding-package-video-upsell.md",
    "wedding-video-photo-checklist",
    "services/personalization/",
]


def head(url: str):
    """HEAD request, return (status, location) tuple."""
    req = urllib.request.Request(url, method="HEAD")
    # Use a real Chrome UA — Cloudflare's default-bot-protection returns 403
    # for python-urllib's default "Python-urllib/3.x" UA. (Screaming Frog has
    # the same issue; the fix there is the same: switch UA to Chrome.)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    try:
        resp = urllib.request.urlopen(req, timeout=12)
        return resp.status, resp.headers.get("Location", "")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location", "") if e.headers else ""
    except Exception as e:
        return "ERR", str(e)[:60]


def main():
    rows = []
    for u in URLS:
        full = f"https://weddingai.video/{u}"
        status, loc = head(full)
        rows.append((u, status, loc))
        time.sleep(0.15)
    counts = {"200": 0, "301": 0, "308": 0, "404": 0, "ERR": 0, "other": 0}
    for _, st, _ in rows:
        s = str(st)
        if s in counts:
            counts[s] += 1
        else:
            counts["other"] += 1
    print()
    print(f"=== 200={counts['200']}  301={counts['301']}  308={counts['308']}  "
          f"404={counts['404']}  ERR={counts['ERR']}  other={counts['other']}  "
          f"(of {len(rows)}) ===")
    print()
    maxlen = max(len(u) for u, _, _ in rows)
    for u, st, loc in rows:
        # Truncate long locations
        if loc and len(loc) > 60:
            loc = loc[:57] + "..."
        print(f"  {st:>4}  {u:<{maxlen}}  {loc}")


if __name__ == "__main__":
    main()
