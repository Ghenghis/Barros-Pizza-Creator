[CmdletBinding()]
param([string]$GameRoot = "S:\Unity_Games\PC3 - Pizza Creator")

$ErrorActionPreference = "Continue"
$report = New-Object Collections.Generic.List[string]
function Add-Check([string]$name, [bool]$passed, [string]$detail) {
    $line = "[{0}] {1}: {2}" -f ($(if ($passed) { "PASS" } else { "FAIL" })), $name, $detail
    $report.Add($line)
    Write-Host $line -ForegroundColor $(if ($passed) { "Green" } else { "Red" })
}

$exe = Join-Path $GameRoot "Pizza Connection 3 - Pizza Creator.exe"
$managed = Join-Path $GameRoot "Pizza Connection 3 - Pizza Creator_Data\Managed"
$assembly = Join-Path $managed "Assembly-CSharp.dll"
$core = Join-Path $GameRoot "BepInEx\core\BepInEx.dll"
$plugin = Join-Path $GameRoot "BepInEx\plugins\BarrosAI\Barros.PizzaCreator.AI.dll"
$python = Join-Path $GameRoot "BarrosAI\runtime\python.exe"
$main = Join-Path $GameRoot "BarrosAI\backend\main.py"
$settings = Join-Path $GameRoot "BarrosAI\backend\settings.json"
$banner = Join-Path $GameRoot "BarrosAI\assets\barros-pizza-creator-header.png"
$log = Join-Path $GameRoot "BepInEx\LogOutput.log"

Add-Check "Game executable" (Test-Path $exe) $exe
Add-Check "Exact managed assembly" (Test-Path $assembly) $(if (Test-Path $assembly) { (Get-FileHash -Algorithm SHA256 $assembly).Hash } else { $assembly })
Add-Check "BepInEx 5 core" (Test-Path $core) $core
Add-Check "AI plugin" (Test-Path $plugin) $(if (Test-Path $plugin) { (Get-FileHash -Algorithm SHA256 $plugin).Hash } else { $plugin })
Add-Check "Private Python" (Test-Path $python) $python
Add-Check "Backend source" (Test-Path $main) $main
Add-Check "Provider settings" (Test-Path $settings) $settings
Add-Check "Barro's header banner" (Test-Path $banner) $banner

if ((Test-Path $python) -and (Test-Path $main)) {
    & $python -m unittest discover -s (Join-Path $PSScriptRoot "tests") *> $null
    Add-Check "Packaged backend tests" ($LASTEXITCODE -eq 0) "unittest exit code $LASTEXITCODE"
}
if (Test-Path $log) {
    $content = Get-Content -LiteralPath $log -Raw
    Add-Check "Plugin observed by loader" ($content -match "Barro's AI Pizza Designer") "BepInEx\LogOutput.log"
    Add-Check "Runtime tab installed" ($content -match "Installed Barro's AI Designer as a live Pizza Creator tab") "BepInEx\LogOutput.log"
    $errors = ($content -split "`n" | Where-Object { $_ -match "Barros|AI Designer" -and $_ -match "error|exception" } | Select-Object -Last 10) -join "`n"
    if ($errors) { $report.Add("`nRelevant log errors:`n" + $errors) }
}
else { Add-Check "BepInEx log" $false "Launch the game once to create $log" }

$reportPath = Join-Path $PSScriptRoot ("Barros-AI-diagnostics-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".txt")
$report | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Host "`nReport: $reportPath"
Write-Host "F10 reopens the AI tab. If the tab is absent, send this report plus BepInEx\LogOutput.log."
