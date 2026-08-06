"""
Trim over-long blog page titles (<=60 chars) by stripping the redundant
"WeddingAI.video Blog" suffix. Most article titles are already descriptive
on their own (frontmatter `title:`), and the brand is set via <meta> and the
visible page header.

Also shortens the blog list page title.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
SUFFIXES = [
    " | WeddingAI.video Blog",
    " | WeddingAI.video",
    " - WeddingAI.video Blog",
    " - WeddingAI.video",
]


def trim(title: str) -> str:
    for s in SUFFIXES:
        if title.endswith(s):
            return title[: -len(s)].rstrip()
    return title


def main() -> int:
    n_changed = 0
    over = []
    for f in BLOG.rglob("*.html"):
        text = f.read_text(encoding="utf-8")
        m = re.search(r"<title>([^<]+)</title>", text)
        if not m:
            continue
        old_title = m.group(1)
        new_title = trim(old_title)
        if new_title == old_title:
            continue
        if len(new_title) > 60:
            over.append((len(new_title), new_title, str(f.relative_to(ROOT))))
        new_text = text.replace(f"<title>{old_title}</title>", f"<title>{new_title}</title>", 1)
        f.write_text(new_text, encoding="utf-8")
        n_changed += 1

    # Also: tighten the blog list page title
    list_page = BLOG / "index.html"
    if list_page.exists():
        text = list_page.read_text(encoding="utf-8")
        new_text = re.sub(
            r"<title>Wedding Video Blog: Tips, Guides & AI Insights \| WeddingAI\.video</title>",
            "<title>Wedding Video Blog | WeddingAI.video</title>",
            text,
        )
        if new_text != text:
            list_page.write_text(new_text, encoding="utf-8")
            n_changed += 1

    print(f"[ok] trimmed {n_changed} blog titles")
    if over:
        print(f"[warn] {len(over)} titles still >60 chars after trim:")
        for length, t, rel in over[:5]:
            print(f"  [{length}] {t}  ({rel})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
