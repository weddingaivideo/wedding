"""
Hard-cap any remaining blog titles over 60 chars by truncating to the
last whole word at or before 60. SEO length limit per Google guidelines.
Idempotent: re-running is a no-op once titles are <= 60.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
LIMIT = 60


def hard_cap(title: str) -> str:
    if len(title) <= LIMIT:
        return title
    # Truncate to LIMIT, then back off to last whitespace
    truncated = title[:LIMIT].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated.rstrip(" ,:-—")


def main() -> int:
    n = 0
    for f in BLOG.rglob("*.html"):
        text = f.read_text(encoding="utf-8")
        m = re.search(r"<title>([^<]+)</title>", text)
        if not m:
            continue
        old = m.group(1)
        new = hard_cap(old)
        if new != old:
            f.write_text(text.replace(f"<title>{old}</title>", f"<title>{new}</title>", 1), encoding="utf-8")
            print(f"  [{len(old)}->{len(new)}] {old}")
            print(f"             -> {new}")
            n += 1
    print(f"\n[ok] {n} titles hard-capped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
