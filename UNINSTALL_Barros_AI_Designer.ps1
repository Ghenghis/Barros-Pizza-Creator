[CmdletBinding()]
param(
    [string]$GameRoot = "S:\Unity_Games\PC3 - Pizza Creator",
    [switch]$RemoveSharedBepInEx
)
$ErrorActionPreference = "Stop"
$exe = Join-Path $GameRoot "Pizza Connection 3 - Pizza Creator.exe"
if (-not (Test-Path $exe)) { throw "Pizza Creator was not found under $GameRoot" }
$processName = [IO.Path]::GetFileNameWithoutExtension($exe)
$running = Get-Process -Name $processName -ErrorAction SilentlyContinue
if ($running) { throw "Close Pizza Connection 3 - Pizza Creator before uninstalling." }
$plugin = Join-Path $GameRoot "BepInEx\plugins\BarrosAI"
$data = Join-Path $GameRoot "BarrosAI"
if (Test-Path $plugin) { Remove-Item -LiteralPath $plugin -Recurse -Force }
if (Test-Path $data) { Remove-Item -LiteralPath $data -Recurse -Force }
if ($RemoveSharedBepInEx) {
    Remove-Item -LiteralPath (Join-Path $GameRoot "BepInEx") -Recurse -Force -ErrorAction SilentlyContinue
    foreach ($name in @("winhttp.dll", "doorstop_config.ini", ".doorstop_version", "changelog.txt")) {
        Remove-Item -LiteralPath (Join-Path $GameRoot $name) -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "Barro's AI Pizza Designer was removed. Original game assemblies and saves were never modified." -ForegroundColor Green
