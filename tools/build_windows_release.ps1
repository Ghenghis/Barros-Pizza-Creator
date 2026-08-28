[CmdletBinding()]
param(
    [string]$OutputDirectory = "",
    [string]$BepInExArchive = (Join-Path $env:TEMP "BepInEx_win_x64_5.4.23.5.zip"),
    [string]$PythonArchive = (Join-Path $env:TEMP "python-3.12.10-embed-amd64.zip"),
    [string]$InnoCompiler = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $repo "releases\windows"
}
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
$workRoot = Join-Path ([IO.Path]::GetTempPath()) "barros-pizza-creator-v1.6.1-windows-build"
$portableName = "Barros_Pizza_Creator_v1.6.1_Portable"
$portableRoot = Join-Path $workRoot $portableName

function Reset-TempDirectory([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $temp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if (-not $full.StartsWith($temp, [StringComparison]::OrdinalIgnoreCase) -or
        [IO.Path]::GetFileName($full) -ne "barros-pizza-creator-v1.6.1-windows-build") {
        throw "Refusing to reset unexpected build directory: $full"
    }
    if (Test-Path -LiteralPath $full) { Remove-Item -LiteralPath $full -Recurse -Force }
    New-Item -ItemType Directory -Path $full | Out-Null
}

function Assert-Hash([string]$Path, [string]$Expected, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "$Label not found: $Path" }
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
    if ($actual -ne $Expected) { throw "$Label SHA-256 mismatch. Expected $Expected but received $actual" }
}

function Copy-RepoFile([string]$RelativePath) {
    $source = Join-Path $repo $RelativePath
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Required payload file missing: $RelativePath" }
    $destination = Join-Path $portableRoot $RelativePath
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Force
}

if (-not (Select-String -LiteralPath (Join-Path $repo "VERSION.txt") -SimpleMatch "Version: 1.6.1" -Quiet)) {
    throw "Windows 1.6 packaging must run from the proven v1.6 source tree."
}
Assert-Hash $BepInExArchive "82F9878551030F54657792C0740D9D51A09500EEAE1FBA21106B0C441E6732C4" "BepInEx 5.4.23.5 x64"
Assert-Hash $PythonArchive "4ACBED6DD1C744B0376E3B1CF57CE906F9DC9E95E68824584C8099A63025A3C3" "Python 3.12.10 embedded x64"
if ([string]::IsNullOrWhiteSpace($InnoCompiler)) {
    $innoCandidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 7\ISCC.exe"),
        (Join-Path $env:ProgramFiles "Inno Setup 7\ISCC.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 7\ISCC.exe")
    )
    $InnoCompiler = $innoCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not (Test-Path -LiteralPath $InnoCompiler -PathType Leaf)) { throw "Inno Setup compiler not found: $InnoCompiler" }

Reset-TempDirectory $workRoot
New-Item -ItemType Directory -Force -Path $portableRoot, $OutputDirectory | Out-Null

$runtimeRoots = @("backend", "assets", "contracts", "plugin-src", "artifacts")
$tracked = @(& git -C $repo ls-files -- $runtimeRoots "scripts/Build-Plugin.ps1") | Where-Object {
    # The installed Media Deck uses the normalized OGG copy. Do not package the
    # redundant same-song MP3 source copy beside it.
    $_ -notmatch '^assets/music/[^/]+\.mp3$'
}
if ($LASTEXITCODE -ne 0 -or $tracked.Count -lt 20) { throw "Could not enumerate the tracked runtime payload." }
foreach ($relative in $tracked) { Copy-RepoFile $relative }

$rootFiles = @(
    "INSTALL_Barros_AI_Designer.ps1",
    "UNINSTALL_Barros_AI_Designer.ps1",
    "CONFIGURE_AI_PROVIDER.ps1",
    "DIAGNOSE_Barros_AI.ps1",
    "VERSION.txt",
    "README.md",
    "THIRD-PARTY-NOTICES.md"
)
foreach ($relative in $rootFiles) { Copy-RepoFile $relative }
foreach ($relative in @("docs/UNITY_UI_AUTHORING_PIPELINE.md", "docs/V1_6_RUNTIME_PROOF_2026-08-27.md")) {
    Copy-RepoFile $relative
}

$dependencies = Join-Path $portableRoot "dependencies"
New-Item -ItemType Directory -Force -Path $dependencies | Out-Null
Copy-Item -LiteralPath $BepInExArchive -Destination (Join-Path $dependencies "BepInEx_win_x64_5.4.23.5.zip") -Force
Copy-Item -LiteralPath $PythonArchive -Destination (Join-Path $dependencies "python-3.12.10-embed-amd64.zip") -Force
Copy-Item -LiteralPath (Join-Path $repo "packaging\windows\INSTALL_OFFLINE.cmd") -Destination $portableRoot -Force
Copy-Item -LiteralPath (Join-Path $repo "packaging\windows\PORTABLE_README.txt") -Destination $portableRoot -Force

$dependencyLines = @(
    "82f9878551030f54657792c0740d9d51a09500eeae1fba21106b0c441e6732c4  dependencies/BepInEx_win_x64_5.4.23.5.zip",
    "4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3  dependencies/python-3.12.10-embed-amd64.zip"
)
[IO.File]::WriteAllLines((Join-Path $portableRoot "OFFLINE_DEPENDENCIES.sha256"), $dependencyLines, (New-Object Text.UTF8Encoding($false)))

$cscCandidates = @(
    (Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"),
    (Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe")
)
$csc = $cscCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $csc) { throw "The Windows .NET Framework compiler was not found." }
$manager = Join-Path $portableRoot "Barros_Pizza_Creator_Manager.exe"
& $csc /nologo /target:winexe /optimize+ /platform:anycpu /utf8output `
    /reference:System.dll /reference:System.Core.dll /reference:System.Drawing.dll /reference:System.Windows.Forms.dll `
    "/out:$manager" (Join-Path $repo "packaging\windows\BarrosCreatorManager.cs")
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $manager)) { throw "Windows manager compilation failed." }

$forbidden = Get-ChildItem -LiteralPath $portableRoot -Recurse -File | Where-Object {
    $_.Name -eq "Pizza Connection 3 - Pizza Creator.exe" -or
    $_.FullName -match "Pizza Connection 3 - Pizza Creator_Data"
}
if ($forbidden) { throw "Commercial game files entered the payload; build refused." }

$portableZip = Join-Path $OutputDirectory ($portableName + ".zip")
if (Test-Path -LiteralPath $portableZip) { Remove-Item -LiteralPath $portableZip -Force }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($portableRoot, $portableZip, [IO.Compression.CompressionLevel]::Optimal, $true)

& $InnoCompiler "/DStageDir=$portableRoot" "/DOutputDir=$OutputDirectory" (Join-Path $repo "packaging\windows\BarrosCreator.iss")
if ($LASTEXITCODE -ne 0) { throw "Inno Setup compilation failed with exit code $LASTEXITCODE." }
$setupExe = Join-Path $OutputDirectory "Barros_Pizza_Creator_v1.6.1_Setup.exe"
if (-not (Test-Path -LiteralPath $setupExe)) { throw "Expected Setup EXE was not produced." }

$outputs = @($setupExe, $portableZip)
$checksumLines = foreach ($file in $outputs) {
    "{0}  {1}" -f (Get-FileHash -Algorithm SHA256 -LiteralPath $file).Hash.ToLowerInvariant(), [IO.Path]::GetFileName($file)
}
$checksumPath = Join-Path $OutputDirectory "Barros_Pizza_Creator_v1.6.1_WINDOWS_SHA256.txt"
[IO.File]::WriteAllLines($checksumPath, $checksumLines, (New-Object Text.UTF8Encoding($false)))

$report = [ordered]@{
    product = "Barro's Pizza Creator"
    version = "1.6.1"
    built_utc = [DateTime]::UtcNow.ToString("o")
    commercial_game_included = $false
    manager_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $manager).Hash.ToLowerInvariant()
    setup = [ordered]@{ path = $setupExe; bytes = (Get-Item $setupExe).Length; sha256 = (Get-FileHash -Algorithm SHA256 $setupExe).Hash.ToLowerInvariant() }
    portable = [ordered]@{ path = $portableZip; bytes = (Get-Item $portableZip).Length; sha256 = (Get-FileHash -Algorithm SHA256 $portableZip).Hash.ToLowerInvariant() }
}
$report | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $OutputDirectory "windows-release-build.json") -Encoding UTF8
$report | ConvertTo-Json -Depth 4
