#!/usr/bin/env pwsh
# verify-security-headers.ps1 - Tier 4 verification matrix.
#
# Confirms that all 10 SF-flagged security headers are present on
# production. The 2026-10-16 SF crawl reported 137-138 URLs missing
# HSTS / CSP / X-Frame-Options / X-Content-Type-Options /
# Referrer-Policy, but live probes show all headers ARE present.
# Likely the crawl hit a stale CF Pages edge cache or a different
# environment. This script makes the actual production state
# auditable.
#
# Headers checked (10):
#   - Strict-Transport-Security        (138 URLs flagged)
#   - Content-Security-Policy          (138 URLs flagged)
#   - X-Frame-Options                  (137 URLs flagged)
#   - X-Content-Type-Options           (137 URLs flagged)
#   - Referrer-Policy                  (138 URLs flagged)
#   - Permissions-Policy               (preventive)
#   - Cross-Origin-Opener-Policy       (preventive)
#   - Cross-Origin-Embedder-Policy     (preventive)
#   - Reporting-Endpoints              (CSP report delivery)
#   - X-XSS-Protection                 (set to 0 to disable old filter)
#
# Probe matrix: 5 representative URLs x 1 lang = 5 probes.
# Expected: all 50 (URL x header) cells filled.
$ErrorActionPreference = 'Stop'

[System.Environment]::SetEnvironmentVariable('HTTPS_PROXY', [string]::Empty, [System.EnvironmentVariableTarget]::Process)
[System.Environment]::SetEnvironmentVariable('HTTP_PROXY',  [string]::Empty, [System.EnvironmentVariableTarget]::Process)
$env:HTTPS_PROXY = $null
$env:HTTP_PROXY  = $null

$URLS = @('', 'pricing/', 'about/', 'blog/', 'services/', 'services/personalization/multilingual/', 'tools/', 'tools/wedding-seating-chart-maker/', 'blog/why-couples-choose-ai-video/', 'order/')

$HEADERS = @(
    'strict-transport-security'
    'content-security-policy'
    'x-frame-options'
    'x-content-type-options'
    'referrer-policy'
    'permissions-policy'
    'cross-origin-opener-policy'
    'cross-origin-embedder-policy'
    'reporting-endpoints'
    'x-xss-protection'
)

$CB = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()

$TotalCells = 0
$Present    = 0
$Missing    = @()

foreach ($p in $URLS) {
    $url = "https://weddingai.video/$p" + '?t=' + $CB
    $tmp = [System.IO.Path]::GetTempFileName()
    try {
        & curl.exe -sI $url -o $tmp | Out-Null
        $body = Get-Content -LiteralPath $tmp -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    } finally {
        # No clean up; temp file is small.
    }
    if (-not $body) { $Missing += "$url :: no body"; continue }

    foreach ($h in $HEADERS) {
        $TotalCells++
        if ($body -match "(?im)^${h}:") {
            $Present++
        } else {
            $Missing += "$url :: $h missing"
        }
    }
    Write-Host ("  [ok]  {0}" -f $url)
}

Write-Host ''
Write-Host "Cells: $Present / $TotalCells present"
if ($Missing.Count -gt 0) {
    Write-Host "MISSING:" -ForegroundColor Yellow
    $Missing | ForEach-Object { Write-Host "  $_" }
    exit 1
}
Write-Host "All 10 security headers present on all probed URLs." -ForegroundColor Green
exit 0
