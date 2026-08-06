text = open(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai\blog\01-restore-old-wedding-videos\index.html', encoding='utf-8').read()
import re
# Show first 100 lines of meaningful content (skip script/style)
m = re.search(r'<body>(.*?)</body>', text, re.DOTALL)
body = m.group(1) if m else text
# Find first <section after header
sects = re.findall(r'<section[^>]*>.*?</section>', body, re.DOTALL)
for i, s in enumerate(sects[:4]):
    print(f'==== section {i} ====')
    print(s[:500])
    print()
