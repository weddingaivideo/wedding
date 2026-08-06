# Helper to set Cloudflare Pages secrets from the command line.
# The secret value is prompted interactively (never passed as a command-line arg
# or written to a file). If you cancel the prompt, no value is stored.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/set-cloudflare-secrets.ps1
#
# Prerequisites:
#   npm install -g wrangler
#   wrangler login   (one-time)
#
# This script:
#   1. Prompts for RESEND_API_KEY (input is masked)
#   2. Calls `wrangler pages secret put RESEND_API_KEY --project-name=weddingai-video`
#   3. Optionally prompts for TO_EMAIL override
#
# IMPORTANT: Rotate the key first if it was ever shared in chat/email/commits.

$projectName = "weddingai-video"

function Set-CloudflareSecret {
    param([string]$SecretName, [string]$Prompt)

    Write-Host ""
    Write-Host "=== Setting $SecretName ===" -ForegroundColor Cyan
    Write-Host "Tip: paste your new key, then press Enter. The value is sent directly to Cloudflare; nothing is written to disk." -ForegroundColor DarkGray

    $secure = Read-Host -Prompt $Prompt -AsSecureString
    if (-not $secure -or $secure.Length -eq 0) {
        Write-Host "  Skipped (empty input)." -ForegroundColor Yellow
        return
    }
    $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    )

    try {
        $plain | wrangler pages secret put $SecretName --project-name=$projectName
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  $SecretName set successfully." -ForegroundColor Green
        } else {
            Write-Host "  wrangler exited with code $LASTEXITCODE" -ForegroundColor Red
        }
    } finally {
        # Wipe from memory
        $plain = $null
        [System.GC]::Collect()
    }
}

# Confirm wrangler is available
$wranglerCheck = Get-Command wrangler -ErrorAction SilentlyContinue
if (-not $wranglerCheck) {
    Write-Host "wrangler not found. Install with:  npm install -g wrangler" -ForegroundColor Red
    exit 1
}

# Confirm logged in
$whoami = wrangler whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not logged in. Run:  wrangler login" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Cloudflare Pages Secrets Setup" -ForegroundColor Cyan
Write-Host "Project: $projectName" -ForegroundColor DarkGray
Write-Host "Logged in as: $($whoami | Select-Object -First 1)" -ForegroundColor DarkGray

Set-CloudflareSecret -SecretName "RESEND_API_KEY" -Prompt "Paste your Resend API key (re_xxx)"

$setTo = Read-Host -Prompt "Set TO_EMAIL override? (press Enter to skip, defaults to order@weddingai.video)"
if ($setTo) {
    $setTo | wrangler pages secret put TO_EMAIL --project-name=$projectName
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  TO_EMAIL set to: $setTo" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Done. Trigger a redeploy to pick up the new secrets." -ForegroundColor Cyan
Write-Host "Verify with:  node scripts/test-form.js" -ForegroundColor DarkGray
