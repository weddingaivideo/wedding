"""Check LSI / long-tail coverage per page.
Each service has a set of expected long-tail terms. We check coverage.
Also analyze non-service pages for any long-tail opportunities.
"""
import os, re, glob

# Expected LSI per service page
SERVICE_LSI = {
    'services/video-enhancement/slow-motion.html': ['120fps', '240fps', 'frame interpolation', 'first dance', 'frame rate', 'cinematic'],
    'services/absence-compensation/family-tribute.html': ['deceased loved one', 'memorial video', 'in loving memory', 'tribute', 'memorial'],
    'services/absence-compensation/family-message.html': ['remote wedding', 'zoom wedding', 'international family', 'remote', 'video message'],
    'services/absence-compensation/celebrity-message.html': ['celebrity', 'ai-generated', 'AI celebrity', 'star', 'famous'],
    'services/personalization/ai-video-generator.html': ['from photos', 'AI film', 'image-to-video', 'photo to video', 'AI video'],
    'services/personalization/wedding-trailer.html': ['cinematic', 'Hollywood', 'movie trailer', 'licensed music', 'social media'],
    'services/personalization/pet-wedding.html': ['pet', 'dog', 'cat', 'furry', 'animal', 'pet wedding'],
    'services/personalization/multilingual.html': ['subtitles', 'voiceover', 'translation', 'language', 'dub'],
    'services/personalization/cartoon-style.html': ['Studio Ghibli', 'Pixar 3D', 'anime', 'animated', 'animation'],
    'services/personalization/meme-generator.html': ['gif', 'meme', 'reaction gif', 'tiktok', 'instagram'],
    'services/index.html': ['AI wedding', 'wedding services', 'restoration', 'multilingual', 'AI film'],
}

# For non-service pages, just check top-3 keyword density is reasonable
PAGES = sorted(glob.glob('*.html') + glob.glob('services/**/*.html', recursive=True))
PAGES = [f for f in PAGES if 'google-site-verification' not in f]

print('=' * 80)
print('LSI COVERAGE REPORT')
print('=' * 80)

for f in PAGES:
    norm = f.replace(os.sep, '/')
    with open(f, 'r', encoding='utf-8') as fh:
        html = fh.read()
    # Strip script/style
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text_lower = text.lower()

    expected = SERVICE_LSI.get(norm, None)
    if expected:
        covered = []
        missing = []
        for term in expected:
            c = text_lower.count(term.lower())
            if c > 0:
                covered.append(f'{term}({c})')
            else:
                missing.append(term)
        status = '✅' if not missing else '⚠️ '
        print(f'\n{status} {f}')
        print(f'   covered: {", ".join(covered)}')
        if missing:
            print(f'   MISSING: {", ".join(missing)}')

# Non-service pages — just count top-3 keywords and check if any 2-word long-tail combo repeats
print('\n\n' + '=' * 80)
print('NON-SERVICE PAGES — keyword check')
print('=' * 80)

NON_SERVICE = [f for f in PAGES if f not in SERVICE_LSI]
for f in NON_SERVICE:
    with open(f, 'r', encoding='utf-8') as fh:
        html = fh.read()
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text_lower = text.lower()
    # Extract title for context
    m = re.search(r'<title>([^<]+)</title>', html)
    title = m.group(1) if m else ''
    # Word frequency
    words = re.findall(r'\b[a-z]{3,}\b', text_lower)
    from collections import Counter
    counter = Counter(words)
    top5 = counter.most_common(5)
    # Bigrams (2-word combos)
    bigrams = Counter(zip(words, words[1:])).most_common(3)
    # Filter stop
    STOP = set('the a an and or of to in for is it on with that this by from as be are was were has have'.split())
    bigrams_clean = [f'{a} {b}({c})' for (a,b), c in bigrams if a not in STOP and b not in STOP][:3]
    print(f'\n{f}  title="{title[:50]}"')
    print(f'  top words: {", ".join(f"{w}({c})" for w,c in top5)}')
    print(f'  top bigrams: {", ".join(bigrams_clean)}')
