#!/usr/bin/env python3
"""
Bulk fix pass 1 — quick wins + safe content edits.

Fixes:
  QW1: required="None" -> required (Python artifact; breaks form validation)
  QW2: theme-color #c45a72 -> #D4AF37 (rose pink clashes with gold brand)
  QW3: <pstyle= ...> -> <p style= ...>  (broken HTML from f-string bug)
  QW4: Tom & Jerry R. (cartoon name) -> James & Emily R.
  QW5: Tom & Hannah (cartoon-adjacent) -> Daniel & Hannah
  QW6: Delete FIRST-discount paragraph + FAQ in services/index.html
  QW7: Footer-bottom CTA "Ready to start? Get a Free Quote"
  P0-5: aggregateRating reviewCount 127 -> 6 in index.html & services/index.html

Reads: workspace HTML files + i18n JSON
Writes: same paths, UTF-8 (no BOM)
"""
import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
I18N = ROOT / "i18n"

HTML_GLOB = "**/*.html"
HTML_EXCLUDE_DIRS = {"qa", "tmp", "i18n", "node_modules", ".git"}

changes = {}


def should_skip(p: Path) -> bool:
    rel = p.relative_to(ROOT)
    return any(part in HTML_EXCLUDE_DIRS for part in rel.parts)


def walk_html():
    for p in ROOT.rglob(HTML_GLOB):
        if not should_skip(p):
            yield p


def walk_i18n_json():
    for p in I18N.glob("*.json"):
        yield p


# ---------- 1. required="None"  →  required ----------
RX_REQ_NONE = re.compile(r'\brequired="None"')


def fix_required_none(text: str) -> tuple[str, int]:
    new, n = RX_REQ_NONE.subn("required", text)
    return new, n


# ---------- 2. theme-color  ----------
RX_THEME = re.compile(r'theme-color"\s+content="#c45a72"', re.IGNORECASE)


def fix_theme_color(text: str) -> tuple[str, int]:
    new, n = RX_THEME.subn('theme-color" content="#D4AF37"', text)
    return new, n


# ---------- 3. <pstyle=  →  <p style= ----------
RX_PSTYLE = re.compile(r"<pstyle=")


def fix_pstyle(text: str) -> tuple[str, int]:
    new, n = RX_PSTYLE.subn("<p style=", text)
    return new, n


# ---------- 4 + 5. Tom & Jerry / Tom & Hannah  ----------
RX_TJ = re.compile(r"Tom\s*&\s*Jerry\s*R\.")
RX_TH = re.compile(r"Tom\s*&\s*Hannah")


def fix_tom_jerry(text: str) -> tuple[str, int]:
    new, n1 = RX_TJ.subn("James & Emily R.", text)
    new, n2 = RX_TH.subn("Daniel & Hannah", new)
    return new, n1 + n2


# ---------- 6. delete FIRST discount ----------
# The whole FAQ question and answer is:
#   <details class="faq-item">
#       <summary ...>Do you offer any discounts?</summary>
#       <p ...>Yes: 10% off... Discounts stack up to a maximum of 30%.</p>
#   </details>
# We remove the entire <details> block.
RX_FIRST_DISCOUNT = re.compile(
    r'<details\s+class="faq-item">\s*'
    r'<summary\s+data-i18n="services\.summary_text\.do_you_offer_any_discounts\.[^"]+">'
    r"Do you offer any discounts\?.*?</details>",
    re.DOTALL,
)


def fix_first_discount(text: str) -> tuple[str, int]:
    new, n = RX_FIRST_DISCOUNT.subn("", text)
    return new, n


# ---------- 7. footer-bottom CTA  ----------
# Insert a CTA strip before the existing footer-bottom div.
# Original pattern:  <div class="footer-bottom">
# Insert: a new div.cta-strip + small inline styles, idempotent.
CTA_STRIP = (
    '\n        <div class="wa-cta-strip" '
    'style="background: var(--color-primary); color: var(--color-white); '
    'padding: 1.25rem 0; text-align: center;">'
    '\n            <div class="container" '
    'style="display:flex;align-items:center;justify-content:center;'
    'gap:1rem;flex-wrap:wrap;">'
    '\n                <span style="font-weight:600;">Ready to start your project?</span>'
    '\n                <a href="/order/" class="btn-cta" '
    'style="background: var(--color-secondary); color: var(--color-white); '
    'padding: 0.625rem 1.25rem; border-radius: 8px; font-weight: 700; '
    'text-decoration: none;">Get a Free Quote &rarr;</a>'
    "\n            </div>"
    "\n        </div>\n        "
)

FOOTER_BOTTOM_MARKER = '<div class="footer-bottom">'
FOOTER_BOTTOM_NEW = CTA_STRIP + FOOTER_BOTTOM_MARKER


def fix_footer_cta(text: str) -> tuple[str, int]:
    if "wa-cta-strip" in text:
        return text, 0
    new, n = text.replace(FOOTER_BOTTOM_MARKER, FOOTER_BOTTOM_NEW, 1), 1
    return new, n


# ---------- P0-5. aggregateRating reviewCount 127  →  6 ----------
RX_REVIEW_127 = re.compile(r'"reviewCount":\s*"127"')


def fix_review_count(text: str) -> tuple[str, int]:
    new, n = RX_REVIEW_127.subn('"reviewCount": "6"', text)
    return new, n


# ---------- Pipeline ----------
def process_file(p: Path, fixers: list[tuple[str, callable]]) -> int:
    raw = p.read_text(encoding="utf-8")
    total = 0
    for name, fn in fixers:
        raw, n = fn(raw)
        if n:
            changes.setdefault(name, []).append((str(p.relative_to(ROOT)), n))
        total += n
    if total:
        p.write_text(raw, encoding="utf-8", newline="")
    return total


def process_json(p: Path, fixers: list[tuple[str, callable]]) -> int:
    """Apply each fix to the raw JSON text (we treat it as text, not parsed)."""
    raw = p.read_text(encoding="utf-8")
    total = 0
    for name, fn in fixers:
        raw, n = fn(raw)
        if n:
            changes.setdefault(name, []).append((p.name, n))
        total += n
    if total:
        p.write_text(raw, encoding="utf-8", newline="")
    return total


HTML_FIXERS = [
    ("required_none", fix_required_none),
    ("theme_color", fix_theme_color),
    ("pstyle_bug", fix_pstyle),
    ("tom_jerry_hannah", fix_tom_jerry),
    ("first_discount", fix_first_discount),
    ("footer_cta", fix_footer_cta),
    ("review_count", fix_review_count),
]

JSON_FIXERS = [
    # only Tom & Jerry / Tom & Hannah strings appear in JSON
    ("tom_jerry_hannah", fix_tom_jerry),
]


def main():
    total = 0
    for p in walk_html():
        total += process_file(p, HTML_FIXERS)
    for p in walk_i18n_json():
        total += process_json(p, JSON_FIXERS)

    # Report
    print(f"\n=== Total edits: {total} ===\n")
    for name, sites in changes.items():
        n = sum(c for _, c in sites)
        print(f"  {name}: {n} changes across {len(sites)} files")
        for path, cnt in sites[:5]:
            print(f"     - {path}  ×{cnt}")
        if len(sites) > 5:
            print(f"     ... +{len(sites) - 5} more")


if __name__ == "__main__":
    main()
