"""
Add ?v=3.11.0 cache buster to all styles.min.css references in HTML files.
This forces browsers to bypass disk cache and re-download the CSS,
ensuring they get the latest .process-step:has(> picture) layout fix.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "3.11.0"
# Match both /styles.min.css (absolute, used in /index.html files) and
# styles.min.css (relative, used in legacy root .html back-compat files).
# Always rewrite to absolute /styles.min.css?v=VERSION.
PATTERN = re.compile(r'href="((?:/)?styles\.min\.css)(\?v=[^"]*)?"')

updated = 0
skipped = 0
for html in ROOT.rglob("*.html"):
    # skip tmp / diag / functions / node_modules
    parts = html.relative_to(ROOT).parts
    if any(p in {"tmp", "node_modules", "functions", ".git"} for p in parts):
        continue
    text = html.read_text(encoding="utf-8")
    new_text, n = PATTERN.subn(f'href="/styles.min.css?v={VERSION}"', text)
    if n > 0 and new_text != text:
        html.write_text(new_text, encoding="utf-8")
        # verify
        v_count = new_text.count(f"?v={VERSION}")
        print(f"  {html.relative_to(ROOT)}: {n} refs -> ?v={VERSION} ({v_count} now have buster)")
        updated += 1
    elif "?v=" in text:
        skipped += 1

print(f"\nUpdated {updated} files, skipped {skipped} (already had buster)")
