<#
.SYNOPSIS
    Re-send lead notifications that Resend silently dropped (suppressed / bounced).

.DESCRIPTION
    Background (2026-10-29): the weddingai.video zone lost its MX records on 2026-10-12
    during a DNS cleanup. Resend accepted the sends (HTTP 200 -> the site logged
    email_status=delivered) but never actually delivered them, and after the first
    hard bounce it added order@weddingai.video to its suppression list, so every
    later lead was dropped without a trace. The site's KV still holds every lead,
    so nothing was lost - it just has to be re-sent once the mailbox works.

    This script reads the leads back out of the site's KV (through the existing
    /api/dead-letters endpoint) and re-sends them through Resend, mirroring the
    body format of functions/api/quote.js so the operator sees the same shape of
    notification as a live submission would produce.

    Test leads (example.com recipients, reference ids starting with TEST-) are
    skipped by default.

.EXAMPLE
    .\internal-tools\resend-backlog-leads.ps1 -DryRun
    .\internal-tools\resend-backlog-leads.ps1
    .\internal-tools\resend-backlog-leads.ps1 -LeadKey 'lead:1793037888314:WA-20261026-4EII'
#>
[CmdletBinding()]
param(
    [string]$TokenFile = ".cf-tokens.txt",
    [string]$Site = "https://weddingai.video",
    [string[]]$LeadKey = @(),
    [switch]$IncludeTestLeads,
    [switch]$DryRun,
    [int]$PollSeconds = 45,
    [int]$KvDelaySeconds = 2,
    # Seconds to wait between two sends. The enterprise mail server blocks a
    # sender that delivers a burst of mail to the same recipient
    # ("550 Mailbox unavailable or access denied", 企业微信帮助中心 doc 20057),
    # so the backlog goes in one message at a time.
    [int]$SendDelaySeconds = 90,
    [string]$To = "order@weddingai.video",
    [string]$From = "WeddingAI Quote <noreply@weddingai.video>"
)

$ErrorActionPreference = 'Stop'

function Get-Tokens {
    if (-not (Test-Path $TokenFile)) { throw "Token file not found: $TokenFile" }
    $kv = @{}
    Get-Content -LiteralPath $TokenFile -Encoding UTF8 | ForEach-Object {
        if ($_ -match '^\s*([A-Z0-9_]+)\s*=\s*(\S+)\s*$') { $kv[$Matches[1]] = $Matches[2] }
    }
    if (-not $kv['RESEND_API_KEY']) { throw "RESEND_API_KEY not found in $TokenFile" }
    if (-not $kv['DLQ_TOKEN']) { throw "DLQ_TOKEN not found in $TokenFile" }
    return $kv
}

$SERVICE_LABELS = @{
    "slow-motion" = "AI Slow Motion Enhancement"; "vintage-restoration" = "Vintage Footage Restoration"
    "family-tribute" = "Family Tribute"; "family-message" = "Family Message"
    "ai-video-generator" = "AI Wedding Video Generator"; "wedding-trailer" = "Cinematic Wedding Trailer"
    "pet-wedding" = "Pet Wedding Video"; "multilingual" = "Multilingual Dubbing & Subtitles"
    "cartoon-style" = "Cartoon / Animated Style"; "meme-generator" = "Wedding GIFs & Memes"
    "other" = "Other / Not Sure"
}
$COUNTRY_LABELS = @{
    US = "United States"; UK = "United Kingdom"; CA = "Canada"; AU = "Australia"
    DE = "Germany"; FR = "France"; ES = "Spain"; IT = "Italy"; IN = "India"
    CN = "China"; JP = "Japan"; other = "Other"
}
$BUDGET_LABELS = @{
    "under-100" = "Under `$100"; "100-300" = "`$100 - `$300"; "300-600" = "`$300 - `$600"
    "600-plus" = "`$600+"; "not-sure" = "Not sure yet"
}

function Get-Label($map, $key) {
    if (-not $key) { return "-" }
    if ($map.ContainsKey($key)) { return $map[$key] }
    return $key
}

function Invoke-Admin {
    param([string]$Uri, [int]$DelaySeconds = 2)
    # /api/dead-letters allows only 10 reads per 5 minutes per IP (functions/api/dead-letters.js),
    # so a 429 is expected on a long list. Back off and retry instead of failing.
    for ($attempt = 1; $attempt -le 6; $attempt++) {
        try {
            return Invoke-RestMethod -Uri $Uri -TimeoutSec 60
        } catch {
            $status = $null
            try { $status = [int]$_.Exception.Response.StatusCode } catch { }
            if ($status -eq 429) {
                Write-Host ("   (rate limited, waiting {0}s before retry {1})" -f (60 * $attempt), $attempt) -ForegroundColor DarkGray
                Start-Sleep -Seconds (60 * $attempt)
                continue
            }
            throw
        }
    }
    throw "Admin endpoint still rate limited after 6 attempts: $Uri"
}

function Get-Leads {
    param($dlqToken, [int]$DelaySeconds = 2)
    $url = "$Site/api/dead-letters?token=$dlqToken"
    $raw = Invoke-Admin -Uri $url
    $out = @()
    foreach ($item in $raw.items) {
        # The reference id is embedded in the key (lead:<ts>:<ref>), so test leads
        # can be dropped BEFORE their body is fetched - that keeps the number of
        # admin reads under the 10-per-5-minutes limit.
        $ref = ($item.key -split ':', 3)[2]
        if (-not $IncludeTestLeads) {
            if (-not $ref -or $ref -eq 'no-ref' -or $ref -like 'TEST-*') { continue }
        }
        $lead = Invoke-Admin -Uri "$url&key=$([uri]::EscapeDataString($item.key))"
        Start-Sleep -Seconds $DelaySeconds
        $out += [pscustomobject]@{ Key = $item.key; Lead = $lead }
    }
    return $out
}

function Test-IsTestLead {
    param($entry)
    $email = [string]$entry.Lead.form.email
    $ref = [string]$entry.Lead.reference_id
    if ($email -match '@example\.com$') { return $true }
    if ($ref -like 'TEST-*') { return $true }
    if (-not $ref) { return $true }
    return $false
}

function Build-Text {
    param($lead)
    $f = $lead.form
    $lines = @(
        "New Quote Request - WeddingAI.video",
        "====================================",
        "Reference:   " + $(if ($lead.reference_id) { $lead.reference_id } else { "-" }),
        "",
        "Name:        " + $(if ($f.name) { $f.name } else { "-" }),
        "Email:       " + $(if ($f.email) { $f.email } else { "-" }),
        "Country:     " + (Get-Label $COUNTRY_LABELS $f.country),
        "Wedding:     " + $(if ($f.wedding_date) { $f.wedding_date } else { "Not provided" }),
        "Service:     " + (Get-Label $SERVICE_LABELS $f.service),
        "Duration:    " + $(if ($f.video_duration) { $f.video_duration } else { "Not provided" }),
        "Budget:      " + (Get-Label $BUDGET_LABELS $f.budget),
        "Referral:    " + $(if ($f.referral) { $f.referral } else { "Not provided" }),
        "",
        "Project Details:",
        "----------------",
        $(if ($f.details) { $f.details } else { "(empty)" }),
        "",
        "Originally submitted: " + $lead.received_at
    )
    if ($f.upload_link) { $lines = $lines[0..9] + @("Upload:      " + $f.upload_link) + $lines[10..($lines.Count - 1)] }
    return ($lines -join "`n")
}

function Wait-DeliveryEvent {
    param([string]$EmailId, [int]$TimeoutSeconds = 45)
    $event = "unknown"
    for ($i = 0; $i -lt [Math]::Max(1, [int]($TimeoutSeconds / 10)); $i++) {
        Start-Sleep -Seconds 10
        try {
            $e = Invoke-RestMethod -Uri "https://api.resend.com/emails/$EmailId" -Headers $resendHeaders -TimeoutSec 60
            $event = $e.last_event
        } catch { $event = "poll-error" }
        if ($event -in @("delivered", "bounced", "failed", "suppressed")) { break }
    }
    return $event
}

function Get-BounceDetail {
    param([string]$EmailId)
    try {
        $e = Invoke-RestMethod -Uri "https://api.resend.com/emails/$EmailId" -Headers $resendHeaders -TimeoutSec 60
        if ($e.bounce -and $e.bounce.diagnosticCode) { return ($e.bounce.diagnosticCode -join ' ') }
    } catch { }
    return ""
}

$tokens = Get-Tokens
$resendHeaders = @{ Authorization = "Bearer $($tokens['RESEND_API_KEY'])"; "Content-Type" = "application/json" }

Write-Host "=== 1. load leads from KV ===" -ForegroundColor Cyan
$entries = Get-Leads -dlqToken $tokens['DLQ_TOKEN'] -DelaySeconds $KvDelaySeconds
Write-Host ("   {0} leads in KV" -f $entries.Count)

if ($LeadKey.Count -gt 0) {
    $entries = @($entries | Where-Object { $LeadKey -contains $_.Key })
    Write-Host ("   {0} selected by -LeadKey" -f $entries.Count)
} elseif (-not $IncludeTestLeads) {
    $real = @($entries | Where-Object { -not (Test-IsTestLead $_) })
    Write-Host ("   {0} customer leads (test leads skipped)" -f $real.Count)
    $entries = $real
}

if ($entries.Count -eq 0) { Write-Host "Nothing to send." -ForegroundColor Yellow; exit 0 }

Write-Host ""
Write-Host ("=== 2. re-send (one at a time, {0}s apart) ===" -f $SendDelaySeconds) -ForegroundColor Cyan
$sent = @()
$stopped = $null
foreach ($entry in $entries) {
    $lead = $entry.Lead
    $f = $lead.form
    $name = $(if ($f.name) { $f.name } else { "there" })
    $subject = "New quote: $name - " + (Get-Label $SERVICE_LABELS $f.service)
    $body = @{
        from       = $From
        to         = @($To)
        reply_to   = $f.email
        subject    = $subject
        html       = "<pre>" + ((Build-Text $lead) -replace '&', '&amp;' -replace '<', '&lt;') + "</pre>"
        text       = (Build-Text $lead)
    } | ConvertTo-Json -Compress -Depth 5
    Write-Host ("   {0,-16} {1,-22} -> {2}" -f $lead.reference_id, $f.email, $To)
    if ($DryRun) { Write-Host ("      [WhatIf] subject: {0}" -f $subject); continue }
    $res = Invoke-RestMethod -Method POST -Uri "https://api.resend.com/emails" -Headers $resendHeaders -Body $body -TimeoutSec 60
    $sent += [pscustomobject]@{ Id = $res.id; Ref = $lead.reference_id; Email = $f.email }
    Write-Host ("      sent id={0}" -f $res.id)

    # One message at a time: the enterprise mail server blocks a sender that
    # delivers a burst to the same recipient ("550 Mailbox unavailable or
    # access denied", 企业微信帮助中心 doc 20057). Wait for this message to
    # land before sending the next one, and stop the run on the first failure
    # instead of pushing the whole backlog into the same wall.
    $event = Wait-DeliveryEvent -EmailId $res.id -TimeoutSeconds $PollSeconds
    $color = if ($event -eq "delivered") { "Green" } else { "Yellow" }
    Write-Host ("      event: {0}" -f $event) -ForegroundColor $color
    if ($event -ne "delivered") {
        $detail = Get-BounceDetail -EmailId $res.id
        if ($detail) { Write-Host ("      bounce: {0}" -f $detail) -ForegroundColor Yellow }
        $stopped = $lead.reference_id
        Write-Host ("   STOPPED at {0} ({1}) - the rest of the backlog was NOT sent." -f $lead.reference_id, $event) -ForegroundColor Red
        Write-Host "   Check the bounce above, wait out any rate limit, then run this script again." -ForegroundColor Yellow
        break
    }
    if ($SendDelaySeconds -gt 0 -and $entry -ne $entries[$entries.Count - 1]) {
        Write-Host ("      waiting {0}s before the next one" -f $SendDelaySeconds) -ForegroundColor DarkGray
        Start-Sleep -Seconds $SendDelaySeconds
    }
}

if ($DryRun) { Write-Host "`n[WhatIf] nothing was sent." -ForegroundColor Yellow; exit 0 }

Write-Host ""
Write-Host "=== 3. summary ===" -ForegroundColor Cyan
foreach ($s in $sent) {
    $e = Invoke-RestMethod -Uri "https://api.resend.com/emails/$($s.Id)" -Headers $resendHeaders -TimeoutSec 60
    $color = if ($e.last_event -eq "delivered") { "Green" } else { "Yellow" }
    Write-Host ("   {0,-16} {1,-24} {2}" -f $s.Ref, $s.Email, $e.last_event) -ForegroundColor $color
}

Write-Host ""
if ($stopped) {
    Write-Host ("Stopped early at {0}. {1} of {2} leads were sent." -f $stopped, $sent.Count, $entries.Count) -ForegroundColor Yellow
} else {
    Write-Host ("All {0} leads were sent and confirmed delivered." -f $sent.Count) -ForegroundColor Green
}
Write-Host "Done. Every lead is still in KV (90 day TTL) until it is deleted by hand." -ForegroundColor Cyan
exit 0
