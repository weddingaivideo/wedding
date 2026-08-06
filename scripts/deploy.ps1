# WeddingAI.video — one-shot deploy to Cloudflare Pages.
# Wraps: pre-deploy check + wrangler pages deploy.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1 -ProjectName my-project
#
# Prerequisites (one-time):
#   npm install -g wrangler
#   wrangler login

param(
    [string]$ProjectName = "weddingai-video",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Set-Location $root

Write-Host "=== WeddingAI.video Deploy ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectName"
Write-Host "Branch:  $Branch"
Write-Host ""
Write-Host "Steps:  [0/5] sitemap regen → [1/5] pre-check → [2/5] wrangler → [3/5] deploy → [4/5] smoke → [5/5] indexnow" -ForegroundColor DarkGray
Write-Host ""

# ---------- 0. Regenerate sitemap (lastmod=today, 71 pages × 10 langs = 710 URLs) ----------
Write-Host "[0/4] Regenerating sitemap.xml with lastmod=today..." -ForegroundColor Yellow
& python "$root\qa\gen_sitemap.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "" -ForegroundColor Red
    Write-Host "Sitemap regeneration FAILED. Aborting deploy." -ForegroundColor Red
    exit 1
}

# ---------- 1. Pre-deploy check ----------
Write-Host "[1/4] Running pre-deploy check..." -ForegroundColor Yellow
& powershell -ExecutionPolicy Bypass -File "$root\internal-tools\pre-deploy-check.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Pre-deploy check FAILED. Fix the errors above before deploying." -ForegroundColor Red
    exit 1
}

# ---------- 2. Wrangler sanity ----------
Write-Host ""
Write-Host "[2/4] Checking wrangler..." -ForegroundColor Yellow
$wrangler = Get-Command wrangler -ErrorAction SilentlyContinue
if (-not $wrangler) {
    Write-Host "  wrangler not found. Install with:  npm install -g wrangler" -ForegroundColor Red
    exit 1
}
$whoami = wrangler whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Not logged in. Run:  wrangler login" -ForegroundColor Red
    exit 1
}
Write-Host "  Logged in as: $($whoami[0])" -ForegroundColor Green

# ---------- 3. Deploy ----------
Write-Host ""
Write-Host "[3/4] Deploying to Cloudflare Pages..." -ForegroundColor Yellow
Write-Host "  This uploads the project folder (incl. functions/) to Cloudflare." -ForegroundColor DarkGray
Write-Host ""

wrangler pages deploy . --project-name=$ProjectName --branch=$Branch

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== Deploy complete ===" -ForegroundColor Green
    Write-Host "Visit: https://$ProjectName.pages.dev  to verify." -ForegroundColor Cyan
    Write-Host "If the live domain (weddingai.video) doesn't work yet, configure it under Pages project → Custom domains." -ForegroundColor DarkGray

    # ---------- 4. Post-deploy smoke test (catches broken Content-Type) ----------
    # Live curl on /, /zh/, /order/ to confirm the middleware is serving
    # text/html (not text/plain). This catches the class of bug where
    # functions/_middleware.js reconstructs a Response without preserving
    # Content-Type, which makes the browser dump raw HTML source to screen.
    # (Added 2026-08-04 after the withCspHeaders incident.)
    Write-Host ""
    Write-Host "[4/5] Running post-deploy smoke test (Content-Type sanity)..." -ForegroundColor Yellow
    & powershell -ExecutionPolicy Bypass -File "$root\scripts\post-deploy-smoke.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "=== Post-deploy smoke test FAILED ===" -ForegroundColor Red
        Write-Host "The site is LIVE but the smoke check failed (Content-Type or body mismatch)." -ForegroundColor Red
        Write-Host "Possible cause: middleware bug. Inspect functions/_middleware.js for header mutations." -ForegroundColor Red
        Write-Host "If this is a transient edge-cache issue, wait 30s and re-run scripts/post-deploy-smoke.ps1." -ForegroundColor DarkYellow
        exit 1
    }

    # ---------- 5. Notify IndexNow (Bing / Yandex / Seznam / Naver) ----------
    Write-Host ""
    Write-Host "[5/5] Notifying IndexNow of updated sitemap..." -ForegroundColor Yellow
    & powershell -ExecutionPolicy Bypass -File "$root\scripts\submit-indexnow.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  IndexNow notification failed (non-fatal). The site is still live." -ForegroundColor DarkYellow
    }
} else {
    Write-Host ""
    Write-Host "=== Deploy FAILED ===" -ForegroundColor Red
    exit 1
}
