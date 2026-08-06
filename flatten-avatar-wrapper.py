"""
1. Add missing </picture> closing tag to avatar pictures
2. Flatten unnecessary <div class="testimonial-avatar"><picture>...</picture></div>
   into <picture class="testimonial-avatar">...</picture>

Idempotent.
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
files = list(ROOT.rglob("*.html"))
files = [p for p in files if p.name != "google-site-verification.html"]

# Pattern matches the broken (missing </picture>) + div wrapper
# <div class="testimonial-avatar"><picture><source...><img...></div>
# The browser auto-closes <picture> when it sees </div>
pat = re.compile(
    r'<div class="testimonial-avatar">'
    r'<picture>'
    r'(<source[^>]+type="image/webp"[^>]*>)'
    r'(<img[^>]+>)'
    r'</div>'
)

n = 0
for p in files:
    text = p.read_text(encoding="utf-8")
    new_text = pat.sub(
        lambda m: f'<picture class="testimonial-avatar">{m.group(1)}{m.group(2)}</picture>',
        text
    )
    if new_text != text:
        p.write_text(new_text, encoding="utf-8")
        n += 1
        rel = p.relative_to(ROOT)
        print(f"[+] {rel}")

print(f"\nDone. {n} file(s) updated")
