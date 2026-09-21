# Sync collections/tools.json -> web deploy artifacts
# Usage: powershell -File scripts/sync-catalog.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$src = Join-Path $root "collections\tools.json"
$jsOut = Join-Path $root "web\assets\js\catalog-data.js"
$jsonOut = Join-Path $root "web\assets\data\tools.json"

if (-not (Test-Path $src)) {
  throw "catalog source not found: $src"
}

$raw = Get-Content $src -Raw -Encoding UTF8
$data = $raw | ConvertFrom-Json
$tools = $data.tools
Write-Host ("catalog tools: " + $tools.Count)

# JSON copy for HTTP fetch consumers
Copy-Item $src $jsonOut -Force

# JS payload so file:// double-click still works
$js = "/* Auto-generated from collections/tools.json — do not edit by hand. Run scripts/sync-catalog.ps1 */`n"
$js += "window.SUSU_CATALOG = "
$js += ($raw.Trim() + ";`n")
# Ensure UTF-8 without BOM issues on Windows PowerShell 5
[System.IO.File]::WriteAllText($jsOut, $js, [System.Text.UTF8Encoding]::new($false))
Write-Host ("wrote " + $jsOut)
Write-Host ("wrote " + $jsonOut)
