import sys
sys.path.insert(0, "scripts")
import importlib
audit = importlib.import_module("audit-issues")
from pathlib import Path
audit.audit_file(Path("index.html"))
print("---")
print("Done")
