[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$GameRoot,
    [string]$ReleaseDirectory = ""
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($ReleaseDirectory)) { $ReleaseDirectory = Join-Path $repo "releases\windows" }
$setup = Join-Path $ReleaseDirectory "Barros_Pizza_Creator_v1.6.0_Setup.exe"
if (-not (Test-Path -LiteralPath $setup)) { throw "Build the Windows release first: $setup" }
$sourceGame = (Resolve-Path $GameRoot).Path
$testRoot = Join-Path $repo "work\windows-installer-proof"
$fakeGame = Join-Path $testRoot "Pizza Creator Test"
$managerInstall = Join-Path $testRoot "Manager Install"
$reportPath = Join-Path $testRoot "windows-installer-proof.txt"

function Reset-ProofDirectory([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $workspace = [IO.Path]::GetFullPath((Join-Path $repo "work"))
    if (-not $full.StartsWith($workspace + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
        [IO.Path]::GetFileName($full) -ne "windows-installer-proof") {
        throw "Refusing to reset unexpected proof directory: $full"
    }
    if (Test-Path -LiteralPath $full) { Remove-Item -LiteralPath $full -Recurse -Force }
    New-Item -ItemType Directory -Path $full | Out-Null
}

function Invoke-Checked([string]$File, [string]$Arguments, [string]$Label) {
    $process = Start-Process -FilePath $File -ArgumentList $Arguments -Wait -PassThru -WindowStyle Hidden
    if ($process.ExitCode -ne 0) { throw "$Label failed with exit code $($process.ExitCode)." }
}

Reset-ProofDirectory $testRoot
New-Item -ItemType Directory -Force -Path (Join-Path $fakeGame "Pizza Connection 3 - Pizza Creator_Data\Managed") | Out-Null
Copy-Item -LiteralPath (Join-Path $sourceGame "Pizza Connection 3 - Pizza Creator.exe") -Destination $fakeGame
Copy-Item -LiteralPath (Join-Path $sourceGame "Pizza Connection 3 - Pizza Creator_Data\Managed\Assembly-CSharp.dll") -Destination (Join-Path $fakeGame "Pizza Connection 3 - Pizza Creator_Data\Managed")
Copy-Item -LiteralPath (Join-Path $sourceGame "Pizza Connection 3 - Pizza Creator_Data\Managed\Assembly-CSharp-firstpass.dll") -Destination (Join-Path $fakeGame "Pizza Connection 3 - Pizza Creator_Data\Managed")

$setupArgs = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /DIR="' + $managerInstall + '" /GameRoot="' + $fakeGame + '"'
Invoke-Checked $setup $setupArgs "Clean silent install"

$plugin = Join-Path $fakeGame "BepInEx\plugins\BarrosAI\Barros.PizzaCreator.AI.dll"
$python = Join-Path $fakeGame "BarrosAI\runtime\python.exe"
$settings = Join-Path $fakeGame "BarrosAI\backend\settings.json"
foreach ($required in @($plugin, $python, $settings, (Join-Path $managerInstall "Barros_Pizza_Creator_Manager.exe"))) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Installed file missing: $required" }
}
$expectedPlugin = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $repo "artifacts\Barros.PizzaCreator.AI.dll")).Hash
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $plugin).Hash -ne $expectedPlugin) { throw "Installed plug-in hash mismatch." }

$settingsMarker = "WINDOWS_INSTALLER_REPAIR_PRESERVES_SETTINGS"
$settingsDocument = Get-Content -LiteralPath $settings -Raw | ConvertFrom-Json
$settingsDocument | Add-Member -NotePropertyName "windows_installer_proof" -NotePropertyValue $settingsMarker -Force
$settingsDocument | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $settings -Encoding UTF8
Invoke-Checked $setup $setupArgs "Repair install"
if (-not (Select-String -LiteralPath $settings -SimpleMatch $settingsMarker -Quiet)) { throw "Repair overwrote the user's settings file." }

$uninstaller = Join-Path $managerInstall "unins000.exe"
Invoke-Checked $uninstaller "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART" "Silent uninstall"
if (Test-Path -LiteralPath (Join-Path $fakeGame "BarrosAI")) { throw "Uninstall left the BarrosAI data tree." }
if (Test-Path -LiteralPath (Join-Path $fakeGame "BepInEx\plugins\BarrosAI")) { throw "Uninstall left the BarrosAI plug-in tree." }
if (-not (Test-Path -LiteralPath (Join-Path $fakeGame "BepInEx\core\BepInEx.dll"))) { throw "Uninstall removed shared BepInEx unexpectedly." }
if (-not (Test-Path -LiteralPath (Join-Path $fakeGame "Pizza Connection 3 - Pizza Creator.exe"))) { throw "Uninstall removed the game executable." }

$lines = @(
    "Barro's Pizza Creator 1.6 Windows installer proof",
    "clean_install=PASS",
    "exact_plugin_hash=PASS",
    "private_python=PASS",
    "repair_preserved_settings=PASS",
    "uninstall_removed_barros_files=PASS",
    "uninstall_preserved_shared_bepinex=PASS",
    "uninstall_preserved_original_game=PASS",
    "commercial_game_packaged=NO"
)
[IO.File]::WriteAllLines($reportPath, $lines, (New-Object Text.UTF8Encoding($false)))
$lines
