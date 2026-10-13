"""
Insert Microsoft Clarity (clarity.ms) tracking snippet into all production HTML
files of weddingai.video, right before </head>.

Clarity is a heatmap + session-recording analytics tool. The official install
instructions just say "paste this script into <head>". Like the Baidu Tongji
script, this project installs it on EVERY page via static injection (not via
middleware) so the tool is a flat-file editor that mutates HTML.

The snippet is the official async loader; it dynamically appends a
<script src="https://www.clarity.ms/tag/<id>">. Under the project's CSP
(strict-dynamic + per-request nonce on inline scripts), the dynamically-injected
external script is allowed without listing the host in script-src — but we list
it anyway for documentation and to satisfy the static _headers fallback.

Mirrors tools/add_baidu_tongji.py structure for consistency:
  - skips google-site-verification.html (must stay raw)
  - skips any path under tmp/ (scratch)
  - idempotent: re-running is safe
  - cleans up a broken v1 insertion on next run if you ever pasted the snippet
    with </script> glued to a previous tag (the v1 broken pattern).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
CLARITY_ID = "ywxiu97hg8"
SKIP_NAMES = {"google-site-verification.html"}
SKIP_DIR_PARTS = {"tmp"}

# Match Clarity's official snippet (any leading whitespace on each line).
# The IIFE signature (function(c,l,a,r,i,t,y)) is unique enough to identify
# the script unambiguously across minor whitespace variations.
CLARITY_PRESENT = re.compile(
    r"window,\s*document,\s*\"clarity\",\s*\"script\",\s*\"" + re.escape(CLARITY_ID) + r"\"\s*\);",
    re.DOTALL,
)

# Match a previously-broken insertion OR a prior clean run, so we can replace
# it idempotently. Same shape as the Baidu tool's BAIDU_BLOCK_TO_STRIP.
CLARITY_BLOCK_TO_STRIP = re.compile(
    r"[ \t]*<!-- Clarity \(clarity\.ms\) — heatmaps & session replay -->\s*"
    r"<script type=\"text/javascript\">\s*"
    r"\(function\(c,l,a,r,i,t,y\)\{[\s\S]*?\}\)\(window,\s*document,\s*\"clarity\",\s*\"script\",\s*\"" + re.escape(CLARITY_ID) + r"\"\s*\);\s*"
    r"</script>\s*",
)

# The official Clarity snippet, with a leading newline for separation and a
# 4-space indent to match project convention.
SNIPPET = (
    "\n    <!-- Clarity (clarity.ms) — heatmaps & session replay -->\n"
    "    <script type=\"text/javascript\">\n"
    "    (function(c,l,a,r,i,t,y){\n"
    "        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};\n"
    "        t=l.createElement(r);t.async=1;t.src=\"https://www.clarity.ms/tag/\"+i;\n"
    "        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);\n"
    "    })(window, document, \"clarity\", \"script\", \"" + CLARITY_ID + "\");\n"
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

    # 0. If the file already has the standard Clarity block, leave it alone.
    if CLARITY_PRESENT.search(text):
        # Sanity check: make sure the block is on its own lines, not glued
        # to a previous </script> (the v1 broken pattern).
        if not re.search(r"</script>[ \t]+<!-- Clarity", text):
            return "already-present"
        # else: fall through to strip + re-insert

    # 1. Strip any previous Clarity block (clean up v1 broken insertion OR a
    #    previous clean run, idempotently).
    new_text, strip_count = CLARITY_BLOCK_TO_STRIP.subn("", text)

    # 2. Insert the snippet immediately before </head>.
    new_text, count = re.subn(
        r"</head>",
        lambda m: SNIPPET + "</head>",
        new_text,
        count=1,
        flags=re.IGNORECASE,
    )
    if count == 0:
        return "no-head"

    # 3. Preserve original line endings. Python's default text-mode IO
    #    translates CRLF↔LF on Windows, so a CRLF file round-trips correctly
    #    even though this branch only runs when text has LF-only endings.
    if "\r\n" in text and "\r\n" not in SNIPPET:
        new_text = new_text.replace("\n", "\r\n")
    elif "\r" in text and "\r" not in SNIPPET and "\r\n" not in text:
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
