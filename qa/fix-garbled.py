"""Fix 7 garbled translation values in the i18n JSON files.
These were introduced when the LLM hallucinated non-existent script during
the initial bulk-write. Each value below is the clean correct translation
replacing the corrupted one.
"""
import json
from pathlib import Path

I18N_DIR = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai\i18n")
HEX = "e8f9a0b1"

FIXES = {
    ("fr", "h4_text.card2_title"): "Generateur de video IA",
    ("ru", "p_text.pair_it_with_intro"): "Эти услуги хорошо дополняют то, что вы рассматриваете. 2+ услуги — скидка 10-20% на пакет.",
    ("ru", "h4_text.card2_title"): "AI-генератор видео",
    ("th", "p_text.pair_it_with_intro"): "บริการเหล่านี้เข้ากันได้ดีกับสิ่งที่คุณกำลังดูอยู่ 2+ บริการ รับส่วนลด 10-20% แบบแพ็คเกจ.",
    ("th", "p_text.card1_desc"): "ผสมผสานช่วงเวลาสโลว์โมชั่นเข้ากับรีล 60 วินาทีจากฟุตเทจที่บูรณะแล้ว.",
    ("zh", "p_text.card1_desc"): "将慢动作瞬间与修复素材中 60 秒高光片段相结合。",
    ("zh", "p_text.card2_desc"): "用匹配的风格生成新的 B-roll 素材，与修复片段自然衔接。",
}

for (lang, slot), new_value in FIXES.items():
    path = I18N_DIR / f"{lang}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    full_key = f"services.vintage_restoration.{slot}.{HEX}"
    if full_key not in data:
        print(f"  SKIP: {lang} {slot} (key not present)")
        continue
    old = data[full_key]
    data[full_key] = new_value
    out = "{\n"
    items = list(data.items())
    for i, (k, v) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        out += f'  {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}{comma}\n'
    out += "}"
    path.write_text(out, encoding="utf-8")
    print(f"  FIXED: {lang} {slot}  --  was: {old!r}")
