"""
Bump cache buster to 3.22 across all HTML and js/i18n.js.
Touches:
  - i18n.js?v=3.21  -> i18n.js?v=3.22   (in every HTML)
  - styles.min.css?v=3.20  -> styles.min.css?v=3.21   (in every HTML)
  - I18N_VERSION = "3.21"  -> I18N_VERSION = "3.22"  (in js/i18n.js)

Run after any change to i18n JSON files or js/i18n.js, before deploy.
"""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
EXCLUDE_DIRS = {"admin", "functions", "tmp", "__pycache__", "qa", "i18n", "styles", "scripts", "docs", "search"}

# Bump pairs: (old, new)
HTML_BUMPS = [
    ("/js/i18n.js?v=3.21", "/js/i18n.js?v=3.22"),
    ("/styles.min.css?v=3.20", "/styles.min.css?v=3.21"),
]
I18N_JS_BUMPS = [
    ('var I18N_VERSION = "3.21"', 'var I18N_VERSION = "3.22"'),
]

def process_html(p: Path) -> int:
    text = p.read_text(encoding='utf-8', errors='ignore')
    n = 0
    for old, new in HTML_BUMPS:
        if old in text:
            n += text.count(old)
            text = text.replace(old, new)
    if n:
        p.write_text(text, encoding='utf-8')
    return n

def process_i18n_js() -> int:
    p = ROOT / "js" / "i18n.js"
    text = p.read_text(encoding='utf-8')
    n = 0
    for old, new in I18N_JS_BUMPS:
        if old in text:
            n += text.count(old)
            text = text.replace(old, new)
    if n:
        p.write_text(text, encoding='utf-8')
    return n

if __name__ == "__main__":
    total = 0
    for f in ROOT.rglob("*.html"):
        parts = {str(p) for p in f.parts}
        if parts & EXCLUDE_DIRS:
            continue
        if f.name == "google-site-verification.html":
            continue
        n = process_html(f)
        if n:
            rel = f.relative_to(ROOT)
            print(f"  {rel}: {n} bumps")
            total += n
    n = process_i18n_js()
    print(f"  js/i18n.js: {n} bumps")
    total += n
    print(f"\nTotal: {total} cache-buster bumps applied (3.21 -> 3.22 / 3.20 -> 3.21)")
