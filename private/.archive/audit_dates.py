import re
from pathlib import Path
from collections import Counter

counts = Counter()
for p in sorted(Path("blog").glob("*/index.html")):
    if p.parent.name == "blog":
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})"', text)
    if m:
        counts[m.group(1)] += 1
    else:
        counts["(none)"] += 1

print(f"Total: {sum(counts.values())}")
print(f"Distinct datePublished values: {len([c for c in counts if c != '(none)'])}")
print()
print("Distribution by month:")
month_counts = Counter()
for d, c in counts.items():
    if d == "(none)":
        continue
    month = d[:7]
    month_counts[month] += c
for month, c in sorted(month_counts.items()):
    print(f"  {month}: {c}")
