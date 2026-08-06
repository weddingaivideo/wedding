"""Print remaining hero batches for paste into image_synthesize."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "scripts" / "blog-image-prompts.json").read_text(encoding="utf-8"))

# Skip first 10 (already generated)
done = 10
for slug, entry in list(data.items())[done:]:
    p = entry["hero"]["prompt"]
    fn = f"images/blog/hero/{slug}.jpg"
    print(f"  - {fn}")
    print(f"    prompt: {p}")
    print()
