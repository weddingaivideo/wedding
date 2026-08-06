#!/usr/bin/env python3
"""
Align blog filenames across all languages to match English canonical slugs.
Strategy: Read first 5 lines of each file, extract title, match to canonical topic.
"""
import os
import re
import shutil

BASE = "/home/work/.openclaw/workspace/weddingai-blogs"
EN_DIR = os.path.join(BASE, "en")

# Canonical slugs (from EN) and their topic identifiers (unique keywords in title)
TOPIC_MAP = {
    "wedding-video-trends-2026": ["trend", "2026", "趋势", "tendencia", "tendance", "トレンド", "트렌드", "اتجاه", "แนวโน้ม"],
    "why-wedding-video-important": ["why", "important", "为什么", "重要", "por qué", "pourquoi", "warum", "por que", "なぜ", "왜", "لماذا", "ทำไม"],
    "wedding-photos-vs-video": ["photos vs", "photo vs", "照片", "foto vs", "photo vs", "写真", "사진", "صورة", "ภาพ"],
    "wedding-video-cost-2026-new": ["cost", "price", "价格", "precio", "coût", "preis", "custo", "費用", "가격", "تكلفة", "ราคา", "多少钱", "cuánto", "combien", "wie viel", "quanto", "いくら", "얼마", "كم", "เท่าไหร่"],
    "affordable-wedding-video-ai": ["affordable", "cheap", "budget", "便宜", "预算", "asequible", "economique", "günstig", "acessível", "手頃", "저렴", "بמחיר", "ราคาประหยัด"],
    "what-is-ai-wedding-video-generator": ["what is", "generator", "什么是", "生成器", "qué es", "générateur", "was ist", "gerador", "ジェネレーター", "제너레이터", "مولد", "ตัวสร้าง"],
    "ai-photos-to-wedding-video": ["photos to", "photo to", "照片", "fotos a", "photos vers", "fotos zu", "fotos para", "写真", "사진", "صورة", "ภาพ"],
    "wedding-video-no-editing-skills": ["no editing", "without skill", "不会剪辑", "sin editar", "sans compétence", "ohne", "sem saber", "編集なし", "편집 없이", "بدون", "ไม่ต้อง"],
    "ai-wedding-video-workflow": ["workflow", "flow", "流程", "flujo", "flux", "fluxo", "ワークフロー", "워크플로우", "سير العمل", "ขั้นตอน"],
    "ai-wedding-video-privacy": ["privacy", "safe", "安全", "privacidad", "sécurité", "datenschutz", "segurança", "プライバシー", "프라이버시", "خصوصية", "ความปลอดภัย"],
    "proposal-video-ideas": ["proposal", "idea", "求婚", "创意", "propuesta", "demande", "antrag", "pedido", "プロポーズ", "프로포즈", "طلب", "ขอแต่งงาน"],
    "ai-proposal-video": ["ai proposal", "ai求婚", "ia propuesta", "ia demande", "ki antrag", "ia pedido", "aiプロポーズ", "ai프로포즈", "aiطلب", "aiขอ"],
    "wedding-countdown-video": ["countdown", "倒计时", "cuenta regresiva", "compte", "countdown", "contagem", "カウントダウン", "카운트다운", "عد تنازلي", "นับถอยหลัง"],
    "wedding-invitation-video-guide": ["invitation guide", "邀请", "指南", "invitación", "invitation", "einladung", "convite", "招待", "초대", "دعوة", "เชิญ"],
    "video-wedding-invitation": ["video invitation", "视频请柬", "video invitación", "vidéo invitation", "video einladung", "vídeo convite", "動画招待", "비디오 초대", "فيديو دعوة", "วิดีโอ การ์ดเชิญ"],
    "wedding-video-without-videographer": ["without videographer", "no photographer", "没有摄影师", "sin fotógrafo", "sans caméraman", "ohne kameramann", "sem fotógrafo", "カメラマンなし", "촬영기사 없이", "بدون مصور", "ไม่มีช่างภาพ"],
    "diy-wedding-video-phone": ["phone", "diy", "手机", "teléfono", "téléphone", "handy", "celular", "スマホ", "스마트폰", "هاتف", "มือถือ"],
    "automatic-wedding-video-editing": ["automatic", "auto edit", "自动", "automático", "automatique", "automatisch", "自動", "자동", "تلقائي", "อัตโนมัติ"],
    "wedding-video-types-guide": ["30 type", "type guide", "类型", "tipo", "art", "タイプ", "유형", "نوع", "ประเภท"],
    "wedding-highlight-video": ["highlight", "ไฮไลท์", "ハイライト", "하이라이트"],
    "wedding-trailer-video": ["trailer", "预告片", "tráiler", "トレーラー", "트레일러", "تريلر", "เทรลเลอร์"],
    "wedding-slideshow-guide": ["slideshow", "diaporama", "幻灯片", "diapositiva", "diashow", "スライドショー", "슬라이드쇼", "عرض الشرائح", "สไลด์โชว์"],
    "wedding-wishes-video": ["wishes", "祝福", "deseos", "vœux", "wünsche", "votos", "축하", "تمنيات", "คำอวยพร"],
    "couple-slideshow-video": ["couple slideshow", "成长回忆", "pareja", "couple diaporama", "paar diashow", "casal", "カップル", "커플", "زوجين", "คู่รัก"],
    "bride-wedding-video-checklist": ["bride checklist", "新娘清单", "novia", "mariée", "braut", "noiva", "花嫁", "신부", "عروس", "เจ้าสาว"],
    "wedding-video-inspiration": ["inspiration", "pinterest", "灵感", "inspiración", "inspiration", "inspiração", "インスピレーション", "영감", "إلهام", "แรงบันดาลใจ"],
    "ai-tools-for-photographers": ["tools photographer", "摄影师工具", "herramientas fotógrafo", "outils photographe", "tools fotograf", "ferramentas fotógrafo", "ツールカメラマン", "도구사진작가", "أدواتمصور", "เครื่องมือช่างภาพ"],
    "photographer-upsell-video": ["photographer upsell", "摄影师收入", "fotógrafo ingreso", "photographe revenu", "fotograf umsatz", "fotógrafo renda", "カメラマン収入", "사진작가수입", "مصوردخل", "ช่างภาพรายได้"],
    "ai-wont-replace-photographers": ["ai replace", "ai取代", "ia reemplaza", "ia remplace", "ki ersetzt", "ia substitui", "ai置き換える", "ai대체", "aiيحل", "aiแทน"],
    "wedding-planner-ai-services": ["planner ai", "婚庆ai", "planificador ia", "planificateur ia", "planer ki", "planejador ia", "プランナーai", "플래너ai", "منسقai", "แพลนเนอร์ai"],
    "wedding-package-video-upsell": ["package video", "套餐视频", "paquete video", "forfait vidéo", "paket video", "pacote vídeo", "パッケージビデオ", "패키지비디오", "باقةفيديو", "แพ็กเกจวิดีโอ"],
    "destination-wedding-video-guide": ["destination", "海外", "destino", "デスティネーション", "데스티네이션", "وجهة", "เดสติเนชัน"],
    "small-wedding-video-ideas": ["small wedding", "小型", "boda pequeña", "mariage petit", "kleine hochzeit", "casamento pequeno", "小規模", "소규모", "حفلصغير", "งานเล็ก"],
    "wedding-video-under-500": ["under 500", "budget 500", "500 dollar", "500美元", "500 dólar", "500 euro", "500ドル", "500달러", "500دولار", "500ดอลลาร์"],
    "elopement-wedding-video-guide": ["elopement", "私奔", "エロープメント", "엘로프먼트", "إلوبمنت", "อโลปเมนต์"],
    "lgbtq-wedding-video-ideas": ["lgbtq", "same-sex", "同性", "lgbtq"],
    "ai-video-maker-vs-videographer": ["ai vs videographer", "ai vs摄影师", "ia vs videógrafo", "ia vs caméraman", "ki vs kameramann", "ai vsカメラマン", "ai vs촬영기사", "ai vsمصور", "ai vsช่างภาพ"],
    "best-ai-wedding-video-tools-2026": ["best tool", "最佳工具", "mejor herramienta", "meilleur outil", "beste tool", "melhor ferramenta", "最高ツール", "최고도구", "أفضلأداة", "เครื่องมือดีที่สุด"],
    "canva-vs-ai-wedding-video": ["canva vs", "canva vs"],
    "ai-editor-vs-traditional-editing": ["traditional vs ai", "传统vs ai", "tradicional vs ia", "traditionnel vs ia", "traditionell vs ki", "tradicional vs ia", "従来vs ai", "전통vs ai", "تقليديvs ai"],
    "how-to-make-wedding-video": ["how to make", "如何制作", "cómo hacer", "comment faire", "wie man macht", "como fazer", "作り方", "만드는방법", "كيفيةصنع", "วิธีทำ"],
    "wedding-video-photo-checklist": ["photo checklist", "照片清单", "foto checklist", "photo checkliste", "foto checkliste", "写真チェックリスト", "사진체크리스트", "صورةقائمة", "ภาพเช็คลิสต์"],
    "wedding-video-music-guide-new": ["music guide", "音乐指南", "música guía", "musique guide", "musik guide", "música guia", "音楽ガイド", "음악가이드", "موسيقىدليل", "เพลงคู่มือ"],
    "wedding-video-captions": ["caption", "subtitle", "字幕", "subtítulo", "sous-titre", "unterschrift", "legenda", "자막", "ترجمة", "คำบรรยาย"],
    "wedding-video-length-guide": ["length", "duration", "长度", "duración", "durée", "länge", "duração", "長さ", "길이", "مدة", "ความยาว"],
    "why-couples-choose-ai-video": ["why choose", "为什么选择", "por qué elige", "pourquoi choisit", "warum wählen", "por que escolhem", "なぜ選ぶ", "왜선택", "لماذايختار", "ทำไมเลือก"],
    "make-first-ai-wedding-video": ["first video", "5 min", "第一支", "5分钟", "primer video", "5 minutos", "premier vidéo", "5 minutes", "erstes video", "5 minuten", "primeiro vídeo", "最初の動画", "5分", "첫비디오", "5분", "أولفيديو", "5 دقائق", "วิดีโอแรก", "5 นาที"],
    "free-wedding-video-maker": ["free tool", "免费", "gratuit", "kostenlos", "gratuito", "無料", "무료", "مجاني", "ฟรี"],
    "weddingai-video-guide": ["weddingai guide", "完整指南", "guía completa", "guide complet", "komplett guide", "guia completo", "完全ガイド", "완벽가이드", "دليلشامل", "คู่มือสมบูรณ์"],
    "weddingai-video-case-studies": ["case study", "案例", "caso de éxito", "étude de cas", "fallstudie", "caso de sucesso", "ケーススタディ", "사례연구", "دراساتحالة", "กรณีศึกษา"],
}

def get_title(filepath):
    """Extract title from first line of markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    return line.lstrip('#').strip().lower()
                if line and not line.startswith('*') and not line.startswith('**') and not line.startswith('>') and len(line) > 10:
                    return line.lower()
    except:
        pass
    return ""

def match_topic(title, slug):
    """Check if a title matches a topic's keywords."""
    keywords = TOPIC_MAP.get(slug, [])
    for kw in keywords:
        if kw.lower() in title:
            return True
    return False

def align_language(lang):
    """Align a language folder's filenames to canonical slugs."""
    lang_dir = os.path.join(BASE, lang)
    if not os.path.isdir(lang_dir):
        return
    
    # Get current files
    current_files = set(f for f in os.listdir(lang_dir) if f.endswith('.md'))
    canonical_slugs = set(s + '.md' for s in TOPIC_MAP.keys())
    
    # Find non-canonical files
    non_canonical = current_files - canonical_slugs
    
    # For each non-canonical file, try to match it to a canonical slug
    renamed = 0
    unmatched = []
    
    for nc_file in sorted(non_canonical):
        filepath = os.path.join(lang_dir, nc_file)
        title = get_title(filepath)
        
        if not title:
            unmatched.append(nc_file)
            continue
        
        # Try to match
        best_match = None
        for slug in TOPIC_MAP.keys():
            canonical_file = slug + '.md'
            # Skip if canonical already exists
            if canonical_file in current_files:
                continue
            if match_topic(title, slug):
                best_match = slug
                break
        
        if best_match:
            new_path = os.path.join(lang_dir, best_match + '.md')
            os.rename(filepath, new_path)
            print(f"  RENAME: {nc_file} -> {best_match}.md")
            renamed += 1
            current_files.add(best_match + '.md')
        else:
            unmatched.append(nc_file)
    
    # Delete unmatched non-canonical files (they are duplicates or junk)
    deleted = 0
    for uf in unmatched:
        filepath = os.path.join(lang_dir, uf)
        os.remove(filepath)
        deleted += 1
    
    print(f"  Renamed: {renamed} | Deleted (unmatched): {deleted}")

# Main
print("=== Smart Filename Alignment (Python) ===\n")

for lang in ['zh', 'es', 'fr', 'de', 'pt', 'ja', 'ko', 'ar', 'th']:
    print(f"=== Processing {lang} ===")
    align_language(lang)

print("\n=== Final Counts ===")
for lang in ['en', 'zh', 'es', 'fr', 'de', 'pt', 'ja', 'ko', 'ar', 'th']:
    lang_dir = os.path.join(BASE, lang)
    count = len([f for f in os.listdir(lang_dir) if f.endswith('.md')])
    print(f"  {lang}: {count}")

# Verify all languages have the same files
print("\n=== Verification ===")
en_files = set(f for f in os.listdir(EN_DIR) if f.endswith('.md'))
all_match = True
for lang in ['zh', 'es', 'fr', 'de', 'pt', 'ja', 'ko', 'ar', 'th']:
    lang_dir = os.path.join(BASE, lang)
    lang_files = set(f for f in os.listdir(lang_dir) if f.endswith('.md'))
    if lang_files != en_files:
        missing = en_files - lang_files
        extra = lang_files - en_files
        if missing:
            print(f"  {lang} MISSING: {sorted(missing)}")
        if extra:
            print(f"  {lang} EXTRA: {sorted(extra)}")
        all_match = False
    else:
        print(f"  {lang}: ✅ MATCHES EN")

if all_match:
    print("\n✅ All languages have identical filenames!")
