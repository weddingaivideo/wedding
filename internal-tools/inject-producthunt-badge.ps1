<#
.SYNOPSIS
  DISABLED: No-op. The Product Hunt badge was removed from the site footer because
  weddingai.video does not have a Product Hunt page (the link was returning 403/404
  in SEO audits). Re-enable this script only when the Product Hunt page is created.

.HISTORY
  2026-08-04 — Disabled. Previously injected a Product Hunt "Featured" badge
                into the site footer of every HTML page. The page does not exist;
                the badge is misleading (claims a "Featured on Product Hunt"
                social proof that is not real).
#>

$ErrorActionPreference = "Stop"
Write-Host "inject-producthunt-badge.ps1 is disabled (no Product Hunt page exists)." -ForegroundColor Yellow
Write-Host "Delete this script when you no longer need to remember why it is disabled." -ForegroundColor DarkGray
exit 0
