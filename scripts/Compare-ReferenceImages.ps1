[CmdletBinding()]
param(
    [string]$PackageRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$LiveRoot = "S:\Unity_Games\PC3 - Pizza Creator\BarrosAI\evidence\screenshots",
    [string]$OutputRoot = "",
    [double]$PanelStartRatio = 0.69,
    [double]$MaximumMeanAbsoluteError = 0.30,
    [double]$MinimumEdgeIntersectionOverUnion = 0.10,
    [switch]$ReportOnly
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
if ([string]::IsNullOrWhiteSpace($OutputRoot)) { $OutputRoot = $LiveRoot }
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$sampleWidth = 256
$sampleHeight = 144
$panelStart = [Math]::Max(0, [Math]::Min($sampleWidth - 1, [Math]::Floor($sampleWidth * $PanelStartRatio)))

function Open-NormalizedBitmap([string]$Path, [int]$Width, [int]$Height) {
    $source = [System.Drawing.Image]::FromFile($Path)
    try {
        $output = New-Object System.Drawing.Bitmap($Width, $Height, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
        $graphics = [System.Drawing.Graphics]::FromImage($output)
        try {
            $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $graphics.DrawImage($source, 0, 0, $Width, $Height)
        }
        finally { $graphics.Dispose() }
        return $output
    }
    finally { $source.Dispose() }
}

function Get-Luma([System.Drawing.Color]$Color) {
    return 0.2126 * $Color.R + 0.7152 * $Color.G + 0.0722 * $Color.B
}

$modes = @(
    @{ Name = "chat"; Reference = "01_chat.png" },
    @{ Name = "lab"; Reference = "02_lab.png" },
    @{ Name = "crew"; Reference = "03_crew.png" },
    @{ Name = "voice"; Reference = "04_voice.png" }
)
$allPassed = $true
foreach ($mode in $modes) {
    $referencePath = Join-Path $PackageRoot ("docs\mockups\" + $mode.Reference)
    $livePath = Join-Path $LiveRoot ($mode.Name + ".png")
    $reportPath = Join-Path $OutputRoot ("comparison-" + $mode.Name + ".json")
    $diffPath = Join-Path $OutputRoot ("difference-" + $mode.Name + ".png")
    if (-not (Test-Path -LiteralPath $referencePath) -or -not (Test-Path -LiteralPath $livePath)) {
        $missing = [ordered]@{
            schema = 1; mode = $mode.Name; pass = $false; state = "blocked";
            detail = "Reference or live screenshot is missing."; reference = $referencePath; live = $livePath
        }
        $missing | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $reportPath -Encoding UTF8
        Write-Host "[BLOCKED] $($mode.Name): live screenshot is missing." -ForegroundColor Yellow
        $allPassed = $false
        continue
    }

    $reference = Open-NormalizedBitmap $referencePath $sampleWidth $sampleHeight
    $live = Open-NormalizedBitmap $livePath $sampleWidth $sampleHeight
    $difference = New-Object System.Drawing.Bitmap($sampleWidth, $sampleHeight, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    try {
        $delta = 0.0
        $pixelCount = 0
        $edgeIntersection = 0
        $edgeUnion = 0
        for ($y = 0; $y -lt $sampleHeight; $y++) {
            for ($x = 0; $x -lt $sampleWidth; $x++) {
                if ($x -lt $panelStart) {
                    $difference.SetPixel($x, $y, [System.Drawing.Color]::Black)
                    continue
                }
                $a = $reference.GetPixel($x, $y)
                $b = $live.GetPixel($x, $y)
                $dr = [Math]::Abs([int]$a.R - [int]$b.R)
                $dg = [Math]::Abs([int]$a.G - [int]$b.G)
                $db = [Math]::Abs([int]$a.B - [int]$b.B)
                $delta += $dr + $dg + $db
                $pixelCount++
                $difference.SetPixel($x, $y, [System.Drawing.Color]::FromArgb($dr, $dg, $db))

                if ($x -lt $sampleWidth - 1 -and $y -lt $sampleHeight - 1) {
                    $aRight = $reference.GetPixel($x + 1, $y)
                    $aDown = $reference.GetPixel($x, $y + 1)
                    $bRight = $live.GetPixel($x + 1, $y)
                    $bDown = $live.GetPixel($x, $y + 1)
                    $edgeA = ([Math]::Abs((Get-Luma $a) - (Get-Luma $aRight)) + [Math]::Abs((Get-Luma $a) - (Get-Luma $aDown))) -ge 46.0
                    $edgeB = ([Math]::Abs((Get-Luma $b) - (Get-Luma $bRight)) + [Math]::Abs((Get-Luma $b) - (Get-Luma $bDown))) -ge 46.0
                    if ($edgeA -or $edgeB) { $edgeUnion++ }
                    if ($edgeA -and $edgeB) { $edgeIntersection++ }
                }
            }
        }
        $mae = if ($pixelCount -gt 0) { $delta / ($pixelCount * 3.0 * 255.0) } else { 1.0 }
        $edgeIou = if ($edgeUnion -gt 0) { $edgeIntersection / [double]$edgeUnion } else { 0.0 }
        $passed = $mae -le $MaximumMeanAbsoluteError -and $edgeIou -ge $MinimumEdgeIntersectionOverUnion
        if (-not $passed) { $allPassed = $false }
        $difference.Save($diffPath, [System.Drawing.Imaging.ImageFormat]::Png)
        $report = [ordered]@{
            schema = 1
            mode = $mode.Name
            pass = $passed
            state = $(if ($passed) { "pass" } else { "fail" })
            scope = "right-side panel after bicubic normalization"
            sample = @{ width = $sampleWidth; height = $sampleHeight; panel_start_ratio = $PanelStartRatio }
            metrics = @{
                normalized_mean_absolute_error = [Math]::Round($mae, 6)
                edge_intersection_over_union = [Math]::Round($edgeIou, 6)
            }
            thresholds = @{
                maximum_mean_absolute_error = $MaximumMeanAbsoluteError
                minimum_edge_intersection_over_union = $MinimumEdgeIntersectionOverUnion
            }
            reference = $referencePath
            live = $livePath
            difference = $diffPath
            observed_utc = [DateTime]::UtcNow.ToString("o")
            note = "Metrics are objective triage, not a substitute for checking legibility, clipping, close-button access, and interaction."
        }
        $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8
        $color = if ($passed) { "Green" } else { "Red" }
        Write-Host ("[{0}] {1}: MAE={2:N4}; edge IoU={3:N4}" -f $(if ($passed) { "PASS" } else { "FAIL" }), $mode.Name, $mae, $edgeIou) -ForegroundColor $color
    }
    finally {
        $reference.Dispose()
        $live.Dispose()
        $difference.Dispose()
    }
}

if (-not $allPassed -and -not $ReportOnly) { exit 1 }
exit 0
