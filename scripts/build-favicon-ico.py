#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build a multi-size favicon.ico (16, 32, 48) from the existing icon-512.png
Pillow saves all 3 sizes in a single .ico container (Vista+ ICO format).
Result: /favicon.ico at the project root.
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "icon-512.png")
DST = os.path.join(ROOT, "favicon.ico")

if not os.path.exists(SRC):
    raise SystemExit(f"missing source: {SRC}")

base = Image.open(SRC).convert("RGBA")
sizes = [(16, 16), (32, 32), (48, 48)]
base.save(DST, format="ICO", sizes=sizes)
print(f"OK {DST} {os.path.getsize(DST)} bytes (sizes: {[s[0] for s in sizes]})")
