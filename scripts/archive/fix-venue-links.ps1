# Fix /services/venue.html -> /services/#venue in all service page footers
# Venue section doesn't have a standalone page; it's a section on services/index.html

$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"

$htmlFiles = Get-ChildItem $root -Recurse -Include "*.html"

foreach ($file in $htmlFiles) {
    $content = Get-Content $file.FullName -Raw
    $original = $content

    # Fix /services/venue.html -> /services/#venue (venue is a section on services/index.html)
    $content = $content -replace 'href="/services/venue\.html"', 'href="/services/#venue"'
    # Also handle the original /services/venue/ form if any remain
    $content = $content -replace 'href="/services/venue/"', 'href="/services/#venue"'

    if ($content -ne $original) {
        Set-Content $file.FullName $content -NoNewline
        Write-Host "Fixed venue link: $($file.Name)"
    }
}

Write-Host "Done."
