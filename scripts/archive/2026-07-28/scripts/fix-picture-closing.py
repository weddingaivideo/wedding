"""Fix picture-tag nesting bug.

The current pattern is:
    <div class="X-img" role="img" ...>
        <picture><source ...><img ...>
    </div>
    </picture><div class="X-body">

But it should be:
    <div class="X-img" role="img" ...>
        <picture>
            <source ...>
            <img ...>
        </picture>
    </div>
    <div class="X-body">

The `</div>` closes the *img wrapper* early, then `</picture>` appears
*outside* the wrapper (and outside the parent role=img div), then the
body div opens. The HTML parser auto-closes, but W3C validators flag
"End tag picture seen, but there were open elements" and "Unclosed
element picture."

Two patterns to fix:
  1) </div>\s*</picture>\s*<div class="X-body|card">  (case-card, service-card)
  2) </div>\s*</picture>\s*<div class="hero-overlay">    (hero)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Pattern: </div> immediately followed by </picture> immediately followed by
# any opening <div> (this is the universal broken pattern).
PAT = re.compile(r"</div>(\s*)</picture>(\s*)(?=<div\b)")


def fix(text: str) -> tuple[str, int]:
    new = PAT.sub(r"</picture>\1</div>\2", text)
    return new, len(PAT.findall(text))


def main() -> int:
    n_files = 0
    n_total = 0
    for f in sorted(ROOT.rglob("*.html")):
        if "google-site-verification" in f.name:
            continue
        text = f.read_text(encoding="utf-8")
        new, n = fix(text)
        if n > 0:
            f.write_text(new, encoding="utf-8")
            n_files += 1
            n_total += n
            print(f"[ok] {f.relative_to(ROOT)}: {n} picture nests fixed")
    print(f"\nTotal: {n_total} picture nests fixed in {n_files} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
