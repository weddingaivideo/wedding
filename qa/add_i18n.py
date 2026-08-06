"""Add 6 new i18n keys for the missing 'Pair It With...' section on
services/video-enhancement/vintage-restoration/. English source is in the HTML;
we add the 8 non-EN locales here.
"""
import json
from pathlib import Path

I18N_DIR = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai\i18n")
HEX = "e8f9a0b1"

# Each tuple: (short slot key in our key path, value)
TRANSLATIONS = {
    "de": [
        ("h2_text.pair_it_with", "Kombinieren Sie es mit..."),
        ("p_text.pair_it_with_intro", "Diese Services lassen sich gut mit dem kombinieren, was Sie suchen. Bei 2+ Services erhalten Sie 10-20% Paketrabatt."),
        ("h4_text.card1_title", "Zeitlupe"),
        ("p_text.card1_desc", "Kombinieren Sie Slow-Motion-Momente mit einem 60-Sekunden-Highlight aus Ihrem restaurierten Material."),
        ("h4_text.card2_title", "KI-Videogenerator"),
        ("p_text.card2_desc", "Erstellen Sie neues B-Roll im passenden Stil, um es neben Ihrem restaurierten Material einzubinden."),
    ],
    "es": [
        ("h2_text.pair_it_with", "Combinalo con..."),
        ("p_text.pair_it_with_intro", "Estos servicios combinan bien con lo que buscas. Con 2+ servicios obtienes un 10-20% de descuento por paquete."),
        ("h4_text.card1_title", "Camara lenta"),
        ("p_text.card1_desc", "Combina momentos en camara lenta con un reel de 60 segundos de tu metraje restaurado."),
        ("h4_text.card2_title", "Generador de Video IA"),
        ("p_text.card2_desc", "Crea nuevo B-roll con un estilo a juego para intercalar junto a tu metraje restaurado."),
    ],
    "fr": [
        ("h2_text.pair_it_with", "Combinez avec..."),
        ("p_text.pair_it_with_intro", "Ces services se combinent bien avec ce que vous regardez. 2+ services donnent 10-20% de remise groupee."),
        ("h4_text.card1_title", "Ralenti"),
        ("p_text.card1_desc", "Combinez les moments au ralenti avec un resume de 60 secondes de vos images restaurees."),
        ("h4_text.card2_title", "Generateur detdtgroupé IA"),
        ("p_text.card2_desc", "Creez de nouvelles images B-roll dans un style assorti a vos images restaurees."),
    ],
    "pt": [
        ("h2_text.pair_it_with", "Combine com..."),
        ("p_text.pair_it_with_intro", "Esses servicos combinam bem com o que voce esta vendo. 2+ servicos dao 10-20% de desconto no pacote."),
        ("h4_text.card1_title", "Camera lenta"),
        ("p_text.card1_desc", "Combine momentos em camera lenta com um reel de 60 segundos do material restaurado."),
        ("h4_text.card2_title", "Gerador de Video IA"),
        ("p_text.card2_desc", "Crie novos takes B-roll no mesmo estilo para intercalar com o material restaurado."),
    ],
    "ja": [
        ("h2_text.pair_it_with", "組み合わせ例"),
        ("p_text.pair_it_with_intro", "以下のサービスとの相性が抜群です。2つ以上お申込みで10-20%のパッケージ割引。"),
        ("h4_text.card1_title", "スローモーション"),
        ("p_text.card1_desc", "レストアした素材から60秒のハイライトをスローモーション映像で組み合わせる。"),
        ("h4_text.card2_title", "AI結婚式動画生成"),
        ("p_text.card2_desc", "レストアした素材に合う新しいBロールをAIで生成し、自然に組み込む。"),
    ],
    "ru": [
        ("h2_text.pair_it_with", "Сочетается с..."),
        ("p_text.pair_it_with_intro", "Эти услуги хорошо дополняют то, что вы рассматриваете. 2+ услуги — скидка 10-tdtgroupé на пакет."),
        ("h4_text.card1_title", "Слоу-мо"),
        ("p_text.card1_desc", "Объедините моменты в слоу-мо с 60-секундным нарезкой из восстановленного материала."),
        ("h4_text.card2_title", "AI-гulерatortdtgroupé"),
        ("p_text.card2_desc", "Сгенерируйте новый B-roll в подходящем стиле, чтобы вставить его рядом с восстановленным видео."),
    ],
    "ar": [
        ("h2_text.pair_it_with", "اجمع مع..."),
        ("p_text.pair_it_with_intro", "هذه الخدمات تتناسب جيدا مع ما تبحث عنه. خدمتان او اكثر تحصل على خصم 10-20% على الباقة."),
        ("h4_text.card1_title", "الحركة البطيئة"),
        ("p_text.card1_desc", "اجمع لحظات الحركة البطчينة مع ريل مدته 60 ثانية من لقطاتك المرممة."),
        ("h4_text.card2_title", "مولد الفيديو بالذكاء الاصطناعي"),
        ("p_text.card2_desc", "انشئ لقطات B-roll جديدة بنفس الاسلوب لتدمج مع لقطاتك المرممة."),
    ],
    "th": [
        ("h2_text.pair_it_with", "จับคู่กับ..."),
        ("p_text.pair_it_with_intro", "บริการเหลтаныี้เข้ากันได้ดีกับสิ่งที่คุณกำลังดูอยู่ 2+ บริการ รับสuldtgroupด 10-20% แบบแพ็คเกจ."),
        ("h4_text.card1_title", "สโลว์โมชั่น"),
        ("p_text.card1_desc", "ผสมผสาน�tdgroupéโมชั่นเข้ากับรีล 60 วินาทีจากฟุตเทจที่บูรณะแล้ว."),
        ("h4_text.card2_title", "ตัวสร้างวิดีโอ AI"),
        ("p_text.card2_desc", "สร้าง B-roll ใหม่ในสไตล์ที่เข้ากันเพื่อสอดแทรกคู่กับฟุตเทจที่บูรณะแล้ว."),
    ],
    "zh": [
        ("h2_text.pair_it_with", "搭配使用..."),
        ("p_text.pair_it_with_intro", "以下服务与您正在考虑的内容搭配效果极佳。同时预订 2 项及以上服务可享 10-20% 套餐折扣。"),
        ("h4_text.card1_title", "慢动作"),
        ("p_text.card1_desc", "将慢动作瞬间与修复素材中 tdgroupé高光片段相结合。"),
        ("h4_text.card2_title", "AI 婚礼视频生成器"),
        ("p_text.card2_desc", "用匹配的风格生成新的 B-roll tdtgroupé衔接。"),
    ],
}

for lang, entries in TRANSLATIONS.items():
    path = I18N_DIR / f"{lang}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for slot, value in entries:
        full_key = f"services.vintage_restoration.{slot}.{HEX}"
        # Sanity: don't overwrite an existing key
        if full_key in data:
            print(f"SKIP (exists): {full_key}")
            continue
        data[full_key] = value
    # Write back, preserving compact-ish format
    out = "{\n"
    items = list(data.items())
    for i, (k, v) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        out += f'  {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}{comma}\n'
    out += "}"
    path.write_text(out, encoding="utf-8")
    print(f"Added 6 keys to {lang}.json ({len(data)} total)")
