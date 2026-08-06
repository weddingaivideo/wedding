import urllib.request
import re
url = 'https://weddingai.video/blog/01-restore-old-wedding-videos/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as r:
    html = r.read().decode('utf-8', errors='ignore')
m = re.search(r'<section class="page-hero[^"]*">.*?</section>', html, re.DOTALL)
print(m.group(0)[:900] if m else 'NOT FOUND')
