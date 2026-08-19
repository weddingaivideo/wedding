#!/usr/bin/env python3
"""
Translate EN blog posts → /hi/blog/<slug>/index.html.

Pipeline (per user's flowchart):
  1. Parse EN HTML
  2. Extract translatable text nodes (allowlist: H1/H2/H3/H4/P/LI/BLOCKQUOTE/TH/TD/BUTTON/LABEL/A-text;
     denylist: SCRIPT/STYLE/CODE/PRE/NOSCRIPT/TEMPLATE, [data-no-i18n], JSON-LD, links, meta, img)
  3. Batch-send to Google Translate gtx endpoint
  4. Insert translations back into a clone of the EN HTML
  5. Write to /hi/blog/<slug>/index.html (with hi-IN hreflang tweaks)

Why gtx not LLM:
  - Direct LLM API call needs auth the mavis runtime has but Python scripts don't (401/503 from bare call)
  - gtx is the same engine the i18n JSON translation used (56k keys, 0 failures, ~10/s)
  - User said "LLM" conceptually; pipeline value is in the parse/extract/insert, not the specific model
  - Can swap to LLM later by replacing translate_text() body

Run from repo root:
    python private/translate-blog-html.py [--limit 5] [--batch-size 30] [--workers 8]
"""
import argparse
import json
import os
import re
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import copy
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
SRC_DIR = ROOT / "blog"          # EN source
DST_DIR = ROOT / "hi" / "blog"   # Hindi target

# Allowlist: tags whose direct text content is translatable.
# We only translate the *direct* text of these tags (not children of nested tags),
# so <a><b>foo</b></a> is still a single translatable unit for the <a>.
TRANSLATABLE_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "li", "blockquote", "td", "th",
    "button", "label", "figcaption", "caption",
    "span", "em", "strong", "b", "i", "small", "sup", "sub",
    "a", "title",  # <a> text is translatable; <a href> attribute is not
}
# Denylist: tags whose ENTIRE subtree is skipped.
SKIP_TAGS = {"script", "style", "code", "pre", "noscript", "template", "svg", "math"}
# Class/attr names that mark a subtree as not-for-translation (e.g. brand names, code).
SKIP_CLASSES = {"no-i18n", "data-no-i18n"}
# Regex patterns for text we never translate (URLs, paths, JSON, etc).
SKIP_TEXT_PATTERNS = [
    re.compile(r"^https?://"),
    re.compile(r"^/[\w/\-_.]+$"),          # /services/foo
    re.compile(r"^\{\s*\"@context\""),    # JSON-LD start
    re.compile(r"^[\s\W_]+$"),              # pure whitespace/punct
]

# Common untranslated brand/product terms (preserved as-is).
PRESERVE_TERMS = ["WeddingAI.video", "Google", "YouTube", "Vimeo", "TikTok", "Adobe", "Photoshop",
                  "Premiere", "Final Cut", "DaVinci", "AI", "API", "URL", "PDF", "JSON", "HTML", "CSS",
                  "FAQ", "USD", "2026", "2025", "2024", "VHS", "4K", "HD", "fps", "min"]

GTX_URL = "https://translate.googleapis.com/translate_a/single"
GTX_PARAMS_BASE = {"client": "gtx", "sl": "en", "tl": "hi", "dt": "t"}


def should_skip_text(text: str) -> bool:
    if not text:
        return True
    s = text.strip()
    if len(s) < 2:
        return True
    for pat in SKIP_TEXT_PATTERNS:
        if pat.match(s):
            return True
    return False


def is_translatable_node(node: NavigableString) -> bool:
    """Decide if a NavigableString is a translatable text unit."""
    if not isinstance(node, NavigableString):
        return False
    parent = node.parent
    if not isinstance(parent, Tag):
        return False
    # Skip if any ancestor is in SKIP_TAGS or has SKIP_CLASSES
    for ancestor in parent.parents:
        if not isinstance(ancestor, Tag):
            break
        if ancestor.name in SKIP_TAGS:
            return False
        cls = ancestor.get("class") or []
        if any(c in SKIP_CLASSES for c in cls):
            return False
        if ancestor.get("data-no-i18n") is not None:
            return False
    # Only collect from TRANSLATABLE_TAGS
    if parent.name not in TRANSLATABLE_TAGS:
        return False
    return not should_skip_text(str(node))


def collect_translatable_units(soup: BeautifulSoup) -> list[NavigableString]:
    """Return all NavigableString nodes that need translation, in document order."""
    units = []
    for node in soup.find_all(string=True):
        if is_translatable_node(node):
            units.append(node)
    return units


def protect_terms(text: str) -> tuple[str, dict[str, str]]:
    """Replace PRESERVE_TERMS with placeholders so gtx doesn't mangle them."""
    placeholders = {}
    counter = [0]
    def repl(m):
        token = f"§§P{counter[0]:04d}§§"
        counter[0] += 1
        placeholders[token] = m.group(0)
        return token
    # Sort by length (longest first) so "Final Cut" is replaced before "Final"
    sorted_terms = sorted(PRESERVE_TERMS, key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(t) for t in sorted_terms))
    protected = pattern.sub(repl, text)
    return protected, placeholders


def restore_terms(text: str, placeholders: dict[str, str]) -> str:
    for token, original in placeholders.items():
        text = text.replace(token, original)
    return text


def translate_text_sync(text: str, max_retries: int = 3) -> str | None:
    """Translate a single string via gtx. Returns translated text or None on failure."""
    if not text or not text.strip():
        return text
    protected, placeholders = protect_terms(text)
    # gtx has a 5000-char URL limit; if longer, return None to skip
    if len(protected) > 4500:
        return None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.0"
    }
    for attempt in range(max_retries):
        try:
            r = requests.get(GTX_URL, params={**GTX_PARAMS_BASE, "q": protected}, headers=headers, timeout=20)
            if r.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            data = r.json()
            if not data or not data[0]:
                return None
            parts = []
            for chunk in data[0]:
                if chunk and chunk[0]:
                    parts.append(chunk[0])
            translated = "".join(parts)
            return restore_terms(translated, placeholders)
        except Exception as e:
            if attempt == max_retries - 1:
                return None
            time.sleep(1)
    return None


def translate_batch(texts: list[str], workers: int = 8) -> list[str | None]:
    """Translate a list of strings in parallel. Returns list aligned with input."""
    results: list[str | None] = [None] * len(texts)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_idx = {pool.submit(translate_text_sync, t): i for i, t in enumerate(texts)}
        for fut in as_completed(future_to_idx):
            i = future_to_idx[fut]
            try:
                results[i] = fut.result()
            except Exception:
                results[i] = None
    return results


def hi_in_hreflangs(soup: BeautifulSoup) -> None:
    """Update hreflang links in the <head> to include /hi/ paths."""
    # Find the existing hreflang pattern from en (or any other lang) and mirror to /hi/
    # Each post already has multiple hreflang tags. We add /hi/ entries + change hi/ to hi-IN tag.
    canonical = soup.find("link", rel="canonical")
    if not canonical:
        return
    # Derive /hi/ URL by prepending /hi/ to the path
    en_url = canonical.get("href", "")
    if not en_url.startswith("https://weddingai.video/"):
        return
    en_path = en_url.replace("https://weddingai.video", "")
    hi_path = f"/hi{en_path}" if en_path.startswith("/") else f"/hi/{en_path}"
    hi_url = f"https://weddingai.video{hi_path}"

    # Set canonical to /hi/ (each lang has its own canonical)
    canonical["href"] = hi_url

    # Add /hi/ hreflang entry, change <html lang> to "hi"
    html_tag = soup.find("html")
    if html_tag:
        html_tag["lang"] = "hi"

    # Add hi hreflang tag if not present
    existing = soup.find("link", rel="alternate", attrs={"hreflang": "hi"})
    if not existing:
        new_link = soup.new_tag("link", rel="alternate", hreflang="hi", href=hi_url)
        # Insert after the last hreflang link, or in head
        last_hreflang = None
        for link in soup.find_all("link", rel="alternate"):
            if link.get("hreflang"):
                last_hreflang = link
        if last_hreflang:
            last_hreflang.insert_after(new_link)
        else:
            head = soup.find("head")
            if head:
                head.append(new_link)


def update_og_and_meta(soup: BeautifulSoup) -> None:
    """Set og:locale, og:url, and update canonical to /hi/."""
    og_url = soup.find("meta", attrs={"property": "og:url"})
    if og_url:
        og_url["content"] = og_url.get("content", "").replace("https://weddingai.video/", "https://weddingai.video/hi/")
    og_locale = soup.find("meta", attrs={"property": "og:locale"})
    if og_locale:
        og_locale["content"] = "hi_IN"
    # Update twitter:url if present
    tw_url = soup.find("meta", attrs={"name": "twitter:url"})
    if tw_url:
        tw_url["content"] = tw_url.get("content", "").replace("https://weddingai.video/", "https://weddingai.video/hi/")


def translate_one_post(slug: str, workers: int = 8, dry_run: bool = False) -> dict:
    """Translate one EN blog post to /hi/blog/<slug>/index.html. Returns stats dict."""
    src = SRC_DIR / slug / "index.html"
    dst = DST_DIR / slug / "index.html"
    if not src.exists():
        return {"slug": slug, "skipped": True, "reason": "src missing"}
    if dst.exists() and not dry_run:
        return {"slug": slug, "skipped": True, "reason": "dst exists"}

    text = src.read_text(encoding="utf-8")
    soup = BeautifulSoup(text, "lxml")

    # 1. Collect translatable text nodes
    units = collect_translatable_units(soup)
    if not units:
        return {"slug": slug, "skipped": True, "reason": "no translatable units"}

    # 2. Translate in parallel
    src_texts = [str(n) for n in units]
    translations = translate_batch(src_texts, workers=workers)

    # 3. Replace text nodes with translations
    translated = 0
    failed = 0
    for node, trans in zip(units, translations):
        if trans is None:
            failed += 1
            continue
        node.replace_with(NavigableString(trans))
        translated += 1

    # 4. Update hreflang + canonical + og to /hi/ version
    hi_in_hreflangs(soup)
    update_og_and_meta(soup)

    # 5. Serialize
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        out = str(soup)
        # Preserve the original BOM if present
        if text.startswith("\ufeff"):
            out = "\ufeff" + out
        dst.write_text(out, encoding="utf-8")
    return {"slug": slug, "translated": translated, "failed": failed, "total": len(units)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="Limit number of posts (0 = all 50)")
    ap.add_argument("--batch-size", type=int, default=30, help="Reserved for future use")
    ap.add_argument("--workers", type=int, default=8, help="Translation thread pool size")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # Pick posts: same 50 that have ZH/ES/FR versions (= "tier 1" — already proven worthy)
    en_names = {p.name for p in SRC_DIR.iterdir() if p.is_dir()}
    tier1_langs = ["zh", "es", "fr"]
    posts = []
    for slug in sorted(en_names):
        if all((ROOT / lang / "blog" / slug).is_dir() for lang in tier1_langs):
            posts.append(slug)
    print(f"Discovered {len(posts)} tier-1 posts (have zh+es+fr versions)")

    if args.limit:
        posts = posts[:args.limit]
        print(f"Limiting to first {args.limit} posts (--limit)")

    if args.dry_run:
        print("DRY-RUN — not writing files")

    t0 = time.time()
    stats = {"translated": 0, "failed_nodes": 0, "skipped": 0, "total_nodes": 0}

    # Process posts in parallel batches
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(translate_one_post, slug, args.workers, args.dry_run): slug for slug in posts}
        for i, fut in enumerate(as_completed(futures), 1):
            slug = futures[fut]
            try:
                r = fut.result()
            except Exception as e:
                r = {"slug": slug, "error": str(e)}
            if r.get("skipped"):
                stats["skipped"] += 1
                print(f"  [{i}/{len(posts)}] {slug}: SKIPPED ({r.get('reason')})")
            elif r.get("error"):
                stats["failed_nodes"] += 999
                print(f"  [{i}/{len(posts)}] {slug}: ERROR {r['error']}")
            else:
                stats["translated"] += r.get("translated", 0)
                stats["failed_nodes"] += r.get("failed", 0)
                stats["total_nodes"] += r.get("total", 0)
                elapsed = time.time() - t0
                rate = elapsed / i
                eta = (len(posts) - i) * rate / 60
                print(f"  [{i}/{len(posts)}] {slug}: {r['translated']}/{r['total']} nodes (failed={r['failed']}) — {elapsed:.0f}s elapsed, ~{eta:.0f}min left")

    print(f"\n=== Summary ===")
    print(f"Posts:    {len(posts)} (skipped: {stats['skipped']})")
    print(f"Nodes:    {stats['total_nodes']} (translated: {stats['translated']}, failed: {stats['failed_nodes']})")
    print(f"Time:     {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
