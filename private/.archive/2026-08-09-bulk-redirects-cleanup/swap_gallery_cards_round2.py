"""
Replace 3 more gallery cards' <picture> blocks with <video> blocks.

Round 2 (continuation of round 1):
  Card A: Sarah & James (47 Photos, 4-Minute Cinematic Film) — catalog-ai-video-generator.jpg
  Card B: Anika & Dev   (Pre-Wedding AI Engagement Film)    — preset-romantic-soft.jpg
  Card C: Maria & David (3-Minute Sunset Trailer)            — catalog-wedding-trailer.jpg

Same pattern as round 1's swap_gallery_cards.py: find the <picture> by its
fallback <img src="NEEDLE">, swap with a <video data-lazy-video> block.
The negative-lookahead `</picture>` in the inner regex guarantees we don't
span across unrelated <picture> blocks.
"""
import io
import re
import sys

GALLERY = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai\gallery\index.html"

with io.open(GALLERY, "r", encoding="utf-8", newline="") as f:
    content = f.read()

replacements = [
    {
        "needle": "/images/catalog-ai-video-generator.jpg",
        "video": (
            '                            <video controls autoplay muted loop playsinline '
            'preload="none" width="1376" height="768" '
            'poster="/images/case-sarah-james-super8-poster.webp" '
            'aria-label="Sarah &amp; James — 47 hero photos animated into a 4-minute '
            'Super 8mm-style cinematic film, Brooklyn rooftop at golden hour" data-lazy-video>\n'
            '                            <source src="/images/case-sarah-james-super8.webm?v=4.29" type="video/webm">\n'
            '                            <source src="/images/case-sarah-james-super8.mp4?v=4.29" type="video/mp4">\n'
            '                        </video>'
        ),
    },
    {
        "needle": "/images/preset-romantic-soft.jpg",
        "video": (
            '                            <video controls autoplay muted loop playsinline '
            'preload="none" width="1376" height="768" '
            'poster="/images/case-anika-dev-save-the-date-poster.webp" '
            'aria-label="Anika &amp; Dev — pre-wedding AI engagement save-the-date film, '
            'South Asian couple in blush pink lehenga and cream sherwani on a flower-decorated swing in a Mumbai garden" data-lazy-video>\n'
            '                            <source src="/images/case-anika-dev-save-the-date.webm?v=4.29" type="video/webm">\n'
            '                            <source src="/images/case-anika-dev-save-the-date.mp4?v=4.29" type="video/mp4">\n'
            '                        </video>'
        ),
    },
    {
        "needle": "/images/catalog-wedding-trailer.jpg",
        "video": (
            '                            <video controls autoplay muted loop playsinline '
            'preload="none" width="1376" height="768" '
            'poster="/images/case-maria-david-sunset-trailer-poster.webp" '
            'aria-label="Maria &amp; David — 3-minute cinematic wedding trailer at golden hour '
            'sunset, Napa Valley vineyards, Hollywood-style color grading and slow motion" data-lazy-video>\n'
            '                            <source src="/images/case-maria-david-sunset-trailer.webm?v=4.29" type="video/webm">\n'
            '                            <source src="/images/case-maria-david-sunset-trailer.mp4?v=4.29" type="video/mp4">\n'
            '                        </video>'
        ),
    },
]

# Anchor on the fallback <img src="..."> inside the <picture>...</picture> block.
# Negative-lookahead `</picture>` prevents spanning across blocks.
PAT = re.compile(
    r'<picture>(?:(?!</picture>).)*?src="(?P<src>[^"]+)"(?:(?!</picture>).)*?</picture>',
    re.DOTALL,
)

new_content = content
applied = 0
for spec in replacements:
    needle = spec["needle"]
    matches = [m for m in PAT.finditer(new_content) if m.group("src") == needle]
    if len(matches) != 1:
        print(f"ERROR: needle '{needle}' matched {len(matches)} times, expected 1", file=sys.stderr)
        sys.exit(1)
    m = matches[0]
    new_content = new_content[: m.start()] + spec["video"] + new_content[m.end():]
    applied += 1
    print(f"OK: replaced picture with src={needle!r} at offset {m.start()}")

if applied != 3:
    print(f"ERROR: applied {applied} replacements, expected 3", file=sys.stderr)
    sys.exit(1)

# Preserve line endings.
has_crlf = "\r\n" in content
print(f"Original line endings: {'CRLF' if has_crlf else 'LF'}")
if has_crlf and "\r\n" not in new_content:
    new_content = new_content.replace("\n", "\r\n")

with io.open(GALLERY, "w", encoding="utf-8", newline="") as f:
    f.write(new_content)

print(f"\nDone: 3 cards updated in {GALLERY}")
