# Remove all non-email contact methods. Only keep order@weddingai.video as the sole contact.

$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"
$htmlFiles = Get-ChildItem $root -Recurse -Filter "*.html" -File | Where-Object { $_.Name -ne "google-site-verification.html" }

$totalChanged = 0

foreach ($file in $htmlFiles) {
    $c = Get-Content $file.FullName -Raw
    $origC = $c
    $fileChanged = $false

    # 1. Replace email everywhere
    if ($c -match 'hello@weddingai\.video') {
        $c = $c -replace 'hello@weddingai\.video', 'order@weddingai.video'
        $fileChanged = $true
    }

    # 2. Remove the WhatsApp <li> from footer
    $whatsappLiPattern = '(?s)\s*<li>.*?WhatsApp.*?</li>'
    if ($c -match $whatsappLiPattern) {
        $c = [regex]::Replace($c, $whatsappLiPattern, '', 1)
        $fileChanged = $true
    }

    # 3. Remove the entire social-links div from footer
    $socialPattern = '(?s)\s*<div class="social-links">.*?</div>'
    if ($c -match $socialPattern) {
        $c = [regex]::Replace($c, $socialPattern, '', 1)
        $fileChanged = $true
    }

    # 4. In order.html, simplify the direct-contact section to only keep email
    # The contact-methods block has multiple <a class="contact-method"> entries (Email, WhatsApp, Instagram, TikTok)
    # We want to keep only the email one
    if ($file.Name -eq 'order.html') {
        # Match the contact-methods block
        $contactBlockPattern = '(?s)(<div class="contact-methods">)(.*?)(</div>)'
        $match = [regex]::Match($c, $contactBlockPattern)
        if ($match.Success) {
            $inner = $match.Groups[2].Value
            # Keep only the email <a> (first one, which has mailto:order@...)
            $emailMethodPattern = '(?s)\s*<a href="mailto:[^"]+" class="contact-method">.*?</a>'
            $emailMatch = [regex]::Match($inner, $emailMethodPattern)
            if ($emailMatch.Success) {
                # Wrap in proper grid (it's a flex container, but we just keep one)
                $newInner = "`n                    $($emailMatch.Value.Trim())`n                "
                $c = $c.Substring(0, $match.Index) + $match.Groups[1].Value + $newInner + $match.Groups[3].Value + $c.Substring($match.Index + $match.Length)
                $fileChanged = $true
            }
        }
    }

    # 5. Update schema.org email in index.html
    if ($file.Name -in @('index.html') -and $c -match '"email":\s*"[^"]+"') {
        $c = $c -replace '"email":\s*"[^"]+"', '"email": "order@weddingai.video"'
        $fileChanged = $true
    }

    if ($fileChanged) {
        Set-Content $file.FullName $c -NoNewline
        Write-Host "CHANGED: $($file.Name)"
        $totalChanged++
    }
}

Write-Host "---"
Write-Host "Total files changed: $totalChanged"

# Verify
Write-Host ""
Write-Host "=== Verification ==="
$helloCount = 0
$phoneCount = 0
$socialTextCount = 0
$socialHandleCount = 0
$orderEmailCount = 0
foreach ($file in $htmlFiles) {
    $c = Get-Content $file.FullName -Raw
    $helloCount += ([regex]::Matches($c, 'hello@weddingai\.video')).Count
    $phoneCount += ([regex]::Matches($c, '\+1 \(555\) 000-0000')).Count
    $socialTextCount += ([regex]::Matches($c, 'WhatsApp|Instagram|TikTok|YouTube')).Count
    $socialHandleCount += ([regex]::Matches($c, '@weddingai\.video')).Count
    $orderEmailCount += ([regex]::Matches($c, 'order@weddingai\.video')).Count
}
Write-Host "hello@ references remaining: $helloCount (should be 0)"
Write-Host "phone numbers remaining:      $phoneCount (should be 0)"
Write-Host "social media text remaining:  $socialTextCount (should be 0)"
Write-Host "@weddingai.video handles:     $socialHandleCount (should be 0)"
Write-Host "order@ references:            $orderEmailCount"
