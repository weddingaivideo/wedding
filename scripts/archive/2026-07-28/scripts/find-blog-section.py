text = open(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai\blog\index.html', encoding='utf-8').read()
for needle in ['Article archive', 'case-grid', 'article-grid', 'class="section', 'class="container', 'class="case-']:
    idx = text.find(needle)
    if idx != -1:
        ctx = text[max(0, idx-100):idx+200]
        print(f'Found {needle!r} at L{idx}')
        print(f'  context: {ctx}')
        print()
