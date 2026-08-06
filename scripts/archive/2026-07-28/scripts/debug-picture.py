text = open("index.html", encoding="utf-8").read()
import re
PIC_OPEN = re.compile(r"<picture[\s>]")
PIC_CLOSE = re.compile(r"</picture\s*>")
opens = [m.start() for m in PIC_OPEN.finditer(text)]
closes = [m.start() for m in PIC_CLOSE.finditer(text)]
print(f"total pictures: {len(opens)}")
print(f"opens[:5]: {opens[:5]}")
print(f"closes[:5]: {closes[:5]}")
# Check 11415 — what is it?
print(f"text[11400:11450]: {text[11400:11450]!r}")
# 11415 specifically
print(f"text[11415]: {text[11415]!r}")
# Is 11415 between open/close pair?
for i in range(len(opens)):
    o = opens[i]
    c = closes[i] if i < len(closes) else -1
    if o <= 11415 <= c + 11:
        print(f"11415 is inside picture #{i}: open={o}, close={c}")
        break
else:
    print("11415 is NOT inside any picture per simple ranges")
    # Maybe the 4th bad position (11415) corresponds to the 4th picture if zero-indexed
    # The bad message said "index.html @ 11415" - it's reporting the OPEN position
    # Let me just look at what's at 11415 in the OPEN list
    print(f"opens[3] = {opens[3] if len(opens) > 3 else 'N/A'}")
