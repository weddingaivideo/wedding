#!/usr/bin/env python3
"""在所有 HTML 页面 <head> 中插入 Google AdSense 自动广告脚本。
插入位置：紧跟 GA4 gtag config 脚本之后。
"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# AdSense auto-ads code
ADSENSE_SCRIPT = '''    <!-- Google AdSense (auto ads) -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1670381960525419"
         crossorigin="anonymous"></script>'''

# Anchor: end of GA4 gtag config block
# Pattern matches: gtag('config', 'G-4FE7KSJDNB');\n    </script>
GA4_END_PATTERN = re.compile(
    r"(gtag\('config',\s*'G-4FE7KSJDNB'\s*\);[\s\n]*</script>)",
    re.MULTILINE
)

# Idempotency check
ADSENSE_ALREADY = re.compile(r"ca-pub-1670381960525419")


def find_html_files(root):
    htmls = []
    for dirpath, dirnames, filenames in os.walk(root):
        # skip node_modules, .git, etc
        dirnames[:] = [d for d in dirnames if d not in {'.git', 'node_modules', '.wrangler'}]
        for f in filenames:
            if f.endswith('.html'):
                htmls.append(os.path.join(dirpath, f))
    return sorted(htmls)


def process(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Skip if already added
    if ADSENSE_ALREADY.search(content):
        return "already"

    m = GA4_END_PATTERN.search(content)
    if not m:
        return "no-ga4"

    insertion = "\n" + ADSENSE_SCRIPT
    new_content = content[:m.end()] + insertion + content[m.end():]
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(new_content)
    return "added"


def main():
    htmls = find_html_files(ROOT)
    added, already, no_ga4 = 0, 0, 0
    for path in htmls:
        rel = os.path.relpath(path, ROOT)
        result = process(path)
        if result == "added":
            print(f"  ✓ {rel}")
            added += 1
        elif result == "already":
            already += 1
        else:
            print(f"  ✗ {rel}: no GA4 block found")
            no_ga4 += 1
    print(f"\nAdded: {added}, Already had: {already}, No GA4: {no_ga4}")


if __name__ == "__main__":
    main()
