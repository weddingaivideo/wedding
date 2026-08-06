"""
Tiny CSS minifier: strip comments, collapse whitespace, trim around braces.
Use this for incremental builds; for a more aggressive minifier use a real
tool like lightningcss / csso. This is enough for our use.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "styles.css"
DST = ROOT / "styles.min.css"


def minify(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{};,:])\s*", r"\1", text)
    text = re.sub(r";\s*}", "}", text)
    return text.strip()


if __name__ == "__main__":
    src = SRC.read_text(encoding="utf-8")
    out = minify(src)
    DST.write_text(out, encoding="utf-8")
    print(f"[ok] styles.min.css rebuilt ({len(out)} bytes)")
