from pathlib import Path
files = [
    "blog/weddingai-video-guide/index.html",
    "blog/affordable-wedding-video-ai/index.html",
    "sitemap.xml",
    "sitemap-en.xml",
    "qa/gen_sitemap.py",
    "scripts/inject-blog-breadcrumb.py",
    "scripts/generate-blog.py",
    "scripts/patch-sitemaps.py",
]
for f in files:
    p = Path(f)
    b = p.read_bytes()
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n")
    cr_only = b.count(b"\r") - crlf
    print(f"{f}: size={len(b):>6}  CRLF={crlf:>4}  LF-only={lf-crlf:>4}  CR-only={cr_only}")
