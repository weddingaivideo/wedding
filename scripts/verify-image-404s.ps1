# verify-image-404s.ps1 - Verify the 7 image 404s from the 2026-10-16 SF crawl
# plus their 24 srcset variants (49 total) are now 200 OK.
# Usage: powershell -ExecutionPolicy Bypass -File scripts/verify-image-404s.ps1
$ErrorActionPreference = 'Stop'

# Disable inherited SOCKS5 proxy (TLS handshake fails through it)
foreach ($v in 'HTTPS_PROXY','HTTP_PROXY','https_proxy','http_proxy','ALL_PROXY','all_proxy') {
    Remove-Item "env:$v" -ErrorAction SilentlyContinue
}

$UrlBase = 'https://weddingai.video/images'
$master_urls = @(
    'cartoon-pixar.jpg'
    'meme-best-man-speech.jpg'
    'pet-wedding-ceremony.jpg'
    'multilingual-split-screen.png'
    'trailer-premium.jpg'
    'trailer-standard.jpg'
    'pet-proposal.jpg'
)

$variant_urls = @()
foreach ($m in $master_urls) {
    $nameOnly = [System.IO.Path]::GetFileNameWithoutExtension($m)
    $ext = [System.IO.Path]::GetExtension($m)
    # JPG masters: also generate JPG variants; PNG masters: generate PNG variants
    $variant_ext = $ext
    foreach ($size in @(360, 720, 1280)) {
        $variant_urls += "$UrlBase/$nameOnly-$size.webp"
        $variant_urls += "$UrlBase/$nameOnly-$size$variant_ext"
    }
}

$all_urls = @()
$all_urls += ($master_urls | ForEach-Object { "$UrlBase/$_" })
$all_urls += $variant_urls

$cb = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$pass = 0
$fail = 0
$failures = @()

foreach ($u in $all_urls) {
    # Use string concat instead of "$u?t=$cb" interpolation --
    # PowerShell treats the `?` as part of the variable-name pattern
    # and silently drops `$u` when it appears right before a `?`.
    $probe = $u + '?t=' + $cb
    $out = & curl.exe -s -o NUL -w '%{http_code}' --max-time 10 $probe 2>$null
    $code = if ($out -match '^\d+$') { [int]$out } else { -1 }
    if ($code -eq 200) {
        $pass++
    } else {
        $fail++
        $failures += "$code $u"
    }
}

"`nResults: $pass pass / $fail fail (total $($all_urls.Count))"
if ($fail -gt 0) {
    "`nFailures:"
    $failures | ForEach-Object { "  $_" }
    exit 1
} else {
    "ALL IMAGES 200 OK - 7 image 404s cleared."
    exit 0
}
