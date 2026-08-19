"""Reset all blog page JSON-LD Article dates back to the original
2026-08-01 / 2026-08-04 pattern. Used to undo a buggy first attempt
at M-4 differentiation that assigned the same fallback date to every
post in the bad batch.
"""
import json
import re
from pathlib import Path

OLD_PUB = "2026-08-01"
OLD_MOD = "2026-08-04"

ARTICLE_RE = re.compile(
    r'(<script\s+type\s*=\s*"application/ld\+json"\s*>)(\{"@context":\s*"https://schema.org",\s*"@type":\s*"Article".*?\})(</script>)',
    re.IGNORECASE | re.DOTALL,
)
DATE_PUB_RE = re.compile(r'("datePublished"\s*:\s*")\d{4}-\d{2}-\d{2}(")')
DATE_MOD_RE = re.compile(r'("dateModified"\s*:\s*")\d{4}-\d{2}-\d{2}(")')

BLOG = Path("blog")
reset = 0
for p in sorted(BLOG.glob("*/index.html")):
    if p.parent.name == "blog":
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    m = ARTICLE_RE.search(text)
    if not m:
        continue
    block = m.group(2)
    try:
        data = json.loads(block)
    except Exception:
        continue
    if data.get("datePublished") == OLD_PUB:
        continue  # Already in original state
    # Reset to OLD values
    new_block = DATE_PUB_RE.sub(lambda m: m.group(1) + OLD_PUB + m.group(2), block, count=1)
    new_block = DATE_MOD_RE.sub(lambda m: m.group(1) + OLD_MOD + m.group(2), new_block, count=1)
    new_html = text[: m.start(2)] + new_block + text[m.end(2) :]
    p.write_bytes(new_html.encode("utf-8"))
    reset += 1
print(f"Reset {reset} files to {OLD_PUB} / {OLD_MOD}")
