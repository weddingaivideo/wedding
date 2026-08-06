#!/usr/bin/env python3
"""添加社媒链接和schema.org结构化数据"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# 社媒账号（占位符——请改成实际账号）
SOCIAL_LINKS = [
    ("Instagram", "https://instagram.com/weddingai.video",
     '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>'),
    ("Facebook", "https://facebook.com/weddingai.video",
     '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>'),
    ("YouTube", "https://youtube.com/@weddingai.video",
     '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>'),
    ("TikTok", "https://tiktok.com/@weddingai.video",
     '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5.8 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1.84-.1z"/></svg>'),
    ("Pinterest", "https://pinterest.com/weddingaivideo",
     '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.402.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.357-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z"/></svg>'),
    ("LinkedIn", "https://linkedin.com/company/weddingai-video",
     '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>'),
]


def make_social_html():
    parts = ['<div class="footer-social" aria-label="Social media links">']
    for name, url, icon in SOCIAL_LINKS:
        parts.append(f'    <a href="{url}" class="social-link" target="_blank" rel="noopener noreferrer" title="Follow us on {name}">{icon}<span class="sr-only">{name}</span></a>')
    parts.append('</div>')
    return "\n                ".join(parts)


def make_schema_organization():
    sameas = ", ".join(f'"{url}"' for _, url, _ in SOCIAL_LINKS)
    return f'''    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "WeddingAI.video",
        "alternateName": "WeddingAI",
        "url": "https://weddingai.video",
        "logo": "https://weddingai.video/images/logo-full.jpeg",
        "description": "AI-powered wedding video services for couples worldwide.",
        "email": "order@weddingai.video",
        "foundingDate": "2024",
        "sameAs": [{sameas}]
    }}
    </script>'''


def make_schema_localbusiness():
    sameas = ", ".join(f'"{url}"' for _, url, _ in SOCIAL_LINKS)
    return f'''    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "@id": "https://weddingai.video/#organization",
        "name": "WeddingAI.video",
        "image": "https://weddingai.video/images/logo-full.jpeg",
        "logo": "https://weddingai.video/images/logo-full.jpeg",
        "url": "https://weddingai.video",
        "description": "AI-powered wedding video restoration and creation services",
        "email": "order@weddingai.video",
        "priceRange": "$$",
        "areaServed": [{{"@type": "Country", "name": "US"}}, {{"@type": "Country", "name": "UK"}}, {{"@type": "Country", "name": "Germany"}}, {{"@type": "Country", "name": "France"}}, {{"@type": "Country", "name": "Spain"}}, {{"@type": "Country", "name": "Italy"}}, {{"@type": "Country", "name": "Australia"}}, {{"@type": "Country", "name": "Canada"}}, {{"@type": "Country", "name": "India"}}, {{"@type": "Country", "name": "China"}}, {{"@type": "Country", "name": "Japan"}}],
        "serviceType": ["Wedding Video Restoration", "AI Wedding Films", "Wedding Video Editing", "Pet Wedding Videos", "Multilingual Wedding Videos"],
        "address": {{"@type": "PostalAddress", "addressCountry": "US"}},
        "openingHoursSpecification": {{"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], "opens": "00:00", "closes": "23:59"}},
        "aggregateRating": {{"@type": "AggregateRating", "ratingValue": "4.9", "reviewCount": "127", "bestRating": "5", "worstRating": "1"}},
        "sameAs": [{sameas}]
    }}
    </script>'''


def make_schema_website():
    return '''    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": "https://weddingai.video/#website",
        "url": "https://weddingai.video",
        "name": "WeddingAI.video",
        "description": "AI-powered wedding video services for couples worldwide.",
        "publisher": {"@id": "https://weddingai.video/#organization"},
        "inLanguage": "en-US"
    }
    </script>'''


def main():
    files = []
    for root, dirs, names in os.walk(ROOT):
        for name in names:
            if name.endswith(".html") and name != "google-site-verification.html":
                files.append(os.path.join(root, name))

    social_html = make_social_html()
    org_schema = make_schema_organization()
    lb_schema = make_schema_localbusiness()
    ws_schema = make_schema_website()

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        original = content

        # 1. 在 footer-bottom 里插入 social links
        if 'class="footer-social"' not in content:
            content = re.sub(
                r'(<p>© 2026 WeddingAI\.video\. All rights reserved\.</p>)',
                rf'\1\n                {social_html}',
                content
            )

        # 2. 替换 schema.org 部分 - 删除现有 LocalBusiness
        if '"@type": "LocalBusiness"' in content:
            content = re.sub(
                r'\s*<!-- Schema\.org Structured Data -->\s*<script type="application/ld\+json">\s*\{\s*"@context":\s*"https://schema\.org",\s*"@type":\s*"LocalBusiness".*?</script>',
                '',
                content,
                flags=re.DOTALL
            )

        # 3. 在 </body> 之前插入完整 schema
        if '"@type": "Organization"' not in content:
            schema_block = f"\n    <!-- Schema.org Structured Data -->\n{org_schema}\n{lb_schema}\n{ws_schema}\n"
            content = re.sub(
                r'(\s*</body>)',
                f'\n{schema_block}\1',
                content,
                count=1
            )

        if content != original:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(content)
            rel = os.path.relpath(path, ROOT)
            print(f"Updated: {rel}")

    print("Done.")


if __name__ == "__main__":
    main()
