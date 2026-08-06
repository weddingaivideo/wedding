#!/usr/bin/env python3
"""Add ?service= URL prefill script to the order forms so /order/?service=family-tribute etc. auto-selects."""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")

PREFILL_SCRIPT = """
                <script>
                (function() {
                    // Pre-select service if /order/?service=X
                    var params = new URLSearchParams(window.location.search);
                    var svc = params.get('service');
                    if (svc) {
                        var sel = document.getElementById('service');
                        if (sel) {
                            for (var i = 0; i < sel.options.length; i++) {
                                if (sel.options[i].value === svc) {
                                    sel.value = svc;
                                    sel.dispatchEvent(new Event('change'));
                                    break;
                                }
                            }
                        }
                    }
                })();
                </script>"""

# Insert before </body> on order.html and order/index.html
TARGETS = [ROOT / "order.html", ROOT / "order" / "index.html"]

for target in TARGETS:
    raw = target.read_text(encoding="utf-8")
    if "Pre-select service if /order/" in raw:
        print(f"  already has prefill: {target.name}")
        continue
    new = raw.replace("</body>", PREFILL_SCRIPT + "\n</body>", 1)
    if new == raw:
        print(f"  NO </body> found: {target.name}")
        continue
    target.write_text(new, encoding="utf-8", newline="")
    print(f"  added prefill: {target.name}")
