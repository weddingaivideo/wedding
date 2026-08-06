"""Fix family-tribute.html and family-tribute/index.html: h1->h3 skip.

'A Note on Sensitivity' is currently h3 directly under h1.
Promote to h2 — it's a section-level callout, not a sub-sub-heading.
"""
from pathlib import Path

OLD = '<h3>A Note on Sensitivity</h3>'
NEW = '<h2>A Note on Sensitivity</h2>'

for rel in [r'C:\Users\qiaoshan\.openclaw\workspace\weddingai\services\absence-compensation\family-tribute.html',
            r'C:\Users\qiaoshan\.openclaw\workspace\weddingai\services\absence-compensation\family-tribute\index.html']:
    p = Path(rel)
    text = p.read_text(encoding='utf-8')
    if OLD not in text:
        print(f"  MISS in {p.name}")
        continue
    text = text.replace(OLD, NEW, 1)
    p.write_text(text, encoding='utf-8')
    print(f"OK: {p.name}")
