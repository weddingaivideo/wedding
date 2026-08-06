import urllib.request
import re
from collections import Counter
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
req = urllib.request.Request('https://3608bf61.weddingai-video.pages.dev/sitemap.xml', headers={'User-Agent': UA})
r = urllib.request.urlopen(req, timeout=10)
body = r.read().decode('utf-8', errors='ignore')
locs = re.findall(r'<loc>([^<]+)</loc>', body)
lastmods = re.findall(r'<lastmod>([^<]+)</lastmod>', body)
alts = re.findall(r'xhtml:link', body)
print(f'Sitemap stats:')
print(f'  Total URLs: {len(locs)}')
print(f'  Lastmod values: {set(lastmods)}')
print(f'  hreflang alternate count: {len(alts)} (expected {len(locs) * 11})')
# Sample first URL entry
print(f'First URL entry:')
m = re.search(r'<url>[\s\S]*?</url>', body)
if m:
    print(m.group(0)[:1500])
