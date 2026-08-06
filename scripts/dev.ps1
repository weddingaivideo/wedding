<#
.SYNOPSIS
  WeddingAI.video local dev — one command to start wrangler pages dev + open browser.

.DESCRIPTION
  Wraps `npx --yes wrangler@4.114 pages dev .` so you can preview changes
  locally with the EXACT same behavior as production:
    * functions/_middleware.js runs (CSP nonce injection, i18n URL rewrite,
      Accept-Language auto-redirect, canonical/hreflang rewrite)
    * functions/api/quote.js + dead-letters.js run (local KV via miniflare)
    * _redirects / _headers are honored
    * The only difference from prod is no edge cache + no real Resend send.

  Usage:
    powershell -ExecutionPolicy Bypass -File scripts\dev.ps1
  Then edit files, refresh browser. Ctrl+C to stop.

  Localhost URL: http://localhost:8788

  First-visit behavior (matches prod):
    * Browser's Accept-Language header determines auto-redirect target
    * Cookie 'wa_lang_auto' is set so we don't redirect again
    * Visit http://localhost:8788/en/ to skip auto-redirect

.PARAMETER Port
  Local port to bind. Default: 8788 (wrangler pages dev default).

.PARAMETER NoBrowser
  Start wrangler but don't auto-open browser. Useful for headless / CI.

.PARAMETER Clean
  Wipe .wrangler/state/ before starting. Use this if you changed
  wrangler.toml KV bindings or want to reset rate-limit counters.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\dev.ps1
  # Start dev server on :8788, open browser.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 -Port 9000
  # Use port 9000 instead.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 -NoBrowser
  # Headless: just run wrangler, no browser popup.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 -Clean
  # Wipe local KV state (rate-limit counters etc.) before starting.
#>
param(
    [int]$Port = 8788,
    [switch]$NoBrowser,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# --- 0. Sanity checks --------------------------------------------------------
if (-not (Get-Command npx.cmd -ErrorAction SilentlyContinue)) {
    Write-Host "npx not found. Install Node.js first (https://nodejs.org)." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path wrangler.toml)) {
    Write-Host "wrangler.toml not found in $root. Run from the project root." -ForegroundColor Red
    exit 1
}

# --- 1. Kill anything already on $Port ---------------------------------------
$existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "[1/4] Port $Port busy — killing existing listener ..." -ForegroundColor Yellow
    foreach ($c in $existing) {
        $pid_kill = $c.OwningProcess
        try {
            & taskkill.exe /T /F /PID $pid_kill 2>$null | Out-Null
            Write-Host "    killed PID $pid_kill (tree)" -ForegroundColor DarkGray
        } catch {
            Write-Warning "    could not kill PID ${pid_kill}: $_"
        }
    }
    Start-Sleep -Seconds 1
}

# --- 2. Optionally wipe local miniflare state -------------------------------
if ($Clean) {
    $stateDir = Join-Path $root ".wrangler/state"
    if (Test-Path $stateDir) {
        Write-Host "[2/4] Wiping $stateDir (Clean mode) ..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $stateDir
    } else {
        Write-Host "[2/4] Clean mode requested but $stateDir doesn't exist (skipping)." -ForegroundColor DarkGray
    }
}

# --- 3. Start wrangler in background ----------------------------------------
$logOut = Join-Path $root "qa/.dev-stdout.log"
$logErr = Join-Path $root "qa/.dev-stderr.log"
"" | Set-Content $logOut
"" | Set-Content $logErr

Write-Host ""
Write-Host "=== WeddingAI.video local dev ===" -ForegroundColor Cyan
Write-Host "  Project:  $root" -ForegroundColor DarkGray
Write-Host "  Command:  npx --yes wrangler@4.114 pages dev . --port=$Port" -ForegroundColor DarkGray
Write-Host "  Logs:     $logOut" -ForegroundColor DarkGray
Write-Host ""

$proc = Start-Process `
    -FilePath "npx.cmd" `
    -ArgumentList "--yes","wrangler@4.114","pages","dev",".","--port=$Port" `
    -WorkingDirectory $root `
    -RedirectStandardOutput $logOut `
    -RedirectStandardError $logErr `
    -NoNewWindow `
    -PassThru

# --- 4. Wait for port to be ready -------------------------------------------
$timeoutSec = 45
$deadline = (Get-Date).AddSeconds($timeoutSec)
$ready = $false
Write-Host "[3/4] Waiting for wrangler to open port $Port (timeout ${timeoutSec}s) ..." -ForegroundColor Yellow
while ((Get-Date) -lt $deadline) {
    if ($proc.HasExited) {
        Write-Host ""
        Write-Host "wrangler exited unexpectedly. Last stderr lines:" -ForegroundColor Red
        if (Test-Path $logErr) { Get-Content $logErr -Tail 30 | ForEach-Object { Write-Host "  $_" } }
        exit 1
    }
    $c = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($c) { $ready = $true; break }
    Start-Sleep -Milliseconds 500
}
if (-not $ready) {
    Write-Host ""
    Write-Host "wrangler didn't open port $Port within ${timeoutSec}s." -ForegroundColor Red
    if (Test-Path $logErr) { Get-Content $logErr -Tail 30 | ForEach-Object { Write-Host "  $_" } }
    & taskkill.exe /T /F /PID $proc.Id 2>$null | Out-Null
    exit 1
}

# --- 5. Open browser ---------------------------------------------------------
$url = "http://localhost:${Port}/"
Write-Host "[4/4] Ready. Open: $url" -ForegroundColor Green
Write-Host "      (First visit may 302 to /zh/ etc. based on your browser language.)" -ForegroundColor DarkGray
Write-Host "      (Use http://localhost:${Port}/en/  to skip auto-redirect.)" -ForegroundColor DarkGray
Write-Host ""
if (-not $NoBrowser) {
    Start-Process $url | Out-Null
}

# --- 6. Tail the log until Ctrl+C -------------------------------------------
Write-Host "=== wrangler dev is running (PID $($proc.Id)). Ctrl+C to stop. ===" -ForegroundColor Cyan
Write-Host ""

try {
    # Stream the wrangler log. Use -Wait to follow new lines until interrupted.
    # We use a small poll to also detect the process exiting unexpectedly.
    $logStream = [System.IO.File]::Open($logOut, "Open", "Read", "ReadWrite", "FileShare.ReadWrite | FileShare.Delete")
    $reader = New-Object System.IO.StreamReader($logStream)
    try {
        while (-not $proc.HasExited) {
            $line = $reader.ReadLine()
            if ($null -ne $line) { Write-Host $line }
            else { Start-Sleep -Milliseconds 200 }
        }
    } finally {
        $reader.Close()
        $logStream.Close()
    }
    if ($proc.HasExited) {
        Write-Host ""
        Write-Host "wrangler exited (code $($proc.ExitCode)). Last stderr:" -ForegroundColor Yellow
        if (Test-Path $logErr) { Get-Content $logErr -Tail 20 | ForEach-Object { Write-Host "  $_" } }
    }
}
finally {
    Write-Host ""
    Write-Host "=== Stopping wrangler (PID $($proc.Id), tree) ... ===" -ForegroundColor Yellow
    & taskkill.exe /T /F /PID $proc.Id 2>$null | Out-Null
    Start-Sleep -Milliseconds 500
    if (-not $proc.HasExited) {
        try { Stop-Process -Id $proc.Id -Force -ErrorAction Stop } catch {}
    }
    Write-Host "Done." -ForegroundColor Green
}
