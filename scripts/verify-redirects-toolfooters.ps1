# verify-redirects-toolfooters.ps1 - 132-probe matrix for the 2026-10-16 tool-footer cleanup
# Usage: powershell -ExecutionPolicy Bypass -File scripts/verify-redirects-toolfooters.ps1
# Expects: 100% pass = all 132 probes return 301 with Location header matching expected target
#
# Pattern (from weddingai memory):
#   - real curl.exe with --max-redirs 0 (NOT --max-redir)
#   - 10s connect/read timeout to avoid hangs on in-flight deploy
#   - cache-bust via ?t=<epoch-ms>
#   - 132 probes = 12 broken URLs x 11 langs (en + 10 i18n)
#
# Exit codes: 0 = all pass, 1 = any probe failed.

$ErrorActionPreference = 'Stop'

# Disable any inherited proxy env vars. CF Pages is reachable directly; the
# SOCKS5 proxy at 127.0.0.1:7897 (if set) fails the TLS handshake for some
# URLs (curl exit 35 "SSL/TLS connection failed"). See memory note
# 2026-10-15 "LobsterAI .lnk and socks5 proxy" for the same root cause.
foreach ($v in 'HTTPS_PROXY','HTTP_PROXY','https_proxy','http_proxy','ALL_PROXY','all_proxy') {
    Remove-Item "env:$v" -ErrorAction SilentlyContinue
}

$BASE = 'https://weddingai.video'
$langs = @('', '/zh', '/hi', '/th', '/ar', '/ru', '/ja', '/pt', '/de', '/fr', '/es')
$pairs = @(
    @{ Broken = '/services/wedding-trailer/';             Target = '/services/personalization/wedding-trailer/' }
    @{ Broken = '/services/wedding-video/';               Target = '/services/personalization/ai-video-generator/' }
    @{ Broken = '/services/family-tribute/';              Target = '/services/absence-compensation/family-tribute/' }
    @{ Broken = '/about-us/';                             Target = '/about/' }
    @{ Broken = '/contact/';                              Target = '/order/' }
    @{ Broken = '/blog/wedding-budget-breakdown-2026/';  Target = '/blog/wedding-video-cost-2026/' }
    @{ Broken = '/blog/average-wedding-cost-2026/';      Target = '/blog/wedding-video-cost-2026/' }
    @{ Broken = '/blog/wedding-vendor-payment-schedule/';Target = '/blog/wedding-video-cost-2026/' }
    @{ Broken = '/blog/wedding-reception-timeline/';     Target = '/blog/wedding-video-timeline/' }
    @{ Broken = '/blog/wedding-seating-chart-ideas/';    Target = '/tools/wedding-seating-chart-maker/' }
    @{ Broken = '/blog/best-wedding-photo-books-2026/';  Target = '/tools/wedding-photo-book-planner/' }
    @{ Broken = '/blog/wedding-photo-album-ideas/';      Target = '/tools/wedding-photo-book-planner/' }
)

$cb = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$results = @()
$pass = 0
$fail = 0
$errCount = 0

foreach ($pair in $pairs) {
    foreach ($lang in $langs) {
        $broken_url = "$BASE$lang$($pair.Broken)"
        $probe_url  = "$broken_url`?t=$cb"
        $expected   = "$BASE$lang$($pair.Target)"
        $langTag    = if ($lang -eq '') { 'en' } else { $lang.TrimStart('/') }

        $status = $null
        $loc = $null
        $err = $null

        # curl.exe with timeout to avoid hangs on slow deploy edge.
        # On Windows, /dev/null doesn't exist -- use NUL for discard sink.
        # 2>&1 captures both stdout (headers + body) and stderr (curl errors)
        # into one array of lines; we join to a single string for regex match.
        $curlOut = & curl.exe -s -o NUL -D - --max-redirs 0 `
                               --connect-timeout 8 --max-time 15 `
                               -H 'Cache-Control: no-cache' `
                               -A 'weddingai-verify-script' `
                               $probe_url 2>&1
        $exitCode = $LASTEXITCODE
        $curlStr = $curlOut -join "`n"
        if ($exitCode -eq 0 -or $exitCode -eq 23) {
            # exit 23 = "Failed writing body" -- the body never reached -o NUL
            # because --max-redirs 0 stopped after the redirect response.
            # Headers were already captured before the body write failed,
            # so the curlStr string is still useful.
            if ($curlStr -match 'HTTP/[\d.]+\s+(\d+)') { $status = [int]$Matches[1] }
            if ($curlStr -match '(?im)^location:\s*(.+?)\s*$') {
                $loc = $Matches[1].Trim()
            }
        } else {
            $err = "curl exit $exitCode"
            $errCount++
        }

        # Normalize Location: CF Pages sends absolute (https://...). Strip scheme+host for compare.
        $loc_normalized = $null
        if ($loc) {
            if ($loc -match '^https?://[^/]+(/.*)$') {
                $loc_normalized = $Matches[1]
            } elseif ($loc.StartsWith('/')) {
                $loc_normalized = $loc
            } else {
                $loc_normalized = '/'
            }
            # Strip our cache-bust ?t= for compare (CF Pages propagates qs into Location)
            $loc_normalized = ($loc_normalized -replace '\?t=\d+$', '')
        }
        # Strip scheme+host from expected too (was previously still had https://weddingai.video prefix)
        $expected_normalized = ($expected -replace '^https?://[^/]+', '') -replace '\?t=\d+$', ''

        $ok = ($status -eq 301) -and ($loc_normalized -eq $expected_normalized)
        if ($ok) { $pass++ } else { $fail++ }

        $results += [pscustomobject]@{
            Lang     = $langTag
            Broken   = $pair.Broken
            Status   = $status
            Location = $loc_normalized
            Expected = $expected_normalized
            Pass     = $ok
            Error    = $err
        }
    }
}

# Output CSV (for future diffs; not Bulk CSV format per memory - this is human-readable report)
$out = "scripts/verify-redirects-toolfooters-results.csv"
$results | Export-Csv -NoTypeInformation -Path $out

"`nResults: $pass pass / $fail fail (curl-errors: $errCount, total $($results.Count))"
"CSV written to: $out"
""

# Print failures
if ($fail -gt 0 -or $errCount -gt 0) {
    "`nFAILURES / ERRORS:"
    $results | Where-Object { -not $_.Pass -or $_.Error } |
               Format-Table -AutoSize |
               Out-String | Write-Host
    if ($fail -eq 0 -and $errCount -gt 0) {
        # Pure transient errors (in-flight deploy) - retry once after 30s
        "`nTransient curl errors only (no permanent failures). Waiting 30s and retrying..."
        Start-Sleep -Seconds 30
        powershell -ExecutionPolicy Bypass -File $PSCommandPath
        exit $LASTEXITCODE
    }
    exit 1
} else {
    "ALL 132 PROBES PASS - tool-footer 4xx cleanup verified in production."
    exit 0
}
