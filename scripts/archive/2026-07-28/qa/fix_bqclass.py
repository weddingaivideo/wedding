from pathlib import Path
import re
text = Path('gallery/index.html').read_text(encoding='utf-8')
new_text = re.sub(r'<blockquoteclass="', r'<blockquote class="', text)
Path('gallery/index.html').write_text(new_text, encoding='utf-8')
print('Fixed')
