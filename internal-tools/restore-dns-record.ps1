<#
.SYNOPSIS
    Restore the weddingai.video custom-domain DNS records in Cloudflare and re-activate
    the matching Cloudflare Pages custom domains, then verify end to end.

.DESCRIPTION
    Background (2026-10-28): the apex A/CNAME record was deleted from the Cloudflare
    zone. Two things then broke, and BOTH have to be undone:

      1. DNS      - the apex had no address record at all (NOERROR/NODATA) and
                    www was NXDOMAIN, so the site was unreachable for visitors.
      2. Pages    - Cloudflare Pages automatically DEACTIVATES a custom domain whose
                    DNS record disappears. A deactivated Pages custom domain answers
                    with HTTP 403 even when the DNS record is put back, until Pages
                    re-verifies it.

    This script therefore does, in order:
      1. zone lookup
      2. read the Pages project to learn its REAL pages.dev subdomain
         (the project name is not always the subdomain - this project is
          "weddingai-video" but its subdomain is "weddingai-video-bin.pages.dev")
      3. create/repair the apex CNAME and (optionally) the www CNAME, proxied
      4. re-activate the Pages custom domains so Pages re-verifies them
      5. verify via DoH + a DoH-resolved HTTPS request, with retries because
         Pages re-verification is not instantaneous

    Usage:
      .\internal-tools\restore-dns-record.ps1 -TokenFile C:\...\cloudflare.token
      $env:CLOUDFLARE_API_TOKEN = "..."; .\internal-tools\restore-dns-record.ps1 -AlsoWWW
      .\internal-tools\restore-dns-record.ps1 -TokenFile ... -WhatIf

    Token permissions required (scoped to this one zone + this Pages project):
      Zone -> DNS -> Edit, Zone -> Read
      Pages -> Edit  (account level, for the custom-domain re-activation)
#>
[CmdletBinding()]
param(
    [string]$TokenFile = "",
    [string]$Domain = "weddingai.video",
    [string]$Project = "weddingai-video",
    [switch]$AlsoWWW,
    [switch]$WhatIf,
    [int]$WaitSeconds = 300
)

$ErrorActionPreference = 'Stop'

function Get-Token {
    $raw = $null
    if ($env:CLOUDFLARE_API_TOKEN) {
        $raw = $env:CLOUDFLARE_API_TOKEN
    } elseif ($TokenFile) {
        if (-not (Test-Path $TokenFile)) { throw "Token file not found: $TokenFile" }
        $raw = Get-Content $TokenFile -Raw
    } else {
        throw "No token. Pass -TokenFile <path> or set $env:CLOUDFLARE_API_TOKEN."
    }
    $raw = $raw.Trim()
    # Accept a bare token, a "Bearer <token>" line, or "<label>: <token>".
    if ($raw -match '(?i)\bbearer\s+([A-Za-z0-9_\-\.=]{20,})') {
        $raw = $Matches[1]
    } elseif ($raw -match '(?im)^[^\r\n:=]{0,40}[:=]\s*([A-Za-z0-9_\-\.=]{20,})') {
        $raw = $Matches[1]
    }
    if ($raw.Length -lt 20) { throw "Token could not be parsed (length $($raw.Length))." }
    return $raw.Trim()
}

function Invoke-CfApi {
    param([string]$Method, [string]$Path, [object]$Body, [string]$Token)
    $params = @{
        Uri        = "https://api.cloudflare.com/client/v4$Path"
        Method     = $Method
        Headers    = @{ Authorization = "Bearer $Token" }
        TimeoutSec = 60
    }
    if ($null -ne $Body) {
        $params.ContentType = "application/json"
        $params.Body = ($Body | ConvertTo-Json -Depth 6)
    }
    $resp = Invoke-RestMethod @params
    if (-not $resp.success) {
        $errs = ($resp.errors | ForEach-Object { "$($_.code): $($_.message)" }) -join "; "
        throw "Cloudflare API $Method $Path failed: $errs"
    }
    return $resp.result
}

function Get-DohJson {
    param([string]$Uri)
    $resp = Invoke-WebRequest -Uri $Uri -Headers @{ accept = "application/dns-json" } -UseBasicParsing -TimeoutSec 25
    if ($resp.Content -is [byte[]]) {
        $text = [System.Text.Encoding]::UTF8.GetString($resp.Content)
    } else {
        $text = [string]$resp.Content
    }
    return ($text | ConvertFrom-Json)
}

$token = Get-Token

Write-Host "=== 1. zone + account lookup ===" -ForegroundColor Cyan
$zones = Invoke-CfApi -Method GET -Path "/zones?name=$Domain" -Token $token
if (-not $zones -or $zones.Count -eq 0) { throw "Zone '$Domain' not visible with this token." }
$zone = $zones[0]
$zoneId = $zone.id
Write-Host "  zone  : $($zone.name)  id=$zoneId  status=$($zone.status) paused=$($zone.paused)"

$accounts = Invoke-CfApi -Method GET -Path "/accounts" -Token $token
if (-not $accounts -or $accounts.Count -eq 0) { throw "No account visible with this token." }
$accountId = $accounts[0].id
Write-Host "  account: $($accounts[0].name)  id=$accountId"

Write-Host "=== 2. Pages project (real pages.dev subdomain) ===" -ForegroundColor Cyan
$proj = Invoke-CfApi -Method GET -Path "/accounts/$accountId/pages/projects/$Project" -Token $token
$target = $proj.subdomain
Write-Host "  project name : $($proj.name)"
Write-Host "  subdomain    : $target   <- CNAME target (NOT always equal to the project name)"

Write-Host "=== 3. current DNS records ===" -ForegroundColor Cyan
$records = Invoke-CfApi -Method GET -Path "/zones/$zoneId/dns_records?per_page=100" -Token $token
$records | ForEach-Object {
    Write-Host ("  {0,-6} {1,-28} -> {2}  proxied={3}" -f $_.type, $_.name, $_.content, $_.proxied)
}

function Ensure-Cname {
    param([string]$Name, [string]$TargetHost, [string]$ZoneId, [string]$Token, [bool]$DryRun)
    $existing = @($records | Where-Object { $_.name -eq $Name -and $_.type -in @('A', 'AAAA', 'CNAME') })
    if ($existing.Count -gt 0) {
        $rec = $existing[0]
        if ($rec.type -eq 'CNAME' -and $rec.content -eq $TargetHost -and $rec.proxied) {
            Write-Host "  $Name -> $TargetHost (proxied) already correct."
            return $rec.id
        }
        if ($DryRun) {
            Write-Host "  [WhatIf] would UPDATE ${Name}: $($rec.type)/$($rec.content)/proxied=$($rec.proxied) -> CNAME/$TargetHost/proxied=True"
            return $rec.id
        }
        $body = @{ type = "CNAME"; name = $Name; content = $TargetHost; proxied = $true; ttl = 1 }
        $upd = Invoke-CfApi -Method PUT -Path "/zones/$ZoneId/dns_records/$($rec.id)" -Body $body -Token $Token
        Write-Host "  UPDATED $Name : $($rec.type)/$($rec.content) -> CNAME/$TargetHost (proxied)" -ForegroundColor Green
        return $upd.id
    }
    if ($DryRun) {
        Write-Host "  [WhatIf] would CREATE CNAME $Name -> $TargetHost (proxied)"
        return $null
    }
    $body = @{ type = "CNAME"; name = $Name; content = $TargetHost; proxied = $true; ttl = 1 }
    $new = Invoke-CfApi -Method POST -Path "/zones/$ZoneId/dns_records" -Body $body -Token $Token
    Write-Host "  CREATED CNAME $Name -> $TargetHost (proxied)" -ForegroundColor Green
    return $new.id
}

Write-Host "=== 4. ensure DNS records ===" -ForegroundColor Cyan
$null = Ensure-Cname -Name $Domain -TargetHost $target -ZoneId $zoneId -Token $token -DryRun:$WhatIf
if ($AlsoWWW) {
    $null = Ensure-Cname -Name "www.$Domain" -TargetHost $target -ZoneId $zoneId -Token $token -DryRun:$WhatIf
}

Write-Host "=== 5. re-activate the Pages custom domains ===" -ForegroundColor Cyan
$domains = Invoke-CfApi -Method GET -Path "/accounts/$accountId/pages/projects/$Project/domains" -Token $token
$names = @($Domain)
if ($AlsoWWW) { $names += "www.$Domain" }
foreach ($d in @($domains)) {
    Write-Host ("  {0,-22} status={1}" -f $d.name, $d.status)
}
foreach ($n in $names) {
    $d = @($domains | Where-Object { $_.name -eq $n })
    if ($d.Count -eq 0) {
        if ($WhatIf) { Write-Host "  [WhatIf] would ATTACH Pages custom domain $n"; continue }
        try {
            $null = Invoke-CfApi -Method POST -Path "/accounts/$accountId/pages/projects/$Project/domains" -Body @{ name = $n } -Token $token
            Write-Host "  ATTACHED Pages custom domain $n" -ForegroundColor Green
        } catch {
            Write-Host "  could not attach $n : $($_.Exception.Message)" -ForegroundColor Yellow
        }
        continue
    }
    if ($d[0].status -eq 'active') {
        Write-Host "  $n already active in Pages."
        continue
    }
    if ($WhatIf) { Write-Host "  [WhatIf] would re-activate Pages custom domain $n"; continue }
    try {
        # PATCH is the verb Cloudflare accepts for re-activating a deactivated
        # Pages custom domain (PUT answers 405). The status then goes
        # deactivated -> pending -> active once Pages re-verifies the DNS.
        $null = Invoke-CfApi -Method PATCH -Path "/accounts/$accountId/pages/projects/$Project/domains/$n" -Body @{ status = "active" } -Token $token
        Write-Host "  re-activation requested for $n (status -> pending)" -ForegroundColor Green
    } catch {
        Write-Host "  re-activation of $n failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

if ($WhatIf) {
    Write-Host "`n[WhatIf] no change made." -ForegroundColor Yellow
    exit 0
}

Write-Host "=== 6. verify (DoH + DoH-resolved HTTPS, with retries) ===" -ForegroundColor Cyan
$deadline = (Get-Date).AddSeconds($WaitSeconds)
$httpsOk = $false
$dnsOk = $false
while ((Get-Date) -lt $deadline) {
    $ips = @()
    foreach ($r in @(
            "https://dns.google/resolve?name=$Domain&type=A",
            "https://cloudflare-dns.com/dns-query?name=$Domain&type=A")) {
        try {
            $j = Get-DohJson $r
            $ips += @($j.Answer | Where-Object { $_.type -eq 1 } | ForEach-Object { $_.data })
        } catch {
            Write-Host "  (resolver query failed: $($_.Exception.Message -replace '\s+', ' '))" -ForegroundColor DarkGray
        }
    }
    if ($ips.Count -gt 0) {
        if (-not $dnsOk) { Write-Host ("  A record visible: " + (($ips | Select-Object -Unique) -join ", ")) -ForegroundColor Green; $dnsOk = $true }
        $probe = & curl.exe -s -o NUL -L -w "%{http_code}" --max-time 30 --doh-url "https://dns.google/dns-query" "https://$Domain/" 2>&1
        $exit = $LASTEXITCODE
        if ("$probe" -eq "200") {
            Write-Host "  https://$Domain/ -> HTTP 200" -ForegroundColor Green
            $httpsOk = $true
            break
        }
        Write-Host "  DNS resolves but HTTPS returned '$probe' (curl exit $exit) - Pages may still be re-verifying..." -ForegroundColor DarkGray
    } else {
        Write-Host "  DNS not resolved yet, retrying in 10s..." -ForegroundColor DarkGray
    }
    Start-Sleep -Seconds 10
}

if (-not $httpsOk) {
    Write-Host "`nDNS resolved but the Pages custom domain did not return 200 within $WaitSeconds s." -ForegroundColor Red
    Write-Host "Check the Pages custom-domain status (it must be 'active', not 'deactivated')." -ForegroundColor Yellow
    exit 1
}

Write-Host "`nRESTORED - $Domain resolves and serves the site (HTTP 200)." -ForegroundColor Green
exit 0
