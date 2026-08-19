"""
Replace 3 gallery cards' <picture>...</picture></div> blocks with <video>...</video></div>.

SAFER than the previous version: it operates on exactly TWO lines (the picture line and
the </picture></div> line), not on a multi-line span. This guarantees no cross-card
collisions even if the regex engine is greedy.

  Card 1: Ahmed & Layla   — hero-wedding-vineyard.png
  Card 2: Rodriguez       — catalog-celebrity-message.jpg
  Card 3: Mei & Jin       — wedding-trailer-sunset.png
"""
import io
import re
import sys

GALLERY = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai\gallery\index.html"

with io.open(GALLERY, "r", encoding="utf-8", newline="") as f:
    content = f.read()

# 3-card plan: each entry maps a UNIQUE fallback img src (the only thing that makes
# the picture block identifiable) to the new <video> block (with closing </div>).
replacements = [
    {
        "needle": "/images/hero-wedding-vineyard.png",
        "video": (
            '                            <video controls autoplay muted loop playsinline '
            'preload="none" width="1280" height="720" '
            'poster="/images/case-ahmed-layla-broadcast-poster.webp" '
            'aria-label="Ahmed &amp; Layla — full ceremony broadcast with picture-in-picture '
            'video blessings from family in Pakistan, London, and Egypt" data-lazy-video>\n'
            '                            <source src="/images/case-ahmed-layla-broadcast.webm?v=4.29" type="video/webm">\n'
            '                            <source src="/images/case-ahmed-layla-broadcast.mp4?v=4.29" type="video/mp4">\n'
            '                        </video></div>'
        ),
    },
    {
        "needle": "/images/catalog-celebrity-message.jpg",
        "video": (
            '                            <video controls autoplay muted loop playsinline '
            'preload="none" width="1280" height="720" '
            'poster="/images/case-rodriguez-glamorous-opener-poster.webp" '
            'aria-label="The Rodriguez family — Hollywood-style glamorous wedding opener, '
            'charming leading-man and leading-lady walking through a Mediterranean villa at golden hour" data-lazy-video>\n'
            '                            <source src="/images/case-rodriguez-glamorous-opener.webm?v=4.29" type="video/webm">\n'
            '                            <source src="/images/case-rodriguez-glamorous-opener.mp4?v=4.29" type="video/mp4">\n'
            '                        </video></div>'
        ),
    },
    {
        "needle": "/images/wedding-trailer-sunset.png",
        "video": (
            '                            <video controls autoplay muted loop playsinline '
            'preload="none" width="1280" height="720" '
            'poster="/images/case-mei-jin-celebrity-package-poster.webp" '
            'aria-label="Mei &amp; Jin — multiple celebrity style wedding package, leading-man '
            'entrance, comedic cake cutting, glamorous recessional wave" data-lazy-video>\n'
            '                            <source src="/images/case-mei-jin-celebrity-package.webm?v=4.29" type="video/webm">\n'
            '                            <source src="/images/case-mei-jin-celebrity-package.mp4?v=4.29" type="video/mp4">\n'
            '                        </video></div>'
        ),
    },
]

# Pattern: <picture>...<img src="NEEDLE"...
# then a newline
# then </picture></div>
# Use a non-greedy char class that excludes '<' so we don't span across tags,
# BUT picture inner has <source> and <img> so we DO need to allow <. The trick:
# anchor to the SPECIFIC needle src, which uniquely identifies one picture, then
# match only up to the next </picture></div> (with the same single-line constraint).
needle_escaped = lambda s: re.escape(s)
PAT = re.compile(
    r'<picture>(?:(?!</picture>).)*?src="(?P<src>[^"]+)"(?:(?!</picture>).)*?</picture></div>',
    re.DOTALL,
)

new_content = content
applied = 0
for spec in replacements:
    needle = spec["needle"]
    # Find candidate matches: only those where the picture's <img src> ends with our needle
    candidates = []
    for m in PAT.finditer(new_content):
        src = m.group("src")
        if src == needle:
            candidates.append(m)
    if len(candidates) != 1:
        print(f"ERROR: needle '{needle}' matched {len(candidates)} times, expected 1", file=sys.stderr)
        sys.exit(1)
    m = candidates[0]
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
    print("Normalized line endings back to CRLF")

with io.open(GALLERY, "w", encoding="utf-8", newline="") as f:
    f.write(new_content)

print(f"\nDone: 3 cards updated in {GALLERY}")
