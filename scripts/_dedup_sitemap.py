#!/usr/bin/env python3
"""
Dedupe sitemap-en.xml using XML parser (not regex).
- 7 tool paths each appear 11 times; keep 1, remove 10 duplicates.
- /private/architecture/ entry: remove entirely.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai")
SM = REPO / "sitemap-en.xml"

TOOL_PATHS = {
    "/tools/",
    "/tools/add-text-to-wedding-photo/",
    "/tools/compress-wedding-photos/",
    "/tools/crop-wedding-photo-for-reels/",
    "/tools/heic-to-jpg-wedding-photos/",
    "/tools/remove-background-wedding-portrait/",
    "/tools/wedding-photo-collage/",
}
PRIVATE_PATH = "/private/architecture/"

NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "xhtml": "http://www.w3.org/1999/xhtml",
    "image": "http://www.google.com/schemas/sitemap-image/1.1",
}
for prefix, uri in NS.items():
    ET.register_namespace("" if prefix == "sm" else prefix, uri)

def path_from_loc(loc: str) -> str:
    return loc.replace("https://weddingai.video", "")

def main():
    raw = SM.read_text(encoding="utf-8")
    print(f"Initial file size: {len(raw):,} bytes")
    initial_count = raw.count("<url>")
    print(f"Initial <url> blocks: {initial_count}")

    root = ET.fromstring(raw)
    children = list(root)
    print(f"Parsed root children: {len(children)}")

    seen_tool = set()
    kept_children = []
    removed = []
    for c in children:
        # Find <loc>
        loc_el = c.find("sm:loc", NS)
        if loc_el is None or not loc_el.text:
            kept_children.append(c)
            continue
        loc = loc_el.text
        path = path_from_loc(loc)
        if path == PRIVATE_PATH:
            removed.append((path, "private"))
            continue
        if path in TOOL_PATHS:
            if path in seen_tool:
                removed.append((path, "tool-dup"))
                continue
            seen_tool.add(path)
        kept_children.append(c)

    # Rebuild root
    new_root = ET.Element(root.tag, root.attrib)
    for c in kept_children:
        new_root.append(c)

    # Serialize
    out = ET.tostring(new_root, encoding="unicode")
    out = '<?xml version="1.0" encoding="UTF-8"?>\n' + out + "\n"

    # Verify XML
    try:
        ET.fromstring(out)
    except ET.ParseError as e:
        print(f"[ERROR] output XML parse failed: {e}")
        sys.exit(1)

    # Verify expected per-path counts
    print(f"\nFinal per-tool-path <loc> count:")
    for p in sorted(TOOL_PATHS, key=len):
        cnt = out.count(f"<loc>https://weddingai.video{p}</loc>")
        marker = "OK" if cnt == 1 else "WRONG"
        print(f"  [{marker}] {p} : {cnt}")
    pcnt = out.count(f"<loc>https://weddingai.video{PRIVATE_PATH}</loc>")
    print(f"  [{'OK' if pcnt == 0 else 'WRONG'}] {PRIVATE_PATH} : {pcnt}")

    final_count = out.count("<url>")
    expected = initial_count - len(removed)
    print(f"\nFinal <url> count: {final_count} (expected {expected}, removed {len(removed)})")
    for r in removed[:80]:
        print(f"  - {r[0]} ({r[1]})")
    if len(removed) > 80:
        print(f"  ... and {len(removed) - 80} more")

    if final_count != expected:
        print("[ABORT] final count mismatch")
        sys.exit(1)

    # Atomic write
    tmp = SM.with_suffix(".xml.tmp")
    tmp.write_text(out, encoding="utf-8", newline="")
    if tmp.stat().st_size < 100_000:
        tmp.unlink()
        print(f"[ABORT] tmp too small: {tmp.stat().st_size} bytes")
        sys.exit(1)
    import shutil
    shutil.move(str(tmp), str(SM))
    print(f"\n[OK] Wrote {SM} ({SM.stat().st_size:,} bytes)")

if __name__ == "__main__":
    main()
