$ErrorActionPreference = "Stop"
$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"
$baseUrl = "https://weddingai.video"

function Get-LastModForPath([string]$urlPath) {
  $rel = $urlPath.Replace($baseUrl, "").TrimEnd('/')
  if ([string]::IsNullOrEmpty($rel)) {
    $local = Join-Path $root "index.html"
  } else {
    $relPath = $rel.TrimStart('/')
    if ($relPath -notmatch '\.[a-z]+$') { $relPath = "$relPath.html" }
    $local = Join-Path $root ($relPath.Replace('/', [IO.Path]::DirectorySeparatorChar))
    if ((Test-Path $local -PathType Container) -or (-not (Test-Path $local) -and (Test-Path (Join-Path $local "index.html")))) {
      $local = Join-Path $local "index.html"
    }
  }
  if (Test-Path $local) { return (Get-Item $local).LastWriteTime.ToString("yyyy-MM-dd") }
  return (Get-Date).ToString("yyyy-MM-dd")
}

function Save-Xml($doc, $path) {
  $ws = New-Object System.Xml.XmlWriterSettings
  $ws.Indent = $true
  $ws.IndentChars = "    "
  $ws.Encoding = [System.Text.Encoding]::UTF8
  $ws.OmitXmlDeclaration = $false
  $mem = New-Object System.IO.MemoryStream
  $w = [System.Xml.XmlWriter]::Create($mem, $ws)
  $doc.Save($w)
  $w.Flush(); $w.Close()
  [System.IO.File]::WriteAllBytes($path, $mem.ToArray())
}

# Update index sitemap
$indexPath = Join-Path $root "sitemap.xml"
[xml]$indexDoc = Get-Content $indexPath -Raw -Encoding UTF8
$ns = New-Object System.Xml.XmlNamespaceManager($indexDoc.NameTable)
$ns.AddNamespace("s", "http://www.sitemaps.org/schemas/sitemap/0.9")

$indexSitemaps = $indexDoc.SelectNodes("/s:sitemapindex/s:sitemap", $ns)
Write-Host "Index sitemaps: $($indexSitemaps.Count)"
foreach ($u in $indexSitemaps) {
  $lm = $u.SelectSingleNode("s:lastmod", $ns)
  if ($lm) { $lm.InnerText = (Get-Date).ToString("yyyy-MM-dd") }
}
Save-Xml $indexDoc $indexPath

# Update each per-language sitemap
$subSitemaps = Get-ChildItem $root -Filter "sitemap-*.xml"
foreach ($f in $subSitemaps) {
  [xml]$d = Get-Content $f.FullName -Raw -Encoding UTF8
  $ns2 = New-Object System.Xml.XmlNamespaceManager($d.NameTable)
  $ns2.AddNamespace("s", "http://www.sitemaps.org/schemas/sitemap/0.9")
  $ns2.AddNamespace("i", "http://www.google.com/schemas/sitemap-image/1.1")
  $urls = $d.SelectNodes("/s:urlset/s:url", $ns2)
  $updated = 0
  foreach ($u in $urls) {
    $loc = $u.SelectSingleNode("s:loc", $ns2)
    if ($loc) {
      $lm = $u.SelectSingleNode("s:lastmod", $ns2)
      if ($lm) { $lm.InnerText = Get-LastModForPath $loc.InnerText; $updated++ }
    }
  }
  Save-Xml $d $f.FullName
  Write-Host "  $($f.Name) - $updated URLs updated"
}
