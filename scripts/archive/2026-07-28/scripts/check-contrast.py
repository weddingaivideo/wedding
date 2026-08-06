#!/usr/bin/env python3
"""检查每个页面的背景色和文字色对比度。
- 解析 HTML 里所有 section 的 inline style="background: ..."
- 解析每个 section 内文字元素的 color
- 计算 WCAG 对比度
- 标记对比度 < 4.5 的组合（AA body text 标准）
"""
import os
import re
import math

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# Full design system
PALETTE = {
    '--color-primary':      '#D4AF37',
    '--color-primary-dark': '#B8962E',
    '--color-secondary':    '#2C2C2C',
    '--color-bg':           '#FDFBF8',
    '--color-bg-alt':       '#F5F0EA',
    '--color-text':         '#2C2C2C',
    '--color-text-light':   '#6B6B6B',
    '--color-white':        '#FFFFFF',
    '--color-border':       '#E5E0D8',
}


def hex_to_rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c*2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def rel_lum(rgb):
    """WCAG relative luminance."""
    def channel(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(c1, c2):
    l1 = rel_lum(hex_to_rgb(c1))
    l2 = rel_lum(hex_to_rgb(c2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def resolve_color(val):
    """Resolve 'var(--xxx)' or '#xxx' or 'rgba(...)' to a hex approximation."""
    val = val.strip()
    if val.startswith('var('):
        name = val[4:val.index(')')]
        return PALETTE.get(name)
    if val.startswith('#'):
        return val
    if val.startswith('rgb'):
        nums = re.findall(r'\d+\.?\d*', val)
        if len(nums) >= 3:
            r, g, b = [int(float(x)) for x in nums[:3]]
            return f'#{r:02X}{g:02X}{b:02X}'
    return None


def grade(ratio):
    """WCAG 2.1 grading."""
    if ratio >= 7:
        return 'AAA'
    if ratio >= 4.5:
        return 'AA'
    if ratio >= 3:
        return 'AA-Large'
    return 'FAIL'


def find_html_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in {'.git', 'node_modules', '.wrangler'}]
        for f in filenames:
            if f.endswith('.html'):
                out.append(os.path.join(dirpath, f))
    return sorted(out)


def check_page(path):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    rel = os.path.relpath(path, ROOT)

    # Find sections with background color
    issues = []

    # 1. section-level background colors
    for m in re.finditer(r'<section[^>]*style="([^"]+)"[^>]*>(.*?)</section>', html, re.DOTALL):
        style = m.group(1)
        body = m.group(2)
        bg_match = re.search(r'background:\s*([^;"]+)', style)
        if not bg_match:
            continue
        bg = resolve_color(bg_match.group(1))
        if not bg:
            continue

        # Look for text colors inside this section
        # Find color: var(--color-xxx) in inline styles within this section
        text_colors_used = set()
        for tm in re.finditer(r'color:\s*(var\(--[a-z-]+\)|#[0-9A-Fa-f]+|rgba?\([^)]+\))', body):
            tc = resolve_color(tm.group(1))
            if tc:
                text_colors_used.add(tc)

        if not text_colors_used:
            continue

        # Compute contrast for each text color
        for tc in text_colors_used:
            ratio = contrast(bg, tc)
            g = grade(ratio)
            if ratio < 4.5:
                issues.append((bg, tc, ratio, g, m.start()))

    # 2. check divs that are footer / nav (large blocks with background)
    for m in re.finditer(r'<(?:footer|nav|header)[^>]*style="([^"]+)"[^>]*>(.*?)</(?:footer|nav|header)>', html, re.DOTALL):
        style = m.group(1)
        body = m.group(2)
        bg_match = re.search(r'background:\s*([^;"]+)', style)
        if not bg_match:
            continue
        bg = resolve_color(bg_match.group(1))
        if not bg:
            continue
        for tm in re.finditer(r'color:\s*(var\(--[a-z-]+\)|#[0-9A-Fa-f]+|rgba?\([^)]+\))', body):
            tc = resolve_color(tm.group(1))
            if tc:
                ratio = contrast(bg, tc)
                g = grade(ratio)
                if ratio < 4.5:
                    issues.append((bg, tc, ratio, g, m.start()))

    return rel, issues


def main():
    print(f'{"RATIO":<7} {"BG":<10} {"TEXT":<10} {"GRADE":<10} WHERE')
    print('=' * 90)

    total_issues = 0
    pages_with_issues = 0
    for path in find_html_files():
        rel, issues = check_page(path)
        for bg, tc, ratio, g, _pos in issues:
            print(f'{ratio:5.2f}  {bg:<10} {tc:<10} {g:<10} {rel}')
            total_issues += 1
        if issues:
            pages_with_issues += 1

    print('=' * 90)
    print(f'Total: {total_issues} low-contrast combos across {pages_with_issues} pages')

    # Also: print the baseline contrasts of the palette vs itself for reference
    print()
    print('=== Reference: Palette contrast matrix ===')
    header_label = 'BG \\ TEXT'
    print(f'{header_label:<20}', end='')
    for k in PALETTE:
        print(f'{k:<20}', end='')
    print()
    for bg_k, bg_v in PALETTE.items():
        print(f'{bg_k:<20}', end='')
        for txt_k, txt_v in PALETTE.items():
            r = contrast(bg_v, txt_v)
            g = grade(r)
            mark = '!' if r < 4.5 else 'OK'
            cell = f'{r:.2f} {g} {mark}'
            print(f'{cell:<20}', end='')
        print()


if __name__ == '__main__':
    main()
