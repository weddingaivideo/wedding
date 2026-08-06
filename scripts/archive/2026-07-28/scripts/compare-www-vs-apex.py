"""Compare the homepage served on www vs apex to see if there's any difference
that could explain Google's 'not evaluated' report for the www version."""
import re
import urllib.request

for url in ['https://weddingai.video/', 'https://www.weddingai.video/']:
    print(f"==== {url} ====")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'})
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
    try:
        with opener.open(req, timeout=15) as r:
            print(f"  final URL: {r.geturl()}")
            print(f"  status: {r.status}")
            print(f"  content-type: {r.headers.get('Content-Type')}")
            # Check critical headers
            print(f"  HSTS: {r.headers.get('Strict-Transport-Security')}")
            print(f"  CSP: {bool(r.headers.get('Content-Security-Policy'))}")
            # Read first 4KB and look for any HTTP (non-HTTPS) references
            html = r.read(8192).decode('utf-8', errors='ignore')
            # Find http:// references
            http_refs = re.findall(r'(?:href|src)=["\']http://[^"\']+', html)
            print(f"  http:// refs in first 8KB: {len(http_refs)}")
            for h in http_refs[:3]:
                print(f"    {h[:100]}")
            # Canonical
            can = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', html)
            print(f"  canonical: {can.group(1) if can else 'NONE'}")
    except Exception as e:
        print(f"  ERR: {e}")
    print()
