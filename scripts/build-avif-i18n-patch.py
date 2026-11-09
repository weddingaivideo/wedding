#!/usr/bin/env python3
"""
Build the i18n patch for §2.12 (AVIF + lossless WebP output).

The format control now offers five formats, and the prose has to say so:
"outputs JPG, WebP, or PNG" would become a false promise the moment AVIF
and lossless WebP are on the menu.

For the three option keys that already exist in seven dictionaries, the
existing translation is kept verbatim - only the four languages that never
had them (en, zh, pt, ru) get a new value, and those values are the text
the pages already carried inline.

Usage:  python scripts/build-avif-i18n-patch.py <out.json>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

P = "tools.compress-wedding-photos."
K_LABEL = P + "label_text.output_format.a4b5c6d7"
K_JPG = P + "option_text.c06b8c68"
K_WEBP = P + "option_text.1724a385"
K_PNG = P + "option_text.babb5986"
K_AVIF = P + "option_text.b6c7d8e9"
K_LOSSLESS = P + "option_text.c7d8e9f0"
K_DOES = P + "p_text.what_it_does.7h2k4m6n"
K_DOES_NOT = P + "p_text.what_it_does_not.8j3l5n7p"

# --- the label -------------------------------------------------------------
LABEL = {
    "en": "Output format",
    "zh": "输出格式",
    "es": "Formato de salida",
    "fr": "Format de sortie",
    "de": "Ausgabeformat",
    "pt": "Formato de saída",
    "ja": "出力形式",
    "ru": "Формат вывода",
    "ar": "صيغة الإخراج",
    "th": "รูปแบบไฟล์ผลลัพธ์",
    "hi": "आउटपुट फ़ॉर्मेट",
}

# --- the three options that already existed -------------------------------
# (the values the pages carried inline before they were dictionary-bound)
EXISTING = {
    K_JPG: {
        "en": "JPG (smaller, recommended for sharing)",
        "zh": "JPG（体积更小，推荐用于分享）",
        "pt": "JPG (menor, recomendado para compartilhar)",
        "ru": "JPG (компактнее, рекомендуется для отправки)",
    },
    K_WEBP: {
        "en": "WebP (smaller, modern browsers)",
        "zh": "WebP（体积更小，现代浏览器）",
        "pt": "WebP (menor, navegadores modernos)",
        "ru": "WebP (компактнее, современные браузеры)",
    },
    K_PNG: {
        "en": "PNG (lossless, biggest files)",
        "zh": "PNG（无损，文件最大）",
        "pt": "PNG (sem perda, arquivos maiores)",
        "ru": "PNG (без потерь, самые большие файлы)",
    },
}

# --- the two new options --------------------------------------------------
AVIF = {
    "en": "AVIF (smallest files — downloads a 3.4 MB encoder once)",
    "zh": "AVIF（文件最小 —— 需一次性下载 3.4 MB 编码器）",
    "es": "AVIF (los archivos más pequeños; descarga un codificador de 3,4 MB una vez)",
    "fr": "AVIF (fichiers les plus petits ; télécharge un encodeur de 3,4 Mo une fois)",
    "de": "AVIF (kleinste Dateien – lädt einmalig einen 3,4-MB-Encoder herunter)",
    "pt": "AVIF (os menores arquivos — baixa um codificador de 3,4 MB uma vez)",
    "ja": "AVIF（最小ファイル —— 3.4 MB のエンコーダーを一度だけダウンロードします）",
    "ru": "AVIF (самые маленькие файлы — один раз загружает кодировщик 3,4 МБ)",
    "ar": "AVIF (أصغر الملفات — ينزّل مُرمِّزًا بحجم 3.4 ميغابايت مرة واحدة)",
    "th": "AVIF (ไฟล์เล็กที่สุด — ดาวน์โหลดตัวเข้ารหัส 3.4 MB ครั้งเดียว)",
    "hi": "AVIF (सबसे छोटी फ़ाइलें — एक बार 3.4 MB एन्कोडर डाउनलोड होता है)",
}

LOSSLESS = {
    "en": "WebP lossless (for graphics — a photo gets bigger)",
    "zh": "WebP 无损（适合图形 —— 照片反而会变大）",
    "es": "WebP sin pérdida (para gráficos: una foto pesa más)",
    "fr": "WebP sans perte (pour les graphismes : une photo devient plus lourde)",
    "de": "WebP verlustfrei (für Grafiken – ein Foto wird größer)",
    "pt": "WebP sem perdas (para gráficos — uma foto fica maior)",
    "ja": "WebP ロスレス（グラフィック向け — 写真は逆に大きくなります）",
    "ru": "WebP без потерь (для графики — фотография станет больше)",
    "ar": "WebP بلا فقد (للرسوم — الصورة تصبح أكبر)",
    "th": "WebP แบบไม่สูญเสีย (สำหรับกราฟิก — ภาพถ่ายจะใหญ่ขึ้น)",
    "hi": "WebP लॉसलेस (ग्राफ़िक्स के लिए — फ़ोटो बड़ी हो जाती है)",
}

# --- the prose -------------------------------------------------------------
DOES = {
    "en": ("The compressor uses the browser's built-in <strong>Canvas API</strong> to re-encode each "
           "dropped image at your chosen quality. It supports JPG, PNG, and WebP input and outputs "
           "JPG, WebP, PNG, <strong>AVIF</strong> or <strong>lossless WebP</strong>. Optional "
           "\"Max longest edge\" caps the longest side — handy if you know the destination's size "
           "limit. A <strong>target size</strong> in MB replaces the quality slider entirely: the tool "
           "searches for the highest quality that still fits under it, and scales the photo down only "
           "when even the lowest quality is too big. AVIF is the smallest of the five, but no browser "
           "can encode it on its own, so the first time you pick it a 3.4 MB encoder is downloaded once "
           "and then stays in your browser's cache. Lossless WebP is the right choice for flat graphics "
           "— on a photograph it produces a bigger file, not a smaller one. Either way it all runs on "
           "your device; nothing is uploaded."),
    "zh": ("压缩器用浏览器内置的 <strong>Canvas API</strong> 按你选择的画质重新编码每一张拖入的图片。"
           "它支持 JPG、PNG、WebP 输入，输出 JPG、WebP、PNG、<strong>AVIF</strong> 或 "
           "<strong>WebP 无损</strong>。可选的「最长边上限」会限制最长边——知道目标平台的尺寸限制时很有用。"
           "<strong>目标体积</strong>（MB）会完全取代质量滑块：工具会自动搜索仍能塞进这个体积的最高画质，"
           "只有当连最低画质都超限时才会缩小照片。AVIF 是这五种里最小的，但没有任何浏览器能自己编码它，"
           "所以第一次选择它时会一次性下载 3.4 MB 的编码器，之后就留在你的浏览器缓存里。"
           "WebP 无损适合平面图形——用在照片上反而会生成更大的文件。"
           "无论选哪一种，处理都仍然在你的设备上完成，不会上传任何东西。"),
    "es": ("El compresor usa el <strong>Canvas API</strong> integrado del navegador para recodificar "
           "cada imagen soltada con la calidad que elijas. Admite entradas JPG, PNG y WebP y produce "
           "salidas JPG, WebP, PNG, <strong>AVIF</strong> o <strong>WebP sin pérdida</strong>. La "
           "opción opcional \"Borde máximo\" limita el lado más largo: útil cuando conoces el límite de "
           "tamaño del destino. Un <strong>tamaño objetivo</strong> en MB sustituye por completo al "
           "control de calidad: la herramienta busca la calidad más alta que aún cabe dentro de él y "
           "sólo reduce la foto cuando ni la calidad más baja cabe. AVIF es el más pequeño de los "
           "cinco, pero ningún navegador puede codificarlo por sí solo, así que la primera vez que lo "
           "eliges se descarga un codificador de 3,4 MB una vez y luego se queda en la caché de tu "
           "navegador. El WebP sin pérdida es la opción para gráficos planos: sobre una photographía "
           "produce un archivo más grande, no más pequeño. En cualquier caso todo se ejecuta en tu "
           "dispositivo; no se sube nada."),
    "fr": ("Le compresseur utilise le <strong>Canvas API</strong> intégré au navigateur pour réencoder "
           "chaque image déposée avec la qualité que vous choisissez. Il accepte les entrées JPG, PNG et "
           "WebP et produit du JPG, du WebP, du PNG, de l'<strong>AVIF</strong> ou du "
           "<strong>WebP sans perte</strong>. L'option facultative « Plus long côté » limite le côté le "
           "plus long : utile si vous connaissez la limite de taille de la destination. Une "
           "<strong>taille cible</strong> en Mo remplace complètement le curseur de qualité : l'outil "
           "cherche la qualité la plus élevée qui tient encore en dessous, et ne réduit la photo que "
           "si même la qualité la plus basse est trop grande. L'AVIF est le plus petit des cinq, mais "
           "aucun navigateur ne sait l'encode tout seul : la première fois que vous le choisissez, un "
           "encodeur de 3,4 Mo est téléchargé une fois, puis reste dans le cache de votre navigateur. "
           "Le WebP sans perte convient aux graphics plats : sur une photo, il produit un fichier plus "
           "gros, pas plus petit. Dans tous les cas, tout se passe sur votre appareil ; rien n'est "
           "téléversé."),
    "de": ("Der Kompressor verwendet die integrierte <strong>Canvas API</strong> des Browsers, um jedes "
           "abgelegte Bild mit der von dir gewählten Qualität neu zu kodieren. Er nimmt JPG, PNG und "
           "WebP als Eingabe entgegen und erzeugt JPG, WebP, PNG, <strong>AVIF</strong> oder "
           "<strong>verlustfreies WebP</strong>. Die optionale Einstellung „Längste Kante“ begrenzt die "
           "längste Seite — praktisch, wenn du die Größengrenze des Ziels kennst. Eine "
           "<strong>Zielgröße</strong> in MB ersetzt den Qualitätsregler vollständig: Das Werkzeug sucht "
           "die höchste Qualität, die noch darunter passt, und verkleinert das Foto nur dann, wenn "
           "selbst die niedrigste Qualität noch zu groß ist. AVIF ist die kleinste der fünf Varianten, "
           "aber kein Browser kann sie selbst encodieren: Beim ersten Mal wird deshalb ein 3,4-MB-"
           "Encoder einmalig geladen und bleibt danach im Browser-Cache. Verlustfreies WebP ist die "
           "richtige Wahl für flache Grafiken — bei einem Foto erzeugt es eine größere, keine kleinere "
           "Datei. Alles läuft in jedem Fall auf deinem Gerät; es wird nichts hochgeladen."),
    "pt": ("O compressor usa a <strong>Canvas API</strong> integrada do navegador para recodificar "
           "cada imagem solta com a qualidade escolhida. Aceita entradas JPG, PNG e WebP e produz JPG, "
           "WebP, PNG, <strong>AVIF</strong> ou <strong>WebP sem perdas</strong>. A opção opcional "
           "\"Maior lado\" limita o lado mais comprido — útil se você conhece o limite de tamanho do "
           "destino. Um <strong>tamanho alvo</strong> em MB substitui completamente o controle de "
           "qualidade: a ferramenta procura a maior qualidade que ainda cabe abaixo dele e só reduz a "
           "foto quando até a menor qualidade é grande demais. O AVIF é o menor dos cinco, mas nenhum "
           "navegador consegue codificá-lo sozinho, então na primeira vez que você o escolher um "
           "codificador de 3,4 MB é baixado uma única vez e fica no cache do navegador. O WebP sem "
           "perdas é a escolha para gráficos chapados — em uma fotografia ele gera um arquivo maior, "
           "não menor. Em qualquer caso tudo roda no seu dispositivo; nada é enviado."),
    "ja": ("コンプレッサはブラウザの標準の <strong>Canvas API</strong> を使い、ドロップした画像を選んだ画質で"
           "再エンコードします。入力は JPG・PNG・WebP、出力は JPG・WebP・PNG・<strong>AVIF</strong>・"
           "<strong>WebP ロスレス</strong>。任意の「最長辺」は長い辺を制限するので、配信先のサイズ制限が"
           "分かっているときに便利です。<strong>目標サイズ</strong>（MB）を指定すると画質スライダーは"
           "完全に置き換わり、その下に収まる最高画質を探索します。最も低い画質でも収まらないときだけ"
           "写真を縮小します。AVIF は 5 つのうち最も小さいですが、どのブラウザも自前でエンコードできず、"
           "最初に選んだときだけ 3.4 MB のエンコーダーが一度ダウンロードされ、その後はブラウザのキャッシュに"
           "残ります。WebP ロスレスは均一なグラフィック向きです。写真に使うと小さくなるのではなく"
           "大きくなります。いずれの場合も処理はすべてお使いの端末上で行われ、アップロードはされません。"),
    "ru": ("Компрессор использует встроенный в браузер <strong>Canvas API</strong>, чтобы перекодировать "
           "каждое перетащенное изображение с выбранным качеством. На вход принимаются JPG, PNG и WebP, "
           "на выход — JPG, WebP, PNG, <strong>AVIF</strong> или <strong>WebP без потерь</strong>. "
           "Необязательная настройка «Максимальная длинная сторона» ограничивает длинную сторону — "
           "удобно, когда известен лимит размера получателя. <strong>Целевой размер</strong> в МБ "
           "полностью заменяет ползунок качества: инструмент ищет самое высокое качество, которое ещё "
           "помещается в этот размер, и уменьшает фотографию только тогда, когда даже минимальное "
           "качество слишком велико. AVIF — самый маленький из пяти вариантов, но ни один браузер не "
           "умеет кодировать его сам, поэтому при первом выборе один раз загружается кодировщик 3,4 МБ и "
           "дальше остаётся в кэше браузера. WebP без потерь — правильный выбор для плоских "
           "изображений: на фотографии он даёт файл БОЛЬШЕ, а не меньше. В любом случае всё считается "
           "на вашем устройстве; ничего не загружается."),
    "ar": ("يستخدم الضاغط <strong>Canvas API</strong> المدمجة في المتصفح لإعادة ترميز كل صورة تُفلت "
           "بالجودة التي تختارها. يقبل ملفات JPG وPNG وWebP كمدخلات، ويُخرج JPG أو WebP أو PNG أو "
           "<strong>AVIF</strong> أو <strong>WebP بلا فقد</strong>. الخيار الاختياري «أطول ضلع» يحدّ "
           "الضلع الأطول — مفيد إذا كنت تعرف حد الحجم عند الوجهة. حجم الهدف <strong>بالميغابايت</strong> "
           "يحلّ محل شريط الجودة تمامًا: تبحث الأداة عن أعلى جودة ما زالت تتّسع تحته، ولا تصغّر "
           "الصورة إلا عندما لا تتّسع حتى أدنى جودة. ملف AVIF هو الأصغر من الخمسة، لكن لا يوجد متصفح "
           "يستطيع ترميزه وحده، لذا عند اختياره لأول مرة يُنزَّل مُرمِّز بحجم 3.4 ميغابايت مرة واحدة ثم "
           "يبقى في ذاكرة المتصفح المؤقتة. أما WebP بلا فقد فهو للرسوم المسطّحة — وعلى الصورة "
           "الفوتوغرافية ينتج ملفًا أكبر لا أصغر. وفي كل الأحوال يبقى كل شيء يعمل على جهازك؛ لا يتم "
           "رفع أي شيء."),
    "th": ("ตัวบีบอัดใช้ <strong>Canvas API</strong> ที่มาพร้อมเบราว์เซอร์เพื่อเข้ารหัสรูปภาพทุกใบที่คุณลาก "
           "เข้ามาใหม่ตามคุณภาพที่เลือก รองรับไฟล์นำเข้า JPG, PNG และ WebP และส่งออกได้เป็น JPG, WebP, "
           "PNG, <strong>AVIF</strong> หรือ <strong>WebP แบบไม่สูญเสีย</strong> ตัวเลือก \"ขอบยาวที่สุด\" "
           "จำกัดขอบที่ยาวที่สุด — มีประโยชน์เมื่อคุณรู้ขนาดสูงสุดของปลายทาง การกำหนด"
           "<strong>ขนาดเป้าหมาย</strong> เป็น MB จะแทนที่แถบคุณภาพทั้งหมด เครื่องมือจะหาคุณภาพสูงสุดที่ยัง "
           "พอดีขนาด และจะย่อภาพลงก็ต่อเมื่อแม้แต่คุณภาพต่ำสุดก็ยังใหญ่เกินไป AVIF เล็กที่สุดในห้าแบบ "
           "แต่ไม่มีเบราว์เซอร์ใดเข้ารหัสมันเองได้ เมื่อเลือกครั้งแรกจึงมีการดาวน์โหลดตัวเข้ารหัสขนาด "
           "3.4 MB เพียงครั้งเดียว แล้วอยู่ในแคชของเบราว์เซอร์ของคุณ ส่วน WebP แบบไม่สูญเสียเหมาะกับ "
           "ภาพกราฟิกที่สีเรียบ บนภาพถ่ายจะได้ไฟล์ที่ใหญ่กว่าไม่ใช่เล็กกว่า ไม่ว่าจะเลือกแบบใด "
           "การประมวลผลยังคงทำงานทั้งหมดบนอุปกรณ์ของคุณ ไม่มีการอัปโหลด"),
    "hi": ("कंप्रेसर आपकी चुनी हुई क्वालिटी पर हर गिराई गई इमेज को दोबारा एन्कोड करने के लिए ब्राउज़र का "
           "<strong>Canvas API</strong> इस्तेमाल करता है। इनपुट में JPG, PNG और WebP चलते हैं, और आउटपुट "
           "में JPG, WebP, PNG, <strong>AVIF</strong> या <strong>लॉसलेस WebP</strong>। वैकल्पिक "
           "\"सबसे लंबा किनारा\" सबसे लंबी भुजा को सीमित करता है — जब आपको डेस्टिनेशन का साइज़ लिमिट पता हो तब "
           "काम आता है। <strong>MB में लक्ष्य आकार</strong> क्वालिटी स्लाइडर की जगह पूरी तरह ले लेता है: "
           "टूल उसके नीचे आने वाली सबसे ऊँची क्वालिटी खोजता है, और फ़ोटो को तभी छोटा करता है जब सबसे कम "
           "क्वालिटी भी बहुत बड़ी हो। पाँच में AVIF सबसे छोटा है, पर कोई ब्राउज़र इसे खुद एन्कोड नहीं कर सकता, "
           "इसलिए पहली बार चुनने पर 3.4 MB का एन्कोडर एक बार डाउनलोड होता है और फिर ब्राउज़र की कैश में रहता "
           "है। लॉसलेस WebP सपाट ग्राफ़िक्स के लिए है — फ़ोटो पर यह छोटी फ़ाइल नहीं, बड़ी फ़ाइल बनाता है। "
           "हर स्थिति में सब कुछ आपके डिवाइस पर ही चलता है; कुछ भी अपलोड नहीं होता।"),
}

DOES_NOT = {
    "en": ("What it does not do: it cannot reach a target smaller than the photo can be, and it cannot "
           "write PNG metadata. EXIF is copied over from the original file — camera, lens, shooting date "
           "— so a compressed photo still says when and where it was taken. The orientation is "
           "deliberately reset, because the pixels are already upright: keeping the original rotation "
           "flag would make every viewer turn the photo sideways. The EXIF block travels with the JPG "
           "only — AVIF and WebP outputs are written without it."),
    "zh": ("它做不到的事：无法达到比照片本身更小的目标体积，也无法写入 PNG 元数据。EXIF 会从原文件复制过来"
           "——相机、镜头、拍摄日期——所以压缩后的照片仍然记录着它是在何时何地拍摄的。方向标记会被刻意重置，"
           "因为像素本身已经是正的：保留原来的旋转标记会让每个查看器把照片再转一次。EXIF 只会随 JPG 一起保留；"
           "AVIF 和 WebP 输出不写入这些信息。"),
    "es": ("Lo que no hace: no puede alcanzar un objetivo más pequeño que la propia foto, ni escribir "
           "metadatos PNG. El EXIF se copia del archivo original —cámara, objetivo, fecha de disparo— para "
           "que una foto comprimida siga diciendo cuándo y dónde se hizo. La orientación se reinicia a "
           "propósito, porque los píxeles ya están verticales: mantener la marca de rotación original "
           "haría que cualquier visor girara la foto de lado. El bloque EXIF viaja solo con el JPG: las "
           "salidas AVIF y WebP se escriben sin él."),
    "fr": ("Ce qu'il ne fait pas : atteindre une cible plus petite que la photo elle-même, ni écrire des "
           "métadonnées PNG. L'EXIF est recopié depuis le fichier d'origine — appareil, objectif, date de "
           "prise de vue — pour qu'une photo compressée dise toujours quand et où elle a été prise. "
           "L'orientation est réinitialisée volontairement, parce que les pixels sont déjà droits : "
           "garder l'indicateur de rotation d'origine ferait pivoter la photo de côté dans tous les "
           "visionneuses. Le bloc EXIF n accompanye que le JPG : les sorties AVIF et WebP sont écrites "
           "sans lui."),
    "de": ("Was es nicht kann: ein Ziel erreichen, das kleiner ist als das Foto selbst, und keine "
           "PNG-Metadaten schreiben. Die EXIF-Daten werden aus der Originaldatei übernommen — Kamera, "
           "Objektiv, Aufnahmedatum —, damit ein komprimiertes Foto weiterhin sagt, wann und wo es "
           "entstanden ist. Die Ausrichtung wird bewusst zurückgesetzt, weil die Pixel bereits gerade "
           "stehen: Das Original-Rotationsflag zu behalten würde jedes Anzeigeprogramm das Foto um 90 "
           "Grad drehen. Der EXIF-Block wandert nur mit dem JPG mit — AVIF- und WebP-Ausgaben werden ohne "
           "ihn geschrieben."),
    "pt": ("O que ele não faz: atingir um alvo menor do que a própria foto, nem escrever metadados PNG. "
           "O EXIF é copiado do arquivo original — câmera, lente, data da foto — para que uma foto "
           "comprimida ainda diga quando e onde foi tirada. A orientação é redefinida de propósito, "
           "porque os pixels já estão na vertical: manter a marca de rotação original faria qualquer "
           "visualizador virar a foto de lado. O bloco EXIF acompanha apenas o JPG — as saídas AVIF e "
           "WebP são gravadas sem ele."),
    "ja": ("できないこと：写真そのものの大きさより小さい目標には到達できないこと、そして PNG のメタデータ"
           "を書き込めないこと。EXIF は元ファイルから引き継がれます——カメラ、レンズ、撮影日——そのため"
           "压缩后的照片にも、いつどこで撮ったかがちゃんと残ります。方向は意図的にリセットされます。"
           "ピクセルはすでに正立しているためです。元の回転フラグを残すと、どのビューアも写真を横に"
           "倒してしまいます。EXIF ブロックは JPG にだけ付きます。AVIF と WebP の出力には書き込まれません。"),
    "ru": ("Чего он не делает: не может достичь цели меньше самого снимка и не пишет метаданные PNG. "
           "EXIF переносится из исходного файла — камера, объектив, дата съёмки —, поэтому сжатое фото "
           "по-прежнему говорит, когда и где оно сделано. Ориентация намеренно сбрасывается, потому что "
           "пиксели уже стоят прямо: если сохранить исходный флаг поворота, любой просмотрщик повернёт "
           "фото на бок. Блок EXIF идёт только с JPG — вывод в AVIF и WebP записывается без него."),
    "ar": ("ما لا يفعله: لا يمكنه بلوغ حجم أصغر من الصورة نفسها، ولا يكتب بيانات PNG الوصفية. تُنسخ "
           "بيانات EXIF من الملف الأصلي — الكاميرا والعدسة وتاريخ التصوير — لتبقى الصورة المضغوطة تقول "
           "متى وأين التُقطت. وتُصفَّر زاوية الالتفاف عمدًا، لأن البكسلات قائمة بالفعل: الإبقاء على "
           "علامة الالتفاف الأصلية يجعل كل عارض يدوّر الصورة على جانبها. كتلة EXIF ترافق ملف JPG فقط — "
           "أما مخرجات AVIF وWebP فتُكتب بدونها."),
    "th": ("สิ่งที่มันทำไม่ได้: ไปถึงขนาดเป้าหมายที่เล็กกว่าตัวภาพเองไม่ได้ และเขียนเมทาดาทา PNG ไม่ได้ "
           "ข้อมูล EXIF ถูกคัดลอกมาจากไฟล์ต้นฉบับ — กล้อง เลนส์ วันที่ถ่าย — เพื่อให้ภาพที่บีบอัดแล้วยังบอกได้ว่า"
           "ถ่ายเมื่อไรและที่ไหน การหมุนถูกรีเซ็ตโดยเจตนา เพราะพิกเซลเอยู่ตั้งตรงอยู่แล้ว: การเก็บแฟล็กการหมุน"
           "เดิมไว้จะทำให้โปรแกรมดูภาพทุกตัวหมุนภาพตะแคง บล็อก EXIF ไปกับไฟล์ JPG เท่านั้น ผลลัพธ์แบบ AVIF "
           "และ WebP จะถูกเขียนโดยไม่มีข้อมูลนี้"),
    "hi": ("यह नहीं कर पाता: फ़ोटो के आकार से छोटा लक्ष्य तक नहीं पहुँच सकता, और PNG मेटाडेटा नहीं लिख सकता। "
           "EXIF मूल फ़ाइल से कॉपी हो जाता है — कैमरा, लेंस, शूट की तारीख़ — इसलिए कंप्रेस की गई फ़ोटो भी बताती है "
           "कि वह कब और कहाँ ली गई थी। ओरिएंटेशन जानबूझकर रीसेट किया जाता है, क्योंकि पिक्सेल पहले से सीधे खड़े "
           "होते हैं: मूल रोटेशन फ़्लैग रखने पर हर व्यूअर फ़ोटो को साइड कर देता है। EXIF ब्लॉक केवल JPG के साथ "
           "जाता है — AVIF और WebP आउटपुट उसे छोड़कर लिखे जाते हैं।"),
}


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".tmp" / "patch-avif-i18n.json"
    patch = {}

    # The label: new everywhere.
    patch[K_LABEL] = dict(LABEL)

    # The three existing options: keep what seven dictionaries already have.
    for key, fresh in EXISTING.items():
        entry = {}
        for lang in LANGS:
            data = json.loads((I18N / ("%s.json" % lang)).read_text(encoding="utf-8"))
            if key in data:
                entry[lang] = data[key]
            else:
                if lang not in fresh:
                    raise SystemExit("[FAIL] no value for %s / %s" % (key, lang))
                entry[lang] = fresh[lang]
        patch[key] = entry

    patch[K_AVIF] = dict(AVIF)
    patch[K_LOSSLESS] = dict(LOSSLESS)
    patch[K_DOES] = dict(DOES)
    patch[K_DOES_NOT] = dict(DOES_NOT)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote %s (%d keys)" % (out, len(patch)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
