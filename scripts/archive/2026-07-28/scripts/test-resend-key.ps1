# Test Resend API key directly
# Reads the key from $env:RESEND_API_KEY — never hardcode it here.
$key = $env:RESEND_API_KEY
if (-not $key) {
    Write-Host "ERROR: Set the RESEND_API_KEY environment variable first, e.g." -ForegroundColor Red
    Write-Host '  $env:RESEND_API_KEY = "re_xxx"' -ForegroundColor Yellow
    Write-Host "  powershell -File scripts\test-resend-key.ps1" -ForegroundColor Yellow
    exit 1
}
$headers = @{
    "Authorization" = "Bearer $key"
    "Content-Type"  = "application/json"
}

# Use Resend's own test sender to bypass domain verification
$payload = @{
    from    = "onboarding@resend.dev"
    to      = @("order@weddingai.video")
    subject = "Direct API key test"
    html    = "<p>If you get this, the key is valid.</p>"
} | ConvertTo-Json -Compress

Write-Host "=== Test 1: Send email with onboarding@resend.dev ==="
Write-Host "Key prefix: $($key.Substring(0, 8))..."

try {
    $r = Invoke-WebRequest `
        -Uri "https://api.resend.com/emails" `
        -Method POST `
        -Headers $headers `
        -Body $payload `
        -UseBasicParsing `
        -TimeoutSec 15 `
        -ErrorAction Stop

    Write-Host "Status: $($r.StatusCode)"
    Write-Host "Body: $($r.Content)"
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    $raw = $_.Exception.Response.GetResponseStream()
    $reader = [System.IO.StreamReader]::new($raw)
    $bodyText = $reader.ReadToEnd()
    Write-Host "Status: $code"
    Write-Host "Body: '$bodyText'"
}

Write-Host ""
Write-Host "=== Test 2: Check API key info (GET /api-keys is not allowed; trying /domains) ==="
try {
    $r = Invoke-WebRequest `
        -Uri "https://api.resend.com/domains" `
        -Method GET `
        -Headers $headers `
        -UseBasicParsing `
        -TimeoutSec 15 `
        -ErrorAction Stop
    Write-Host "Status: $($r.StatusCode)"
    Write-Host "Body: $($r.Content)"
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    $raw = $_.Exception.Response.GetResponseStream()
    $reader = [System.IO.StreamReader]::new($raw)
    $bodyText = $reader.ReadToEnd()
    Write-Host "Status: $code"
    Write-Host "Body: '$bodyText'"
}
