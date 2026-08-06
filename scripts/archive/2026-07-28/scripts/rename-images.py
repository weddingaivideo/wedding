#!/usr/bin/env python3
"""重命名图片文件并更新所有引用"""
import os
import re
import shutil

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# 图片重命名映射
RENAMES = {
    "wedding-restoration-before-after.png": "wedding-restoration-before-after.png",
    "wedding-restoration-vhs-tv.png": "wedding-restoration-vhs-tv.png",
}


def rename_files():
    images_dir = os.path.join(ROOT, "images")
    for old_name, new_name in RENAMES.items():
        old_path = os.path.join(images_dir, old_name)
        new_path = os.path.join(images_dir, new_name)
        if os.path.exists(old_path):
            if os.path.exists(new_path):
                print(f"  SKIP: {new_name} already exists")
                continue
            shutil.move(old_path, new_path)
            print(f"  Renamed: {old_name} -> {new_name}")
        else:
            print(f"  Not found: {old_name}")


def update_references():
    """更新所有文件中的引用"""
    for root, dirs, names in os.walk(ROOT):
        if "scripts\\archive" in root or "scripts/archive" in root:
            continue
        for name in names:
            if not (name.endswith(".html") or name.endswith(".md") or name.endswith(".ps1") or name.endswith(".py")):
                continue
            path = os.path.join(root, name)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            original = content
            for old, new in RENAMES.items():
                content = content.replace(old, new)
            if content != original:
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(content)
                rel = os.path.relpath(path, ROOT).replace("\\", "/")
                print(f"  Updated: {rel}")


def main():
    print("=== Step 1: Rename files ===")
    rename_files()
    print()
    print("=== Step 2: Update references ===")
    update_references()
    print()
    print("Done.")


if __name__ == "__main__":
    main()
