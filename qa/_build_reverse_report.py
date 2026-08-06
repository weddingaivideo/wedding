"""Final REPORT_I18N_REVERSE.md: 9-language summary."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(".")
LANGS = ["zh", "ja", "th", "es", "de", "fr", "pt", "ru", "ar"]
LANG_NAMES = {
    "zh": "Chinese", "ja": "Japanese", "th": "Thai", "es": "Spanish",
    "de": "German", "fr": "French", "pt": "Portuguese", "ru": "Russian",
    "ar": "Arabic",
}

en = json.loads(open(ROOT / "i18n" / "en.json", encoding="utf-8").read())
en_keys = sum(1 for k in en if k != "_meta")

md = []
md.append("# i18n Reverse-Translation Audit — 2026-07-28\n")
md.append(f"**Source keys (en.json):** {en_keys}")
md.append("**Method:** Google translate gtx (zh/es/fr/de/pt/ja/ru/ar/th) reverse-translated to English, then SequenceMatcher similarity vs. original EN. 4 workers concurrent.\n")
md.append("**Translator (declared in `_meta`):** Google Translate (machine) for all 9 langs. The audit is checking how well those machine translations actually preserve meaning when round-tripped.\n")

md.append("## Per-language summary\n")
md.append("| lang | name | total_keys | scored | SUSPICIOUS (sim<0.65) | review (0.65-0.9) | ok (>=0.9) | no_score (short text) | susp_rate |")
md.append("|------|------|------------|--------|------------------------|---------------------|------------|----------------------|-----------|")

grand = Counter()
for code in LANGS:
    csv_p = ROOT / "qa" / f"i18n_reverse_google_{code}.csv"
    if not csv_p.exists():
        md.append(f"| {code} | {LANG_NAMES[code]} | ? | ? | ? | ? | ? | ? | ? |")
        continue
    rows = list(csv.DictReader(open(csv_p, encoding="utf-8")))
    by_kind = Counter(r["flag"] for r in rows)
    sus = by_kind.get("SUSPICIOUS", 0)
    rev = by_kind.get("review", 0)
    ok = by_kind.get("ok", 0)
    ns = by_kind.get("no_score", 0)
    scored = sus + rev + ok
    grand["SUSPICIOUS"] += sus
    grand["review"] += rev
    grand["ok"] += ok
    grand["no_score"] += ns
    grand["total"] += len(rows)
    susp_rate = sus / max(scored, 1) * 100
    md.append(f"| {code} | {LANG_NAMES[code]} | {en_keys} | {scored} | {sus} | {rev} | {ok} | {ns} | {susp_rate:.1f}% |")

md.append("")
md.append("## Grand total\n")
md.append(f"- Total rows: {grand['total']}")
md.append(f"- SUSPICIOUS (sim<0.65): **{grand['SUSPICIOUS']}**")
md.append(f"- review (sim 0.65-0.9): {grand['review']}")
md.append(f"- ok (sim≥0.9): {grand['ok']}")
md.append(f"- no_score (text too short to score): {grand['no_score']}")
md.append("")
md.append("## What this means\n")
md.append("- **SUSPICIOUS = sim<0.65**: The translation, when round-tripped to English, doesn't match the source. Either the translation is **truncated** (e.g. the famous '对于大多数情侣来说，是的。' which drops the rest of the paragraph), **semantically off**, or **written about something else entirely** (the 'mamá passed away' vs '1985 photo came alive' case).\n")
md.append("- **review = 0.65-0.9**: Borderline. Worth a native speaker's eye before publishing.\n")
md.append("- **no_score = text too short**: Names, URLs, brand strings. These are not meaningful to score and don't need fixing.\n")
md.append("")
md.append("## Top 10 most-suspicious per language (preview)\n")
for code in LANGS:
    csv_p = ROOT / "qa" / f"i18n_reverse_google_{code}.csv"
    if not csv_p.exists():
        continue
    rows = list(csv.DictReader(open(csv_p, encoding="utf-8")))
    sus = sorted(
        [r for r in rows if r["flag"] == "SUSPICIOUS"],
        key=lambda r: float(r["similarity"]),
    )[:5]
    if not sus:
        continue
    md.append(f"\n### {code} ({LANG_NAMES[code]})")
    for r in sus:
        en_v = r["en"][:120].replace("\n", " ")
        tgt_v = r["tgt"][:120].replace("\n", " ")
        md.append(f"- sim={r['similarity']} `{r['key']}`")
        md.append(f"  - EN: {en_v}")
        md.append(f"  - {code.upper()}: {tgt_v}")

md.append("")
md.append("## What was done about it\n")
md.append("See `qa/REPORT_I18N_ZH_FIX.md` for the zh fix report (V1 single-sample, V2 N=3 stable, with rollback).")
md.append("Other 8 languages can be fixed with the same pipeline: `qa/fix_lang.py --lang <code>`.\n")

(ROOT / "qa" / "REPORT_I18N_REVERSE.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("Wrote qa/REPORT_I18N_REVERSE.md")
print(f"\nGrand total: {grand}")
