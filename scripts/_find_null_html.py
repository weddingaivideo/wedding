"""Find which HTML file Get-Content returns null for."""
import subprocess
import os
root = r'C:\Users\qiaoshan\.openclaw\workspace\weddingai'
ps_script = f'''
$ErrorActionPreference = 'Stop'
$root = '{root}'
$files = Get-ChildItem -Path $root -Recurse -Filter '*.html' -File
$deployedHtml = $files | Where-Object {{
    $_.FullName -notlike '*\tmp\*' -and
    $_.FullName -notlike '*\i18n\*' -and
    $_.FullName -notlike '*\qa\*' -and
    $_.FullName -notlike '*\admin\*' -and
    $_.FullName -notlike '*\scripts\*' -and
    $_.FullName -notlike '*\node_modules\*' -and
    $_.FullName -notlike '*\functions\*'
}}
Write-Host "Total: $($deployedHtml.Count)"
$bad = 0
foreach ($f in $deployedHtml) {{
    try {{
        $c = Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue
        if ($null -eq $c) {{
            Write-Host "NULL: $($f.FullName)"
            $bad++
        }}
    }} catch {{
        Write-Host "ERR: $($f.FullName): $_"
        $bad++
    }}
}}
Write-Host "Bad: $bad"
'''
result = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script], capture_output=True, text=True, timeout=60)
print('STDOUT:', result.stdout[-3000:])
print('STDERR:', result.stderr[-1000:])
