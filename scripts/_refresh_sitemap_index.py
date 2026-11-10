"""Refresh sitemap.xml (index) lastmod.

Kept for backwards compatibility — the index is now refreshed by
scripts/_refresh_sitemap_lastmod.py, which handles the 11 per-language
sitemaps AND the index in one atomic pass (same UTC date everywhere).

This wrapper used to hardcode 2026-10-17 and the owner's absolute path,
which meant running it could silently roll the index date backwards.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
subprocess.run(
    [sys.executable, str(REPO / "scripts" / "_refresh_sitemap_lastmod.py")],
    cwd=str(REPO),
    check=True,
)
