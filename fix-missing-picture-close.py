"""
Fix <picture>> double-gt bug from the previous fix script, and properly close
<picture> blocks. Use a simpler regex-based approach: for every <picture>...
that doesn't have a matching </picture>, insert one right after the <img>
inside it.
"""
import re
from pathlib import Path

ROOT = Path('.')
files = list(ROOT.rglob('*.html'))
files = [p for p in files if p.name != 'google-site-verification.html']

n = 0
for f in sorted(files):
    text = f.read_text(encoding='utf-8')
    original = text
    # 1) Fix the double-> from the buggy previous run: <picture>> -> <picture>
    text = text.replace('<picture>>', '<picture>')
    # 2) Remove any </picture> that was inserted in the WRONG place
    #    (e.g. </picture> immediately after <picture> with no source/img in between)
    text = re.sub(r'<picture>\s*</picture>', '<picture>', text)

    # 3) For <picture> blocks without a closing, find the <img ...> inside
    #    and append </picture> right after the <img ...> tag.
    # We process iteratively to handle multiple unclosed pictures.
    changed = True
    while changed:
        changed = False
        # Find <picture> with no </picture> before next <picture> or end-of-section
        m = re.search(r'<picture>(?!.*?</picture>)(<source[^>]+>(?:<source[^>]+>)*<img[^>]+>)', text, re.DOTALL)
        if m:
            # Insert </picture> right after the <img ...> tag
            insert_pos = m.end()
            text = text[:insert_pos] + '</picture>' + text[insert_pos:]
            changed = True

    if text != original:
        f.write_text(new if False else text, encoding='utf-8') if False else f.write_text(text, encoding='utf-8')
        n += 1
        rel = f.relative_to(ROOT)
        print(f"[fixed] {rel}")

print(f"\nDone. {n} file(s) fixed")
