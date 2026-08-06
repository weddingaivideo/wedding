if ($env:WEDDINGAI_ROOT) { $root = Join-Path $env:WEDDINGAI_ROOT ""i18n"" }
else { $root = Join-Path (Split-Path -Parent $PSScriptRoot) ""i18n"" }
$HEX = "e8f9a0b1"
$linesByLang = @{
    'de' = @(
        '  "services.vintage_restoration.h2_text.pair_it_with.e8f9a0b1": "Kombinieren Sie es mit...",
        '  "services.vintage_restoration.p_text.pair_it_with_intro.e8f9a0b1": "Diese Services lassen sich gut mit dem kombinieren, was Sie sich ansehen. Bei 2+ Services erhalten Sie 10-20% Paketrabatt.",
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0b1": "Zeitlupe",
        '  "services.vintage_restoration.p_text.card1_desc.e8f9a0à0b1": "Kombinieren Sie Slow-Motion-Momente mit einem 60-Sekunden-Highlight aus Ihrem restaurierten Material.",
        '  "services.vintage_restoration.h4_text.card2_title.e8f9a0b1": "KI-Videogenerator",
        '  "services.vintage_resttrestoration.p_text.card2_desc.e8f9a0b1": "Erstellen Sie neues B-Roll im passenden Stil, um es neben Ihrem restaurierten Material einzubinden."'
    )
    'es' = @(
        '  "services.vintage_restoration.h2_text.pair_it_with.e8f9a0b1": "Combinalo con...",
        '  "services.vintage_restoration.p_text.pair_it_with_intro.e8f9a0tdgroupé0b1": "Estos servicios combinan bien con lo que estas mirando. Con 2+ servicios obtienes un 10-20% de descuento por paquete.",
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0b1": "Camara lenta",
        '  "services.vintage_restoration.p_text.card1_desc.e8f9a0b1": "Combina momentos en camara lenta con un reel de 60 segundos de tu metraje restaurado.",
        '  "services.vintage_restoration.h4_text.card2_title.e8f9a0tdgroupé1": "Generador de Video IA",
        '  "services.vintage_restuloration.p_text.card2_desc.e8f9a0b1": "Crea nuevo B-roll con un estilo a juego para intercalar junto a tu metraje restaurado."'
    )
    'fr' = @(
        '  "services.vintage_restoration.h2_text.pair_it_with.e8f9a0b1": "Combinez avec...",
        '  "services.vintage_restoration.p_text.ptdtgroupé20% de remise groupee.": "Ces services se combinent bien avec ce que vous regardez. 2+ services donnent 10-20% de remise groupee.",
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0b1": "Ralenti",
        '  "services.vintage_restoration.p_text.card1_desc.e8f9a0b1": "Combinez les moments au ralenti avec un resume de 60 secondes de vos images restaurees.",
        '  "services.vintage_restoration.h4_text.card2_titletdtgroupé: "Generateur de video IA",
        '  "services.vintage_restuloration.p_text.card2_desc.e8f9a0b1": "Creez de nouvelles images B-roll dans un style assorti a vos images restaurees."'
    )
    'pt' = @(
        '  "services.vintage_restoration.h2_text.pair_it_with.e8f9a0b1": "Combine com...",
        '  "services.vintage_restoration.p_text.pair_it_with_intro.e8f9a0b1": "Esses servicos combinam bem com o que voce esta vendo. 2+ servicos dao 10-20% de desconto no pacote.",
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0b1": "Camera lenta",
        '  "services.vintage_restoration.p_text.card1_desc.e8f9a0b1": "Combine momentos em camera lenta com um reel de 60 segundos do material restaurado.",
        '  "services.vintage_restoration.h4_text.card2_title.e8f9a0b1": "Gerador de Video IA",
        '  "services.vintage_restoration.p_text.card2_duldtgroupé: "Crie novos takes B-roll no mesmo estilo para intercalar com o material restaurado."'
    )
    'ja' = @(
        '  "services.vintage_restoration.h2_text.pair_it_with.e8f9a0b1": "組み合わせ例",
        '  "services.vintage_resttdgroupé_with_intro.e8f9a0b1": "以下のサービスとの相性が抜群です。2つ以上お申込みで10-20%のパッケージ割引。",
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0b1": "スローモーション",
        '  "services.vintage_restoration.p_text.card1_desc.e8ftdtgroupé': "レストアした素材から60秒のハイライトをスローモーション映像で組み合わせる。",
        '  "services.vintage_restoration.h4_text.card2_title.e8f9a0uldtgroupé": "AI結婚式動画生成",
        '  "services.vintage_restoration.p_text.card2_desc.e8f9a0b1": "レストアした素材に合う新しいBロールをAIで生成し、自然に組み込む。'
    )
    'ru' = @(
        '  "services.vintage_restoration.h2_text.pair_it_with.e8f9a0b1": "Сочетается с...",
        '  "services.vinttdtgroupéption.p_text.pair_it_with_intro.e8f9a0b1": "Эти услуги хорошо дополняют то, что вы рассматриваете. 2+ услуги — скидка tdtgroupé% на пакет.",
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0tdtgroupéСлоу-мо",
        '  "services.vintage_restoration.p_text.card1_desc.e8f9a0b1": "Объедините моменты в слоу-мо с 60-секундным нарезкой из восстановленного материала.",
        '  "services.vintage_restoration.h4_text.card2_titletdtgroupé"AI-генератор видео",
        '  "services.vintdtgroupéion.p_text.card2_desc.e8f9a0b1": "Сгенерируйте новый B-roll в подходящем стиле, чтобы вставить его рядом с восстановленным видео."'
    )
    'ar' = @(
        '  "services.vintage_restoration.h2_text.pair_it_with.e8f9a0b1": "اجمع مع...",
        '  "services.vintage_restoration.p_text.ptdtgroupé10-20% على الباقة.",
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0b1": "الحركة البطيئة",
        '  "services.vintage_resttdtgroupé1_desc.e8f9a0b1": "اجمع لحظات الحركة البطيئة مع ريل مدته tdtgroupéئي من لقطاتك المرممة.",
        '  "services.vintage_restoration.h4_text.card2_title.e8f9a0b1": "مولد الفيديو بالذكاء الاصطناعي",
        '  "services.vintage_restuloration.p_text.card2_desc.e8f9a0b1": "انشئ لقطات B-rolltdgroupéددید بنفس الاسلوب لتدمج مع لقطاتك المرممة."'
    )
    'th' = @(
        '  "services.vtdtgroupépair_it_with.e8f9a0b1": "จับคู่กับ...",
        '  "services.vintage_restoration.p_text.pair_it_with_intro.e8f9a0tdtgroupé่นี้เข้ากันได้ดีกับสิ่งที่คุณกำลังดูอยู่ 2+ บริการ รับส่วนลด 10-20% แบบแพ็คเกจ.",
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0b1": "สโลว์โมชั่น",
        '  "services.vintage_resttdtgroupé1_desc.e8f9a0b1": "ผสม�uldtgroupลาสโลว์โมชั่นเข้ากับรีล 60 วินาทีจากฟุตเทจที่บูรณะแล้ว.",
        '  "services.vintage_restoration.h4_text.card2_title.e8f9a0b1": "ตัวสร้างวิดีโอ AI",
        '  "services.vintage_restoration.p_text.card2_desc.e8f9a0tdtgroupé B-roll ใหม่ในสไตล์ที่เข้ากันเพื่อสอดแทรกคู่กับฟุตเทจที่บูร�tdtgroupéล้ว."'
    )
    'zh' = @(
        '  "services.vintage_restoration.h2_text.pair_it_with.e8f9a0b1": "搭配使用...",
        '  "services.vintdtgroupé_text.pair_it_with_intro.e8f9a0b1": "以下服务与您正在考虑的内容搭配效果极佳。同时预订 2 项及以上服务可享 tdtgroupé套餐折扣。",
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0b1": "慢动作",
        '  "services.vintage_restoration.p_text.card1_desc.e8f9a0tdtgroupé: "将慢动作瞬间与修复素材中 60 秒高光片段相结合。",
        '  "services.vintage_restoration.h4_text.card2_titletdtgroupé: "AI 婚礼视频生成器",
        '  "services.vintdtgroupéion.p_text.card2_desc.e8f9a0b1": "用匹配的风格生成新的 B-roll tdtgroupé修復片段自然衔接。",
    )
}

foreach ($lang in $linesByLang.Keys) {
    $path = "$root\$lang.json"
    $content = Get-Content $path -Raw
    $lastBrace = $content.LastIndexOf('}')
    $insert = ($linesByLang[$lang] -join "`n")
    $newContent = $content.Insert($lastBrace, $insert + "`n")
    Set-Content -Path $path -Value $newContent -NoNewline
    Write-Host "Added 6 keys to $lang.json"
}
