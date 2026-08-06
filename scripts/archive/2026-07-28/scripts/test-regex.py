import re
# Test what "AI wedding video generator" matches first
kw = "AI wedding video generator"
patterns = [
    (r"\brestor|repair|recover|damag|legacy\b", "restor"),
    (r"\b(ai video generator|ai film|ai[- ]generated|generative)\b", "ai generator"),
    (r"\b(wedding video|video vs|video versus|video or)\b", "wedding video"),
]
for pat, name in patterns:
    m = re.search(pat, kw.lower())
    print(f"  {name}: {bool(m)}")
