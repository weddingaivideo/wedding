from pathlib import Path
import re
text = Path('services/index.html').read_text(encoding='utf-8')
text = re.sub(r'href="(/personalization/[^"]+)"', r'href="/services\1/"', text)
text = re.sub(r'href="(/absence-compensation/[^"]+)"', r'href="/services\1/"', text)
text = re.sub(r'href="(/video-enhancement/[^"]+)"', r'href="/services\1/"', text)
Path('services/index.html').write_text(text, encoding='utf-8')
print('Fixed')
