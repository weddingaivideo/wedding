import re
kw = "restore old wedding photos"
patterns = [
    r"\b(restor|repair|recover|damag|fix (old|broken|legacy))\b",
    r"\b(vhs|tape|cassette|hi8|mini-dv|mini dv|8mm|film reel)\b",
    r"\b(wedding video|video vs|video versus|video or)\b",
]
for p in patterns:
    m = re.search(p, kw.lower())
    print(f"  {p!r}: {bool(m)}")
