"""Normalize _redirects and _headers to UTF-8 LF (CF Pages edge parser requirement)."""
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")

for fname in ("_redirects", "_headers"):
    p = ROOT / fname
    b = p.read_bytes()
    # Count line endings
    crlf = b.count(b"\r\n")
    lone_cr = b.count(b"\r") - crlf
    lone_lf = b.count(b"\n") - crlf
    new = b.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if new != b:
        p.write_bytes(new)
        print(f"  {fname}: {crlf} CRLF, {lone_cr} lone CR, {lone_lf} lone LF -> all LF")
    else:
        print(f"  {fname}: no change (already LF)")
