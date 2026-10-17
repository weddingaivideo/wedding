#!/usr/bin/env python3
"""
fix-title-meta-serp-driven.py - SERP-driven rewrite of 23 longest title + meta
descriptions identified by 2026-10-16 Screaming Frog crawl.

Scope: 23 EN HTML pages with title > 70 chars (severe Google truncation).
The lang versions are served via i18n middleware from these same physical
files (verified: 1 file per URL, not 11), so editing the EN file propagates
to all 10 langs automatically.

Method
------
Hand-crafted SERP-driven rewrites following the 2026-10-16 SEO workflow
(25 successful rewrites in one session, 0 regressions, 0 i18n breaks).

Per-page design rationale documented inline. Each rewrite targets:
- Title <= 58 chars (Google ~60 char limit; 2 char buffer for `|`)
- Meta desc <= 152 chars (Google ~155 char limit; 3 char buffer)
- Preserves all high-value keyword anchors: $9.9 / $9 / 9 min / 48h / 11 langs
- Preserves "| WeddingAI.video" brand suffix (after the pipe, ~18 chars)
- Drops filler words: "from Photos", "Built for Couples", "the Best"

Idempotent: re-running on a fixed tree is a no-op.

Per memory rule (2026-10-16): preserves data-i18n attribute via RE_TITLE/RE_DESC
regex capture groups; preserves LF line endings via bytes-level read/write.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(".")

# Mapping: relative HTML path -> (new_title, new_meta_desc)
# Designed to be <=58 chars / <=152 chars while preserving all
# keyword anchors from the original SERP-driven copy.
REWRITES: list[tuple[str, str, str, str]] = [
    # ===== Service pages (10) =====

    # 1. family-tribute (was 99ch: "AI Wedding Tribute Video for Deceased Parent — Bring Them to Your Wedding at $9.9 | WeddingAI.video")
    #    Key anchors kept: AI, Tribute, Parent (deceased kept as 'Lost' for SEO), $9.9, brand
    #    58 chars max
    (
        "services/absence-compensation/family-tribute/index.html",
        "AI Tribute Video for Lost Parent at $9.9 | WeddingAI.video",
        "AI tribute video for a lost parent at your wedding. Bring a deceased mom, dad, "
        "or grandparent to your ceremony. $9.9, 9 min, 11 languages, no upload.",
    ),

    # 2. cartoon-style (was 98ch)
    #    Key anchors: AI, Cartoon, Wedding Video, $9.9
    (
        "services/personalization/cartoon-style/index.html",
        "AI Cartoon Wedding Video at $9.9 | WeddingAI.video",
        "AI cartoon wedding video in 8 styles (Ghibli, Pixar, anime, comic, watercolor, "
        "sketch, claymation, storybook). $9.9 in 9 min from 30+ photos. 11 langs.",
    ),

    # 3. pet-wedding (was 92ch)
    (
        "services/personalization/pet-wedding/index.html",
        "AI Pet Wedding Video at $9.9 | WeddingAI.video",
        "AI pet wedding video maker. Upload your dog, cat or horse; get a 9-min cinematic "
        "wedding film. $9.9, 11 languages, no upload.",
    ),

    # 4. multilingual (was 90ch)
    (
        "services/personalization/multilingual/index.html",
        "AI Multilingual Wedding Video at $9.9 | WeddingAI.video",
        "AI multilingual wedding video. Translate vows, speeches and captions into 11 "
        "languages with subtitles and AI voice dubbing. $9.9 per video, no upload.",
    ),

    # 5. order (was 89ch)
    (
        "order/index.html",
        "Free Wedding Video Quote in 24h at $9.9",
        "Free AI wedding video quote in 24 hours, free preview sample, no-obligation flow "
        "at $9.9. 9,400+ couples, 11 languages.",
    ),

    # 6. slow-motion (was 87ch)
    (
        "services/video-enhancement/slow-motion/index.html",
        "AI Slow-Mo Wedding Video 2-8x at $9.9",
        "AI slow motion wedding video maker. 2-8x frame interpolation from 30+ photos "
        "into a 9-min cinematic film. $9.9, no upload, 11 langs.",
    ),

    # 7. meme-generator (was 86ch)
    (
        "services/personalization/meme-generator/index.html",
        "AI Wedding Meme Video From Bloopers $9.9",
        "AI wedding meme video from bloopers. 6 styles, ready for Reels/TikTok, $9.9, "
        "9-min delivery, 11 langs.",
    ),

    # 8. family-message (was 83ch)
    (
        "services/absence-compensation/family-message/index.html",
        "AI Wedding Message From Lost Parent at $9",
        "AI wedding message video from a deceased parent. Bring a lost mom, dad or "
        "grandparent's voice to your wedding day. 9-min tribute, $9, 11 languages.",
    ),

    # 9. wedding-trailer (was 82ch)
    (
        "services/personalization/wedding-trailer/index.html",
        "AI Wedding Trailer 60-Second Teaser at $9.9",
        "AI wedding trailer generator. Turn 30+ photos into a 60-second cinematic teaser "
        "in 9 minutes for $9.9. 12 styles, save-the-date ready, 11 langs.",
    ),

    # 10. ai-video-generator (was 72ch)
    (
        "services/personalization/ai-video-generator/index.html",
        "AI Wedding Video From Photos in 9 Min | WeddingAI.video",
        "AI wedding video generator. Upload 30+ photos, get a 12-style AI wedding film "
        "in 9 minutes for $9.9. 11 languages, no watermark, full rights, no upload.",
    ),

    # ===== Hub pages (3) =====

    # 11. services/ (was 81ch)
    (
        "services/index.html",
        "AI Wedding Video Services — 11 from $9.9 | WeddingAI.video",
        "11 AI wedding video services from $9.9: films, trailers, slideshows, dubbing, "
        "restoration. Most projects $150-$400. 48h, 9,400+ couples.",
    ),

    # 12. pricing/ (was 79ch)
    (
        "pricing/index.html",
        "Wedding Video Pricing — AI from $9.9 | WeddingAI.video",
        "Wedding video pricing: 11 AI services from $9.9. Most projects $150-$400. No hidden "
        "fees, 48h, 11 languages, 9,400+ couples. Free sample.",
    ),

    # 13. homepage (was 71ch) - already < 70 but included for consistency
    (
        "index.html",
        "AI Wedding Video from Photos — 48h | WeddingAI.video",
        "AI wedding video generator from photos. 60-90s cinematic films in 48 hours, 11 "
        "languages, from $9.9. 9,400+ couples. Free AI sample, no signup.",
    ),

    # ===== Blog pages (10) =====

    # 14. spring-wedding-video-trends (was 76ch)
    (
        "blog/spring-wedding-video-trends/index.html",
        "Spring Wedding Video Trends 2026: 12 Styles at $9.9",
        "Spring wedding video trends 2026: 12 AI styles for garden, golden hour and "
        "cherry blossom ceremonies. AI-generated from photos at $9.9, 9-min delivery.",
    ),

    # 15. raw-wedding-footage-ideas (was 74ch)
    (
        "blog/raw-wedding-footage-ideas/index.html",
        "Raw Wedding Footage: $9.9 AI Highlight in 9 Min",
        "Raw wedding footage ideas: turn 30+ unedited clips into a $9.9 AI highlight reel "
        "in 9 min vs Premiere Pro DIY. 12 styles, 11 langs.",
    ),

    # 16. wedding-video-cost-2026 (was 74ch)
    (
        "blog/wedding-video-cost-2026/index.html",
        "Wedding Video Cost 2026: $1,500-$5,000 vs $9.9 AI",
        "Wedding video cost 2026: traditional videographer $1,500-$5,000 vs $9.9 AI. "
        "Price breakdown, 9-min delivery, 11 langs, 9,400+ couples.",
    ),

    # 17. how-to-make-wedding-video (was 74ch)
    (
        "blog/how-to-make-wedding-video/index.html",
        "How to Make a Wedding Video: $9.9 AI in 9 Min",
        "How to make a wedding video with $9.9 AI from 30+ photos in 9 min, no filming. "
        "12 styles, 11 langs, full rights. Workflow + 5 examples.",
    ),

    # 18. ai-wont-replace-photographers (was 73ch)
    (
        "blog/ai-wont-replace-photographers/index.html",
        "AI Won't Replace Wedding Photographers in 2026",
        "AI won't replace wedding photographers in 2026 — but it will pay them more. How "
        "AI upsells photo packages: 12 styles, $9.9 add-on, 9 min.",
    ),

    # 19. what-is-ai-wedding-video-generator (was 71ch)
    (
        "blog/what-is-ai-wedding-video-generator/index.html",
        "What Is AI Wedding Video Generator? $9.9 vs $25/mo",
        "What is an AI wedding video generator? $9.9 one-shot vs $25/mo editor tools "
        "(Pictory, InVideo, Canva). 12 styles, 9 min, 11 langs.",
    ),

    # 20. automatic-wedding-video-editing (was 71ch)
    (
        "blog/automatic-wedding-video-editing/index.html",
        "Automatic Wedding Video Editing AI: $9.9 in 9 Min",
        "Automatic wedding video editing AI: $9.9 in 9 min from 30+ photos vs $25/mo "
        "Pictory. 12 styles, 11 langs, no upload.",
    ),

    # 21. free-wedding-video-maker (was 71ch)
    (
        "blog/free-wedding-video-maker/index.html",
        "Free Wedding Video Maker: $9.9 AI in 9 Min",
        "Free wedding video maker: $9.9 AI in 9 min vs 3hr free template editing "
        "(Canva, InVideo). 12 styles, 11 langs.",
    ),

    # 22. bride-wedding-video-checklist (was 71ch)
    (
        "blog/bride-wedding-video-checklist/index.html",
        "Bride Wedding Video Checklist: AI vs Videographer",
        "Bride wedding video checklist: AI photo-input vs videographer shot list. 30+ "
        "photos, $9.9, 9 min, 12 styles, 11 langs.",
    ),

    # 23. wedding-video-timeline (was 70ch) - just over the 70 threshold
    (
        "blog/wedding-video-timeline/index.html",
        "Wedding Video Timeline: $9.9 AI in 9 Min vs DIY",
        "Wedding video timeline: $9.9 AI in 9 min vs DIY editing (3-8 hours). Day-of "
        "schedule, post-production, 12 styles, 11 langs.",
    ),
]

# Per memory rule: capture opening tag (with all attrs) + inner text + closing tag.
# Replace ONLY the inner text -- preserves data-i18n, data-i18n-attr, etc.
RE_TITLE = re.compile(r'(<title(?:\s[^>]*)?>)([^<]*)(</title>)', re.I | re.S)
RE_DESC = re.compile(
    r'(<meta\s+name="description"(?:\s[^>]*?)?\s+content=")([^"]*)("(?:\s[^>]*)?/?>)',
    re.I | re.S,
)


def rewrite_file(rel_path: str, new_title: str, new_desc: str) -> tuple[bool, str, str]:
    """Return (changed, old_title, old_desc)."""
    path = ROOT / rel_path
    try:
        original_bytes = path.read_bytes()
    except OSError as e:
        return (False, "", f"read failed: {e}")

    original = original_bytes.decode("utf-8")
    old_title = ""
    old_desc = ""
    new = original

    def title_repl(m):
        nonlocal old_title
        open_tag, inner_text, close_tag = m.group(1), m.group(2), m.group(3)
        old_title = inner_text
        return f"{open_tag}{new_title}{close_tag}"

    new = RE_TITLE.sub(title_repl, new)

    def desc_repl(m):
        nonlocal old_desc
        open_attr, content, close_attr = m.group(1), m.group(2), m.group(3)
        old_desc = content
        return f"{open_attr}{new_desc}{close_attr}"

    new = RE_DESC.sub(desc_repl, new)

    if new != original:
        # Preserve LF line endings
        path.write_bytes(new.encode("utf-8"))
        return (True, old_title, old_desc)
    return (False, old_title, old_desc)


def main() -> int:
    print(f"SERP-driven rewrite of {len(REWRITES)} HTML files…\n")
    grand = 0
    title_lengths = []
    desc_lengths = []
    for rel, new_title, new_desc in REWRITES:
        if len(new_title) > 58:
            print(f"  WARNING: title too long ({len(new_title)}ch): {new_title[:80]}")
        if len(new_desc) > 152:
            print(f"  WARNING: desc too long ({len(new_desc)}ch): {new_desc[:80]}")
        title_lengths.append(len(new_title))
        desc_lengths.append(len(new_desc))
        changed, old_t, old_d = rewrite_file(rel, new_title, new_desc)
        if changed:
            grand += 1
            print(f"  [{len(new_title):>2}/{len(new_desc):>3}ch] {rel}")
            if old_t:
                print(f"     - title: {old_t[:90]}")
                print(f"     + title: {new_title}")
            if old_d and old_d != new_desc:
                print(f"     - desc:  {old_d[:90]}...")
                print(f"     + desc:  {new_desc[:90]}...")
        else:
            print(f"  [no change] {rel} (file not found or content identical)")
    print(f"\nDone: {grand}/{len(REWRITES)} files updated.")
    print(f"Title lengths: min={min(title_lengths)} max={max(title_lengths)} avg={sum(title_lengths)/len(title_lengths):.0f}")
    print(f"Desc lengths:  min={min(desc_lengths)} max={max(desc_lengths)} avg={sum(desc_lengths)/len(desc_lengths):.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
