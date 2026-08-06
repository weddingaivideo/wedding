"""
Fix the broken desktop nav bar on the homepage.

Root cause
----------
`inject-critical-css.py` extracts CSS rules from styles.min.css into an
inline <style id="critical-css"> block in index.html. Its regex grabs the
first @media block containing `.main-nav`, which (wrongly) matches the
mobile-only @media (max-width:768px) block. The inlined result is then:

    .main-nav { display: none; ... mobile-only rules ... }
    .nav-list  { flex-direction: column; ... }

So the first paint on desktop hides the entire nav bar until the async
styles.min.css loads. styles.min.css itself is fine; only the inlined
critical CSS is wrong.

Fix
---
Bypass the broken extractor and write a known-good critical CSS block
directly into index.html. Bump the styles.min.css ?v= cache buster so
the new (correct) file reaches repeat visitors immediately.

Idempotent — safe to run multiple times.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"


def critical_css() -> str:
    """Hand-curated critical CSS for the LCP page (index.html).

    Covers above-the-fold: header + hero. ~3 KB.
    Uses explicit `.main-nav { display: block }` so even before
    styles.min.css loads, the desktop nav bar is visible.
    """
    return (
        # CSS variables
        ":root{--color-primary:#D4AF37;--color-primary-dark:#B8962E;--color-secondary:#2C2C2C;--color-accent:#E8D5B7;--color-bg:#FDFBF8;--color-bg-alt:#F5F0EA;--color-text:#2C2C2C;--color-text-light:#6B6B6B;--color-white:#FFFFFF;--color-border:#E5E0D8;--font-heading:'Playfair Display',Georgia,serif;--font-body:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;--spacing-xs:.5rem;--spacing-sm:1rem;--spacing-md:1.5rem;--spacing-lg:2rem;--spacing-xl:3rem;--spacing-2xl:5rem;--radius-sm:4px;--radius-md:8px;--radius-lg:16px;--radius-xl:24px;--shadow-sm:0 2px 8px rgba(0,0,0,.06);--shadow-md:0 4px 20px rgba(0,0,0,.08);--shadow-lg:0 8px 40px rgba(0,0,0,.12);--transition:.3s ease;--max-width:1200px}"
        # Reset + base
        "*,::after,::before{box-sizing:border-box;margin:0;padding:0}"
        "html{scroll-behavior:smooth;font-size:16px}"
        "body{color:var(--color-text);font-family:var(--font-body);background-color:var(--color-bg);line-height:1.6;-webkit-font-smoothing:antialiased}"
        "img,video{height:auto;display:block;max-width:100%}"
        "a{color:inherit;text-decoration:none}"
        "ol,ul{list-style:none}"
        "button{cursor:pointer;border:0;background:0 0;font-family:inherit}"
        "h1,h2,h3,h4,h5,h6{font-family:var(--font-heading);line-height:1.2;font-weight:600}"
        # Layout
        ".container{max-width:var(--max-width);margin:0 auto;padding:0 var(--spacing-md)}"
        ".btn{display:inline-flex;align-items:center;justify-content:center;gap:var(--spacing-xs);padding:.75rem 1.5rem;border-radius:var(--radius-md);font-size:.9375rem;font-weight:600;transition:var(--transition);white-space:nowrap}"
        ".btn-primary{background:var(--color-primary);color:var(--color-white)}"
        ".btn-primary:hover{background:var(--color-primary-dark);transform:translateY(-1px);box-shadow:var(--shadow-md)}"
        ".btn-secondary{background:0 0;color:var(--color-secondary);border:2px solid var(--color-secondary)}"
        # Header — explicit display:block on .main-nav (THE FIX)
        ".site-header{position:sticky;top:0;z-index:100;background:rgba(253,251,248,.95);backdrop-filter:blur(10px);border-bottom:1px solid var(--color-border)}"
        ".header-inner{display:flex;align-items:center;justify-content:space-between;height:72px}"
        ".logo{display:flex;align-items:center}"
        ".logo img{width:auto;height:auto;object-fit:contain;max-height:72px;max-width:400px}"
        # --- THE FIX: explicit desktop defaults ---
        ".main-nav{display:block}"
        ".main-nav .nav-list{display:flex;align-items:center;gap:var(--spacing-lg)}"
        ".main-nav a{font-size:.9375rem;font-weight:500;color:var(--color-text);transition:var(--transition)}"
        ".mobile-menu-toggle{display:none;flex-direction:column;gap:5px;padding:var(--spacing-xs)}"
        # Hero
        ".hero{position:relative;min-height:90vh;display:flex;align-items:center;overflow:hidden}"
        ".hero-bg{position:absolute;inset:0}"
        ".hero-overlay{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(44,44,44,.3)0,rgba(44,44,44,.5) 50%,rgba(44,44,44,.7) 100%)}"
        ".hero-content{position:relative;z-index:1;text-align:center;padding-top:var(--spacing-2xl);padding-bottom:var(--spacing-2xl)}"
        ".hero-title{font-size:clamp(2rem,5vw,3.5rem);color:var(--color-white);max-width:800px;margin:0 auto var(--spacing-md);text-shadow:0 2px 20px rgba(0,0,0,.3)}"
        ".hero-subtitle{font-size:clamp(1rem,2vw,1.25rem);color:rgba(255,255,255,.9);max-width:600px;margin:0 auto var(--spacing-lg)}"
        ".hero-cta{display:flex;flex-wrap:wrap;gap:var(--spacing-sm);justify-content:center;margin-bottom:var(--spacing-lg)}"
        ".hero-trust{font-size:.875rem;color:rgba(255,255,255,.75)}"
        ".section-dark{background:var(--color-secondary);color:#fff}"
        # Mobile @media — single, clean, not duplicated
        "@media (max-width:768px){"
        ".main-nav{display:none;position:absolute;top:72px;left:0;right:0;background:var(--color-white);border-top:1px solid var(--color-border);box-shadow:var(--shadow-md);padding:var(--spacing-md)}"
        ".main-nav.active{display:block}"
        ".main-nav .nav-list{flex-direction:column;align-items:flex-start;gap:var(--spacing-sm)}"
        ".mobile-menu-toggle{display:flex}"
        ".hero{min-height:80vh}"
        ".hero-cta{flex-direction:column;align-items:center}"
        ".hero-cta .btn{width:100%;max-width:280px}"
        "}"
    )


def rewrite_critical_css_block() -> None:
    if not INDEX.exists():
        sys.exit(f"[fail] {INDEX} missing")

    html = INDEX.read_text(encoding="utf-8")
    style_block = f'    <style id="critical-css">{critical_css()}</style>'

    pat = re.compile(r'\s*<style id="critical-css">.*?</style>', re.DOTALL)
    matches = list(pat.finditer(html))
    if matches:
        first = matches[0]
        new_html = html[: first.start()] + style_block + html[first.end() :]
        # Drop any further duplicates that snuck in
        leftover = list(pat.finditer(new_html))
        for m in reversed(leftover[1:]):
            new_html = new_html[: m.start()].rstrip() + new_html[m.end() :]
    else:
        preload = re.search(r'(<link rel="preload" href="/?styles\.min\.css")', html)
        if not preload:
            sys.exit("[fail] no styles.min.css preload link in index.html — can't anchor insertion")
        new_html = html[: preload.start()] + style_block + "\n    " + html[preload.start() :]

    INDEX.write_text(new_html, encoding="utf-8")
    print(f"[ok] index.html critical CSS rewritten ({len(critical_css())} bytes)")


def bump_cache_buster() -> None:
    """Bump styles.min.css?v=X.Y so the fixed CSS reaches the browser
    immediately, sidestepping the disk-cache vs HTTP-cache trap."""
    pattern = re.compile(r'(styles\.min\.css)(\?v=[0-9.]+)?')

    # Find current highest version across all HTML files
    max_v = 0.0
    for f in ROOT.rglob("*.html"):
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m in pattern.finditer(text):
            v = m.group(2)
            if v:
                try:
                    max_v = max(max_v, float(v.lstrip("?v=")))
                except ValueError:
                    pass
    # Continue from a sensible baseline if no existing version found
    next_v = f"v={max(max_v + 0.1, 3.12):.2f}"

    def repl(m):
        return f"{m.group(1)}?{next_v}"

    n = 0
    for f in ROOT.rglob("*.html"):
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "styles.min.css" not in text:
            continue
        new_text = pattern.sub(repl, text)
        if new_text != text:
            f.write_text(new_text, encoding="utf-8")
            n += 1
    print(f"[ok] cache-buster -> {next_v} on {n} HTML files")


if __name__ == "__main__":
    rewrite_critical_css_block()
    bump_cache_buster()
    print("\nDone. Verify by visiting / and checking the desktop nav bar is visible.")
