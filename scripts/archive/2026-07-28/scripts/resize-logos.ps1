$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"
$files = Get-ChildItem -Path $root -Recurse -Filter "*.html"

foreach ($file in $files) {
    $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
    $original = $content

    # 把所有 logo height 改成 72（header 和 footer 都统一）
    $content = $content -replace '(logo-full\.jpeg" alt="WeddingAI\.video" )height="(32|7)"', '$1height="72"'

    if ($content -ne $original) {
        $content | Set-Content -Path $file.FullName -NoNewline -Encoding UTF8
        Write-Host "Updated: $($file.Name)"
    }
}
Write-Host "Done."
