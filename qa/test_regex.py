import re
html = '''
<script nonce="xx" type="application/ld+json">{"@context":"https://schema.org","name":"Tool 1"},{"name":"Wedding Photo Collage Maker"}</script>
<p>visible body</p>
'''
visible = re.sub(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>[\s\S]*?</script>', '', html)
print('AFTER:')
print(repr(visible))
print('contains WPCM:', 'Wedding Photo Collage Maker' in visible)
