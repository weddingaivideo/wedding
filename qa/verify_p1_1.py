"""Verify P1-1 fix: pre-deploy-check.ps1 can read functions/docs/[id].js now."""
import os
import subprocess
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
# Run pre-deploy-check.ps1 and capture output
r = subprocess.run(
    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
     "-File", str(ROOT / "internal-tools" / "pre-deploy-check.ps1")],
    capture_output=True, text=True, timeout=300,
    cwd=str(ROOT),
)
out = r.stdout

# Look for any error markers
bad_markers = [
    (r"ObjectNotFound", "ObjectNotFound (PowerShell wildcard bug)"),
    (r"ItemNotFound", "ItemNotFound (PowerShell missing file)"),
    (r"Get-Content.*does not exist", "Get-Content not found"),
    (r"\[id\]", "explicit [id] reference in error"),
]

found_bad = False
for pattern, desc in bad_markers:
    if re.search(pattern, out):
        print(f"FAIL: found {desc}")
        found_bad = True

# Check that secret scanner PASSed (the bug would have caused failures)
if "No hardcoded API keys/tokens detected" in out:
    print("PASS: secret scanner ran cleanly (no ObjectNotFound for [id].js)")
elif "No hardcoded" not in out:
    print("FAIL: secret scanner didn't pass")
    found_bad = True

# Confirm the fixed line is in the script
script = (ROOT / "internal-tools" / "pre-deploy-check.ps1").read_text(encoding="utf-8")
if "[System.IO.File]::ReadAllText" in script:
    print("PASS: pre-deploy-check.ps1 uses [System.IO.File]::ReadAllText")
else:
    print("FAIL: pre-deploy-check.ps1 still uses Get-Content")
    found_bad = True

if found_bad:
    sys.exit(1)
print("\nAll P1-1 checks passed.")
