# Replace inline JS in HTML files with <script src="js/main.js"></script>
$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"
$htmlFiles = Get-ChildItem $root -Recurse -Filter "*.html" -File | Where-Object { $_.Name -ne "google-site-verification.html" }
$fixed = 0

# Patterns to match each kind of inline script
$patterns = @(
    '(?s)<script>\s*document\.querySelector\(.\.mobile-menu-toggle.\).*?\}\);\s*</script>',
    '(?s)<script>\s*document\.querySelector\(.\.order-form.\).*?btn\.textContent\s*=\s*.Sending\.\.\..*?\}\s*\}\);\s*</script>'
)

foreach ($file in $htmlFiles) {
    $c = Get-Content $file.FullName -Raw
    $origC = $c

    # Compute relative path to js/main.js based on file location
    $relPath = $file.FullName.Substring($root.Length).TrimStart('\').Replace('\','/')
    $depth = ($relPath.Split('/').Count - 1)
    $jsPath = ''
    for ($i = 0; $i -lt $depth; $i++) { $jsPath += '../' }
    $jsPath += 'js/main.js'

    foreach ($pat in $patterns) {
        $c = [regex]::Replace($c, $pat, "<script src=`"$jsPath`"></script>")
    }

    if ($c -ne $origC) {
        Set-Content $file.FullName $c -NoNewline
        Write-Host "FIXED: $($file.FullName.Substring($root.Length)) -> $jsPath"
        $fixed++
    }
}

Write-Host "---"
Write-Host "Total fixed: $fixed"
