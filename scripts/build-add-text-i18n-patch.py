#!/usr/bin/env python3
"""
Build the i18n patch for §2.2 (drag the text on the photo).

Two groups of keys:

  * The seven the position control ALREADY used in the seven languages
    that had it bound. Those values are kept verbatim; the four
    languages that had the text inline and unbound (en/zh/pt/ru) get the
    same keys with the text they already showed.
  * The two new ones - the drag hint and the reset button - in all
    eleven languages.

Usage:  python scripts/build-add-text-i18n-patch.py <out.json>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]

P = "tools.add-text-to-wedding-photo."
K_LABEL = P + "label_text.d4d2a668"
K_TOP = P + "option_text.c949729c"
K_TOPC = P + "option_text.f620edd1"
K_CENTER = P + "option_text.c646a231"
K_BOTC = P + "option_text.879e6d08"
K_BOTTOM = P + "option_text.12c4c5e8"
K_SAVEDATE = P + "small_text.943ad5ab"
K_DRAG = P + "small_text.drag_to_move.k7m2n4p6"
K_RESET = P + "button_text.reset_position.r9s3t5v7"

# The text en/zh/pt/ru already showed inline, before the control was
# bound to the dictionary.
EXISTING = {
    K_LABEL: {
        "en": "Position",
        "zh": "位置",
        "pt": "Posição",
        "ru": "Положение",
    },
    K_TOP: {
        "en": "Top",
        "zh": "顶部",
        "pt": "Topo",
        "ru": "Сверху",
    },
    K_TOPC: {
        "en": "Top-Center",
        "zh": "顶部居中",
        "pt": "Centro no topo",
        "ru": "Сверху по центру",
    },
    K_CENTER: {
        "en": "Center",
        "zh": "正中",
        "pt": "Centro",
        "ru": "По центру",
    },
    K_BOTC: {
        "en": "Bottom-Center",
        "zh": "底部居中",
        "pt": "Centro embaixo",
        "ru": "Снизу по центру",
    },
    K_BOTTOM: {
        "en": "Bottom",
        "zh": "底部",
        "pt": "Embaixo",
        "ru": "Снизу",
    },
    K_SAVEDATE: {
        "en": "Bottom-Center is the classic save-the-date spot.",
        "zh": "「底部居中」是 Save the Date 最经典的写法。",
        "pt": "Centro embaixo é o lugar clássico do save-the-date.",
        "ru": "«Снизу по центру» — классический формат save the date.",
    },
}

DRAG = {
    "en": "Drag the text straight on the photo to move it — the position applies to every photo in the batch.",
    "zh": "直接在照片上拖动文字即可移动——这个位置会应用到批次里的每一张照片。",
    "es": "Arrastra el texto directamente sobre la foto para moverlo: la posición se aplica a todas las fotos del lote.",
    "fr": "Faites glisser le texte directement sur la photo pour le déplacer — la position s'applique à toutes les photos du lot.",
    "de": "Ziehe den Text direkt auf dem Foto, um ihn zu verschieben – die Position gilt für jedes Foto im Stapel.",
    "pt": "Arraste o texto direto sobre a foto para movê-lo — a posição vale para todas as fotos do lote.",
    "ja": "写真の上のテキストを直接ドラッグすると動かせます。この位置はバッチ内のすべての写真に適用されます。",
    "ru": "Перетащите текст прямо по фото, чтобы переместить его — положение применяется к каждой фотографии в пакете.",
    "ar": "اسحب النص مباشرة على الصورة لتحريكه — ينطبق الموضع على كل صورة في الدفعة.",
    "th": "ลากข้อความบนรูปภาพโดยตรงเพื่อย้ายตำแหน่ง — ตำแหน่งนี้ใช้กับทุกภาพในชุด",
    "hi": "टेक्स्ट को सीधे फ़ोटो पर खींचकर उसे हिलाएँ — यह स्थिति बैच की हर फ़ोटो पर लागू होती है।",
}

RESET = {
    "en": "Reset position",
    "zh": "重置位置",
    "es": "Restablecer posición",
    "fr": "Réinitialiser la position",
    "de": "Position zurücksetzen",
    "pt": "Redefinir posição",
    "ja": "位置をリセット",
    "ru": "Сбросить положение",
    "ar": "إعادة تعيين الموضع",
    "th": "รีเซ็ตตำแหน่ง",
    "hi": "स्थिति रीसेट करें",
}


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".tmp" / "patch-add-text-i18n.json"
    patch = {}

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

    patch[K_DRAG] = dict(DRAG)
    patch[K_RESET] = dict(RESET)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote %s (%d keys)" % (out, len(patch)))
    for key in patch:
        filled = [l for l in LANGS
                  if key not in json.loads((I18N / ("%s.json" % l)).read_text(encoding="utf-8"))]
        print("  %-46s newly added for: %s" % (key.split(".", 1)[1], ", ".join(filled) or "(nothing)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
