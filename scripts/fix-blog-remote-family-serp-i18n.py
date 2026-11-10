#!/usr/bin/env python3
"""Add the three page-specific SERP strings to all 11 dictionaries.

The remote-family blog page carries a SERP comparison table whose heading,
intro and closing paragraph were bound to a namespace that exists nowhere
(blog.include_remote_family_wedding_video.serp_comparison.*). They are
repointed at the page's OWN namespace, blog.include-remote-family-wedding-video.
serp_comparison.*, which is the same namespace as the page's other 149 keys
-> same shard file, no new shard, no new manifest entry.

This script writes the 3 values into i18n/<lang>.json for all 11 languages,
inserting them in the file's existing (sorted) key order so the diff is
3 added lines per dictionary and nothing else moves.

Insertion is textual, not a re-serialisation: the dictionaries are 6-17 MB
and a json.dump() round trip would rewrite every line. The file is validated
with json.loads() afterwards, and written atomically (tmp + os.replace) so a
crash cannot leave a half-written dictionary behind.
"""
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NS = "blog.include-remote-family-wedding-video.serp_comparison."

TRANSLATIONS = {
    "en": {
        "h2": "AI Wedding Video Tools for Including Remote Family: 7 Tools vs WeddingAI.video",
        "p_text": (
            "Google SERPs (October 2025) for 'AI wedding video for remote family': "
            "Vidu AI, PicLumen, Pollo AI, RunwayML, Pika Labs, HeyGen. Most are "
            "generic AI video tools built for marketing clips, not for a wedding "
            "film that relatives abroad can watch. WeddingAI.video delivers a "
            "60-90s cinematic wedding film + 11 languages + face preservation:"
        ),
        "p_trailing": (
            "When the audience is family who could not travel, multilingual "
            "delivery and face preservation decide whether the message lands. "
            "WeddingAI.video delivers a 60-90s cinematic film + 11 languages + "
            "face preservation from your photos."
        ),
    },
    "zh": {
        "h2": "为异地家人制作婚礼视频的 AI 工具比较：7 个工具与 WeddingAI.video",
        "p_text": (
            "Google SERP（2025 年 10 月）“异地家人 AI 婚礼视频”：Vidu AI、PicLumen、"
            "Pollo AI、RunwayML、Pika Labs、HeyGen。大多数都是通用的 AI 视频工具，"
            "适合做营销短片，而不是给无法到场的远方亲人观看的婚礼影片。"
            "WeddingAI.video 提供 60-90 秒电影级婚礼影片 + 11 种语言 + 面部保留："
        ),
        "p_trailing": (
            "当观众是未能前来的家人时，多语言播放和面部保留决定了这份心意能否送到。"
            "WeddingAI.video 从你的照片中交付 60-90 秒电影级影片 + 11 种语言 + 面部保留。"
        ),
    },
    "es": {
        "h2": "Herramientas de vídeo de boda con IA para incluir a la familia remota: 7 herramientas frente a WeddingAI.video",
        "p_text": (
            "SERP de Google (octubre de 2025) para el 'vídeo de boda con IA para la "
            "familia remota': Vidu AI, PicLumen, Pollo AI, RunwayML, Pika Labs, HeyGen. "
            "La mayoría son herramientas de vídeo de IA genéricas, pensadas para clips "
            "de marketing y no para una película de boda que pueda ver la familia en el "
            "extranjero. WeddingAI.video ofrece una película cinematográfica de boda de "
            "60-90 segundos + 11 idiomas + preservación de rostros:"
        ),
        "p_trailing": (
            "Cuando el público es la familia que no pudo viajar, la entrega multilingüe "
            "y la preservación de rostros deciden si el mensaje llega. WeddingAI.video "
            "ofrece películas cinematográficas de 60-90 segundos + 11 idiomas + preservación "
            "de rostros a partir de fotografías."
        ),
    },
    "fr": {
        "h2": "Outils vidéo de mariage IA pour inclure la famille à distance : 7 outils vs WeddingAI.video",
        "p_text": (
            "SERPs Google (octobre 2025) pour le « vidéo de mariage IA pour la famille à "
            "distance » : Vidu AI, PicLumen, Pollo AI, RunwayML, Pika Labs, HeyGen. La "
            "plupart sont des outils vidéo d'IA génériques conçus pour des clips marketing, "
            "pas pour un film de mariage que la famille à l'étranger pourra regarder. "
            "WeddingAI.video propose un film cinématographique de mariage de 60-90 secondes "
            "+ 11 langues + préservation du visage :"
        ),
        "p_trailing": (
            "Quand le public est une famille qui n'a pas pu voyager, la diffusion "
            "multilingue et la préservation du visage décident si le message arrive. "
            "WeddingAI.video propose un film cinématographique de 60-90 secondes + 11 "
            "langues + préservation des visages à partir de photos."
        ),
    },
    "de": {
        "h2": "KI-Video-Tools für Hochzeitsvideos mit Remote-Familie: 7 Tools vs. WeddingAI.video",
        "p_text": (
            "Google SERPs (Oktober 2025) für „KI-Hochzeitsvideo für die Remote-Familie“: "
            "Vidu AI, PicLumen, Pollo AI, RunwayML, Pika Labs, HeyGen. Bei den meisten "
            "handelt es sich um generische KI-Videotools für Marketing-Clips, nicht für "
            "einen Hochzeitsfilm, den die Familie im Ausland ansieht. WeddingAI.video "
            "liefert filmische Hochzeitsfilme von 60-90 Sekunden + 11 Sprachen + "
            "Gesichtserhaltung:"
        ),
        "p_trailing": (
            "Wenn das Publikum Familie ist, die nicht reisen konnte, entscheiden "
            "mehrsprachige Auslieferung und Gesichtserhaltung darüber, ob die Botschaft "
            "ankommt. WeddingAI.video liefert Kinofilme von 60-90 Sekunden + 11 Sprachen + "
            "Gesichtserhaltung aus Fotos."
        ),
    },
    "pt": {
        "h2": "Ferramentas de vídeo de casamento com IA para incluir a família remota: 7 ferramentas vs WeddingAI.video",
        "p_text": (
            "SERPs do Google (outubro de 2025) para 'vídeo de casamento com IA para a família "
            "remota': Vidu AI, PicLumen, Pollo AI, RunwayML, Pika Labs, HeyGen. A maioria "
            "são ferramentas genéricas de vídeo de IA, feitas para clipes de marketing e não "
            "para um filme de casamento que a família no exterior possa assistir. "
            "WeddingAI.video oferece filme de casamento cinematográfico de 60-90 segundos + "
            "11 idiomas + preservação de rosto:"
        ),
        "p_trailing": (
            "Quando o público é a família que não pôde viajar, a entrega multilíngue e a "
            "preservação de rosto decidem se a mensagem chega. WeddingAI.video oferece filme "
            "cinematográfico de 60-90 segundos + 11 idiomas + preservação de rosto de fotos."
        ),
    },
    "ja": {
        "h2": "遠隔の家族を招待する AI ウェディング ビデオ ツールの比較: 7 つのツールと WeddingAI.video",
        "p_text": (
            "「遠隔の家族向け AI ウェディング ビデオ」の Google SERP (2025 年 10 月): Vidu AI、"
            "PicLumen、Pollo AI、RunwayML、Pika Labs、HeyGen。そのほとんどは、マーケティング用"
            "クリップ向けの汎用的な AI ビデオ ツールであり、海外の親族が視聴できる結婚式フィルム"
            "向けではありません。WeddingAI.video は、60 ～ 90 秒の映画のような結婚式のフィルム + "
            "11 言語 + 顔の保存を提供します:"
        ),
        "p_trailing": (
            "観客が来られなかった家族であれば、多言語での配信と顔の保存によってメッセージが"
            "届くかどうかが決まります。WeddingAI.video は、写真から 60 ～ 90 秒の映画フィルム + "
            "11 言語 + 顔の保存を配信します。"
        ),
    },
    "ru": {
        "h2": "Инструменты ИИ для свадебного видео с удалёнными родственниками: 7 инструментов против WeddingAI.video",
        "p_text": (
            "Google SERPs (октябрь 2025) по запросу «свадебное видео с ИИ для удалённых "
            "родственников»: Vidu AI, PicLumen, Pollo AI, RunwayML, Pika Labs, HeyGen. "
            "Большинство из них — универсальные ИИ-видеоинструменты для маркетинговых роликов, "
            "а не для свадебного фильма, который посмотрят родственники за границей. "
            "WeddingAI.video предлагает кинематографичный свадебный фильм на 60-90 секунд + "
            "11 языков + сохранение лиц:"
        ),
        "p_trailing": (
            "Когда зрители — родственники, которые не смогли приехать, многоязычная доставка "
            "и сохранение лиц определяют, дойдёт ли сообщение. WeddingAI.video делает "
            "кинематографичный фильм на 60-90 секунд + 11 языков + сохранение лиц из ваших "
            "фотографий."
        ),
    },
    "ar": {
        "h2": "أدوات فيديو زفاف بالذكاء الاصطناعي لإدراج العائلة البعيدة: 7 أدوات مقابل WeddingAI.video",
        "p_text": (
            "Google SERPs (أكتوبر 2025) عن \"فيديو زفاف بالذكاء الاصطناعي للعائلة البعيدة\": "
            "Vidu AI، وPicLumen، وPollo AI، وRunwayML، وPika Labs، وHeyGen. معظمها أدوات فيديو "
            "عامة تعمل بالذكاء الاصطناعي ومصممة لمقاطع التسويق، وليست لفيلم زفاف يمكن لأقارب "
            "في الخارج مشاهدته. يقدم موقع WeddingAI.video فيلم زفاف سينمائي من 60 إلى 90 ثانية + "
            "11 لغة + الحفاظ على الوجه:"
        ),
        "p_trailing": (
            "عندما يكون الجمهور عائلة لم تستطع الحضور، فإن التعدد اللغوي والحفاظ على الوجه "
            "يحددان ما إذا كانت الرسالة تصل. يقدم موقع WeddingAI.video فيلمًا سينمائيًا من 60 "
            "إلى 90 ثانية + 11 لغة + الحفاظ على الوجه من الصور."
        ),
    },
    "th": {
        "h2": "เครื่องมือวิดีโอวานแต่งงาน AI สำหรับให้ญาติทางไกลได้ร่วมงาน: 7 เครื่องมือเทียบกับ WeddingAI.video",
        "p_text": (
            "Google SERPs (ตุลาคม 2025) สำหรับ 'วิดีโอวานแต่งงาน AI สำหรับญาติทางไกล': Vidu AI, "
            "PicLumen, Pollo AI, RunwayML, Pika Labs, HeyGen ส่วนใหญ่เป็นเครื่องมือวิดีโอ AI ทั่วไปที่ทำ"
            "คลิปการตลาด ไม่ใช่ภาพยนตร์งานแต่งงานที่ญาติต่างประเทศจะได้ดู WeddingAI.video นำเสนอภาพยนตร์"
            "งานแต่งงานระดับโรงภาพยนตร์ยาว 60-90 วินาที + 11 ภาษา + การถนอมใบหน้า:"
        ),
        "p_trailing": (
            "เมื่อผู้ชมคือญาติที่ไม่สามารถเดินทางมาร่วมได้ การส่งมอบหลายภาษาและการถนอมใบหน้าจะเป็น"
            "ตัวกำหนดว่าข้อความจะส่งถึงหรือไม่ WeddingAI.video นำเสนอภาพยนตร์ยาว 60-90 วินาที + "
            "11 ภาษา + รักษาใบหน้าจากภาพถ่าย"
        ),
    },
    "hi": {
        "h2": "दूर के परिवार को शामिल करने के लिए एआई वेडिंग वीडियो टूल्स: 7 टूल्स बनाम WeddingAI.video",
        "p_text": (
            "'दूर के परिवार के लिए एआई वेडिंग वीडियो' के लिए Google SERPs (अक्टूबर 2025): विदु एआई, "
            "पिकलुमेन, पोलो एआई, रनवेएमएल, पिका लैब्स, हेजेन। अधिकांश सामान्य एआई वीडियो उपकरण हैं जो "
            "मार्केटिंग क्लिप के लिए बने हैं, विदेश में बैठे परिवार के लिए वेडिंग फिल्म के लिए नहीं। "
            "WeddingAI.video 60-90 सेकंड की सिनेमाई विवाह फिल्म + 11 भाषाएं + चेहरा संरक्षण प्रदान करता है:"
        ),
        "p_trailing": (
            "जब दर्शक वे परिवार हैं जो यात्रा नहीं कर सके, तो बहुभाषी वितरण और चेहरा संरक्षण तय करते हैं कि "
            "संदेश पहुँचेगा या नहीं। WeddingAI.video आपकी तस्वीरों से 60-90 सेकंड की सिनेमाई फिल्म + 11 "
            "भाषाएं + चेहरे का संरक्षण प्रदान करता है।"
        ),
    },
}

KEY_RE = re.compile(r'^\s*"([^"]+)":')


def insert_keys(path: Path, new_items: list[tuple[str, str]]) -> int:
    raw = path.read_text(encoding="utf-8")
    lines = raw.split("\n")
    added = 0
    for key, value in new_items:
        if f'"{key}"' in raw:
            continue
        # Find the first line whose key sorts after ours.
        insert_at = None
        for i, line in enumerate(lines):
            m = KEY_RE.match(line)
            if m and m.group(1) > key:
                insert_at = i
                break
        if insert_at is None:
            raise RuntimeError(f"{path.name}: no insertion point for {key}")
        encoded = json.dumps(value, ensure_ascii=False)
        lines.insert(insert_at, f'  {json.dumps(key, ensure_ascii=False)}: {encoded},')
        added += 1
    if added == 0:
        return 0
    out = "\n".join(lines)
    data = json.loads(out)  # validate
    for key, value in new_items:
        if data.get(key) != value:
            raise RuntimeError(f"{path.name}: {key} did not round-trip")
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(out, encoding="utf-8", newline="")
    os.replace(str(tmp), str(path))
    return added


def main() -> int:
    total = 0
    for lang, values in TRANSLATIONS.items():
        path = REPO / "i18n" / f"{lang}.json"
        items = [(NS + k, v) for k, v in values.items()]
        added = insert_keys(path, items)
        total += added
        data = json.loads(path.read_text(encoding="utf-8"))
        print(f"  {lang}.json: +{added} key(s), {len(data)} keys total")
    print(f"\nTotal: {total} keys added across {len(TRANSLATIONS)} dictionaries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
