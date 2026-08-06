"""
Insert Baidu Tongji (hm.baidu.com) tracking snippet into all production HTML files
of weddingai.video, right before </head>.

Skips:
  - google-site-verification.html  (GSC HTML-tag verification; must stay raw)
  - anything under tmp/            (scratch / staging, not deployed)
  - files that already have the snippet (idempotent)

Idempotent: re-running is safe. Will also clean up the broken v1 insertion
(`</script>    <!-- Baidu Tongji...` glued on the same line).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
BAIDU_ID = "784c824843f328ed5f8254991ef8b2f4"
SKIP_NAMES = {"google-site-verification.html"}
SKIP_DIR_PARTS = {"tmp"}

# Match the snippet as Baidu ships it (any leading whitespace on each line).
BAIDU_PRESENT = re.compile(
    r"var _hmt = _hmt \|\| \[\];.*?hm\.baidu\.com/hm\.js\?" + re.escape(BAIDU_ID) + r".*?\)\(\);",
    re.DOTALL,
)

# Match the full Baidu block we insert, INCLUDING our HTML comment, so we can
# strip a previously-broken insertion in one shot.
# - Leading whitespace (greedy) before the comment
# - The HTML comment line
# - The <script>...</script> block
# - Trailing whitespace + the leading "  \n" we add for separation
BAIDU_BLOCK_TO_STRIP = re.compile(
    r"[ \t]*<!-- Baidu Tongji \(hm\.baidu\.com\) — analytics -->\s*"
    r"<script>\s*"
    r"var _hmt = _hmt \|\| \[\];\s*"
    r"\(function\(\) \{[\s\S]*?\}\)\(\);\s*"
    r"</script>\s*",
)

# Snippet to insert. Leading "\n" guarantees separation from the previous
# line, even when the file had no trailing whitespace before </head>.
# 4-space indent matches project convention.
SNIPPET = (
    "\n    <!-- Baidu Tongji (hm.baidu.com) — analytics -->\n"
    "    <script>\n"
    "    var _hmt = _hmt || [];\n"
    "    (function() {\n"
    "      var hm = document.createElement(\"script\");\n"
    "      hm.src = \"https://hm.baidu.com/hm.js?" + BAIDU_ID + "\";\n"
    "      var s = document.getElementsByTagName(\"script\")[0]; \n"
    "      s.parentNode.insertBefore(hm, s);\n"
    "    })();\n"
    "    </script>\n"
)


def should_skip(path: Path) -> bool:
    if path.name in SKIP_NAMES:
        return True
    return any(part in SKIP_DIR_PARTS for part in path.parts)


def process(path: Path) -> str:
    """Return one of: 'inserted', 'rewritten', 'already-present', 'no-head', 'error'."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ERROR reading {path}: {e}", file=sys.stderr)
        return "error"

    # 0. If the file already has the standard Baidu block, leave it alone
    #    (true idempotency — no rewrite, no drift).
    if BAIDU_PRESENT.search(text):
        # Sanity check: make sure the block is on its own lines, not glued
        # to a previous </script> (the v1 broken pattern).
        if not re.search(r"</script>[ \t]+<!-- Baidu Tongji", text):
            return "already-present"
        # else: fall through to strip + re-insert

    # 1. Strip any previous Baidu block (clean up v1 broken insertion OR a
    #    previous clean run, idempotently).
    new_text, strip_count = BAIDU_BLOCK_TO_STRIP.subn("", text)

    # 2. Insert the snippet immediately before </head>.
    #    Simple, non-capturing match — avoid the (\s*) trap that glued
    #    </script> and <!-- Baidu ... together in v1.
    new_text, count = re.subn(
        r"</head>",
        lambda m: SNIPPET + "</head>",
        new_text,
        count=1,
        flags=re.IGNORECASE,
    )
    if count == 0:
        return "no-head"

    # 3. Preserve original line endings.
    if "\r\n" in text and "\r\n" not in SNIPPET:
        new_text = new_text.replace("\n", "\r\n")
    elif "\r" in text and "\r" not in SNIPPET and "\r\n" not in text:
        # Old-Mac line endings — unlikely, but be safe.
        new_text = new_text.replace("\n", "\r")

    path.write_text(new_text, encoding="utf-8")

    if strip_count:
        return "rewritten"
    return "inserted"


def main() -> int:
    html_files = sorted(ROOT.rglob("*.html"))
    targets = [p for p in html_files if not should_skip(p)]

    counts = {"inserted": 0, "rewritten": 0, "already-present": 0, "no-head": 0, "error": 0}
    skipped = [p for p in html_files if should_skip(p)]

    for path in targets:
        rel = path.relative_to(ROOT).as_posix()
        result = process(path)
        counts[result] += 1
        print(f"  [{result:>16}]  {rel}")

    print()
    print(f"Scanned: {len(html_files)} HTML files")
    print(f"Skipped: {len(skipped)}  ({', '.join(p.relative_to(ROOT).as_posix() for p in skipped)})")
    print(f"  inserted (new):   {counts['inserted']}")
    print(f"  rewritten (clean+insert): {counts['rewritten']}")
    print(f"  already-present:  {counts['already-present']}")
    print(f"  no </head>:       {counts['no-head']}")
    print(f"  errors:           {counts['error']}")
    return 0 if counts["error"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
