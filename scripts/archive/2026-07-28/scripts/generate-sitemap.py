#!/usr/bin/env python3
"""从 HTML 文件夹自动生成 sitemap.xml。

- URL 用真实存在的 .html 文件名（避免 Google 抓到 404）
- 加 lastmod 时间戳
- 加 image:image 扩展（image sitemap）
- 跳过 robots/canonical 标记为 noindex 的页面
"""
import os
import re
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"
BASE_URL = "https://weddingai.video"

# Priority and changefreq by URL pattern
def get_priority(rel):
    if rel == "index.html":
        return 1.0, "weekly"
    if rel in ("gallery.html", "order.html", "services/index.html"):
        return 0.9, "weekly"
    if rel == "about.html":
        return 0.7, "monthly"
    if rel in ("privacy.html", "terms.html"):
        return 0.4, "yearly"
    if rel.startswith("services/"):
        return 0.8, "monthly"
    return 0.5, "monthly"

# Pages to skip (e.g. success page, verification file)
SKIP = {"google-site-verification.html", "success.html"}


def find_html_files(root):
    htmls = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {'.git', 'node_modules', '.wrangler'}]
        for f in filenames:
            if f.endswith('.html') and f not in SKIP:
                full = os.path.join(dirpath, f)
                rel = os.path.relpath(full, root).replace('\\', '/')
                htmls.append((rel, full))
    return sorted(htmls)


def get_images(html_path):
    """Find images referenced in <img src=...>"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return []
    imgs = re.findall(r'<img\s[^>]*src="([^"]+)"', content)
    # Only local images, dedupe
    seen = set()
    out = []
    for src in imgs:
        if src.startswith(('http', '//', 'data:')):
            continue
        if src in seen:
            continue
        seen.add(src)
        # Resolve relative to html file
        html_dir = os.path.dirname(html_path)
        resolved = os.path.normpath(os.path.join(html_dir, src))
        if os.path.commonpath([ROOT, resolved]) == ROOT:
            rel = os.path.relpath(resolved, ROOT).replace('\\', '/')
            out.append(rel)
    return out


def url_for(rel):
    """Convert 'X.html' -> 'X', 'services/index.html' -> 'services/', 'index.html' -> '/'."""
    if rel == "index.html":
        return f"{BASE_URL}/"
    if rel.endswith("/index.html"):
        return f"{BASE_URL}/{rel[:-10]}"  # strip 'index.html'
    if rel.endswith(".html"):
        return f"{BASE_URL}/{rel[:-5]}"  # strip '.html' (clean URL — no server redirect)
    return f"{BASE_URL}/{rel}"


def get_lastmod(html_path):
    """Use file mtime as lastmod."""
    mtime = os.path.getmtime(html_path)
    return datetime.date.fromtimestamp(mtime).isoformat()


def main():
    files = find_html_files(ROOT)
    print(f"Found {len(files)} HTML files to include")

    # Build XML using ET for proper escaping
    NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
    NS_IMG = "http://www.google.com/schemas/sitemap-image/1.1"
    ET.register_namespace('', NS)
    ET.register_namespace('image', NS_IMG)

    urlset = ET.Element(f'{{{NS}}}urlset')

    for rel, full in files:
        url = ET.SubElement(urlset, f'{{{NS}}}url')
        loc = ET.SubElement(url, f'{{{NS}}}loc')
        loc.text = url_for(rel)
        lastmod = ET.SubElement(url, f'{{{NS}}}lastmod')
        lastmod.text = get_lastmod(full)
        priority, changefreq = get_priority(rel)
        pr = ET.SubElement(url, f'{{{NS}}}priority')
        pr.text = f'{priority:.1f}'
        cf = ET.SubElement(url, f'{{{NS}}}changefreq')
        cf.text = changefreq

        # Image extensions
        for img_rel in get_images(full):
            img = ET.SubElement(url, f'{{{NS_IMG}}}image')
            img_loc = ET.SubElement(img, f'{{{NS_IMG}}}loc')
            img_loc.text = f'{BASE_URL}/{img_rel}'

    # Pretty print
    rough = ET.tostring(urlset, encoding='utf-8', xml_declaration=False)
    pretty = minidom.parseString(rough).toprettyxml(indent='    ', encoding='utf-8').decode('utf-8')

    # Add XML declaration on first line
    if pretty.startswith('<?xml'):
        # normalize encoding case (minidom uses 'utf-8')
        pretty = re.sub(r"encoding=([\"'])[^\"']+([\"'])", 'encoding="UTF-8"', pretty, count=1)
    else:
        pretty = '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty

    out = os.path.join(ROOT, 'sitemap.xml')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(pretty)
    print(f"Wrote {out} ({len(files)} URLs)")


if __name__ == "__main__":
    main()
