import sys
sys.path.insert(0, "scripts")
import importlib
audit = importlib.import_module("audit-issues")
from pathlib import Path
# Run the exact main() function but print everything
audit.ISSUES.clear()
for f in sorted(audit.ROOT.rglob("*.html")):
    if "google-site-verification" in f.name:
        continue
    audit.audit_file(f)
# Print only heading-skip issues
for k, v in audit.ISSUES.items():
    if "heading" in k:
        print(f"  {v}  {k}")
print("---")
# What was reported for index.html?
for k in audit.ISSUES:
    if "h1->h3" in k:
        print(f"issue key: {k!r}, count: {audit.ISSUES[k]}")
