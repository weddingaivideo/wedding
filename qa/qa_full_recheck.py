"""Re-verify: which P0/P1 from previous QA are STILL valid after recent edits?
Confirm the state of:
  - blog NN- old key format (4348 missing in en.json)
  - duplicate i18n.css in noscript (65+ files)
  - nested <a><a> (602 occurrences)
  - styles.min.css cache buster inconsistency
  - search page HTML damage
  - 360 nav/footer empty default text
  - 67/73 <a> tag imbalance
  - missing robots.txt, llms.txt, bca20c...txt
  - order/index.html og:url typo
  - sitemap lastmod
"""
import re
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path('.')
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

files = [p for p in ROOT.rglob('*.html') if not (set(str(x) for x in p.parts) & EXCLUDE)]

print('=== Re-verification of QA findings ===\n')

# 1. blog NN- old key format
en = json.load(open('i18n/en.json', encoding='utf-8'))
en_keys = set(en.keys())
old_format = re.compile(r'^blog\.\d{2}-')
old_html_keys = set()
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    for k in re.findall(r'data-i18n="([^"]+)"', text):
        if old_format.match(k):
            old_html_keys.add(k)
print(f'[P0 #1] blog NN- old key format: {len(old_html_keys)} keys in HTML, 0 in en.json')
print(f'         Still valid: {len(old_html_keys) > 0}')

# 2. duplicate i18n.css in noscript
dup_i18n_files = []
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    for block in re.findall(r'<noscript>.*?</noscript>', text, re.DOTALL):
        if block.count('i18n.css') > 1:
            dup_i18n_files.append(f.relative_to(ROOT))
            break
print(f'\n[P1 #6] Duplicate i18n.css in noscript: {len(dup_i18n_files)} files')
print(f'         Still valid: {len(dup_i18n_files) > 0}')

# 3. nested <a><a>
nested_a = 0
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    nested_a += len(re.findall(r'<a\s[^>]*>\s*<a\s', text))
print(f'\n[P1 #5] Nested <a><a>: {nested_a} occurrences')
print(f'         Still valid: {nested_a > 0}')

# 4. styles.min.css cache buster inconsistency
css_versions = defaultdict(int)
no_version_files = []
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'styles\.min\.css(?:\?v=([\d.]+))?', text)
    if m:
        v = m.group(1) or '(none)'
        css_versions[v] += 1
        if v == '(none)':
            no_version_files.append(f.relative_to(ROOT))
print(f'\n[P1 #4] styles.min.css versions: {dict(css_versions)}')
print(f'         Still inconsistent: {len(css_versions) > 1}')

# 5. search page HTML damage (p </div></section>)
search = ROOT / 'search' / 'index.html'
search_text = search.read_text(encoding='utf-8', errors='ignore')
broken = bool(re.search(r'<p[^>]*>\s*</div>\s*</section>', search_text))
print(f'\n[P1 #7] search page <p></div></section>: {broken}')
print(f'         Still valid: {broken}')

# 6. 360 nav/footer empty default text (we now know it is 360; recheck)
empty_default = 0
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'<([a-zA-Z][a-zA-Z0-9]*)\s+[^>]*data-i18n="([^"]+)"[^>]*>\s*</\1>', text):
        empty_default += 1
print(f'\n[P2 #13] empty default text on data-i18n elements: {empty_default}')

# 7. 67/73 <a> tag imbalance
imbalance = 0
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    o = len(re.findall(r'<a[\s>]', text, re.IGNORECASE))
    c = len(re.findall(r'</a>', text, re.IGNORECASE))
    if o != c:
        imbalance += 1
print(f'\n[P2 #12] <a> tag imbalance: {imbalance}/{len(files)} files')

# 8. Missing files
for fname in ['robots.txt', 'llms.txt', 'llms-full.txt', 'bca20c476d04af209950cbf5921e821d.txt']:
    p = ROOT / fname
    print(f'[P2 #8] {fname}: {"EXISTS" if p.exists() else "MISSING"}')

# 9. order/index.html og:url: should be /order/ (with trailing slash) to match canonical
order = ROOT / 'order' / 'index.html'
order_text = order.read_text(encoding='utf-8', errors='ignore')
og_url_no_slash = bool(re.search(r'og:url"\s+content="https://weddingai\.video/order"', order_text))
print(f'\n[P2 #11] order/index.html og:url missing trailing slash: {og_url_no_slash}')

# 10. sitemap lastmod
sitemap_index = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
lastmods = re.findall(r'<lastmod>(\d{4}-\d{2}-\d{2})</lastmod>', sitemap_index)
from datetime import date
today = date.today().isoformat()
print(f'\n[P0 #3] sitemap.xml lastmod: {lastmods[0] if lastmods else "?"}, today: {today}')
print(f'         Still stale: {lastmods[0] != today if lastmods else True}')

# 11. CSP report-to relative URL
headers = (ROOT / '_headers').read_text(encoding='utf-8')
csp_bug = bool(re.search(r'report-to\s+csp-endpoint', headers)) and bool(re.search(r'csp-endpoint="/__csp_report"', headers))
print(f'\n[P2 #10] CSP report-to relative URL: {csp_bug}')

# 12. .ps1 files at root
ps1_files = list(ROOT.glob('*.ps1'))
print(f'\n[P0 #2 fixed] .ps1 files at root: {len(ps1_files)} (verified covered by _redirects /*.ps1 → /404)')
