#!/usr/bin/env python3
"""
Build the i18n patch for the collage free-placement work (§2.3).

FOUR KEYS
---------
3 new ones for the UI that the drag feature adds, and 1 CHANGED one:

    tools.wedding-photo-collage.p_text.most_collage_makers_require_yo.5s6t7u8v

That paragraph used to say the tool needs "no dragging". After §2.3 the user
CAN drag - so the sentence had to be rewritten in every language, not just in
English. A key that says "no dragging" next to a tool that drags is the same
claim/implementation mismatch this whole pass is about.

Usage
-----
    python scripts/build-collage-i18n-patch.py
    python scripts/add-tool-ui-keys.py .tmp/patch-collage-i18n.json --dry-run
    python scripts/add-tool-ui-keys.py .tmp/patch-collage-i18n.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".tmp" / "patch-collage-i18n.json"

P = "tools.wedding-photo-collage."


PARA = {
"en": "Most collage makers require you to manually drag each photo into a grid cell. WeddingAI.video fills the grid for you in 6 ready-made layouts (2×2, 2×3, 3×3, 3×4, horizontal strip, vertical strip) — and you can still drag: drop a photo onto another cell to swap the two, drag inside a cell to reposition the crop, and zoom one photo without touching the others. The same collage also doubles as a chapter cover in the AI wedding video — in print or on screen, your photos stay organized. Export PNG/PDF/4K, print, or share via link; 11 languages for captions.",
"zh": "大多数拼贴工具都要你把照片一张张手动拖进网格单元。WeddingAI.video 会用 6 种现成版式（2×2、2×3、3×3、3×4、横向长条、纵向长条）直接帮你填满网格——而且你仍然可以拖动：把一张照片拖到另一个单元上即可互换两张，在单元内拖动可以调整裁切位置，滚轮可以单独放大某一张照片而不影响其它照片。同一张拼贴还能直接当作 AI 婚礼视频的章节封面——无论印刷还是屏幕播放，照片都井井有条。可导出 PNG/PDF/4K，可打印、可分享链接；字幕支持 11 种语言。",
"es": "La mayoría de los generadores de collages te obligan a arrastrar manualmente cada foto a una celda de la cuadrícula. WeddingAI.video llena la cuadrícula por ti con 6 diseños listos para usar (2×2, 2×3, 3×3, 3×4, tira horizontal, tira vertical) — y aun así puedes arrastrar: suelta una foto sobre otra celda para intercambiarlas, arrastra dentro de una celda para recolocar el recorte y usa la rueda sobre la foto seleccionada para ampliar una sola foto sin tocar las demás. El mismo collage también sirve de portada de capítulo para el vídeo de boda con IA: impreso o en pantalla, tus fotos quedan ordenadas. Exporta PNG/PDF/4K, imprime o comparte por enlace; 11 idiomas para los pies de foto.",
"fr": "La plupart des outils de collage vous obligent à glisser manuellement chaque photo dans une case de la grille. WeddingAI.video remplit la grille pour vous avec 6 mises en page prêtes à l'emploi (2×2, 2×3, 3×3, 3×4, bande horizontale, bande verticale) — et vous pouvez quand même tout glisser : déposez une photo sur une autre case pour les échanger, glissez à l'intérieur d'une case pour recadrer, et utilisez la molette sur la photo sélectionnée pour agrandir une seule photo sans toucher aux autres. Le même collage sert aussi de couverture de chapitre pour la vidéo de mariage IA : à l'impression ou à l'écran, vos photos restent bien ordonnées. Export PNG/PDF/4K, impression ou partage par lien ; 11 langues pour les légendes.",
"de": "Die meisten Collage-Maker lassen dich jedes Foto manuell in eine Rasterzelle ziehen. WeddingAI.video füllt das Raster mit 6 fertigen Layouts (2×2, 2×3, 3×3, 3×4, horizontaler Streifen, vertikaler Streifen) für dich — und du kannst trotzdem ziehen: Zieh ein Foto auf eine andere Zelle, um die beiden zu tauschen, zieh innerhalb einer Zelle, um den Ausschnitt zu verschieben, und zoome mit dem Mausrad ein einzelnes Foto, ohne die anderen zu verändern. Dieselbe Collage dient auch als Kapitelbild für das KI-Hochzeitsvideo — im Druck oder auf dem Bildschirm bleiben deine Fotos geordnet. Export als PNG/PDF/4K, drucken oder per Link teilen; 11 Sprachen für Bildunterschriften.",
"pt": "A maioria dos criadores de colagem exige que você arraste cada foto manualmente para uma célula da grade. O WeddingAI.video preenche a grade para você com 6 layouts prontos (2×2, 2×3, 3×3, 3×4, faixa horizontal, faixa vertical) — e você ainda pode arrastar: solte uma foto sobre outra célula para trocar as duas, arraste dentro de uma célula para reposicionar o corte e use a roda do mouse sobre a foto selecionada para ampliar uma só foto sem mexer nas restantes. A mesma colagem também serve de capa de capítulo no vídeo de casamento com IA: impressa ou na tela, suas fotos ficam organizadas. Exporte PNG/PDF/4K, imprima ou compartilhe por link; 11 idiomas para as legendas.",
"ja": "ほとんどのコラージュメーカーでは、写真を1枚ずつ手作業でグリッドのセルへ配置する必要があります。WeddingAI.video は 6 つの既製レイアウト（2×2、2×3、3×3、3×4、横ストリップ、縦ストリップ）でグリッドを自動で埋めてくれます——しかもドラッグも引き続き使えます。写真を別のセルへドラッグすると 2 枚が入れ替わり、セルの中でドラッグすれば切り抜き位置を調整でき、選択した写真の上でホイールを操作すればその 1 枚だけを拡大できます。作成したコラージュはそのまま AI 結婚式動画のチャプター表紙にも使えます。印刷用でも画面でも、写真の並びはそのまま。PNG/PDF/4K 出力、印刷、リンク共有に対応。キャプションは 11 言語対応。",
"ru": "Большинство конструкторов коллажей заставляют перетаскивать каждую фотографию в ячейку сетки вручную. WeddingAI.video заполняет сетку за вас по 6 готовым макетам (2×2, 2×3, 3×3, 3×4, горизонтальная полоса, вертикальная полоса) — и при этом вы всё равно можете перетаскивать: перетащите фото на другую ячейку, чтобы поменять их местами, перетащите внутри ячейки, чтобы сдвинуть кадрирование, а колёсиком мыши увеличьте одно фото, не трогая остальные. Тот же коллаж может стать обложкой главы для свадебного видео на ИИ — на печати или на экране фотографии остаются в порядке. Экспорт PNG/PDF/4K, печать или ссылка для отправки; 11 языков для подписей.",
"ar": "معظم أدوات الكولاج تجعلك تسحب كل صورة يدويًا إلى خلية في الشبكة. أما WeddingAI.video فيملأ الشبكة عنك عبر 6 تخطيطات جاهزة (2×2، 2×3، 3×3، 3×4، شريط أفقي، شريط عمودي) — ومع ذلك ما زال بإمكانك السحب: أفلت صورة على خلية أخرى لتبديل الصورتين، واسحب داخل الخلية لتعديل موضع القص، واستخدم عجلة الفأرة فوق الصورة المحددة لتكبير صورة واحدة دون المساس بالبقية. الكولاج نفسه يخدم أيضًا كغلاف فصل لفيديو الزفاف بالذكاء الاصطناعي — مطبوعًا أو على الشاشة، تبقى صورك مرتبة. تصدير PNG/PDF/4K، أو طباعة، أو مشاركة عبر رابط؛ 11 لغة للتسميات التوضيحية.",
"th": "เครื่องมือคอลลาจเกือบทั้งหมดต้องให้คุณลากรูปทีละรูปไปวางในช่องกริดเอง WeddingAI.video เติมกริดให้คุณเองด้วยเลย์เอาต์สำเร็จรูป 6 แบบ (2×2, 2×3, 3×3, 3×4, แถบแนวนอน, แถบแนวตั้ง) — และยังลากได้เหมือนเดิม: ลากรูปไปวางบนช่องอื่นเพื่อสลับกัน ลากภายในช่องเพื่อปรับตำแหน่งการครอป และเลื่อนเมาส์เหนือรูปที่เลือกไว้เพื่อซูมเฉพาะรูปนั้น คอลลาจเดียวกันยังใช้เป็นปกบทของวิดีโอแต่งงานด้วย AI ได้ — ทั้งบนกระดาษและบนจอ รูปของคุณยังเรียงเป็นระเบียบ ส่งออกได้ทั้ง PNG/PDF/4K พิมพ์ได้ แชร์ได้ด้วยลิงก์ และมีคำบรรยายให้เลือก 11 ภาษา",
"hi": "अधिकांश कोलाज निर्माताओं को प्रत्येक फोटो को मैन्युअल रूप से ग्रिड सेल में खींचना पड़ता है। WeddingAI.video आपके लिए 6 तैयार लेआउट (2×2, 2×3, 3×3, 3×4, क्षैतिज़ पट्टी, लंबवत़ पट्टी) से ग्रिड भर देता है — और आप फिर भी खींच सकते हैं: एक फोटो को दूसरे सेल पर छोड़कर दोनों की अदला-बदली करें, सेल के अंदर खींचकर क्रॉप की जगह समायोजित करें, और चुनी हुई फोटो पर माउस व्हील स्क्रॉल करके सिर्फ़ उसी फोटो को ज़ूम करें। वही कोलाज AI वेडिंग वीडियो का चैप्टर कवर भी बन जाता है — प्रिंट हो या स्क्रीन पर, आपकी फोटो तरतीब से रहती हैं। PNG/PDF/4K निर्यात, प्रिंट, या लिंक से साझा करें; कैप्शन के लिए 11 भाषाएँ।",
}


HINT = {
"en": "Click a photo to select it. Drag it onto another cell to swap the two, drag inside a cell to reposition the crop, and scroll over the selected photo to zoom it.",
"zh": "点一下照片即可选中。把一张照片拖到另一个单元上就会互换两张；在单元内拖动可以调整裁切位置；滚轮在选中的照片上滚动可以放大它。",
"es": "Haz clic en una foto para seleccionarla. Arrástrala sobre otra celda para intercambiar las dos, arrastra dentro de una celda para recolocar el recorte y usa la rueda sobre la foto seleccionada para ampliarla.",
"fr": "Cliquez sur une photo pour la sélectionner. Glissez-la sur une autre case pour échanger les deux, glissez à l'intérieur d'une case pour recadrer, et faites défiler la molette sur la photo sélectionnée pour l'agrandir.",
"de": "Klicke ein Foto an, um es auszuwählen. Zieh es auf eine andere Zelle, um die beiden zu tauschen, zieh innerhalb einer Zelle, um den Ausschnitt zu verschieben, und scrolle mit dem Mausrad über das ausgewählte Foto, um es zu vergrößern.",
"pt": "Clique em uma foto para selecioná-la. Arraste-a sobre outra célula para trocar as duas, arraste dentro de uma célula para reposicionar o corte e use a roda do mouse sobre a foto selecionada para ampliá-la.",
"ja": "写真をクリックすると選択できます。別のセルへドラッグすると 2 枚が入れ替わり、セルの中でドラッグすれば切り抜き位置を調整でき、選択した写真の上でホイールを操作すると拡大できます。",
"ru": "Щёлкните по фото, чтобы выбрать его. Перетащите его на другую ячейку, чтобы поменять их местами, перетащите внутри ячейки, чтобы сдвинуть кадрирование, и прокрутите колесо над выбранным фото, чтобы увеличить его.",
"ar": "انقر على صورة لتحديدها. اسحبها إلى خلية أخرى لتبديل الصورتين، واسحب داخل الخلية لتعديل موضع القص، واستخدم عجلة الفأرة فوق الصورة المحددة لتكبيرها.",
"th": "คลิกที่รูปเพื่อเลือก ลากรูปไปวางบนช่องอื่นเพื่อสลับกัน ลากภายในช่องเพื่อปรับตำแหน่งการครอป และเลื่อนเมาส์เหนือรูปที่เลือกไว้เพื่อซูม",
"hi": "किसी फोटो पर क्लिक करके उसे चुनें। उसे दूसरे सेल पर खींचें और दोनों की अदला-बदली करें, सेल के अंदर खींचकर क्रॉप की जगह समायोजित करें, और चुनी हुई फोटो पर माउस व्हील स्क्रॉल करके उसे ज़ूम करें।",
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


RESET_LABEL = {
"en": "Reset layout",
"zh": "重置排版",
"es": "Restablecer el diseño",
"fr": "Réinitialiser la mise en page",
"de": "Layout zurücksetzen",
"pt": "Redefinir o layout",
"ja": "レイアウトをリセット",
"ru": "Сбросить макет",
"ar": "إعادة تعيين التخطيط",
"th": "รีเซ็ตเลย์เอาต์",
"hi": "लेआउट रीसेट करें",
}


PATCH = {
    P + "p_text.most_collage_makers_require_yo.5s6t7u8v": PARA,
    P + "small_text.free_placement_hint.7q4v2m8x": HINT,
    P + "label_text.zoom_selected.4n8k6p1w": ZOOM_LABEL,
    P + "button_text.reset_layout.2r9t5y7u": RESET_LABEL,
}


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(PATCH, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote %s (%d keys)" % (OUT, len(PATCH)))
    for key in PATCH:
        missing = [l for l in ("en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi")
                   if l not in PATCH[key]]
        if missing:
            print("  [FAIL] %s is missing %s" % (key, missing))
            return 1
    print("  every key has all 11 languages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
