"""
Round 2: clean up everything round 1 missed.

Round 1 deleted i18n keys whose literal name contained "celebrity" and HTML
blocks whose body contained the literal string. Round 2 catches the long tail:

  - i18n keys whose translated value contains /services/absence-compensation/celebrity-message/
    (these are markdown-link translations; the slug part of the key uses the
     *target language's* word for "celebrity", e.g. German "promi", French
     "clbrit", Spanish "celebridades", Portuguese "celebridade", Thai keeps
     the English "celebrity")
  - i18n keys whose key name ends with `celebr` (catches celebri, celebridade,
    celebridad, etc.) but whose root slug is otherwise innocuous — verified
    safe because every "celebr*"-suffix key in the corpus is a celebrity-message
    artifact
  - The pt/blog/weddingai-video-guide/ line 274-275 residual that survived
    round 1 (its key name didn't contain "celebrity"; only the value did)
  - generate-service-category-indexes.py footer template line 457 (round 1
    only touched NAV_ITEMS + the absence-compensation group child, not the
    hardcoded footer block used by all 4 generated group indexes)
  - The 7 extra orphan keys in i18n/en.json whose value mentions "celebrity"
    but whose key name is innocuous

Safe to re-run (idempotent).
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
PRESERVE_KEYS = {
    "services.absence-compensation.celebrity-message.a_text.home.90820803",
}

# i18n key names that are clearly celebrity-message artifacts (translated slug
# in the key name). Verified manually across all 10 language files.
ORPHAN_KEY_PATTERNS = [
    re.compile(r"\.celebr[a-z_]*services?absence_compensation[_.]?celebr", re.IGNORECASE),
    re.compile(r"\.clbrit", re.IGNORECASE),
    re.compile(r"\.promi", re.IGNORECASE),
    re.compile(r"\.celebridadess?services", re.IGNORECASE),
    re.compile(r"\.celebridadeservices", re.IGNORECASE),
    re.compile(r"\.celebridadeserv", re.IGNORECASE),
    re.compile(r"\.celebridadeservice", re.IGNORECASE),
    re.compile(r"\.mensagem_de_celebridadeservices", re.IGNORECASE),
    re.compile(r"\.mensagens_de_celebridadesservices", re.IGNORECASE),
    re.compile(r"\.messagedeclbritservices", re.IGNORECASE),
    re.compile(r"\.messagesdeclbritsservices", re.IGNORECASE),
    re.compile(r"\.mensaes_de_celebridadesservices", re.IGNORECASE),
    re.compile(r"\.mensajesdecelebridadesservices", re.IGNORECASE),
    re.compile(r"\.mensajedecelebridadservices", re.IGNORECASE),
    re.compile(r"\.celebrityservicesabsence", re.IGNORECASE),
    re.compile(r"\.celebrity_message\.html", re.IGNORECASE),
    # Markdown-link-style keys that combine the slug with the URL path
    re.compile(r"\.httpsweddingaivideoservicesabsence_compensationcel", re.IGNORECASE),
    re.compile(r"\.un_mensaje_personalizado_de_una_celebridadservices", re.IGNORECASE),
    re.compile(r"\.message_de_clbritservicesabsence_compensationceleb", re.IGNORECASE),
    re.compile(r"\.messages_de_clbritsservicesabsence_compensationcel", re.IGNORECASE),
    re.compile(r"\.o_servio_de_mensagem_de_celebridadeservicesabsence", re.IGNORECASE),
    re.compile(r"\.para_o_casamento_letcia_quis_surpreender_marcos_co", re.IGNORECASE),
    re.compile(r"\.integraes_de_mensagens_de_celebridades_para_um_toq", re.IGNORECASE),
    re.compile(r"\.ideal_para_criar_mensagens_de_familiares_dista", re.IGNORECASE),
    re.compile(r"\.se_algum_importante_no_pde_comparecer_considere_in", re.IGNORECASE),
    re.compile(r"\.a_ia_pode_criar_uma_mensagem_personalizada_de_cele", re.IGNORECASE),
    re.compile(r"\.uma_mensagem_de_algum_que_o_casal_no_esperava_um_a", re.IGNORECASE),
    re.compile(r"\.fr_den_meme_generatorservicespersonalizationme", re.IGNORECASE),
    re.compile(r"\.a_tendncia_no_substituir_o_videgrafo_humano_mas_si", re.IGNORECASE),
    re.compile(r"\.et_pour_une_surprise_vritablement_inoubliable_notr", re.IGNORECASE),
    re.compile(r"\.pourquoi_cest_gnial_la_surprise_ultime_imaginez_la", re.IGNORECASE),
    re.compile(r"\.family_tributeservicesabsence_compensationfamily_t", re.IGNORECASE),
]

# Specific value-level orphan key names (value contains "/services/absence-
# compensation/celebrity-message/" or "Celebrity/Influencer Message" etc.).
# These are all blog/inline-mention keys whose value referenced the deleted
# service. We delete by exact key name to be safe.
ORPHAN_KEY_NAMES_BY_VALUE = {
    "en.json": [
        "blog.wedding-video-cost-2026.li_text.use_weddingai_video_for_unique_add_ons_c.50939596",
        "blog.wedding-video-cost-2026.p_text.service_price_range_what_s_included_ai.12151409",
        "gallery.p_text.couple_wanted_a_hollywood_style_wedding.62985265",
        "index.p_text.ai_archetype_wedding_message.22222223",
        "index.p_text.ai_safety_answer.99999992",
        "pricing.td_text.reception_opener_surprise_moment.99b02f6e",
        "blog.family-tribute-video-wedding.p_text.combine_your_family_tributeservicesabsence_compens.2b77cd31",
        "blog.wedding-video-trends-2026.p_text.and_for_a_truly_unforgettable_surprise_our_celebri.4574633e",
        "blog.wedding-video-types-guide.p_text.best_for_entertainment_surprise_moments_our_celebr.61c0ac1b",
        "blog.wedding-wishes-video.p_text.when_parents_cant_attend_the_wishes_video_serves_a.87b41f10",
        "blog.weddingai-video-guide.p_text.add_a_fun_surprising_element_to_your_video_with_ai.a86ad4ab",
        "blog.why-wedding-video-important.p_text.for_couples_dealing_with_significant_absences_our_.f5f77704",
    ],
}


def is_orphan(key: str, value: str) -> bool:
    if key in PRESERVE_KEYS:
        return False
    if "/services/absence-compensation/celebrity-message" in value:
        return True
    for rx in ORPHAN_KEY_PATTERNS:
        if rx.search(key):
            return True
    return False


def rewrite_i18n(path: Path) -> int:
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    by_name = set(ORPHAN_KEY_NAMES_BY_VALUE.get(path.name, []))
    to_delete = []
    for k, v in data.items():
        if k in PRESERVE_KEYS:
            continue
        if k in by_name:
            to_delete.append(k)
            continue
        if is_orphan(k, str(v)):
            to_delete.append(k)
    if not to_delete:
        return 0
    ordered = [(k, v) for k, v in json.loads(raw, object_pairs_hook=list) if k not in set(to_delete)]
    path.write_text(
        json.dumps(dict(ordered), ensure_ascii=False, indent=2, separators=(",", ": ")) + "\n",
        encoding="utf-8",
    )
    return len(to_delete)


# ---------------------------------------------------------------------------
# generate-service-category-indexes.py footer template — line 457 hardcoded
# celebrity <li> still inside the f-string the generator emits into every
# /services/<group>/index.html footer.
# ---------------------------------------------------------------------------

GEN_CAT_FOOTER_LI = re.compile(
    r'^[ \t]*<li><a href="/services/absence-compensation/celebrity-message/"[^>]*>[^<]*</a></li>[ \t]*\r?\n',
    re.MULTILINE,
)


def rewrite_gen_cat_footer(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    new = GEN_CAT_FOOTER_LI.sub("", text)
    if new != text:
        path.write_text(new, encoding="utf-8")
        return 1
    return 0


# ---------------------------------------------------------------------------
# pt/blog/weddingai-video-guide/index.html — round 1 missed the two <p> lines
# (their key names were slug-only, no "celebrity" string). We delete them by
# data-i18n attribute to be precise.
# ---------------------------------------------------------------------------

PT_WEDDINGAI_VIDEO_GUIDE_LINES = re.compile(
    r'^[ \t]*<p[^>]*data-i18n="blog\.weddingai-video-guide\.p_text\.mensagem_de_celebridade\.[a-f0-9]+">[^<]*</p>[ \t]*\r?\n'
    r'^[ \t]*<p[^>]*data-i18n="blog\.weddingai-video-guide\.p_text\.o_servio_de_mensagem_de_celebridadeservicesabsence\.[a-f0-9]+">[^<]*<a href="/services/absence-compensation/celebrity-message/">[^<]*</a>[^<]*</p>[ \t]*\r?\n',
    re.MULTILINE,
)


def rewrite_pt_blog(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    new = PT_WEDDINGAI_VIDEO_GUIDE_LINES.sub("", text)
    if new != text:
        path.write_text(new, encoding="utf-8")
        return 1
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=== i18n JSON files (round 2) ===")
    i18n_total = 0
    for p in sorted(ROOT.glob("i18n/*.json")):
        n = rewrite_i18n(p)
        if n:
            i18n_total += n
            print(f"  [{n:>3} keys] {p.relative_to(ROOT)}")
    print(f"  -> {i18n_total} extra orphan keys removed (Home key still preserved)\n")

    print("=== generate-service-category-indexes.py footer template ===")
    if rewrite_gen_cat_footer(ROOT / "scripts/generate-service-category-indexes.py"):
        print(f"  [1] scripts/generate-service-category-indexes.py\n")
    else:
        print("  (no change)\n")

    print("=== pt/blog/weddingai-video-guide/ residual ===")
    if rewrite_pt_blog(ROOT / "pt/blog/weddingai-video-guide/index.html"):
        print(f"  [1] pt/blog/weddingai-video-guide/index.html\n")
    else:
        print("  (no change)\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
