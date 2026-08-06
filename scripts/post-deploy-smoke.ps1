# WeddingAI.video — Post-Deploy Smoke Test
# Runs AFTER `wrangler pages deploy` to catch the class of bug where
# Cloudflare Pages Functions middleware reconstructs a Response without
# preserving the original Content-Type (defaults to text/plain → browser
# dumps raw HTML source to screen). Symptom that prompted this script:
# 2026-08-04 03:00 EST — `withCspHeaders` was simplified to drop header
# copying, Content-Type was lost, the live site rendered as raw source
# for ~2 hours before anyone noticed.
#
# What this checks:
# 1. /          — no-prefix branch (context.next() in middleware)
# 2. /zh/       — with-prefix branch (fetch() in middleware)
# 3. /order/    — sub-page, exercises the same code path with a real
#                 form page (where the bug is most visible to users)
#
# Each check asserts:
#   - HTTP 200
#   - Content-Type starts with "text/html"
#   - body contains <title> (sanity: body actually arrived, not an error)
#
# Exits 1 on any failure. Exits 0 if all three pass.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/post-deploy-smoke.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/post-deploy-smoke.ps1 -BaseUrl https://staging.example.com

param(
    [string]$BaseUrl = "https://weddingai.video",
    [int]$MaxAttempts = 3,
    [int]$RetryDelaySeconds = 5
)

$ErrorActionPreference = "Stop"
$script:errors = 0
$script:warns = 0

function Pass($msg) { Write-Host "  [PASS] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow; $script:warns++ }
function Fail($msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red; $script:errors++ }

function Test-Page([string]$label, [string]$path, [string]$bodyMustContain) {
    Write-Host ""
    Write-Host "  $label  ($path)" -ForegroundColor Cyan

    $url = "${BaseUrl}${path}?cb=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())"
    $lastErr = $null

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
            $req = [System.Net.HttpWebRequest]::Create($url)
            $req.Method = "GET"
            $req.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (WeddingAI-SmokeTest)"
            $req.AllowAutoRedirect = $true
            $req.Timeout = 15000
            $req.CachePolicy = New-Object System.Net.Cache.RequestCachePolicy([System.Net.Cache.RequestCacheLevel]::NoCacheNoStore)

            $resp = $req.GetResponse()
            $status = [int]$resp.StatusCode
            $ct = $resp.Headers["Content-Type"]
            $stream = $resp.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
            $body = $reader.ReadToEnd()
            $resp.Close()

            if ($status -ne 200) {
                Fail "HTTP $status (expected 200)"
                return
            }
            Pass "HTTP 200"

            if ([string]::IsNullOrWhiteSpace($ct)) {
                Fail "Content-Type header missing entirely"
                return
            }
            if ($ct -notmatch '^text/html') {
                Fail "Content-Type is '$ct' (expected text/html...)"
                Write-Host "         The browser will render this as plain text, dumping HTML source to screen." -ForegroundColor DarkRed
                Write-Host "         Likely cause: middleware reconstructs Response without preserving Content-Type." -ForegroundColor DarkRed
                Write-Host "         Fix: add 'Content-Type: text/html; charset=utf-8' to the new Response init." -ForegroundColor DarkRed
                return
            }
            Pass "Content-Type: $ct"

            if ($body -notmatch [regex]::Escape($bodyMustContain)) {
                Fail "Body missing expected marker '$bodyMustContain' (body length: $($body.Length) bytes)"
                Write-Host "         First 200 chars of body: $($body.Substring(0, [Math]::Min(200, $body.Length)))" -ForegroundColor DarkGray
                return
            }
            Pass "Body contains '$bodyMustContain' ($($body.Length) bytes)"

            return
        } catch [System.Net.WebException] {
            $ex = $_.Exception
            $code = $null
            try { $code = [int]$ex.Response.StatusCode } catch { $code = "n/a" }
            $lastErr = "HTTP $code — $($ex.Message)"
            if ($attempt -lt $MaxAttempts) {
                Write-Host "  [RETRY $attempt/$MaxAttempts] $lastErr — waiting ${RetryDelaySeconds}s" -ForegroundColor DarkYellow
                Start-Sleep -Seconds $RetryDelaySeconds
            }
        } catch {
            $lastErr = $_.Exception.Message
            if ($attempt -lt $MaxAttempts) {
                Write-Host "  [RETRY $attempt/$MaxAttempts] $lastErr — waiting ${RetryDelaySeconds}s" -ForegroundColor DarkYellow
                Start-Sleep -Seconds $RetryDelaySeconds
            }
        }
    }
    Fail "All $MaxAttempts attempts failed. Last error: $lastErr"
}

Write-Host ""
Write-Host "=== WeddingAI.video Post-Deploy Smoke Test ===" -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl"
Write-Host "Max attempts per check: $MaxAttempts (${RetryDelaySeconds}s delay between retries)"

# 1. Home page — exercises no-prefix branch (context.next() in middleware).
#    Marker is "<title" (no closing >) so it matches both bare <title> and
#    <title data-i18n="..."> forms — the i18n transform rewrites opening
#    tags with data-i18n attrs.
Test-Page "[1/3] Home page" "/" "<title"

# 2. /zh/ — exercises with-prefix branch (fetch() + i18n in middleware)
Test-Page "[2/3] Chinese home (server-side i18n path)" "/zh/" 'lang="zh"'

# 3. /order/ — sub-page form (most visible to users; was the first
#    user-reported broken state in the 2026-08-04 incident)
Test-Page "[3/3] Order form (sub-page)" "/order/" "<title"

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "  Errors:   $($script:errors)"
Write-Host "  Warnings: $($script:warns)"
Write-Host ""

if ($script:errors -gt 0) {
    Write-Host "POST-DEPLOY SMOKE TEST FAILED" -ForegroundColor Red
    Write-Host "The site is LIVE but broken. Consider rolling back the deploy." -ForegroundColor Red
    exit 1
}

Write-Host "POST-DEPLOY SMOKE TEST PASSED" -ForegroundColor Green
exit 0
