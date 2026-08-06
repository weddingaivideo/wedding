import re
text = open('blog/13-how-long-should-wedding-video-be/index.html', encoding='utf-8').read()
print(f'<strong<strong remaining: {len(re.findall(r"<strong<strong", text))}')
