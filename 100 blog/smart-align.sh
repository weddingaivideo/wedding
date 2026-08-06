#!/bin/bash
# Smart filename alignment: match non-canonical files to canonical slugs by topic keywords
BASE="/home/work/.openclaw/workspace/weddingai-blogs"
EN_DIR="$BASE/en"

# Canonical slugs and their topic keywords for matching
declare -A SLUG_KEYWORDS
SLUG_KEYWORDS=(
  ["wedding-video-trends-2026"]="trend|趋势|tendencia|tendance|trend|トレンド|트렌드|اتجاه|แนวโน้ม"
  ["why-wedding-video-important"]="why.*important|为什么.*重要|por.*qué.*importa|pourquoi.*important|warum.*wichtig|por.*que.*importa|なぜ.*重要|왜.*중요|لماذا.*مهم|ทำไม.*สำคัญ"
  ["wedding-photos-vs-video"]="photo.*vs.*video|照片.*视频|foto.*vs.*video|photo.*vs.*vidéo|foto.*vs.*video|写真.*動画|사진.*비디오|صورة.*فيديو|ภาพ.*วิดีโอ"
  ["wedding-video-cost-2026-new"]="cost|price|价格|precio|coût|preis|custo|費用|가격|تكلفة|ราคา"
  ["affordable-wedding-video-ai"]="affordable|cheap|budget|便宜|预算|asequible|economique|günstig|acessível|手頃|저렴|بמחיר معقول|ราคาประหยัด"
  ["what-is-ai-wedding-video-generator"]="what.*is.*generator|什么是.*生成器|qué.*es.*generador|qu.*est.*générateur|was.*ist.*generator|o.*que.*gerador|ジェネレーターとは|제너레이터란|ما.*مولد|ตัวสร้าง"
  ["ai-photos-to-wedding-video"]="photo.*to.*video|照片.*制作|foto.*a.*video|photo.*vers.*vidéo|foto.*zu.*video|foto.*para.*video|写真.*動画|사진.*비ديو|صورة.*فيديو|ภาพ.*วิดีโอ"
  ["wedding-video-no-editing-skills"]="no.*editing|without.*skill|不会剪辑|sin.*editar|sans.*compétence|ohne.*kenntnisse|sem.*saber|編集なし|편집 없이|بدون.*مهارات|ไม่ต้องตัดต่อ"
  ["ai-wedding-video-workflow"]="workflow|flow|流程|flujo|flux|workflow|fluxo|ワークフロー|워크플로우|سير العمل|ขั้นตอน"
  ["ai-wedding-video-privacy"]="privacy|safe|安全|privacidad|sécurité|datenschutz|segurança|プライバシー|프라이버시|خصوصية|ความปลอดภัย"
  ["proposal-video-ideas"]="proposal.*idea|求婚.*创意|propuesta.*idea|demande.*idée|antrag.*idee|pedido.*ideia|プロポーズ.*アイデア|프로포즈.*아이디어|طلب.*فكرة|ขอแต่งงาน.*ไอเดีย"
  ["ai-proposal-video"]="ai.*proposal|AI.*求婚|IA.*propuesta|IA.*demande|KI.*antrag|IA.*pedido|AI.*プロポーズ|AI.*프로포زي|AI.*طلب|AI.*ขอแต่งงาน"
  ["wedding-countdown-video"]="countdown|倒计时|cuenta.*regresiva|compte.*à.*rebours|countdown|contagem.*regressiva|カウントダウン|카운트다운|عد.*تنازلي|นับถอยหลัง"
  ["wedding-invitation-video-guide"]="invitation.*guide|邀请.*指南|invitación.*guía|invitation.*guide|einladung.*guide|convite.*guia|招待.*ガイド|초대.*가이드|دعوة.*دليل|เชิญ.*คู่มือ"
  ["video-wedding-invitation"]="video.*invitation|视频.*请柬|video.*invitación|vidéo.*invitation|video.*einladung|vídeo.*convite|動画.*招待|비디오.*초대|فيديو.*دعوة|วิดีโอ.*การ์ดเชิญ"
  ["wedding-video-without-videographer"]="without.*videographer|no.*photographer|没有摄影师|sin.*fotógrafo|sans.*caméraman|ohne.*kameramann|sem.*fotógrafo|カメラマンなし|촬영기사 없이|بدون.*مصور|ไม่มีช่างภาพ"
  ["diy-wedding-video-phone"]="phone|diy|手机|teléfono|téléphone|handy|celular|スマホ|스마트폰|هاتف|มือถือ"
  ["automatic-wedding-video-editing"]="automatic|auto.*edit|自动|automático|automatique|automatisch|automático|自動|자동|تلقائي|อัตโนมัติ"
  ["wedding-video-types-guide"]="type.*guide|30.*type|类型|tipo|type|art|tipo|タイプ|유형|نوع|ประเภท"
  ["wedding-highlight-video"]="highlight|ไฮไลท์|highlight|highlight|highlight|highlight|ハイライト|하이라이트|ハイライト|วิดีโอไฮไลท์"
  ["wedding-trailer-video"]="trailer|预告片|tráiler|trailer|trailer|trailer|トレーラー|트레일러|تريلر|เทรลเลอร์"
  ["wedding-slideshow-guide"]="slideshow|diaporama|幻灯片|diapositiva|diaporama|diashow|slideshow|スライドショー|슬라이드쇼|عرض الشرائح|สไลด์โชว์"
  ["wedding-wishes-video"]="wishes|祝福|deseos|vœux|wünsche|votos|祝福|축하|تمنيات|คำอวยพร"
  ["couple-slideshow-video"]="couple.*slideshow|成长回忆|pareja.*diapositiva|couple.*diaporama|paar.*diashow|casal.*slideshow|カップル.*スライドショー|커플.*슬라이드쇼|زوجين.*عرض|คู่รัก.*สไลด์"
  ["bride-wedding-video-checklist"]="bride.*checklist|新娘.*清单|novia.*lista|mariée.*checkliste|braut.*checkliste|noiva.*checklist|花嫁.*チェックリスト|신부.*체크리스트|عروس.*قائمة|เจ้าสาว.*เช็คลิสต์"
  ["wedding-video-inspiration"]="inspiration|pinterest|灵感|inspiración|inspiration|inspiration|inspiração|インスピレーション|영감|إلهام|แรงบันดาลใจ"
  ["ai-tools-for-photographers"]="tools.*photographer|摄影师.*工具|herramientas.*fotógrafo|outils.*photographe|tools.*fotograf|ferramentas.*fotógrafo|ツール.*カメラマン|도구.*사진작가|أدوات.*مصور|เครื่องมือ.*ช่างภาพ"
  ["photographer-upsell-video"]="photographer.*upsell|摄影师.*收入|fotógrafo.*ingreso|photographe.*revenu|fotograf.*umsatz|fotógrafo.*renda|カメラマン.*収入|사진작가.*수입|مصور.*دخل|ช่างภาพ.*รายได้"
  ["ai-wont-replace-photographers"]="ai.*replace|AI.*取代|IA.*reemplaza|IA.*remplace|KI.*ersetzt|IA.*substitui|AI.*置き換える|AI.*대체|AI.*يحل|AI.*แทน"
  ["wedding-planner-ai-services"]="planner.*ai|婚庆.*AI|planificador.*IA|planificateur.*IA|planer.*KI|planejador.*IA|プランナー.*AI|플래너.*AI|منسق.*AI|แพลนเนอร์.*AI"
  ["wedding-package-video-upsell"]="package.*video|套餐.*视频|paquete.*video|forfait.*vidéo|paket.*video|pacote.*vídeo|パッケージ.*ビデオ|패키지.*비디오|باقة.*فيديو|แพ็กเกจ.*วิดีโอ"
  ["destination-wedding-video-guide"]="destination|海外|destino|destination|destination|destino|デスティネーション|데스티네이션|وجهة|เดสติเนชัน"
  ["small-wedding-video-ideas"]="small.*wedding|小型|boda.*pequeña|mariage.*petit|kleine.*hochzeit|casamento.*pequeno|小規模.*結婚式|소규모.*웨딩|حفل.*صغير|งาน.*เล็ก"
  ["wedding-video-under-500"]="under.*500|budget.*500|500.*dollar|500.*美元|500.*dólar|500.*dollar|500.*euro|500.*dólar|500.*ドル|500.*달러|500.*دولار|500.*ดอลลาร์"
  ["elopement-wedding-video-guide"]="elopement|私奔|elopement|elopement|elopement|elopement|エロープメント|엘로프먼트|إلوبمنت|อโลปเมนต์"
  ["lgbtq-wedding-video-ideas"]="lgbtq|same.sex|同性|lgbtq|lgbtq|lgbtq|lgbtq|lgbtq|lgbtq|lgbtq|lgbtq"
  ["ai-video-maker-vs-videographer"]="ai.*vs.*videographer|AI.*vs.*摄影师|IA.*vs.*videógrafo|IA.*vs.*caméraman|KI.*vs.*kameramann|IA.*vs.*videógrafo|AI.*vs.*カメラマン|AI.*vs.*촬영기사|AI.*vs.*مصور|AI.*vs.*ช่างภาพ"
  ["best-ai-wedding-video-tools-2026"]="best.*tool|最佳.*工具|mejor.*herramienta|meilleur.*outil|beste.*tool|melhor.*ferramenta|最高.*ツール|최고.*도구|أفضل.*أداة|เครื่องมือ.*ดีที่สุด"
  ["canva-vs-ai-wedding-video"]="canva.*vs|canva.*vs|canva.*vs|canva.*vs|canva.*vs|canva.*vs|canva.*vs|canva.*vs|canva.*vs|canva.*vs"
  ["ai-editor-vs-traditional-editing"]="traditional.*vs.*ai|传统.*vs.*AI|tradicional.*vs.*IA|traditionnel.*vs.*IA|traditionell.*vs.*KI|tradicional.*vs.*IA|従来.*vs.*AI|전통.*vs.*AI|تقليدي.*vs.*AI|传统.*vs.*AI"
  ["how-to-make-wedding-video"]="how.*to.*make|如何制作|cómo.*hacer|comment.*faire|wie.*man.*macht|como.*fazer|作り方|만드는.*방법|كيفية.*صنع|วิธีทำ"
  ["wedding-video-photo-checklist"]="photo.*checklist|照片.*清单|foto.*checklist|photo.*checkliste|foto.*checkliste|foto.*checklist|写真.*チェックリスト|사진.*체크리스트|صورة.*قائمة|ภาพ.*เช็คลิสต์"
  ["wedding-video-music-guide-new"]="music.*guide|音乐.*指南|música.*guía|musique.*guide|musik.*guide|música.*guia|音楽.*ガイド|음악.*가이드|موسيقى.*دليل|เพลง.*คู่มือ"
  ["wedding-video-captions"]="caption|subtitle|字幕|subtítulo|sous-titre|unterschrift|legenda|字幕|자막|ترجمة|คำบรรยาย"
  ["wedding-video-length-guide"]="length|duration|长度|duración|durée|länge|duração|長さ|길이|مدة|ความยาว"
  ["why-couples-choose-ai-video"]="why.*choose|为什么.*选择|por.*qué.*elige|pourquoi.*choisit|warum.*wählen|por.*que.*escolhem|なぜ.*選ぶ|왜.*선택|لماذا.*يختار|ทำไม.*เลือก"
  ["make-first-ai-wedding-video"]="first.*video.*5.*min|5.*分钟|5.*minuto|5.*minute|5.*minuto|5.*分|5.*분|5.*دقيقة|5.*นาที"
  ["free-wedding-video-maker"]="free.*tool|免费|gratuit|kostenlos|gratuito|無料|무료|مجاني|ฟรี"
  ["weddingai-video-guide"]="weddingai.*guide|完整.*指南|guía.*completa|guide.*complet|komplett.*guide|guia.*completo|完全ガイド|완벽.*가이드|دليل.*شامل|คู่มือ.*สมบูรณ์"
  ["weddingai-video-case-studies"]="case.*study|案例|caso.*de.*éxito|étude.*de.*cas|fallstudie|caso.*de.*sucesso|ケーススタディ|사례.*연구|دراسات.*حالة|กรณีศึกษา"
)

echo "=== Smart Filename Alignment ==="
echo ""

for lang in zh es fr de pt ja ko ar th; do
    LANG_DIR="$BASE/$lang"
    echo "=== Processing $lang ==="
    
    RENAMED=0
    FAILED=0
    
    # Find missing canonical files
    for slug in "${!SLUG_KEYWORDS[@]}"; do
        if [ ! -f "$LANG_DIR/$slug" ]; then
            # This canonical file is missing - try to find a match
            KEYWORDS="${SLUG_KEYWORDS[$slug]}"
            
            # Search for a non-canonical file whose first line matches the keywords
            BEST_MATCH=""
            for f in "$LANG_DIR"/*.md; do
                fname=$(basename "$f")
                # Skip if this is already a canonical file
                if echo "${!SLUG_KEYWORDS[@]}" | grep -qw "${fname%.md}"; then
                    continue
                fi
                # Check if the first line (title) matches keywords
                FIRST_LINE=$(head -1 "$f")
                if echo "$FIRST_LINE" | grep -iqE "$KEYWORDS"; then
                    BEST_MATCH="$fname"
                    break
                fi
            done
            
            if [ -n "$BEST_MATCH" ]; then
                echo "  RENAME: $BEST_MATCH -> $slug"
                mv "$LANG_DIR/$BEST_MATCH" "$LANG_DIR/$slug"
                RENAMED=$((RENAMED + 1))
            else
                echo "  MISSING: $slug (no match found)"
                FAILED=$((FAILED + 1))
            fi
        fi
    done
    
    echo "  Renamed: $RENAMED | Still missing: $FAILED"
done

echo ""
echo "=== Final Check ==="
for lang in en zh es fr de pt ja ko ar th; do
    echo -n "$lang: "
    ls "$BASE/$lang" | wc -l
done
