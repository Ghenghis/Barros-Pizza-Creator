[CmdletBinding()]
param(
    [string]$SourceFolder = "",
    [string]$GameRoot = "",
    [ValidateRange(1, 500)][int]$Limit = 500,
    [ValidateSet("user-owned", "permission-granted", "reference-only")][string]$Rights = "reference-only",
    [string]$SourceUrl = ""
)

$ErrorActionPreference = "Stop"
$packageRoot = $PSScriptRoot

if ([string]::IsNullOrWhiteSpace($GameRoot)) {
    $candidates = @(
        "C:\Program Files (x86)\Steam\steamapps\common\Pizza Connection 3 - Pizza Creator",
        "S:\Unity_Games\PC3 - Pizza Creator"
    )
    $GameRoot = $candidates |
        Where-Object { Test-Path -LiteralPath (Join-Path $_ "BarrosAI\backend") } |
        Select-Object -First 1
}

if ([string]::IsNullOrWhiteSpace($SourceFolder)) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = "Select a folder containing pizza-design JPG, PNG, or WebP images"
    $dialog.ShowNewFolderButton = $false
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        throw "Inspiration import cancelled."
    }
    $SourceFolder = $dialog.SelectedPath
}

$SourceFolder = (Resolve-Path -LiteralPath $SourceFolder).Path
$tool = Join-Path $packageRoot "tools\import_inspiration_images.py"
if (-not [string]::IsNullOrWhiteSpace($GameRoot) -and (Test-Path -LiteralPath (Join-Path $GameRoot "BarrosAI\backend"))) {
    $GameRoot = (Resolve-Path -LiteralPath $GameRoot).Path
    $library = Join-Path $GameRoot "BarrosAI\backend\data\inspiration"
    $privatePython = Join-Path $GameRoot "BarrosAI\runtime\python.exe"
}
else {
    $library = Join-Path $packageRoot "backend\data\inspiration"
    $privatePython = Join-Path $packageRoot "BarrosAI\runtime\python.exe"
}
if (Test-Path -LiteralPath $privatePython) {
    $python = $privatePython
    $pythonArgs = @()
}
elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $python = "py"
    $pythonArgs = @("-3")
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python = "python"
    $pythonArgs = @()
}
else {
    throw "Python 3 was not found. Install Barro's first or install Python 3."
}

$arguments = @($pythonArgs) + @(
    $tool,
    $SourceFolder,
    "--library-dir", $library,
    "--limit", $Limit,
    "--rights", $Rights,
    "--source-label", "facebook-or-local-reference"
)
if (-not [string]::IsNullOrWhiteSpace($SourceUrl)) {
    $arguments += @("--source-url", $SourceUrl)
}

& $python @arguments
if ($LASTEXITCODE -ne 0) { throw "The inspiration image import failed." }
Write-Host "The local inspiration library is ready. Turn Ideas ON in Barro's Chat to use it." -ForegroundColor Green
