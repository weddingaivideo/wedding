<#
    Local test server watchdog for the UX harness.

    `wrangler pages dev` (workerd) occasionally dies under the sustained load of a
    few hundred automated page loads ("fatal error:" with an empty ERROR banner,
    no stack). This wrapper restarts it automatically so a server crash never
    gets mis-reported as a site defect.

    Usage:
        powershell -ExecutionPolicy Bypass -File qa\ux\serve-watch.ps1 -Port 8788
#>
param(
    [int]$Port = 8788,
    [string]$Wrangler = "npx.cmd",
    [string]$WranglerArgs = "--yes wrangler@4.151.2"
)

$ErrorActionPreference = "Continue"
# qa\ux -> qa -> <site root>
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

# The runtime needs a plain HTTP proxy (undici rejects socks5h); localhost must
# bypass it or miniflare proxies its own requests into a loop.
$env:HTTP_PROXY = "http://127.0.0.1:7897"
$env:HTTPS_PROXY = "http://127.0.0.1:7897"
$env:NO_PROXY = "127.0.0.1,localhost,::1"

$out = Join-Path $root "qa/ux/results/dev-stdout.log"
$err = Join-Path $root "qa/ux/results/dev-stderr.log"
New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null

$restarts = 0
while ($true) {
    $p = $null
    if ($Wrangler -eq "npx.cmd") {
        # .cmd shims must be launched through cmd.exe when output is redirected
        $cmdLine = "npx --yes wrangler@4.151.2 pages dev . --port $Port --ip 127.0.0.1"
        $p = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $cmdLine -WorkingDirectory $root `
            -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden -PassThru
    } else {
        $argList = @("pages", "dev", ".", "--port", "$Port", "--ip", "127.0.0.1")
        $p = Start-Process -FilePath $Wrangler -ArgumentList $argList -WorkingDirectory $root `
            -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden -PassThru
    }

    # wait for the port, then wait for the process to die
    $deadline = (Get-Date).AddSeconds(90)
    $ready = $false
    while ((Get-Date) -lt $deadline) {
        if ($p.HasExited) { break }
        if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) { $ready = $true; break }
        Start-Sleep -Milliseconds 800
    }
    Write-Host "[watch] wrangler started pid=$($p.Id) ready=$ready restarts=$restarts"

    while (-not $p.HasExited) { Start-Sleep -Seconds 3 }
    $restarts++
    Write-Host "[watch] wrangler exited (code $($p.ExitCode)) - restarting (#$restarts) ..."
    Start-Sleep -Seconds 2
}
