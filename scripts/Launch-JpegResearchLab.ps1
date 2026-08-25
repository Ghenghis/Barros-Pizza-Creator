param(
    [string]$CreatorRoot = "S:\Unity_Games\PC3 - Pizza Creator",
    [string]$StudioRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path

function Find-Python {
    $researchPython = Join-Path $CreatorRoot "_research-tools\python-env\Scripts\python.exe"
    if (Test-Path -LiteralPath $researchPython -PathType Leaf) { return $researchPython }
    $localResearch = Join-Path $repoRoot "_research-tools\python-env\Scripts\python.exe"
    if (Test-Path -LiteralPath $localResearch -PathType Leaf) { return $localResearch }
    foreach ($name in @("py", "python", "python3")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    return ""
}

function Find-StudioRoot {
    $candidates = @()
    if ($StudioRoot) { $candidates += $StudioRoot }
    if ($env:BARROS_STUDIO_ROOT) { $candidates += $env:BARROS_STUDIO_ROOT }
    $candidates += @(
        "S:\Unity_Games\PC3\_agent-workspaces\chatgpt-pc3-main",
        "S:\Unity_Games\PC3\_agent-workspaces\chatgpt-pc3-studio",
        (Join-Path (Split-Path $repoRoot -Parent) "PC3_Barros_Runtime_Proof_Studio")
    )
    foreach ($candidate in $candidates) {
        if (-not $candidate) { continue }
        $generator = Join-Path $candidate "scripts\generate_creator_controlled_stimuli.py"
        $scope = Join-Path $candidate "00_READ_FIRST_PC3_ONLY.md"
        if ((Test-Path -LiteralPath $generator -PathType Leaf) -and (Test-Path -LiteralPath $scope -PathType Leaf)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return ""
}

function Select-File {
    param([string]$Title, [string]$Filter, [string]$InitialDirectory = "")
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = $Title
    $dialog.Filter = $Filter
    $dialog.CheckFileExists = $true
    if ($InitialDirectory -and (Test-Path -LiteralPath $InitialDirectory -PathType Container)) {
        $dialog.InitialDirectory = $InitialDirectory
    }
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { return "" }
    return $dialog.FileName
}

function Select-Folder {
    param([string]$Description, [string]$SelectedPath = "")
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Description
    $dialog.ShowNewFolderButton = $true
    if ($SelectedPath -and (Test-Path -LiteralPath $SelectedPath -PathType Container)) {
        $dialog.SelectedPath = $SelectedPath
    }
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { return "" }
    return $dialog.SelectedPath
}

function Show-Error([string]$Message) {
    [System.Windows.Forms.MessageBox]::Show(
        $Message,
        "PC3 Native JPEG Research Lab",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    ) | Out-Null
}

function Invoke-PythonFileVisible {
    param([string]$ScriptPath, [string[]]$Arguments)
    $python = Find-Python
    if (-not $python) {
        Show-Error "Python was not found. Run 'Setup / Verify Research Tools' first."
        return $false
    }
    if (-not (Test-Path -LiteralPath $ScriptPath -PathType Leaf)) {
        Show-Error "Research script is missing:`r`n$ScriptPath"
        return $false
    }
    $quoted = @('"' + $ScriptPath + '"')
    foreach ($arg in $Arguments) { $quoted += ('"' + $arg.Replace('"','\"') + '"') }
    $command = '& "' + $python + '" ' + ($quoted -join ' ')
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command + '; Write-Host ""; Read-Host "Press Enter to close"'))
    Start-Process powershell.exe -ArgumentList @("-NoProfile", "-EncodedCommand", $encoded)
    return $true
}

function Invoke-CreatorPythonVisible {
    param([string]$RelativeScript, [string[]]$Arguments)
    return Invoke-PythonFileVisible (Join-Path $repoRoot $RelativeScript) $Arguments
}

function Default-EvidenceRoot {
    $candidate = Join-Path $CreatorRoot "BarrosAI\evidence\jpeg-research"
    if (Test-Path -LiteralPath $CreatorRoot -PathType Container) {
        New-Item -ItemType Directory -Force -Path $candidate | Out-Null
        return $candidate
    }
    $candidate = Join-Path $repoRoot "evidence\jpeg-research"
    New-Item -ItemType Directory -Force -Path $candidate | Out-Null
    return $candidate
}

$evidenceRoot = Default-EvidenceRoot

$form = New-Object System.Windows.Forms.Form
$form.Text = "PC3 Pizza Creator — Native JPEG Research Lab"
$form.StartPosition = "CenterScreen"
$form.Size = New-Object System.Drawing.Size(760, 650)
$form.MinimumSize = New-Object System.Drawing.Size(760, 650)
$form.BackColor = [System.Drawing.Color]::FromArgb(38, 38, 42)
$form.ForeColor = [System.Drawing.Color]::WhiteSmoke
$form.Font = New-Object System.Drawing.Font("Segoe UI", 10)

$title = New-Object System.Windows.Forms.Label
$title.Text = "PC3 Native Pizza JPEG / Placement Research"
$title.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 17)
$title.AutoSize = $true
$title.Location = New-Object System.Drawing.Point(24, 20)
$form.Controls.Add($title)

$subtitle = New-Object System.Windows.Forms.Label
$subtitle.Text = "Creator executor + Studio canonical stimuli/observer • creator-0.11.272"
$subtitle.AutoSize = $true
$subtitle.ForeColor = [System.Drawing.Color]::Silver
$subtitle.Location = New-Object System.Drawing.Point(27, 58)
$form.Controls.Add($subtitle)

$scope = New-Object System.Windows.Forms.Label
$scope.Text = "Ownership remains strict: this Creator lab may read/run Studio's canonical stimulus generator, but never edits Studio/Workbench. Runtime PASS still requires retained contract evidence."
$scope.Size = New-Object System.Drawing.Size(690, 48)
$scope.Location = New-Object System.Drawing.Point(27, 88)
$scope.ForeColor = [System.Drawing.Color]::FromArgb(235, 190, 120)
$form.Controls.Add($scope)

function Add-Button {
    param([string]$Text, [int]$X, [int]$Y, [scriptblock]$Action, [string]$Tip)
    $button = New-Object System.Windows.Forms.Button
    $button.Text = $Text
    $button.Size = New-Object System.Drawing.Size(330, 52)
    $button.Location = New-Object System.Drawing.Point($X, $Y)
    $button.FlatStyle = "Flat"
    $button.BackColor = [System.Drawing.Color]::FromArgb(62, 62, 68)
    $button.ForeColor = [System.Drawing.Color]::WhiteSmoke
    $button.Add_Click($Action)
    $toolTip = New-Object System.Windows.Forms.ToolTip
    $toolTip.SetToolTip($button, $Tip)
    $form.Controls.Add($button)
}

Add-Button "1. Setup / Verify Research Tools" 28 145 {
    try {
        $script = Join-Path $repoRoot "scripts\Setup-JpegResearchTools.ps1"
        Start-Process powershell.exe -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ('"' + $script + '"'), "-PromptOptional")
    } catch { Show-Error $_.Exception.Message }
} "Downloads pinned official tools, verifies SHA-256, and creates the isolated analysis environment."

Add-Button "2. Trace Decompiled Save → JPEG Source" 390 145 {
    try {
        $source = Select-Folder "Select the exact Creator 0.11.272 decompiled C# root"
        if (-not $source) { return }
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $out = Join-Path $evidenceRoot ("static-trace-" + $stamp)
        Invoke-CreatorPythonVisible "scripts\trace_native_jpeg_source.py" @($source, "--out", $out) | Out-Null
    } catch { Show-Error $_.Exception.Message }
} "Ranks save/render/readback/JPEG/file-write methods and probable caller references."

Add-Button "3. Generate Canonical Studio Stimuli" 28 215 {
    try {
        $studio = Find-StudioRoot
        if (-not $studio) {
            $studio = Select-Folder "Select the READ-ONLY Runtime Proof Studio repository root containing scripts\generate_creator_controlled_stimuli.py"
        }
        if (-not $studio) { return }
        $generator = Join-Path $studio "scripts\generate_creator_controlled_stimuli.py"
        if (-not (Test-Path -LiteralPath $generator -PathType Leaf)) {
            Show-Error "The selected folder is not the expected Studio repository; canonical generator not found.`r`n$generator"
            return
        }
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $out = Join-Path $evidenceRoot ("canonical-stimuli-" + $stamp)
        Invoke-PythonFileVisible $generator @("--output-root", $out) | Out-Null
    } catch { Show-Error $_.Exception.Message }
} "Runs Studio's canonical E00-E10 generator read-only. Creator does not own or modify that generator."

Add-Button "4. Analyze Native JPEG Pair" 390 215 {
    try {
        $script = Join-Path $repoRoot "scripts\Analyze-NativeJpegPair.ps1"
        Start-Process powershell.exe -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ('"' + $script + '"'))
    } catch { Show-Error $_.Exception.Message }
} "Hashes/parses/compares two stock/native JPEGs and optional model signatures."

Add-Button "5. Fingerprint JPEG Encoder Structure" 28 285 {
    try {
        $jpeg = Select-File "Select native Pizza Creator JPEG" "JPEG (*.jpg;*.jpeg)|*.jpg;*.jpeg|All files (*.*)|*.*"
        if (-not $jpeg) { return }
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $outDir = Join-Path $evidenceRoot ("encoder-fingerprint-" + $stamp)
        New-Item -ItemType Directory -Force -Path $outDir | Out-Null
        $out = Join-Path $outDir "jpeg-encoder-fingerprint.json"
        Invoke-CreatorPythonVisible "scripts\fingerprint_jpeg_encoder.py" @($jpeg, "--out", $out) | Out-Null
    } catch { Show-Error $_.Exception.Message }
} "DQT/DHT/SOF/APP fingerprint + exact IJG quality-family matching when applicable."

Add-Button "6. Fit World X/Z → JPEG Camera Map" 390 285 {
    try {
        $csv = Select-File "Select camera calibration CSV (label,x,z,u,v)" "CSV (*.csv)|*.csv|All files (*.*)|*.*"
        if (-not $csv) { return }
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $out = Join-Path $evidenceRoot ("camera-mapping-" + $stamp + ".json")
        Invoke-CreatorPythonVisible "scripts\fit_jpeg_camera_mapping.py" @($csv, "--out", $out) | Out-Null
    } catch { Show-Error $_.Exception.Message }
} "Fits affine and homography models with held-out residuals."

Add-Button "7. Fit Native Yaw → JPEG Orientation" 28 355 {
    try {
        $baseline = Select-File "Select minimal dough/background baseline JPEG" "JPEG (*.jpg;*.jpeg)|*.jpg;*.jpeg|All files (*.*)|*.*"
        if (-not $baseline) { return }
        $csv = Select-File "Select orientation CSV (label,yaw_degrees,image)" "CSV (*.csv)|*.csv|All files (*.*)|*.*" (Split-Path -Parent $baseline)
        if (-not $csv) { return }
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $out = Join-Path $evidenceRoot ("orientation-transfer-" + $stamp + ".json")
        Invoke-CreatorPythonVisible "scripts\fit_jpeg_orientation_transfer.py" @($baseline, $csv, "--out", $out) | Out-Null
    } catch { Show-Error $_.Exception.Message }
} "Uses difference masks + PCA to estimate image orientation and fit native yaw transfer."

Add-Button "8. Open Research Evidence Folder" 390 355 {
    try {
        New-Item -ItemType Directory -Force -Path $evidenceRoot | Out-Null
        Start-Process explorer.exe -ArgumentList ('"' + $evidenceRoot + '"')
    } catch { Show-Error $_.Exception.Message }
} "Opens the local retained JPEG research evidence root."

Add-Button "Open Research Roadmap / Papers Guide" 28 425 {
    try {
        Start-Process (Join-Path $repoRoot "docs\NATIVE_PIZZA_JPEG_REVERSE_ENGINEERING_ROADMAP.md")
    } catch { Show-Error $_.Exception.Message }
} "Opens the native JPEG reverse-engineering roadmap."

Add-Button "Open Exact Experiment Harness Spec" 390 425 {
    try {
        Start-Process (Join-Path $repoRoot "docs\NATIVE_JPEG_EXPERIMENT_HARNESS_SPEC.md")
    } catch { Show-Error $_.Exception.Message }
} "Opens Claude's implementation-ready exact-model stimulus executor specification."

$status = New-Object System.Windows.Forms.TextBox
$status.Multiline = $true
$status.ReadOnly = $true
$status.ScrollBars = "Vertical"
$status.BackColor = [System.Drawing.Color]::FromArgb(28, 28, 31)
$status.ForeColor = [System.Drawing.Color]::Gainsboro
$status.BorderStyle = "FixedSingle"
$status.Location = New-Object System.Drawing.Point(28, 500)
$status.Size = New-Object System.Drawing.Size(692, 82)
$status.Text = "Creator repo: $repoRoot`r`nCreator root: $CreatorRoot`r`nStudio read-only root: $(Find-StudioRoot)`r`nEvidence: $evidenceRoot`r`nPython: $(Find-Python)"
$form.Controls.Add($status)

[void]$form.ShowDialog()
