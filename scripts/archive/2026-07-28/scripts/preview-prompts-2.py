import json
d = json.load(open("scripts/blog-image-prompts.json", encoding="utf-8"))
for slug in ["01-restore-old-wedding-videos", "02-vhs-to-digital-wedding-cost", "03-ai-wedding-video-generator", "04-wedding-video-from-photos", "21-restore-old-wedding-photos"]:
    e = d[slug]
    kw = e["primary_keyword"]
    hero = e["hero"]["prompt"]
    print(f"{slug}  (kw={kw})")
    print(f"  HERO: {hero[:200]}")
    print()
