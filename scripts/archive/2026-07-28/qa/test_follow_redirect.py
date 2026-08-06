import urllib.request

opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
req = urllib.request.Request('https://3f615e80.weddingai-video.pages.dev/about/')
req.add_header('User-Agent', 'Mozilla/5.0')
req.add_header('Accept-Language', 'ja,en;q=0.5')
r = opener.open(req, timeout=10)
print('Final URL:', r.url)
print('Status:', r.status)
body = r.read().decode('utf-8', errors='ignore')
# Extract lang
lang = '?'
if '<html lang="' in body:
    lang = body.split('<html lang="')[1].split('"')[0]
# Extract canonical
canon = '?'
if 'rel="canonical" href="' in body:
    canon = body.split('rel="canonical" href="')[1].split('"')[0]
print('lang:', lang)
print('canonical:', canon)
print('Content sample (h1):', body.split('</head>')[0][-200:] if '</head>' in body else '?')
