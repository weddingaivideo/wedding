<#
.SYNOPSIS
  Regenerate sitemap.xml with lastmod pulled from each HTML file's mtime.

.DESCRIPTION
  Walks the workspace, finds every *.html page, and rewrites sitemap.xml
  with accurate <lastmod> dates. Preserves the existing image:image block
  for each URL and the existing priority/changefreq settings.

.EXAMPLE
  pwsh ./update-sitemap.ps1
#>

$ErrorActionPreference = "Stop"
$root       = $PSScriptRoot
$sitemapIn  = Join-Path $root "sitemap.xml"
$baseUrl    = "https://weddingai.video"

# Load current sitemap as XML so we keep the per-URL <image:image> blocks
[xml]$doc = Get-Content $sitemapIn -Raw -Encoding UTF8
$ns = New-Object System.Xml.XmlNamespaceManager($doc.NameTable)
$ns.AddNamespace("s", "http://www.sitemaps.org/schemas/sitemap/0.9")
$ns.AddNamespace("i", "http://www.google.com/schemas/sitemap-image/1.1")

function Get-LastModForPath([string]$urlPath) {
  # Convert https://weddingai.video/about -> /about -> root\about.html
  # (sitemap now uses clean URLs; map them back to the on-disk .html file)
  $rel = $urlPath.Replace($baseUrl, "").TrimEnd('/')
  if ([string]::IsNullOrEmpty($rel)) {
    # Root -> index.html
    $local = Join-Path $root "index.html"
  } else {
    $relPath = $rel.TrimStart('/')
    # If URL has no extension, try .html (e.g. /about -> about.html)
    if ($relPath -notmatch '\.[a-z]+$') {
      $relPath = "$relPath.html"
    }
    $local = Join-Path $root ($relPath.Replace('/', [IO.Path]::DirectorySeparatorChar))
    # If directory-style URL (e.g. /services/), append index.html
    if ((Test-Path $local -PathType Container) -or (-not (Test-Path $local) -and (Test-Path (Join-Path $local "index.html")))) {
      $local = Join-Path $local "index.html"
    }
  }
  if (Test-Path $local) {
    return (Get-Item $local).LastWriteTime.ToString("yyyy-MM-dd")
  }
  return (Get-Date).ToString("yyyy-MM-dd")
}

# Update each <lastmod> using the actual file mtime
$urls = $doc.SelectNodes("//s:url", $ns)
foreach ($u in $urls) {
  $loc = $u.SelectSingleNode("s:loc", $ns).InnerText
  $lastmod = $u.SelectSingleNode("s:lastmod", $ns)
  if ($lastmod) {
    $lastmod.InnerText = Get-LastModForPath $loc
  }
}

# Pretty-print
$writerSettings = New-Object System.Xml.XmlWriterSettings
$writerSettings.Indent = $true
$writerSettings.IndentChars = "    "
$writerSettings.Encoding = [System.Text.Encoding]::UTF8
$writerSettings.OmitXmlDeclaration = $false

$mem = New-Object System.IO.MemoryStream
$writer = [System.Xml.XmlWriter]::Create($mem, $writerSettings)
$doc.Save($writer)
$writer.Flush(); $writer.Close()
[System.IO.File]::WriteAllBytes($sitemapIn, $mem.ToArray())

Write-Host "[ok] sitemap.xml updated - $($urls.Count) URLs" -ForegroundColor Green
Get-Content $sitemapIn | Select-String -Pattern "<lastmod>" | ForEach-Object { Write-Host "  $($_.Line.Trim())" }
