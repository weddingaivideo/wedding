"""
Fix blog/index.html: wrap each title anchor in <h3>...</h3>.

The original code has:
  <a href="/blog/SLUG/" ... data-i18n="...">Title</a></h3>
Missing the opening <h3>. Restore the heading semantic for SEO + a11y.

Idempotent: re-running on already-fixed file is a no-op (anchors already inside <h3>).
"""
import re
import sys
from pathlib import Path

FILE = Path(r"C:/Users/qiaoshan/.openclaw/workspace/weddingai/blog/index.html")

content = FILE.read_text(encoding="utf-8")

# Pattern: any line that contains a title anchor ending in </a></h3> with no
# surrounding <h3>. We match the leading whitespace + the opening <a>, and
# inject <h3> right before it.
# The title anchor starts with optional leading whitespace then `<a href="/blog/`
# and ends with `</a></h3>`.
pattern = re.compile(
    r'(?P<indent>^[ \t]*)'
    r'(?P<anchor><a\s+href="/blog/[^"]+"[^>]*data-i18n="[^"]+"[^>]*>[^<]+</a></h3>)',
    re.MULTILINE,
)

def repl(m):
    indent = m.group("indent")
    anchor = m.group("anchor")
    # If already wrapped in <h3>, skip
    return indent + "<h3>" + anchor + "</h3>"

new_content, n = pattern.subn(repl, content)
if n == 0:
    print("No matches — already fixed? Or pattern mismatch.")
    sys.exit(1)

# Safety: also handle the case where <h3> is already wrapping some (idempotent)
# Re-run to confirm idempotency
new_content2, n2 = pattern.subn(repl, new_content)
if n2 != 0:
    print(f"WARN: not idempotent — {n2} extra matches on second pass. Aborting write.")
    sys.exit(2)

FILE.write_text(new_content, encoding="utf-8")
print(f"OK: wrapped {n} title anchors in <h3>...</h3>")
