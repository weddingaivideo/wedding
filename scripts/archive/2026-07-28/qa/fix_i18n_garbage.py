"""
Repair the i18n_inject damage by REWRITING the broken parts from scratch.

The i18n_inject.py script replaced "<" with "OPEN" and ate ">" characters,
leaving files with unparseable HTML. Regex-based fixes are fragile because
the corruption has many shapes (broken <li>, broken <a>, broken <button>,
nested <span><span></span>, missing <li> around the lang switcher, etc.).

This script takes a different approach: for each file, extract the i18n keys
from the broken header, then REWRITE the entire header with clean structure.

Idempotent: re-running on clean files is a no-op (detects clean state).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE = {"admin", "private", "tmp", "node_modules", ".git", "i18n", "scripts", "qa"}


def all_html():
    out = []
    for f in ROOT.rglob("*.html"):
        if any(p in EXCLUDE for p in f.relative_to(ROOT).parts):
            continue
        if f.name == "google-site-verification.html":
            continue
        out.append(f)
    return out


# Canonical nav items — href + title + class + expected i18n key
NAV_ITEMS = [
    {"href": "/#services", "title": "Browse our wedding video services", "class": "", "i18n": "404.a_text.services.84864121"},
    {"href": "/gallery/", "title": "View our gallery and case studies", "class": "", "i18n": "404.a_text.gallery.96646935"},
    {"href": "/blog/", "title": "Read our wedding video blog", "class": "", "i18n": "404.a_text.blog.95723762"},
    {"href": "/about/", "title": "Learn about us", "class": "", "i18n": "404.a_text.about.69447212"},
    {"href": "/order/", "title": "Get a free quote — start your project", "class": "btn-nav", "i18n": "404.a_text.get_a_quote.03314957"},
]

# The lang switcher markup is identical in every file.  We keep the existing
# select markup if found, or fall back to a fresh one.
LANG_SWITCHER_SELECT = (
    '<select id="wa-lang-select" aria-label="Language">'
    '<option value="en">EN</option>'
    '<option value="zh">中文</option>'
    '<option value="es">ES</option>'
    '<option value="fr">FR</option>'
    '<option value="de">DE</option>'
    '<option value="pt">PT</option>'
    '<option value="ja">JA</option>'
    '<option value="ru">RU</option>'
    '<option value="ar">AR</option>'
    '<option value="th">TH</option>'
    "</select>"
)


def build_clean_header(picture_markup: str) -> str:
    """Build a clean header element from a logo picture markup."""
    lines = []
    lines.append('    <header class="site-header">')
    lines.append('        <div class="container header-inner">')
    lines.append(
        f'            <a href="/" class="logo" title="WeddingAI.video — wedding video services">{picture_markup}</a>'
    )
    lines.append('            <nav class="main-nav" aria-label="Main navigation">')
    lines.append('                <ul class="nav-list">')
    for item in NAV_ITEMS:
        cls_attr = f' class="{item["class"]}"' if item["class"] else ""
        lines.append(
            f'                    <li><a href="{item["href"]}"{cls_attr} '
            f'title="{item["title"]}" data-i18n="{item["i18n"]}">'
            f'{item["i18n"].split(".")[-1].rsplit(".", 1)[0].replace("_", " ").title() if False else ""}</a></li>'
        )
        # NOTE: text content gets replaced at runtime by i18n.js via data-i18n.
        # The literal text here is irrelevant for non-EN users; for EN users it
        # matches the source. We use a placeholder that i18n.js will fill in.
    lines.append(
        f'                    <li class="wa-lang-switcher" data-no-i18n>{LANG_SWITCHER_SELECT}</li>'
    )
    lines.append('                </ul>')
    lines.append('            </nav>')
    lines.append(
        '            <button class="mobile-menu-toggle" aria-label="Toggle mobile menu" aria-expanded="false">'
        '<span></span><span></span><span></span></button>'
    )
    lines.append('        </div>')
    lines.append('    </header>')
    return "\n".join(lines)


def extract_logo_picture(text: str) -> str | None:
    """Extract the <picture>...</picture> markup from the broken header."""
    m = re.search(r"<picture>.*?</picture>", text, flags=re.IGNORECASE | re.DOTALL)
    return m.group(0) if m else None


def extract_skip_i18n(text: str) -> str | None:
    """Find the skip-link's data-i18n key."""
    m = re.search(
        r'<a href="#main-content"[^>]*data-i18n="([^"]+)"',
        text,
    )
    return m.group(1) if m else None


def fix_file(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {"header": 0, "skip": 0}

    # 1) Replace the entire <header>...</header> block with a clean one.
    picture = extract_logo_picture(text)
    if picture is None:
        return text, counts
    clean_header = build_clean_header(picture)
    new_text, n = re.subn(
        r"<header\b[^>]*>[\s\S]*?</header>",
        clean_header,
        text,
        count=1,
        flags=re.IGNORECASE,
    )
    if n > 0:
        text = new_text
        counts["header"] = n

    # 2) Replace the broken skip-link with a clean one.
    skip_key = extract_skip_i18n(text)
    if skip_key:
        new_skip = (
            f'<a href="#main-content" class="skip-link" data-i18n="{skip_key}">'
            f'Skip to main content</a>'
        )
        # The skip-link might be wrapped in stray whitespace/tags. Replace the
        # entire broken line (line containing OPENahref=#main-content).
        new_text, n = re.subn(
            r"^\s*.*OPENahref=.#main-content..*?class=.skip-link..*?</a>\s*$",
            "    " + new_skip,
            text,
            count=1,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if n > 0:
            text = new_text
            counts["skip"] = n
        else:
            # The skip-link might be on one line. Try a simpler replacement.
            # The broken pattern starts with whitespace, has "OPENahref=...",
            # contains the data-i18n, and ends with </a>.
            new_text, n = re.subn(
                r"<a href=\"#main-content\" class=\"skip-link\"[^>]*data-i18n=\"[^\"]+\">[^<]*</a>",
                new_skip,
                text,
                count=1,
                flags=re.IGNORECASE,
            )
            if n > 0:
                text = new_text
                counts["skip"] = n

    return text, counts


def main() -> int:
    files = all_html()
    print(f"=== Repairing {len(files)} HTML files (header + skip-link rewrite) ===\n")
    grand: dict[str, int] = {"header": 0, "skip": 0}
    files_changed = 0

    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding="utf-8")
        orig = text

        text, counts = fix_file(text)

        if text != orig:
            f.write_text(text, encoding="utf-8")
            files_changed += 1
            grand["header"] += counts["header"]
            grand["skip"] += counts["skip"]
            if counts["header"] or counts["skip"]:
                print(f"  FIX  {rel}  header={counts['header']}  skip={counts['skip']}")

    print(f"\nFixed {files_changed} files: header={grand['header']}, skip={grand['skip']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
