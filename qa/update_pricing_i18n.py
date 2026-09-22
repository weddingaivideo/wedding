#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update three pricing/positioning keys in all 11 i18n JSON files.
Goal: unify on "Starting at $9.9" across all languages.

Keys:
  - index.meta_description.ai_powered_wedding_videos_ai_films_multi.40129620
  - about.p_text.founder_story_para3.88a1b2c3
  - pricing.p_text.every_project_is_different_a_5minute_vhs.688d1fd6

Each language has its own line-based JSON. We do line-level text replacement
(don't reparse the whole 9-16MB file) and only touch the lines that match.
"""

import os
import sys

I18N_DIR = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai\i18n"

# For each language, a dict of {i18n_key: new_value}
# Use straight $9.9 across all languages to keep the price anchor consistent
# (locale-specific decimal separators are NOT used here on purpose — this is
# a USD price the brand wants to look identical everywhere).
TRANSLATIONS = {
    "zh": {
        "index.meta_description.ai_powered_wedding_videos_ai_films_multi.40129620":
            "受到美欧 500+ 对夫妇信赖的 AI 婚礼视频服务。AI 电影、多语言配音、修复、慢动作等 10+ 项服务。起价 $9.9，48 小时交付。免费报价 →",
        "about.p_text.founder_story_para3.88a1b2c3":
            "2024 年，我与 Maria（调色师，在旧金山一家婚礼工作室工作了 8 年）和 James Park 博士（计算机视觉研究员，一直在悄悄微调档案镜头的运动模型）合作。索菲亚 (Sofia) 作为客户体验 &mdash; 加入，她曾负责策划婚礼，并且了解情侣的实际需求。我们创办了 WeddingAI.video，旨在以 9.9 美元起（而不是 1,500 美元以上）的价格提供这种经过人工审核的仔细修复。",
        "pricing.p_text.every_project_is_different_a_5minute_vhs.688d1fd6":
            "每个项目都是不同的。5 分钟的 VHS 录像带和 3 小时的 4K 婚礼影片不是同一部作品。我们根据素材长度、复杂性和周转时间进行报价。9.9 美元起价是每项服务的入门点；最终报价反映您项目的实际范围。",
    },
    "ar": {
        "index.meta_description.ai_powered_wedding_videos_ai_films_multi.40129620":
            "خدمات فيديو زفاف AI يثق بها 500+ زوج في الولايات المتحدة وأوروبا. أفلام، دبلجة، ترميم، حركة بطيئة. ابتداءً من 9.9$، 48 ساعة. عرض سعر مجاني ←",
        "about.p_text.founder_story_para3.88a1b2c3":
            "في عام 2024، تعاونت مع ماريا (مصممة ألوان، قضت 8 سنوات في استوديو حفلات الزفاف في سان فرانسيسكو) والدكتور جيمس بارك (باحث في الرؤية الحاسوبية كان يعمل بهدوء على ضبط النماذج المتحركة للقطات أرشيفية). انضمت صوفيا كخبرة عميل &mdash; وكانت تخطط لحفلات الزفاف وتعرف ما يحتاجه الأزواج بالفعل. لقد بدأنا موقع WeddingAI.video لجعل هذا النوع من الترميم الدقيق والمراجع من قبل الإنسان متاحًا ابتداءً من 9.9 دولار أمريكي بدلاً من 1500 دولار أمريكي أو أكثر.",
        "pricing.p_text.every_project_is_different_a_5minute_vhs.688d1fd6":
            "كل مشروع مختلف. إن شريط VHS مدته 5 دقائق وفيلم زفاف 4K مدته 3 ساعات ليسا نفس العمل. نحن نقتبس بناءً على طول اللقطات وتعقيدها وتحولها. سعر البدء 9.9$ هو نقطة الدخول لكل خدمة؛ يعكس العرض النهائي نطاق مشروعك الفعلي.",
    },
    "de": {
        "index.meta_description.ai_powered_wedding_videos_ai_films_multi.40129620":
            "KI-Hochzeitsvideo-Dienste, denen 500+ Paare in den USA und Europa vertrauen. KI-Filme, Synchronisation, Restaurierung. Ab 9,9 $, 48 h. Kostenloses Angebot →",
        "about.p_text.founder_story_para3.88a1b2c3":
            "Im Jahr 2024 tat ich mich mit Maria (Koloristin, 8 Jahre in einem Hochzeitsstudio in San Francisco) und Dr. James Park (Computer-Vision-Forscher, der im Stillen Bewegungsmodelle für Archivmaterial verfeinerte) zusammen. Sofia kam als Kundenerfahrung hinzu &mdash; Sie hat früher Hochzeiten geplant und weiß, was Paare tatsächlich brauchen. Wir haben WeddingAI.video ins Leben gerufen, um diese Art der sorgfältigen, von Menschen überprüften Restaurierung bereits ab 9,9 $ statt über 1.500 $ zugänglich zu machen.",
        "pricing.p_text.every_project_is_different_a_5minute_vhs.688d1fd6":
            "Jedes Projekt ist anders. Eine 5-minütige VHS-Kassette und ein 3-stündiger 4K-Hochzeitsfilm sind nicht dasselbe Werk. Wir bieten Angebote basierend auf der Länge, Komplexität und Bearbeitungszeit des Filmmaterials an. Der Einstiegspreis von 9,9 $ ist der Ausgangspunkt für jede Dienstleistung; das endgültige Angebot spiegelt den tatsächlichen Umfang Ihres Projekts wider.",
    },
    "es": {
        "index.meta_description.ai_powered_wedding_videos_ai_films_multi.40129620":
            "Vídeo de boda con IA para 500+ parejas. Películas, doblaje, restauración, cámara lenta. Desde $9.9, 48 h. Cotización gratis →",
        "about.p_text.founder_story_para3.88a1b2c3":
            "En 2024, me asocié con María (colorista, 8 años en un estudio de bodas en San Francisco) y el Dr. James Park (investigador de visión por computadora que había estado ajustando silenciosamente modelos de movimiento para imágenes de archivo). Sofía se unió como Client Experience &mdash;, solía planificar bodas y sabe lo que las parejas realmente necesitan. Comenzamos WeddingAI.video para hacer accesible este tipo de restauración cuidadosa y revisada por humanos a partir de $9.9 en lugar de $1,500+.",
        "pricing.p_text.every_project_is_different_a_5minute_vhs.688d1fd6":
            "Cada proyecto es diferente. Una cinta VHS de 5 minutos y una película de boda en 4K de 3 horas no son el mismo trabajo. Cotizamos en función de la duración, la complejidad y el tiempo de entrega del metraje. El precio de partida de $9.9 es el punto de entrada para cada servicio; la cotización final refleja el alcance real de tu proyecto.",
    },
    "fr": {
        "index.meta_description.ai_powered_wedding_videos_ai_films_multi.40129620":
            "Services vidéo de mariage IA approuvés par 500+ couples aux USA et en Europe. Films IA, doublage, restauration, ralenti. Dès 9,9 $, 48 h. Devis gratuit →",
        "about.p_text.founder_story_para3.88a1b2c3":
            "En 2024, j'ai fait équipe avec Maria (coloriste, 8 ans dans un studio de mariage à San Francisco) et le Dr James Park (chercheur en vision par ordinateur qui peaufinait discrètement les modèles de mouvement pour les images d'archives). Sofia a rejoint l'équipe en tant qu'Expérience Client &mdash;. Elle planifiait les mariages et sait ce dont les couples ont réellement besoin. Nous avons lancé WeddingAI.video pour rendre ce type de restauration minutieuse et vérifiée par des humains accessible à partir de 9,9 $ au lieu de 1 500$+.",
        "pricing.p_text.every_project_is_different_a_5minute_vhs.688d1fd6":
            "Chaque projet est différent. Une cassette VHS de 5 minutes et un film de mariage 4K de 3 heures ne sont pas la même œuvre. Nous citons en fonction de la longueur des images, de la complexité et du délai d'exécution. Le prix de départ de 9,9 $ est le point d'entrée de chaque service ; le devis final reflète la portée réelle de votre projet.",
    },
    "hi": {
        "index.meta_description.ai_powered_wedding_videos_ai_films_multi.40129620":
            "एआई विवाह वीडियो सेवाओं पर अमेरिका और यूरोप में 500 से अधिक जोड़े भरोसा करते हैं। फ़िल्में, डबिंग, रेस्टोरेशन, स्लो-मो। $9.9 से शुरू, 48 घंटे। निःशुल्क उद्धरण →",
        "about.p_text.founder_story_para3.88a1b2c3":
            "2024 में मैंने मारिया (रंगकर्मी, सैन फ्रांसिस्को में एक वेडिंग स्टूडियो में 8 साल तक काम किया) और डॉ. जेम्स पार्क (कंप्यूटर विज़न शोधकर्ता जो अभिलेखीय फुटेज के लिए गति मॉडल को चुपचाप ठीक कर रहे थे) के साथ मिलकर काम किया। सोफिया क्लाइंट एक्सपीरियंस &mdash; के रूप में शामिल हुई, वह शादियों की योजना बनाती थी और जानती थी कि जोड़ों को वास्तव में क्या चाहिए। हमने इस तरह की सावधानीपूर्वक, मानव-समीक्षित बहाली को $1,500+ के बजाय $9.9 से शुरू करके सुलभ बनाने के लिए वेडिंगएआई.वीडियो शुरू किया।",
        "pricing.p_text.every_project_is_different_a_5minute_vhs.688d1fd6":
            "हर प्रोजेक्ट अलग है. 5 मिनट का वीएचएस टेप और 3 घंटे की 4K वेडिंग फिल्म एक ही काम नहीं हैं। हम फ़ुटेज की लंबाई, जटिलता और टर्नअराउंड के आधार पर उद्धरण देते हैं। $9.9 शुरुआती कीमत हर सेवा का प्रवेश बिंदु है; अंतिम उद्धरण आपके प्रोजेक्ट के वास्तविक दायरे को दर्शाता है।",
    },
    "ja": {
        "index.meta_description.ai_powered_wedding_videos_ai_films_multi.40129620":
            "米国・欧州の500組以上のカップルに信頼されるAI結婚式動画サービス。AI映画、多言語吹き替え、修復、スローモーションなど10以上のサービス。$9.9〜、48時間対応。無料見積もり →",
        "about.p_text.founder_story_para3.88a1b2c3":
            "2024 年、私はマリア (カラリスト、サンフランシスコのウェディング スタジオで 8 年間勤務) とジェームス パーク博士 (アーカイブ映像のモーション モデルを密かに微調整していたコンピューター ビジョン研究者) とチームを組みました。ソフィアはクライアント エクスペリエンス &mdash; として参加しました。以前は結婚式の計画を立てていたため、カップルが実際に必要なものを知っています。私たちは、このような慎重で人間によるレビューを経た修復を $1,500+ ではなく $9.9〜 で利用できるようにするために WeddingAI.video を始めました。",
        "pricing.p_text.every_project_is_different_a_5minute_vhs.688d1fd6":
            "すべてのプロジェクトは異なります。 5 分の VHS テープと 3 時間の 4K ウェディング フィルムは同じ作品ではありません。映像の長さ、複雑さ、納期に基づいて見積もりを作成します。$9.9 の開始価格は各サービスのエントリーポイントです。最終的な見積もりはプロジェクトの実際の範囲を反映します。",
    },
    "pt": {
        "index.meta_description.ai_powered_wedding_videos_ai_films_multi.40129620":
            "Serviços de vídeo de casamento com IA para 500+ casais nos EUA e Europa. Filmes, dublagem, restauração. A partir de $9.9, 48 h. Orçamento grátis →",
        "about.p_text.founder_story_para3.88a1b2c3":
            "Em 2024, me juntei a Maria (colorista, 8 anos em um estúdio de casamento em São Francisco) e ao Dr. James Park (pesquisador de visão computacional que vinha ajustando silenciosamente modelos de movimento para imagens de arquivo). Sofia ingressou como Client Experience &mdash; ela planejava casamentos e sabe o que os casais realmente precisam. Começamos WeddingAI.video para tornar esse tipo de restauração cuidadosa e revisada por humanos acessível a partir de US$ 9.9 em vez de US$ 1.500+.",
        "pricing.p_text.every_project_is_different_a_5minute_vhs.688d1fd6":
            "Cada projeto é diferente. Uma fita VHS de 5 minutos e um filme de casamento 4K de 3 horas não são o mesmo trabalho. Orçamos com base na duração, complexidade e tempo de execução da filmagem. O preço inicial de $9.9 é o ponto de entrada para cada serviço; o orçamento final reflete o escopo real do seu projeto.",
    },
    "ru": {
        "index.meta_description.ai_powered_wedding_videos_ai_films_multi.40129620":
            "Сервис свадебного видео на AI, которому доверяют 500+ пар в США и Европе. Фильмы, дубляж, реставрация. От $9.9, 48 ч. Бесплатный расчёт →",
        "about.p_text.founder_story_para3.88a1b2c3":
            "В 2024 году я объединился с Марией (колорист, 8 лет в свадебной студии в Сан-Франциско) и доктором Джеймсом Парком (исследователь компьютерного зрения, который незаметно настраивал модели движения для архивных кадров). София присоединилась к нам в качестве клиента &mdash;. Раньше она планировала свадьбы и знает, что на самом деле нужно парам. Мы запустили WeddingAI.video, чтобы сделать такую тщательную реставрацию, проверенную людьми, доступной от $9.9 вместо $1500+.",
        "pricing.p_text.every_project_is_different_a_5minute_vhs.688d1fd6":
            "Каждый проект уникален. 5-минутная видеокассета и 3-часовой свадебный фильм в 4К — это не одно и то же. Мы оцениваем длину, сложность и сроки выполнения отснятого материала. Начальная цена $9.9 — это отправная точка для каждой услуги; окончательная оценка отражает фактический объём вашего проекта.",
    },
    "th": {
        "index.meta_description.ai_powered_wedding_videos_ai_films_multi.40129620":
            "บริการวิดีโอแต่งงานด้วย AI ที่คู่รัก 500+ คู่ในสหรัฐฯ และยุโรปไว้วางใจ หนัง AI พากย์หลายภาษา บูรณะ สโลว์โมชัน เริ่มต้นที่ $9.9, 48 ชม. →",
        "about.p_text.founder_story_para3.88a1b2c3":
            "ในปี 2024 ฉันร่วมมือกับ Maria (นักวาดภาพสี 8 ปีที่สตูดิโอจัดงานแต่งงานในซานฟรานซิสโก) และ Dr. James Park (นักวิจัยด้านคอมพิวเตอร์วิทัศน์ซึ่งปรับแต่งโมเดลการเคลื่อนไหวอย่างเงียบๆ สำหรับฟุตเทจที่เก็บถาวร) โซเฟียเข้าร่วมในฐานะประสบการณ์ลูกค้า &mdash; เธอเคยวางแผนงานแต่งงานและรู้ว่าคู่รักต้องการอะไรจริงๆ เราเริ่มต้น WeddingAI.video เพื่อให้การบูรณะอย่างรอบคอบและได้รับการตรวจสอบโดยมนุษย์สามารถเข้าถึงได้ในราคาเริ่มต้น $9.9 แทนที่จะเป็น $1,500+",
        "pricing.p_text.every_project_is_different_a_5minute_vhs.688d1fd6":
            "ทุกโครงการมีความแตกต่างกัน เทป VHS ความยาว 5 นาที และภาพยนตร์งานแต่งงาน 4K ความยาว 3 ชั่วโมงไม่ใช่งานเดียวกัน เราเสนอราคาตามความยาวฟุตเทจ ความซับซ้อน และการตอบสนอง ราคาเริ่มต้น $9.9 คือจุดเริ่มต้นของบริการแต่ละอย่าง ใบเสนอราคาขั้นสุดท้ายสะท้อนขอบเขตจริงของโครงการของคุณ",
    },
}

# Keys that must be replaced in every file
KEYS_TO_REPLACE = list(next(iter(TRANSLATIONS.values())).keys())


def main():
    if not os.path.isdir(I18N_DIR):
        print(f"FATAL: i18n dir not found: {I18N_DIR}", file=sys.stderr)
        return 1

    # We only touch the 10 non-English files (en.json was already updated
    # by the user/editor before this script ran).
    targets = sorted(lang for lang in TRANSLATIONS if lang != "en")
    replaced_total = 0
    for lang in targets:
        path = os.path.join(I18N_DIR, f"{lang}.json")
        if not os.path.isfile(path):
            print(f"  SKIP {lang} (no file)")
            continue

        with open(path, "r", encoding="utf-8", newline="") as f:
            raw = f.read()

        # Detect line ending; preserve it
        newline = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.split(newline)
        new_lines = []
        replaced_keys = []
        for line in lines:
            replaced = False
            for key in KEYS_TO_REPLACE:
                # Match: "key": "old value",
                prefix = f'  "{key}": "'
                if line.startswith(prefix):
                    suffix = '"'  # closing quote of the value
                    # The original line ends with `",` (or `"\n` for last line).
                    # We rebuild the line with the new value.
                    trailing = ""
                    stripped = line[len(prefix):]
                    # Find end of the value (the last `"` in the line; the JSON-LD
                    # values we replace don't contain unescaped `"` inside).
                    end = stripped.rfind('"')
                    if end < 0:
                        break
                    trailing = stripped[end+1:]  # the `,` and any whitespace
                    new_value = TRANSLATIONS[lang][key]
                    new_line = f'{prefix}{new_value}{trailing}'
                    new_lines.append(new_line)
                    replaced = True
                    replaced_keys.append(key)
                    break
            if not replaced:
                new_lines.append(line)

        new_raw = newline.join(new_lines)
        if new_raw != raw:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new_raw)
            print(f"  OK   {lang}: replaced {len(replaced_keys)} keys")
            replaced_total += len(replaced_keys)
        else:
            print(f"  --   {lang}: no change")

    print(f"\nDone. Total keys replaced: {replaced_total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
