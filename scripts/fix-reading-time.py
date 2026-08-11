#!/usr/bin/env python3
"""
fix-reading-time.py

Recalculate the reading time for every blog post (EN + 8 i18n languages)
based on actual word count of the article body, then update:
  1. JSON-LD Article schema (timeRequired, wordCount)
  2. i18n dict value for the visible "X min read" line

Reading speed: 250 wpm (industry standard). Round up to nearest minute.

Optimization: read each i18n dict file ONCE, then process all slugs against
the in-memory dict, write back at the end. Original version read 10 dicts
per post which was 10x slower than necessary.

Usage: python scripts/fix-reading-time.py [--root <path>] [--dry-run]
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

WPM = 250  # words per minute, industry standard for web articles
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"]

ARTICLE_LD_RE = re.compile(
    r'<script\s+type="application/ld\+json"[^>]*>(\s*\{[\s\S]*?\})\s*</script>',
    re.IGNORECASE,
)
READING_KEY_RE = re.compile(
    r'^(blog\.[^.]+)\.p_text\.\d+_min_read[^.]*\.[0-9a-f]{8}$'
)


def count_words(html: str) -> int:
    """Count words in the article body — strip tags, normalize whitespace."""
    text = re.sub(r'<script\b[\s\S]*?</script>', ' ', html, flags=re.IGNORECASE)
    text = re.sub(r'<style\b[\s\S]*?</style>', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = (
        text.replace('&nbsp;', ' ').replace('&mdash;', '—')
            .replace('&ndash;', '–').replace('&rsquo;', "'")
            .replace('&lsquo;', "'").replace('&ldquo;', '"')
            .replace('&rdquo;', '"').replace('&hellip;', '…')
            .replace('&amp;', '&').replace('&quot;', '"')
    )
    return len([w for w in re.split(r'\s+', text) if w.strip()])


def reading_minutes(word_count: int, wpm: int = WPM) -> int:
    if word_count == 0:
        return 0
    return max(1, -(-word_count // wpm))


def iso_duration(minutes: int) -> str:
    return f"PT{minutes}M"


def update_article_json_ld(html: str, word_count: int, minutes: int) -> tuple[str, bool]:
    changed_any = False

    def repl(m: re.Match) -> str:
        nonlocal changed_any
        body = m.group(1)
        try:
            obj = json.loads(body)
        except json.JSONDecodeError:
            return m.group(0)
        if not isinstance(obj, dict) or obj.get("@type") != "Article":
            return m.group(0)
        new_tr = iso_duration(minutes)
        new_wc = word_count
        if obj.get("timeRequired") == new_tr and obj.get("wordCount") == new_wc:
            return m.group(0)
        obj["timeRequired"] = new_tr
        obj["wordCount"] = new_wc
        changed_any = True
        return m.group(0).replace(body, json.dumps(obj, ensure_ascii=False, separators=(",", ":")))

    return ARTICLE_LD_RE.sub(repl, html), changed_any


def load_i18n_dicts(i18n_root: Path) -> dict[str, dict]:
    """Load all 10 i18n dicts once. Returns {lang: dict}."""
    out = {}
    for lang in LANGS:
        p = i18n_root / f"{lang}.json"
        try:
            out[lang] = json.loads(p.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            out[lang] = {}
    return out


def update_dict_for_slug(dict_obj: dict, slug: str, minutes: int) -> tuple[bool, str | None]:
    """Update reading-time key value in a single dict (in-place)."""
    prefix = f"blog.{slug}.p_text."
    for k, v in list(dict_obj.items()):
        if k.startswith(prefix) and "_min_read" in k:
            # Preserve the existing "Updated YYYY-MM-DD" portion if present.
            date_part = ""
            m = re.search(r'Updated\s*\d{4}-\d{2}-\d{2}', v)
            if m:
                date_part = m.group(0)
            new_value = f"{minutes} min read · {date_part}".strip(" ·")
            if v == new_value:
                return False, k
            dict_obj[k] = new_value
            return True, k
    return False, None


def write_i18n_dicts(i18n_root: Path, dicts: dict[str, dict], dry: bool) -> dict[str, int]:
    """Write back each i18n dict if changed."""
    n_changed = {}
    for lang, obj in dicts.items():
        if not obj:
            continue
        p = i18n_root / f"{lang}.json"
        try:
            cur_text = p.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
        # We'll rely on a per-key changed flag set by the caller; here we just
        # write the (possibly-mutated) dict to disk.
        if dry:
            continue
        # Detect change: serialize and compare.
        new_text = json.dumps(obj, ensure_ascii=False, indent=2, separators=(",", ": "))
        if new_text != cur_text:
            p.write_text(new_text, encoding="utf-8")
            # count by counting "blog.<slug>.p_text." entries that look like
            # reading-time keys; we don't track per-key counts in this
            # optimization, so we just return 1 per file changed.
            n_changed[lang] = 1
    return n_changed


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2
    i18n_root = root / "i18n"
    if not i18n_root.is_dir():
        print(f"i18n dir not found: {i18n_root}", file=sys.stderr)
        return 2

    # Collect ALL blog HTML files (EN + 8 i18n langs). Each gets its own
    # word count and JSON-LD update since translation length differs.
    en_blog = root / "blog"
    html_targets: list[Path] = []
    if en_blog.is_dir():
        for d in sorted(en_blog.iterdir()):
            if d.is_dir() and (d / "index.html").is_file():
                html_targets.append(d / "index.html")
    for lang in ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"]:
        lang_blog = root / lang / "blog"
        if not lang_blog.is_dir():
            continue
        for d in sorted(lang_blog.iterdir()):
            if d.is_dir() and (d / "index.html").is_file():
                html_targets.append(d / "index.html")
    if not html_targets:
        print("no blog posts found", file=sys.stderr)
        return 1

    # Load i18n dicts ONCE.
    dicts = load_i18n_dicts(i18n_root)
    n_html = 0
    sample_lines: list[str] = []
    seen_slugs: set[str] = set()  # for sample output, only first per slug

    for html_path in html_targets:
        slug = html_path.parent.name
        try:
            text = html_path.read_text(encoding="utf-8")
        except Exception:
            continue
        word_count = count_words(text)
        minutes = reading_minutes(word_count)

        new_text, html_changed = update_article_json_ld(text, word_count, minutes)
        if html_changed and not args.dry_run:
            html_path.write_text(new_text, encoding="utf-8")
            n_html += 1

        # Update each lang's dict for this slug (only once per slug — the
        # dict entry is the same key in en/zh/etc.; we don't need to
        # re-derive per-language word counts for the dict value).
        if slug not in seen_slugs:
            seen_slugs.add(slug)
            for lang in LANGS:
                update_dict_for_slug(dicts[lang], slug, minutes)
            if len(sample_lines) < 8:
                old_tr = ""
                m = re.search(r'"timeRequired":"(PT\d+M)"', text)
                if m:
                    old_tr = m.group(1)
                sample_lines.append(
                    f"  {slug}: words={word_count}, {old_tr}→PT{minutes}M, "
                    f"reading='{minutes} min read'"
                )

    # Write dicts once at the end — only if changed (compare length + content).
    n_dict_changed = 0
    for lang in LANGS:
        obj = dicts[lang]
        if not obj:
            continue
        p = i18n_root / f"{lang}.json"
        try:
            cur = p.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
        # Quick check: serialize and compare. If equal, skip the write.
        new_text = json.dumps(obj, ensure_ascii=False, indent=2, separators=(",", ": "))
        if new_text != cur:
            if not args.dry_run:
                p.write_text(new_text, encoding="utf-8")
            n_dict_changed += 1

    print("Sample updates:")
    for s in sample_lines:
        print(s)
    mode = "DRY RUN" if args.dry_run else "DONE"
    print(f"\n{mode}: html JSON-LD updated={n_html}, i18n dicts changed={n_dict_changed}/10")
    return 0


if __name__ == "__main__":
    sys.exit(main())
