#!/usr/bin/env python3
"""添加更多 schema.org 结构化数据 (FAQPage, Review, Service, BreadcrumbList)"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"


def faq_schema():
    return '''    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": "How long does it take to restore an old wedding video?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Standard turnaround is 48–72 hours. For complex restorations (heavy damage, multiple tapes), it may take 5–7 business days. Rush delivery is available for an additional fee."
                }
            },
            {
                "@type": "Question",
                "name": "What video formats do you accept?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "We accept VHS, VHS-C, DV, Hi8, MiniDVD, 8mm, 16mm film, and all modern digital formats (MP4, MOV, AVI, MKV)."
                }
            },
            {
                "@type": "Question",
                "name": "How do I send my video files?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "After submitting your request, we'll send you a secure upload link. Files are encrypted and deleted 30 days after delivery."
                }
            },
            {
                "@type": "Question",
                "name": "Can you restore a video with missing audio?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Yes. Our AI can reconstruct audio from visual cues and ambient sound."
                }
            },
            {
                "@type": "Question",
                "name": "What's your refund policy?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "If you're not satisfied with the result, we'll revise it twice at no extra cost. Full refund is available if we can't meet your requirements after revisions."
                }
            }
        ]
    }
    </script>'''


def reviews_schema():
    return '''    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "WeddingAI.video Services",
        "description": "AI-powered wedding video restoration, creation, and personalization services",
        "brand": {"@type": "Brand", "name": "WeddingAI.video"},
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.9",
            "reviewCount": "127",
            "bestRating": "5",
            "worstRating": "1"
        },
        "review": [
            {
                "@type": "Review",
                "author": {"@type": "Person", "name": "Jennifer L."},
                "datePublished": "2025-09-15",
                "reviewRating": {"@type": "Rating", "ratingValue": "5", "bestRating": "5"},
                "reviewBody": "I was heartbroken when my father's 1995 wedding speech on VHS wouldn't play. WeddingAI restored every word perfectly. I'll treasure this forever."
            },
            {
                "@type": "Review",
                "author": {"@type": "Person", "name": "Priya M."},
                "datePublished": "2025-10-02",
                "reviewRating": {"@type": "Rating", "ratingValue": "5", "bestRating": "5"},
                "reviewBody": "We got married in Italy but have family in India. They created a Hindi version of our wedding video that made everyone feel included. Absolutely magical."
            },
            {
                "@type": "Review",
                "author": {"@type": "Person", "name": "Mike T."},
                "datePublished": "2025-11-20",
                "reviewRating": {"@type": "Rating", "ratingValue": "5", "bestRating": "5"},
                "reviewBody": "The real-time editing at our reception was a game changer. Our guests couldn't stop talking about the live-comments screen. Worth every penny."
            },
            {
                "@type": "Review",
                "author": {"@type": "Person", "name": "Sophie K."},
                "datePublished": "2025-12-08",
                "reviewRating": {"@type": "Rating", "ratingValue": "5", "bestRating": "5"},
                "reviewBody": "Our wedding videographer only gave us a 10-minute highlight. WeddingAI turned our raw footage into a 45-minute cinematic film we watch every anniversary."
            },
            {
                "@type": "Review",
                "author": {"@type": "Person", "name": "Emma W."},
                "datePublished": "2026-01-14",
                "reviewRating": {"@type": "Rating", "ratingValue": "5", "bestRating": "5"},
                "reviewBody": "Our cats got married on our 5th anniversary and the video they made is genuinely better than our human wedding video. 10/10 would recommend."
            }
        ]
    }
    </script>'''


def breadcrumb_schema(items):
    """items: [(name, url), ...]"""
    item_list = ",\n".join(
        f'            {{"@type": "ListItem", "position": {i+1}, "name": "{name}", "item": "{url}"}}'
        for i, (name, url) in enumerate(items)
    )
    return f'''    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
{item_list}
        ]
    }}
    </script>'''


def service_schema(name, description, price_from, url):
    return f'''    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "Service",
        "serviceType": "{name}",
        "name": "{name}",
        "description": "{description}",
        "provider": {{"@id": "https://weddingai.video/#organization"}},
        "url": "{url}",
        "areaServed": [{{"@type": "Country", "name": "US"}}, {{"@type": "Country", "name": "UK"}}, {{"@type": "Country", "name": "Germany"}}, {{"@type": "Country", "name": "France"}}, {{"@type": "Country", "name": "Italy"}}, {{"@type": "Country", "name": "Spain"}}, {{"@type": "Country", "name": "Australia"}}, {{"@type": "Country", "name": "Canada"}}, {{"@type": "Country", "name": "India"}}, {{"@type": "Country", "name": "China"}}, {{"@type": "Country", "name": "Japan"}}],
        "offers": {{
            "@type": "Offer",
            "url": "{url}",
            "priceCurrency": "USD",
            "price": "{price_from}",
            "priceSpecification": {{"@type": "PriceSpecification", "priceCurrency": "USD", "minPrice": "{price_from}", "price": "{price_from}"}},
            "availability": "https://schema.org/InStock"
        }}
    }}
    </script>'''


# 各服务的schema配置
# Keys are local on-disk paths (e.g. "services/X/Y.html"); the `url` field uses the
# canonical clean URL on the live site.
SERVICES = {
    "services/video-enhancement/slow-motion.html": (
        "AI Slow Motion Enhancement",
        "Transform standard footage into smooth 60fps+ slow motion using AI frame interpolation.",
        "99",
        "https://weddingai.video/services/video-enhancement/slow-motion"
    ),
    "services/absence-compensation/family-tribute.html": (
        "Family Tribute for Deceased Loved Ones",
        "Respectfully include deceased family members in your wedding video using AI-enhanced archived photos and audio.",
        "149",
        "https://weddingai.video/services/absence-compensation/family-tribute"
    ),
    "services/absence-compensation/family-message.html": (
        "Remote Family Wedding Message",
        "Integrate video messages from family who can't attend in person, seamlessly blended into your wedding film.",
        "149",
        "https://weddingai.video/services/absence-compensation/family-message"
    ),
    "services/absence-compensation/celebrity-message.html": (
        "Celebrity-Style Wedding Message",
        "AI-generated celebrity-style wedding greeting for fun, shareable, milestone-celebration content.",
        "499",
        "https://weddingai.video/services/absence-compensation/celebrity-message"
    ),
    "services/personalization/ai-video-generator.html": (
        "AI Wedding Video Generator",
        "Turn your photos into a cinematic wedding film using AI — no editing skills needed.",
        "199",
        "https://weddingai.video/services/personalization/ai-video-generator"
    ),
    "services/personalization/wedding-trailer.html": (
        "Cinematic Wedding Trailer",
        "Hollywood-style 1-3 minute cinematic wedding trailer with licensed music.",
        "399",
        "https://weddingai.video/services/personalization/wedding-trailer"
    ),
    "services/personalization/pet-wedding.html": (
        "Pet Wedding Video",
        "Heartwarming and hilarious AI-generated wedding videos starring your dog, cat, or any pet.",
        "149",
        "https://weddingai.video/services/personalization/pet-wedding"
    ),
    "services/personalization/multilingual.html": (
        "Multilingual Wedding Video Dubbing & Subtitles",
        "AI voiceovers and subtitles in 20+ languages — English, Spanish, Hindi, Mandarin, Arabic, and more.",
        "99",
        "https://weddingai.video/services/personalization/multilingual"
    ),
    "services/personalization/cartoon-style.html": (
        "Cartoon / Animated Wedding Video",
        "Transform wedding footage into Ghibli, Pixar, anime, or watercolor cartoon styles.",
        "149",
        "https://weddingai.video/services/personalization/cartoon-style"
    ),
    "services/personalization/meme-generator.html": (
        "Wedding GIFs & Memes",
        "Custom shareable wedding GIFs and memes for social media and group chats.",
        "49",
        "https://weddingai.video/services/personalization/meme-generator"
    ),
}


# 根级页面 breadcrumbs (uses clean URLs on the live site)
ROOT_BREADCRUMBS = {
    "about.html": [("Home", "https://weddingai.video/"), ("About Us", "https://weddingai.video/about")],
    "gallery.html": [("Home", "https://weddingai.video/"), ("Gallery", "https://weddingai.video/gallery")],
    "order.html": [("Home", "https://weddingai.video/"), ("Get a Quote", "https://weddingai.video/order")],
    "privacy.html": [("Home", "https://weddingai.video/"), ("Privacy Policy", "https://weddingai.video/privacy")],
    "terms.html": [("Home", "https://weddingai.video/"), ("Terms of Service", "https://weddingai.video/terms")],
    "success.html": [("Home", "https://weddingai.video/"), ("Thank You", "https://weddingai.video/success")],
}


def main():
    files = []
    for root, dirs, names in os.walk(ROOT):
        for name in names:
            if name.endswith(".html") and name != "google-site-verification.html":
                files.append(os.path.join(root, name))

    for path in files:
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        original = content

        # 1. index.html - 加 FAQ + Reviews
        if rel == "index.html":
            if '"@type": "FAQPage"' not in content:
                content = content.replace(
                    "    </main>",
                    f"    </main>\n\n{faq_schema()}\n",
                    1
                )
            # Review schema 放在 FAQ 后面
            if '"@type": "Product"' not in content and '"review":' not in content:
                content = content.replace(
                    "    </main>",
                    f"    </main>\n\n{reviews_schema()}\n",
                    1
                )

        # 2. 各服务页面 - 加 Service schema
        if rel in SERVICES:
            if '"@type": "Service"' not in content:
                name, desc, price, url = SERVICES[rel]
                # 在 schema 区域之前插入
                content = content.replace(
                    "    </main>",
                    f"    </main>\n\n{service_schema(name, desc, price, url)}\n",
                    1
                )

        # 3. 所有非首页：加 BreadcrumbList
        if rel != "index.html":
            if '"@type": "BreadcrumbList"' not in content:
                # 根据路径生成 breadcrumb
                if rel in ROOT_BREADCRUMBS:
                    items = ROOT_BREADCRUMBS[rel]
                elif rel.startswith("services/"):
                    # service 页
                    parts = rel.split("/")
                    if len(parts) == 2:
                        # /services/index.html
                        items = [("Home", "https://weddingai.video/"), ("Services", "https://weddingai.video/services/")]
                    else:
                        category = parts[1]  # video-enhancement
                        # 特殊处理类目名
                        category_name_map = {
                            "video-enhancement": "Video Enhancement",
                            "absence-compensation": "Absence Compensation",
                            "personalization": "Personalization",
                        }
                        category_name = category_name_map.get(category, category.replace("-", " ").title())
                        cat_url = f"https://weddingai.video/services/#{category}"
                        # 特殊处理服务名
                        service_name_raw = parts[2].replace(".html", "")
                        service_name_map = {
                            "slow-motion": "Slow Motion Enhancement",
                            "family-tribute": "Family Tribute",
                            "family-message": "Family Message",
                            "celebrity-message": "Celebrity Message",
                            "ai-video-generator": "AI Video Generator",
                            "wedding-trailer": "Wedding Trailer",
                            "pet-wedding": "Pet Wedding",
                            "multilingual": "Multilingual Dubbing",
                            "cartoon-style": "Cartoon Style",
                            "meme-generator": "Wedding Memes & GIFs",
                        }
                        service_name = service_name_map.get(service_name_raw, service_name_raw.replace("-", " ").title())
                        items = [
                            ("Home", "https://weddingai.video/"),
                            ("Services", "https://weddingai.video/services/"),
                            (category_name, cat_url),
                            (service_name, f"https://weddingai.video/{rel}"),
                        ]
                else:
                    items = [("Home", "https://weddingai.video/"), (rel.replace(".html", "").replace("-", " ").title(), f"https://weddingai.video/{rel}")]

                content = content.replace(
                    "    </main>",
                    f"    </main>\n\n{breadcrumb_schema(items)}\n",
                    1
                )

        if content != original:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(content)
            print(f"Updated: {rel}")

    print("Done.")


if __name__ == "__main__":
    main()
