#!/usr/bin/env python3
"""Insert a /pricing/ link into the main nav of every HTML file."""
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")

# Match the line that has the Get a Quote nav link and insert a Pricing link right before it.
# The line looks like: <li><a href="/order/" class="btn-nav" ...>...</a></li>
NAV_MARKER = '<li><a href="/order/" class="btn-nav"'
PRICING_NAV = (
    '<li><a href="/pricing/" title="View transparent pricing">'
    'Pricing</a></li>\n                    '
)

def main():
    count = 0
    for p in ROOT.rglob("*.html"):
        if any(seg in p.parts for seg in ("i18n", "qa", "tmp")):
            continue
        # skip the new /pricing/ page itself
        if p.name == "index.html" and p.parent.name == "pricing":
            continue
        raw = p.read_text(encoding="utf-8")
        if "/pricing/" in raw[:3000]:
            # already has pricing in nav (or somewhere high up)
            # only count if it has the exact <li> for nav pricing
            if '<li><a href="/pricing/" title="View transparent pricing">Pricing</a></li>' in raw:
                continue
        new = raw.replace(NAV_MARKER, PRICING_NAV + NAV_MARKER, 1)
        if new != raw:
            p.write_text(new, encoding="utf-8", newline="")
            count += 1
    print(f"  added Pricing nav link to {count} HTML files")


if __name__ == "__main__":
    main()
