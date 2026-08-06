import re
for slug in ["11-unique-wedding-video-ideas", "26-wedding-anniversary-video-ideas"]:
    text = open(f"blog/{slug}/index.html", encoding="utf-8").read()
    m = re.search(r"<img[^>]+>", text)
    if m:
        print(f"=== {slug} ===")
        print(f"  first img: {m.group(0)[:200]}")
        a = re.search(r'alt="([^"]+)"', m.group(0))
        if a:
            print(f"  alt: {a.group(1)}")
