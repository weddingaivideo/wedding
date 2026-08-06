"""End-to-end sanity check after the blog + nav fix."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
print("=== Sanity Check ===\n")

# 1. index.html critical-css fix
text = (ROOT / "index.html").read_text(encoding="utf-8")
m = re.search(r'<style id="critical-css">([^<]+)</style>', text)
if m:
    css = m.group(1)
    has_main_nav_block = ".main-nav{display:block}" in css
    has_nav_list_flex = "nav-list{display:flex" in css
    has_mobile_media = "@media (max-width:768px){.main-nav{display:none" in css
    has_one_media = css.count("@media") == 1
    print(f"[{'OK' if has_main_nav_block else 'FAIL'}] critical: .main-nav{{display:block}}")
    print(f"[{'OK' if has_nav_list_flex else 'FAIL'}] critical: .nav-list display:flex")
    print(f"[{'OK' if has_mobile_media else 'FAIL'}] critical: mobile @media present")
    print(f"[{'OK' if has_one_media else 'FAIL'}] critical: 1 @media (got {css.count('@media')})")

print()
top_pages = [
    "index.html",
    "about.html",
    "gallery.html",
    "order.html",
    "services/index.html",
    "blog/index.html",
    "privacy.html",
]
for p in top_pages:
    f = ROOT / p
    if not f.exists():
        print(f"[SKIP] {p} not found")
        continue
    text = f.read_text(encoding="utf-8")
    has_blog = 'href="/blog/"' in text
    print(f"[{'OK' if has_blog else 'FAIL'}] {p}: Blog link in nav")

print()
bl = (ROOT / "blog" / "index.html").read_text(encoding="utf-8")
n_articles = bl.count('class="case-card"')
print(f"[{'OK' if n_articles == 50 else 'FAIL'}] blog list: {n_articles} article cards (expected 50)")

sample = (ROOT / "blog" / "01-restore-old-wedding-videos" / "index.html").read_text(encoding="utf-8")
has_h1 = "<h1>" in sample
has_blog_link = "/blog/" in sample
print(f"[{'OK' if has_h1 else 'FAIL'}] sample article: h1 present")
print(f"[{'OK' if has_blog_link else 'FAIL'}] sample article: /blog/ internal link")

red = (ROOT / "_redirects").read_text(encoding="utf-8")
print(f"[{'OK' if '/blog.html' in red else 'FAIL'}] _redirects: /blog.html entry")

sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
n_blog_urls = sm.count("weddingai.video/blog")
print(f"[{'OK' if n_blog_urls == 51 else 'FAIL'}] sitemap: {n_blog_urls} blog URLs (expected 51)")

mc = (ROOT / "styles.min.css").read_text(encoding="utf-8")
has_blog_css = ".blog-article" in mc
print(f"[{'OK' if has_blog_css else 'FAIL'}] styles.min.css: .blog-article rules")

cb = re.findall(r"styles\.min\.css\?v=([\d.]+)", text)
print(f"[INFO] index.html cache buster: v={cb[0] if cb else 'n/a'}")

print()
print("=== Done ===")
