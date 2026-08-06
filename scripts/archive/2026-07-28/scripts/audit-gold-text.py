#!/usr/bin/env python3
"""找出所有 'color: var(--color-primary)' 用在浅色背景上的位置。
- 找到每个 color: var(--color-primary) 的位置
- 回溯最近的 <section ... style="background: ..."> 父级
- 计算对比度
"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

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
    def channel(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(c1, c2):
    l1 = rel_lum(hex_to_rgb(c1))
    l2 = rel_lum(hex_to_rgb(c2))
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def grade(ratio):
    if ratio >= 7: return 'AAA'
    if ratio >= 4.5: return 'AA'
    if ratio >= 3: return 'AA-Large'
    return 'FAIL'


def resolve(val):
    val = val.strip()
    if val.startswith('var('):
        return PALETTE.get(val[4:val.index(')')])
    if val.startswith('#'):
        return val
    if val.startswith('rgb'):
        nums = re.findall(r'\d+\.?\d*', val)
        if len(nums) >= 3:
            r, g, b = [int(float(x)) for x in nums[:3]]
            return f'#{r:02X}{g:02X}{b:02X}'
    return None


def find_enclosing_section_bg(content, pos):
    """Walk backwards from pos to find the nearest <section ... style="background: ...">"""
    # Find all section starts before pos
    section_re = re.compile(r'<section[^>]*style="([^"]+)"[^>]*>')
    last_bg = None
    for m in section_re.finditer(content, 0, pos):
        style = m.group(1)
        bg_match = re.search(r'background:\s*([^;"]+)', style)
        if bg_match:
            last_bg = resolve(bg_match.group(1))
    return last_bg


def check_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    rel = os.path.relpath(path, ROOT)
    issues = []
    for m in re.finditer(r'color:\s*(var\(--color-primary\))', content):
        pos = m.start()
        bg = find_enclosing_section_bg(content, pos)
        if not bg:
            continue
        primary = PALETTE['--color-primary']
        ratio = contrast(bg, primary)
        g = grade(ratio)
        # Find context (the line)
        line_start = content.rfind('\n', 0, pos) + 1
        line_end = content.find('\n', pos)
        if line_end == -1: line_end = len(content)
        line = content[line_start:line_end].strip()[:80]
        issues.append((pos, bg, primary, ratio, g, line))
    return rel, issues


def main():
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in {'.git', 'node_modules', '.wrangler'}]
        for f in filenames:
            if f.endswith('.html'):
                files.append(os.path.join(dirpath, f))
    files = sorted(files)

    print(f'{"RATIO":<7} {"BG":<10} {"GOLD":<10} {"GRADE":<10} FILE:LINE')
    print('=' * 100)

    total_fail = 0
    total_warn = 0
    for path in files:
        rel, issues = check_file(path)
        for pos, bg, gold, ratio, g, line in issues:
            mark = '!!' if g == 'FAIL' else '! ' if g == 'AA-Large' else ''
            if g in ('FAIL', 'AA-Large'):
                print(f'{ratio:5.2f}  {bg:<10} {gold:<10} {g:<10} {mark} {rel}')
                print(f'       LINE: {line}')
                if g == 'FAIL':
                    total_fail += 1
                else:
                    total_warn += 1
    print('=' * 100)
    print(f'HARD FAIL (invisible): {total_fail}, BORDERLINE (large only): {total_warn}')


if __name__ == '__main__':
    main()
