#!/usr/bin/env python3
"""
Comprehensive structural fix for weddingai.video HTML files.

Fixes (in order):
 1. Cross-tag dup `<TAG1<MIDDLE<TAG2` (no `>` between) — insert `>` at right place:
    - No MIDDLE: after TAG1 (sibling case): `<p<ahref` → `<p><a href`
    - With MIDDLE: after MIDDLE (child case): `<a href="X"<picture>` → `<a href="X"><picture>`
 2. <listyle= → <li style= (missing space)
 3. Orphan </li> with `<strong>...</strong> ...</li>` pattern — prepend `<li>`

Idempotent: running twice produces no further changes.
"""
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
EXCLUDE_DIRS = {"admin", "functions", "tmp", "__pycache__", "qa", "i18n", "js", "styles", "scripts", "docs"}

def should_process(p: Path) -> bool:
    if p.name == "google-site-verification.html": return False
    parts = set(p.parts)
    return not (parts & {Path(d) for d in EXCLUDE_DIRS})

def fix_crosstag(text: str) -> str:
    """Fix `<TAG1<MIDDLE<TAG2` patterns by inserting `>` at the right place."""
    # Match: <TAG1 (with optional attrs that don't include < or >) <TAG2
    # The greedy issue: we want the SHORTEST middle.
    # Pattern: <([a-zA-Z][a-zA-Z0-9]*)((?:[^<>]*?))<([a-zA-Z][a-zA-Z0-9]*)
    pattern = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)((?:[^<>]*?))<([a-zA-Z][a-zA-Z0-9]*)')

    def repl(m):
        tag1 = m.group(1)
        middle = m.group(2)  # may be empty
        tag2 = m.group(3)
        if not middle:
            # No attrs: close tag1 immediately, tag2 is sibling
            return f'<{tag1}><{tag2}'
        else:
            # Has attrs: close tag1 after attrs, tag2 is child
            return f'<{tag1}{middle}><{tag2}'

    return pattern.sub(repl, text)

def fix_text(text: str) -> str:
    orig = text

    # 1. Cross-tag dup: <TAG1<MIDDLE<TAG2
    text = fix_crosstag(text)

    # 1b. <ahref missing space (caused by i18n_inject removing space)
    text = re.sub(r'<ahref=', '<a href=', text)

    # 2. <listyle= → <li style= (missing space, 3 cases)
    text = re.sub(r'<listyle=', '<li style=', text)

    # 3. Orphan </li>: line-based fix
    new_lines = []
    for line in text.split('\n'):
        li_opens = len(re.findall(r'<li[\s>]', line))
        li_closes = len(re.findall(r'</li>', line))
        if li_closes > li_opens:
            n_needed = li_closes - li_opens
            m = re.match(r'^(\s*)(.*)$', line)
            if m:
                ws, content = m.group(1), m.group(2)
                line = ws + '<li>' * n_needed + content
        new_lines.append(line)
    text = '\n'.join(new_lines)

    return text

def main(dry_run: bool = False):
    total_files = 0
    for p in sorted(ROOT.rglob("*.html")):
        if not should_process(p): continue
        text = p.read_text(encoding='utf-8', errors='ignore')
        new_text = fix_text(text)
        if new_text != text:
            if not dry_run:
                p.write_text(new_text, encoding='utf-8')
            total_files += 1
            rel = p.relative_to(ROOT)
            # Compute diff stats
            n_crosstag = text.count('<a<picture') + text.count('<a href') - new_text.count('<a<picture')  # rough
            n_changes = sum(1 for a, b in zip(text.split('\n'), new_text.split('\n')) if a != b)
            print(f"  {rel}: {n_changes} lines changed")
    print(f"\nTotal: {total_files} files modified")

if __name__ == '__main__':
    dry = '--dry' in sys.argv
    main(dry_run=dry)
