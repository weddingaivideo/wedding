import re
for slug in ["11-unique-wedding-video-ideas", "26-wedding-anniversary-video-ideas"]:
    text = open(f"blog/{slug}/index.html", encoding="utf-8").read()
    print(f"=== {slug} ===")
    for m in re.finditer(r"<img[^>]+>", text):
        a = re.search(r'alt="([^"]+)"', m.group(0))
        if a and (len(a.group(1)) < 10 or a.group(1).lower() in ("image", "img", "photo", "picture", "wedding")):
            print(f"  weak: {a.group(1)}")
