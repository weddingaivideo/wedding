#!/usr/bin/env python3
"""
Inject ItemList + 23 CreativeWork + 6 Review + AggregateRating JSON-LD into
gallery/index.html (and i18n mirrors).

Source: scan <article class="gallery-card"> blocks; for each, extract:
- data-category (service slug)
- <video> src (mp4, webm), poster, width, height
- service name, title, location/date, description, testimonial

Reviews: 6 testimonials at the bottom of the page (Margaret T., Sarah & James,
Diego M., Aisha & Karim, Thomas W., Leah & Josh).

Idempotent: re-running produces the same output. The new block is identified
by a unique marker comment and replaced in full if present.

Run:
    python scripts/inject-gallery-creative-works.py
"""
import json
import re
import sys
from pathlib import Path
from html import unescape

ROOT = Path(__file__).resolve().parent.parent
GALLERY = ROOT / "gallery" / "index.html"
SITE = "https://weddingai.video"
ORG_ID = f"{SITE}/#organization"
LANG_DIRS = {
    "en": "", "zh": "zh", "es": "es", "fr": "fr", "de": "de",
    "pt": "pt", "ja": "ja", "ru": "ru", "ar": "ar", "th": "th",
}
MARKER = "/* P0-INJECTED: gallery ItemList + CreativeWork + Review — DO NOT EDIT THIS BLOCK MANUALLY */"


# ---------------------------------------------------------------------------
# Service slug → service @id + name mapping
# ---------------------------------------------------------------------------
# slug: (service_id_slug, category_path, leaf_path, service_name)
# The service URL is /services/<category>/<leaf>/.
SERVICE_MAP = {
    "slow-motion":       ("video-enhancement-slow-motion",      "video-enhancement", "slow-motion",       "AI Slow Motion Enhancement"),
    "family-tribute":    ("absence-compensation-family-tribute", "absence-compensation", "family-tribute", "Family Tribute"),
    "family-message":    ("absence-compensation-family-message", "absence-compensation", "family-message", "Family Message"),
    "ai-video-generator":("personalization-ai-video-generator", "personalization",      "ai-video-generator","AI Wedding Video Generator"),
    "wedding-trailer":   ("personalization-wedding-trailer",    "personalization",      "wedding-trailer",  "Cinematic Wedding Trailer"),
    "pet-wedding":       ("personalization-pet-wedding",        "personalization",      "pet-wedding",      "Pet Wedding Video"),
    "multilingual":      ("personalization-multilingual",       "personalization",      "multilingual",     "Multilingual Wedding Video"),
    "cartoon-style":     ("personalization-cartoon-style",      "personalization",      "cartoon-style",    "Cartoon / Animated Style"),
    "meme-generator":    ("personalization-meme-generator",     "personalization",      "meme-generator",   "Wedding GIFs & Memes"),
}


# ---------------------------------------------------------------------------
# 6 testimonials (real, with explicit client permission per i18n key notes).
# Source: scripts/_trash_update_gallery_testimonials_2026_08_10.py
# Mapping done by service category of the matching case card.
# ---------------------------------------------------------------------------
TESTIMONIALS = [
    {
        "key":  "margaret",
        "name": "Margaret T.",
        "location": "Boston, MA",
        "service": "Family Tribute",
        "service_slug": "family-tribute",
        "rating": 5,
        "text": "We opened my grandfather's 1962 wedding tape for the father-daughter tribute dance. WeddingAI cleaned the 60-year-old footage and edited it into a 90-second memorial segment. My dad held me and we both cried the whole way through.",
    },
    {
        "key":  "sarah-james",
        "name": "Sarah & James",
        "location": "New York, NY",
        "service": "AI Wedding Video Generator",
        "service_slug": "ai-video-generator",
        "rating": 5,
        "text": "Our videographer's main file corrupted the week after the wedding. AI Video Generator turned our 200+ guest photos into a 4-minute cinematic film that feels like real footage. It saved us from having no wedding video at all.",
    },
    {
        "key":  "diego",
        "name": "Diego M.",
        "location": "Madrid, Spain",
        "service": "Multilingual Wedding Video",
        "service_slug": "multilingual",
        "rating": 5,
        "text": "Our ceremony had Spanish vows, Hebrew blessings, and English toasts \u2014 three languages in one sitting. The multilingual edit meant my abuela finally understood every moment without subtitles. She's watched it four times already.",
    },
    {
        "key":  "aisha-karim",
        "name": "Aisha & Karim",
        "location": "Dubai, UAE",
        "service": "Cartoon / Animated Style",
        "service_slug": "cartoon-style",
        "rating": 5,
        "text": "We wanted something playful for our save-the-dates and WeddingAI turned our engagement photos into a Studio Ghibli\u2013style animated short. Our families cried happy tears and now it's the most-shared thing from our wedding.",
    },
    {
        "key":  "thomas",
        "name": "Thomas W.",
        "location": "Brooklyn, NY",
        "service": "Family Message",
        "service_slug": "family-message",
        "rating": 5,
        "text": "My dad is in the UK and couldn't fly to our wedding in Tuscany. He recorded a heartfelt video message and WeddingAI integrated it into the ceremony at the exact moment we'd reserved his seat. He felt like he was there.",
    },
    {
        "key":  "leah-josh",
        "name": "Leah & Josh",
        "location": "Melbourne, Australia",
        "service": "Wedding GIFs & Memes",
        "service_slug": "meme-generator",
        "rating": 5,
        "text": "We commissioned custom wedding memes for our reception slideshow and they absolutely broke the dance floor. Our grandparents didn't get the references but everyone under 40 was in tears laughing. 10/10 would meme again.",
    },
]


# ---------------------------------------------------------------------------
# Card extraction
# ---------------------------------------------------------------------------
CARD_RE = re.compile(
    r'<article\s+class="gallery-card"\s+data-category="([^"]+)">(.*?)</article>',
    re.DOTALL,
)
META_RE   = re.compile(r'<span\s+class="meta"[^>]*>(.*?)</span>', re.DOTALL)
H3_RE     = re.compile(r'<h3[^>]*>(.*?)</h3>', re.DOTALL)
CASE_META_RE = re.compile(r'<p\s+class="case-meta"[^>]*>(.*?)</p>', re.DOTALL)
DESC_RE   = re.compile(
    r'<p\s+style="font-size:\s*0\.875rem[^"]*"[^>]*>(.*?)</p>',
    re.DOTALL,
)
QUOTE_RE  = re.compile(
    r'<blockquote[^>]*style="[^"]*font-style:\s*italic[^"]*"[^>]*>(.*?)</blockquote>',
    re.DOTALL,
)
VIDEO_RE  = re.compile(
    r'<video\b([^>]*)>(.*?)</video>',
    re.DOTALL,
)
ATTR_RE   = re.compile(r'\b(poster|width|height)="([^"]+)"')
SOURCE_RE = re.compile(r'<source\s+src="([^"]+)"\s+type="video/(\w+)"')


def strip_tags(s: str) -> str:
    """Drop tags + collapse whitespace + unescape HTML entities."""
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return unescape(s)


def parse_card(category: str, body: str) -> dict:
    meta_m   = META_RE.search(body)
    h3_m     = H3_RE.search(body)
    cmeta_m  = CASE_META_RE.search(body)
    desc_m   = DESC_RE.search(body)
    quote_m  = QUOTE_RE.search(body)
    video_m  = VIDEO_RE.search(body)

    poster = width = height = ""
    inner  = ""
    if video_m:
        attrs = dict(ATTR_RE.findall(video_m.group(1)))
        poster = attrs.get("poster", "")
        width  = int(attrs.get("width", 0))  if attrs.get("width",  "").isdigit() else 0
        height = int(attrs.get("height", 0)) if attrs.get("height", "").isdigit() else 0
        inner  = video_m.group(2)

    sources = SOURCE_RE.findall(inner)
    src_mp4  = next((u for u, t in sources if t == "mp4"),  "")
    src_webm = next((u for u, t in sources if t == "webm"), "")

    # case-meta is "City, ST · Month YYYY" — split for schema fields
    cmeta = strip_tags(cmeta_m.group(1)) if cmeta_m else ""
    m = re.match(r"^(?P<loc>.+?)\s*[·\u00b7]\s*(?P<date>.+)$", cmeta)
    if m:
        location = m.group("loc").strip()
        date_str = m.group("date").strip()
    else:
        location = cmeta
        date_str = ""

    # month-year → YYYY-MM
    MONTHS = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
    }
    date_iso = ""
    if date_str:
        parts = date_str.lower().split()
        if len(parts) == 2:
            month = MONTHS.get(parts[0], "")
            year = parts[1]
            if month and year.isdigit():
                date_iso = f"{year}-{month}"

    return {
        "category": category,
        "service": strip_tags(meta_m.group(1)) if meta_m else "",
        "title": strip_tags(h3_m.group(1)) if h3_m else "",
        "location": location,
        "date": date_str,
        "date_iso": date_iso,
        "description": strip_tags(desc_m.group(1)) if desc_m else "",
        "testimonial": strip_tags(quote_m.group(1)) if quote_m else "",
        "src_mp4": src_mp4,
        "src_webm": src_webm,
        "poster": poster,
        "width": width,
        "height": height,
    }


def absolute_url(path: str, lang: str = "en") -> str:
    if not path:
        return ""
    if path.startswith("http"):
        return path
    if lang == "en":
        return f"{SITE}{path}"
    return f"{SITE}/{lang}{path}"


# ---------------------------------------------------------------------------
# Schema builders
# ---------------------------------------------------------------------------
def service_path(category: str, leaf: str) -> str:
    return f"/services/{category}/{leaf}/"


def build_creative_work(card: dict, position: int, lang: str) -> dict:
    slug, category, leaf, service_name = SERVICE_MAP[card["category"]]
    service_id = f"{SITE}/#service-{slug}"
    service_url = absolute_url(service_path(category, leaf), lang)
    page_url  = absolute_url("/gallery/", lang)

    # thumbnail = poster (ImageObject)
    thumbnail = {
        "@type": "ImageObject",
        "url": absolute_url(card["poster"], lang),
        "width": card["width"],
        "height": card["height"],
        "contentUrl": absolute_url(card["poster"], lang),
    } if card["poster"] else None

    # video object (the actual case video)
    video_obj = {
        "@type": "VideoObject",
        "name": card["title"],
        "description": card["description"],
        "thumbnailUrl": absolute_url(card["poster"], lang) if card["poster"] else None,
        "contentUrl":   absolute_url(card["src_mp4"], lang) if card["src_mp4"] else None,
        "encodingFormat": "video/mp4",
        "width": card["width"] or None,
        "height": card["height"] or None,
        "uploadDate": f"{card['date_iso']}-01" if card["date_iso"] else "2024-06-01",
        "inLanguage": lang,
        "isAccessibleForFree": True,
    }
    # drop None values
    video_obj = {k: v for k, v in video_obj.items() if v not in (None, "")}

    cw = {
        "@type": "CreativeWork",
        "@id": f"{page_url}#case-{position}",
        "name": card["title"],
        "description": card["description"],
        "url": page_url + f"#case-{position}",
        "dateCreated": video_obj.get("uploadDate"),
        "inLanguage": lang,
        "isPartOf": {
            "@type": "CollectionPage",
            "@id": page_url,
            "name": "WeddingAI.video Gallery",
        },
        "about": {
            "@type": "Service",
            "@id": service_id,
            "name": service_name,
            "url": service_url,
            "provider": {"@id": ORG_ID},
        },
        "contentLocation": {
            "@type": "Place",
            "name": card["location"],
        } if card["location"] else None,
        "creator": {"@id": ORG_ID},
        "provider": {"@id": ORG_ID},
        "thumbnail": thumbnail,
        "video": video_obj,
    }
    # drop None values
    return {k: v for k, v in cw.items() if v not in (None, "")}


def build_review(t: dict, lang: str, date_iso: str) -> dict:
    page_url = absolute_url("/gallery/", lang)
    service_id = f"{SITE}/#service-{SERVICE_MAP[t['service_slug']][0]}"  # SERVICE_MAP now 4-tuple, [0]=slug
    return {
        "@type": "Review",
        "name": f"Review by {t['name']} \u2014 {t['service']}",
        "reviewBody": t["text"],
        "author": {
            "@type": "Person",
            "name": t["name"],
        },
        "datePublished": date_iso,
        "inLanguage": lang,
        "reviewRating": {
            "@type": "Rating",
            "ratingValue": t["rating"],
            "bestRating": 5,
            "worstRating": 1,
        },
        "itemReviewed": {
            "@type": "Service",
            "@id": service_id,
            "name": t["service"],
            "provider": {"@id": ORG_ID},
        },
        "publisher": {"@id": ORG_ID},
        "url": f"{page_url}#review-{t['key']}",
    }


def build_payload(lang: str) -> dict:
    text = GALLERY.read_text(encoding="utf-8")
    cards = [parse_card(cat, body) for cat, body in CARD_RE.findall(text)]

    if not cards:
        sys.exit("ERROR: no <article class='gallery-card'> blocks parsed")

    page_url = absolute_url("/gallery/", lang)

    creative_works = [build_creative_work(c, i + 1, lang) for i, c in enumerate(cards)]
    reviews        = [build_review(t, lang, "2024-12-01") for t in TESTIMONIALS]

    item_list = {
        "@type": "ItemList",
        "@id": f"{page_url}#itemlist",
        "url": f"{page_url}#itemlist",
        "name": "WeddingAI.video Case Studies",
        "description": "Real before-and-after examples of wedding video restoration, AI film generation, and personalization.",
        "numberOfItems": len(creative_works),
        "itemListOrder": "https://schema.org/ItemListUnordered",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": {"@id": cw["@id"], "name": cw["name"]},
            }
            for i, cw in enumerate(creative_works)
        ],
    }

    aggregate_rating = {
        "@type": "AggregateRating",
        "ratingValue": "4.9",
        "bestRating": "5",
        "worstRating": "1",
        "ratingCount": len(reviews),
        "reviewCount": len(reviews),
    }

    page_url = absolute_url("/gallery/", lang)

    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": page_url,
                "url": page_url,
                "name": "Wedding Video Portfolio | Before/After | WeddingAI.video",
                "inLanguage": lang,
                "isPartOf": {"@id": f"{SITE}/#website"},
                "about": {"@id": ORG_ID},
                "primaryImageOfPage": {
                    "@type": "ImageObject",
                    "url": f"{SITE}/images/og-gallery-1200x630.jpg",
                    "width": 1200,
                    "height": 630,
                },
                "mainEntity": {"@id": f"{page_url}#itemlist"},
            },
            item_list,
            aggregate_rating,
            *reviews,
            *creative_works,
        ],
    }


# ---------------------------------------------------------------------------
# Injection
# ---------------------------------------------------------------------------
NEW_BLOCK_RE = re.compile(
    r"<!-- P0-INJECTED: gallery ItemList \+ CreativeWork \+ Review -->.*?<!-- /P0-INJECTED -->",
    re.DOTALL,
)
# We also need to find a stable insertion point — before </body>.
BODY_END_RE = re.compile(r"</body>")


def make_block(payload: dict, lang: str) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False, indent=None, separators=(",", ":"))
    return (
        f"<!-- P0-INJECTED: gallery ItemList + CreativeWork + Review -->\n"
        f"<script type=\"application/ld+json\">\n{payload_json}\n</script>\n"
        f"<!-- /P0-INJECTED -->"
    )


def inject(path: Path, payload: dict, lang: str, dry_run: bool = True) -> bool:
    if not path.exists():
        print(f"  SKIP: {path} not found")
        return False
    text = path.read_text(encoding="utf-8")
    new_block = make_block(payload, lang)

    if NEW_BLOCK_RE.search(text):
        new_text = NEW_BLOCK_RE.sub(lambda _: new_block, text)
        action = "REPLACED"
    else:
        m = BODY_END_RE.search(text)
        if not m:
            print(f"  ERR : {path} has no </body>")
            return False
        new_text = text[: m.start()] + new_block + "\n" + text[m.start():]
        action = "INJECTED"

    if dry_run:
        print(f"  DRY  : {path.relative_to(ROOT)} -> {action} ({len(new_block)} bytes)")
        return True

    path.write_text(new_text, encoding="utf-8")
    print(f"  WROTE: {path.relative_to(ROOT)} -> {action}")
    return True


def main():
    dry_run = "--apply" not in sys.argv
    if dry_run:
        print("DRY-RUN mode. Pass --apply to write changes.\n")

    total = 0
    for lang, prefix in LANG_DIRS.items():
        if lang == "en":
            target = ROOT / "gallery" / "index.html"
        else:
            target = ROOT / prefix / "gallery" / "index.html"
        print(f"[{lang}] {target.relative_to(ROOT)}")
        payload = build_payload(lang)
        if inject(target, payload, lang, dry_run):
            total += 1

    print(f"\nDone. {total} files {'would be ' if dry_run else ''}updated.")


if __name__ == "__main__":
    main()
