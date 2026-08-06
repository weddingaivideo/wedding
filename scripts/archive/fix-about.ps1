$content = Get-Content "C:\Users\qiaoshan\.openclaw\workspace\weddingai\about.html" -Raw
$content = $content -replace '<span class="img-placeholder">.*?AI Lead.*?</span>', '<img src="images/about-team-studio.png" alt="AI Research Lead" loading="lazy">'
$content = $content -replace '<span class="img-placeholder">.*?Client Lead.*?</span>', '<img src="images/about-team-studio.png" alt="Client Experience Lead" loading="lazy">'
Set-Content "C:\Users\qiaoshan\.openclaw\workspace\weddingai\about.html" $content -NoNewline
Write-Host "Done. Replaced placeholders in about.html"
