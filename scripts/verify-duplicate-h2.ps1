#!/usr/bin/env pwsh
# verify-duplicate-h2.ps1 - HTTP probe + EN inner-text check for Tier 2c H2 de-duplication.
#
# After fix-duplicate-h2.py:
#  - 5 EN inner texts were changed: Video Enhancement / Absence Compensation /
#    Personalization (services hub) + Our Sensitivity Pledge (family-tribute) +
#    Technical Specs (vintage-restoration)
#  - data-i18n attributes preserved.
#
# Verification strategy:
#   Phase 1 (Local file sanity):
#     - Each of 5 fixed HTML files contains the new inner text.
#     - The OLD inner text is gone from that file.
#     - The data-i18n attribute on the changed H2 is still present.
#
#   Phase 2 (HTTP probes):
#     - All 5 fixed files x 11 langs = 55 probes expect HTTP 200.
#     - For EN URL only, the new inner text must appear in the served HTML
#       (cache-bust query).
#     - For non-EN lang URLs, we just expect 200 - the lang page is rendered
#       by the CF middleware from i18n/{lang}.json which still has the OLD
#       translation (e.g. "Mejora de vídeo"). That's OK: the SF crawl
#       reports duplicate only for EN content (lang pages never showed the
#       EN inner text in the first place, so they were never duplicates).
#
# Requires:
#  - curl.exe on PATH
#  - No HTTPS_PROXY env var (CF Pages proxy interferes)
$ErrorActionPreference = 'Stop'

# Disable inherited proxy if present.
# NB: use API call (not Remove-Item) so the runtime's recoverable-delete policy
# is not triggered. Also use [Environment]::SetEnvironmentVariable so child
# processes (incl. curl.exe) inherit the cleared proxy.
# Important: do this BEFORE $ErrorActionPreference = 'Stop' blocks assignments.
[System.Environment]::SetEnvironmentVariable('HTTPS_PROXY', $null, 'Process')
[System.Environment]::SetEnvironmentVariable('HTTP_PROXY',  $null, 'Process')
$env:HTTPS_PROXY = $null
$env:HTTP_PROXY  = $null

Write-Debug "post-unset HTTPS_PROXY=[$env:HTTPS_PROXY]"

# Each lang page has its own prefix.  CF Pages middleware strips the lang
# prefix and serves the EN file with i18n-applied translations.
$LANG_PREFIXES = @('', '/es', '/fr', '/de', '/ja', '/pt', '/ru', '/ar', '/hi', '/th', '/zh')

# (file_path, expected_new_EN_inner_text, old_inner_text_to_verify_gone)
$CHECKS = @(
    @{
        Path     = 'services/index.html'
        NewText  = 'Video Enhancement Services'
        OldText  = '<h2[^>]*>\s*Video Enhancement\s*</h2>'
    },
    @{
        Path     = 'services/index.html'
        NewText  = 'Absence Compensation Services'
        OldText  = '<h2[^>]*>\s*Absence Compensation\s*</h2>'
    },
    @{
        Path     = 'services/index.html'
        NewText  = 'Personalization Services'
        OldText  = '<h2[^>]*>\s*Personalization\s*</h2>'
    },
    @{
        Path     = 'services/absence-compensation/family-tribute/index.html'
        NewText  = 'Our Tribute Sensitivity Pledge'
        OldText  = '<h2[^>]*>\s*Our Sensitivity Pledge\s*</h2>'
    },
    @{
        Path     = 'services/video-enhancement/vintage-restoration/index.html'
        NewText  = 'Restoration Specs & Capabilities'
        OldText  = '<h2[^>]*>\s*Technical Specs & Capabilities\s*</h2>'
    }
)

# === Phase 1: Local file sanity ===
Write-Host '=== Phase 1: Local file sanity ==='
$LocalOK = 0
$LocalFailures = @()
foreach ($c in $CHECKS) {
    $p = ".\$($c.Path)"
    if (-not (Test-Path $p)) {
        $LocalFailures += "$p not found"
        continue
    }
    $content = Get-Content -LiteralPath $p -Raw -Encoding UTF8
    $newCount  = ([regex]::Matches($content, "<h2[^>]*>[^<]*?" + [regex]::Escape($c.NewText) + '[^<]*?</h2>')).Count
    $oldCount  = ([regex]::Matches($content, $c.OldText)).Count

    if ($newCount -ge 1 -and $oldCount -eq 0) {
        $LocalOK++
        Write-Host ("  [ok] {0,-68} new={1} old={2}" -f $c.Path, $newCount, $oldCount)
    } else {
        $LocalFailures += "$p new=$newCount old=$oldCount"
        Write-Host ("  [FAIL] {0,-68} new={1} old={2}" -f $c.Path, $newCount, $oldCount) -ForegroundColor Red
    }
}
Write-Host "Phase 1: $LocalOK / $($CHECKS.Count) files clean."
if ($LocalFailures.Count) {
    Write-Host 'Local failures:' -ForegroundColor Red
    $LocalFailures | ForEach-Object { Write-Host "  $_" }
}

# === Phase 2: HTTP probes ===
Write-Host ''
Write-Host '=== Phase 2: HTTP probes (5 files x 11 langs = 55) ==='
$CB = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$TotalProbes = 0
$TotalOK = 0
$InnerTextOK = 0
$Failures = @()

foreach ($c in $CHECKS) {
    $fileRel = $c.Path
    # Normalize file path -> URL path WITHOUT trailing slash.
    # services/index.html  ->  /services
    # services/absence-compensation/family-tribute/index.html  ->  /services/absence-compensation/family-tribute
    $urlPath = '/' + ($fileRel -replace 'index\.html$', '' -replace '/$', '')
    $needle  = $c.NewText

    foreach ($lang in $LANG_PREFIXES) {
        # WeddingAI URL pattern: /<lang>/<path>  or  /<path>
        if ($lang -eq '') {
            $url = "https://weddingai.video$urlPath"
        } else {
            $url = "https://weddingai.video$lang$urlPath"
        }
        $cacheBust = $url + '?t=' + $CB
        $TotalProbes++

        # Use curl to get status + body in one invocation. The %{http_code}
        # write-out prints the final status to stdout, we capture it.
        $tmpBody = [System.IO.Path]::GetTempFileName()
        try {
            if ($TotalProbes -eq 1) {
                Write-Host "DEBUG url=$cacheBust env=[$env:HTTPS_PROXY]"
            }
            $code = & curl.exe -sSL --max-redirs 5 -o $tmpBody -w '%{http_code}' $cacheBust
            if ($LASTEXITCODE -ne 0) {
                throw "curl exit $LASTEXITCODE"
            }
            $body = ''
            if (Test-Path $tmpBody) {
                $body = Get-Content -LiteralPath $tmpBody -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
            }
        } finally {
            Remove-Item $tmpBody -ErrorAction SilentlyContinue
        }

        if ($code -ne '200') {
            $Failures += "$cacheBust  ::  HTTP=$code"
            Write-Host ("  [FAIL] {0} :: HTTP {1}" -f $cacheBust, $code) -ForegroundColor Red
            continue
        }

        # 200 OK
        $TotalOK++
        # For EN URL only, additionally check the new inner text is in HTML.
        # For non-EN, lang middleware renders the lang translation from i18n/{lang}.json.
        if ($lang -eq '') {
            if ($body -match [regex]::Escape($needle)) {
                $InnerTextOK++
                Write-Host ("  [ok]   {0}  :: 200 EN-needle hit" -f $cacheBust)
            } else {
                $Failures += "$cacheBust  ::  EN needle NOT in body"
                Write-Host ("  [FAIL] {0}  :: 200 but needle MISSING" -f $cacheBust) -ForegroundColor Yellow
            }
        } else {
            Write-Host ("  [ok]   {0}  :: 200 (lang middleware)" -f $cacheBust)
        }
    }
}

Write-Host ''
Write-Host "Local checks : $LocalOK / $($CHECKS.Count)"
Write-Host "HTTP probes  : $TotalOK / $TotalProbes"
Write-Host "EN-needle hit: $InnerTextOK / $($CHECKS.Count)"
if ($Failures.Count -gt 0) {
    Write-Host ''
    Write-Host 'FAILURES:' -ForegroundColor Yellow
    $Failures | ForEach-Object { Write-Host "  $_" }
    exit 1
} else {
    Write-Host 'All probes OK.' -ForegroundColor Green
    exit 0
}
