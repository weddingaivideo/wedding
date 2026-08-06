import re
kw = "wedding video from photos"
patterns = [
    r"\b(from photos|photo[- ]?to[- ]?video|photo slideshow|stills|still photos)\b",
    r"\bwedding video\b",
]
for p in patterns:
    m = re.search(p, kw.lower())
    print(f"  {p!r}: {bool(m)}")
