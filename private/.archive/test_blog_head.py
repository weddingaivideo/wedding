"""Sanity-check the new breadcrumb_block + head_block changes in generate-blog.py."""
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("genblog", Path("scripts/generate-blog.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

bc = mod.breadcrumb_block("WeddingAI Video Complete Guide", "https://weddingai.video/blog/weddingai-video-guide/")
print("breadcrumb_block output:")
print(repr(bc))
print()

head = mod.head_block(
    "WeddingAI Video Complete Guide | WeddingAI.video Blog",
    "desc",
    "https://weddingai.video/blog/weddingai-video-guide/",
    extra_head=bc,
)
print("head_block contains BreadcrumbList JSON-LD:", '"BreadcrumbList"' in head)
print("head_block still closes </head>:</body>:", "</head>\n<body>" in head)
print("head_block end (last 300 chars):")
print(head[-300:])
