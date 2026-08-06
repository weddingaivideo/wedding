"""Fix order.html and order/index.html: h1->h3 skip.

The 4 feature highlights ('Free, No-Obligation Quote', '24-Hour Response',
'Secure File Transfer', '100% Satisfaction') are currently h3 directly under h1.
Promote them to h2 — they're top-level section headings, and 4 in a row is fine.
"""
from pathlib import Path

H3_TO_H2 = [
    '<h3>Free, No-Obligation Quote</h3>',
    '<h3>24-Hour Response</h3>',
    '<h3>Secure File Transfer</h3>',
    '<h3>100% Satisfaction</h3>',
]

for rel in [r'C:\Users\qiaoshan\.openclaw\workspace\weddingai\order.html',
            r'C:\Users\qiaoshan\.openclaw\workspace\weddingai\order\index.html']:
    p = Path(rel)
    text = p.read_text(encoding='utf-8')
    for h3 in H3_TO_H2:
        h2 = h3.replace('<h3>', '<h2>').replace('</h3>', '</h2>')
        if h3 not in text:
            print(f"  MISS in {p.name}: {h3}")
            continue
        text = text.replace(h3, h2, 1)
    p.write_text(text, encoding='utf-8')
    print(f"OK: {p.name}")
