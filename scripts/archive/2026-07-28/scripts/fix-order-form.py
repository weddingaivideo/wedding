#!/usr/bin/env python3
"""Replace the order form in order.html and order/index.html with the new 5-field version."""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
NEW_FORM_PATH = ROOT / "order_new_form.html"

TARGETS = [
    ROOT / "order.html",
    ROOT / "order" / "index.html",
]

# Match the form block non-greedy.
RX_FORM = re.compile(
    r'<form class="order-form"[^>]*>.*?</form>',
    re.DOTALL,
)


def main():
    new_form = NEW_FORM_PATH.read_text(encoding="utf-8").strip()

    for target in TARGETS:
        if not target.exists():
            print(f"  SKIP missing: {target}")
            continue
        raw = target.read_text(encoding="utf-8")
        new, n = RX_FORM.subn(new_form, raw, count=1)
        if n == 0:
            print(f"  NO MATCH: {target}")
            continue
        target.write_text(new, encoding="utf-8", newline="")
        print(f"  OK: {target.relative_to(ROOT)}  (1 form replaced, {len(new)} bytes)")


if __name__ == "__main__":
    main()
