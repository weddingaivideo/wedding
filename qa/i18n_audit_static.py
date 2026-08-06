"""
Static i18n translation audit.

Checks (per non-EN language, vs en.json):
  1. Missing keys (in EN but absent in target)
  2. Empty / null values
  3. Untranslated (value == EN source, len > 20)
  4. Length anomaly: target length vs EN length ratio
     - too_short: ratio < 0.3 (suspiciously truncated)
     - too_long:  ratio > 5.0 (suspiciously inflated)
  5. Placeholder drift: target has different {var} / {{var}} / %s / %d set than EN
  6. HTML tag drift: target has unbalanced < or different <tag> count than EN
  7. EN-only chars in target (raw EN words in non-Latin scripts, > 5 EN tokens)

Output: qa/REPORT_I18N_AUDIT.md + per-language CSV.

Usage:  python qa/i18n_audit_static.py [--langs zh,ja] [--ratio-low 0.3] [--ratio-high 5.0]
"""

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"

LANG_NAMES = {
    "en": "English",
    "zh": "Chinese",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "ja": "Japanese",
    "ru": "Russian",
    "ar": "Arabic",
    "th": "Thai",
}

# Latin-script languages where raw EN tokens are NOT a quality red flag.
# Only flag untranslated EN in non-Latin languages.
NON_LATIN = {"zh", "ja", "ru", "ar", "th"}


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


# --- placeholders ---------------------------------------------------------
# Match common i18n placeholder syntaxes.
PH_PATTERNS = [
    re.compile(r"\{\{[^}]+\}\}"),     # {{var}}
    re.compile(r"\{[a-zA-Z_][\w]*\}"),  # {var}
    re.compile(r"%[sdif]"),            # %s, %d, %i, %f
    re.compile(r"\$\{[^}]+\}"),        # ${var}
    re.compile(r"<[^>]+>"),            # <placeholder>
]


def extract_placeholders(s: str) -> set:
    out = set()
    for pat in PH_PATTERNS:
        out.update(m.group(0) for m in pat.finditer(s))
    return out


# --- HTML tags ------------------------------------------------------------
TAG_RE = re.compile(r"<\s*/?\s*([a-zA-Z][\w-]*)(?:\s[^>]*)?\s*>")


def extract_tags(s: str) -> set:
    return {m.group(1).lower() for m in TAG_RE.finditer(s)}


# --- EN-token detection (for non-Latin langs) ----------------------------
# Heuristic: 3+ consecutive a-z letters is an EN token.
EN_TOKEN_RE = re.compile(r"\b[A-Za-z]{3,}\b")


def count_en_tokens(s: str) -> int:
    return len(EN_TOKEN_RE.findall(s))


# --- main check -----------------------------------------------------------
def audit(en: dict, tgt: dict, lang: str, ratio_low: float, ratio_high: float) -> dict:
    findings = []
    en_keys = [k for k in en if k != "_meta"]
    tgt_keys = [k for k in tgt if k != "_meta"]
    en_set, tgt_set = set(en_keys), set(tgt_keys)

    for k in en_keys:
        en_v = en[k]
        if not isinstance(en_v, str):
            continue
        if k not in tgt:
            findings.append({"key": k, "issue": "missing", "en": en_v, "tgt": ""})
            continue
        t_v = tgt[k]
        if not isinstance(t_v, str):
            findings.append({"key": k, "issue": "non_string", "en": en_v, "tgt": str(t_v)})
            continue
        if t_v == "" or t_v is None:
            findings.append({"key": k, "issue": "empty", "en": en_v, "tgt": ""})
            continue
        if t_v == en_v and len(en_v) > 20:
            findings.append({"key": k, "issue": "untranslated", "en": en_v, "tgt": t_v})
            continue
        # length ratio
        if len(en_v) > 0:
            ratio = len(t_v) / len(en_v)
            if ratio < ratio_low:
                findings.append({"key": k, "issue": f"too_short(r={ratio:.2f})", "en": en_v, "tgt": t_v})
                continue
            if ratio > ratio_high:
                findings.append({"key": k, "issue": f"too_long(r={ratio:.2f})", "en": en_v, "tgt": t_v})
                continue
        # placeholder drift
        en_ph = extract_placeholders(en_v)
        t_ph = extract_placeholders(t_v)
        if en_ph != t_ph:
            findings.append({
                "key": k,
                "issue": f"placeholder_drift(en={sorted(en_ph)} tgt={sorted(t_ph)})",
                "en": en_v, "tgt": t_v,
            })
            continue
        # HTML tag drift
        en_tags = extract_tags(en_v)
        t_tags = extract_tags(t_v)
        if en_tags != t_tags:
            findings.append({
                "key": k,
                "issue": f"html_tag_drift(en={sorted(en_tags)} tgt={sorted(t_tags)})",
                "en": en_v, "tgt": t_v,
            })
            continue
        # EN-token leak in non-Latin
        if lang in NON_LATIN:
            n_en = count_en_tokens(t_v)
            if n_en >= 5:
                findings.append({
                    "key": k,
                    "issue": f"en_token_leak(n={n_en})",
                    "en": en_v, "tgt": t_v,
                })
                continue

    # extra in tgt
    for k in tgt_set - en_set:
        findings.append({"key": k, "issue": "extra_in_target", "en": "", "tgt": tgt[k]})

    return {
        "lang": lang,
        "en_keys": len(en_keys),
        "tgt_keys": len(tgt_keys),
        "findings": findings,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default="", help="comma-separated subset, e.g. zh,ja")
    ap.add_argument("--ratio-low", type=float, default=0.3)
    ap.add_argument("--ratio-high", type=float, default=5.0)
    ap.add_argument("--out-dir", default=str(ROOT / "qa"))
    args = ap.parse_args()

    en = load(I18N / "en.json")
    all_langs = ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"]
    if args.langs:
        wanted = set(s.strip() for s in args.langs.split(",") if s.strip())
        langs = [c for c in all_langs if c in wanted]
    else:
        langs = all_langs

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # per-language CSVs
    for code in langs:
        tgt = load(I18N / f"{code}.json")
        r = audit(en, tgt, code, args.ratio_low, args.ratio_high)
        csv_path = out / f"i18n_audit_{code}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["key", "issue", "en", "tgt"])
            for fnd in r["findings"]:
                w.writerow([fnd["key"], fnd["issue"], fnd["en"], fnd["tgt"]])
        n = len(r["findings"])
        print(f"[{code}] keys={r['tgt_keys']} findings={n}  ->  {csv_path.name}")

    # summary markdown
    md = ["# i18n Static Audit\n", "## Per-language summary\n"]
    md.append("| lang | name | keys | missing | untranslated | too_short | too_long | placeholder | tag | en_leak | empty | extra | total |")
    md.append("|------|------|------|---------|--------------|-----------|----------|-------------|-----|---------|-------|-------|-------|")
    for code in langs:
        tgt = load(I18N / f"{code}.json")
        r = audit(en, tgt, code, args.ratio_low, args.ratio_high)
        by_issue = {}
        for fnd in r["findings"]:
            kind = fnd["issue"].split("(")[0]
            by_issue[kind] = by_issue.get(kind, 0) + 1
        row = [
            code, LANG_NAMES.get(code, code), r["tgt_keys"],
            by_issue.get("missing", 0),
            by_issue.get("untranslated", 0),
            by_issue.get("too_short", 0),
            by_issue.get("too_long", 0),
            by_issue.get("placeholder_drift", 0),
            by_issue.get("html_tag_drift", 0),
            by_issue.get("en_token_leak", 0),
            by_issue.get("empty", 0),
            by_issue.get("extra_in_target", 0),
            len(r["findings"]),
        ]
        md.append("| " + " | ".join(str(x) for x in row) + " |")

    (out / "REPORT_I18N_AUDIT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nWrote {out / 'REPORT_I18N_AUDIT.md'}")


if __name__ == "__main__":
    main()
