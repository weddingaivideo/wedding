import re
text = open("index.html", encoding="utf-8").read()
headings = [(int(m.group(1)), m.group(2)) for m in re.finditer(r"<h([1-6])[^>]*>(.*?)</h[1-6]>", text, re.DOTALL)]
print(f"count: {len(headings)}")
prev = 0
for level, htext in headings:
    txt = re.sub(r"<[^>]+>", "", htext).strip()[:60]
    skip = ""
    if prev > 0 and level > prev + 1:
        skip = "  <- SKIP"
    print(f"  level={level} text={txt}{skip}")
    prev = level
