param(
    [string]$ImageA = "",
    [string]$ImageB = "",
    [string]$ModelA = "",
    [string]$ModelB = "",
    [string]$OutDir = "",
    [string]$ExperimentId = "manual-pair"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$analyzer = Join-Path $repoRoot "scripts\analyze_jpeg_experiment.py"
if (-not (Test-Path -LiteralPath $analyzer -PathType Leaf)) {
    throw "JPEG analyzer is missing: $analyzer"
}

Add-Type -AssemblyName System.Windows.Forms

function Select-File {
    param(
        [string]$Title,
        [string]$Filter,
        [string]$InitialDirectory = ""
    )
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = $Title
    $dialog.Filter = $Filter
    $dialog.CheckFileExists = $true
    $dialog.Multiselect = $false
    if ($InitialDirectory -and (Test-Path -LiteralPath $InitialDirectory -PathType Container)) {
        $dialog.InitialDirectory = $InitialDirectory
    }
    $result = $dialog.ShowDialog()
    if ($result -ne [System.Windows.Forms.DialogResult]::OK) { return "" }
    return $dialog.FileName
}

function Select-Folder {
    param([string]$Description)
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Description
    $dialog.ShowNewFolderButton = $true
    $result = $dialog.ShowDialog()
    if ($result -ne [System.Windows.Forms.DialogResult]::OK) { return "" }
    return $dialog.SelectedPath
}

function Resolve-Python {
    $candidates = @(
        (Get-Command py -ErrorAction SilentlyContinue),
        (Get-Command python -ErrorAction SilentlyContinue),
        (Get-Command python3 -ErrorAction SilentlyContinue)
    ) | Where-Object { $_ -ne $null }
    if ($candidates.Count -eq 0) {
        throw "Python was not found on PATH. Install/use the existing Creator Python runtime, then rerun."
    }
    return $candidates[0].Source
}

if (-not $ImageA) {
    $ImageA = Select-File "Select baseline native Pizza Creator JPEG (A)" "JPEG images (*.jpg;*.jpeg)|*.jpg;*.jpeg|All files (*.*)|*.*"
}
if (-not $ImageA) { Write-Host "Canceled before image A."; exit 2 }

if (-not $ImageB) {
    $ImageB = Select-File "Select variant native Pizza Creator JPEG (B)" "JPEG images (*.jpg;*.jpeg)|*.jpg;*.jpeg|All files (*.*)|*.*" (Split-Path -Parent $ImageA)
}
if (-not $ImageB) { Write-Host "Canceled before image B."; exit 2 }

if (-not $ModelA) {
    $choice = [System.Windows.Forms.MessageBox]::Show(
        "Do you want to bind a model/signature JSON to image A?",
        "PC3 Native JPEG Research",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    if ($choice -eq [System.Windows.Forms.DialogResult]::Yes) {
        $ModelA = Select-File "Select model/signature JSON for A" "JSON (*.json)|*.json|All files (*.*)|*.*" (Split-Path -Parent $ImageA)
    }
}
if (-not $ModelB) {
    $choice = [System.Windows.Forms.MessageBox]::Show(
        "Do you want to bind a model/signature JSON to image B?",
        "PC3 Native JPEG Research",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    if ($choice -eq [System.Windows.Forms.DialogResult]::Yes) {
        $ModelB = Select-File "Select model/signature JSON for B" "JSON (*.json)|*.json|All files (*.*)|*.*" (Split-Path -Parent $ImageB)
    }
}

if (-not $OutDir) {
    $OutDir = Select-Folder "Choose or create an output folder for the JPEG comparison evidence"
}
if (-not $OutDir) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutDir = Join-Path $repoRoot ("evidence\jpeg-research\pair-" + $stamp)
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$python = Resolve-Python
$argsList = @(
    $analyzer,
    $ImageA,
    $ImageB,
    "--out", $OutDir,
    "--experiment-id", $ExperimentId,
    "--label-a", "A",
    "--label-b", "B"
)
if ($ModelA) { $argsList += @("--model-a", $ModelA) }
if ($ModelB) { $argsList += @("--model-b", $ModelB) }

Write-Host "PC3 Pizza Creator native JPEG analysis"
Write-Host "A: $ImageA"
Write-Host "B: $ImageB"
Write-Host "Output: $OutDir"
Write-Host ""

& $python @argsList
$code = $LASTEXITCODE
if ($code -ne 0) {
    [System.Windows.Forms.MessageBox]::Show(
        "Analysis failed with exit code $code. See the console output for the factual error.",
        "PC3 Native JPEG Research",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    ) | Out-Null
    exit $code
}

$report = Join-Path $OutDir "analysis.json"
[System.Windows.Forms.MessageBox]::Show(
    "Analysis complete.`r`n`r`nReport:`r`n$report",
    "PC3 Native JPEG Research",
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Information
) | Out-Null

if (Test-Path -LiteralPath $OutDir) {
    Start-Process explorer.exe -ArgumentList ('"' + $OutDir + '"')
}
exit 0
