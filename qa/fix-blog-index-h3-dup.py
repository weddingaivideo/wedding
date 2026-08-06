"""
Fix double </h3> introduced by the first wrap script.

The first script wrapped `<a ...>...</a></h3>` in `<h3>...</h3>`, producing
`<h3><a ...>...</a></h3></h3>`. This script removes the duplicate closing.
"""
import re
import sys
from pathlib import Path

FILE = Path(r"C:/Users/qiaoshan/.openclaw/workspace/weddingai/blog/index.html")
content = FILE.read_text(encoding="utf-8")

# Find: </a></h3></h3>  →  </a></h3>
pattern = re.compile(r'</a></h3></h3>')
new_content, n = pattern.subn('</a></h3>', content)

if n == 0:
    print("No double </h3> found. Already clean or something else is off.")
    sys.exit(1)

FILE.write_text(new_content, encoding="utf-8")
print(f"OK: removed {n} duplicate </h3> tags")
