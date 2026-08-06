#!/usr/bin/env python3
"""Validate sitemap image:image coverage and report which URLs lack it."""
import glob
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "image": "http://www.google.com/schemas/sitemap-image/1.1",
}


def main() -> int:
    files = sorted(glob.glob("sitemap-*.xml"))
    if not files:
        print("FAIL: no sitemap-*.xml found")
        return 1
    total_urls = 0
    total_with_image = 0
    for f in files:
        tree = ET.parse(f)
        urls = tree.getroot().findall("sm:url", NS)
        imgs = tree.getroot().findall(".//image:image", NS)
        n_urls = len(urls)
        n_with = sum(1 for u in urls if u.find("image:image", NS) is not None)
        total_urls += n_urls
        total_with_image += n_with
        # Find URLs without image
        no_img = []
        for u in urls:
            if u.find("image:image", NS) is None:
                loc = u.find("sm:loc", NS).text
                # Get path part only
                path = loc.replace("https://weddingai.video", "")
                no_img.append(path)
        status = "OK" if not no_img else f"MISSING {len(no_img)}"
        print(f"  {f}: {n_urls} urls, {n_with} with image ({status})")
        if no_img and len(no_img) <= 10:
            for p in no_img:
                print(f"    - {p}")
        elif no_img:
            print(f"    - {len(no_img)} urls without image (first 5):")
            for p in no_img[:5]:
                print(f"      {p}")
    print()
    print(f"Total: {total_urls} urls, {total_with_image} with image ({total_with_image*100//total_urls}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
