import re
for slug in ["11-unique-wedding-video-ideas", "26-wedding-anniversary-video-ideas"]:
    text = open(f"blog/{slug}/index.html", encoding="utf-8").read()
    print(f"=== {slug} ===")
    for img in re.finditer(r"<img[^>]+>", text):
        attrs = img.group(0)
        m = re.search(r'alt="([^"]*)"', attrs)
        if m:
            alt = m.group(1)
            if len(alt) < 10 or alt in ("image", "img", "photo", "picture", "wedding"):
                print(f"  weak alt: {alt!r}")
                print(f"    tag: {attrs[:200]}")
