import os
ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# (rel, old, new)
replacements = [
    (
        "about.html",
        "Filmmakers, AI engineers, and wedding lovers building AI-powered wedding video services. Learn how we make every love story unforgettable through technology and craft.",
        "Filmmakers and AI engineers building AI-powered wedding video services. Learn how we make every love story unforgettable.",
    ),
    (
        "index.html",
        "AI-powered wedding videos: AI films, multilingual dubbing, restoration, and more. 10+ services for couples worldwide. Get a free quote — start your project today!",
        "AI-powered wedding videos: AI films, multilingual dubbing, restoration, and more. 10+ services. Get a free quote — start today!",
    ),
]

for rel, old, new in replacements:
    path = os.path.join(ROOT, rel)
    content = open(path, encoding="utf-8").read()
    new_content = content.replace(old, new)
    if new_content != content:
        open(path, "w", encoding="utf-8", newline="").write(new_content)
        print(f"  ✓ {rel}: {len(new)} chars (was {len(old)})")
    else:
        print(f"  ! {rel}: no match")
