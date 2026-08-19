"""Check the slug structure of the 50 'bad batch' posts."""
import re
from pathlib import Path

bad_batch = []
for p in sorted(Path("blog").glob("*/index.html")):
    if p.parent.name == "blog":
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})"', text)
    if m and m.group(1) == "2026-08-01":
        bad_batch.append(p.parent.name)

print(f"Bad batch count: {len(bad_batch)}")
print()
with_prefix = [s for s in bad_batch if re.match(r"^\d+", s)]
without_prefix = [s for s in bad_batch if not re.match(r"^\d+", s)]
print(f"  with numeric prefix: {len(with_prefix)}")
print(f"  without numeric prefix: {len(without_prefix)}")
print()
print("Slugs with prefix (first 15):")
for s in sorted(with_prefix)[:15]:
    print(f"  {s}")
print()
print("Slugs without prefix (first 15):")
for s in sorted(without_prefix)[:15]:
    print(f"  {s}")
