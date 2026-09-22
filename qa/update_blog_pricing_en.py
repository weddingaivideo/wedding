#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update English blog posts: replace $49 / $49.99 brand-starting-price
anchors with $9.9 to match the unified positioning.

DOES NOT TOUCH:
  - Specific real service prices ($149, $199, $249, $299, $349, $399, $499)
  - Per-tape VHS restoration prices ($15, $25, $50)
  - DIY tool / software subscription prices ($20/month, etc.)
  - Traditional videographer comparison prices ($1500+)
  - Per-project real quotes (e.g. "$299 for AI Video Generator processing")

Targets (English): brand "starts at $49" / "ranges from $49" / "$49.99"
as the entry anchor.
"""

import os
import re
import sys

BLOG_DIR = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai\blog"


# (slug, old_text, new_text) — surgical replacements.
# Each old_text must appear exactly once in the target file.
EDITS = [
    # 1) ai-vs-human-wedding-editing
    (
        "ai-vs-human-wedding-editing",
        ">AI-powered wedding video editing typically ranges from $49 for basic enhancements to $399 for comprehensive packages including multiple deliverables.",
        ">AI-powered wedding video editing typically starts at $9.9 for basic enhancements, with comprehensive packages up to $399 including multiple deliverables.",
    ),
    # 2) ai-wedding-video-industry
    (
        "ai-wedding-video-industry",
        ">AI-powered wedding video services typically range from $49 for basic enhancements to $499 for comprehensive packages that include multiple deliverables.",
        ">AI-powered wedding video services typically start at $9.9 for basic enhancements, with comprehensive packages up to $499 that include multiple deliverables.",
    ),
    # 3) skip-wedding-videographer
    (
        "skip-wedding-videographer",
        ">WeddingAI.video's services start at $49 and range up to $499 for comprehensive packages. At the $149-$399 level, you get a professionally edited, cinematic wedding video created from your existing footage \u2014 whether that's from phones, consumer cameras, or a combination of sources.",
        ">WeddingAI.video's services start at $9.9 and range up to $499 for comprehensive packages. At the $149-$399 level, you get a professionally edited, cinematic wedding video created from your existing footage \u2014 whether that's from phones, consumer cameras, or a combination of sources.",
    ),
    # 4) wedding-slow-motion-effect (L270: typical cost line)
    (
        "wedding-slow-motion-effect",
        "$49-$349 depending on footage length and complexity.",
        "$9.9-$349 depending on footage length and complexity.",
    ),
    # 5) wedding-slow-motion-effect (L340: ranges from line)
    (
        "wedding-slow-motion-effect",
        "Professional AI slow motion enhancement ranges from $49 for a short clip to $349 for a full wedding film. DIY software costs $0-$299 (one-time purchase) but requires your time and technical skill.",
        "Professional AI slow motion enhancement starts at $9.9 for a short clip, with most projects landing at $150-$349 for a full wedding film. DIY software costs $0-$299 (one-time purchase) but requires your time and technical skill.",
    ),
    # 6) wedding-video-cost-2026 (L396)
    (
        "wedding-video-cost-2026",
        "Yes. WeddingAI.video's services start at $49 for specific enhancements and $149 for full video generation. Combined with free guest-captured footage, you can get a professional-quality wedding video for well under $500.",
        "Yes. WeddingAI.video's services start at $9.9 for specific enhancements and $149 for full video generation. Combined with free guest-captured footage, you can get a professional-quality wedding video for well under $500.",
    ),
    # 7) wedding-video-cost-2026-new (L267: starts at just $49.99)
    (
        "wedding-video-cost-2026-new",
        'starts at just $49.99 and delivers results that rival videos costing thousands.',
        'starts at $9.9 and delivers results that rival videos costing thousands.',
    ),
    # 8) wedding-video-cost-2026-new (L283: Vintage Restoration $49.99)
    (
        "wedding-video-cost-2026-new",
        "**Vintage Restoration:** $49.99 — Restore old family wedding videos to HD quality.",
        "**Vintage Restoration:** starting at $9.9 — Restore old family wedding videos to HD quality.",
    ),
    # 9) weddingai-video-review (L214: services range from $49 to $499)
    (
        "weddingai-video-review",
        "WeddingAI.video's services range from $49 to $499 — roughly 70-90% less than traditional videographers. For couples on a budget,",
        "WeddingAI.video's services start at $9.9 (most projects $150-$400) and range up to $499 — roughly 70-90% less than traditional videographers. For couples on a budget,",
    ),
    # 10) weddingai-video-review (L325)
    (
        "weddingai-video-review",
        "WeddingAI.video services range from $49 to $499, while traditional videographers charge $1,500 to $5,000+ on average.",
        "WeddingAI.video services start at $9.9 (most projects $150-$400) and range up to $499, while traditional videographers charge $1,500 to $5,000+ on average.",
    ),
    # 11) wedding-video-from-photos (L307: Add slow motion and enhancement: $49-$149 extra)
    (
        "wedding-video-from-photos",
        ">$49-$149 extra</",
        ">$9.9-$149 extra</",
    ),
    # 12) wedding-photos-vs-video L223-224 — these are real service prices ($50-$300 photo-to-video, $100-$500 AI editing). LEAVE.
    # (placeholder to keep numbering consistent)
]


def main():
    if not os.path.isdir(BLOG_DIR):
        print(f"FATAL: blog dir not found: {BLOG_DIR}", file=sys.stderr)
        return 1

    by_slug = {}
    for slug, old, new in EDITS:
        if not old:
            continue
        by_slug.setdefault(slug, []).append((old, new))

    total_applied = 0
    for slug, ops in by_slug.items():
        path = os.path.join(BLOG_DIR, slug, "index.html")
        if not os.path.isfile(path):
            print(f"  SKIP {slug} (no index.html)")
            continue

        with open(path, "r", encoding="utf-8", newline="") as f:
            raw = f.read()

        # Detect line ending
        newline = "\r\n" if "\r\n" in raw else "\n"

        original = raw
        applied = 0
        for old, new in ops:
            count = raw.count(old)
            if count == 0:
                print(f"  WARN {slug}: pattern not found: {old[:80]!r}")
                continue
            if count > 1:
                # Replace all occurrences to be safe (this would only happen
                # for accidentally repeated identical phrases).
                raw = raw.replace(old, new)
                applied += count
            else:
                raw = raw.replace(old, new)
                applied += 1

        if raw != original:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(raw)
            print(f"  OK   {slug}: {applied} replacement(s)")
            total_applied += applied

    print(f"\nTotal replacements applied: {total_applied}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
