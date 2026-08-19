"""Verify hi-IN deploy: poll /hi/, /hi/blog/, /i18n/hi.json until 200 + Devanagari."""
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
URLS = [
    ('https://weddingai.video/hi/', 'home'),
    ('https://weddingai.video/hi/blog/', 'blog index'),
    ('https://weddingai.video/hi/blog/affordable-wedding-video-ai/', 'blog post'),
    ('https://weddingai.video/i18n/hi.json', 'i18n json'),
    ('https://weddingai.video/sitemap-hi.xml', 'sitemap-hi'),
    ('https://weddingai.video/robots.txt', 'robots'),
]


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 verify'})
    return urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', errors='replace')


def main():
    print(f"Polling CF Pages deploy for hi-IN... (max 5 min)")
    start = time.time()
    last_err = None
    while time.time() - start < 300:
        all_ok = True
        results = []
        for url, name in URLS:
            try:
                body = fetch(url, timeout=10)
                # Sanity checks
                if 'hi.json' in url:
                    ok = '"_meta.lang"' in body
                    detail = f'{len(body):,} bytes'
                elif 'sitemap' in url:
                    hi_count = len(re.findall(r'hreflang="hi"', body))
                    ok = hi_count > 50
                    detail = f'{hi_count} hi hreflangs'
                elif 'robots' in url:
                    ok = 'sitemap-hi.xml' in body
                    detail = 'sitemap-hi.xml line present'
                else:
                    devanagari = len(re.findall(r'[\u0900-\u097F]', body))
                    ok = devanagari > 50
                    detail = f'{devanagari} Devanagari chars'
                results.append((name, 'OK' if ok else 'FAIL', detail))
                if not ok:
                    all_ok = False
            except urllib.error.HTTPError as e:
                results.append((name, f'HTTP {e.code}', str(e)[:50]))
                all_ok = False
            except Exception as e:
                results.append((name, 'ERR', str(e)[:50]))
                all_ok = False
                last_err = str(e)
        elapsed = time.time() - start
        print(f'\n--- t+{elapsed:.0f}s ---')
        for name, status, detail in results:
            mark = '✓' if status == 'OK' else '✗'
            print(f'  {mark} {name:14s} {status:6s} {detail}')
        if all_ok:
            print(f'\nAll checks passed at t+{elapsed:.0f}s')
            return 0
        time.sleep(15)
    print(f'\nTimed out after 5 min. Last error: {last_err}')
    return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
