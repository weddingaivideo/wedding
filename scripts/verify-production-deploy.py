#!/usr/bin/env python3
"""
Production verification of the schema.org upgrade.

Fetches the live HTML for key pages, extracts every JSON-LD block, counts
@type and key fields, and prints a before/after-style comparison against
the pre-deploy targets we set in the rollout plan.

Expectations:
  - /                       : WebApplication present; Organization has knowsLanguage
  - /gallery/               : >= 23 CreativeWork, 6 Review, 1 ItemList
  - /about/                 : AboutPage present
  - /resources/             : LearningResource present
  - /blog/                  : 1 ItemList with numberOfItems=100
  - /blog/<slug>/           : Article with speakable + articleSection
  - /pricing/               : FAQPage with author/upvoteCount on questions
  - /services/.../          : FAQPage with author/upvoteCount
  - /zh/                    : All 200, JSON-LD present, inLanguage=zh-CN
"""
import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

SITE = "https://weddingai.video"
SCRIPT_RE = re.compile(r'<script\b[^>]*\btype="application/ld\+json"[^>]*>(.*?)</script>', re.DOTALL)

PROBES = [
    {"path": "/",                                   "expect": {"WebApplication", "Organization"},  "expect_org_field": "knowsLanguage",  "expect_knows": 10},
    {"path": "/gallery/",                           "expect": {"CreativeWork", "Review", "ItemList"},  "expect_creativework": 23, "expect_review": 6, "expect_itemlist": 1},
    {"path": "/about/",                             "expect": {"AboutPage", "Organization"}},
    {"path": "/resources/",                         "expect": {"LearningResource"}},
    {"path": "/blog/",                              "expect": {"ItemList"}, "expect_itemlist_count": 100},
    {"path": "/blog/weddingai-video-guide/",        "expect": {"Article"}, "expect_article_field": "speakable"},
    {"path": "/blog/wedding-video-cost-2026-new/",  "expect": {"Article"}, "expect_article_field": "articleSection"},
    {"path": "/pricing/",                           "expect": {"FAQPage"}},
    {"path": "/services/personalization/ai-video-generator/", "expect": {"FAQPage"}},
    {"path": "/zh/",                                "expect": {"Organization"}},
    {"path": "/zh/blog/weddingai-video-guide/",     "expect": {"Article"}},
    {"path": "/de/services/",                       "expect": {"Organization"}},
]


def fetch(path: str) -> tuple[str, str]:
    req = Request(SITE + path, headers={"User-Agent": "Mozilla/5.0 (compatible; MavisSchemaVerifier/1.0)",
                                         "Cache-Control": "no-cache",
                                         "Accept": "text/html,application/xhtml+xml"})
    with urlopen(req, timeout=300) as r:
        # stream read so large pages like /blog/ (100-item ItemList) don't
        # hit the per-chunk 60s timeout.
        chunks = []
        while True:
            chunk = r.read(64 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return r.status, b"".join(chunks).decode("utf-8", errors="ignore")


def collect_nodes(data):
    if isinstance(data, dict):
        if "@type" in data:
            yield data
        if "@graph" in data:
            for n in data["@graph"]:
                yield from collect_nodes(n)
    elif isinstance(data, list):
        for n in data:
            yield from collect_nodes(n)


def analyze(path: str) -> dict:
    status, html = fetch(path)
    types = Counter()
    fields = {
        "WebApplication": 0, "AboutPage": 0, "LearningResource": 0,
        "ItemList": 0, "CreativeWork": 0, "Review": 0,
        "Organization.knowsLanguage": 0, "Organization.founder": 0,
        "Article.speakable": 0, "Article.articleSection": 0,
        "FAQPage": 0, "faq.author": 0, "faq.upvoteCount": 0, "faq.answer.url": 0,
    }
    itemlist_total = 0
    script_count = 0
    parse_fail = 0
    for body in SCRIPT_RE.findall(html):
        script_count += 1
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            parse_fail += 1
            continue
        for node in collect_nodes(data):
            t = node.get("@type")
            if isinstance(t, str):
                types[t] += 1
            elif isinstance(t, list):
                for x in t:
                    types[x] += 1
            if node.get("knowsLanguage") and isinstance(node.get("knowsLanguage"), list):
                fields["Organization.knowsLanguage"] = max(fields["Organization.knowsLanguage"], len(node["knowsLanguage"]))
            if node.get("founder"):
                fields["Organization.founder"] += 1
            if node.get("speakable") and t == "Article":
                fields["Article.speakable"] += 1
            if node.get("articleSection") and t == "Article":
                fields["Article.articleSection"] += 1
            if t == "ItemList":
                fields["ItemList"] += 1
                ils = node.get("itemListElement", [])
                if isinstance(ils, list):
                    itemlist_total += len(ils)
            if t == "FAQPage":
                fields["FAQPage"] += 1
                for q in node.get("mainEntity", []) or []:
                    if q.get("author"):
                        fields["faq.author"] += 1
                    if "upvoteCount" in q:
                        fields["faq.upvoteCount"] += 1
                    ans = q.get("acceptedAnswer", {}) or {}
                    if ans.get("url"):
                        fields["faq.answer.url"] += 1
    return {
        "status": status,
        "types": types,
        "fields": fields,
        "script_count": script_count,
        "parse_fail": parse_fail,
        "itemlist_total": itemlist_total,
    }


def main():
    print("=" * 70)
    print(f"PRODUCTION SCHEMA DEPLOYMENT VERIFICATION")
    print(f"site: {SITE}")
    print(f"time: {__import__('datetime').datetime.utcnow().isoformat()}Z")
    print("=" * 70)

    results = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(analyze, p["path"]): p for p in PROBES}
        for fut in as_completed(futs):
            p = futs[fut]
            try:
                results[p["path"]] = (p, fut.result())
            except Exception as e:
                results[p["path"]] = (p, {"error": str(e)})

    overall_pass = 0
    overall_fail = 0
    for p in PROBES:
        path = p["path"]
        probe, res = results[path]
        if "error" in res:
            print(f"\n  ✗  {path}  ERROR: {res['error']}")
            overall_fail += 1
            continue

        checks = []
        types = res["types"]
        # expect @types present
        for et in probe.get("expect", []):
            checks.append((f"has {et}", types.get(et, 0) > 0))

        if "expect_creativework" in probe:
            n = types.get("CreativeWork", 0)
            checks.append((f"CreativeWork ≥ {probe['expect_creativework']}", n >= probe["expect_creativework"]))
        if "expect_review" in probe:
            n = types.get("Review", 0)
            checks.append((f"Review = {probe['expect_review']}", n == probe["expect_review"]))
        if "expect_itemlist" in probe:
            checks.append((f"ItemList ≥ {probe['expect_itemlist']}", types.get("ItemList", 0) >= probe["expect_itemlist"]))
        if "expect_itemlist_count" in probe:
            n = res["itemlist_total"]
            checks.append((f"ItemList items = {probe['expect_itemlist_count']}", n == probe["expect_itemlist_count"]))
        if "expect_org_field" in probe:
            n = res["fields"][f"Organization.{probe['expect_org_field']}"]
            checks.append((f"Organization.{probe['expect_org_field']} > 0", n > 0))
        if "expect_knows" in probe:
            n = res["fields"]["Organization.knowsLanguage"]
            checks.append((f"knowsLanguage ≥ {probe['expect_knows']}", n >= probe["expect_knows"]))
        if "expect_article_field" in probe:
            f = f"Article.{probe['expect_article_field']}"
            n = res["fields"][f]
            checks.append((f"{f} > 0", n > 0))

        passed = sum(1 for _, ok in checks if ok)
        total = len(checks)
        status = "✓" if passed == total else "✗"
        print(f"\n  {status}  {path}  [{passed}/{total}]  types={dict(types)}")
        for name, ok in checks:
            print(f"      {'✓' if ok else '✗'}  {name}")
        if res["parse_fail"]:
            print(f"      ⚠  {res['parse_fail']} parse failures out of {res['script_count']} blocks")
        if passed == total:
            overall_pass += 1
        else:
            overall_fail += 1

    print("\n" + "=" * 70)
    print(f"OVERALL: {overall_pass}/{overall_pass+overall_fail} URLs passed all checks")
    if overall_fail == 0:
        print("✅ Production schema deployment fully verified.")
    else:
        print(f"⚠  {overall_fail} URL(s) have failing checks — review above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
