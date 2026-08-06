"""Verify the inlink cleanup removed all 4xx targets from href attributes."""
import re
from pathlib import Path

ROOT = Path(".")
SKIP = {".git", ".wrangler", "node_modules", "100 blog", "internal-tools",
        "private", "admin", "functions", "i18n", "config", "qa", "tmp"}

BAD = [
    (r'href="[^"]*\.md[#"\'?]',                                "Category B: .md leakage"),
    (r'href="/weddingai-video-guide/?[#"\'?]',                "Category A: root weddingai-video-guide"),
    (r'href="/make-first-ai-wedding-video/?[#"\'?]',          "Category A: root make-first-ai-wedding-video"),
    (r'href="/wedding-video-music-guide-new/?[#"\'?]',        "Category A: root wedding-video-music-guide-new"),
    (r'href="/wedding-video-cost-2026-new/?[#"\'?]',          "Category A: root wedding-video-cost-2026-new"),
    (r'href="/weddingai-video-case-studies/?[#"\'?]',         "Category A: root weddingai-video-case-studies"),
    (r'href="/how-to-make-wedding-video/?[#"\'?]',            "Category A: root how-to-make-wedding-video"),
    (r'href="/wedding-video-captions/?[#"\'?]',               "Category A: root wedding-video-captions"),
    (r'href="/wedding-video-photo-checklist/?[#"\'?]',        "Category A: root wedding-video-photo-checklist"),
    (r'href="/ai-editor-vs-traditional-editing/?[#"\'?]',     "Category A: root ai-editor-vs-traditional-editing"),
    (r'href="[^"]*blog/destination-wedding-video-guide/?[#"\'?]', "Category C: wrong slug destination-wedding-video-guide"),
    (r'href="[^"]*blog/wedding-video-under-500/?[#"\'?]',     "Category C: missing under-500"),
    (r'href="[^"]*/small-wedding-video-ideas/?[#"\'?]',       "Category C: missing small-wedding-video-ideas"),
    (r'href="[^"]*/wedding-package-video-upsell/?[#"\'?]',    "Category C: missing wedding-package-video-upsell"),
    (r'href="[^"]*/services/personalization/wedding-invitation/?[#"\'?]', "Category D: missing wedding-invitation"),
]

total = 0
files_with_issues = 0
for p in ROOT.rglob("*.html"):
    if SKIP & set(p.parts):
        continue
    try:
        t = p.read_text(encoding="utf-8")
    except Exception:
        continue
    for pat, label in BAD:
        m = re.findall(pat, t)
        if m:
            total += len(m)
            files_with_issues += 1
            print(f"  {p}  -- {label}  ({len(m)})")
            for hit in re.finditer(pat, t):
                print(f"      {hit.group(0)[:130]}")

print(f"\n{'='*60}")
print(f"Total leftover bad inlinks: {total}")
print(f"Files with issues: {files_with_issues}")
print(f"{'CLEAN' if total == 0 else 'STILL DIRTY'}")
