from pathlib import Path
import sys
p = Path("blog/weddingai-video-guide/index.html")
b = p.read_bytes()
crlf = b.count(b"\r\n")
lf = b.count(b"\n")
cr_only = b.count(b"\r") - crlf
print(f"Size: {len(b)}")
print(f"CRLF: {crlf}")
print(f"LF (total): {lf}")
print(f"CR-only: {cr_only}")
print(f"Last 100 bytes: {b[-100:]!r}")
