[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$SourceDirectory = "S:\Unity_Games\PC3 - Pizza Creator\Barros_Music",
    [string]$OutputDirectory = "",
    [string]$FfmpegPath = "",
    [ValidateRange(-1.0, 10.0)]
    [double]$Quality = 5.0,
    [ValidateSet(32000, 44100, 48000)]
    [int]$SampleRate = 44100,
    [ValidateSet(1, 2)]
    [int]$Channels = 2,
    [switch]$Overwrite,
    [switch]$IncludeExistingOgg
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-FfmpegExecutable {
    param([string]$RequestedPath)

    if (-not [string]::IsNullOrWhiteSpace($RequestedPath)) {
        if (-not (Test-Path -LiteralPath $RequestedPath -PathType Leaf)) {
            throw "FFmpeg was not found at '$RequestedPath'."
        }
        return (Resolve-Path -LiteralPath $RequestedPath).Path
    }

    $command = Get-Command "ffmpeg.exe" -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        $command = Get-Command "ffmpeg" -ErrorAction SilentlyContinue
    }
    if ($null -eq $command) {
        throw "FFmpeg is required. Install an official Windows build, add ffmpeg.exe to PATH, or pass -FfmpegPath."
    }
    return $command.Source
}

function Get-Sha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

if (-not (Test-Path -LiteralPath $SourceDirectory -PathType Container)) {
    throw "Music source directory not found: $SourceDirectory"
}

$sourceRoot = (Resolve-Path -LiteralPath $SourceDirectory).Path.TrimEnd('\', '/')
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $sourceRoot "converted-ogg"
}
$outputRoot = [System.IO.Path]::GetFullPath($OutputDirectory).TrimEnd('\', '/')

if ([string]::Equals($sourceRoot, $outputRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "The output directory must differ from the source directory."
}

$ffmpeg = Resolve-FfmpegExecutable $FfmpegPath
$encoderText = (& $ffmpeg -hide_banner -encoders 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0 -or $encoderText -notmatch "(?m)^\s*A.*\blibvorbis\b") {
    throw "This FFmpeg build does not expose the libvorbis encoder. Use a build configured with --enable-libvorbis."
}
$ffmpegVersion = ((& $ffmpeg -version 2>&1 | Select-Object -First 1) -join "").Trim()

$extensions = @(".wav", ".mp3", ".flac", ".m4a", ".aac", ".wma", ".aiff", ".aif", ".opus", ".oga")
if ($IncludeExistingOgg) {
    $extensions += ".ogg"
}

$outputPrefix = $outputRoot + [System.IO.Path]::DirectorySeparatorChar
$inputs = @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File | Where-Object {
    $extensions -contains $_.Extension.ToLowerInvariant() -and
    -not $_.FullName.StartsWith($outputPrefix, [System.StringComparison]::OrdinalIgnoreCase)
} | Sort-Object FullName)

if ($inputs.Count -eq 0) {
    throw "No supported audio files were found under '$sourceRoot'."
}

New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null
$records = New-Object System.Collections.Generic.List[object]
$converted = 0
$skipped = 0
$failed = 0

foreach ($input in $inputs) {
    $relative = $input.FullName.Substring($sourceRoot.Length).TrimStart('\', '/')
    $relativeOgg = [System.IO.Path]::ChangeExtension($relative, ".ogg")
    $destination = Join-Path $outputRoot $relativeOgg
    $destinationDirectory = Split-Path -Parent $destination

    if ((Test-Path -LiteralPath $destination -PathType Leaf) -and -not $Overwrite) {
        $records.Add([ordered]@{
            source = $relative
            source_sha256 = Get-Sha256 $input.FullName
            output = $relativeOgg
            output_sha256 = Get-Sha256 $destination
            state = "skipped_existing"
            detail = "Use -Overwrite to regenerate this file."
        })
        $skipped += 1
        continue
    }

    if (-not $PSCmdlet.ShouldProcess($input.FullName, "Convert to $destination")) {
        $records.Add([ordered]@{
            source = $relative
            source_sha256 = Get-Sha256 $input.FullName
            output = $relativeOgg
            output_sha256 = $null
            state = "what_if"
            detail = "Conversion was not executed."
        })
        continue
    }

    New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
    $temporary = "$destination.$([Guid]::NewGuid().ToString('N')).partial.ogg"
    try {
        $arguments = @(
            "-hide_banner", "-nostdin", "-v", "error", "-y",
            "-i", $input.FullName,
            "-map", "0:a:0", "-vn", "-map_metadata", "0",
            "-c:a", "libvorbis", "-q:a", $Quality.ToString([System.Globalization.CultureInfo]::InvariantCulture),
            "-ar", $SampleRate.ToString(), "-ac", $Channels.ToString(),
            $temporary
        )
        $encodeText = (& $ffmpeg @arguments 2>&1 | Out-String).Trim()
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $temporary -PathType Leaf)) {
            throw "FFmpeg encode failed with exit code $LASTEXITCODE. $encodeText"
        }

        $validationText = (& $ffmpeg -hide_banner -nostdin -v error -i $temporary -map 0:a:0 -f null - 2>&1 | Out-String).Trim()
        if ($LASTEXITCODE -ne 0) {
            throw "FFmpeg decode validation failed with exit code $LASTEXITCODE. $validationText"
        }

        Move-Item -LiteralPath $temporary -Destination $destination -Force
        $records.Add([ordered]@{
            source = $relative
            source_sha256 = Get-Sha256 $input.FullName
            output = $relativeOgg
            output_sha256 = Get-Sha256 $destination
            state = "converted_and_validated"
            detail = "libvorbis q=$Quality, $SampleRate Hz, $Channels channel(s)"
        })
        $converted += 1
    }
    catch {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
        $records.Add([ordered]@{
            source = $relative
            source_sha256 = Get-Sha256 $input.FullName
            output = $relativeOgg
            output_sha256 = $null
            state = "failed"
            detail = $_.Exception.Message
        })
        $failed += 1
    }
}

$manifest = [ordered]@{
    schema_version = "1.0"
    generated_utc = [DateTime]::UtcNow.ToString("o")
    source_directory = $sourceRoot
    output_directory = $outputRoot
    ffmpeg = $ffmpeg
    ffmpeg_version = $ffmpegVersion
    encoder = "libvorbis"
    quality = $Quality
    sample_rate_hz = $SampleRate
    channels = $Channels
    counts = [ordered]@{
        discovered = $inputs.Count
        converted = $converted
        skipped = $skipped
        failed = $failed
    }
    files = $records
}

$manifestPath = Join-Path $outputRoot "conversion-manifest.json"
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

Write-Host "Music conversion manifest: $manifestPath"
Write-Host "Discovered: $($inputs.Count)  Converted: $converted  Skipped: $skipped  Failed: $failed"
if ($failed -gt 0) {
    throw "$failed audio file(s) failed conversion. See the manifest for exact errors."
}
