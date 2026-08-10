"""
Round 3: clean up everything round 1+2 missed.

What survives after round 2:
  - Blog article <p data-i18n="..."> paragraphs that still link to
    /services/absence-compensation/celebrity-message/. These are the only
    remaining public-facing references to the deleted service. We unwrap the
    <a> tags (keep the visible text, drop the link) so the articles remain
    readable but no longer point at a dead URL.
  - The 308 → /services/absence-compensation/celebrity-message/ line in
    _redirects. We change it to 301 → /services/absence-compensation/ so
    external links / old bookmarks get a sensible target instead of 404.
  - services/absence-compensation/family-tribute/index.html still had a
    related-card <a> block round 1 may have missed (the regex used
    specific title/desc text). Re-check.
  - articles/47-wedding-video-cost-2026.md line 120 table row + line 277
    bullet still reference the deleted service.
  - scripts/verify-4xx-inlinks.py and similar scripts may have hardcoded
    paths to verify against.

Idempotent: re-running this is a no-op.
"""

import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")

# ---------------------------------------------------------------------------
# 1) Unwrap <a href="/services/absence-compensation/celebrity-message/">
#    tags everywhere in the published site (HTML files only, excluding
#    scripts/archive/private/tmp).
# ---------------------------------------------------------------------------

ANCHOR_RE = re.compile(
    r'<a [^>]*href="/services/absence-compensation/celebrity-message/[^"]*"[^>]*>([^<]*)</a>',
    re.IGNORECASE,
)


def unwrap_anchors_in_html(root: Path) -> int:
    files = list(root.rglob("*.html"))
    files = [p for p in files if "_trash_celebrity" not in p.parts and "private" not in p.parts]
    changed = 0
    for p in files:
        text = p.read_text(encoding="utf-8")
        new = ANCHOR_RE.sub(lambda m: m.group(1), text)
        if new != text:
            p.write_text(new, encoding="utf-8")
            changed += 1
    return changed


# ---------------------------------------------------------------------------
# 2) articles/47-wedding-video-cost-2026.md
#    Drop the table row "| Celebrity/Influencer Message | $199-$499 | ..."
#    and the bullet that mentions "celebrity message".
# ---------------------------------------------------------------------------

ARTICLE_TABLE_ROW_RE = re.compile(
    r"^[ \t]*\| Celebrity/Influencer Message \| \$199-\$499 \| Personalized video messages \|.*\r?\n",
    re.MULTILINE,
)

ARTICLE_BULLET_RE = re.compile(
    r"^[ \t]*- Use WeddingAI\.video for unique add-ons \(cartoon style, pet video, celebrity message\) \(\$300-\$1,000\)\r?\n",
    re.MULTILINE,
)


def rewrite_article(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    new = ARTICLE_TABLE_ROW_RE.sub("", text)
    new = ARTICLE_BULLET_RE.sub("", new)
    if new != text:
        path.write_text(new, encoding="utf-8")
        return 1
    return 0


# ---------------------------------------------------------------------------
# 3) _redirects line 724: change 308 → 301 to /services/absence-compensation/
# ---------------------------------------------------------------------------

REDIRECTS_RE = re.compile(
    r'^(/celebrity-message/)[ \t]+(/services/absence-compensation/celebrity-message/)[ \t]+(308)\s*$',
    re.MULTILINE,
)


def rewrite_redirects(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    # Use a callable so we can rebuild the line with the new target.
    new = REDIRECTS_RE.sub(
        lambda m: f"{m.group(1).rstrip('/') + '/':<30s}/services/absence-compensation/   301",
        text,
    )
    if new != text:
        path.write_text(new, encoding="utf-8")
        return 1
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=== Unwrap dead <a> links in HTML ===")
    n = unwrap_anchors_in_html(ROOT)
    print(f"  -> {n} HTML files cleaned\n")

    print("=== articles/47-wedding-video-cost-2026.md ===")
    if rewrite_article(ROOT / "articles/47-wedding-video-cost-2026.md"):
        print("  [1] articles/47-wedding-video-cost-2026.md\n")
    else:
        print("  (no change)\n")

    print("=== _redirects 308 -> 301 (target: /services/absence-compensation/) ===")
    if rewrite_redirects(ROOT / "_redirects"):
        print("  [1] _redirects\n")
    else:
        print("  (no change)\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
