#!/usr/bin/env python3
"""为所有HTML的 <a> 链接添加 title 属性 (不破坏内部子标签)。"""
import os
import re
import sys

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# 自定义：某些链接的title需要特殊处理
TITLE_OVERRIDES = {
    "Order": "Get a free quote — start your project",
    "Get a Free Quote": "Get a free quote — start your project",
    "Send My Request — Free Quote →": "Send my request — get a free quote",
    "View All Cases →": "View all case studies",
    "Learn More →": "Learn more about this service",
    "Explore Our Services": "Explore all our wedding video services",
    "Services": "Browse our wedding video services",
    "Gallery": "View our gallery and case studies",
    "About": "Learn about us",
    "About Us": "Learn about us",
    "Get a Quote": "Get a free quote — start your project",
    "Privacy Policy": "Read our privacy policy",
    "Terms of Service": "Read our terms of service",
    "Back to top": "Back to top",
}

def clean_text(text):
    return re.sub(r'\s*[→←↑↓]\s*', '', text).strip()


# 移除已添加title中的→以便重新匹配
def normalize_for_match(text):
    return clean_text(text)

def infer_title(href, link_text, has_image):
    text = clean_text(link_text)
    if not text and has_image:
        return "WeddingAI.video — wedding video services"
    if not text:
        return None
    if text in TITLE_OVERRIDES:
        return TITLE_OVERRIDES[text]
    # 移除 → 后再匹配
    no_arrow = re.sub(r'\s*[→←↑↓]\s*', '', text).strip()
    if no_arrow in TITLE_OVERRIDES:
        return TITLE_OVERRIDES[no_arrow]
    if href.startswith("mailto:"):
        email = href.replace("mailto:", "").split("?")[0]
        return f"Send us an email at {email}"
    if href.startswith("tel:"):
        return f"Call us at {href.replace('tel:', '')}"
    if href.startswith("#"):
        return f"Jump to {text}"
    return text


# 匹配 <a ...>...</a> 包含嵌套 <a> 不会匹配（因为是 .*?非贪婪）
# 嵌套情况: <a href="x"><a href="y">text</a></a> 在正则下匹配外层
# 这种情况下我们处理外层时内部会丢失——但实际 HTML 中嵌套 a 非法，浏览器会修正
A_PATTERN = re.compile(r'(<a\s+[^>]*?>)(.*?</a>)', re.DOTALL | re.IGNORECASE)


def add_title_to_a(match):
    open_tag = match.group(1)  # <a ...>
    rest = match.group(2)      # ...inner...</a>

    # 检查是否已有 title
    if re.search(r'\btitle\s*=\s*["\']', open_tag):
        return match.group(0)

    # 提取 href
    href_match = re.search(r'href\s*=\s*["\']([^"\']*)["\']', open_tag)
    href = href_match.group(1) if href_match else ""

    # 提取链接内部内容
    inner = rest[:-len('</a>')] if rest.endswith('</a>') else rest

    # 提取链接文本（去内部标签）
    text = re.sub(r'<[^>]+>', '', inner)
    text = clean_text(text)
    has_image = '<img' in inner

    title = infer_title(href, text, has_image)
    if not title:
        return match.group(0)

    # 转义 title 中的双引号
    title_escaped = title.replace('"', '&quot;')

    # 在 open_tag 的 > 前插入 title="..."
    if open_tag.endswith('>'):
        new_open = open_tag[:-1] + f' title="{title_escaped}">'
    else:
        return match.group(0)

    return new_open + rest


def process_html(content):
    return A_PATTERN.sub(add_title_to_a, content)


def main():
    files = []
    for root, dirs, names in os.walk(ROOT):
        for name in names:
            if name.endswith(".html") and name != "google-site-verification.html":
                files.append(os.path.join(root, name))

    total_updated = 0
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        new_content = process_html(content)
        if new_content != content:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new_content)
            rel = os.path.relpath(path, ROOT)
            print(f"Updated: {rel}")
            total_updated += 1
    print(f"\nTotal: {total_updated} files updated")


if __name__ == "__main__":
    main()
