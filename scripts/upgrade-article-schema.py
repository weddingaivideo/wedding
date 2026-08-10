#!/usr/bin/env python3
"""
Upgrade every Article JSON-LD across blog posts (and any other pages that
declare @type:Article) to add:

  - speakable: SpeakableSpecification targeting the article summary CSS hook
  - articleSection: derived from the headline + keywords (best match in the
                    keyword map; falls back to "Wedding Video")
  - mainEntityOfPage.inLanguage: synced from the top-level inLanguage

Idempotent. Only fills fields that are missing — never overwrites user values.
Skips internal/recon directories.

Run:
    python scripts/upgrade-article-schema.py         # dry-run
    python scripts/upgrade-article-schema.py --apply # write
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://weddingai.video"

SCRIPT_RE = re.compile(
    r'(<script type="application/ld\+json"[^>]*>)(.*?)(</script>)',
    re.DOTALL,
)
HAS_ARTICLE = re.compile(r'"@type"\s*:\s*"Article"')

# Speakable: target the meta description and the first H1/H2 block on the page.
# This is the standard pattern Google uses for voice/AI snippet extraction.
DEFAULT_SPEAKABLE = {
    "@type": "SpeakableSpecification",
    "cssSelector": [
        "head > title",
        'head > meta[name="description"]',
        "h1",
        ".article-summary",
        ".article-excerpt",
        "article > p:first-of-type",
    ],
}

# Keyword -> ArticleSection. First match wins. Order matters: more specific
# rules first so "ai-wedding-video-workflow" maps to "AI Wedding Video" and
# not to a generic "Wedding Video".
KEYWORD_SECTIONS = [
    # (regex against the combined headline + keywords text, section)
    (r"\bai[\s\-]?wedding[\s\-]?video\b|\bai[\s\-]?generator\b|\bai[\s\-]?film\b|\bai[\s\-]?editing\b", "AI Wedding Video"),
    (r"\bvintage\b|\brestor(?:ation|ed?)\b|\bvhs\b|\b8mm\b|\bhi[\s\-]?8\b|\bmini[\s\-]?dv\b|\bfilm[\s\-]?restoration\b", "Vintage Restoration"),
    (r"\bslow[\s\-]?motion\b|\bslowmo\b|\b120fps\b|\b60fps\b", "Slow Motion"),
    (r"\btrailer\b", "Wedding Trailer"),
    (r"\bpet\b|\bdog\b|\bcat\b", "Pet Wedding"),
    (r"\bmultilingual\b|\bdub(?:bed|bing)?\b|\bsubtitle\b|\blanguages?\b|\btranslator\b", "Multilingual Wedding Video"),
    (r"\bcartoon\b|\banime\b|\bghibli\b|\bpixar\b|\banimat(?:ed?|ion)\b", "Cartoon / Animated Style"),
    (r"\bmeme\b|\bgif\b", "Wedding Memes"),
    (r"\btribute\b|\bmemorial\b|\bhono(?:u?r|red)\b|\babsence\b|\bin[\s\-]?memoriam\b", "Family Tribute"),
    (r"\bremote\b|\bfamily[\s\-]?message\b|\bcouldn[\'’]t attend\b|\bcouldn[\'’]t fly\b|\bcan[\'’]t attend\b", "Family Message"),
    (r"\bcost\b|\bprice\b|\bpricing\b|\bbudget\b|\bcheap\b|\baffordabl", "Pricing & Cost"),
    (r"\bmusic\b|\bsong\b|\bsoundtrack\b", "Wedding Music"),
    (r"\binvitation\b|\bsave[\s\-]?the[\s\-]?date\b", "Wedding Invitation"),
    (r"\bproposal\b|\bengagement\b", "Engagement & Proposal"),
    (r"\banniversary\b", "Anniversary"),
    (r"\bvow[\s\-]?renewal\b", "Vow Renewal"),
    (r"\belopement\b", "Elopement"),
    (r"\bdestination\b", "Destination Wedding"),
    (r"\bspring\b|\bsummer\b|\bautumn\b|\bfall\b|\bwinter\b|\bchristmas\b|\bholiday\b", "Seasonal"),
    (r"\bsame[\s\-]?sex\b|\blgbtq\b", "LGBTQ+ Wedding"),
    (r"\bhighlight(?:\s+reel)?\b|\brecap\b", "Highlight Reel"),
    (r"\bslideshow\b", "Slideshow"),
    (r"\bcountdown\b", "Wedding Countdown"),
    (r"\bprivacy\b|\bdata\b|\bgdpr\b", "Privacy & Data"),
    (r"\bphotos?\b|\bphoto[\s\-]?to[\s\-]?video\b", "Photo-to-Video"),
    (r"\bphotographer\b|\bvideographer\b", "Videography"),
    (r"\btypes?\b|\bkinds?\b", "Wedding Video Types"),
    (r"\binspiration\b|\bideas\b|\btips\b|\bguide\b", "Inspiration & Tips"),
    (r"\bwedding[\s\-]?video\b", "Wedding Video"),
]
DEFAULT_SECTION = "Wedding Video"


def infer_section(article: dict) -> str:
    # Only inspect title-shaped signals: headline + keywords. We deliberately
    # avoid the meta description because it tends to mention competitor
    # services ("compare to vintage", "perfect for restoration") and would
    # pull a price/pricing article into "Vintage Restoration" by accident.
    headline = (article.get("headline") or "").lower()
    keywords = (article.get("keywords") or "").lower()
    # The url slug is also a strong signal (it's human-written and not
    # stuffed with competitor keywords).
    mep = article.get("mainEntityOfPage") or {}
    slug = ""
    if isinstance(mep, dict):
        slug = (mep.get("@id") or "").lower()
    blob = " ".join([headline, keywords, slug])
    for pattern, section in KEYWORD_SECTIONS:
        if re.search(pattern, blob, re.IGNORECASE):
            return section
    return DEFAULT_SECTION


def upgrade_article(article: dict) -> int:
    added = 0
    if article.get("@type") != "Article":
        return 0

    if "speakable" not in article:
        article["speakable"] = dict(DEFAULT_SPEAKABLE)
        added += 1

    if "articleSection" not in article:
        article["articleSection"] = infer_section(article)
        added += 1

    mep = article.get("mainEntityOfPage")
    if isinstance(mep, dict) and "inLanguage" not in mep:
        lang = article.get("inLanguage", "en")
        mep["inLanguage"] = lang
        added += 1

    return added


def process_file(path: Path, dry_run: bool) -> tuple[int, int]:
    """Returns (num_articles, num_fields_added)."""
    text = path.read_text(encoding="utf-8")
    articles = fields = 0

    def replace(match: re.Match) -> str:
        nonlocal articles, fields
        open_tag, body, close_tag = match.group(1), match.group(2), match.group(3)
        if not HAS_ARTICLE.search(body):
            return match.group(0)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return match.group(0)

        nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
        changed = False
        for node in nodes:
            if isinstance(node, dict) and node.get("@type") == "Article":
                n = upgrade_article(node)
                if n:
                    fields += n
                    articles += 1
                    changed = True

        if not changed:
            return match.group(0)
        new_body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return f"{open_tag}{new_body}{close_tag}"

    new_text = SCRIPT_RE.sub(replace, text)
    if dry_run or new_text == text:
        return articles, fields
    path.write_text(new_text, encoding="utf-8")
    return articles, fields


def main():
    dry_run = "--apply" not in sys.argv
    if dry_run:
        print("DRY-RUN mode. Pass --apply to write changes.\n")

    SKIP_DIRS = ("tmp", "private", "scripts", "tests", "qa", "internal-tools", "tools")
    candidates = []
    for p in ROOT.rglob("*.html"):
        if not p.is_file():
            continue
        if any(seg in p.relative_to(ROOT).parts for seg in SKIP_DIRS):
            continue
        if HAS_ARTICLE.search(p.read_text(encoding="utf-8", errors="ignore")):
            candidates.append(p)
    candidates.sort()

    total_files = total_articles = total_fields = 0
    for p in candidates:
        arts, n = process_file(p, dry_run)
        if arts == 0:
            continue
        rel = p.relative_to(ROOT)
        verb = "DRY  " if dry_run else "WROTE"
        print(f"  {verb}: {rel}  ({arts} articles, {n} new fields)")
        total_files += 1
        total_articles += arts
        total_fields += n

    print(f"\nDone. {total_files} files, {total_articles} articles, "
          f"{total_fields} fields {'would be ' if dry_run else ''}added.")


if __name__ == "__main__":
    main()
