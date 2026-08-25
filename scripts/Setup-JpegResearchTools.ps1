param(
    [string]$ToolRoot = "",
    [switch]$SkipPythonPackages,
    [switch]$InstallRenderDoc,
    [switch]$InstallImageMagick,
    [switch]$PromptOptional
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($ToolRoot)) {
    $creatorRoot = "S:\Unity_Games\PC3 - Pizza Creator"
    if (Test-Path -LiteralPath $creatorRoot -PathType Container) {
        $ToolRoot = Join-Path $creatorRoot "_research-tools"
    } else {
        $ToolRoot = Join-Path $repoRoot "_research-tools"
    }
}

$downloads = Join-Path $ToolRoot "downloads"
$apps = Join-Path $ToolRoot "apps"
$evidence = Join-Path $ToolRoot "evidence"
New-Item -ItemType Directory -Force -Path $downloads, $apps, $evidence | Out-Null

function Get-Sha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-VerifiedDownload {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Sha256,
        [string]$FileName
    )
    $destination = Join-Path $downloads $FileName
    if (Test-Path -LiteralPath $destination -PathType Leaf) {
        $existing = Get-Sha256 $destination
        if ($existing -eq $Sha256.ToLowerInvariant()) {
            Write-Host "[PASS] $Name already downloaded and hash-verified."
            return $destination
        }
        $bad = $destination + ".bad-" + (Get-Date -Format "yyyyMMdd-HHmmss")
        Move-Item -LiteralPath $destination -Destination $bad -Force
        Write-Warning "$Name existing download had the wrong hash and was quarantined to $bad"
    }

    Write-Host "[GET]  $Name"
    Invoke-WebRequest -Uri $Url -OutFile $destination -UseBasicParsing
    $actual = Get-Sha256 $destination
    if ($actual -ne $Sha256.ToLowerInvariant()) {
        $bad = $destination + ".bad-hash"
        Move-Item -LiteralPath $destination -Destination $bad -Force
        throw "$Name SHA-256 mismatch. Expected $Sha256, got $actual. Download quarantined."
    }
    Write-Host "[PASS] $Name hash verified: $actual"
    return $destination
}

function Expand-VerifiedZip {
    param(
        [string]$Archive,
        [string]$Destination,
        [string]$Marker
    )
    if (Test-Path -LiteralPath $Marker -PathType Leaf) {
        Write-Host "[PASS] Already staged: $Destination"
        return
    }
    if (Test-Path -LiteralPath $Destination) {
        Remove-Item -LiteralPath $Destination -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    Expand-Archive -LiteralPath $Archive -DestinationPath $Destination -Force
    if (-not (Test-Path -LiteralPath $Marker -PathType Leaf)) {
        throw "Archive extracted but expected marker is missing: $Marker"
    }
    Write-Host "[PASS] Staged: $Destination"
}

$manifest = @(
    [pscustomobject]@{
        Name = "ILSpy 10.1.1 self-contained x64"
        Url = "https://github.com/icsharpcode/ILSpy/releases/download/v10.1.1/ILSpy_selfcontained_10.1.1.8388-x64.zip"
        Sha256 = "e2e733760f10e215aa705fba393601a1c7c6536cccda594bda56f45a4c42e2ae"
        FileName = "ILSpy_selfcontained_10.1.1.8388-x64.zip"
        AppDir = "ILSpy-10.1.1"
        Marker = "ILSpy.exe"
    },
    [pscustomobject]@{
        Name = "dnSpyEx 6.6.0 Windows x64"
        Url = "https://github.com/dnSpyEx/dnSpy/releases/download/v6.6.0/dnSpy-net-win64.zip"
        Sha256 = "8ed48f165dc355e869f3a0037ad4f9216147f995a5ae0258b296eeef1f73aab0"
        FileName = "dnSpy-net-win64.zip"
        AppDir = "dnSpyEx-6.6.0"
        Marker = "dnSpy.exe"
    },
    [pscustomobject]@{
        Name = "AssetRipper 2.0.0 Windows x64"
        Url = "https://github.com/AssetRipper/AssetRipper/releases/download/2.0.0/AssetRipper_win_x64.zip"
        Sha256 = "9a7ef0e7c5c3ea5b90b4e6d855e2d98d5f7ec8c3f9e26fccbc194c6a7b01baf7"
        FileName = "AssetRipper_win_x64.zip"
        AppDir = "AssetRipper-2.0.0"
        Marker = "AssetRipper.GUI.Free.exe"
    }
)

$toolRecords = @()
foreach ($item in $manifest) {
    $archive = Get-VerifiedDownload $item.Name $item.Url $item.Sha256 $item.FileName
    $destination = Join-Path $apps $item.AppDir
    $marker = Join-Path $destination $item.Marker
    Expand-VerifiedZip $archive $destination $marker
    $toolRecords += [ordered]@{
        name = $item.Name
        source = $item.Url
        download = $archive
        download_sha256 = Get-Sha256 $archive
        staged_path = $destination
        marker = $marker
        marker_sha256 = Get-Sha256 $marker
    }
}

$jpegInstaller = Get-VerifiedDownload \
    "libjpeg-turbo 3.2.0 Visual C++ x64" \
    "https://github.com/libjpeg-turbo/libjpeg-turbo/releases/download/3.2.0/libjpeg-turbo-3.2.0-vc-x64.exe" \
    "662761d8ba8dae04aec74023ebaeceb856c2b56b9b59cfd180759d26300dda42" \
    "libjpeg-turbo-3.2.0-vc-x64.exe"
$toolRecords += [ordered]@{
    name = "libjpeg-turbo 3.2.0 Visual C++ x64 installer"
    source = "https://github.com/libjpeg-turbo/libjpeg-turbo/releases/tag/3.2.0"
    download = $jpegInstaller
    download_sha256 = Get-Sha256 $jpegInstaller
    staged_path = $null
    note = "Downloaded and verified only; installer is not silently executed by this staging script."
}

function Resolve-Python {
    foreach ($name in @("py", "python", "python3")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    return ""
}

$pythonInfo = [ordered]@{}
$python = Resolve-Python
if (-not $python) {
    $pythonInfo.state = "blocked"
    $pythonInfo.detail = "Python not found on PATH; raw JPEG structure analyzer can run later after Python is available."
    Write-Warning $pythonInfo.detail
} else {
    $venv = Join-Path $ToolRoot "python-env"
    if (-not (Test-Path -LiteralPath (Join-Path $venv "Scripts\python.exe") -PathType Leaf)) {
        Write-Host "[SETUP] Creating isolated Python analysis environment."
        & $python -m venv $venv
        if ($LASTEXITCODE -ne 0) { throw "Python venv creation failed." }
    }
    $venvPython = Join-Path $venv "Scripts\python.exe"
    if (-not $SkipPythonPackages) {
        Write-Host "[SETUP] Installing/upgrading Pillow, numpy and scikit-image in isolated analysis venv."
        & $venvPython -m pip install --upgrade pip
        if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
        & $venvPython -m pip install --upgrade Pillow numpy scikit-image
        if ($LASTEXITCODE -ne 0) { throw "Python image-analysis dependency install failed." }
    }
    $pythonVersion = (& $venvPython --version 2>&1 | Out-String).Trim()
    $freeze = @(& $venvPython -m pip freeze 2>&1)
    $freezePath = Join-Path $evidence "python-pip-freeze.txt"
    $freeze | Set-Content -LiteralPath $freezePath -Encoding UTF8
    $pythonInfo.state = "ready"
    $pythonInfo.python = $venvPython
    $pythonInfo.version = $pythonVersion
    $pythonInfo.pip_freeze = $freezePath
}

if ($PromptOptional) {
    Add-Type -AssemblyName System.Windows.Forms
    $renderChoice = [System.Windows.Forms.MessageBox]::Show(
        "Install RenderDoc 1.45 through Windows Package Manager?`r`n`r`nThis is optional and mainly needed if source/dnSpy tracing cannot fully expose draw order and render targets.",
        "PC3 Creator Research Tools",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    if ($renderChoice -eq [System.Windows.Forms.DialogResult]::Yes) { $InstallRenderDoc = $true }

    $magickChoice = [System.Windows.Forms.MessageBox]::Show(
        "Install current official ImageMagick Q16-HDRI through Windows Package Manager?`r`n`r`nThe repository analyzer works without it, but ImageMagick provides additional comparison metrics and inspection tools.",
        "PC3 Creator Research Tools",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    if ($magickChoice -eq [System.Windows.Forms.DialogResult]::Yes) { $InstallImageMagick = $true }
}

$optional = [ordered]@{}
$winget = Get-Command winget -ErrorAction SilentlyContinue
if (($InstallRenderDoc -or $InstallImageMagick) -and -not $winget) {
    Write-Warning "winget is unavailable; optional RenderDoc/ImageMagick installation is blocked."
}
if ($InstallRenderDoc -and $winget) {
    Write-Host "[SETUP] Installing pinned RenderDoc 1.45.0 via winget."
    & winget install --id BaldurKarlsson.RenderDoc --exact --version 1.45.0 --accept-package-agreements --accept-source-agreements
    $optional.renderdoc_exit = $LASTEXITCODE
    $optional.renderdoc_package = "BaldurKarlsson.RenderDoc 1.45.0"
}
if ($InstallImageMagick -and $winget) {
    Write-Host "[SETUP] Installing current official ImageMagick Q16-HDRI via winget."
    & winget install ImageMagick.Q16-HDRI --accept-package-agreements --accept-source-agreements
    $optional.imagemagick_exit = $LASTEXITCODE
    $optional.imagemagick_package = "ImageMagick.Q16-HDRI"
}

$record = [ordered]@{
    schema_version = "1.0"
    kind = "pc3-creator-jpeg-research-tool-staging"
    created_at = (Get-Date).ToUniversalTime().ToString("o")
    scope = "PC3 Pizza Creator only"
    tool_root = $ToolRoot
    tools = $toolRecords
    python_analysis = $pythonInfo
    optional_installs = $optional
    truth_note = "Tool staging/provenance only. Installed tools do not promote any runtime or JPEG reverse-engineering gate."
}
$recordPath = Join-Path $evidence "tool-versions.json"
$record | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $recordPath -Encoding UTF8

Write-Host ""
Write-Host "PC3 Creator JPEG research tool staging complete."
Write-Host "Tools:    $ToolRoot"
Write-Host "Evidence: $recordPath"
Write-Host "libjpeg installer retained (not executed): $jpegInstaller"

if ($PromptOptional) {
    [System.Windows.Forms.MessageBox]::Show(
        "PC3 Creator research-tool staging finished.`r`n`r`nTool root:`r`n$ToolRoot`r`n`r`nProvenance:`r`n$recordPath",
        "PC3 Creator Research Tools",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    ) | Out-Null
}
