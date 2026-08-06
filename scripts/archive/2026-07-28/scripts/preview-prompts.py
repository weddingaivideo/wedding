import json
data = json.load(open("scripts/blog-image-prompts.json", encoding="utf-8"))
for slug in ["01-restore-old-wedding-videos", "08-pet-wedding-videos", "15-wedding-video-social-media", "40-cartoon-wedding-video", "47-wedding-video-cost-2026"]:
    e = data[slug]
    print(f"=== {slug} ===")
    print("  HERO: ", e["hero"]["prompt"])
    for i, ie in enumerate(e["inline"], 1):
        print(f"  IN{i}:  ", ie["prompt"])
    print()
