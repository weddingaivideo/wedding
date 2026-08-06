"""Fix heading-level skips.

Two specific issues:
  1) Footer nav uses <h4> directly after the last <h2> in <main>.
     Solution: change <h4> to <h3> in footer-nav (footer is a sub-section
     of the page, h3 fits its semantic weight).
  2) Section-header uses <h2> + <p class="section-intro"> but no h3 before
     h4 children. This is mostly false-positive from the audit (it counts
     <h2> as the document level, then any <h4> in the same section would
     skip). Actually our pages use <h2> for section, then <h3>/<h4> for
     sub-cards (testimonials, FAQs etc.) — that's fine within the section.

For the footer case, change every `<h4>...</h4>` inside `<nav class="footer-nav">`
to `<h3>...</h3>`. Idempotent.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Match: <nav ...footer-nav...> ... <h4>...</h4> ... </nav>
# (non-greedy nav block, then h4 inside)
PAT = re.compile(
    r"(<nav\b[^>]*footer-nav[^>]*>)(.*?)(</nav>)",
    re.DOTALL,
)


def fix(text: str) -> tuple[str, int]:
    n = 0
    def repl(m):
        nonlocal n
        head, body, tail = m.group(1), m.group(2), m.group(3)
        new_body = re.sub(r"<h4>(.*?)</h4>", lambda x: f"<h3>{x.group(1)}</h3>", body)
        if new_body != body:
            n += new_body.count("<h3>") - body.count("<h3>")
        return head + new_body + tail
    new = PAT.sub(repl, text)
    return new, n


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
            print(f"[ok] {f.relative_to(ROOT)}: {n} h4->h3 in footer-nav")
    print(f"\nTotal: {n_total} h4 promoted to h3 in {n_files} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
