import json
d = json.load(open("scripts/blog-image-prompts.json", encoding="utf-8"))
e = d["04-wedding-video-from-photos"]
print(f"primary: {e['primary_keyword']}")
print(f"hero prompt: {e['hero']['prompt'][:250]}")
