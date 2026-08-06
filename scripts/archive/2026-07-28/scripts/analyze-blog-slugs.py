#!/usr/bin/env python3
"""
Build the blog 01-50 -> semantic-slug mapping.
Read each blog's H1 and derive a clean slug.
"""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
BLOG = ROOT / "blog"

# Manual curated mapping (cleaner than auto-deriving; the H1 titles include year/category noise)
SLUG_MAP = {
    "01-restore-old-wedding-videos":        "restore-vhs-wedding-footage",
    "02-vhs-to-digital-wedding-cost":       "vhs-to-digital-wedding-cost",
    "03-ai-wedding-video-generator":        "ai-wedding-video-generator-guide",
    "04-wedding-video-from-photos":         "wedding-video-from-photos",
    "05-wedding-slow-motion-effect":        "wedding-slow-motion-effect",
    "06-honor-deceased-parent-wedding":     "honor-deceased-parent-wedding",
    "07-cinematic-wedding-trailer":         "cinematic-wedding-trailer-guide",
    "08-pet-wedding-videos":                "pet-wedding-videos",
    "09-include-remote-family-wedding-video": "include-remote-family-wedding-video",
    "10-multilingual-wedding-videos":       "multilingual-wedding-videos",
    "11-unique-wedding-video-ideas":        "unique-wedding-video-ideas",
    "12-wedding-video-formats":             "wedding-video-formats",
    "13-how-long-should-wedding-video-be":  "how-long-should-wedding-video-be",
    "14-wedding-video-vs-photos":           "wedding-video-vs-photos",
    "15-wedding-video-social-media":        "wedding-video-social-media",
    "16-raw-wedding-footage-ideas":         "raw-wedding-footage-ideas",
    "17-ai-wedding-video-industry":         "ai-wedding-video-industry",
    "18-ai-vs-human-wedding-editing":       "ai-vs-human-wedding-editing",
    "19-choose-wedding-videographer":       "choose-wedding-videographer",
    "20-wedding-highlight-reel":            "wedding-highlight-reel",
    "21-restore-old-wedding-photos":        "restore-old-wedding-photos",
    "22-elopement-video-ideas":             "elopement-video-ideas",
    "23-destination-wedding-video":         "destination-wedding-video",
    "24-wedding-video-music":               "wedding-video-music",
    "25-wedding-video-gift-ideas":          "wedding-video-gift-ideas",
    "26-wedding-anniversary-video-ideas":   "wedding-anniversary-video-ideas",
    "27-spring-wedding-video-trends":       "spring-wedding-video-trends",
    "28-christmas-wedding-video":           "christmas-wedding-video",
    "29-summer-wedding-video-tips":         "summer-wedding-video-tips",
    "30-what-to-do-with-wedding-video":     "what-to-do-with-wedding-video",
    "31-micro-wedding-video":               "micro-wedding-video",
    "32-share-wedding-video-with-family":   "share-wedding-video-with-family",
    "33-same-sex-wedding-video":            "same-sex-wedding-video",
    "34-vow-renewal-video":                 "vow-renewal-video",
    "35-wedding-video-for-parents":         "wedding-video-for-parents",
    "36-digitize-parents-wedding-video":    "digitize-parents-wedding-video",
    "37-fix-shaky-wedding-video":           "fix-shaky-wedding-video",
    "38-wedding-photo-slideshow":           "wedding-photo-slideshow",
    "39-wedding-video-subtitles":           "wedding-video-subtitles",
    "40-cartoon-wedding-video":             "cartoon-wedding-video",
    "41-wedding-memes":                     "wedding-memes",
    "42-wedding-video-music-guide":         "wedding-video-music-guide",
    "43-wedding-video-audio-fix":           "wedding-video-audio-fix",
    "44-wedding-video-timeline":            "wedding-video-timeline",
    "45-send-large-wedding-video":          "send-large-wedding-video",
    "46-weddingai-video-review":            "weddingai-video-review",
    "47-wedding-video-cost-2026":           "wedding-video-cost-2026",
    "48-skip-wedding-videographer":         "skip-wedding-videographer",
    "49-budget-wedding-video":              "budget-wedding-video",
    "50-weddingai-success-stories":         "weddingai-success-stories",
}

# Verify all 50 directories exist
existing = {p.name for p in BLOG.iterdir() if p.is_dir() and re.match(r"^\d{2}-", p.name)}
mapped = set(SLUG_MAP.keys())
missing_in_map = existing - mapped
missing_in_dir = mapped - existing

print(f"Total directories found: {len(existing)}")
print(f"Total mappings: {len(SLUG_MAP)}")
if missing_in_map:
    print(f"\n!! Directories NOT in SLUG_MAP (need manual slug): {missing_in_map}")
if missing_in_dir:
    print(f"\n!! Mappings NOT in directories: {missing_in_dir}")
if not missing_in_map and not missing_in_dir:
    print("\nOK: all 50 directories have a mapping")

# Also write a CSV for the report
import csv
csv_path = ROOT / "blog_slug_map.csv"
with csv_path.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["old_slug", "new_slug", "old_url", "new_url"])
    for old, new in sorted(SLUG_MAP.items()):
        w.writerow([old, new, f"/blog/{old}/", f"/blog/{new}/"])
print(f"\nWrote {csv_path}")
