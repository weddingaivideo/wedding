"""Test that article dates are diversified per URL."""
import os
import json
import re
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
exec((ROOT / "qa" / "test_middleware_regex.py").read_text(encoding="utf-8").split("# --- Tests ---")[0])

# Re-define the diversify function (it's not in the test file)
def diversifyArticleDates(html, requestUrl):
    ANCHOR_DATE_MS = (2026 - 1970) * 365.25 * 86400  # rough
    # Use the actual anchor: Date.UTC(2026, 6, 23)
    from datetime import datetime, timezone
    anchor = datetime(2026, 6, 23, tzinfo=timezone.utc).timestamp() * 1000
    WINDOW_DAYS = 60
    MAX_OFFSET_DAYS = 45
    path = requestUrl.split("://", 1)[-1].split("/", 1)[-1] if "://" in requestUrl else requestUrl
    path = "/" + path
    h = 0
    for c in path:
        h = (h * 31 + ord(c)) & 0x7FFFFFFF
    seed = h % 1000
    offsetDays = (seed / 1000) * MAX_OFFSET_DAYS
    newDate = datetime.fromtimestamp((anchor + offsetDays * 86400000) / 1000, tz=timezone.utc)
    newDateStr = newDate.strftime("%Y-%m-%d")
    modOffset = 1 + (abs(h * 7) % 3)
    newModDate = datetime.fromtimestamp((anchor + (offsetDays + modOffset) * 86400000) / 1000, tz=timezone.utc)
    newModDateStr = newModDate.strftime("%Y-%m-%d")

    def repl(m):
        body = m.group(1)
        try:
            obj = json.loads(body)
            if not obj or obj.get("@type") != "Article":
                return m.group(0)
            changed = False
            if obj.get("datePublished") and re.match(r"^\d{4}-\d{2}-\d{2}$", str(obj["datePublished"])):
                obj["datePublished"] = newDateStr
                changed = True
            if obj.get("dateModified") and re.match(r"^\d{4}-\d{2}-\d{2}$", str(obj["dateModified"])):
                obj["dateModified"] = newModDateStr
                changed = True
            if not changed:
                return m.group(0)
            return m.group(0).replace(body, json.dumps(obj, separators=(",", ":")))
        except Exception:
            return m.group(0)
    return re.sub(r'<script\s+type="application/ld\+json"[^>]*>([\s\S]*?)</script>', repl, html, flags=re.I)


# Test on a few blog posts
posts = [
    ROOT / "blog" / "ai-wedding-video-generator-guide" / "index.html",
    ROOT / "blog" / "vhs-to-digital-wedding-cost" / "index.html",
    ROOT / "blog" / "wedding-memes" / "index.html",
    ROOT / "blog" / "weddingai-success-stories" / "index.html",
]

for post in posts:
    if not post.exists():
        continue
    html = post.read_text(encoding="utf-8")
    url = "https://weddingai.video" + str(post.relative_to(ROOT)).replace("\\", "/").replace("/index.html", "/")
    out = diversifyArticleDates(html, url)
    # Find Article schema
    m = re.search(r'<script[^>]+ld\+json[^>]*>([\s\S]*?)</script>', out)
    if m:
        try:
            obj = json.loads(m.group(1))
            if obj.get("@type") == "Article":
                rel = post.relative_to(ROOT)
                print(f"{rel}:")
                print(f"  datePublished: {obj.get('datePublished')}")
                print(f"  dateModified: {obj.get('dateModified')}")
        except Exception:
            pass
