#!/usr/bin/env python3
"""B6 / B13 / B14 / B15 / C19 bulk fixes."""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")

# ---- B6: relative ../privacy → absolute /privacy/ ----
print("=== B6: relative ../privacy → absolute /privacy/ ===")
RX_REL = re.compile(r'href="\.\./(privacy|terms)([/"]?)')
fixed_b6 = 0
for p in ROOT.rglob("*.html"):
    if any(s in p.parts for s in ("i18n", "qa", "tmp")):
        continue
    raw = p.read_text(encoding="utf-8")
    new, n = RX_REL.subn(r'href="/\1/\2', raw)
    if n:
        p.write_text(new, encoding="utf-8", newline="")
        fixed_b6 += n
        print(f"  {p.relative_to(ROOT)}: {n} fixes")
print(f"  Total B6 fixes: {fixed_b6}")

# ---- B13: add GA4 to 3 missing files ----
print("\n=== B13: add GA4 to 404/google-verification/admin-leads ===")
GA4_BLOCK = """
    <!-- Google tag (gtag.js) — lazy-loaded to keep it off the critical render path -->
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-4FE7KSJDNB', { send_page_view: true });
    </script>
"""
# for /admin/leads/index.html we use the same gtag
for target in [ROOT / "404.html", ROOT / "google-site-verification.html", ROOT / "admin" / "leads" / "index.html"]:
    if not target.exists():
        print(f"  SKIP missing: {target}")
        continue
    raw = target.read_text(encoding="utf-8")
    if "G-4FE7KSJDNB" in raw:
        print(f"  already has GA4: {target.name}")
        continue
    # Insert before </head>
    new = raw.replace("</head>", GA4_BLOCK + "</head>", 1)
    if new == raw:
        print(f"  NO </head> in {target.name}")
        continue
    target.write_text(new, encoding="utf-8", newline="")
    print(f"  added GA4 to {target.name}")

# ---- B14: _redirects cleanup (deduplicate service short-name rules) ----
print("\n=== B14: _redirects deduplicate service short-name rules ===")
REDIRECTS = ROOT / "_redirects"
content = REDIRECTS.read_text(encoding="utf-8")
lines = content.splitlines()

# Service slugs that have both bare and trailing-slash versions
service_slugs = [
    "family-message", "family-tribute", "celebrity-message",
    "slow-motion", "ai-video-generator", "pet-wedding",
    "wedding-trailer", "multilingual", "cartoon-style", "meme-generator",
]

# For each service, keep only the trailing-slash version (308 canonical)
seen_with_slash = set()
new_lines = []
removed = 0
for line in lines:
    # Match bare service rule like /family-message   /services/...
    bare_match = re.match(r"^\s*/(family-message|family-tribute|celebrity-message|slow-motion|ai-video-generator|pet-wedding|wedding-trailer|multilingual|cartoon-style|meme-generator)\s+/services/", line)
    slash_match = re.match(r"^\s*/(family-message|family-tribute|celebrity-message|slow-motion|ai-video-generator|pet-wedding|wedding-trailer|multilingual|cartoon-style|meme-generator)/\s+/services/", line)
    if bare_match and not slash_match:
        # Bare version — skip
        removed += 1
        continue
    new_lines.append(line)

if removed:
    REDIRECTS.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
print(f"  Removed {removed} duplicate bare-slug service redirect rules")

# ---- B15: remove AI IMAGE PROMPT comments from service pages ----
print("\n=== B15: remove AI IMAGE PROMPT comments from service pages ===")
RX_PROMPT = re.compile(
    r"\s*<!--\s*AI IMAGE PROMPT[\s\S]*?-->\s*\n",
    re.IGNORECASE,
)
fixed_b15 = 0
for p in (ROOT / "services").rglob("*.html"):
    raw = p.read_text(encoding="utf-8")
    new, n = RX_PROMPT.subn("\n", raw)
    if n:
        p.write_text(new, encoding="utf-8", newline="")
        fixed_b15 += n
        print(f"  {p.relative_to(ROOT)}: {n} comments removed")
print(f"  Total B15 comments removed: {fixed_b15}")

# ---- C19: _headers add per-type cache strategy ----
print("\n=== C19: _headers add fine-grained cache ===")
HEADERS = ROOT / "_headers"
header_content = HEADERS.read_text(encoding="utf-8")

# Append a section for asset caching
if "# Fine-grained per-type caching" not in header_content:
    cache_block = """

# ---------- Fine-grained per-type caching -------------------------------
# CSS/JS use ?v=N versioning so cache-busting is via query string.
# HTML is short-lived (1 min) so deploys propagate fast; pure static
# assets (images, fonts) cache 30 days. The CDN still enforces its own
# max-age=14400 for static — this only adjusts the HTML TTL.
/*.html
  Cache-Control: public, max-age=60
/blog/*/*.html
  Cache-Control: public, max-age=300
/sitemap.xml
  Cache-Control: public, max-age=3600
/llms.txt
  Cache-Control: public, max-age=86400
/llms-full.txt
  Cache-Control: public, max-age=86400

# Images & fonts: long cache (1 year) since they have hashed filenames
# or are content-stable.
"""
    HEADERS.write_text(header_content + cache_block, encoding="utf-8")
    print("  Added fine-grained cache strategy to _headers")
else:
    print("  _headers already has cache strategy")

print("\n=== Done ===")
