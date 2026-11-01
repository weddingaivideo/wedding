<#
.SYNOPSIS
    Rebuilds the i18n shards and proves they match the dictionaries.

.DESCRIPTION
    The shards under i18n/shards/<lang>/ are a DERIVED artefact: they are
    built from i18n/<lang>.json by qa/build-i18n-shards.py. Editing a
    dictionary without rebuilding the shards makes the middleware serve the
    OLD translations - silently, because the page still returns 200.

    This runs the builder and then the verifier, and exits non-zero if
    anything is still out of sync. Run it as the LAST step before committing
    a dictionary change, and commit the result:

        git add i18n/shards i18n/<lang>.manifest.json
        git commit

    The shards and the manifests are not tracked by git yet, so a plain
    `git add .` will not pick them up.

.PARAMETER SkipVerify
    Build only, do not verify.

.EXAMPLE
    powershell -File internal-tools/refresh-i18n-shards.ps1
#>
[CmdletBinding()]
param(
    [switch]$SkipVerify
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$py = $null
foreach ($candidate in @("python", "python3", "py")) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) { $py = $candidate; break }
}
if (-not $py) {
    Write-Host "[FAIL] Python not found in PATH - cannot rebuild the shards." -ForegroundColor Red
    exit 1
}

Write-Host "=== Rebuilding the i18n shards ===" -ForegroundColor Cyan
& $py "qa/build-i18n-shards.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] The shard build failed." -ForegroundColor Red
    exit 1
}

if ($SkipVerify) {
    Write-Host "[WARN] Verification skipped. Run this script again without -SkipVerify before committing." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "=== Verifying the shards against the dictionaries ===" -ForegroundColor Cyan
& $py "scripts/verify-i18n-shards.py"
$verifyExit = $LASTEXITCODE

if ($verifyExit -ne 0) {
    Write-Host ""
    Write-Host "[FAIL] The shards do not match the dictionaries." -ForegroundColor Red
    Write-Host "       A dictionary was probably edited while this script was running." -ForegroundColor Yellow
    Write-Host "       Wait for every other session that touches i18n/<lang>.json to finish, then run this again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[PASS] The shards match the dictionaries." -ForegroundColor Green
Write-Host "       Now commit them:" -ForegroundColor DarkGray
Write-Host "         git add i18n/shards i18n/*.manifest.json" -ForegroundColor DarkGray
exit 0
