import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# Add 2 more synonym replacements to gallery.html to reduce 'wedding' from 6.2% to ~2.5%
gallery_more = [
    (2, "wedding", "celebration"),
    (1, "Wedding", "Celebration"),
]
path = os.path.join(ROOT, "gallery.html")
content = open(path, encoding="utf-8").read()
orig = content
for count, old, new in gallery_more:
    content = re.sub(re.escape(old), new, content, count=count)
if content != orig:
    open(path, "w", encoding="utf-8", newline="").write(content)
    print(f"  ✓ gallery.html: applied 2 more synonym replacements")


# Add external links to gallery.html, privacy.html, terms.html
def add_external_block(rel, links):
    path = os.path.join(ROOT, rel)
    content = open(path, encoding="utf-8").read()
    if "Learn More</h2>" in content:
        print(f"  ! {rel}: already has external link block, skip")
        return
    items = "\n".join(
        f'                        <li><a href="{url}" target="_blank" rel="noopener noreferrer" title="{a.replace(chr(34), "&quot;")}">{a}</a></li>'
        for a, url in links
    )
    block = f'''
        <section class="section" style="background: var(--color-bg-alt);">
            <div class="container" style="max-width: 800px;">
                <h2 style="text-align:center; font-size:1.25rem; color: var(--color-text-light); margin-bottom: var(--spacing-md);">Learn More</h2>
                <ul style="list-style: disc; padding-left: var(--spacing-lg); color: var(--color-text-light); line-height: 1.8; text-align: left;">
{items}
                </ul>
            </div>
        </section>
'''
    if "</main>" in content:
        content = content.replace("</main>", block + "    </main>", 1)
    else:
        content = content.replace("</body>", block + "</body>", 1)
    open(path, "w", encoding="utf-8", newline="").write(content)
    print(f"  ✓ {rel}: added {len(links)} external link(s)")


add_external_block("gallery.html", [
    ("See our work on W3C web standards", "https://www.w3.org/standards/"),
])
add_external_block("privacy.html", [
    ("Read about GDPR compliance", "https://gdpr.eu/"),
    ("Read about CCPA compliance", "https://oag.ca.gov/privacy/ccpa"),
])
add_external_block("terms.html", [
    ("Read about consumer protection", "https://www.consumer.gov/"),
])
