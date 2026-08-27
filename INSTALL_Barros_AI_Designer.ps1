[CmdletBinding()]
param(
    [string]$GameRoot = "S:\Unity_Games\PC3 - Pizza Creator",
    [string]$BepInExArchive = "",
    [string]$PythonArchive = "",
    [switch]$ForceLocalCompile,
    [switch]$NoGui
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$packageRoot = $PSScriptRoot
$version = "1.6.0"
$bepVersion = "5.4.23.5"
$bepUrl = "https://github.com/BepInEx/BepInEx/releases/download/v5.4.23.5/BepInEx_win_x64_5.4.23.5.zip"
$bepSha = "82F9878551030F54657792C0740D9D51A09500EEAE1FBA21106B0C441E6732C4"
$pythonUrl = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip"
$pythonSha = "4ACBED6DD1C744B0376E3B1CF57CE906F9DC9E95E68824584C8099A63025A3C3"
$assemblySha = "EBF8698DF7CB4AF904C98C299994705EA529EFBDf1E8CCB3E7CA8CB42A1CBC1C"
$firstpassSha = "F9CBF0951FC4D4B0788C47BBE41A3820FA333D293175BBB7CB398EB4728FD284"

function Get-Sha256([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    try {
        $hash = [Security.Cryptography.SHA256]::Create()
        try {
            return ([BitConverter]::ToString($hash.ComputeHash($stream))).Replace("-", "")
        }
        finally {
            $hash.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}

function Select-GameRoot([string]$initial) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = "Select the folder containing Pizza Connection 3 - Pizza Creator.exe"
    $dialog.ShowNewFolderButton = $false
    if (Test-Path $initial) { $dialog.SelectedPath = $initial }
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw "Installation cancelled." }
    return $dialog.SelectedPath
}

function Get-VerifiedArchive([string]$provided, [string]$url, [string]$sha, [string]$label) {
    $path = $provided
    if ([string]::IsNullOrWhiteSpace($path)) {
        $path = Join-Path ([IO.Path]::GetTempPath()) ([IO.Path]::GetFileName($url))
        if (-not (Test-Path $path) -or (Get-Sha256 $path) -ne $sha) {
            Write-Host "Downloading $label from its official release..."
            Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $path
        }
    }
    if (-not (Test-Path $path)) { throw "$label archive not found: $path" }
    $actual = Get-Sha256 $path
    if ($actual -ne $sha) { throw "$label SHA-256 mismatch. Expected $sha but received $actual." }
    return (Resolve-Path $path).Path
}

try {
    $exeName = "Pizza Connection 3 - Pizza Creator.exe"
    if (-not (Test-Path (Join-Path $GameRoot $exeName))) {
        if ($NoGui) { throw "Game executable not found under $GameRoot" }
        $GameRoot = Select-GameRoot $GameRoot
    }
    $GameRoot = (Resolve-Path $GameRoot).Path
    $gameExe = Join-Path $GameRoot $exeName
    $managed = Join-Path $GameRoot "Pizza Connection 3 - Pizza Creator_Data\Managed"
    $assembly = Join-Path $managed "Assembly-CSharp.dll"
    $firstpass = Join-Path $managed "Assembly-CSharp-firstpass.dll"
    if (-not (Test-Path $gameExe) -or -not (Test-Path $assembly) -or -not (Test-Path $firstpass)) {
        throw "This is not the complete standalone Pizza Creator folder. Expected $gameExe, $assembly and $firstpass"
    }
    $targetExePath = [IO.Path]::GetFullPath($gameExe)
    $running = Get-CimInstance Win32_Process -Filter ("Name='" + $exeName.Replace("'", "''") + "'") -ErrorAction SilentlyContinue |
        Where-Object {
            -not [string]::IsNullOrWhiteSpace($_.ExecutablePath) -and
            [string]::Equals([IO.Path]::GetFullPath($_.ExecutablePath), $targetExePath, [StringComparison]::OrdinalIgnoreCase)
        }
    if ($running) { throw "Close the target Pizza Connection 3 - Pizza Creator copy before installing: $targetExePath" }

    $actualAssemblySha = Get-Sha256 $assembly
    $actualFirstpassSha = Get-Sha256 $firstpass
    Write-Host "Target: $GameRoot"
    Write-Host "Game Assembly-CSharp SHA256: $actualAssemblySha"
    Write-Host "Game Assembly-CSharp-firstpass SHA256: $actualFirstpassSha"
    if ($actualAssemblySha -ne $assemblySha -or $actualFirstpassSha -ne $firstpassSha) {
        throw "Unsupported game build. Creator 1.6 is locked to Pizza Creator 0.11.272. No game or plugin files were changed. Run RUN_RC1_PROOF.bat and retain its assembly-hashes.json for adapter review."
    }
    $core = Join-Path $GameRoot "BepInEx\core\BepInEx.dll"
    if (Test-Path $core) {
        $installedVersion = [Reflection.AssemblyName]::GetAssemblyName($core).Version
        if ($installedVersion.Major -ne 5) { throw "An incompatible BepInEx $installedVersion is installed. This Unity 2017 plugin requires BepInEx 5 x64." }
        Write-Host "Using existing BepInEx $installedVersion."
    }
    else {
        $archive = Get-VerifiedArchive $BepInExArchive $bepUrl $bepSha "BepInEx $bepVersion x64"
        Write-Host "Installing the verified BepInEx 5 x64 loader..."
        Expand-Archive -LiteralPath $archive -DestinationPath $GameRoot -Force
        if (-not (Test-Path $core)) { throw "BepInEx extraction did not create $core" }
    }

    $installRoot = Join-Path $GameRoot "BarrosAI"
    $backendTarget = Join-Path $installRoot "backend"
    $assetsTarget = Join-Path $installRoot "assets"
    $contractsTarget = Join-Path $installRoot "contracts"
    $runtimeTarget = Join-Path $installRoot "runtime"
    $pluginTarget = Join-Path $GameRoot "BepInEx\plugins\BarrosAI"
    New-Item -ItemType Directory -Force -Path $backendTarget, $assetsTarget, $contractsTarget, $runtimeTarget, $pluginTarget | Out-Null
    Copy-Item -Path (Join-Path $packageRoot "backend\*") -Destination $backendTarget -Recurse -Force
    Copy-Item -Path (Join-Path $packageRoot "assets\*") -Destination $assetsTarget -Recurse -Force
    Copy-Item -Path (Join-Path $packageRoot "contracts\*") -Destination $contractsTarget -Recurse -Force
    if (-not (Test-Path (Join-Path $backendTarget "settings.json"))) {
        Copy-Item -LiteralPath (Join-Path $packageRoot "backend\settings.example.json") -Destination (Join-Path $backendTarget "settings.json")
    }

    $pythonExe = Join-Path $runtimeTarget "python.exe"
    if (-not (Test-Path $pythonExe)) {
        $archive = Get-VerifiedArchive $PythonArchive $pythonUrl $pythonSha "Python 3.12.10 embedded x64"
        Write-Host "Installing the verified private Python runtime (no system PATH changes)..."
        Expand-Archive -LiteralPath $archive -DestinationPath $runtimeTarget -Force
    }
    $pth = Join-Path $runtimeTarget "python312._pth"
    if (Test-Path $pth) {
        $lines = New-Object Collections.Generic.List[string]
        $existingLines = @(Get-Content -LiteralPath $pth)
        foreach ($line in $existingLines) { $lines.Add([string]$line) }
        if (-not ($lines -contains "..\backend")) { $lines.Insert(0, "..\backend") }
        $utf8NoBom = New-Object Text.UTF8Encoding($false)
        [IO.File]::WriteAllLines($pth, $lines, $utf8NoBom)
    }
    & $pythonExe -c "import barros_ai; print('Backend import OK')"
    if ($LASTEXITCODE -ne 0) { throw "The bundled Python backend failed its import test." }

    $artifact = Join-Path $packageRoot "artifacts\Barros.PizzaCreator.AI.dll"
    $provenancePath = Join-Path $packageRoot "artifacts\build-provenance.json"
    $buildMode = "certified-prebuilt"
    $prebuiltValid = $false
    if ((Test-Path $artifact) -and (Test-Path $provenancePath)) {
        $provenance = Get-Content -LiteralPath $provenancePath -Raw | ConvertFrom-Json
        $prebuiltValid = ((Get-Sha256 $artifact) -eq ([string]$provenance.artifact_sha256).ToUpperInvariant()) -and
            ($actualAssemblySha -eq ([string]$provenance.target.assembly_csharp_sha256).ToUpperInvariant()) -and
            ($actualFirstpassSha -eq ([string]$provenance.target.assembly_csharp_firstpass_sha256).ToUpperInvariant())
    }
    if ($ForceLocalCompile -or -not $prebuiltValid) {
        $buildMode = "local-windows-compile"
        $artifact = Join-Path $packageRoot "artifacts\Barros.PizzaCreator.AI.local.dll"
        & (Join-Path $packageRoot "scripts\Build-Plugin.ps1") -GameRoot $GameRoot -PackageRoot $packageRoot -OutputPath $artifact
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $artifact)) { throw "Plugin build failed." }
    }
    else {
        Write-Host "Using the SHA-256-certified plugin compiled against this exact game build."
    }
    Copy-Item -LiteralPath $artifact -Destination (Join-Path $pluginTarget "Barros.PizzaCreator.AI.dll") -Force
    Copy-Item -LiteralPath (Join-Path $packageRoot "VERSION.txt") -Destination (Join-Path $pluginTarget "VERSION.txt") -Force

    $manifest = [ordered]@{
        product = "Barro's AI Pizza Designer"
        version = $version
        installed_utc = [DateTime]::UtcNow.ToString("o")
        game_root = $GameRoot
        game_assembly_sha256 = $actualAssemblySha
        game_firstpass_sha256 = $actualFirstpassSha
        plugin_sha256 = Get-Sha256 (Join-Path $pluginTarget "Barros.PizzaCreator.AI.dll")
        plugin_build_mode = $buildMode
        loader = "BepInEx $bepVersion x64"
        backend = "Python 3.12.10 embedded; stdlib only"
    }
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $installRoot "install-manifest.json") -Encoding UTF8
    Copy-Item -LiteralPath (Join-Path $packageRoot "THIRD-PARTY-NOTICES.md") -Destination (Join-Path $installRoot "THIRD-PARTY-NOTICES.md") -Force

    $message = @"
Barro's AI Pizza Designer $version is installed.

Launch Pizza Connection 3 - Pizza Creator normally.
Open the Bakehouse and select the new chef-chat tab.
Press F10 at any time in the Creator to reopen it.

Offline design works immediately. Run CONFIGURE_AI_PROVIDER.bat for LM Studio, Ollama, OpenAI-compatible, or Anthropic mode and voice transcription.
"@
    Write-Host $message -ForegroundColor Green
    if (-not $NoGui) {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show($message, "Installation complete", "OK", "Information") | Out-Null
    }
}
catch {
    $message = "Installation failed:`r`n`r`n" + $_.Exception.Message
    Write-Error $message
    if (-not $NoGui) {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show($message, "Barro's AI Designer", "OK", "Error") | Out-Null
    }
    exit 1
}
