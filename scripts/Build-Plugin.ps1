[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$GameRoot,
    [string]$PackageRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
$managed = Join-Path $GameRoot "Pizza Connection 3 - Pizza Creator_Data\Managed"
$bepinex = Join-Path $GameRoot "BepInEx\core\BepInEx.dll"
$source = Join-Path $PackageRoot "plugin-src"
if (-not (Test-Path $managed)) { throw "Managed folder not found: $managed" }
if (-not (Test-Path $bepinex)) { throw "BepInEx.dll not found: $bepinex" }
if (-not (Test-Path $source)) { throw "Plugin source not found: $source" }
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $PackageRoot "artifacts\Barros.PizzaCreator.AI.dll"
}
$outputDirectory = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

$candidates = @(
    (Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"),
    (Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe")
)
$csc = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $csc) {
    $command = Get-Command csc.exe -ErrorAction SilentlyContinue
    if ($command) { $csc = $command.Source }
}
if (-not $csc) { throw "A C# compiler was not found. Install the .NET Framework 4 developer tools or a Visual Studio Build Tools workload." }

$references = @(
    $bepinex,
    (Join-Path $managed "Assembly-CSharp.dll"),
    (Join-Path $managed "Assembly-CSharp-firstpass.dll"),
    (Join-Path $managed "Newtonsoft.Json.dll"),
    (Join-Path $managed "Zenject.dll"),
    (Join-Path $managed "UnityEngine.dll"),
    (Join-Path $managed "UnityEngine.CoreModule.dll"),
    (Join-Path $managed "UnityEngine.IMGUIModule.dll"),
    (Join-Path $managed "UnityEngine.UI.dll"),
    (Join-Path $managed "UnityEngine.UIModule.dll"),
    (Join-Path $managed "UnityEngine.TextRenderingModule.dll"),
    (Join-Path $managed "UnityEngine.AudioModule.dll"),
    (Join-Path $managed "UnityEngine.InputModule.dll"),
    (Join-Path $managed "UnityEngine.ImageConversionModule.dll"),
    (Join-Path $managed "UnityEngine.ScreenCaptureModule.dll")
    (Join-Path $managed "UnityEngine.VideoModule.dll")
    (Join-Path $managed "UnityEngine.UnityWebRequestWWWModule.dll")
    (Join-Path $managed "UnityEngine.UnityWebRequestModule.dll")
    (Join-Path $managed "UnityEngine.UnityWebRequestAudioModule.dll")
)
foreach ($reference in $references) {
    if (-not (Test-Path $reference)) { throw "Required compile reference is missing: $reference" }
}
$sources = Get-ChildItem -Path $source -Filter "*.cs" -File | Sort-Object Name
if ($sources.Count -lt 5) { throw "Plugin source set is incomplete." }

$response = Join-Path ([IO.Path]::GetTempPath()) ("barros-ai-" + [Guid]::NewGuid().ToString("N") + ".rsp")
try {
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("/nologo")
    $lines.Add("/target:library")
    $lines.Add("/optimize+")
    $lines.Add("/debug:pdbonly")
    $lines.Add("/platform:anycpu")
    $lines.Add("/utf8output")
    $lines.Add("/codepage:65001")
    $lines.Add('/out:"' + $OutputPath + '"')
    foreach ($reference in $references) { $lines.Add('/reference:"' + $reference + '"') }
    foreach ($file in $sources) { $lines.Add('"' + $file.FullName + '"') }
    $utf8NoBom = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllLines($response, $lines, $utf8NoBom)
    & $csc "@$response"
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $OutputPath)) { throw "C# compilation failed with exit code $LASTEXITCODE." }
}
finally {
    Remove-Item -LiteralPath $response -Force -ErrorAction SilentlyContinue
}

$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $OutputPath).Hash
Write-Host "Built: $OutputPath"
Write-Host "SHA256: $hash"
