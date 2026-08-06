$ErrorActionPreference = "Stop"
$ts = Get-Date -Format "yyyyMMddHHmmss"
$paths = @(
    "/styles.min.css",
    "/styles.css",
    "/js/main.min.js",
    "/js/i18n.js",
    "/styles/i18n.css",
    "/images/hero-wedding-vineyard-1920.webp",
    "/images/og-image-1200x630.jpg"
)
$headers = @{"User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
Write-Host "=== CORP verification (cache-busted) ==="
foreach ($p in $paths) {
    try {
        $h = Invoke-WebRequest -Uri "https://weddingai.video${p}?cb=$ts" -Method HEAD -UseBasicParsing -Headers $headers
        $corp = $h.Headers["Cross-Origin-Resource-Policy"]
        if ($corp) {
            Write-Host ("  {0,-50} CORP: {1}" -f $p, $corp) -ForegroundColor Green
        } else {
            Write-Host ("  {0,-50} CORP: <not set>" -f $p) -ForegroundColor Red
        }
    } catch {
        Write-Host ("  {0,-50} ERROR: {1}" -f $p, $_.Exception.Message) -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== HTML page headers (no CORP expected, linkable) ==="
$htmlPaths = @("/", "/zh/", "/order/")
foreach ($p in $htmlPaths) {
    try {
        $h = Invoke-WebRequest -Uri "https://weddingai.video${p}?cb=$ts" -Method HEAD -UseBasicParsing -Headers $headers
        $corp = $h.Headers["Cross-Origin-Resource-Policy"]
        $coep = $h.Headers["Cross-Origin-Embedder-Policy"]
        $coop = $h.Headers["Cross-Origin-Opener-Policy"]
        Write-Host ("  {0,-20} CORP={1}  COEP={2}  COOP={3}" -f $p, $corp, $coep, $coop)
    } catch {
        Write-Host ("  {0,-20} ERROR: {1}" -f $p, $_.Exception.Message) -ForegroundColor Red
    }
}
