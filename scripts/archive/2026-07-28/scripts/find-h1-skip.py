"""Find h1->h3 skips and show context."""
import re
from pathlib import Path
for f in ["index.html", "order.html", "family-tribute.html"]:
    text = Path(f).read_text(encoding="utf-8")
    print(f"=== {f} ===")
    # All headings in order
    for m in re.finditer(r"<(h[1-6])\b[^>]*>(.*?)</\1>", text, re.DOTALL):
        level = int(m.group(1)[1])
        txt = re.sub(r"<[^>]+>", "", m.group(2)).strip()[:60]
        print(f"  pos={m.start()} h{level}: {txt}")
