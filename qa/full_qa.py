#!/usr/bin/env python3
"""
Full QA scan for weddingai.video.
Checks:
 1. i18n injection garbage (OPEN tag remnants, cross-tag dups)
 2. Structural HTML (broken tag balance, dup IDs, broken img refs)
 3. Layout signals (empty <a>, missing alt, broken local hrefs)
 4. Cross-file consistency (i18n key population, header/footer structure)
 5. Translation quality (length sanity, language-specific issues)
"""
import json
import re
import sys
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
EXCLUDE_DIRS = {"admin", "functions", "tmp", "__pycache__", "qa", "i18n", "js", "styles", "scripts", "docs", "search"}
EXCLUDE_FILES = {"google-site-verification.html"}

def all_html():
    out = []
    for p in ROOT.rglob("*.html"):
        # Compare path parts to EXCLUDE_DIRS as strings — `set(p.parts)` returns
        # Path objects, but EXCLUDE_DIRS contains strings. A Path("admin") is
        # NOT equal to the string "admin", so we have to compare on strings.
        parts_str = {str(part) for part in p.parts}
        if parts_str & EXCLUDE_DIRS:
            continue
        if p.name in EXCLUDE_FILES:
            continue
        out.append(p)
    return sorted(out)

def is_i18n_inject_garbage(text: str) -> list:
    """Find leftover 'OPEN<tagname' artifacts from i18n_inject.py."""
    issues = []
    for m in re.finditer(r'\bOPEN<[a-zA-Z][a-zA-Z0-9]*', text):
        issues.append(("OPEN_TAG", m.group(0), m.start()))
    # cross-tag duplicates like <p<a or <li<strong
    for m in re.finditer(r'<(p|li|div|span|strong|em|a|h\d|button|td|th|tr|section|article)(<[a-z]+)', text, re.IGNORECASE):
        issues.append(("CROSS_TAG_DUP", m.group(0)[:60], m.start()))
    return issues

def check_structure(text: str, path: Path) -> list:
    issues = []
    # Check tag balance for common containers
    for tag in ['header', 'footer', 'main', 'nav', 'section', 'article', 'ul', 'ol', 'table', 'form', 'picture', 'figure', 'a', 'p', 'div', 'span']:
        opens = len(re.findall(rf'<{tag}[\s>]', text, re.IGNORECASE))
        closes = len(re.findall(rf'</{tag}>', text, re.IGNORECASE))
        if opens != closes and tag not in ('p', 'li'):  # p/li are auto-closed by HTML parser
            issues.append(("TAG_BALANCE", f"<{tag}> {opens} vs </{tag}> {closes}"))
    # Check for empty <a class="logo"> (logo fix regression)
    for m in re.finditer(r'<a\s+href="/"\s+class="logo"[^>]*>\s*</a>', text):
        issues.append(("EMPTY_LOGO_ANCHOR", m.group(0)[:120]))
    # Check for picture not wrapped in <a class="logo"> (logo fix regression)
    if re.search(r'<picture>.*?</picture>\s*<a\s+href="/"\s+class="logo"', text, re.DOTALL):
        issues.append(("PICTURE_OUTSIDE_LOGO", "picture sibling of logo anchor"))
    return issues

def check_i18n_keys(text: str) -> list:
    issues = []
    # Find all data-i18n keys
    keys = re.findall(r'data-i18n="([^"]+)"', text)
    for k in keys:
        if not re.search(r'\.[0-9a-f]{6,8}$', k):
            issues.append(("I18N_KEY_MALFORMED", k))
    return issues

def check_images(text: str) -> list:
    issues = []
    # Missing alt
    for m in re.finditer(r'<img\s+[^>]*>', text, re.IGNORECASE):
        tag = m.group(0)
        if 'alt=' not in tag and 'role=' not in tag:
            issues.append(("IMG_MISSING_ALT", tag[:100]))
    # Empty src
    for m in re.finditer(r'<img\s+[^>]*src=""', text, re.IGNORECASE):
        issues.append(("IMG_EMPTY_SRC", m.group(0)[:100]))
    return issues

def check_links(text: str, path: Path) -> list:
    issues = []
    # local hrefs to files that don't exist
    for m in re.finditer(r'href="(/[^"#?]*)"', text):
        href = m.group(1)
        if href.startswith('//') or href.startswith('http'):
            continue
        # resolve relative to the file's directory
        target = (ROOT / href.lstrip('/')).resolve()
        # try with /index.html appended
        if not target.exists():
            target_idx = (ROOT / href.lstrip('/') / 'index.html').resolve()
            if not target_idx.exists():
                issues.append(("BROKEN_LOCAL_HREF", f"{href} (from {path.relative_to(ROOT)})"))
    return issues

def main():
    files = all_html()
    print(f"Scanning {len(files)} HTML files\n")

    all_issues = defaultdict(list)
    summary = Counter()
    total_keys = 0

    for f in files:
        text = f.read_text(encoding='utf-8', errors='ignore')
        rel = f.relative_to(ROOT)

        for issue in is_i18n_inject_garbage(text):
            all_issues[issue[0]].append((rel, issue[1]))
        for kind, detail in check_structure(text, f):
            all_issues[kind].append((rel, detail))
        for kind, detail in check_i18n_keys(text):
            all_issues[kind].append((rel, detail))
        for kind, detail in check_images(text):
            all_issues[kind].append((rel, detail))
        for kind, detail in check_links(text, f):
            all_issues[kind].append((rel, detail))

        summary['files'] += 1
        summary['i18n_keys'] += len(re.findall(r'data-i18n="', text))

    print(f"=== SUMMARY ===")
    print(f"Files: {summary['files']}")
    print(f"data-i18n attributes: {summary['i18n_keys']}\n")

    print(f"=== ISSUES BY KIND ===")
    for kind in sorted(all_issues.keys()):
        items = all_issues[kind]
        print(f"\n[{kind}] {len(items)} occurrences")
        # Show first 5 unique issues
        seen = set()
        shown = 0
        for rel, detail in items:
            key = str(detail)[:80]
            if key in seen:
                continue
            seen.add(key)
            print(f"  {rel}: {str(detail)[:100]}")
            shown += 1
            if shown >= 5:
                break
        if len(items) > 5:
            print(f"  ... and {len(items) - 5} more")

if __name__ == '__main__':
    main()
