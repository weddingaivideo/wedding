"""Normalize indentation of round-2 video opening tags to 28 spaces (matching project style)."""
import io
import re

path = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai\gallery\index.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    s = f.read()

pat = re.compile(
    r"^( {56})(<video controls autoplay muted loop playsinline preload=\"none\" width=\"1376\" height=\"768\" poster=\"/images/case-(?:sarah-james-super8|anika-dev-save-the-date|maria-david-sunset-trailer))",
    re.MULTILINE,
)
new, n = pat.subn(r"                            \2", s)
print(f"Replaced {n} lines (expected 3)")
with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(new)
