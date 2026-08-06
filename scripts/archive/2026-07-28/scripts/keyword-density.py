"""Keyword density analyzer.
For each page, extract top meaningful keywords (excluding stop words),
compare against title/h1/description, and flag density issues.
"""
import os, re, glob
from collections import Counter

STOP = set('''a an and are as at be by for from has have he her his i in is it its
of on or our she that the their them they this to was we were what when which who
with you your you re not no so do does did but can will would should could just
also than then there here all any some more most such only own same other
this that these those am is are was were been being'''.split())

# Noise from HTML attributes, JSON-LD schema, CSS variables
NOISE = set('''type name var https http https www com var href rel src alt title class
style span div img meta link script noscript content date description
publisher organization organizationname person address telephone email
street city region postal country openinghoursprice currency price
availability lowprice highprice ratingvalue reviewcount author headline
image caption area rooms bedbed amenityfeature
contenturl encodingformat thumbnailurl upload datewidth
heightduration interactstatistic userinteractioncount
target urltemplate entrypoint searchaction potentialaction
query-input query input web site website search action name
identifier alternatename sameas knowslanguage knowsabout
mainentityofpage main entityofpage'''.split())

def meaningful_words(text):
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)  # strip tags
    text = re.sub(r'&[a-z]+;', ' ', text)  # strip entities
    words = re.findall(r"\b[a-z][a-z'-]{2,}\b", text.lower())
    return [w for w in words if w not in STOP and w not in NOISE and len(w) >= 3]

def get_meta(html, attr):
    m = re.search(rf'<meta name="{attr}" content="([^"]+)"', html)
    return m.group(1) if m else ''

def get_og(html, attr):
    m = re.search(rf'<meta property="{attr}" content="([^"]+)"', html)
    return m.group(1) if m else ''

def get_h1(html):
    m = re.findall(r'<h1[^>]*>([^<]+)</h1>', html)
    return ' '.join(m).strip()

def title_text(html):
    m = re.search(r'<title>([^<]+)</title>', html)
    return m.group(1) if m else ''

files = sorted(glob.glob('*.html') + glob.glob('services/**/*.html', recursive=True))
files = [f for f in files if 'google-site-verification' not in f]

print('=' * 80)
print('KEYWORD DENSITY REPORT')
print('=' * 80)

issues = []
for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        html = fh.read()
    words = meaningful_words(html)
    if not words:
        continue
    total = len(words)
    counter = Counter(words)
    top = counter.most_common(8)

    title = title_text(html).lower()
    desc = get_meta(html, 'description').lower()
    h1 = get_h1(html).lower()

    # Check if top 1-2 keywords appear in title/h1
    primary = top[0][0] if top else ''
    secondary = top[1][0] if len(top) > 1 else ''

    p_in_title = primary in title
    p_in_h1 = primary in h1
    p_in_desc = primary in desc
    p_density = round(top[0][1] / total * 100, 2) if total else 0

    s_in_title = secondary in title
    s_in_h1 = secondary in h1
    s_density = round(top[1][1] / total * 100, 2) if len(top) > 1 else 0

    flags = []
    if not p_in_title:
        flags.append(f'primary "{primary}" NOT in title')
    if not p_in_h1:
        flags.append(f'primary "{primary}" NOT in h1')
    if p_density < 0.5 and total > 100:
        flags.append(f'primary "{primary}" density LOW ({p_density}%)')
    if p_density > 4.0:
        flags.append(f'primary "{primary}" density HIGH ({p_density}%, risk stuffing)')

    print(f'\n{f}')
    print(f'  Title: {title[:60]}')
    print(f'  Words: {total}')
    print(f'  Top 5: {", ".join(f"{w}({c})" for w,c in top[:5])}')
    print(f'  Primary: "{primary}"  density={p_density}%  in_title={p_in_title}  in_h1={p_in_h1}  in_desc={p_in_desc}')
    print(f'  Secondary: "{secondary}"  density={s_density}%  in_title={s_in_title}  in_h1={s_in_h1}')
    if flags:
        for flag in flags:
            print(f'  ⚠️  {flag}')
            issues.append((f, flag))

print(f'\n{"=" * 80}')
print(f'SUMMARY: {len(issues)} flags across {len(files)} pages')
print('=' * 80)
