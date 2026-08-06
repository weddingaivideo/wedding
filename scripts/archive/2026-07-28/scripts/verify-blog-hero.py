text = open(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai\blog\01-restore-old-wedding-videos\index.html', encoding='utf-8').read()
import re
m = re.search(r'<section class="page-hero[^"]*">.*?</section>', text, re.DOTALL)
print(m.group(0)[:800] if m else 'NOT FOUND')
