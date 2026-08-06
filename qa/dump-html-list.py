"""Debug: list all .html files that all_html() would return."""
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
import gen_llms

files = gen_llms.all_html()
print(f"Total: {len(files)}")
for p in files[:20]:
    rel = p.relative_to(gen_llms.ROOT)
    print(f"  {rel}")
print("...")
for p in files[-5:]:
    rel = p.relative_to(gen_llms.ROOT)
    print(f"  {rel}")
