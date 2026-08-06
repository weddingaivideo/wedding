"""Print remaining hero entries as JSON for image_synthesize batching."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "scripts" / "blog-image-prompts.json").read_text(encoding="utf-8"))
hero_dir = ROOT / "images" / "blog" / "hero"
done = {f.stem for f in hero_dir.glob("*.jpg")}

remaining = []
for slug, entry in data.items():
    if slug in done:
        continue
    remaining.append({
        "slug": slug,
        "prompt": entry["hero"]["prompt"],
        "filename": f"images/blog/hero/{slug}.jpg",
    })
print(f"Remaining: {len(remaining)}")
for r in remaining:
    print(f"\n--- {r['slug']} ---")
    print(f"  file: {r['filename']}")
    print(f"  prompt: {r['prompt'][:300]}{'...' if len(r['prompt']) > 300 else ''}")
