#!/usr/bin/env python3
"""Fill the blank SERP comparison table on the remote-family blog page.

THE BUG
-------
blog/include-remote-family-wedding-video/index.html carries a SERP comparison
table whose 51 elements all point at

    blog.include_remote_family_wedding_video.serp_comparison.*

That namespace does not exist in ANY dictionary (en/zh/es/fr/de/pt/ja/ru/
ar/th/hi all use the HYPHENATED page namespace
blog.include-remote-family-wedding-video.*). It was never more than a
copy-paste artifact from the sibling page
blog/best-ai-wedding-video-tools-2026/, whose table has the same shape:
6 columns (Tool / Style / Languages / Output / Price / Workflow) and the same
7 rows (WeddingAI, Vidu, PicLumen, Pollo, RunwayML, Pika, HeyGen).

Because the middleware resolves a key's shard by its FIRST TWO DOTTED
SEGMENTS (namespaceOf() in functions/_lib/i18n-shards.js), the underscore
namespace is not in i18n/<lang>.manifest.json -> no shard is ever fetched for
it -> every one of those 51 elements stays empty in all 11 languages. The
table renders as 6 blank headers and 42 blank cells.

THE FIX
-------
1. The 48 shared keys (th.* + td.*) are repointed at the sibling namespace
   blog.best_ai_wedding_video_tools_2026.serp_comparison.*, which EXISTS in
   every language dictionary (42-52 of 52 keys per language) and already has
   a shard in the manifest. Reusing the published copy keeps the site's own
   wording and claims - nothing new is asserted about a competitor.
2. The 3 page-specific strings (h2, p_text, p_trailing) are repointed at the
   page's OWN namespace, blog.include-remote-family-wedding-video.
   serp_comparison.*, which is the same namespace as the page's other 149
   keys -> same shard file, no new shard, no new manifest entry.
   Their English source is written here; the 11 dictionaries get the
   translations from qa/fix-blog-remote-family-serp-i18n.py.

Every element also gets its English text as static content, because the
English site never runs the translation pass (the middleware returns null for
DEFAULT_LANG) and because applyDataI18n() leaves the English source alone
when a key is missing from a language dictionary.

Idempotent: running it twice changes nothing.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGE = REPO / "blog" / "include-remote-family-wedding-video" / "index.html"

OLD_NS = "blog.include_remote_family_wedding_video.serp_comparison."
SIBLING_NS = "blog.best_ai_wedding_video_tools_2026.serp_comparison."
OWN_NS = "blog.include-remote-family-wedding-video.serp_comparison."

# The three strings that are specific to THIS page. The table itself is the
# published "best AI wedding video tools" comparison; the framing is about
# including family who could not travel to the wedding.
PAGE_SPECIFIC = {
    "h2": (
        "AI Wedding Video Tools for Including Remote Family: "
        "7 Tools vs WeddingAI.video"
    ),
    "p_text": (
        "Google SERPs (October 2025) for 'AI wedding video for remote "
        "family': Vidu AI, PicLumen, Pollo AI, RunwayML, Pika Labs, HeyGen. "
        "Most are generic AI video tools built for marketing clips, not for "
        "a wedding film that relatives abroad can watch. WeddingAI.video "
        "delivers a 60-90s cinematic wedding film + 11 languages + face "
        "preservation:"
    ),
    "p_trailing": (
        "When the audience is family who could not travel, multilingual "
        "delivery and face preservation decide whether the message lands. "
        "WeddingAI.video delivers a 60-90s cinematic film + 11 languages + "
        "face preservation from your photos."
    ),
}


def main() -> int:
    import json

    en = json.loads((REPO / "i18n" / "en.json").read_text(encoding="utf-8"))
    text = PAGE.read_text(encoding="utf-8")

    # Every element bound to the broken namespace.
    keys = sorted(set(re.findall(r'data-i18n="' + re.escape(OLD_NS) + r'([^"]+)"', text)))
    if not keys:
        print("Nothing to do: no keys bound to " + OLD_NS)
        return 0

    changed = 0
    missing = []
    for key in keys:
        if key in PAGE_SPECIFIC:
            new_ns, value = OWN_NS, PAGE_SPECIFIC[key]
        else:
            new_ns = SIBLING_NS
            value = en.get(new_ns + key)
            if value is None:
                missing.append(key)
                continue

        # Replace the whole element: opening tag (with the new data-i18n) +
        # the value as its content.
        pat = re.compile(
            r'<(\w+)\b[^>]*\bdata-i18n="' + re.escape(OLD_NS + key) + r'"[^>]*>'
            r'([\s\S]*?)</\1>'
        )

        def repl(m, value=value, new_ns=new_ns):
            open_tag = m.group(0)[: m.group(0).index(">") + 1]
            open_tag = open_tag.replace(
                'data-i18n="' + OLD_NS + key + '"', 'data-i18n="' + new_ns + key + '"'
            )
            return open_tag + value + "</" + m.group(1) + ">"

        text, n = pat.subn(repl, text)
        if n == 0:
            print(f"  !! no element matched for {key}")
        else:
            changed += n

    PAGE.write_text(text, encoding="utf-8", newline="")
    print(f"  {PAGE.relative_to(REPO)}: {changed} element(s) filled, {len(keys)} key(s) seen")
    if missing:
        print(f"  !! no en.json value for: {', '.join(missing)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
