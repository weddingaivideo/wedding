"""Verify i18n files on production match local."""
import json
import urllib.request
import sys

LANGS = ["en", "zh", "es", "fr", "de", "ja", "pt", "ar", "ru", "th"]

print(f"Lang | Local size | Online size | Match | Violations")
print("-" * 100)
total_mismatches = 0
for lang in LANGS:
    with open(f"i18n/{lang}.json", "r", encoding="utf-8") as f:
        local = json.load(f)
    try:
        req = urllib.request.Request(
            f"https://weddingai.video/i18n/{lang}.json",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            online = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"{lang}: ERROR {e}")
        continue

    # Compare
    local_keys = set(local.keys())
    online_keys = set(online.keys())
    only_local = local_keys - online_keys
    only_online = online_keys - local_keys

    # Count violations
    violations = 0
    for k, v in online.items():
        if ".title_text." in k and v and len(v) > 60:
            violations += 1
        elif ".meta_description." in k and v and len(v) > 160:
            violations += 1

    if only_local or only_online:
        print(f"{lang}: ❌ {len(only_local)} only local, {len(only_online)} only online")
        total_mismatches += len(only_local) + len(only_online)
    else:
        # Check value diffs
        diffs = sum(1 for k in local if local.get(k) != online.get(k))
        status = "✅" if diffs == 0 else f"⚠️ {diffs} value diffs"
        print(f"{lang}: {len(local):>5} keys | violations: {violations} | {status}")
        total_mismatches += diffs

print()
print(f"Total mismatches: {total_mismatches}")
if total_mismatches == 0:
    print("✅ All i18n files match between local and production")
    sys.exit(0)
else:
    print(f"❌ {total_mismatches} differences found")
    sys.exit(1)
