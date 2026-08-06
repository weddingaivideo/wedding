import re
text = open("blog/01-restore-old-wedding-videos/index.html", encoding="utf-8").read()
matches = re.findall(r"<picture.*?</picture>", text, re.DOTALL)
print(f"Total picture count: {len(matches)}")
for i, m in enumerate(matches, 1):
    print(f"\n--- {i} ---")
    print(m[:500])
