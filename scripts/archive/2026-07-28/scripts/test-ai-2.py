import re
kw = "AI wedding video generator"
patterns = [
    r"\bai[- ]?generat\w*|ai[- ]?film|ai[- ]?video|generative",
    r"\b(wedding video|video vs|video versus|video or)\b",
]
for p in patterns:
    m = re.search(p, kw.lower())
    print(f"  {p!r}: {bool(m)}")
