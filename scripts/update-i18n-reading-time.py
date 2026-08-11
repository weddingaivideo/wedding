#!/usr/bin/env python3
"""
update-i18n-reading-time.py

Same as fix-reading-time.py but ONLY updates i18n HTML files (zh, es, fr, etc.)
— skips the EN blog (already done by fix-reading-time.py) and skips the
i18n dict updates (already done).

Each i18n post has its own translated word count, so the JSON-LD
timeRequired and wordCount need to be updated per language.

Usage: python scripts/update-i18n-reading-time.py [--root <path>] [--dry-run]
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

WPM = 250
ARTICLE_LD_RE = re.compile(
    r'<script\s+type="application/ld\+json"[^>]*>(\s*\{[\s\S]*?\})\s*</script>',
    re.IGNORECASE,
)
LANGS = ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"]


def count_words(html: str) -> int:
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


def update_article_json_ld(html: str, word_count: int, minutes: int) -> tuple[str, bool]:
    changed_any = False
    new_tr = f"PT{minutes}M"

    def repl(m: re.Match) -> str:
        nonlocal changed_any
        body = m.group(1)
        try:
            obj = json.loads(body)
        except json.JSONDecodeError:
            return m.group(0)
        if not isinstance(obj, dict) or obj.get("@type") != "Article":
            return m.group(0)
        if obj.get("timeRequired") == new_tr and obj.get("wordCount") == word_count:
            return m.group(0)
        obj["timeRequired"] = new_tr
        obj["wordCount"] = word_count
        changed_any = True
        return m.group(0).replace(body, json.dumps(obj, ensure_ascii=False, separators=(",", ":")))

    return ARTICLE_LD_RE.sub(repl, html), changed_any


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2

    # Collect all i18n blog HTML files.
    targets: list[Path] = []
    for lang in LANGS:
        lang_blog = root / lang / "blog"
        if not lang_blog.is_dir():
            continue
        for d in lang_blog.iterdir():
            if d.is_dir() and (d / "index.html").is_file():
                targets.append(d / "index.html")
    if not targets:
        print("no i18n blog posts found", file=sys.stderr)
        return 1

    print(f"Processing {len(targets)} i18n blog posts...")
    n_html = 0
    sample_lines: list[str] = []
    for i, html_path in enumerate(sorted(targets)):
        try:
            text = html_path.read_text(encoding="utf-8")
        except Exception:
            continue
        word_count = count_words(text)
        minutes = max(1, -(-word_count // WPM))
        new_text, changed = update_article_json_ld(text, word_count, minutes)
        if changed:
            if not args.dry_run:
                html_path.write_text(new_text, encoding="utf-8")
            n_html += 1
            if len(sample_lines) < 6:
                rel = html_path.relative_to(root)
                old_tr = ""
                m = re.search(r'"timeRequired":"(PT\d+M)"', text)
                if m:
                    old_tr = m.group(1)
                sample_lines.append(
                    f"  {rel}: words={word_count}, {old_tr}→PT{minutes}M"
                )
        if (i + 1) % 50 == 0:
            print(f"  ... {i+1}/{len(targets)} processed", file=sys.stderr)

    print("Sample updates:")
    for s in sample_lines:
        print(s)
    mode = "DRY RUN" if args.dry_run else "DONE"
    print(f"\n{mode}: i18n HTML JSON-LD updated={n_html}/{len(targets)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
