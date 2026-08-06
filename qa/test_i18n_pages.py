"""Test that the full pipeline works for blog posts (Article schema)."""
import os
import json
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(ROOT))

# Reuse functions from test_middleware_regex
exec((ROOT / "qa" / "test_middleware_regex.py").read_text(encoding="utf-8").split("# --- Tests ---")[0])

# Test blog post
post = ROOT / "blog" / "ai-wedding-video-generator-guide" / "index.html"
html = post.read_text(encoding="utf-8")
print(f"===== {post.relative_to(ROOT)} =====")

zh_dict = json.loads((ROOT / "i18n" / "zh.json").read_text(encoding="utf-8"))

# Apply full pipeline
out = html
out = setOgLocale(out, "zh")
out = rewriteInLanguage(out, "zh")
out = fixOgUrlTrailingSlash(out)
out = applyDataI18n(out, zh_dict)
out = applyDataI18nAttr(out, zh_dict)

# Check: og:locale
m = re.search(r'<meta\s+property="og:locale"\s+content="([^"]+)"', out)
print(f"  og:locale = {m.group(1) if m else 'NOT FOUND'}")

# Check: <h1>
m = re.search(r'<h1[^>]*>([^<]+)</h1>', out)
print(f"  <h1> = {m.group(1)[:80] if m else 'NOT FOUND'}")

# Check: Article schema inLanguage
m = re.search(r'<script[^>]+ld\+json[^>]*>([\s\S]*?)</script>', out)
if m:
    try:
        obj = json.loads(m.group(1))
        print(f"  Article @type: {obj.get('@type')}")
        print(f"  Article inLanguage: {obj.get('inLanguage')}")
    except Exception as e:
        print(f"  JSON parse failed: {e}")

# Check: meta description
m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', out)
print(f"  meta description = {m.group(1)[:80] if m else 'NOT FOUND'}")

# Check: og:url
m = re.search(r'<meta\s+property="og:url"\s+content="([^"]+)"', out)
print(f"  og:url = {m.group(1) if m else 'NOT FOUND'}")

print()
print("===== Success page (should get noindex) =====")
success = ROOT / "success" / "index.html"
html = success.read_text(encoding="utf-8")
out = addNoindexIfSuccess(html, "/success")
print(f"  has noindex: {'PASS' if 'noindex' in out else 'FAIL'}")
m = re.search(r'<meta\s+name="robots"\s+content="([^"]+)"', out)
print(f"  robots meta: {m.group(1) if m else 'NOT FOUND'}")

print()
print("===== About page (no trailing slash on og:url) =====")
about = ROOT / "about" / "index.html"
html = about.read_text(encoding="utf-8")
out = fixOgUrlTrailingSlash(html)
m = re.search(r'<meta\s+property="og:url"\s+content="([^"]+)"', out)
print(f"  og:url = {m.group(1) if m else 'NOT FOUND'}")
print(f"  trailing slash added: {'PASS' if m and m.group(1).endswith('/') else 'FAIL'}")
