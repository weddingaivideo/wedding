#!/usr/bin/env python3
"""批量修复超长的 title 和 description。
- title ≤ 60 字符（HTML entity 解码后）
- description ≤ 160 字符（HTML entity 解码后）
"""
import os
import re
from html import unescape

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# path -> (new_title, new_description, new_og_description)
# new_og_description 可以为 None（保持原样）
REPLACEMENTS = {
    "about.html": (
        "About Us | Filmmakers + AI Engineers | WeddingAI.video",
        "Filmmakers, AI engineers, and wedding lovers building AI-powered wedding video services. Get to know us!",
        "Filmmakers, AI engineers, and wedding lovers behind AI-powered wedding video services. Meet us!",
    ),
    "gallery.html": (
        "Wedding Video Portfolio | Real Case Studies",
        "Real before-and-after examples of wedding video restoration, AI films, and personalization. Find inspiration!",
        "Real before-and-after examples of wedding video restoration, AI films, and personalization. See our work!",
    ),
    "index.html": (
        "AI-Powered Wedding Video Services | WeddingAI.video",
        "AI-powered wedding videos: AI films, multilingual dubbing, restoration, and more. 10+ services. Get a free quote!",
        "AI-powered wedding videos: AI films, multilingual dubbing, restoration, and more. 10+ services. Get a free quote!",
    ),
    "order.html": (
        "Free Wedding Video Quote | WeddingAI.video",
        "Ready to restore or create your wedding video? Submit your request and get a free personalized quote within 24 hours. No commitment!",
        None,
    ),
    "services/index.html": (
        "All Wedding Video Services | WeddingAI.video",
        "Browse all WeddingAI.video services: AI films, pet weddings, multilingual dubbing, and more. 10 services — explore now!",
        "Browse all WeddingAI.video services: AI films, pet weddings, multilingual dubbing, and more. Explore!",
    ),
    "services/absence-compensation/celebrity-message.html": (
        "Celebrity Wedding Messages — AI Generated",
        "Want a celebrity message for your wedding? Our AI creates personalized, realistic wedding greetings. Perfect for milestones!",
        None,
    ),
    "services/absence-compensation/family-message.html": (
        "Family Wedding Messages — Seamlessly Integrated",
        "Family can't make it to your wedding? We film their message and integrate it into your wedding video. They feel part of the day!",
        None,
    ),
    "services/absence-compensation/family-tribute.html": (
        "Honor a Loved One in Your Wedding Video",
        "Keep loved ones present on your wedding day. We respectfully create tributes from photos and audio to include in your video!",
        None,
    ),
    "services/personalization/ai-video-generator.html": (
        "AI Wedding Video Generator — From Photos",
        "Upload your photos and describe your dream wedding video. Our AI generates a cinematic film automatically — no editing skills needed!",
        None,
    ),
    "services/personalization/cartoon-style.html": (
        "Cartoon Wedding Video — Ghibli, Pixar, Anime",
        "Transform your wedding footage into a beautiful animation. Ghibli, Pixar, anime, or watercolor styles. Perfect for social sharing!",
        None,
    ),
    "services/personalization/multilingual.html": (
        "Multilingual Wedding Video — 20+ Languages",
        "Share your wedding video with family worldwide. AI voiceovers and subtitles in 20+ languages: English, Spanish, Hindi, Mandarin, more!",
        None,
    ),
    "services/personalization/pet-wedding.html": (
        "Pet Wedding Video — For Your Furry Family",
        "Your pet is family too. We create hilarious, heartwarming wedding videos starring your dog, cat, or any pet. Anniversary or just for fun!",
        None,
    ),
    "services/personalization/wedding-trailer.html": (
        "AI Wedding Trailer in 48 Hours — Cinematic",
        "Want a sneak peek of your wedding? We create cinematic trailers from your footage — perfect for Instagram, TikTok, and sharing with guests!",
        None,
    ),
    "services/video-enhancement/slow-motion.html": (
        "AI Slow Motion — Wedding Video Enhancement",
        "Smooth, natural slow motion for your wedding video. Our AI frame interpolation turns standard footage into buttery-smooth 60fps+. Try it!",
        None,
    ),
}


def escape_attr(s):
    """Escape for use in HTML attribute value (double-quoted)."""
    return s.replace("&", "&amp;").replace('"', "&quot;")


def process_file(rel, new_title, new_desc, new_og):
    path = os.path.join(ROOT, rel)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    original = content

    # Replace <title>...</title>
    content = re.sub(
        r'<title>.*?</title>',
        f'<title>{escape_attr(new_title)}</title>',
        content,
        count=1,
        flags=re.DOTALL,
    )

    # Replace meta description
    content = re.sub(
        r'<meta name="description"\s+content="[^"]*">',
        f'<meta name="description" content="{escape_attr(new_desc)}">',
        content,
        count=1,
    )

    # Optionally replace og:description
    if new_og is not None:
        content = re.sub(
            r'<meta property="og:description"\s+content="[^"]*">',
            f'<meta property="og:description" content="{escape_attr(new_og)}">',
            content,
            count=1,
        )

    if content != original:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        return True
    return False


def main():
    changed = 0
    for rel, (title, desc, og) in REPLACEMENTS.items():
        # Sanity check
        t_len = len(unescape(title))
        d_len = len(unescape(desc))
        if t_len > 60:
            print(f"  ⚠️  SKIP {rel}: title {t_len} > 60")
            continue
        if d_len > 160:
            print(f"  ⚠️  SKIP {rel}: desc {d_len} > 160")
            continue
        if process_file(rel, title, desc, og):
            print(f"  ✓ {rel}: title={t_len}, desc={d_len}")
            changed += 1
    print(f"\nTotal: {changed} files updated")


if __name__ == "__main__":
    main()
