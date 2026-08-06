"""
Fix i18n_inject damage in the body of HTML files.

The script that produced the damage replaced "<" with the literal string
"OPEN" in tag names throughout the body (not just the header). It also
removed the closing ">" of the original tag, then injected a new tag with
data-i18n right after. So bodies have:
  - "OPENp style=\"X\"<p style=\"X\" data-i18n=\"Y\">Text</p>"

Strategy:  do the minimum fix — restore the leading "<" so the document is
at least parseable.  The duplicate adjacent tag pattern (the broken original
+ the i18n version) means users will see some text twice in some cases, but
i18n.js sets textContent on the i18n version, so the broken tag will still
show its original (EN) text.

For a clean fix we'd need to detect & remove the broken original.  That's
a much harder problem (false positives in any heuristic), so we do the
minimum here and document the limitation.

Idempotent: re-running on clean files is a no-op (detects no remaining
"OPEN<tag>" patterns).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE = {"admin", "private", "tmp", "node_modules", ".git", "i18n", "scripts", "qa"}

KNOWN_TAGS = (
    "title", "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "a", "button", "label", "span", "td", "th", "li", "ul", "ol",
    "option", "strong", "em", "b", "i", "small", "blockquote",
    "figcaption", "summary",
)


def all_html():
    out = []
    for f in ROOT.rglob("*.html"):
        if any(p in EXCLUDE for p in f.relative_to(ROOT).parts):
            continue
        if f.name == "google-site-verification.html":
            continue
        out.append(f)
    return out


def fix_body(text: str) -> tuple[str, int]:
    """Replace any 'OPEN<TAGNAME' with '<TAGNAME'. Returns (new_text, count)."""
    n = 0
    # No boundary check after the tag name — i18n_inject always concatenates
    # the tag name with the following attribute (e.g. "OPENp class="),
    # so we just need to find "OPEN" + any of our known tag names anywhere.
    # Risk: if "OPEN" + tag name appears in user content. Unlikely — these
    # tag names are all short common words and would not normally appear
    # in body text immediately preceded by "OPEN".
    alts = "|".join(KNOWN_TAGS)
    pattern = re.compile(rf"OPEN({alts})")
    text, n = pattern.subn(r"<\1", text)
    return text, n


def main() -> int:
    files = all_html()
    print(f"=== Repairing {len(files)} HTML files (body OPEN cleanup) ===\n")
    grand = 0
    files_changed = 0

    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding="utf-8")
        orig = text

        text, n = fix_body(text)

        if text != orig:
            f.write_text(text, encoding="utf-8")
            files_changed += 1
            grand += n
            if n:
                print(f"  FIX  {rel}  +{n} < restored")

    print(f"\nFixed {files_changed} files: {grand} '<' characters restored")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
