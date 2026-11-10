#!/usr/bin/env python3
"""
Build the i18n patch for the face-aware crop tool (§2.11).

WHAT IT DOES
------------
Writes .tmp/patch-crop-face-i18n.json: the new and corrected strings for
the crop tool, in all eleven languages.

The keys fall into three groups:

  * the NEW face-aware controls (the switch, its hint, the two prose
    paragraphs),
  * the TWO EXISTING keys whose value stopped being true - the page used to
    promise "an off-center bias instead of face detection", and the
    comparison table used to claim the tool had no face framing at all,
  * the runtime strings of the status line, which live in the "tools.copy"
    namespace because the middleware hands that namespace to the client as
    window.__WA_I18N__ (see functions/_middleware.js).

THE OFF-CENTER HINT
--------------------
tools.crop-wedding-photo-for-reels.small_text.a6b24d1f already existed, but
only in the seven languages whose pages bound it - and in those seven the
value was CHINESE. The four other pages had the text inline and unbound.
This patch gives all eleven a real translation of the corrected sentence.

Usage
-----
    python scripts/build-crop-face-i18n-patch.py
    python scripts/add-tool-ui-keys.py .tmp/patch-crop-face-i18n.json
    python scripts/add-shards-for-keys.py i18n/<lang>.json i18n/<lang>.manifest.json
    python scripts/verify-i18n-shards.py
"""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".tmp" / "patch-crop-face-i18n.json"

P = "tools.crop-wedding-photo-for-reels."

KEYS = {}


def add(key, en, zh, es, fr, de, pt, ja, ru, ar, th, hi):
    KEYS[key] = {
        "en": en, "zh": zh, "es": es, "fr": fr, "de": de, "pt": pt,
        "ja": ja, "ru": ru, "ar": ar, "th": th, "hi": hi,
    }


# --- the off-center control ------------------------------------------------

add(
    P + "label_text.off_center_bias.9a8b7c6d",
    "Off-center bias — automatic starting position",
    "中心偏移 — 自动起始位置",
    "Sesgo fuera del centro — posición de inicio automática",
    "Décalage hors centre — position de départ automatique",
    "Off-Center-Versatz — automatische Startposition",
    "Viés fora do centro — posição inicial automática",
    "オフセンターオフセット — 自動の開始位置",
    "Смещение от центра — автоматическая начальная позиция",
    "انزياح خارج المركز — موضع البداية التلقائي",
    "ออฟเซ็นเตอร์ไบแอส — ตำแหน่งเริ่มต้นอัตโนมัติ",
    "ऑफ-सेंटर बायस — स्वचालित प्रारंभिक स्थिति",
)

add(
    P + "small_text.a6b24d1f",
    "Sets where the crop frame starts: 60% down the Y axis for landscape sources "
    "(where wedding couples typically stand) and true center for portrait sources. "
    "It is a fixed heuristic, not a measurement — switch on Face-aware framing "
    "below to have the crop follow the actual faces. Drag the frame in step 3 to "
    "override it for any photo. ON for landscape sources, OFF if your source is "
    "already a tight portrait composition.",
    "决定裁剪框从哪里开始：横版原图沿 Y 轴下移 60%（新人通常站立的位置），竖版原图取正中。"
    "它只是一个固定的经验规则，并不是真正的测量——想让它跟着真实人脸走，请打开下方的"
    "“人脸感知取景”。第 3 步里拖动裁剪框可以为任意一张照片单独调整。横版素材建议开启；"
    "如果原图已经是紧凑的竖版构图，可以关闭。",
    "Define dónde empieza el marco de recorte: 60 % hacia abajo en el eje Y "
    "para fuentes apaisadas (donde suelen situarse los novios) y el centro exacto para "
    "fuentes verticales. Es una regla fija, no una medición: activa el encuadre "
    "con detección de rostros más abajo para que el recorte siga las caras "
    "reales. Arrastra el marco en el paso 3 para anularlo en cualquier foto. Actívalo "
    "para fuentes apaisadas y desactívalo si tu original ya es una composición "
    "vertical ajustada.",
    "Définit où commence le cadre de recadrage : 60 % vers le bas sur "
    "l’axe Y pour les sources paysage (là où les mariés se tiennent "
    "en général) et le centre exact pour les sources verticales. C’est une "
    "règle fixe, pas une mesure — activez le cadrage avec détection des "
    "visages ci-dessous pour que le recadrage suive les vrais visages. Faites glisser le "
    "cadre à l’étape 3 pour le remplacer sur n’importe quelle photo. "
    "À activer pour les sources paysage, à désactiver si votre original est "
    "déjà un portrait serré.",
    "Legt fest, wo der Beschnittungsrahmen beginnt: 60 % nach unten auf der Y-Achse "
    "für Querformat-Quellen (dort, wo Hochzeitspaare meist stehen) und die exakte Mitte "
    "für Hochformat-Quellen. Das ist eine feste Heuristik, keine Messung – "
    "schalten Sie unten die gesichtsbewusste Rahmensetzung ein, damit der Beschnitt den "
    "echten Gesichtern folgt. Ziehen Sie den Rahmen in Schritt 3, um ihn für ein "
    "einzelnes Foto zu überschreiben. Für Querformat-Quellen einschalten, "
    "ausschalten, wenn das Original bereits eine enge Hochformatkomposition ist.",
    "Define onde a moldura de corte começa: 60% para baixo no eixo Y para fontes "
    "horizontais (onde os noivos costumam ficar) e o centro exato para fontes verticais. "
    "É uma regra fixa, não uma medição — ative o "
    "enquadramento com detecção de rostos abaixo para que o corte acompanhe os "
    "rostos de verdade. Arraste a moldura na etapa 3 para substituir em qualquer foto. "
    "Ligue para fontes horizontais e desligue se a sua original já for uma "
    "composição vertical apertada.",
    "トリミング枠の開始位置を決めます。横向きの素材では Y 軸の 60%（新人が立つことが多い位置）、"
    "縦向きの素材では真正中央ンターです。これは固定のヒューリスティックであり、測定ではありません。"
    "実際の顔に追従させたい場合は下の「顔認識トリミング」をオンにしてください。ステップ 3 で枠を"
    "ドラッグすれば、写真ごとに上書きできます。横向きの素材ではオン、すでに締まった縦構図の素材では"
    "オフにします。",
    "Задаёт, откуда начинается рамка кадрирования: на 60 % ниже по оси Y для "
    "горизонтальных исходников (там, где обычно стоит пара) и точно по центру для "
    "вертикальных. Это фиксированная эвристика, а не измерение — включите "
    "«кадрирование по лицам» ниже, чтобы кадр следовал за реальными лицами. Перетащите "
    "рамку на шаге 3, чтобы изменить её для отдельной фотографии. Включайте для "
    "горизонтальных исходников и выключайте, если оригинал уже плотно скомпонован по вертикали.",
    "يحدّد مكان بداية إطار القصّ: 60% لأسفل على المحور Y للمصادر الأفقية (حيث يقف "
    "العروسان عادةً) والمنتصف تمامًا للمصادر العمودية. هذه قاعدة ثابتة وليست قياسًا "
    "— فعّل «التأطير الواعي بالوجوه» أدناه ليبتبع القصّ الوجوه الحقيقية. اسحب الإطار "
    "في الخطوة 3 لتجاوزه لأي صورة. فعّله للمصادر الأفقية، وأوقفه إذا كانت صورتك الأصلية "
    "تكوينًا عموديًا ضيقًا.",
    "กำหนดจุดเริ่มต้นของกรอบตัด: 60% ลงไปตามแกน Y สำหรับภาพแนวนอน (ตรงที่คู่บ่าสามีมายืน) "
    "และกึ่งกลางจริงสำหรับภาพแนวตั้ง นี่คือกฎคงที่ ไม่ใช่การวัดจริง — เปิด "
    "“การตัดโดยรู้หน้า” ด้านล่างเพื่อให้การตัดตามใบหน้าจริง ลากกรอบในขั้นตอนที่ 3 "
    "เพื่อปรับสำหรับแต่ละรูป เปิดสำหรับภาพแนวนอน และปิดถ้าภาพต้นฉบับเป็นองค์ประกอบ"
    "แนวตั้งที่กระชับอยู่แล้ว",
    "यह तय करता है कि क्रॉप फ़्रेम कहाँ से शुरू हो: लैंडस्केप स्रोतों के लिए Y-अक्ष पर 60% "
    "नीचे (जहाँ नव-जोड़े आमतौर पर खड़े होते हैं) और पोर्ट्रेट स्रोतों के लिए ठीक बीच में। यह "
    "एक तय नियम है, माप नहीं — असली चेहरों के अनुसार क्रॉप चलाने के लिए नीचे "
    "“चेहरा-आधारित फ़्रेमिंग” चालू करें। किसी भी फ़ोटो के लिए इसे बदलने हेतु चरण 3 में फ़्रेम "
    "खींचें। लैंडस्केप स्रोतों के लिए चालू रखें, और यदि स्रोत पहले से ही कसा हुआ पोर्ट्रेट "
    "कंपोज़िशन है तो बंद कर दें।",
)

# --- the face-aware control ------------------------------------------------

add(
    P + "label_text.face_aware_framing.5d4c3b2a",
    "Face-aware framing — optional",
    "人脸感知取景 — 可选",
    "Encuadre con detección de rostros — opcional",
    "Cadrage avec détection des visages — facultatif",
    "Gesichtsbewusste Rahmensetzung – optional",
    "Enquadramento com detecção de rostos — opcional",
    "顔認識トリミング — 任意",
    "Кадрирование по лицам — необязательно",
    "التأطير الواعي بالوجوه — اختياري",
    "การตัดโดยรู้หน้า — ไม่บังคับ",
    "चेहरा-आधारित फ़्रेमिंग — वैकल्पिक",
)

add(
    P + "small_text.face_aware_hint.6e7f8091",
    "Finds the faces in each photo and moves the crop frame so every face stays "
    "inside it. The detector (about 840 KB) downloads once, the first time you "
    "switch this on, and then runs entirely on your device — your photos are "
    "never uploaded. A photo with no detectable face keeps the off-center bias.",
    "在每张照片里找出人脸，并移动裁剪框，让每一张脸都留在画面里。检测模型（约 840 KB）"
    "只在你第一次打开这个开关时下载一次，之后全部在你自己的设备上运行——照片永远不会被上传。"
    "找不到人脸的照片仍然沿用中心偏移。",
    "Encuentra los rostros en cada foto y mueve el marco de recorte para que todas las "
    "caras queden dentro. El detector (unos 840 KB) se descarga una sola vez, la "
    "primera vez que activas esta opción, y después funciona "
    "íntegramente en tu dispositivo: tus fotos nunca se suben. Una foto sin rostros "
    "detectables mantiene el sesgo fuera del centro.",
    "Trouve les visages sur chaque photo et déplace le cadre de recadrage pour que "
    "tous les visages restent à l’intérieur. Le détecteur (environ "
    "840 Ko) est téléchargé une seule fois, la première fois que "
    "vous activez cette option, puis fonctionne entièrement sur votre appareil : vos "
    "photos ne sont jamais envoyées. Une photo sans visage détectable conserve le "
    "décalage hors centre.",
    "Findet die Gesichter auf jedem Foto und verschiebt den Beschnittungsrahmen so, dass "
    "alle Gesichter darin bleiben. Der Detektor (rund 840 KB) wird nur einmal "
    "geladen, und zwar beim ersten Einschalten dieser Option, danach läuft er "
    "vollständig auf Ihrem Gerät – Ihre Fotos werden nie hochgeladen. Ein Foto "
    "ohne erkennbares Gesicht behält den Off-Center-Versatz.",
    "Encontra os rostos em cada foto e move a moldura de corte para que todos os rostos "
    "fiquem dentro. O detector (cerca de 840 KB) é baixado uma única vez, na "
    "primeira vez que você liga esta opção, e depois roda inteiramente no seu "
    "dispositivo — suas fotos nunca são enviadas. Uma foto sem rosto detectável "
    "mantém o viés fora do centro.",
    "各写真の中から顔を見つけ、すべての顔がフレーム内に収まるようトリミング枠を動かします。"
    "検出モデル（約 840 KB）は、この設定を初めてオンにしたときだけ一度ダウンロードされ、"
    "その後はすべてお使いのデバイス上で動作します。写真そのものがアップロードされることは"
    "ありません。顔を検出できなかった写真はオフセンターのバイアスのままです。",
    "Находит лица на каждой фотографии и сдвигает рамку кадрирования так, чтобы все лица "
    "остались внутри. Детектор (около 840 КБ) загружается один раз — в момент "
    "первого включения этой опции, — а дальше работает полностью на вашем устройстве: "
    "фотографии никуда не отправляются. Фото без распознанных лиц сохраняют смещение от "
    "центра.",
    "يبحث عن الوجوه في كل صورة ويحرّك إطار القصّ ليبقى كل وجه داخل الإطار. يُنزَّل الكاشف "
    "(نحو 840 كيلوبايت) مرة واحدة فقط، عند أول تشغيل لهذا الخيار، ثم يعمل بالكامل على "
    "جهازك — ولا تُرفع صورك أبدًا. الصورة التي لا يُكتشف فيها وجه تحتفظ بانزياح خارج "
    "المركز.",
    "ค้นหาใบหน้าในแต่ละรูปและเลื่อนกรอบตัดให้ทุกใบหน้าอยู่ภายในกรอบ ตัวตรวจจับ "
    "(ประมาณ 840 KB) จะดาวน์โหลดครั้งเดียว ตอนที่คุณเปิดใช้งานครั้งแรก จากนั้นทำงาน"
    "ทั้งหมดบนเครื่องของคุณ — รูปของคุณจะไม่ถูกอัปโหลด รูปที่ตรวจจับใบหน้าไม่ได้จะยังคง"
    "ใช้ออฟเซ็นเตอร์ไบแอสเดิม",
    "हर फ़ोटो में चेहरे खोजता है और क्रॉप फ़्रेम को ऐसे खिसकाता है कि हर चेहरा फ़्रेम के अंदर "
    "रहे। डिटेक्टर (लगभग 840 KB) पहली बार ऑन करते समय एक बार ही डाउनलोड होता है, और उसके "
    "बाद पूरी तरह आपके डिवाइस पर चलता है — आपकी फ़ोटो कभी अपलोड नहीं होती। जिस फ़ोटो में "
    "चेहरा न मिले, वह ऑफ-सेंटर बायस पर ही रहती है।",
)

# --- the prose --------------------------------------------------------------

add(
    P + "p_text.why_off_center_beats_center.1b2c3d4e",
    "A wedding photo is almost never “subject at exact center.” Composition "
    "rules (rule of thirds, leading lines) push the subject off-center — usually "
    "slightly below center on a horizontal frame. A naive center-crop system blindly "
    "halves the image and ships it, often cutting the bride’s face out of the frame "
    "entirely. The off-center heuristic used here is intentionally simple — a "
    "fixed bias, not a measurement — but it matches the photographic convention "
    "well enough to handle ~85% of wedding shots correctly on the first try. When you "
    "want the frame to follow the real faces instead of the convention, switch on "
    "Face-aware framing.",
    "婚纱照几乎从不把主体放在正中央。构图法则（三分法、引导线）会把主体推到偏中的位置——横版画框里"
    "通常还略低于正中。朴素的居中裁剪只会把照片对半切了就交付，结果经常把新娘的脸整个切出画面。"
    "这里用的中心偏移有意做得简单——它是一个固定的经验值，不是一次真实测量——但它足够贴合摄影惯例，"
    "第一次尝试就能把大约 85% 的婚纱照处理对。如果你希望画框跟着真实的人脸走，而不是跟着惯例走，"
    "请打开“人脸感知取景”。",
    "Una foto de boda casi nunca es «sujeto en el centro exacto». Las reglas de "
    "composición (regla de los tercios, líneas guía) empujan al sujeto fuera "
    "del centro — normalmente un poco por debajo del centro en un encuadre horizontal. "
    "Un recorte centrado ingenuo corta la imagen por la mitad a ciegas y la entrega, y a "
    "menudo se lleva por delante la cara de la novia. El sesgo fuera del centro que usamos "
    "aquí es intencionadamente simple — un sesgo fijo, no una medición "
    "— pero encaja con la convención fotográfica lo bastante bien como para "
    "acertar con aproximadamente el 85 % de las fotos de boda a la primera. Cuando quieras "
    "que el encuadre siga las caras reales en lugar de la convención, activa el encuadre "
    "con detección de rostros.",
    "Une photo de mariage n’est presque jamais « sujet au centre exact ». Les "
    "règles de composition (règle des tiers, lignes directrices) décalent le "
    "sujet hors centre — généralement un peu sous le centre sur un cadre "
    "horizontal. Un recadrage centré naïf coupe l’image en deux à "
    "l’aveugle et l’envoie, et emporte souvent le visage de la mariée. Le "
    "décalage hors centre utilisé ici est volontairement simple — un biais "
    "fixe, pas une mesure — mais il suit la convention photographique assez bien pour "
    "traiter correctement environ 85 % des photos de mariage du premier coup. Quand vous "
    "voulez que le cadre suive les vrais visages plutôt que la convention, activez le "
    "cadrage avec détection des visages.",
    "Ein Hochzeitsfoto ist fast nie „Motiv in exakter Mitte“. Kompositionsregeln "
    "(Drittel-Regel, Leitlinien) schieben das Motiv aus der Mitte — bei einem "
    "Querformat meist etwas unterhalb der Mitte. Ein naives Center-Crop halbiert das Bild "
    "blind und liefert es, und schneidet dabei oft das Gesicht der Braut aus dem Rahmen. Der "
    "hier verwendete Off-Center-Versatz ist bewusst einfach — ein fester Versatz, keine "
    "Messung —, trifft die fotografische Konvention aber gut genug, um rund "
    "85 % der Hochzeitsbilder beim ersten Versuch richtig zu treffen. Wenn der Rahmen "
    "den echten Gesichtern folgen soll statt der Konvention, schalten Sie die "
    "gesichtsbewusste Rahmensetzung ein.",
    "Uma foto de casamento quase nunca é «assunto no centro exato». As regras "
    "de composição (regra dos terços, linhas-guia) empurram o assunto para "
    "fora do centro — num quadro horizontal, quase sempre um pouco abaixo do centro. Um "
    "corte central ingênuo corta a imagem ao meio às cegas e entrega o resultado, muitas vezes "
    "levando junto o rosto da noiva. O viés fora do centro usado aqui é "
    "intencionalmente simples — um viés fixo, não uma medição "
    "—, mas acompanha a convenção fotográfica o bastante para acertar "
    "cerca de 85% das fotos de casamento na primeira tentativa. Quando quiser que o "
    "enquadramento siga os rostos de verdade em vez da convenção, ative o "
    "enquadramento com detecção de rostos.",
    "結婚写真が「被写体が正確な中央にある」ことはほぼありません。構図のルール（三分法、"
    "リーディングライン）は被写体をオフセンターへ押し、横長のフレームではたいてい中央より少し下"
    "になります。中央トリミングの素朴な実装は画像の半分を機械的に切って出し、花嫁の顔ごとフレーム"
    "から切り落としてしまいます。ここでのオフセンターヒューリスティックは意図的に単純で、測定では"
    "なく固定のバイアスです。それでも写真の慣習に十分沿うので、最初の試行でおよそ 85% の"
    "結婚写真を正しく処理できます。慣習ではなく実際の顔に画枠を合わせたい場合は、顔認識トリミング"
    "をオンにしてください。",
    "Свадебный кадр почти никогда не ставит объект строго в центр. Композиционные правила "
    "(правило третей, ведущие линии) уводят объект от центра — на горизонтальном кадре "
    "обычно чуть ниже середины. Наивное центральное кадрирование бездумно делит снимок пополам и "
    "отдаёт результат, зачастую вырезая лицо невесты из кадра. Смещение от центра, которое "
    "используется здесь, намеренно простое — это фиксированное смещение, а не измерение, "
    "— но оно достаточно точно совпадает с фотографической конвенцией, чтобы с первого "
    "раза верно обработать примерно 85 % свадебных кадров. Когда хочется, чтобы кадр "
    "следовал за настоящими лицами, а не за конвенцией, включите кадрирование по лицам.",
    "الصورة الزفافية نادرًا ما تضع الموضوع في المنتصف بالضبط. قواعد التكوين (قاعدة الأثلاث، "
    "خطوط الإرشاد) تزيح الموضوع خارج المركز — وعادةً قليلًا تحت المنتصف في الإطار "
    "الأفقي. القصّ المركزي الساذج يقسم الصورة إلى نصفين دون تفكير ويسلّم النتيجة، وغالبًا يقطع "
    "وجه العروس من الإطار. الانزياح خارج المركز المستخدَم هنا بسيط عن قصد — إنه انزياح "
    "ثابت لا قياس — لكنه يطابق العرف التصويري بما يكفي ليضع نحو 85% من لقطات الزفاف في "
    "موضعها الصحيح من المحاولة الأولى. وحين تريد أن يتبع الإطار الوجوه الحقيقية بدلًا من العرف، "
    "فعّل «التأطير الواعي بالوجوه».",
    "ภาพแต่งงานแทบไม่เคยวางวัตถุไว้ตรงกลางเป๊ะ กฎการจัดองค์ประกอบ (กฎสามส่วน "
    "เส้นนำสายตา) ผลักวัตถุออกจากกลาง — ในกรอบแนวนอนมักต่ำกว่ากลางเล็กน้อย "
    "ระบบตัดกลางแบบง่ายๆ จะแบ่งภาพครึ่งหนึ่งโดยไม่คิดอะไรแล้วส่งออกไป มักตัดใบหน้าเจ้าสาว"
    "หายไปจากกรอบ ออฟเซ็นเตอร์ไบแอสที่ใช้ที่นี่ตั้งใจให้เรียบง่าย — เป็นค่าคงที่ ไม่ใช่การวัด "
    "— แต่ยังตรงกับข้อตกลงทางการถ่ายภาพพอจะจัดการภาพแต่งงานได้ถูกต้องราว 85% ตั้งแต่ครั้งแรก "
    "และเมื่อคุณอยากให้กรอบตามใบหน้าจริงแทนที่จะตามข้อตกลง ให้เปิด “การตัดโดยรู้หน้า”",
    "शादी की तस्वीर में विषय लगभग कभी भी ठीक बीच में नहीं होता। कंपोज़िशन के नियम (थर्ड्स का नियम, "
    "लीडिंग लाइंस) विषय को बीच से बाहर खींचते हैं — क्षैतिज़ फ़्रेम में आम तौर पर बीच से "
    "थोड़ा नीचे। आसानी से बीच से कटने वाला सिस्टम बिना सोचे तस्वीर को आधा करके भेज देता है, और "
    "अक्सर दुल्हन का चेहरा ही फ़्रेम से बाहर चला जाता है। यहाँ इस्तेमाल किया गया ऑफ-सेंटर बायस जानबूझकर "
    "आसान है — यह एक तय पूर्वाग्रह है, माप नहीं — लेकिन यह फ़ोटोग्राफ़ी की परंपरा से इतना "
    "मेल खाता है कि लगभग 85% शादी की तस्वीरें पहली कोशिश में सही फ़्रेम में आ जाती हैं। और जब आप चाहते हैं "
    "कि फ़्रेम परंपरा के बजाय असली चेहरों का पीछा करे, तो चेहरा-आधारित फ़्रेमिंग चालू कर दें।",
)

add(
    P + "p_text.face_aware_framing.2f3e4d5c",
    "The off-center bias is a guess about where the couple usually stands. If you "
    "would rather the crop followed the actual people in the frame, switch on "
    "<strong>Face-aware framing</strong>: the tool finds the faces in each photo and "
    "slides the crop window so that every face stays inside it, with a little breathing "
    "room around them. The detector is a small model that runs in your browser — "
    "the photos are read on your device and never uploaded — and a photo with no "
    "detectable face simply keeps the off-center bias.",
    "中心偏移只是猜测新人通常站在哪里。如果你想让裁剪跟着画面里的真人走，请打开"
    "<strong>人脸感知取景</strong>：工具会在每张照片里找出人脸，并把裁剪窗口滑到让每一张脸都留在"
    "画面里、四周还留一点余量。检测是一个跑在你浏览器里的小模型——照片在你的设备上被读取，永远不会"
    "被上传——而找不到人脸的照片则继续沿用中心偏移。",
    "El sesgo fuera del centro es una suposición sobre dónde suele estar la pareja. "
    "Si prefieres que el recorte siga a las personas reales del encuadre, activa el "
    "<strong>encuadre con detección de rostros</strong>: la herramienta encuentra los "
    "rostros en cada foto y desliza la ventana de recorte hasta que todas las caras quedan "
    "dentro, con un poco de margen alrededor. El detector es un modelo pequeño que se "
    "ejecuta en tu navegador: las fotos se leen en tu dispositivo y nunca se suben, y una foto "
    "sin rostros detectables simplemente conserva el sesgo fuera del centro.",
    "Le décalage hors centre est une supposition sur l’endroit où le couple se "
    "tient d’habitude. Si vous préférez que le recadrage suive les vraies "
    "personnes de l’image, activez le <strong>cadrage avec détection des visages</strong> : "
    "l’outil trouve les visages sur chaque photo et fait glisser la fenêtre de recadrage "
    "jusqu’à ce que tous les visages restent à l’intérieur, avec un peu de "
    "marge autour. Le détecteur est un petit modèle qui tourne dans votre navigateur "
    "— les photos sont lues sur votre appareil et ne sont jamais envoyées — et une photo "
    "sans visage détectable conserve simplement le décalage hors centre.",
    "Der Off-Center-Versatz ist eine Vermutung darüber, wo das Paar meistens steht. Wenn der "
    "Beschnitt stattdessen den echten Personen im Bild folgen soll, schalten Sie die "
    "<strong>gesichtsbewusste Rahmensetzung</strong> ein: Das Werkzeug findet die Gesichter auf "
    "jedem Foto und verschiebt das Zuschnittfenster so, dass alle Gesichter darin bleiben "
    "– mit etwas Luft ringsum. Der Detektor ist ein kleines Modell, das in Ihrem Browser "
    "läuft – die Fotos werden auf Ihrem Gerät gelesen und niemals hochgeladen – und ein "
    "Foto ohne erkennbares Gesicht behält einfach den Off-Center-Versatz.",
    "O viés fora do centro é um palpite sobre onde o casal costuma estar. Se "
    "preferir que o corte siga as pessoas de verdade no quadro, ative o <strong>enquadramento "
    "com detecção de rostos</strong>: a ferramenta encontra os rostos em cada foto e "
    "desliza a janela de corte até que todos os rostos fiquem dentro, com uma pequena "
    "margem ao redor. O detector é um modelo pequeno que roda no seu navegador — as "
    "fotos são lidas no seu dispositivo e nunca são enviadas — e uma foto sem "
    "rosto detectável simplesmente mantém o viés fora do centro.",
    "オフセンターのバイアスは、新人がどこかにいるかを推測したものです。トリミング枠が実際の人物に"
    "従うようにするには、<strong>顔認識トリミング</strong>をオンにしてください。ツールは各写真の中から"
    "顔を見つけ、すべての顔が内側に収まり周囲に少し余裕が出るまでトリミング枠を滑らせます。"
    "検出はブラウザ内で動く小さなモデルで、写真はお使いのデバイス上で読み取られ、アップロードされる"
    "ことはありません。顔を検出できなかった写真はオフセンターのバイアスのままです。",
    "Смещение от центра — это догадка о том, где обычно стоит пара. Если хочется, чтобы кадр "
    "следовал за реальными людьми в снимке, включите <strong>кадрирование по лицам</strong>: "
    "инструмент находит лица на каждой фотографии и сдвигает окно кадрирования до тех пор, пока все "
    "лица не окажутся внутри, с небольшим запасом вокруг них. Детектор — небольшая модель, "
    "работающая в вашем браузере: фотографии читаются на вашем устройстве и никуда не "
    "отправляются, а фото без распознанных лиц просто сохраняют смещение от центра.",
    "الانزياح خارج المركز هو تقدير لمكان وقوف العروسين عادةً. إن أردت أن يتبع القصّ الأشخاص "
    "الحقيقيين في الصورة، فعّل <strong>التأطير الواعي بالوجوه</strong>: يعثر الأداة على الوجوه في "
    "كل صورة وتُزلق نافذة القصّ حتى تبقى كل الوجوه في الداخل مع هامش بسيط حولها. الكاشف نموذج "
    "صغير يعمل داخل متصفحك — تُقرأ الصور على جهازك ولا تُرفع أبدًا — أما الصورة التي لا "
    "يُكتشف فيها وجه فتحتفظ بالانزياح خارج المركز.",
    "ออฟเซ็นเตอร์ไบแอสเป็นเพียงการคาดเดาว่าคู่บ่าสามักยืนอยู่ตรงไหน หากอยากให้การตัดตามคนจริงในภาพ "
    "เปิด <strong>การตัดโดยรู้หน้า</strong>: เครื่องมือจะค้นหาใบหน้าในแต่ละรูปแล้วเลื่อนหน้าต่างตัดจนทุกใบหน้า"
    "อยู่ภายใน พร้อมเว้นขอบเล็กน้อย ตัวตรวจจับเป็นโมเดลเล็กๆ ที่ทำงานในเบราว์เซอร์ของคุณ — รูปถูกอ่าน"
    "บนเครื่องของคุณและไม่ถูกอัปโหลด — ส่วนรูปที่ตรวจจับใบหน้าไม่ได้ก็ยังคงใช้ออฟเซ็นเตอร์ไบแอสเดิม",
    "ऑफ-सेंटर बायस यह अनुमान लगाना है कि जोड़े आमतौर पर कहाँ खड़े होते हैं। यदि आप चाहते हैं कि क्रॉप "
    "तस्वीर के असली लोगों का पीछा करे, तो <strong>चेहरा-आधारित फ़्रेमिंग</strong> चालू करें: टूल हर फ़ोटो में "
    "चेहरे खोजता है और क्रॉप विंडो को तब तक खिसकाता रहता है जब तक हर चेहरा अंदर आ जाए, चारों ओर थोड़ी "
    "जगह छोड़ते हुए। डिटेक्टर एक छोटा मॉडल है जो आपके ब्राउज़र में ही चलता है — फ़ोटो आपके डिवाइस पर ही "
    "पढ़ी जाती हैं और कभी अपलोड नहीं होतीं — और जिस फ़ोटो में चेहरा न मिले, वह ऑफ-सेंटर बायस पर ही "
    "रहती है।",
)

# --- the two existing keys whose value stopped being true ------------------

add(
    P + "p_text.most_crop_tools_require_manu.5m6n7o8p",
    "Most crop tools require you to manually center the bride and groom for each of "
    "100+ wedding photos. WeddingAI.video’s crop uses an off-center bias by "
    "default — it shifts the crop window 60% down on landscape sources, where "
    "wedding couples usually stand, so the couple stays inside the frame instead of "
    "being cropped out — and it can switch to real on-device face detection when "
    "you want the frame to follow the actual faces. It exports 9:16 + 1:1 + 4:5 in one "
    "batch. Plus, the same batch feeds into the AI video’s IG-ready export "
    "— vertical Reels + horizontal YT Shorts + 1:1 square for feed + 4:5 for IG "
    "carousel.",
    "大多数裁剪工具要你为每张婚纱照手动居中新人。WeddingAI.video 的裁剪默认采用中心偏移：横版原图会"
    "把裁剪窗口下移 60%，也就是新人们通常站立的位置，因此新人会留在画面里而不是被裁掉；如果你希望"
    "画框跟着真实人脸走，也可以切换到真正的本地人脸检测。一次批量导出 9:16 + 1:1 + 4:5。同时这批"
    "裁剪好的照片直接送进 AI 婚礼视频的 IG 适配导出：竖屏抖音 + 9:16 YT Shorts + 1:1 IG Feed + 4:5 "
    "IG 轮播。",
    "La mayoría de las herramientas de recorte te obligan a centrar a los novios a "
    "mano en cada una de más de 100 fotos de boda. El recorte de WeddingAI.video usa "
    "por defecto un sesgo fuera del centro: desplaza la ventana de recorte 60 % hacia "
    "abajo en las fuentes apaisadas, donde los novios suelen estar, para que la pareja se "
    "quede dentro del encuadre en lugar de ser recortada; y puedes cambiarlo a una "
    "detección real de rostros en tu propio dispositivo cuando quieras que el encuadre "
    "siga las caras de verdad. Exporta 9:16 + 1:1 + 4:5 en un solo lote. Además, ese "
    "mismo lote alimenta la exportación para IG del vídeo de IA: Reels verticales + "
    "YT Shorts horizontales + 1:1 para el feed + 4:5 para el carrusel de IG.",
    "La plupart des outils de recadrage vous obligent à centrer manuellement les "
    "mariés sur chacune des 100+ photos de mariage. Le recadrage de WeddingAI.video "
    "utilise par défaut un décalage hors centre : il déplace la "
    "fenêtre de recadrage de 60 % vers le bas sur les sources paysage, là où "
    "les mariés se tiennent en général, pour que le couple reste dans le cadre "
    "au lieu d’être coupé ; et vous pouvez passer à une vraie "
    "détection des visages sur votre appareil quand vous voulez que le cadre suive les "
    "visages réels. Il exporte 9:16 + 1:1 + 4:5 en un seul lot. Ce même lot "
    "alimente ensuite l’export IG du clip IA : Reels verticaux + YT Shorts "
    "horizontaux + 1:1 pour le fil + 4:5 pour le carrousel IG.",
    "Die meisten Crop-Tools verlangen, dass Sie Braut und Bräutigam für jedes der "
    "100+ Hochzeitsfotos von Hand zentrieren. Der Auto-Zuschnitt von WeddingAI.video nutzt "
    "standardmäßig einen Off-Center-Versatz: Bei Querformat-Quellen wird das "
    "Zuschnittsfenster um 60 % nach unten verschoben, also dorthin, wo Hochzeitspaare "
    "meist stehen, so bleibt das Paar im Bild und wird nicht beschnitten – und wenn der "
    "Rahmen den echten Gesichtern folgen soll, können Sie auf eine echte "
    "Gesichtserkennung auf Ihrem Gerät umschalten. Er exportiert 9:16 + 1:1 + 4:5 in "
    "einem Durchgang. Dazu geht derselbe Stapel direkt in den IG-tauglichen Export des "
    "KI-Videos: vertikale Reels + horizontale YT Shorts + 1:1 für den Feed + 4:5 für "
    "den IG-Karussell.",
    "A maioria das ferramentas de corte exige que você centralize os noivos manualmente "
    "em cada uma das 100+ fotos de casamento. O corte do WeddingAI.video usa por padrão "
    "um viés fora do centro: desloca a janela de corte 60% para baixo nas fontes "
    "horizontais, onde os noivos costumam ficar, para que o casal fique dentro do quadro em "
    "vez de ser cortado — e você pode alternar para uma detecção de rostos "
    "real, feita no seu próprio dispositivo, quando quiser que o quadro siga os rostos de "
    "verdade. Ele exporta 9:16 + 1:1 + 4:5 em um único lote. E o mesmo lote alimenta a "
    "exportação para IG do vídeo de IA: Reels verticais + YT Shorts horizontais "
    "+ 1:1 para o feed + 4:5 para o carrossel do IG.",
    "ほとんどの切り抜きツールは、100枚以上の結婚写真のそれぞれで、新郎新婦を手作業で中央に配置"
    "させることを求めます。WeddingAI.videoの切り抜きは初期設定でオフセンターのバイアスを使いま"
    "す。横向きの画像では切り抜き枠を60%下へずらします（結婚式の新郎新婦が立つ位置）ため、新郎新婦が"
    "フレーム内に残り、切り落とされません。枠を実際の顔に追従させたいときは、デバイス上で動く顔検出"
    "に切り替えることもできます。9:16（リール/Stories/YT Shorts）+ 1:1（IGフィード）+ 4:5"
    "（IGポートレート）+ 4:3 + 3:2に対応、結婚式特化9モデル（Save the Date/RSVP/動画チャプター）"
    "+ 11言語 + 9.9€動画と同じワークフロー。同じ一括処理の写真は IG 対応の出力（縦型Reels + "
    "横型YT Shorts + 1:1 IGフィード + 4:5 IGカルーセル）にもそのまま使えます。",
    "Большинство инструментов кадрирования требуют вручную центрировать невесту и жениха на "
    "каждом из 100+ свадебных кадров. Кадрирование в WeddingAI.video по умолчанию использует "
    "смещение от центра: для горизонтальных исходников окно сдвигается на 60 % вниз, туда, "
    "где обычно стоит пара, так что она остаётся в кадре, а не вырезается; а когда хочется, "
    "чтобы кадр следовал за настоящими лицами, можно переключиться на реальное распознавание "
    "лиц прямо на устройстве. Экспорт: 9:16 + 1:1 + 4:5 одним пакетом. Тот же пакет затем "
    "идёт в IG-совместимый экспорт AI-видео: вертикальные Reels + горизонтальные YT Shorts + "
    "1:1 для ленты + 4:5 для карусели IG.",
    "معظم أدوات القص تتطلب توسيط العروس والعريس يدويًا في كل واحدة من أكثر من 100 صورة زفاف. "
    "القص في WeddingAI.video يستخدم افتراضيًا انزياحًا خارج المركز: يزيح نافذة القص 60% لأسفل "
    "في المصادر الأفقية، حيث يقف العروسان عادةً، فيبقى الزوجان داخل الإطار بدلًا من أن يُقتطعا؛ "
    "ويمكنك التبديل إلى كشف وجوه حقيقي يتم على جهازك عندما تريد أن يتبع الإطار الوجوه الفعلية. "
    "يُصدِّر 9:16 + 1:1 + 4:5 في دفعة واحدة. والأهم أن الدفعة نفسها تدخل تصدير الفيديو الذكي "
    "الجاهز لـ IG: Reels عمودية + YT Shorts أفقية + 1:1 للخلاصة + 4:5 لكاروسيل IG.",
    "เครื่องมือตัดภาพส่วนใหญ่ต้องให้คุณจัดวางใบหน้าเจ้าบ่าวด้วยมือในแต่ละรูปจากกว่า 100 ภาพแต่งงาน "
    "เครื่องมือของ WeddingAI.video ใช้ออฟเซ็นเตอร์ไบแอสเป็นค่าเริ่มต้น โดยเลื่อนกรอบตัดลง 60% ในภาพแนวนอน "
    "(ตรงที่คู่บ่าสามักยืนอยู่) เพื่อให้คู่บ่าสาอยู่ในกรอบไม่ถูกตัดออก และคุณยังสลับไปใช้การตรวจจับ"
    "ใบหน้าจริงบนเครื่องตัวเองได้ เมื่ออยากให้กรอบตามใบหน้าจริง รองรับ 9:16 + 1:1 + 4:5 ในการส่งออกครั้งเดียว "
    "และชุดภาพเดียวกันนี้ยังป้อนเข้าการส่งออกสำหรับ IG ของวิดีโอ AI: Reels แนวตั้ง + YT Shorts แนวนอน + "
    "1:1 สำหรับฟีด + 4:5 สำหรับแครอเซลล์ IG",
    "ज़्यादातर क्रॉप टूल्स के लिए आपको 100+ शादी की तस्वीरों में हर एक में दूल्हे-दुल्हन को खुद सेंटर करना "
    "पड़ता है। WeddingAI.video की क्रॉप डिफ़ॉल्ट रूप से ऑफ-सेंटर बायस का उपयोग करती है — लैंडस्केप "
    "स्रोतों में क्रॉप विंडो को 60% नीचे खिसकाती है, यानी जहाँ जोड़े आमतौर पर खड़े होते हैं, ताकि जोड़ा "
    "फ़्रेम में बना रहे और कटे न जाएँ — और जब आप चाहें कि फ़्रेम असली चेहरों का पीछा करे, तो आप अपने "
    "ही डिवाइस पर चलने वाले असली चेहरा-पहचान पर स्विच कर सकते हैं। यह 9:16 + 1:1 + 4:5 एक बार में "
    "एक्सपोर्ट करता है। और यही बैच AI वीडियो के IG-रेडी एक्सपोर्ट में भी जाता है — वर्टिकल Reels + "
    "होरिज़ॉन्टल YT Shorts + 1:1 फ़ीड + 4:5 IG कैरोसेल।",
)

add(
    P + "td_text.ai_facecentered_auto.9c0d1e2f",
    "<strong>Off-center bias + on-device face detection</strong>",
    "<strong>中心偏移 + 本地人脸检测</strong>",
    "<strong>Sesgo fuera del centro + detección de rostros en tu dispositivo</strong>",
    "<strong>Décalage hors centre + détection des visages sur l’appareil</strong>",
    "<strong>Off-Center-Versatz + Gesichtserkennung auf dem Gerät</strong>",
    "<strong>Viés fora do centro + detecção de rostos no seu dispositivo</strong>",
    "<strong>オフセンターバイアス + デバイス上の顔検出</strong>",
    "<strong>Смещение от центра + распознавание лиц на устройстве</strong>",
    "<strong>انزياح خارج المركز + كشف الوجوه على جهازك</strong>",
    "<strong>ออฟเซ็นเตอร์ไบแอส + ตรวจจับใบหน้าบนเครื่อง</strong>",
    "<strong>ऑफ-सेंटर बायस + डिवाइस पर चेहरा पहचान</strong>",
)

# --- the runtime strings of the status line --------------------------------
#
# They live in the "tools.copy" namespace because the middleware hands that
# namespace to the client as window.__WA_I18N__.

add(
    "tools.copy.cropFaceOff.1a2b3c4d",
    "Face detection is off. Switch it on to frame the couple automatically.",
    "人脸检测未开启。打开它即可自动为新人取景。",
    "La detección de rostros está desactivada. Actívala para encuadrar a la "
    "pareja automáticamente.",
    "La détection des visages est désactivée. Activez-la pour cadrer "
    "automatiquement le couple.",
    "Die Gesichtserkennung ist aus. Schalten Sie sie ein, um das Paar automatisch zu rahmen.",
    "A detecção de rostos está desligada. Ligue-a para enquadrar o casal "
    "automaticamente.",
    "顔検出はオフです。オンにすると新人を自動でフレーミングします。",
    "Распознавание лиц выключено. Включите его, чтобы автоматически выбрать кадр с парой.",
    "كشف الوجوه مُعطَّل. فعّله لتأطير العروسين تلقائيًا.",
    "การตรวจจับใบหน้าปิดอยู่ เปิดใช้งานเพื่อจัดเฟรมคู่บ่าสาอัตโนมัติ",
    "चेहरा पहचान बंद है। जोड़े को अपने आप फ़्रेम में लाने के लिए इसे चालू करें।",
)

add(
    "tools.copy.cropFaceLoading.2b3c4d5e",
    "Loading the face detector…",
    "正在加载人脸检测模型…",
    "Cargando el detector de rostros…",
    "Chargement du détecteur de visages…",
    "Gesichtserkennung wird geladen…",
    "Carregando o detector de rostos…",
    "顔検出モデルを読み込み中…",
    "Загружается детектор лиц…",
    "جارٍ تحميل كاشف الوجوه…",
    "กำลังโหลดตัวตรวจจับใบหน้า…",
    "चेहरा डिटेक्टर लोड हो रहा है…",
)

add(
    "tools.copy.cropFaceReady.3c4d5e6f",
    "Face detector ready — it runs on your device, your photos are never uploaded.",
    "人脸检测模型已就绪——它在你自己的设备上运行，照片永远不会被上传。",
    "Detector de rostros listo: se ejecuta en tu dispositivo, tus fotos nunca se suben.",
    "Détecteur de visages prêt — il s’exécute sur votre appareil, vos "
    "photos ne sont jamais envoyées.",
    "Gesichtserkennung bereit – sie läuft auf Ihrem Gerät, Ihre Fotos werden nie "
    "hochgeladen.",
    "Detector de rostos pronto — ele roda no seu dispositivo, suas fotos nunca são "
    "enviadas.",
    "顔検出の準備ができました — お使いのデバイス上で動作し、写真がアップロードされることは"
    "ありません。",
    "Детектор лиц готов — он работает на вашем устройстве, фотографии никуда не "
    "отправляются.",
    "كاشف الوجوه جاهز — يعمل على جهازك، وصورك لا تُرفع أبدًا.",
    "ตัวตรวจจับใบหน้าพร้อมแล้ว — ทำงานบนเครื่องของคุณ รูปของคุณจะไม่ถูกอัปโหลด",
    "चेहरा डिटेक्टर तैयार है — यह आपके डिवाइस पर चलता है, आपकी फ़ोटो कभी अपलोड नहीं होतीं।",
)

add(
    "tools.copy.cropFaceFound.4d5e6f70",
    "{n} face(s) found — the crop frame keeps them all inside.",
    "找到 {n} 张人脸——裁剪框会把它们全部留在画面里。",
    "{n} rostro(s) encontrados: el marco de recorte los mantiene todos dentro.",
    "{n} visage(s) détecté(s) — le cadre de recadrage les garde tous à "
    "l’intérieur.",
    "{n} Gesicht/Gesichter gefunden – der Beschnittungsrahmen hält sie alle darin.",
    "{n} rosto(s) encontrado(s) — a moldura de corte mantém todos dentro.",
    "{n} 件の顔を検出しました — トリミング枠がすべてを内側に収めます。",
    "Найдено лиц: {n} — рамка кадрирования удержит их все внутри.",
    "تم العثور على {n} وجه — إطار القص يبقيها كلها في الداخل.",
    "พบ {n} ใบหน้า — กรอบตัดจะเก็บทุกใบหน้าไว้ภายใน",
    "{n} चेहरे मिले — क्रॉप फ़्रेम उन सभी को अंदर ही रखेगा।",
)

add(
    "tools.copy.cropFaceNone.5e6f7081",
    "No face found in this photo — keeping the off-center bias instead.",
    "这张照片里没有找到人脸——继续沿用中心偏移。",
    "No se encontró ningún rostro en esta foto: se mantiene el sesgo fuera del centro.",
    "Aucun visage détecté sur cette photo — le décalage hors centre est "
    "conservé.",
    "In diesem Foto wurde kein Gesicht gefunden – der Off-Center-Versatz bleibt aktiv.",
    "Nenhum rosto encontrado nesta foto — o viés fora do centro é mantido.",
    "この写真では顔が見つかりませんでした — オフセンターのバイアスをそのまま使います。",
    "На этом фото лиц не найдено — остаётся смещение от центра.",
    "لم يُعثر على وجه في هذه الصورة — يبقى الانزياح خارج المركز.",
    "ไม่พบใบหน้าในรูปนี้ — ยังคงใช้ออฟเซ็นเตอร์ไบแอสเดิม",
    "इस फ़ोटो में कोई चेहरा नहीं मिला — ऑफ-सेंटर बायस ही बनी रहेगी।",
)

add(
    "tools.copy.cropFaceFailed.6f708192",
    "Face detection is not available on this device — keeping the off-center bias "
    "instead.",
    "这台设备无法使用人脸检测——继续沿用中心偏移。",
    "La detección de rostros no está disponible en este dispositivo: se "
    "mantiene el sesgo fuera del centro.",
    "La détection des visages n’est pas disponible sur cet appareil — le "
    "décalage hors centre est conservé.",
    "Auf diesem Gerät ist keine Gesichtserkennung verfügbar – der "
    "Off-Center-Versatz bleibt aktiv.",
    "A detecção de rostos não está disponível neste "
    "dispositivo — o viés fora do centro é mantido.",
    "この端末では顔検出を使えません — オフセンターのバイアスをそのまま使います。",
    "Распознавание лиц на этом устройстве недоступно — остаётся смещение от центра.",
    "كشف الوجوه غير متاح على هذا الجهاز — يبقى الانزياح خارج المركز.",
    "อุปกรณ์นี้ไม่รองรับการตรวจจับใบหน้า — ยังคงใช้ออฟเซ็นเตอร์ไบแอสเดิม",
    "इस डिवाइस पर चेहरा पहचान उपलब्ध नहीं है — ऑफ-सेंटर बायस ही बनी रहेगी।",
)

# --- the crop stage hint ---------------------------------------------------
#
# It said "the automatic centre crop", which stopped being true when the
# off-center bias and then the face detector arrived.

add(
    "tools.copy.cropStageHint.zzzzzz6c02",
    "Drag the corners to frame the shot. Photos you leave untouched keep the "
    "automatic crop — the off-center bias, or the faces when Face-aware framing "
    "is on.",
    "拖动四角来取景。没有手动调整过的照片会保留自动裁剪——默认是中心偏移，打开“人脸感知取景”后"
    "则跟着人脸走。",
    "Arrastra las esquinas para encuadrar. Las fotos que no toques conservan el recorte "
    "automático: el sesgo fuera del centro, o los rostros si el encuadre con "
    "detección está activo.",
    "Faites glisser les coins pour cadrer. Les photos que vous ne touchez pas conservent "
    "le recadrage automatique : le décalage hors centre, ou les visages si le "
    "cadrage avec détection est activé.",
    "Ziehen Sie die Ecken, um den Ausschnitt zu setzen. Fotos, die Sie nicht anfassen, "
    "behalten den automatischen Beschnitt – den Off-Center-Versatz, oder die "
    "Gesichter, wenn die gesichtsbewusste Rahmensetzung aktiv ist.",
    "Arraste os cantos para enquadrar. As fotos que você não mexer mantêm o "
    "corte automático — o viés fora do centro, ou os rostos quando o "
    "enquadramento com detecção está ligado.",
    "四隅をドラッグして画枠を決めます。触らなかった写真は自動トリミングのまま — オフセンターの"
    "バイアス、または顔認識トリミングをオンにしている場合は顔に追従します。",
    "Перетащите углы, чтобы задать кадр. Фотографии, которых вы не касались, сохраняют "
    "автоматическое кадрирование — смещение от центра, а при включённом кадрировании по "
    "лицам — следование за лицами.",
    "اسحب الزوايا لتحديد الإطار. الصور التي لا تلمسها تحتفظ بالقص التلقائي — انزياح خارج "
    "المركز، أو الوجوه عند تفعيل التأطير الواعي بالوجوه.",
    "ลากมุมเพื่อจัดเฟรม รูปที่คุณไม่ได้แตะจะยังคงใช้การตัดอัตโนมัติ — ออฟเซ็นเตอร์ไบแอส "
    "หรือตามใบหน้าเมื่อเปิดการตัดโดยรู้หน้า",
    "फ़्रेम तय करने के लिए कोने खींचें। जिन फ़ोटो को आप छुएँ नहीं, वे स्वचालित क्रॉप बनाए रहती हैं "
    "— ऑफ-सेंटर बायस, या चेहरा-आधारित फ़्रेमिंग चालू होने पर चेहरों के अनुसार।",
)


def main():
    langs = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
    for key, values in KEYS.items():
        missing = [l for l in langs if not values.get(l)]
        if missing:
            raise SystemExit("[FAIL] %s has no translation for %s" % (key, missing))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(KEYS, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, OUT)

    print("keys: %d   languages: %d" % (len(KEYS), len(langs)))
    print("written: %s" % OUT.relative_to(ROOT))
    print("\nNow run:")
    print("  python scripts/add-tool-ui-keys.py %s" % OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
