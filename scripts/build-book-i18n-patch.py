#!/usr/bin/env python3
"""
Build the i18n patch for the photo-book free-placement work (§2.4).

FIVE NEW KEYS
-------------
The placement panel (hint, zoom label, reset button) and the two export
buttons, which used to carry a hardcoded English label in every language.

ONE CHANGED KEY
----------------
    tools.wedding-photo-book-planner.p_text.most_print_services_require_yo.5m6n7o8p

It said the planner fills the grid "in upload order" - still the default,
but the user can now arrange the page, and the album really does export as
print-ready 300 DPI pages. The sentence had to change in all 11 languages.

Usage
-----
    python scripts/build-book-i18n-patch.py
    python scripts/add-tool-ui-keys.py .tmp/patch-book-i18n.json --dry-run
    python scripts/add-tool-ui-keys.py .tmp/patch-book-i18n.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".tmp" / "patch-book-i18n.json"

P = "tools.wedding-photo-book-planner."


PARA = {
"en": "Most print services require you to manually lay out each spread with templates. WeddingAI.video’s planner auto-fills the grid page by page — and then lets you drag the photos into the slots you want, crop each one and zoom it — places captions in 11 languages, and exports the whole album as print-ready 300 DPI pages for any print shop.",
"zh": "大多数印刷服务都要求你自己用模板逐页排版。WeddingAI.video 的规划器会逐页自动填满网格——之后你还可以把照片拖进想要的格位、单独裁切并放大——同时用 11 种语言排版字幕，并把整本相册导出为可直接送印的 300 DPI 页面。导出 PDF 版面后即可上传到 Artifact Uprising、Printerpix 或任何你喜欢的印刷厂。",
"es": "La mayoría de los servicios de impresión te obligan a maquetar cada páginas con plantillas. El planificador de WeddingAI.video rellena la cuadrícula página por página — y además te deja arrastrar las fotos a las casillas que quieras, recortarlas y ampliarlas — coloca los pies en 11 idiomas y exporta todo el álbum como páginas de 300 DPI listas para imprimir. Exporta el PDF y súbelo a Artifact Uprising, Printerpix o la imprenta que prefieras.",
"fr": "La plupart des services d’impression vous obligent à mettre en page chaque double avec des modèles. Le planificateur de WeddingAI.video remplit la grille page par page — et vous laisse ensuite glisser les photos dans les cases de votre choix, les recadrer et les agrandir — place les légendes en 11 langues et exporte tout l’album en pages de 300 DPI prêtes à imprimer. Exportez le PDF et envoyez-le à Artifact Uprising, Printerpix ou à l’imprimeur de votre choix.",
"de": "Die meisten Druckdienstleister lassen dich jedes Spread mit Vorlagen selbst layouten. Der Planer von WeddingAI.video füllt das Raster Seite für Seite — und lässt dich danach die Fotos in die Slots ziehen, die du willst, sie zuschneiden und zoomen — setzt Bildunterschriften in 11 Sprachen und exportiert das ganze Album als druckfertige 300-DPI-Seiten. Exportiere das Layout-PDF und lade es bei Artifact Uprising, Printerpix oder bei der Druckerei deiner Wahl hoch.",
"pt": "A maioria dos serviços de impressão exige que você monte cada página com modelos. O planejador do WeddingAI.video preenche a grade página por página — e depois deixa você arrastar as fotos para os espaços que quiser, recortar cada uma e dar zoom — aplica legendas em 11 idiomas e exporta o álbum inteiro como páginas de 300 DPI prontas para impressão. Exporte o PDF do layout e envie para Artifact Uprising, Printerpix ou para a gráfica que você preferir.",
"ja": "ほとんどの印刷サービスは、テンプレートを使って見開きを自分で組む必要があります。WeddingAI.video のプランナーはページ単位でグリッドを自動で埋めてくれるだけでなく、その後写真を好きなスロットへドラッグしたり、1枚ずつトリミングや拡大ができるほか、11言語のキャプションを配置し、アルバム全体を印刷用の300 DPIページとして書き出せます。レイアウト PDF を書き出して、Artifact Uprising、Printerpix またはお好みの印刷会社に送ってください。",
"ru": "Большинство типографий заставляют вручную сверстать каждый разворот по шаблонам. Планировщик WeddingAI.video заполняет сетку страница за страницей — а потом вы можете перетащить фото в нужные ячейки, обрезать каждое и увеличить его — ставит подписи на 11 языках и экспортирует весь альбом готовыми к печати страницами в 300 DPI. Экспортируйте PDF-развёртку и загрузите её в Artifact Uprising, Printerpix или в любую типографию.",
"ar": "معظم خدمات الطباعة تطلب منك تخطيط كل صفحتين بقوالب جاهزة. مخطّط WeddingAI.video يملأ الشبكة صفحة تلو الأخرى — ثم يتيح لك سحب الصور إلى الخانات التي تريدها، وقص كل صورة وتكبيرها — ويضع التسميات التوضيحية بـ 11 لغة، ويصدّر الألبوم كاملًا كصفحات بدقة 300 DPI جاهزة للطباعة. صدّر ملف PDF بالتخطيط وارفعه إلى Artifact Uprising أو Printerpix أو أي مطبعة تختارها.",
"th": "บริการพิมพ์เกือบทั้งหมดต้องให้คุณจัดหน้าสองหน้าเองด้วยเทมเพลต เครื่องวางแผนของ WeddingAI.video เติมกริดให้ทีละหน้า — แล้วคุณยังลากรูปไปวางในช่องที่ต้องการ ครอปทีละรูปและซูมได้ — พร้อมใส่คำบรรยาย 11 ภาษา และส่งออกทั้งอัลบั้มเป็นหน้าความละเอียด 300 DPI ที่พร้อมพิมพ์ เอาต์ไฟล์ PDF ของเลย์เอาต์ไปอัปโหลดที่ Artifact Uprising, Printerpix หรือโรงพิมพ์ที่คุณชอบก็ได้",
"hi": "ज़्यादातर प्रिंट सेवाओं में हर स्प्रेड को टेम्पलेट से खुद लेआउट करना पड़ता है। WeddingAI.video का प्लानर ग्रिड को पेज-दर-पेज भर देता है — और फिर आप फ़ोटो को जिस स्लॉट में चाहें वहाँ खींच सकते हैं, हर एक को क्रॉप करके ज़ूम कर सकते हैं — 11 भाषाओं में कैप्शन लगाता है, और पूरे एल्बम को प्रिंट-रेडी 300 DPI पेजों में एक्सपोर्ट करता है। लेआउट PDF निर्यात करके इसे Artifact Uprising, Printerpix या अपनी पसंद की प्रिंट शॉप पर अपलोड करें।",
}


HINT = {
"en": "Drag a photo from the library onto a slot, or drag one slot onto another to swap them. Drag inside a slot to reposition the crop, and scroll over a slot to zoom it.",
"zh": "把照片从素材库拖到格位上，或把一个格位拖到另一个上互换两张。在格位内部拖动可以调整裁切位置，滚轮在格位上滚动可以放大。",
"es": "Arrastra una foto de la biblioteca a una casilla, o arrastra una casilla sobre otra para intercambiarlas. Arrastra dentro de una casilla para recolocar el recorte y usa la rueda sobre una casilla para ampliarla.",
"fr": "Glissez une photo de la bibliothèque vers une case, ou glissez une case sur une autre pour les échanger. Glissez à l'intérieur d'une case pour recadrer, et faites défiler la molette sur une case pour l'agrandir.",
"de": "Zieh ein Foto aus der Bibliothek in einen Slot, oder zieh einen Slot auf einen anderen, um die beiden zu tauschen. Zieh innerhalb eines Slots, um den Ausschnitt zu verschieben, und scrolle mit dem Mausrad über einen Slot, um ihn zu vergrößern.",
"pt": "Arraste uma foto da biblioteca para um espaço, ou arraste um espaço sobre outro para trocar as duas. Arraste dentro de um espaço para reposicionar o corte e use a roda do mouse sobre um espaço para ampliá-lo.",
"ja": "ライブラリから写真をスロットへドラッグすると配置されます。スロットを別のスロットへドラッグすると 2 枚が入れ替わります。スロットの中でドラッグすれば切り抜き位置を調整でき、ホイールで拡大できます。",
"ru": "Перетащите фото из библиотеки в ячейку или перетащите одну ячейку на другую, чтобы поменять их местами. Перетаскивание внутри ячейки двигает кадрирование, а колесо мыши над ячейкой увеличивает фото.",
"ar": "اسحب صورة من المكتبة إلى خلية، أو اسحب خلية فوق أخرى لتبديلهما. اسحب داخل الخلية لتعديل موضع القص، واستخدم عجلة الفأرة فوق الخلية لتكبيرها.",
"th": "ลากรูปจากคลังภาพไปวางบนช่อง หรือลากช่องหนึ่งไปทับอีกช่องเพื่อสลับกัน ลากภายในช่องเพื่อปรับตำแหน่งการครอป และเลื่อนเมาส์เหนือช่องเพื่อซูม",
"hi": "फ़ोटो को लाइब्रेरी से स्लॉट पर खींचें, या एक स्लॉट को दूसरे पर खींचकर दोनों की अदला-बदली करें। स्लॉट के अंदर खींचकर क्रॉप की जगह समायोजित करें, और स्लॉट पर माउस व्हील स्क्रॉल करके उसे ज़ूम करें।",
}


ZOOM_LABEL = {
"en": "Zoom selected photo",
"zh": "放大选中的照片",
"es": "Ampliar la foto seleccionada",
"fr": "Agrandir la photo sélectionnée",
"de": "Ausgewähltes Foto vergrößern",
"pt": "Ampliar a foto selecionada",
"ja": "選択した写真を拡大",
"ru": "Увеличить выбранное фото",
"ar": "تكبير الصورة المحددة",
"th": "ซูมรูปที่เลือกไว้",
"hi": "चयनित फोटो ज़ूम करें",
}


RESET_CROP = {
"en": "Reset crop",
"zh": "重置裁切",
"es": "Restablecer el recorte",
"fr": "Réinitialiser le recadrage",
"de": "Ausschnitt zurücksetzen",
"pt": "Redefinir o corte",
"ja": "切り抜きをリセット",
"ru": "Сбросить кадрирование",
"ar": "إعادة تعيين القص",
"th": "รีเซ็ตการครอป",
"hi": "क्रॉप रीसेट करें",
}


DOWNLOAD_PNG = {
"en": "Download this page (300 DPI PNG)",
"zh": "下载本页（300 DPI PNG）",
"es": "Descargar esta página (PNG de 300 DPI)",
"fr": "Télécharger cette page (PNG 300 DPI)",
"de": "Diese Seite herunterladen (300 DPI PNG)",
"pt": "Baixar esta página (PNG de 300 DPI)",
"ja": "このページをダウンロード（300 DPI PNG）",
"ru": "Скачать эту страницу (PNG 300 DPI)",
"ar": "تنزيل هذه الصفحة (PNG بدقة 300 DPI)",
"th": "ดาวน์โหลดหน้านี้ (PNG 300 DPI)",
"hi": "यह पेज डाउनलोड करें (300 DPI PNG)",
}


DOWNLOAD_PDF = {
"en": "Download all pages (print-ready PDF)",
"zh": "下载全部页面（可印刷 PDF）",
"es": "Descargar todas las páginas (PDF listo para imprimir)",
"fr": "Télécharger toutes les pages (PDF prêt à imprimer)",
"de": "Alle Seiten herunterladen (druckfertiges PDF)",
"pt": "Baixar todas as páginas (PDF pronto para impressão)",
"ja": "すべてのページをダウンロード（印刷用 PDF）",
"ru": "Скачать все страницы (PDF, готовый к печати)",
"ar": "تنزيل كل الصفحات (PDF جاهز للطباعة)",
"th": "ดาวน์โหลดทุกหน้า (PDF พร้อมพิมพ์)",
"hi": "सभी पेज डाउनलोड करें (प्रिंट-रेडी PDF)",
}


PATCH = {
    P + "p_text.most_print_services_require_yo.5m6n7o8p": PARA,
    P + "small_text.free_placement_hint.6b3n8q5x": HINT,
    P + "label_text.zoom_selected.9k2v7m4w": ZOOM_LABEL,
    P + "button_text.reset_crop.4t6y1u8s": RESET_CROP,
    P + "button_text.download_page_png.7y2c5v8n": DOWNLOAD_PNG,
    P + "button_text.download_all_pdf.3m8k1w6r": DOWNLOAD_PDF,
}

LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(PATCH, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote %s (%d keys)" % (OUT, len(PATCH)))
    bad = False
    for key in PATCH:
        missing = [l for l in LANGS if l not in PATCH[key]]
        if missing:
            print("  [FAIL] %s is missing %s" % (key, missing))
            bad = True
    if bad:
        return 1
    print("  every key has all 11 languages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
