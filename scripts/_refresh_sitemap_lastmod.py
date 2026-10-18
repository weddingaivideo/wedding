"""Refresh <lastmod> in all 11 sitemap files to today's date (2026-10-17).

Replaces 2026-08-23 (or 2026-09-24) with 2026-10-17.
"""
import re
import shutil
from pathlib import Path
from datetime import date

REPO = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai")
TODAY = "2026-10-17"
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
total = 0
for lang in LANGS:
    sm = REPO / f"sitemap-{lang}.xml"
    if not sm.exists():
        print(f"SKIP: {sm} not found")
        continue
    text = sm.read_text(encoding="utf-8")
    before = text.count("<lastmod>")
    new_text = re.sub(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>", f"<lastmod>{TODAY}</lastmod>", text)
    after_count = new_text.count(f"<lastmod>{TODAY}</lastmod>")
    if new_text == text:
        print(f"  {sm.name}: no change")
        continue
    # Atomic write
    tmp = sm.with_suffix(".xml.tmp")
    tmp.write_text(new_text, encoding="utf-8", newline="")
    if tmp.read_text(encoding="utf-8") != new_text:
        tmp.unlink()
        raise RuntimeError(f"tmp mismatch for {sm}")
    shutil.move(str(tmp), str(sm))
    print(f"  {sm.name}: {before} lastmod entries refreshed ({after_count} now {TODAY})")
    total += before
print(f"\nTotal: {total} lastmod entries refreshed across {len(LANGS)} sitemaps")
