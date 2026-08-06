# Assess structural damage to each file
$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"
$files = @("about.html","gallery.html","index.html","order.html","privacy.html","cartoon-style.html","meme-generator.html")
foreach ($f in $files) {
    $path = "$root\$f"
    if (-not (Test-Path $path)) { $path = "$root\services\personalization\$f" }
    $c = Get-Content $path -Raw
    $hasBtnNav = $c -match 'class="btn-nav"'
    $hasNavList = $c -match 'class="nav-list"'
    $liCount = ([regex]::Matches($c, '<li>')).Count
    $mainOpen = ([regex]::Matches($c, '<main>')).Count
    $mainClose = ([regex]::Matches($c, '</main>')).Count
    $headerOpen = ([regex]::Matches($c, '<header')).Count
    $headerClose = ([regex]::Matches($c, '</header>')).Count
    $footerOpen = ([regex]::Matches($c, '<footer')).Count
    $footerClose = ([regex]::Matches($c, '</footer>')).Count
    Write-Host "${f}: nav=$hasNavList btn=$hasBtnNav li=$liCount main=$mainOpen/$mainClose header=$headerOpen/$headerClose footer=$footerOpen/$footerClose"
}
