"""
Inline critical CSS for index.html (the LCP page) so the first paint happens
without waiting for styles.min.css. Other pages keep the async pattern since
they're not the LCP source for Lighthouse scoring.

Critical CSS = rules needed to render above-the-fold content (header + hero).
We hand-pick the rules to keep the inline block small (~3-4 KB max).

We add a <style id="critical-css"> block right after the async CSS link.
The browser applies the inlined rules first, then styles.min.css layers on
without visual change (same rules + non-critical rules).
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
index = ROOT / "index.html"
css = (ROOT / "styles.min.css").read_text(encoding="utf-8")

# Extract the CSS variables block (:root {...})
def extract_rule(css_text, selector):
    """Find first rule starting with `selector {` and return just that rule."""
    pat = re.compile(rf'({re.escape(selector)}\s*\{{[^{{}}]*\}})', re.DOTALL)
    m = pat.search(css_text)
    return m.group(1) if m else None

# Extract multiple comma-separated selectors that share a rule body
def extract_rule_for_selectors(css_text, selectors):
    """Find rule whose selector matches any of the provided, OR comma-list."""
    for sel in selectors:
        rule = extract_rule(css_text, sel)
        if rule:
            return rule
    return None

# The critical CSS we want to inline. These are hand-picked to cover
# above-the-fold (header + hero) without ballooning size.
critical_selectors = {
    ":root": ":root",
    "*,*::before,*::after": "*,::after,::before",  # matches the minified version
    "html": "html",
    "body": "body",
    "img,video": "img,video",
    "a": "a",
    "ol,ul": "ol,ul",
    "button": "button",
    "h1-h6": "h1,h2,h3,h4,h5,h6",
    ".container": ".container",
    ".btn": ".btn",
    ".btn-primary": ".btn-primary",
    ".btn-primary:hover": ".btn-primary:hover",
    ".btn-secondary": ".btn-secondary",
    ".site-header": ".site-header",
    ".container.header-inner": ".header-inner",
    ".logo": ".logo",
    ".logo img": ".logo img",
    ".main-nav": ".main-nav",
    ".nav-list": ".nav-list",
    ".mobile-menu-toggle": ".mobile-menu-toggle",
    ".hero": ".hero",
    ".hero-bg": ".hero-bg",
    ".hero-bg img": ".hero-bg img",
    ".hero-overlay": ".hero-overlay",
    ".hero-content": ".hero-content",
    ".hero-title": ".hero-title",
    ".hero-subtitle": ".hero-subtitle",
    ".hero-cta": ".hero-cta",
    ".hero-trust": ".hero-trust",
    "section-dark": ".section-dark",
    "section-dark-p": ".section-dark p",
    "section-dark-h2": ".section-dark h2",
}

collected = []
for name, sel in critical_selectors.items():
    rule = extract_rule(css, sel)
    if rule:
        collected.append(rule)

# Special handling for media query rules
# (e.g., "@media (max-width: 768px) { .mobile-menu-toggle { ... } }")
# We need to extract complete media query blocks for the critical rules.
def find_all_media_blocks(css_text):
    """Split CSS into individual @media blocks by counting braces properly."""
    blocks = []
    i = 0
    while i < len(css_text):
        # Find start of next @media
        idx = css_text.find("@media", i)
        if idx == -1:
            break
        # Find the opening brace after the media query condition
        brace_start = css_text.find("{", idx)
        if brace_start == -1:
            i = idx + 1
            continue
        # Count braces to find matching closing brace
        depth = 1
        pos = brace_start + 1
        while pos < len(css_text) and depth > 0:
            ch = css_text[pos]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            pos += 1
        block = css_text[idx:pos]
        blocks.append(block)
        i = pos
    return blocks

def extract_media_queries_for_selectors(css_text, selectors):
    """Find all @media blocks that contain any of the given selectors.
    Each unique @media block is returned only once."""
    all_blocks = find_all_media_blocks(css_text)
    seen = set()
    result = []
    for block in all_blocks:
        for sel in selectors:
            if sel in block:
                # Use first 150 chars as dedup key (the @media condition part)
                key = block[:150]
                if key not in seen:
                    seen.add(key)
                    result.append(block)
                break  # only add once per block
    return result

# Add @media for hero and mobile-menu-toggle
media_selectors = [".hero-content", ".hero-title", ".hero-bg", ".mobile-menu-toggle",
                   ".main-nav", ".nav-list", ".logo", ".hero-cta", ".site-header",
                   ".hero-subtitle", ".hero-trust", ".hero"]
for mq in extract_media_queries_for_selectors(css, media_selectors):
    collected.append(mq)

# Build the inline <style> block
critical_css = "\n".join(collected)
# Strip comments to save bytes
critical_css = re.sub(r'/\*.*?\*/', '', critical_css, flags=re.DOTALL)
# Collapse whitespace
critical_css = re.sub(r'\s+', ' ', critical_css).strip()

print(f"Critical CSS size: {len(critical_css)} bytes")
print(f"Rules collected: {len(collected)}")

# Inject into index.html as <style> right after the noscript
html = index.read_text(encoding="utf-8")
original = html

style_block = f'    <style id="critical-css">{critical_css}</style>'

# Idempotency: if a <style id="critical-css"> block already exists, replace it
# (don't append a duplicate). Match the whole block including closing </style>.
existing_pat = re.compile(r'\s*<style id="critical-css">.*?</style>', re.DOTALL)
existing_matches = list(existing_pat.finditer(html))
if existing_matches:
    # Replace the first occurrence with the new block; remove any further duplicates.
    first = existing_matches[0]
    new_html = html[:first.start()] + style_block + html[first.end():]
    # Strip any leftover duplicates that follow
    leftover = list(existing_pat.finditer(new_html))
    if len(leftover) > 1:
        # remove from the end backwards
        for m in reversed(leftover[1:]):
            new_html = new_html[:m.start()].rstrip() + new_html[m.end():]
    html = new_html
else:
    # Insert right before the <link rel="preload" href="styles.min.css">
    pat = r'(<link rel="preload" href="styles\.min\.css")'
    html = re.sub(pat, style_block + r'\n    \1', html, count=1)

if html != original:
    index.write_text(html, encoding="utf-8")
    print(f"[ok] index.html updated with {len(critical_css)} bytes of critical CSS")
else:
    print("[skip] no change")
