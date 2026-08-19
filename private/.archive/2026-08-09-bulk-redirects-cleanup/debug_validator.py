"""Debug the validator — figure out why it reports 24 missing assets when they're on disk."""
import re
import io
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
HTML_PATH = ROOT / "gallery" / "index.html"
with io.open(HTML_PATH, "r", encoding="utf-8") as f:
    HTML = f.read()

# Test the source regex from the validator
sources = re.findall(r'<source\s[^>]*src="([^"]+)"', HTML)
print(f"Total <source src> matches: {len(sources)}")
ahmed = [s for s in sources if "ahmed" in s]
print(f"ahmed sources: {len(ahmed)}")
for s in ahmed:
    print(f"  {s}")
print()

# Try the same file existence check as the validator
for s in ahmed:
    rel = s.split("?", 1)[0].split("#", 1)[0].lstrip("/")
    fp = ROOT / rel
    print(f"  exists={fp.exists()!s:>5}  fp={fp}")
print()

# Now run the EXACT validator logic on the all_refs
all_refs = set()
for m in re.findall(r'<img\s[^>]*src="([^"]+)"', HTML):
    all_refs.add(m)
for m in re.findall(r'<source\s[^>]*src="([^"]+)"', HTML):
    all_refs.add(m)
for m in re.findall(r'<video\s[^>]*poster="([^"]+)"', HTML):
    all_refs.add(m)
for m in re.findall(r'srcset="([^"]+)"', HTML):
    for part in m.split(","):
        url = part.strip().split()[0]
        if url:
            all_refs.add(url)

print(f"Total all_refs: {len(all_refs)}")
missing = []
for url in sorted(all_refs):
    if not url.startswith("/images/"):
        continue
    rel = url.split("?", 1)[0].split("#", 1)[0].lstrip("/")
    fp = ROOT / rel
    if not fp.exists():
        missing.append(url)

print(f"Missing: {len(missing)}")
for m in missing[:5]:
    rel = m.split("?", 1)[0].split("#", 1)[0].lstrip("/")
    fp = ROOT / rel
    print(f"  {m} -> {fp}  exists={fp.exists()}")
