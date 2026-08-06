"""Fix blog/index.html h1->h3 skip by inserting a parent h2 before the article grid."""
from pathlib import Path

p = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai\blog\index.html")
text = p.read_text(encoding="utf-8")

# Find the cases-grid section and the closing > of the container div that wraps it
grid_idx = text.find('class="cases-grid"')
assert grid_idx > 0, "cases-grid not found"
# Walk back to find the opening of the container div wrapping it
container_open = text.rfind('<div class="container">', 0, grid_idx)
assert container_open > 0, "container not found"
container_close = text.find('>', container_open) + 1

# Insert a small h2 right after the container opens
h2_html = '\n                <h2 style="text-align: center; font-size: 1.5rem; margin-top: 0; margin-bottom: 1.5rem;">All Wedding Video Guides &amp; Tips</h2>\n'
new_text = text[:container_close] + h2_html + text[container_close:]

if new_text == text:
    raise SystemExit("no change made")

p.write_text(new_text, encoding="utf-8")
print(f"OK: inserted h2 in blog/index.html at L{container_close}")
