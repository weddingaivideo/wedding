"""Verify the QA fix results on production."""
import urllib.request
import re

UA = {"User-Agent": "Mozilla/5.0 (WeddingAI-QA/2.0)"}

PAGES = [
    ("https://weddingai.video/", "homepage"),
    ("https://weddingai.video/about/", "about"),
    ("https://weddingai.video/blog/", "blog index"),
    ("https://weddingai.video/blog/01-restore-old-wedding-videos/", "blog 01"),
    ("https://weddingai.video/services/personalization/ai-video-generator/", "AI service"),
    ("https://weddingai.video/order/", "order form"),
    ("https://weddingai.video/404/", "404"),
]

print("=== Production QA smoke test ===\n")
for url, name in PAGES:
    req = urllib.request.Request(url, headers=UA)
    content = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")
    has_open = "OPEN" in content
    has_lost_lt = bool(re.search(r"<[a-z][a-z]+<[a-z]", content))  # <tag<tag pattern
    has_unmatched_li = content.count("<li") - content.count("</li>")  # diff
    has_mobile = '<button class="mobile-menu-toggle"' in content
    has_lang = 'id="wa-lang-select"' in content

    print(f"  {name}: {url}")
    print(f"    OPEN strings:  {'❌' if has_open else '✅ clean'}")
    print(f"    <tag<tag:     {'❌' if has_lost_lt else '✅ clean'}")
    print(f"    <li></li> diff: {has_unmatched_li} {'❌' if has_unmatched_li else '✅'}")
    print(f"    mobile btn:   {'✅' if has_mobile else '❌ missing'}")
    print(f"    lang switch:  {'✅' if has_lang else '❌ missing'}")
    print()
