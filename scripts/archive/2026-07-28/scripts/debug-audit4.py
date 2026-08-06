"""Test: run audit_file on JUST index.html but via the same code path as main()."""
import sys
sys.path.insert(0, "scripts")
import importlib
audit = importlib.import_module("audit-issues")
from pathlib import Path
# Clear counter
audit.ISSUES.clear()
# Run ONLY the files that audit-issues.py reports problems for
for f in sorted(audit.ROOT.rglob("*.html")):
    if "google-site-verification" in f.name:
        continue
    name = f.name
    if name not in ("index.html", "order.html", "family-tribute.html"):
        continue
    audit.audit_file(f)
# Show issues
for k, v in audit.ISSUES.items():
    if "heading" in k:
        print(f"  {v}  {k}")
print("ISSUES:", dict(audit.ISSUES))
