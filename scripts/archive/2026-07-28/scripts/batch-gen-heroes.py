"""Batch-generate hero images for all blog articles.

Reads scripts/blog-image-prompts.json, then issues image_synthesize
calls in chunks of up to 10 requests per call. This script is meant
to be copy-pasted into a single message — the assistant should adapt
the actual `image_synthesize(...)` invocations from the data structure
this script prints.

Output: scripts/blog-image-gen-batches.json — every batch in a format
ready to be plugged into image_synthesize.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "scripts" / "blog-image-prompts.json").read_text(encoding="utf-8"))

BATCH = 10
hero_batches = []  # list of lists of {prompt, output_file_path}
current = []
for slug, entry in DATA.items():
    current.append({
        "prompt": entry["hero"]["prompt"],
        "output_file_path": f"images/blog/hero/{slug}.jpg",
        "aspect_ratio": "16:9",
        "resolution": "1K",
    })
    if len(current) == BATCH:
        hero_batches.append(current)
        current = []
if current:
    hero_batches.append(current)

(ROOT / "scripts" / "blog-image-gen-batches.json").write_text(
    json.dumps({
        "heroes": hero_batches,
        "inline_batches_count": 0,  # populated below
    }, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

# Also dump inline batches
inline_batches = []
current = []
for slug, entry in DATA.items():
    for i, inline in enumerate(entry["inline"], start=1):
        current.append({
            "prompt": inline["prompt"],
            "output_file_path": inline["filename"],
            "aspect_ratio": "16:9",
            "resolution": "1K",
        })
        if len(current) == BATCH:
            inline_batches.append(current)
            current = []
if current:
    inline_batches.append(current)

(ROOT / "scripts" / "blog-image-gen-batches.json").write_text(
    json.dumps({"heroes": hero_batches, "inline": inline_batches}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(f"Hero batches:   {len(hero_batches)} (each <= {BATCH} images, total {sum(len(b) for b in hero_batches)})")
print(f"Inline batches: {len(inline_batches)} (each <= {BATCH} images, total {sum(len(b) for b in inline_batches)})")
print(f"Wrote: scripts/blog-image-gen-batches.json")
