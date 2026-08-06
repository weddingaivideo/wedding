# Mark remaining dead href="#" links with TODO comments
$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"
$htmlFiles = Get-ChildItem $root -Recurse -Filter "*.html" -File | Where-Object { $_.Name -ne "google-site-verification.html" }
$marked = 0

foreach ($file in $htmlFiles) {
    $c = Get-Content $file.FullName -Raw
    $origC = $c

    # Mark WhatsApp dead links with TODO comment
    $c = $c -replace '<a href="#">WhatsApp:\s*([^<]+)</a>',
        '<!-- TODO: replace with real WhatsApp link e.g. https://wa.me/15550000000 --><a href="#" onclick="return false;" title="TODO: real WhatsApp link">WhatsApp: $1</a>'

    # Mark social media dead links (Instagram, TikTok, YouTube) with TODO
    $c = $c -replace '<a href="#" aria-label="(Instagram|TikTok|YouTube)">',
        '<!-- TODO: real social media link --><a href="#" onclick="return false;" title="TODO: real social URL" aria-label="$1">'

    # Mark generic <a href="#" class="contact-method"> dead links (in order.html contact grid)
    $c = $c -replace '(<a href="#" class="contact-method">)',
        '<!-- TODO: real contact method URL --><!--$1-->'

    if ($c -ne $origC) {
        Set-Content $file.FullName $c -NoNewline
        $markInFile = ([regex]::Matches($c, 'TODO:')).Count - ([regex]::Matches($origC, 'TODO:')).Count
        if ($markInFile -gt 0) {
            Write-Host "MARKED $markInFile in: $($file.Name)"
            $marked += $markInFile
        }
    }
}

Write-Host "---"
Write-Host "Total TODO marks added: $marked"
