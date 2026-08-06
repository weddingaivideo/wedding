import re

text = open("blog/01-restore-old-wedding-videos/index.html", encoding="utf-8").read()
# Find all blog-article
for m in re.finditer(r'class="blog-article"', text):
    print("found at:", m.start())
# Find first <h1>
m = re.search(r'<h1>', text)
print("first <h1> at:", m.start() if m else "NO")
# Show 50 chars before
if m:
    print("context:", text[max(0, m.start()-80):m.end()+50])
