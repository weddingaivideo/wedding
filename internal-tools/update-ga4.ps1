# Replace GA4 ID across all HTML files
# Usage: powershell -ExecutionPolicy Bypass -File update-ga4.ps1 -NewId "G-XXXXXXXXXX"
# This is a thin wrapper around scripts/standardize-ga4.ps1 which also normalizes the snippet format.

param(
    [Parameter(Mandatory=$true)]
    [string]$NewId
)

& "$PSScriptRoot\scripts\standardize-ga4.ps1" -NewId $NewId
