"""Debug: show which pattern matches each primary_keyword."""
import json
import re
import sys
from pathlib import Path

# Load the expansions list — same logic as in design-blog-image-prompts.py
sys.path.insert(0, "scripts")
from design_blog_image_prompts import slug_topic_to_visual, parse_fm

# But parse_fm uses inline impl; simpler to copy it:
def parse_fm(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = text[3:end].strip()
    meta = {}
    for line in fm.splitlines():
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            meta[key] = [s.strip().strip('"').strip("'") for s in inner.split(",") if s.strip()]
        else:
            meta[key] = val
    return meta

ARTICLES = Path("articles")
for md in sorted(ARTICLES.glob("*.md"))[:5]:
    text = md.read_text(encoding="utf-8")
    meta = parse_fm(text)
    kw = meta.get("primary_keyword", "")
    # Just use the visible prompt
    vis = slug_topic_to_visual(kw)
    print(f"{md.stem:50s} kw={kw:50s}")
    print(f"   {vis[:100]}")
