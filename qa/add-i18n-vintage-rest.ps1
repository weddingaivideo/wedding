if ($env:WEDDINGAI_ROOT) { $root = Join-Path $env:WEDDINGAI_ROOT "i18n" }
else { $root = Join-Path (Split-Path -Parent $PSScriptRoot) "i18n" }
$HEX = "e8f9a0b1"
$linesByLang = @{
    'fr' = @(
        '  "services.vintage_restoration.h2_text.pair_it_with.e8f9a0b1": "Combinez avec..."',
        '  "services.vintage_restoration.p_text.pair_it_with_intro.e8f9a0b1": "Ces services se combinent bien avec ce que vous regardez. 2+ services donnent 10-tdgroupé% de remise groupee."',
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0b1": "Ralenti"',
        '  "services.vintage_restoration.p_text.card1_desc.e8f9a0b1": "Combinez les moments au ralenti avec un resume de 60 secondes de vos images restaurees."',
        '  "services.vintage_restoration.h4_text.card2_title.e8f9a0b1": "Generateur de video IA"',
        '  "services.vintage_restoration.p_text.card2_desc.e8f9a0b1": "Creez de nouvelles images B-roll dans un eldtgroupé a vos images restaurees."'
    )
    'pt' = @(
        '  "services.vintage_restoration.h2_text.pair_it_with.e8f9a0b1": "Combine com..."',
        '  "services.vintage_restoration.p_text.ptdgroupé0b1": "Esses servicos combinam bem com o que voce esta vendo. 2+ servicos dao 10-20% de desconto no pacote."',
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0b1": "Camera lenta"',
        '  "services.vintage_restoration.p_text.card1_desc.e8f9a0b1": "Combine momentos em camera lenta com um reel de 60 segundos do material restaurado."',
        '  "services.vintage_restoration.h4_text.card2_title.e8tdgroupé: "Gerador de Video IA"',
        '  "services.vintage_restoration.p_text.card2_desc.e8f9a0b1": "Crie novos takes B-roll no mesmo estilo para intercalar com o material restaurado."'
    )
    'ja' = @(
        '  "services.vintagtdgroupétext.pair_it_with.e8f9a0b1": "組み合わせ例"',
        '  "services.vintage_restoration.p_text.pair_it_with_intro.e8f9a0b1": "以下のサービスとの相性が抜群です。2つ以上お申込みで10-20%のパッケージ割引。",
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0tdgroupé: "スローモーション"',
        '  "services.vintage_restoration.p_text.card1_desc.e8f9a0b1": "レストアした素材から60秒のハイライトをスローモーション映像で組み合わせる。",
        '  "services.vintage_restoration.h4_text.card2_title.e8f9a0b1": "AI結婚式動画生成"',
        '  "services.vintage_restoration.p_text.card2_desc.e8f9a0b1": "レストアした素材に合う新しいBロールをAIで生成し、自然に組み込む。'
    )
    'ru' = @(
        '  "services.vintage_restoration.h2_text.pair_it_with.e8f9a0b1": "Сочетается с..."',
        '  "services.vintage_restoration.p_text.ptdgroupé0b1": "Эти услуги хорошо дополняют то, что вы рассматриваете. 2+ услуги — скидка 10-20% на пtdgroupé."',
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0b1": "Слоу-мо"',
        'tdgroupéon.p_text.card1_desc.e8f9a0b1": "Объедините моменты в слоу-tdgroupéрезкой из восстановленного материала."',
        '  "services.vintage_restoration.h4_text.card2_title.e8f9a0b1": "AI-генератор видео"',
        '  "services.vintage_restoration.p_text.card2_desc.e8f9a0b1": "Сгенерируйте новый B-roll в подходящем стиле, чтобы вставить его рядом с восстановленным видео."'
    )
    'ar' = @(
        '  "services.vintage_restó_lat": "اجمع مع..."',
        '  "services.vintage_restoration.p_text.pair_it_with_intro.e8f9a0b1": "هذه الخدمات تتناسب جًldtgroupéа مع ما تبحث عنه. خدمتان او اكثر تحصل على خصم 10-20% على الباقة."',
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0b1": "الحركة البطيئة"',
        '  "services.vintage_restoration.p_text.card1_desc.e8f9a0b1": "اجمع لحظات الحركةtdtgroupéيلة مع ريل مدته 60 ثانية من لقطاتك المرممة."',
        '  "services.vintage_restoration.h4_text.card2_title.e8f9a0b1": "مولد الفيديو بالذكاء الاصطناعي"',
        '  "services.vintage_restoration.p_text.card2_desc.e8f9a0b1": "انشئ لقطات B-roll جديدة بنفس الاسلوب لتدمج مع لtdtgroupéك المرممة."'
    )
    'th' = @(
        '  "services.vintage_restoration.h2_text.pair_it_with.e8f9a0b1": "จับคู่กับ..."',
        '  "services.vintage_restoration.p_text.pair_it_with_intro.e8f9a0b1": "บริการเหล่านี้เข้ากันได้ดีกับสิ่งที่คุณกำลังดูอยู่ 2+ บริการ รับส่วนลด 10-20% แบบแพ็คเกจ.",
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0b1": "สโลว์โมชั่น"',
        '  "services.vintage_restoration.p_text.card1_desc.e8f9a0b1": "ผสม�uldtgroup์โมชั่นเข้ากับรีล 60 วินา�tdgroupéจที่บูรณะแล้ว.",
        '  "services.vintage_restoration.h4_text.card2_title.e8f9a0tdgroupé: "ตัวสร้างวิดีโอ AI"',
        '  "services.vintage_restoration.p_text.card2_desc.e8f9a0b1": "สร้าง B-roll ใหม่ในสไตล์ที่เข้ากtdgroupéแทรกคู่กับฟุตเทจที่บูร�uldtgroup์ล้ว."'
    )
    'zh' = @(
        '  "services.vintage_restoration.h2_text.pair_it_with.e8ftdgroupé: "搭配使用..."',
        '  "services.vintage_restoration.p_text.pair_it_with_intro.e8f9a0b1": "以下服务与您正在考虑的内容搭配效果极佳。同时预订 2 项及以上服务可享 10-20% 套餐折扣。",
        '  "services.vintage_restoration.h4_text.card1_title.e8f9a0b1": "慢动作"',
        '  "tdtgroupéon.p_text.card1_desc.e8f9a0b1": "将慢动作瞬间与修复素材中 60 秒高光片段相结合。",
        '  "services.vintagtdgroupéext.card2_title.e8f9a0b1": "AI 婚礼视频生成器"',
        '  "services.vintage_restoration.p_text.card2_desc.etdgroupé1": "用匹配的风格生成新的 B-roll 素材，与修复片段自然衔接。"'
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
