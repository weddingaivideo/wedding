"""
P2-2: Check the 50 blog-slug 301 redirect rules in _redirects.

Background:
  2026-07-23: blog numeric slugs (01-restore-old-wedding-videos/...) were
  migrated to semantic slugs (restore-vhs-wedding-footage/...). 50
  back-compat 301 rules were added to _redirects so external links
  pointing at the old URLs still resolve.

Retention policy:
  Safe-to-delete: 2027-01-23 (6 months after migration). After that,
  crawl decay + user-share decay should have flushed all external
  references. Until then, prefer to keep.

This script:
  1) Counts the 301 rules in _redirects that match /blog/NN-... → /blog/...
  2) Verifies the target slugs actually exist under /blog/ (no orphans
     redirecting to nowhere)
  3) Prints days-until-expiry and a one-line summary
  4) Optionally runs in pre-deploy-check via `pre-deploy-check.ps1`
     (printed as a WARN if < 30 days remain)
"""
import os
import re
import sys
from datetime import date
from pathlib import Path

# Force UTF-8 stdout — Windows CI runners default to cp1252 which crashes
# on the → / ✅ / ❌ glyphs we print. Belt-and-suspenders alongside the
# PYTHONIOENCODING=utf-8 env var set in the workflow.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
REDIRECTS = ROOT / "_redirects"
BLOG_DIR = ROOT / "blog"
MIGRATION_DATE = date(2026, 7, 23)
SAFE_DELETE = date(2027, 1, 23)
WARN_DAYS = 30  # start warning this far before safe-delete

def parse_rules():
    """Return list of (old_path, new_path) tuples from /blog/NN-... -> /blog/... 301 rules."""
    text = REDIRECTS.read_text(encoding="utf-8")
    rules = []
    for m in re.finditer(
        r"^(/blog/\d{2}-[\w-]+/)\s+(/blog/[\w-]+/)\s+301\s*$",
        text, re.MULTILINE,
    ):
        rules.append((m.group(1), m.group(2)))
    return rules

def main():
    rules = parse_rules()
    today = date.today()
    days_remaining = (SAFE_DELETE - today).days
    print(f"=== Blog slug 301 retention check ===")
    print(f"Migration:  {MIGRATION_DATE.isoformat()}  (blog/01-xxx → semantic)")
    print(f"Safe-delete: {SAFE_DELETE.isoformat()}  (6-month retention)")
    print(f"Today:      {today.isoformat()}")
    print(f"Days until safe-delete: {days_remaining}")
    print()

    print(f"Rules found: {len(rules)} (expected 50)")
    if len(rules) != 50:
        print(f"  WARN: rule count != 50. Re-run scripts/rename-blog-dirs.py?")
    print()

    # Verify each target exists
    orphan = []
    missing_source = []
    for src, dst in rules:
        src_name = src.rstrip("/")
        dst_name = dst.rstrip("/")
        src_dir = BLOG_DIR / src_name.split("/")[-1]
        dst_dir = BLOG_DIR / dst_name.split("/")[-1]
        if not dst_dir.exists():
            orphan.append(dst)
        if not src_dir.exists():
            # Old slug should NOT exist (that's the whole point of 301)
            pass  # this is the expected state

    if orphan:
        print(f"  FAIL: {len(orphan)} redirect target(s) missing on disk:")
        for o in orphan:
            print(f"    {o}")
    else:
        print(f"  All {len(rules)} redirect targets resolve to a real /blog/<slug>/ directory")
    print()

    # Show first 3 + last 3 as sanity samples
    print("Sample rules (first 3):")
    for src, dst in rules[:3]:
        print(f"  {src:<48} -> {dst}")
    if len(rules) > 6:
        print(f"  ... ({len(rules) - 6} more) ...")
    print("Sample rules (last 3):")
    for src, dst in rules[-3:]:
        print(f"  {src:<48} -> {dst}")
    print()

    # Decision
    if days_remaining <= 0:
        print(f">>> ACTION: safe-delete date passed. Delete the 50 rules from _redirects.")
        print(f">>>         Run: python qa/check_blog_redirects.py --prune")
        return 1  # exit non-zero to flag in pre-deploy-check
    elif days_remaining <= WARN_DAYS:
        print(f">>> WARN: {days_remaining} days until safe-delete. Plan cleanup window.")
        return 0  # exit 0 — pre-deploy-check can escalate this to WARN
    else:
        print(f">>> OK: {days_remaining} days retention remain. Keep rules.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
