"""Normalize indentation of the 3 newly-inserted <video> opening tags to match the project's
28-space gallery-card-img indent (vs the over-indented 56 spaces I accidentally wrote)."""
import io
import re

path = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai\gallery\index.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    s = f.read()

# Match exactly the 3 newly-inserted lines and trim 28 leading spaces.
pat = re.compile(
    r"^( {56})(<video controls autoplay muted loop playsinline preload=\"none\" width=\"1280\" height=\"720\" poster=\"/images/case-(?:ahmed-layla-broadcast|rodriguez-glamorous-opener|mei-jin-celebrity-package))",
    re.MULTILINE,
)
new, n = pat.subn(r"                            \2", s)
print(f"Replaced {n} lines (expected 3)")
with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(new)
