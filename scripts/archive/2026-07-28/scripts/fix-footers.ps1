# Fix footer dead links and add Legal section
$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"
$htmlFiles = Get-ChildItem $root -Recurse -Filter "*.html" -File | Where-Object { $_.Name -ne "google-site-verification.html" -and $_.Name -ne "privacy.html" -and $_.Name -ne "terms.html" }
$fixed = 0

foreach ($file in $htmlFiles) {
    $c = Get-Content $file.FullName -Raw
    $origC = $c

    # Compute relative path to root
    $relPath = $file.FullName.Substring($root.Length).TrimStart('\').Replace('\','/')
    $depth = ($relPath.Split('/').Count - 1)
    $rootPath = ''
    for ($i = 0; $i -lt $depth; $i++) { $rootPath += '../' }

    # Fix Privacy Policy dead link
    $c = $c -replace '<a href="#">Privacy Policy</a>', "<a href=`"${rootPath}privacy.html`">Privacy Policy</a>"

    # Fix Terms of Service dead link
    $c = $c -replace '<a href="#">Terms of Service</a>', "<a href=`"${rootPath}terms.html`">Terms of Service</a>"

    if ($c -ne $origC) {
        Set-Content $file.FullName $c -NoNewline
        Write-Host "FIXED: $($file.FullName.Substring($root.Length))"
        $fixed++
    }
}

Write-Host "---"
Write-Host "Total fixed: $fixed"
