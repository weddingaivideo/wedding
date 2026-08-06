# Restore nav <li> items and contact email <li> that were accidentally removed
# by an over-greedy regex in cleanup-contact-info.ps1

$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"
$htmlFiles = Get-ChildItem $root -Recurse -Filter "*.html" -File | Where-Object { $_.Name -ne "google-site-verification.html" }

# The standard 4 nav items (depth-aware paths)
function Get-NavItems($depth) {
    $prefix = ''
    for ($i = 0; $i -lt $depth; $i++) { $prefix += '../' }
    return @(
        "                    <li><a href=`"${prefix}#services`">Services</a></li>"
        "                    <li><a href=`"${prefix}gallery.html`">Gallery</a></li>"
        "                    <li><a href=`"${prefix}about.html`">About</a></li>"
        "                    <li><a href=`"${prefix}order.html`" class=`"btn-nav`">Get a Quote</a></li>"
    )
}

# The single contact email item
function Get-ContactEmail($email) {
    return "                        <li><a href=`"mailto:$email`">$email</a></li>"
}

$fixed = 0
foreach ($file in $htmlFiles) {
    $c = Get-Content $file.FullName -Raw
    $origC = $c
    $fileChanged = $false

    $relPath = $file.FullName.Substring($root.Length).TrimStart('\').Replace('\','/')
    $depth = ($relPath.Split('/').Count - 1)

    # 1. Fix empty nav: <ul class="nav-list">
    #    followed by whitespace and </ul> (with nothing between)
    $emptyNavPattern = '(?s)(<ul class="nav-list">)\s*(</ul>)'
    if ($c -match $emptyNavPattern) {
        $navItems = Get-NavItems $depth
        $navBlock = "`n" + ($navItems -join "`n") + "`n                "
        $c = [regex]::Replace($c, $emptyNavPattern, "`$1$navBlock`$2", 1)
        $fileChanged = $true
    }

    # 2. Fix empty contact ul: <ul>\s*</ul> in footer (but only in footer, not nav)
    #    We look for the pattern: <h4>Contact</h4>\s*<ul>\s*</ul>
    $emptyContactPattern = '(?s)(<h4>Contact</h4>\s*<ul>)\s*(</ul>)'
    if ($c -match $emptyContactPattern) {
        $contactItem = Get-ContactEmail 'order@weddingai.video'
        $contactBlock = "`n$contactItem`n                    "
        $c = [regex]::Replace($c, $emptyContactPattern, "`$1$contactBlock`$2", 1)
        $fileChanged = $true
    }

    if ($fileChanged) {
        Set-Content $file.FullName $c -NoNewline
        Write-Host "FIXED: $($file.Name)"
        $fixed++
    }
}

Write-Host "---"
Write-Host "Total fixed: $fixed"

# Verify
Write-Host ""
Write-Host "=== Verification ==="
$navOK = 0
$contactOK = 0
foreach ($file in $htmlFiles) {
    $c = Get-Content $file.FullName -Raw
    if ($c -match 'class="btn-nav"') { $navOK++ }
    if ($c -match '<h4>Contact</h4>\s*<ul>\s*<li>') { $contactOK++ }
}
Write-Host "Pages with nav Get a Quote button:  $navOK / $($htmlFiles.Count)"
Write-Host "Pages with Contact email <li>:      $contactOK / $($htmlFiles.Count)"
