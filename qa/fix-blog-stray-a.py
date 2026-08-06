"""
Clean up the stray </a> tags in blog/index.html footer.
After multiple edits, we have 4 orphan </a> + 5 whitespace-only lines.
Replace that block with a single clean block.
"""
import os
from pathlib import Path

FILE = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent) / "blog" / "index.html"
content = FILE.read_text(encoding="utf-8")

# Find: </picture></a>\n                 <whitespace+></a>+\n                 <p data-i18n="404.p_text.ai...
# Replace with: </picture></a>\n                <p data-i18n="404.p_text.ai...
import re

# Match the messy block: picture close, then any number of </a> on their own lines (with optional whitespace)
# and the <p> with the 404.p_text key
pattern = re.compile(
    r'(</picture></a>\n)'                        # opening: picture+anchor close
    r'([ \t]*\n[ \t]*)+'                          # whitespace lines
    r'(([ \t]*</a>\n)+)'                          # 1+ orphan </a> lines
    r'[ \t]*'                                      # trailing whitespace
    r'(<p\s+data-i18n="404\.p_text\.ai_powered_wedding_video_services_for_co\.90691298">)',
    re.MULTILINE
)

new_content, n = pattern.subn(r'\1\5', content)
print(f"matched: {n}")

if n != 1:
    print("ERROR: expected exactly 1 match, got", n)
    raise SystemExit(1)

FILE.write_text(new_content, encoding="utf-8")
print("OK: cleaned up orphan </a> tags")
