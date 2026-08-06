#!/usr/bin/env python3
"""全站可视问题审计：
1. .btn-link (gold text) on section backgrounds
2. .btn-primary (gold bg + white text) — known issue
3. Hard-to-read text on light backgrounds
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


# Read styles.css to get class definitions
with open(os.path.join(ROOT, 'styles.css'), 'r', encoding='utf-8') as f:
    css = f.read()

# Build a class -> (bg, color) map for classes that set background or color
class_bg = {}
class_color = {}
for m in re.finditer(r'\.([\w-]+)\s*\{([^}]+)\}', css):
    cls = m.group(1)
    body = m.group(2)
    bg_m = re.search(r'background:\s*([^;]+);', body)
    if bg_m:
        v = bg_m.group(1).strip()
        if 'var(' in v:
            name = re.search(r'var\((--[\w-]+)\)', v)
            if name:
                class_bg[cls] = PALETTE.get(name.group(1), v)
        elif v.startswith('#'):
            class_bg[cls] = v
    color_m = re.search(r'color:\s*([^;]+);', body)
    if color_m:
        v = color_m.group(1).strip()
        if 'var(' in v:
            name = re.search(r'var\((--[\w-]+)\)', v)
            if name:
                class_color[cls] = PALETTE.get(name.group(1), v)
        elif v.startswith('#'):
            class_color[cls] = v


def walk_classes(elem_classes):
    """Given a list of classes, return (bg, color) from the matching rules.
    For multiple classes, later/more-specific wins (in CSS terms)."""
    bg, color = None, None
    for cls in elem_classes.split():
        if cls in class_bg and not bg:
            bg = class_bg[cls]
        if cls in class_color and not color:
            color = class_color[cls]
    return bg, color


# Audit findings
findings = []

# Specific known issues
def add(file, component, bg, fg, ratio, g, note):
    findings.append((file, component, bg, fg, ratio, g, note))


# .btn-link is gold text on whatever its parent background is
# When used on a service card (white bg) → fail
# When used on white section bg → fail
# When used inside section-dark (dark bg) → OK (probably)
for dirpath, _, filenames in os.walk(ROOT):
    for f in filenames:
        if not f.endswith('.html'):
            continue
        path = os.path.join(dirpath, f)
        rel = os.path.relpath(path, ROOT)
        with open(path, 'r', encoding='utf-8') as fp:
            content = fp.read()

        # Find .btn-link instances
        for m in re.finditer(r'<a[^>]*class="[^"]*btn-link[^"]*"[^>]*>([^<]+)</a>', content):
            text = m.group(1).strip()
            # Find enclosing section bg
            pos = m.start()
            section_re = re.compile(r'<section[^>]*style="([^"]+)"[^>]*>')
            section_bg = None
            for sm in section_re.finditer(content, 0, pos):
                bg_m = re.search(r'background:\s*([^;"]+)', sm.group(1))
                if bg_m:
                    v = bg_m.group(1).strip()
                    if v.startswith('var('):
                        section_bg = PALETTE.get(re.search(r'var\((--[\w-]+)\)', v).group(1))
            if not section_bg:
                continue
            ratio = contrast(section_bg, PALETTE['--color-primary'])
            g = grade(ratio)
            if g in ('FAIL', 'AA-Large'):
                add(rel, 'btn-link "' + text + '"', section_bg, '#D4AF37', ratio, g,
                    'gold text on light background')


# Sort and print
print(f'{"RATIO":<7} {"GRADE":<10} {"BG":<10} {"FG":<10} COMPONENT (file)')
print('=' * 100)
for f in findings:
    rel, comp, bg, fg, ratio, g, note = f
    mark = '!!' if g == 'FAIL' else '! '
    print(f'{ratio:5.2f}  {g:<10} {bg:<10} {fg:<10} {mark} {comp}  ({rel})')
print('=' * 100)
print(f'Total findings: {len(findings)}')
