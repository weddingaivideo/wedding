"""Find U+0001 occurrences and show their context."""
from pathlib import Path
ROOT = Path(".")
for f in sorted(ROOT.rglob("*.html")):
    text = f.read_text(encoding="utf-8")
    if "\x01" not in text:
        continue
    # Find all positions
    positions = []
    start = 0
    while True:
        i = text.find("\x01", start)
        if i < 0:
            break
        positions.append(i)
        start = i + 1
    for i in positions[:3]:
        s = max(0, i - 60)
        e = min(len(text), i + 60)
        snippet = text[s:e].replace("\x01", "<U+0001>")
        print(f"{f.name} @ {i}: {snippet}")
    if len(positions) > 3:
        print(f"  ... +{len(positions) - 3} more in {f.name}")
