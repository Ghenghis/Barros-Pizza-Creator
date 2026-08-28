[CmdletBinding()]
param(
    [string]$Version = "1.0.0",
    [string]$SiteUrl = "https://creator.daveai.tech/",
    [string]$PrivateRoot = "C:\private\barros-mobile",
    [switch]$SkipToolchainDownload
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$toolRoot = Join-Path $repoRoot "work\mobile-toolchain"
$sdkRoot = Join-Path $toolRoot "android-sdk"
$gradleRoot = Join-Path $toolRoot "gradle-8.9"
$outputRoot = Join-Path $repoRoot "releases\mobile"
$androidRoot = Join-Path $repoRoot "android"
$cmdZip = Join-Path $toolRoot "commandlinetools-win-15859902_latest.zip"
$gradleZip = Join-Path $toolRoot "gradle-8.9-bin.zip"
$signingPath = Join-Path $PrivateRoot "barros-android-release.jks"
$signingSettings = Join-Path $PrivateRoot "signing.json"

New-Item -ItemType Directory -Force -Path $toolRoot, $sdkRoot, $outputRoot, $PrivateRoot | Out-Null

function Get-VerifiedDownload([string]$Uri, [string]$Path, [string]$Sha256) {
    if ((Test-Path -LiteralPath $Path) -and $Sha256) {
        $existing = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($existing -ne $Sha256.ToLowerInvariant()) {
            $partial = $Path + ".partial-" + [DateTime]::UtcNow.ToString("yyyyMMddHHmmss")
            Move-Item -LiteralPath $Path -Destination $partial
        }
    }
    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Host "Downloading $([IO.Path]::GetFileName($Path))..."
        Invoke-WebRequest -Uri $Uri -OutFile $Path -UseBasicParsing
    }
    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Sha256 -and $actual -ne $Sha256.ToLowerInvariant()) {
        throw "Checksum mismatch for $Path"
    }
}

if (-not $SkipToolchainDownload) {
    Get-VerifiedDownload `
        "https://dl.google.com/android/repository/commandlinetools-win-15859902_latest.zip" `
        $cmdZip `
        "90ae805d20434428bffcb699c290860f19bb5f66a67e6b330067e3de801fb04a"
    Get-VerifiedDownload "https://services.gradle.org/distributions/gradle-8.9-bin.zip" $gradleZip ""
}

$sdkManager = Join-Path $sdkRoot "cmdline-tools\latest\bin\sdkmanager.bat"
if (-not (Test-Path -LiteralPath $sdkManager)) {
    $extract = Join-Path $toolRoot "cmdline-extract"
    if (Test-Path -LiteralPath $extract) { Remove-Item -LiteralPath $extract -Recurse -Force }
    Expand-Archive -LiteralPath $cmdZip -DestinationPath $extract -Force
    $latest = Join-Path $sdkRoot "cmdline-tools\latest"
    New-Item -ItemType Directory -Force -Path (Split-Path $latest) | Out-Null
    if (Test-Path -LiteralPath $latest) { Remove-Item -LiteralPath $latest -Recurse -Force }
    Move-Item -LiteralPath (Join-Path $extract "cmdline-tools") -Destination $latest
}

if (-not (Test-Path -LiteralPath (Join-Path $gradleRoot "bin\gradle.bat"))) {
    Expand-Archive -LiteralPath $gradleZip -DestinationPath $toolRoot -Force
}

$env:ANDROID_HOME = $sdkRoot
$env:ANDROID_SDK_ROOT = $sdkRoot
$licenseInput = (1..40 | ForEach-Object { "y" }) -join "`n"
$licenseInput | & $sdkManager --sdk_root=$sdkRoot --licenses | Out-Null
& $sdkManager --sdk_root=$sdkRoot "platforms;android-35" "build-tools;35.0.0" "platform-tools"
if ($LASTEXITCODE -ne 0) { throw "Android SDK installation failed." }

if (-not (Test-Path -LiteralPath $signingSettings)) {
    $bytes = New-Object byte[] 36
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $password = [Convert]::ToBase64String($bytes).Replace("/", "A").Replace("+", "B").TrimEnd("=")
    @{ alias = "barros-mobile"; password = $password } | ConvertTo-Json | Set-Content -LiteralPath $signingSettings -Encoding utf8NoBOM
}
$signing = Get-Content -Raw -LiteralPath $signingSettings | ConvertFrom-Json
if (-not (Test-Path -LiteralPath $signingPath)) {
    & keytool -genkeypair -v -keystore $signingPath -storepass $signing.password -keypass $signing.password -alias $signing.alias -keyalg RSA -keysize 4096 -validity 10000 -dname "CN=Barros Pizza Creator Mobile, OU=DaveAI, O=Ghenghis, L=Casa Grande, ST=Arizona, C=US"
    if ($LASTEXITCODE -ne 0) { throw "Android signing key creation failed." }
}

$env:BARROS_ANDROID_KEYSTORE = $signingPath
$env:BARROS_ANDROID_KEYSTORE_PASSWORD = $signing.password
$env:BARROS_ANDROID_KEY_ALIAS = $signing.alias
$sdkEscaped = $sdkRoot.Replace("\", "\\")
"sdk.dir=$sdkEscaped" | Set-Content -LiteralPath (Join-Path $androidRoot "local.properties") -Encoding ascii

$gradle = Join-Path $gradleRoot "bin\gradle.bat"
& $gradle -p $androidRoot clean assembleRelease bundleRelease --no-daemon
if ($LASTEXITCODE -ne 0) { throw "Android release build failed." }

$apkSource = Join-Path $androidRoot "app\build\outputs\apk\release\app-release.apk"
$aabSource = Join-Path $androidRoot "app\build\outputs\bundle\release\app-release.aab"
$apkTarget = Join-Path $outputRoot "Barros_Pizza_Creator_Mobile_v$Version.apk"
$aabTarget = Join-Path $outputRoot "Barros_Pizza_Creator_Mobile_v$Version.aab"
Copy-Item -LiteralPath $apkSource -Destination $apkTarget -Force
Copy-Item -LiteralPath $aabSource -Destination $aabTarget -Force

$certificate = (& keytool -list -v -keystore $signingPath -storepass $signing.password -alias $signing.alias | Select-String "SHA256:").ToString().Split("SHA256:", 2)[1].Trim()
$assetLinksPath = Join-Path $repoRoot "web\.well-known\assetlinks.json"
$assetLinks = @(@{ relation = @("delegate_permission/common.handle_all_urls"); target = @{ namespace = "android_app"; package_name = "tech.daveai.barroscreator"; sha256_cert_fingerprints = @($certificate) } })
ConvertTo-Json -InputObject $assetLinks -Depth 6 | Set-Content -LiteralPath $assetLinksPath -Encoding utf8NoBOM

$staging = Join-Path $repoRoot "work\mobile-release-staging"
if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
New-Item -ItemType Directory -Path $staging | Out-Null
foreach ($name in @("backend", "contracts", "deploy", "web", "bridge")) {
    Copy-Item -LiteralPath (Join-Path $repoRoot $name) -Destination (Join-Path $staging $name) -Recurse
}
Copy-Item -LiteralPath (Join-Path $repoRoot "README.md") -Destination $staging
Copy-Item -LiteralPath (Join-Path $repoRoot "docs\MOBILE_VPS_RELEASE.md") -Destination $staging -ErrorAction SilentlyContinue

$serverZip = Join-Path $outputRoot "Barros_Creator_Hostinger_Server_v$Version.zip"
$bridgeZip = Join-Path $outputRoot "Barros_Creator_Windows_Bridge_v$Version.zip"
if (Test-Path -LiteralPath $serverZip) { Remove-Item -LiteralPath $serverZip -Force }
if (Test-Path -LiteralPath $bridgeZip) { Remove-Item -LiteralPath $bridgeZip -Force }
Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $serverZip -CompressionLevel Optimal
Compress-Archive -Path (Join-Path $repoRoot "bridge\*") -DestinationPath $bridgeZip -CompressionLevel Optimal

$records = @($apkTarget, $aabTarget, $serverZip, $bridgeZip) | ForEach-Object {
    $item = Get-Item -LiteralPath $_
    [ordered]@{ file = $item.Name; bytes = $item.Length; sha256 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
}
$records | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $outputRoot "release-manifest.json") -Encoding utf8NoBOM
$records | ForEach-Object { "$($_.sha256)  $($_.file)" } | Set-Content -LiteralPath (Join-Path $outputRoot "SHA256SUMS.txt") -Encoding ascii
Write-Host "Mobile release complete: $outputRoot"
