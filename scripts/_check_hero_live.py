"""Check if the LIVE homepage still has the relative srcset path."""
import urllib.request
req = urllib.request.Request("https://weddingai.video/", headers={"User-Agent": "Mavis-audit"})
body = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")
print(f"Body length: {len(body):,}")
import re
# Find all hero references
for m in re.finditer(r'[^"\'<>]{0,50}hero-wedding-vineyard[^"\'<>]{0,80}', body):
    print("  ", repr(m.group(0)[:130]))
print("---")
REL = 'srcset="hero-wedding-vineyard'
ABS = 'srcset="/images/hero-wedding-vineyard'
print(f"Relative srcset hits: {body.count(REL)}")
print(f"Absolute srcset hits: {body.count(ABS)}")
print(f"1600.webp hits: {body.count('hero-wedding-vineyard-1600.webp')}")
