#!/usr/bin/env pwsh
# verify-hreflang-dedup.ps1 - HTTP probe matrix for Tier 3 Hreflang dedup fix.
#
# After middleware fix (functions/_middleware.js strip regex updated to
# match self-closing <link ... /> forms):
#   - 7 tools pages: each has exactly 1 canonical + 12 alternates (no dups)
#   - Plus a parallel sample of 5 unaffected pages (control)
#
# We re-fetch each URL, count distinct (rel, hreflang) pairs, and verify:
#   - count(canonical) == 1
#   - count(alternate hreflang=*) == 12
#   - distinct hreflang values == 12 (en, zh, es, fr, de, pt, ja, ru, ar, th, hi, x-default)
#
# Also: 1 URL had Page Titles: Multiple / Multiple <body> / Multiple <head>
#   (https://weddingai.video/tools/ — note: the SF audit doesn't even know
#   the source file has a stray <!DOCTYPE html> embedded in the nav menu;
#   this is a separate structural issue that needs the user's call.)
#
# Requires:
#  - curl.exe on PATH
#  - HTTPS_PROXY env var cleared (CF Pages proxy interferes)
$ErrorActionPreference = 'Stop'

# Disable inherited proxy.  We must use [string]::Empty (NOT $null) because
# [Environment]::SetEnvironmentVariable with $null becomes an empty string,
# and curl still sees HTTPS_PROXY='' which ... actually works for some
# Windows curl builds but not others. Using EnvironmentVariableTarget::Process
# with an empty string reliably removes the variable from the process env.
[System.Environment]::SetEnvironmentVariable('HTTPS_PROXY', [string]::Empty, [System.EnvironmentVariableTarget]::Process)
[System.Environment]::SetEnvironmentVariable('HTTP_PROXY',  [string]::Empty, [System.EnvironmentVariableTarget]::Process)
$env:HTTPS_PROXY = $null
$env:HTTP_PROXY  = $null

$CB = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()

# Affected URLs (7 unique tools pages; 3 blog URLs in audit all 301 to
# one of these 2 tool pages).
$AFFECTED = @(
    'tools/wedding-seating-chart-maker/'
    'tools/wedding-budget-calculator/'
    'tools/wedding-hashtag-generator/'
    'tools/wedding-photo-book-planner/'
    'tools/wedding-video-invitation-maker/'
    'tools/wedding-invitation-maker/'
    'tools/save-the-date-maker/'
)

# Control URLs (unaffected homepage/blog/pricing/service pages).
$CONTROL = @(
    ''
    'pricing/'
    'about/'
    'blog/'
    'services/'
)

$EXPECTED_HREFLANGS = @('en','zh','es','fr','de','pt','ja','ru','ar','th','hi','x-default')

$RE_HREFLANG = [regex]'<link[^>]+rel="alternate"[^>]+hreflang="([^"]+)"[^>]*>'
$RE_CANON    = [regex]'<link[^>]+rel="canonical"[^>]+>'

function Check-Url {
    param($UrlPath)
    # Normalize: UrlPath may or may not start with '/'. Always produce
    # /path form before concatenating to base URL to avoid
    # https://weddingai.videotools/... (missing slash).
    $normalized = $UrlPath
    if (-not $normalized.StartsWith('/')) { $normalized = '/' + $normalized }
    $url = "https://weddingai.video$normalized" + '?t=' + $CB

    $tmp = [System.IO.Path]::GetTempFileName()
    try {
        $code = & curl.exe -sSL --max-redirs 5 -o $tmp -w '%{http_code}' $url
        if ($LASTEXITCODE -ne 0) { return @{ url = $url; code = "EXIT_$LASTEXITCODE"; hl = @(); canon = @() } }
        $body = Get-Content -LiteralPath $tmp -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    } finally {
        # Temp file left for diagnostics; mavis-trash not needed.
    }

    $canon = @($RE_CANON.Matches($body) | ForEach-Object { $_.Value })
    $hl = @($RE_HREFLANG.Matches($body) | ForEach-Object { $_.Groups[1].Value })

    return @{ url = $url; code = $code; hl = $hl; canon = $canon }
}

$Results = @()
Write-Host "=== Phase 1: Affected URLs (7 tools pages) ==="
foreach ($p in $AFFECTED) {
    $r = Check-Url $p
    $canonCount = $r.canon.Count
    $hlCount = $r.hl.Count
    $hlUnique = ($r.hl | Sort-Object -Unique).Count
    $hlDups = ($r.hl | Group-Object | Where-Object { $_.Count -gt 1 }).Count

    $ok = ($r.code -eq '200') -and ($canonCount -eq 1) -and ($hlCount -eq 12) -and ($hlUnique -eq 12) -and ($hlDups -eq 0)
    $marker = if ($ok) { "[ok]  " } else { "[FAIL]" }
    Write-Host ("  {0} canon={1} hl={2} unique={3} dups={4}  {5}" -f $marker, $canonCount, $hlCount, $hlUnique, $hlDups, $r.url)
    if (-not $ok) {
        Write-Host "         hl list: $($r.hl -join ', ')"
        Write-Host "         canon:   $($r.canon -join ' || ')"
    }
    $Results += [PSCustomObject]@{
        Section = 'Affected'
        Path    = $p
        Code    = $r.code
        Ok      = $ok
        Canon   = $canonCount
        HL      = $hlCount
        HLUnique = $hlUnique
        HLDups   = $hlDups
    }
}

Write-Host ''
Write-Host "=== Phase 2: Control URLs (5 unaffected pages, must be 1+12) ==="
foreach ($p in $CONTROL) {
    $r = Check-Url $p
    $canonCount = $r.canon.Count
    $hlCount = $r.hl.Count
    $hlUnique = ($r.hl | Sort-Object -Unique).Count
    $hlDups = ($r.hl | Group-Object | Where-Object { $_.Count -gt 1 }).Count

    $ok = ($r.code -eq '200') -and ($canonCount -eq 1) -and ($hlCount -eq 12) -and ($hlUnique -eq 12) -and ($hlDups -eq 0)
    $marker = if ($ok) { "[ok]  " } else { "[FAIL]" }
    Write-Host ("  {0} canon={1} hl={2} unique={3} dups={4}  {5}" -f $marker, $canonCount, $hlCount, $hlUnique, $hlDups, $r.url)
    $Results += [PSCustomObject]@{
        Section = 'Control'
        Path    = $p
        Code    = $r.code
        Ok      = $ok
        Canon   = $canonCount
        HL      = $hlCount
        HLUnique = $hlUnique
        HLDups   = $hlDups
    }
}

Write-Host ''
$failed = $Results | Where-Object { -not $_.Ok }
$passed = $Results | Where-Object { $_.Ok }
Write-Host "Passed: $($passed.Count) / $($Results.Count)"
if ($failed.Count -gt 0) {
    Write-Host "FAILED:" -ForegroundColor Yellow
    $failed | Format-Table -AutoSize
    exit 1
}
Write-Host "All hreflang counts clean (1 canonical + 12 distinct alternates, no dups)." -ForegroundColor Green
exit 0
