<#
.SYNOPSIS
  Remove the duplicate noscript-wrapped stylesheet+script block created by
  the second run of defer-main-js.ps1.

.EXAMPLE
  pwsh ./cleanup-head-styles.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

$files = Get-ChildItem -Path $root -Filter "*.html" -Recurse |
         Where-Object { $_.Name -ne "google-site-verification.html" }

$updated = 0
foreach ($f in $files) {
  $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $original = $content

  # Remove the inner noscript-wrapped block (regex needs to handle the relative path)
  $pat = '(?s)<noscript>\s*<link rel="preload" href="((?:\.\./)*)styles\.css" as="style">\s*<link rel="stylesheet" href="\1styles\.css" media="print" onload="this\.media=''all''">\s*<noscript><link rel="stylesheet" href="\1styles\.css"></noscript>\s*<script defer src="\1js/main\.js"></script>\s*</noscript>\s*'
  $content = [regex]::Replace($content, $pat, "", 1)

  if ($content -ne $original) {
    [System.IO.File]::WriteAllText($f.FullName, $content, [System.Text.Encoding]::UTF8)
    Write-Host "[+] $($f.Name)" -ForegroundColor Green
    $updated++
  }
}

Write-Host ""
Write-Host "Done. files cleaned: $updated" -ForegroundColor Cyan
