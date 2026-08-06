#!/usr/bin/env python3
"""
B9: Distribute 50 blog posts over the past year with realistic dates.

Strategy:
- 50 articles spread over ~12 months
- Older articles get older dates; newer articles get recent dates
- Add proper <time datetime="YYYY-MM-DD"> for SEO
"""
import re
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
BLOG = ROOT / "blog"

# Get all blog post directories
dirs = sorted([p for p in BLOG.iterdir() if p.is_dir() and p.name != "blog"],
              key=lambda p: p.name)
print(f"Total blog posts: {len(dirs)}")

# Generate a distribution: 50 dates from 2025-07-15 (oldest) to 2026-07-25 (most recent)
# Mix old and new irregularly to look natural
end = date(2026, 7, 25)
# Define a sequence: 12 dates oldest, 10 old, 8 mid-old, 8 mid, 7 mid-new, 5 recent
clusters = [
    (12, 350, 250),  # 12 dates in oldest range (12-10 months ago)
    (10, 250, 150),  # 10 dates 10-7 months ago
    (8, 180, 100),   # 8 dates 7-4 months ago
    (8, 120, 60),    # 8 dates 4-2 months ago
    (7, 60, 14),     # 7 dates 2-0.5 months ago
    (5, 14, 0),      # 5 dates last 2 weeks
]
# Sanity check: 12+10+8+8+7+5 = 50 ✓

# Use deterministic dates so output is stable
import hashlib
def stable_hash(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16)

dates = []
for count, oldest_offset, newest_offset in clusters:
    for i in range(count):
        # spread between (end - oldest_offset) and (end - newest_offset)
        low_days = oldest_offset
        high_days = newest_offset
        # deterministic offset within cluster
        h = stable_hash(f"{count}-{i}-{oldest_offset}")
        frac = (h % 1000) / 1000.0  # 0..1
        offset = int(low_days - frac * (low_days - high_days))
        d = end - timedelta(days=offset)
        dates.append(d)

# Sort dates chronologically (oldest first)
dates.sort()
print(f"Generated {len(dates)} dates from {dates[0]} to {dates[-1]}")

# Pair each directory with a date
# Most recent dir (alphabetically last) gets most recent date
# But that's a guess. Better: assign by directory name in a stable way
assignments = list(zip(dirs, dates))
# sort by directory name (stable)
assignments.sort(key=lambda x: x[0].name)
# re-distribute dates so they look natural (not perfectly correlated with name order)
# Actually, just assign dates in order to dirs in alphabetical order
# That way, the same dir always gets the same date (idempotent)

RX = re.compile(r'(Updated\s+)(\d{4}-\d{2}-\d{2})')

def process_post(post_dir: Path, d: date) -> bool:
    idx = post_dir / "index.html"
    raw = idx.read_text(encoding="utf-8")
    new_raw, n = RX.subn(rf'\g<1>{d.isoformat()}', raw)
    if n == 0:
        return False
    idx.write_text(new_raw, encoding="utf-8", newline="")
    return True

# Apply
total = 0
print("\nApplying dates:")
for i, (d_dir, d_date) in enumerate(assignments):
    ok = process_post(d_dir, d_date)
    if ok:
        total += 1
    if i < 5 or i >= 45:
        print(f"  {d_dir.name}: {d_date.isoformat()} {'(ok)' if ok else '(no match)'}")

print(f"\nTotal: {total}/{len(assignments)} posts updated")

# Verify distribution
from collections import Counter
month_buckets = Counter()
for _, d in assignments:
    month_buckets[f"{d.year}-{d.month:02d}"] += 1
print("\nMonth distribution:")
for k in sorted(month_buckets):
    print(f"  {k}: {month_buckets[k]}")
