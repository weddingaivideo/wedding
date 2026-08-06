"""
Generate llms.txt and llms-full.txt.

llms.txt: short index (per https://llmstxt.org/), groups all public pages
  with one-line descriptions, sorted by section.

llms-full.txt: full text dump of all 73 HTML pages concatenated, for LLM
  ingestion. Skips nav/header/footer to keep content dense.

Both are regenerated on every deploy. They sit at the site root and are
referenced by AI crawlers (GPTBot, ClaudeBot, etc.) for index discovery.
"""
import os
import re
from pathlib import Path
from datetime import date

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
SITE = "https://weddingai.video"
EXCLUDE_DIRS = {"admin", "functions", "tmp", "__pycache__", "qa", "i18n",
                "js", "styles", "scripts", "docs", "search", "internal-docs",
                "internal-admin", "google-site-verification.html"}

def all_html():
    out = []
    for p in ROOT.rglob("*.html"):
        parts = {str(x) for x in p.parts}
        if parts & EXCLUDE_DIRS:
            continue
        if p.name in {"google-site-verification.html", "offline.html", "404.html"}:
            continue
        out.append(p)
    return sorted(out)

def extract_meta(text: str) -> tuple[str, str]:
    """Return (title, description) from HTML <head>.

    Handles both bare <title>TEXT</title> and attribute-laden
    <title data-i18n="...">TEXT</title> (the pattern used throughout the
    site — most pages wrap the title in a data-i18n attribute so the
    i18n pipeline can replace it on non-English pages).
    """
    title = ""
    m = re.search(r"<title(?:\s[^>]*)?>([^<]+)</title>", text, re.IGNORECASE)
    if m:
        title = m.group(1).strip()
        # Decode any HTML entities the title may contain
        title = (title
                 .replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                 .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
                 .replace("&mdash;", "—").replace("&ndash;", "–"))
    desc = ""
    # data-i18n-attr="content:..." is the i18n-aware pattern; fall back to
    # the static <meta name="description" content="..."> form for the few
    # pages that don't have i18n attr wrapping.
    m = re.search(r'<meta\s+name="description"(?:\s+data-i18n-attr="[^"]*")?\s+content="([^"]+)"', text, re.IGNORECASE)
    if m:
        desc = m.group(1).strip()
        desc = (desc
                .replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
                .replace("&mdash;", "—").replace("&ndash;", "–"))
    return title, desc

def path_to_url(p: Path) -> str:
    rel = p.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return SITE + "/" + rel[:-len("index.html")]
    return SITE + "/" + rel

def section_for(p: Path) -> str:
    rel = p.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "Home"
    parts = rel.split("/")
    top = parts[0]
    if top.startswith("services"):
        return "Services"
    if top.startswith("blog"):
        return "Blog"
    if top in {"about", "gallery", "pricing", "resources", "order",
               "success", "privacy", "terms"}:
        return top.capitalize()
    return "Other"

# --- llms.txt (short) ---
llms_lines = [
    "# WeddingAI.video",
    "",
    "> AI-powered wedding video restoration and personalization services. "
    "VHS-to-digital, slow motion, family tributes, multilingual dubbing, "
    "cartoon/animation, meme generators, and more.",
    "",
    "## Pages",
    "",
]

by_section: dict[str, list[tuple[str, str, str]]] = {}
for p in all_html():
    title, desc = extract_meta(p.read_text(encoding="utf-8", errors="ignore"))
    if not title:
        title = p.stem
    url = path_to_url(p)
    sec = section_for(p)
    by_section.setdefault(sec, []).append((url, title, desc))

SECTION_ORDER = ["Home", "Services", "Blog", "About", "Gallery", "Pricing",
                 "Resources", "Order", "Success", "Privacy", "Terms", "Other"]
for sec in SECTION_ORDER:
    if sec not in by_section:
        continue
    llms_lines.append(f"### {sec}")
    llms_lines.append("")
    for url, title, desc in by_section[sec]:
        if desc:
            llms_lines.append(f"- [{title}]({url}): {desc}")
        else:
            llms_lines.append(f"- [{title}]({url})")
    llms_lines.append("")

llms_lines.extend([
    "## Optional",
    "",
    f"- [{SITE}/llms-full.txt]({SITE}/llms-full.txt): full text dump for LLM ingestion",
    f"- [{SITE}/sitemap.xml]({SITE}/sitemap.xml): complete URL list",
    "",
])
(ROOT / "llms.txt").write_text("\n".join(llms_lines), encoding="utf-8")
print(f"llms.txt: {len(llms_lines)} lines, {sum(1 for L in llms_lines if L.startswith('- '))} pages")

# --- llms-full.txt (full text) ---
def strip_nav(text: str) -> str:
    """Best-effort: drop <nav>, <header>, <footer> blocks for denser content."""
    text = re.sub(r"<nav[\s\S]*?</nav>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<header[\s\S]*?</header>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<footer[\s\S]*?</footer>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
    return text

def html_to_text(html: str) -> str:
    """Crude HTML → text. Good enough for LLM ingestion."""
    # Remove tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Decode common entities
    text = (text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " "))
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()

full_chunks = [
    f"# WeddingAI.video — full text index for LLM ingestion",
    f"Generated {date.today().isoformat()}. {len(list(all_html()))} pages.",
    f"Site: {SITE}",
    "",
]

for p in all_html():
    title, desc = extract_meta(p.read_text(encoding="utf-8", errors="ignore"))
    url = path_to_url(p)
    body = strip_nav(p.read_text(encoding="utf-8", errors="ignore"))
    body_text = html_to_text(body)
    full_chunks.append(f"## {title or p.stem}")
    full_chunks.append(f"URL: {url}")
    if desc:
        full_chunks.append(f"Description: {desc}")
    full_chunks.append("")
    full_chunks.append(body_text[:30000])  # cap per page so output stays sane
    full_chunks.append("")
    full_chunks.append("---")
    full_chunks.append("")

(ROOT / "llms-full.txt").write_text("\n".join(full_chunks), encoding="utf-8")
print(f"llms-full.txt: {len(full_chunks)} sections, {(ROOT / 'llms-full.txt').stat().st_size:,} bytes")
