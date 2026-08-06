"""Update i18n JSON values for P3 SEO improvements.
Updates H1, Title, Meta description, and Hero trust across all 10 languages.

Strategy: preserve existing translations where they're good, only update
fields that need adjustment per the audit:
- H1: include "AI" + "wedding video" keywords (most langs already have AI; add "wedding video")
- Title: align with H1 (most langs already good)
- Meta description: add data points (500+ couples, $49-$499, 48h)
- Hero trust: rephrase to balance 500+ claim with 4.9/5 from 6 reviews
"""
import json
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")

# i18n keys
KEY_H1 = "index.h1_text.make_every_wedding_moment_unforgettable.26538929"
KEY_TITLE = "index.title_text.ai_powered_wedding_video_services_weddin.58583865"
KEY_META_DESC = "index.meta_description.ai_powered_wedding_videos_ai_films_multi.40129620"
KEY_HERO_TRUST = "index.p_text.trusted_by_500_couples_in_the_us_europe.32124339"

# New values per language. Designed to:
#  - Include "AI" + "wedding video" keywords naturally
#  - Meta desc: 150-200 chars with data points
#  - Hero trust: rephrase to balance 500+ with 4.9/5 + 48h
UPDATES = {
    "en": {
        KEY_H1: "AI Wedding Videos — Make Every Moment Unforgettable",
        KEY_TITLE: "AI Wedding Video Services | WeddingAI.video",
        KEY_META_DESC: "AI wedding video services trusted by 500+ couples in the US & Europe. AI films, multilingual dubbing, restoration, slow-mo, and more. From $49, 48h turnaround. Get your free quote →",
        KEY_HERO_TRUST: "Trusted by 500+ couples · 4.9/5 from 6 verified reviews · 48h turnaround",
    },
    "zh": {
        KEY_H1: "AI 婚礼视频 — 让每一刻都令人难忘",
        KEY_TITLE: "AI 婚礼视频服务 | WeddingAI.video",
        KEY_META_DESC: "受到美欧 500+ 对夫妇信赖的 AI 婚礼视频服务。AI 电影、多语言配音、修复、慢动作等 10+ 项服务。起价 $49，48 小时交付。免费报价 →",
        KEY_HERO_TRUST: "500+ 对夫妇信赖 · 4.9/5 评分（6 条真实评价）· 48 小时交付",
    },
    "es": {
        KEY_H1: "Videos de Boda con IA — Haz Que Cada Momento Sea Inolvidable",
        KEY_TITLE: "Servicios de Video de Boda con IA | WeddingAI.video",
        KEY_META_DESC: "Servicios de video de boda con IA en los que confían más de 500 parejas en EE. UU. y Europa. Películas con IA, doblaje multilingüe, restauración, cámara lenta y más. Desde $49, entrega en 48 h. Cotización gratis →",
        KEY_HERO_TRUST: "Confianza de más de 500 parejas · 4.9/5 de 6 reseñas verificadas · Entrega en 48 h",
    },
    "fr": {
        KEY_H1: "Vidéos de Mariage IA — Rendez Chaque Moment Inoubliable",
        KEY_TITLE: "Services de Vidéo de Mariage IA | WeddingAI.video",
        KEY_META_DESC: "Services de vidéo de mariage IA approuvés par plus de 500 couples aux États-Unis et en Europe. Films IA, doublage multilingue, restauration, ralenti et plus encore. À partir de 49 $, livraison en 48 h. Devis gratuit →",
        KEY_HERO_TRUST: "Approuvé par plus de 500 couples · 4.9/5 sur 6 avis vérifiés · Livraison en 48 h",
    },
    "de": {
        KEY_H1: "KI-Hochzeitsvideos — Machen Sie Jeden Moment Unvergesslich",
        KEY_TITLE: "KI-Hochzeitsvideo-Dienste | WeddingAI.video",
        KEY_META_DESC: "KI-Hochzeitsvideo-Dienste, denen mehr als 500 Paare in den USA und Europa vertrauen. KI-Filme, mehrsprachige Synchronisation, Restaurierung, Zeitlupe und mehr. Ab 49 $, 48-h-Lieferung. Kostenloses Angebot →",
        KEY_HERO_TRUST: "Vertrauen von mehr als 500 Paaren · 4,9/5 aus 6 verifizierten Bewertungen · 48-h-Lieferung",
    },
    "pt": {
        KEY_H1: "Vídeos de Casamento com IA — Torne Cada Momente Inesquecível",
        KEY_TITLE: "Serviços de Vídeo de Casamento com IA | WeddingAI.video",
        KEY_META_DESC: "Serviços de vídeo de casamento com IA, confiáveis para mais de 500 casais nos EUA e Europa. Filmes com IA, dublagem multilíngue, restauração, câmera lenta e muito mais. A partir de US$ 49, entrega em 48 h. Orçamento grátis →",
        KEY_HERO_TRUST: "Confiança de mais de 500 casais · 4,9/5 de 6 avaliações verificadas · Entrega em 48 h",
    },
    "ja": {
        KEY_H1: "AI ウェディングビデオ — すべての瞬間を忘れられないものに",
        KEY_TITLE: "AI ウェディングビデオサービス | WeddingAI.video",
        KEY_META_DESC: "米欧 500 組以上のカップルに信頼される AI ウェディングビデオサービス。AI フィルム、多言語吹き替え、修復、スローモーションなど 10 種類以上。$49 から、48 時間納品。無料見積もり →",
        KEY_HERO_TRUST: "500 組以上のカップルが信頼 · 4.9/5（6 件の検証済みレビュー）· 48 時間納品",
    },
    "ru": {
        KEY_H1: "ИИ Свадебные Видео — Сделайте Каждый Момент Незабываемым",
        KEY_TITLE: "Сервис Свадебного Видео на ИИ | WeddingAI.video",
        KEY_META_DESC: "Сервис свадебного видео на ИИ, которому доверяют более 500 пар в США и Европе. ИИ-фильмы, многоязычный дубляж, реставрация, замедленная съёмка и многое другое. От $49, готовность за 48 ч. Бесплатный расчёт →",
        KEY_HERO_TRUST: "Более 500 пар доверяют · 4,9/5 на основе 6 проверенных отзывов · Готовность за 48 ч",
    },
    "ar": {
        KEY_H1: "فيديوهات زفاف بالذكاء الاصطناعي — اجعل كل لحظة لا تُنسى",
        KEY_TITLE: "خدمات فيديو الزفاف بالذكاء الاصطناعي | WeddingAI.video",
        KEY_META_DESC: "خدمات فيديو الزفاف بالذكاء الاصطناعي التي يثق بها أكثر من 500 زوج في الولايات المتحدة وأوروبا. أفلام بالذكاء الاصطناعي، دبلجة بلغات متعددة، ترميم، حركة بطيئة والمزيد. تبدأ من 49 دولارًا، التسليم خلال 48 ساعة. عرض سعر مجاني ←",
        KEY_HERO_TRUST: "يثق بها أكثر من 500 زوج · 4.9/5 من 6 تقييمات موثقة · التسليم خلال 48 ساعة",
    },
    "th": {
        KEY_H1: "วิดีโอแต่งงานด้วย AI — ทำให้ทุกช่วงเวลาน่าจดจำ",
        KEY_TITLE: "บริการวิดีโอแต่งงานด้วย AI | WeddingAI.video",
        KEY_META_DESC: "บริการวิดีโอแต่งงานด้วย AI ที่คู่รักกว่า 500 คู่ในสหรัฐฯ และยุโรปไว้วางใจ หนัง AI พากย์หลายภาษา บูรณะฟิล์มเก่า สโลว์โมชัน และอื่นๆ อีกมาก เริ่มต้น $49 ส่งงานภายใน 48 ชม. ขอใบเสนอราคาฟรี →",
        KEY_HERO_TRUST: "คู่รักกว่า 500 คู่ไว้วางใจ · 4.9/5 จาก 6 รีวิวที่ยืนยันแล้ว · ส่งงานภายใน 48 ชม.",
    },
}

print("=== Updating i18n JSON files ===")
for lang, updates in UPDATES.items():
    path = ROOT / "i18n" / f"{lang}.json"
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    before = {k: d.get(k) for k in updates.keys()}
    for k, v in updates.items():
        d[k] = v
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    print(f"\n  [{lang}] {path.name}:")
    for k in updates.keys():
        old = before[k]
        new = updates[k]
        old_short = (old or "(MISSING)")[:60]
        new_short = new[:60]
        marker = "=" if old == new else ("+" if not old else "~")
        print(f"    {marker} {k[:40]}...")
        print(f"      - {old_short}{'...' if old and len(old) > 60 else ''}")
        print(f"      + {new_short}{'...' if len(new) > 60 else ''}")

print("\n=== Done. Validating ===")
import re
# Check all JSONs are valid
for lang in UPDATES.keys():
    path = ROOT / "i18n" / f"{lang}.json"
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        # Check all 4 keys exist
        missing = [k for k in UPDATES[lang].keys() if k not in d]
        if missing:
            print(f"  ❌ {lang}: missing keys: {missing}")
        else:
            # Check meta desc length
            md_len = len(d[KEY_META_DESC])
            print(f"  ✅ {lang}: meta desc length = {md_len}")
    except Exception as e:
        print(f"  ❌ {lang}: parse error: {e}")
