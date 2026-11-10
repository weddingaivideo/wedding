"""Refresh <lastmod> in all 11 per-language sitemap files to today's UTC date.

Rewrites every <lastmod>...</lastmod> in sitemap-<lang>.xml (and in the
sitemap.xml index) to one date. The URL set, the hreflang graph and the
image:image blocks are left untouched — only the date changes.

The date defaults to the UTC day on purpose: the CI gate ("Verify sitemap has
today's lastmod" in .github/workflows/ci.yml) compares against
`date -u +%Y-%m-%d`, so a local-time date would drift out of sync for anyone
pushing more than a few hours ahead of UTC.

Usage:
    python scripts/_refresh_sitemap_lastmod.py            # today (UTC)
    python scripts/_refresh_sitemap_lastmod.py 2026-11-10  # explicit date
"""
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TODAY = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).date().isoformat()
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]


def refresh(path: Path, date: str) -> int:
    text = path.read_text(encoding="utf-8")
    before = text.count("<lastmod>")
    new_text = re.sub(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>", f"<lastmod>{date}</lastmod>", text)
    if new_text == text:
        print(f"  {path.name}: no change")
        return 0
    # Atomic write
    tmp = path.with_suffix(".xml.tmp")
    tmp.write_text(new_text, encoding="utf-8", newline="")
    if tmp.read_text(encoding="utf-8") != new_text:
        tmp.unlink()
        raise RuntimeError(f"tmp mismatch for {path}")
    shutil.move(str(tmp), str(path))
    print(f"  {path.name}: {before} lastmod entries refreshed (now {date})")
    return before


total = 0
for lang in LANGS:
    sm = REPO / f"sitemap-{lang}.xml"
    if not sm.exists():
        print(f"SKIP: {sm} not found")
        continue
    total += refresh(sm, TODAY)

index = REPO / "sitemap.xml"
if index.exists():
    total += refresh(index, TODAY)

print(f"\nTotal: {total} lastmod entries refreshed across {len(LANGS) + 1} sitemap files (date={TODAY})")
