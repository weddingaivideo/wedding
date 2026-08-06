$path = "C:\Users\qiaoshan\.openclaw\workspace\weddingai\services\index.html"
$c = Get-Content $path -Raw

# Step 1: Remove misplaced section IDs from inside header
$c = $c -replace '<section id="video-enhancement"></section>', ''
$c = $c -replace '<section id="absence-compensation"></section>', ''
$c = $c -replace '<section id="personalization"></section>', ''
$c = $c -replace '<section id="venue"></section>', ''

# Step 2: Add id attributes to the correct <section> opening tags
# Video Enhancement: style="background: var(--color-bg);"
$c = $c -replace '<section class="section service-group" style="background: var(--color-bg);">', '<section id="video-enhancement" class="section service-group" style="background: var(--color-bg);">'

# Absence Compensation: style="background: var(--color-white);">  (first occurrence = absence)
# We need to replace only the first occurrence of color-white for the section tags
# The pattern: after "<!-- Absence Compensation -->" comment
$parts = $c -split '(<section class="section service-group" style="background: var\(--color-white\);">)'
# Actually this is complex, let's use a different approach with index-based replacement
# Instead: find each section by its comment and modify the section tag after it

$lines = Get-Content $path
$newLines = @()
$skipNext = 0
$foundAbsence = $false
$foundVenue = $false

foreach ($line in $lines) {
    if ($line -match '<!-- Absence Compensation -->') {
        $foundAbsence = $true
        $newLines += $line
    } elseif ($line -match '<!-- Personalization -->') {
        $newLines += $line
    } elseif ($line -match '<!-- Venue -->') {
        $foundVenue = $true
        $newLines += $line
    } elseif ($foundAbsence -and $line -match '<section class="section service-group" style="background: var\(--color-white\);">') {
        $foundAbsence = $false
        $newLines += $line -replace '<section class="section service-group" style="background: var\(--color-white\);">', '<section id="absence-compensation" class="section service-group" style="background: var(--color-white);">'
    } elseif ($foundVenue -and $line -match '<section class="section service-group" style="background: var\(--color-white\);">') {
        $foundVenue = $false
        $newLines += $line -replace '<section class="section service-group" style="background: var\(--color-white\);">', '<section id="venue" class="section service-group" style="background: var(--color-white);">'
    } else {
        $newLines += $line
    }
}

$result = $newLines -join "`n"
Set-Content $path $result -NoNewline

# Verify
$verify = Get-Content $path -Raw
$sectionTags = [regex]::Matches($verify, '<section id="[^"]*"[^>]*class="section service-group"') | ForEach-Object { $_.Value }
Write-Host "Service section tags with IDs:"
$sectionTags | ForEach-Object { Write-Host "  $_" }

$inHeader = $verify -match 'header.*id="(video-enhancement|absence-compensation|personalization|venue)"'
Write-Host "IDs in header: $inHeader"
