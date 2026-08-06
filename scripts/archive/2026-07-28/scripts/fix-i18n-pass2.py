#!/usr/bin/env python3
"""
Content rewrites in en.json + new i18n keys for the homepage refactor.
"""
import json
from pathlib import Path

EN = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai\i18n\en.json")

data = json.loads(EN.read_text(encoding="utf-8"))

# 1. Mike & Rachel new testimonial text (replaces the old real-time editing one)
# Old: "The real-time editing at our reception was a game changer..."
old_key = "index.p_text.the_real_time_editing_at_our_reception.87089643"
new_key = "index.p_text.mike_rachel_first_dance_slow_motion.NEW003"
if old_key in data:
    val = data.pop(old_key)
    data[new_key] = (
        "Watching our first dance at 120fps, the way the veil floated and her face "
        "lit up \u2014 slow motion caught moments we didn't even know happened. "
        "It's our most-watched video."
    )
    print(f"  replaced {old_key[:60]}... -> {new_key}")

# 2. Mike & Rachel Schema review body
# This is inside a JSON-LD script in index.html, not in en.json, so we keep en.json only synced to the visible testimonial.

# 3. Carolina testimonial trim
# Keep existing key but the visible HTML has been rewritten; en.json value needs to match for the English-text fallback.
# New: "When Mamá's 1985 photo came alive in our wedding film, our whole table burst into tears. The most beautiful tribute. Read her full story on the Family Tribute page."
carolina_key = "index.p_text.mam_passed_away_two_months_before_our_w.79329689"
if carolina_key in data:
    data[carolina_key] = (
        "When Mam\u00e1's 1985 photo came alive in our wedding film, our whole table "
        "burst into tears. The most beautiful tribute. Read her full story on the "
        "Family Tribute page."
    )
    print(f"  trimmed {carolina_key[:60]}...")

# 4. New keys for the merged Real Weddings section
data["index.h2_text.real_weddings_real_stories.NEW001"] = "Real Weddings, Real Stories"
data["index.p_text.real_weddings_intro.NEW002"] = (
    "A glimpse of the 25 weddings we've helped preserve. "
    "Click any story to see the full case study."
)
print("  added 2 new keys for merged featured section")

# 5. Mark old "Real Results, Real Love Stories" H2 + "Featured Case Studies" H2 as not used (still in en.json for safety)
# No deletion — keys unused doesn't hurt.

EN.write_text(
    json.dumps(data, ensure_ascii=False, indent=1, separators=(",", ": ")),
    encoding="utf-8",
    newline="\n",
)
print(f"\n  en.json updated: {len(data)} keys total")
