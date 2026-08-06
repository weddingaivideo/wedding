#!/usr/bin/env python3
"""应用定价优化：
1. Slow Motion: 1min $79→$49, 3min $149→$99
2. Family Tribute: 全套包 $599→$499
3. Family Message: 2-3 条 $349→$299
4. Meme Generator: 5 GIFs $49→$79, 15+5 $99→$129
5. services/index.html: Meme Generator 价格提示和预算指南同步
"""
import os

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"


def patch(rel, old, new, expected=1):
    path = os.path.join(ROOT, rel)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    count = content.count(old)
    if count != expected:
        print(f"  ✗ {rel}: expected {expected} matches, found {count} for: {old[:60]}")
        return False
    new_content = content.replace(old, new, expected)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(new_content)
    return True


def main():
    print("Applying pricing changes...\n")
    changes = []

    # 1. Slow Motion
    rel = "services/video-enhancement/slow-motion.html"
    if patch(rel,
             '<span class="label">Slow Motion Enhancement (up to 1 min)</span>\n                        <span class="value price">$79</span>',
             '<span class="label">Slow Motion Enhancement (up to 1 min)</span>\n                        <span class="value price">$49</span>'):
        changes.append(f"{rel}: 1min $79 → $49")
    if patch(rel,
             '<span class="label">Slow Motion Enhancement (1–3 min)</span>\n                        <span class="value price">$149</span>',
             '<span class="label">Slow Motion Enhancement (1–3 min)</span>\n                        <span class="value price">$99</span>'):
        changes.append(f"{rel}: 3min $149 → $99")

    # 2. Family Tribute — full package $599 → $499
    rel = "services/absence-compensation/family-tribute.html"
    # Find the line by its label
    if patch(rel,
             '<span class="label">Full Tribute Package (all three)</span>\n                        <span class="value price">$599</span>',
             '<span class="label">Full Tribute Package (all three)</span>\n                        <span class="value price">$499</span>'):
        changes.append(f"{rel}: Full Tribute Package $599 → $499")

    # 3. Family Message — 2-3 messages $349 → $299
    rel = "services/absence-compensation/family-message.html"
    if patch(rel,
             '<div class="pricing-row"><span class="label">2–3 Family Messages Integration</span><span class="value price">$349</span></div>',
             '<div class="pricing-row"><span class="label">2–3 Family Messages Integration</span><span class="value price">$299</span></div>'):
        changes.append(f"{rel}: 2-3 Family Messages $349 → $299")

    # 4. Meme Generator
    rel = "services/personalization/meme-generator.html"
    if patch(rel,
             '<span class="label">5 GIFs (3–5 sec each)</span>\n                        <span class="value price">$49</span>',
             '<span class="label">5 GIFs (3–5 sec each)</span>\n                        <span class="value price">$79</span>'):
        changes.append(f"{rel}: 5 GIFs $49 → $79")
    if patch(rel,
             '<span class="label">15 GIFs + 5 short clips</span>\n                        <span class="value price">$99</span>',
             '<span class="label">15 GIFs + 5 short clips</span>\n                        <span class="value price">$129</span>'):
        changes.append(f"{rel}: 15 GIFs + 5 clips $99 → $129")

    # 5. services/index.html — price hint + budget guide
    rel = "services/index.html"
    # price-hint for Meme Generator
    if patch(rel,
             '<h3><a href="personalization/meme-generator.html" title="Wedding GIFs &amp; Memes">Wedding GIFs &amp; Memes</a></h3>\n                        <p>Shareable clips for social media and group chats.</p>\n                        <span class="price-hint">From $49</span>',
             '<h3><a href="personalization/meme-generator.html" title="Wedding GIFs &amp; Memes">Wedding GIFs &amp; Memes</a></h3>\n                        <p>Shareable clips for social media and group chats.</p>\n                        <span class="price-hint">From $79</span>'):
        changes.append(f"{rel}: Meme Generator price-hint $49 → $79")
    # budget guide
    if patch(rel,
             'Under $100: Meme Generator ($49) or AI Video Generator from photos ($199 — but commonly $99 with first-customer discount).',
             'Under $100: Meme Generator ($79) or AI Video Generator from photos ($199 — but commonly $99 with first-customer discount).'):
        changes.append(f"{rel}: budget guide Meme Generator $49 → $79")

    print(f"\n=== Applied {len(changes)} changes ===")
    for c in changes:
        print(f"  ✓ {c}")


if __name__ == "__main__":
    main()
