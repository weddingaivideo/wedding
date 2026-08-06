#!/usr/bin/env python3
"""Comprehensive SEO audit per page against Google best practices."""
import os
import re
import sys
from collections import Counter
from html import unescape

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# Stop words to ignore when counting "keywords"
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "as", "into", "your",
    "we", "you", "our", "us", "they", "them", "it", "its", "this", "that", "these",
    "those", "i", "me", "my", "he", "she", "his", "her", "their", "what", "which",
    "who", "when", "where", "why", "how", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "can", "just", "if", "then", "about",
    "up", "out", "off", "over", "after", "before", "while", "during", "through",
    "above", "below", "between", "again", "further", "once", "here", "there",
    "also", "amp", "s",
}


def visible_text(html):
    """Extract visible text from HTML (strip tags, decode entities, collapse whitespace)."""
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_meta(html, name):
    pat = re.compile(rf'<meta\s+name="{name}"\s+content="([^"]+)"', re.IGNORECASE)
    m = pat.search(html)
    return unescape(m.group(1)) if m else None


def get_title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
    return unescape(m.group(1).strip()) if m else None


def get_headings(html):
    h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
    h2 = re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.DOTALL | re.IGNORECASE)
    h3 = re.findall(r"<h3[^>]*>(.*?)</h3>", html, re.DOTALL | re.IGNORECASE)
    return (
        [unescape(re.sub(r"<[^>]+>", "", h)).strip() for h in h1],
        [unescape(re.sub(r"<[^>]+>", "", h)).strip() for h in h2],
        [unescape(re.sub(r"<[^>]+>", "", h)).strip() for h in h3],
    )


def get_imgs_without_alt(html):
    imgs = re.findall(r"<img\b([^>]*)/?>", html, re.IGNORECASE)
    bad = []
    for attrs in imgs:
        if "alt=" not in attrs.lower():
            src_m = re.search(r'src="([^"]+)"', attrs, re.IGNORECASE)
            if src_m:
                bad.append(src_m.group(1).split("/")[-1])
    return bad


def internal_links(html, current_rel):
    """Count internal links (href starting with / or relative)."""
    links = re.findall(r'<a\s+[^>]*href="([^"]+)"', html, re.IGNORECASE)
    internal = 0
    for href in links:
        if href.startswith("/") or href.endswith(".html") or href.startswith("#"):
            if not href.startswith("http"):
                internal += 1
    return internal


def external_links(html):
    links = re.findall(r'<a\s+[^>]*href="(https?://[^"]+)"', html, re.IGNORECASE)
    return links


def top_keywords(text, n=10):
    words = re.findall(r"[a-z][a-z0-9-]{2,}", text.lower())
    counts = Counter(w for w in words if w not in STOP_WORDS and len(w) >= 4)
    return counts.most_common(n)


def check_keyword_in(places, kw):
    """Return list of (place, count) for places containing kw."""
    return [(p, c) for p, c in places]


def audit_page(rel, html):
    issues = []
    score = 100
    metrics = {}

    # 1. Title
    title = get_title(html)
    if not title:
        issues.append(("CRIT", "Missing <title>"))
        score -= 30
    else:
        tlen = len(title)
        metrics["title"] = f"{tlen} chars — {title}"
        if tlen < 30:
            issues.append(("WARN", f"Title short ({tlen} chars). Google may rewrite; aim 40-60."))
            score -= 5
        elif tlen > 60:
            issues.append(("FAIL", f"Title > 60 chars ({tlen}). Truncated in search results."))
            score -= 10
        elif tlen < 40:
            issues.append(("WARN", f"Title under 40 chars ({tlen}). Consider adding more context."))
            score -= 2

    # 2. Description
    desc = get_meta(html, "description")
    if not desc:
        issues.append(("CRIT", "Missing meta description"))
        score -= 20
    else:
        dlen = len(desc)
        metrics["description"] = f"{dlen} chars"
        if dlen < 70:
            issues.append(("WARN", f"Description short ({dlen} chars). Aim 120-160."))
            score -= 3
        elif dlen > 160:
            issues.append(("FAIL", f"Description > 160 chars ({dlen}). Truncated."))
            score -= 5
        elif dlen < 120:
            issues.append(("WARN", f"Description under 120 chars ({dlen}). Google may pad with own snippet."))
            score -= 1

    # 3. Headings
    h1, h2, h3 = get_headings(html)
    metrics["h1/h2/h3"] = f"{len(h1)}/{len(h2)}/{len(h3)}"
    if len(h1) == 0:
        issues.append(("FAIL", "No <h1>. Search engines need exactly one H1 per page."))
        score -= 15
    elif len(h1) > 1:
        issues.append(("WARN", f"{len(h1)} <h1> tags. Best practice: exactly 1 H1 per page."))
        score -= 5
    if len(h2) == 0 and len(h1) > 0:
        issues.append(("WARN", "No <h2>. Page lacks content structure (aim for 3+ H2 per service page)."))
        score -= 3
    if len(h3) == 0 and len(h2) == 0:
        issues.append(("WARN", "No <h2>/<h3>. Add section/subsection headings."))
        score -= 3

    # 4. Body content length
    text = visible_text(html)
    word_count = len(text.split())
    metrics["words"] = word_count
    if word_count < 150:
        issues.append(("CRIT", f"Thin content ({word_count} words). Aim 500+ for service pages."))
        score -= 20
    elif word_count < 300:
        issues.append(("WARN", f"Light content ({word_count} words). Aim 500+ for service pages."))
        score -= 8
    elif word_count < 500:
        issues.append(("WARN", f"Modest content ({word_count} words). Consider expanding to 600+."))
        score -= 3

    # 5. Primary keyword in title
    if title and h1:
        title_lower = title.lower()
        h1_lower = " ".join(h1).lower()
        # Find common words (potential primary keyword)
        title_words = [w for w in re.findall(r"[a-z][a-z0-9]{3,}", title_lower) if w not in STOP_WORDS]
        h1_words = [w for w in re.findall(r"[a-z][a-z0-9]{3,}", h1_lower) if w not in STOP_WORDS]
        overlap = set(title_words) & set(h1_words)
        if not overlap:
            issues.append(("WARN", "Title and H1 share no keywords. They should describe the same topic."))
            score -= 3
        else:
            metrics["title↔h1 overlap"] = ", ".join(list(overlap)[:3])

    # 6. Keyword in first 100 words
    first100 = " ".join(text.split()[:100]).lower()
    if h1:
        # Use first 2 significant H1 words as proxy for primary keyword
        h1_kw = " ".join(h1[0].lower().split()[:2]) if h1[0] else ""
        if h1_kw and h1_kw not in first100:
            issues.append(("WARN", f"Primary keyword '{h1_kw}' not in first 100 words."))
            score -= 3
        else:
            metrics["primary kw in first 100 words"] = "yes"

    # 7. Keyword density (top keyword in body)
    if h1:
        primary = h1[0].lower().split()[0] if h1[0] else ""
        if primary and len(primary) > 3:
            count = text.lower().count(primary)
            density = count / max(word_count, 1) * 100
            metrics["kw density"] = f"'{primary}' = {count} times ({density:.1f}%)"
            if density > 4:
                issues.append(("WARN", f"Possible keyword stuffing: '{primary}' at {density:.1f}% density (>3% is risky)."))
                score -= 4
            elif density < 0.3:
                issues.append(("WARN", f"Primary keyword '{primary}' only {density:.1f}% density (<0.5% is weak signal)."))
                score -= 2

    # 8. Images without alt
    bad_alts = get_imgs_without_alt(html)
    if bad_alts:
        issues.append(("WARN", f"{len(bad_alts)} image(s) missing alt text: {', '.join(bad_alts[:3])}"))
        score -= 2

    # 9. Internal links
    il = internal_links(html, rel)
    metrics["internal links"] = il
    if rel.endswith(".html") and "index.html" not in rel and rel != "order.html" and il < 3:
        issues.append(("WARN", f"Only {il} internal links. Aim for 5+ to spread link equity."))
        score -= 3

    # 10. External links (outbound)
    ext = external_links(html)
    if ext:
        metrics["external links"] = len(ext)
    else:
        if word_count > 300:
            issues.append(("WARN", "No external links. Consider 1-2 outbound to authoritative sources."))
            score -= 1

    # 11. Canonical
    if 'rel="canonical"' not in html:
        issues.append(("WARN", "Missing <link rel='canonical'>."))
        score -= 3

    # 12. Open Graph
    if 'property="og:title"' not in html:
        issues.append(("WARN", "Missing og:title (impacts social sharing)."))
        score -= 2
    if 'property="og:description"' not in html:
        issues.append(("WARN", "Missing og:description."))
        score -= 2
    if 'property="og:image"' not in html:
        issues.append(("WARN", "Missing og:image."))
        score -= 2

    # 13. Schema
    if 'application/ld+json' not in html:
        issues.append(("WARN", "No JSON-LD schema.org markup."))
        score -= 5

    # 14. Mobile viewport
    if 'name="viewport"' not in html:
        issues.append(("CRIT", "Missing viewport meta."))
        score -= 10

    # 15. Top keywords
    top = top_keywords(text, 5)
    metrics["top kw"] = ", ".join(f"{w}({c})" for w, c in top)

    return score, issues, metrics


def main():
    files = []
    for root, dirs, names in os.walk(ROOT):
        if "scripts\\archive" in root or "scripts/archive" in root:
            continue
        for name in names:
            if name.endswith(".html") and name != "google-site-verification.html":
                files.append(os.path.join(root, name))

    results = []
    for path in files:
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        score, issues, metrics = audit_page(rel, html)
        results.append((rel, score, issues, metrics))

    results.sort(key=lambda r: r[1])

    print("=" * 100)
    print("WEDDINGAI.VIDEO — SEO AUDIT (Google best-practices, July 2026)")
    print("=" * 100)
    print()
    for rel, score, issues, metrics in results:
        grade = "A" if score >= 90 else ("B" if score >= 80 else ("C" if score >= 70 else ("D" if score >= 60 else "F")))
        print(f"## {rel}  —  Score: {score}/100  [{grade}]")
        for k, v in metrics.items():
            print(f"   {k:<26} {v}")
        if issues:
            print("   Issues:")
            for sev, msg in issues:
                tag = {"CRIT": "🔴", "FAIL": "❌", "WARN": "⚠️ "}[sev]
                print(f"     {tag} [{sev}] {msg}")
        else:
            print("   ✅ No issues")
        print()

    print("=" * 100)
    avg = sum(r[1] for r in results) / len(results)
    print(f"Overall: {len(results)} pages, average score {avg:.0f}/100")
    fails = [r for r in results if r[1] < 70]
    if fails:
        print(f"Pages needing attention (score < 70): {len(fails)}")
        for r in fails:
            print(f"  - {r[0]}: {r[1]}")


if __name__ == "__main__":
    main()
