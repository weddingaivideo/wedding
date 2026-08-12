"""Diversify the hardcoded 2026-08-01 publish dates in static blog HTML.

Background
----------
On 2026-08-01, generate-blog.py stamped all 50 newly-generated blog posts
with datePublished=2026-08-01 (TODAY at generation time). Google sees 50
posts with identical publish date, which looks suspicious / spammy and
may trigger a "we noticed that all your articles are from the same day"
manual action.

The middleware (functions/_middleware.js#diversifyArticleDates) already
rewrites individual post pages' JSON-LD datePublished at request time,
using a stable per-URL hash to spread the dates across a 60-day window
ending today. But:

  1. The static HTML source still has "2026-08-01" hardcoded, so anyone
     who curls the file, reads view-source, or runs a static audit sees
     the bad dates.

  2. The blog index (/blog/) has an ItemList with 50 nested Article
     items, all "datePublished":"2026-08-01". The middleware did NOT
     recurse into ItemList before, so the live HTTP response still
     showed all 50 posts as 2026-08-01 in the listing.

  3. The visible card text on /blog/ had hardcoded "11 min read · Aug
     1, 2026" in the HTML fallback for the 50 new posts.

The middleware now handles 2 + 3 (see functions/_middleware.js). This
script fixes 1 (the source HTML) so view-source / static audits / new
deploys all show diversified dates from the start.

Usage
-----
  python private/diversify-blog-dates.py              # apply changes
  python private/diversify-blog-dates.py --dry-run    # show diffs only

Idempotent: only touches dates that are still "2026-08-01" or
"2026-08-04" (the original generated values), so re-running is safe.
After this script, the middleware will overwrite with its own
diversified dates at request time, but the source will already be
clean.
"""
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent

# Languages with static blog post pages. Russian is excluded (no /ru/
# directory in the repo; served via middleware i18n only).
LANGS = ["", "zh", "es", "fr", "de", "pt", "ja", "ar", "th"]

# Match the middleware's diversification window: 60 days back, capped at
# today. See functions/_middleware.js (diversifyArticleDates).
SIXTY_DAYS_MS = 60 * 86400000

# Anchor "today" in UTC, matches the middleware's Date.now() interpretation.
NOW_MS = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
TODAY_MS = NOW_MS - (NOW_MS % 86400000)
OLDEST_MS = TODAY_MS - SIXTY_DAYS_MS

# Months used to format visible card dates in en ("Aug 1, 2026").
MONTHS_EN = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def hash_to_date(url_path: str) -> datetime:
    """Mirror functions/_middleware.js diversifyArticleDates hash logic.

    Returns a timezone-aware datetime in UTC, distributed across the
    past 60 days. Same URL always returns the same date.
    """
    h = 0
    for c in url_path:
        # JS `| 0` is 32-bit signed. We replicate that with mask + sign.
        raw = (h * 31 + ord(c)) & 0xFFFFFFFF
        if raw >= 0x80000000:
            h = raw - 0x100000000
        else:
            h = raw
    seed = abs(h) % 10000
    fraction = seed / 10000
    new_date_ms = OLDEST_MS + int(fraction * SIXTY_DAYS_MS)
    capped_date_ms = min(new_date_ms, TODAY_MS)
    return datetime.fromtimestamp(capped_date_ms / 1000, tz=timezone.utc)


def mod_date_for(url_path: str, pub_dt: datetime) -> datetime:
    """dateModified = datePublished + 1-3 days, capped at today.

    Mirrors the middleware's mod-offset logic (modOffset = 1 + (abs(h*7) % 3)).
    """
    h = 0
    for c in url_path:
        raw = (h * 31 + ord(c)) & 0xFFFFFFFF
        if raw >= 0x80000000:
            h = raw - 0x100000000
        else:
            h = raw
    mod_offset = 1 + (abs(h * 7) % 3)
    pub_ms = int(pub_dt.timestamp() * 1000)
    new_mod_ms = min(pub_ms + mod_offset * 86400000, TODAY_MS)
    return datetime.fromtimestamp(new_mod_ms / 1000, tz=timezone.utc)


def fmt_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def fmt_en(dt: datetime) -> str:
    return f"{MONTHS_EN[dt.month - 1]} {dt.day}, {dt.year}"


def read_file_preserve_bom(path: Path) -> tuple[bytes, str]:
    """Read a file as UTF-8, separating BOM from content."""
    raw = path.read_bytes()
    if raw[:3] == b"\xef\xbb\xbf":
        return b"\xef\xbb\xbf", raw[3:].decode("utf-8")
    return b"", raw.decode("utf-8")


def write_file_preserve_line_endings(path: Path, bom: bytes, text: str) -> None:
    """Write text back as UTF-8 with original BOM and matching line endings.

    The repo uses `*.html text eol=lf` in .gitattributes, so most HTML
    files in the index are LF. But some files (wedding-photos-vs-video,
    blog/index.html, etc.) were committed with CRLF — likely because
    the original author was on Windows or used an editor that
    auto-CRLF'd. We detect the dominant line ending in the source and
    preserve it on write, so we never introduce a line-ending change.
    """
    # Detect dominant line ending: count CR-LF vs bare-LF. If both
    # patterns are present, CRLF wins (it's the "stronger" form). If
    # only bare-LF, use LF. If only CR-LF, use CRLF.
    crlf_count = text.count("\r\n")
    lf_only_count = text.count("\n") - crlf_count
    if crlf_count >= lf_only_count and crlf_count > 0:
        # Normalize to CRLF.
        normalized = text.replace("\r\n", "\n").replace("\n", "\r\n")
    else:
        # Normalize to LF.
        normalized = text.replace("\r\n", "\n")
    path.write_bytes(bom + normalized.encode("utf-8"))


# ----------------------------------------------------------------------
# Individual post pages: 9 langs × 50 posts = 450 files
# ----------------------------------------------------------------------

def get_new_post_slugs() -> list[str]:
    """The 50 posts that were batch-generated on 2026-08-01.

    Detection: any directory under /blog/ whose index.html has
    datePublished="2026-08-01" (the old generated stamp).
    """
    blog_dir = ROOT / "blog"
    slugs = []
    for d in sorted(blog_dir.iterdir()):
        if not d.is_dir():
            continue
        idx = d / "index.html"
        if not idx.exists():
            continue
        content = (idx.read_bytes()[3:] if idx.read_bytes()[:3] == b"\xef\xbb\xbf"
                   else idx.read_bytes()).decode("utf-8")
        if '"datePublished":"2026-08-01"' in content:
            slugs.append(d.name)
    return slugs


def process_post_file(slug: str, lang: str, dry_run: bool) -> tuple[str, str, str, int]:
    """Replace 2026-08-01/2026-08-04 dates in a post page.

    Returns (path_rel, new_pub, new_mod, replacement_count).
    """
    if lang:
        post_dir = ROOT / lang / "blog" / slug
    else:
        post_dir = ROOT / "blog" / slug
    index_html = post_dir / "index.html"
    if not index_html.exists():
        return (str(post_dir.relative_to(ROOT)), "<missing>", "<missing>", 0)

    # EN URL has no lang prefix; non-EN has /xx/. The hash must match what
    # the middleware will compute for the same URL path.
    url_path = f"/{lang}/blog/{slug}/" if lang else f"/blog/{slug}/"
    dt_pub = hash_to_date(url_path)
    dt_mod = mod_date_for(url_path, dt_pub)
    new_pub = fmt_iso(dt_pub)
    new_mod = fmt_iso(dt_mod)

    bom, text = read_file_preserve_bom(index_html)
    original = text
    count = 0

    # JSON-LD datePublished (works for EN and non-EN, both have 2026-08-01)
    if '"datePublished":"2026-08-01"' in text:
        text = text.replace('"datePublished":"2026-08-01"', f'"datePublished":"{new_pub}"')
        count += 1
    # JSON-LD dateModified: EN uses 2026-08-04, non-EN uses 2026-08-01
    if '"dateModified":"2026-08-04"' in text:
        text = text.replace('"dateModified":"2026-08-04"', f'"dateModified":"{new_mod}"')
        count += 1
    if '"dateModified":"2026-08-01"' in text:
        text = text.replace('"dateModified":"2026-08-01"', f'"dateModified":"{new_mod}"')
        count += 1
    # og:article:published_time content="2026-08-01"
    if 'og:article:published_time" content="2026-08-01"' in text:
        text = text.replace(
            'og:article:published_time" content="2026-08-01"',
            f'og:article:published_time" content="{new_pub}"',
        )
        count += 1
    # og:article:modified_time content="2026-08-04" (EN) or 2026-08-01 (non-EN)
    if 'og:article:modified_time" content="2026-08-04"' in text:
        text = text.replace(
            'og:article:modified_time" content="2026-08-04"',
            f'og:article:modified_time" content="{new_mod}"',
        )
        count += 1
    if 'og:article:modified_time" content="2026-08-01"' in text:
        text = text.replace(
            'og:article:modified_time" content="2026-08-01"',
            f'og:article:modified_time" content="{new_mod}"',
        )
        count += 1

    if text != original and not dry_run:
        write_file_preserve_line_endings(index_html, bom, text)

    return (str(post_dir.relative_to(ROOT)), new_pub, new_mod, count)


# ----------------------------------------------------------------------
# Blog index ItemList + visible card text
# ----------------------------------------------------------------------

# Match each ListItem that has datePublished=2026-08-01, capturing the
# slug from the immediately-preceding "url" field. The blog index puts
# the URL right before "name" which is right before "datePublished".
LISTITEM_PATTERN = re.compile(
    r'"url":"https://weddingai\.video/blog/([^/]+)/",'
    r'"name":"[^"]*",'
    r'"datePublished":"2026-08-01"',
)

# Match an <article class="case-card"> block, capturing the slug from its href.
ARTICLE_BLOCK = re.compile(
    r'<article class="case-card">.*?</article>',
    re.DOTALL,
)
ARTICLE_HREF = re.compile(r'href="(/blog/([^/]+)/)"')
# Match "Aug 1, 2026" or "Aug D, 2026" right before </p> (the card date suffix).
ARTICLE_VISIBLE_DATE = re.compile(r'(Aug 1, 2026)(?=</)')


def process_blog_index(dry_run: bool) -> tuple[int, int]:
    """Diversify ItemList items and visible card dates on /blog/.

    Returns (itemlist_replacements, card_replacements).
    """
    blog_index = ROOT / "blog" / "index.html"
    bom, text = read_file_preserve_bom(blog_index)
    original = text

    # 1. ItemList items with datePublished 2026-08-01
    itemlist_count = [0]

    def repl_itemlist(m: re.Match) -> str:
        slug = m.group(1)
        # The ItemList on /blog/ only contains EN URLs (the i18n versions
        # of the listing are served by the same source HTML, so the URLs
        # are always /blog/<slug>/).
        url_path = f"/blog/{slug}/"
        dt = hash_to_date(url_path)
        new_pub = fmt_iso(dt)
        itemlist_count[0] += 1
        # Preserve the trailing " that the matched text ends with
        return m.group(0).replace(
            '"datePublished":"2026-08-01"',
            f'"datePublished":"{new_pub}"',
        )

    text = LISTITEM_PATTERN.sub(repl_itemlist, text)

    # 2. Visible card text "Aug 1, 2026"
    card_count = [0]

    def repl_card(m: re.Match) -> str:
        block = m.group(0)
        href_m = ARTICLE_HREF.search(block)
        if not href_m:
            return block
        url_path = href_m.group(1)  # /blog/SLUG/
        dt = hash_to_date(url_path)
        new_date = fmt_en(dt)
        new_block, n = ARTICLE_VISIBLE_DATE.subn(f"{new_date}", block, count=1)
        if n > 0:
            card_count[0] += 1
        return new_block

    text = ARTICLE_BLOCK.sub(repl_card, text)

    if text != original and not dry_run:
        write_file_preserve_line_endings(blog_index, bom, text)

    return itemlist_count[0], card_count[0]


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    args = parser.parse_args()

    slugs = get_new_post_slugs()
    print(f"Detected {len(slugs)} new posts (datePublished=2026-08-01)")
    if not slugs:
        print("Nothing to do.")
        return 0

    # 1. Individual post pages
    print("\n=== Individual post pages (9 langs × N posts) ===")
    post_total = 0
    post_changed = 0
    for slug in slugs:
        for lang in LANGS:
            rel, pub, mod, count = process_post_file(slug, lang, args.dry_run)
            if count > 0:
                post_total += count
                post_changed += 1
                if post_changed <= 5:
                    print(f"  {rel}: pub={pub}, mod={mod}, {count} replacements")
    print(f"  Total: {post_changed} files changed, {post_total} replacements")

    # 2. Blog index
    print("\n=== /blog/index.html ===")
    itemlist_count, card_count = process_blog_index(args.dry_run)
    print(f"  ItemList items diversified: {itemlist_count}")
    print(f"  Visible card dates diversified: {card_count}")

    if args.dry_run:
        print("\n[DRY RUN] No files written.")
    else:
        print("\nDone. Run `git diff` to review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
