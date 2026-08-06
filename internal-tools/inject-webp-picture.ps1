<#
.SYNOPSIS
  Convert <img src="images/foo.jpg"> to <picture><source srcset="images/foo.webp"> <img src="images/foo.jpg"></picture>.

.DESCRIPTION
  Idempotent. Skips images that don't have a .webp counterpart. Preserves all
  other attributes (alt, loading, width, height, fetchpriority, class, etc).

.EXAMPLE
  pwsh ./inject-webp-picture.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$imgDir = Join-Path $root "images"
$webpSet = @{}
Get-ChildItem -Path $imgDir -Filter "*.webp" -File | ForEach-Object {
  $webpSet[$_.BaseName] = $_.Name
}

$files = Get-ChildItem -Path $root -Filter "*.html" -Recurse |
         Where-Object { $_.Name -ne "google-site-verification.html" }

$updated = 0; $replaced = 0
foreach ($f in $files) {
  $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $original = $content

  # Match <img ... src="path/to/foo.jpg" ...>
  $pattern = '<img\s+([^>]*?)src="([^"]+)"([^>]*?)\s*/?>'
  $content = [regex]::Replace($content, $pattern, {
    param($m)
    $before = $m.Groups[1].Value
    $src = $m.Groups[2].Value
    $after = $m.Groups[3].Value
    $selfClose = if ($m.Value -match '/>\s*$') { ' />' } else { '>' }

    # Resolve the basename
    $base = [System.IO.Path]::GetFileNameWithoutExtension($src)
    if (-not $webpSet.ContainsKey($base)) {
      # No webp counterpart - leave as-is
      return $m.Value
    }

    # If src already points to .webp, skip
    if ($src -match '\.webp$') { return $m.Value }

    # If we're already inside a <picture>, skip
    # (rough check: look at recent context)
    $idx = $m.Index
    if ($idx -gt 200) {
      $preceding = $content.Substring([Math]::Max(0, $idx - 200), [Math]::Min(200, $idx))
      if ($preceding -match '<picture[^>]*>\s*<source[^>]+image/webp') {
        return $m.Value
      }
    }

    $webpSrc = ([System.IO.Path]::GetDirectoryName($src) -replace '\\','/') + '/' + $webpSet[$base]
    $webpSrc = $webpSrc -replace '/./', '/'
    $webpSrc = $webpSrc -replace '^\./', ''

    $script:replaced++
    return "<picture><source srcset=`"$webpSrc`" type=`"image/webp`"><img $before src=`"$src`"$after$selfClose</picture>"
  }, [System.Text.RegularExpressions.RegexOptions]::Singleline)

  if ($content -ne $original) {
    [System.IO.File]::WriteAllText($f.FullName, $content, [System.Text.Encoding]::UTF8)
    Write-Host "[+] $($f.FullName.Substring($root.Length + 1))" -ForegroundColor Green
    $updated++
  }
}

Write-Host ""
Write-Host "Done. files updated: $updated, img->picture swaps: $replaced" -ForegroundColor Cyan
