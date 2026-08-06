"""Remove the <span class="case-tag">Article NN</span> spans from the
blog list page. They're redundant — the user just sees "Article 16"
above the title, which adds nothing.
Idempotent.
"""
import re
from pathlib import Path

LIST = Path(__file__).resolve().parent.parent / "blog" / "index.html"
text = LIST.read_text(encoding="utf-8")
new = re.sub(
    r'\s*<span class="case-tag">Article\s+\d+</span>',
    "",
    text,
)
LIST.write_text(new, encoding="utf-8")
n = text.count('class="case-tag">Article')
print(f"[ok] blog/index.html: {n} 'Article NN' tags removed")
