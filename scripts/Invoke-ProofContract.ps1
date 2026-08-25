[CmdletBinding()]
param(
    [ValidateSet("Static", "Build", "Runtime", "All")][string]$Stage = "All",
    [string]$GameRoot = "S:\Unity_Games\PC3 - Pizza Creator",
    [string]$PackageRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$EvidenceRoot = "",
    [switch]$RequireComplete
)

$ErrorActionPreference = "Stop"
$PackageRoot = (Resolve-Path -LiteralPath $PackageRoot).Path
$contractPath = Join-Path $PackageRoot "contracts\rc1.acceptance.json"
if (-not (Test-Path -LiteralPath $contractPath)) { throw "Proof contract not found: $contractPath" }
$contract = Get-Content -LiteralPath $contractPath -Raw | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace($EvidenceRoot)) { $EvidenceRoot = Join-Path $PackageRoot "evidence\runs" }
$runId = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$runRoot = Join-Path $EvidenceRoot $runId
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null

$gateIndex = @{}
$gateOrder = New-Object Collections.Generic.List[string]
foreach ($layer in $contract.layers) {
    foreach ($gate in $layer.gates) {
        $gateIndex[$gate.id] = [pscustomobject]@{ Layer = $layer.id; Gate = $gate }
        $gateOrder.Add([string]$gate.id)
    }
}
$observed = @{}

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return "" }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Add-GateResult([string]$Id, [string]$State, [string]$Detail, [string[]]$Evidence = @()) {
    if (-not $gateIndex.ContainsKey($Id)) { throw "Unknown contract gate: $Id" }
    if (@("not_run", "pass", "fail", "blocked") -notcontains $State) { throw "Invalid gate state: $State" }
    $entry = $gateIndex[$Id]
    $result = [ordered]@{
        gate_id = $Id
        layer = $entry.Layer
        state = $State
        requirement = $entry.Gate.requirement
        release_required = [bool]$entry.Gate.release_required
        detail = $Detail
        evidence = @($Evidence)
        observed_utc = [DateTime]::UtcNow.ToString("o")
    }
    $observed[$Id] = [pscustomobject]$result
    $color = switch ($State) { "pass" { "Green" } "fail" { "Red" } "blocked" { "Yellow" } default { "DarkGray" } }
    Write-Host ("[{0}] {1} - {2}" -f $State.ToUpperInvariant(), $Id, $Detail) -ForegroundColor $color
}

function Find-Python {
    foreach ($name in @("python", "python3", "py")) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) { return $command.Source }
    }
    return ""
}

function Invoke-StaticGates {
    $required = @(
        "README.md", "INSTALL_Barros_AI_Designer.ps1", "DIAGNOSE_Barros_AI.ps1",
        "plugin-src\BarrosAiPlugin.cs", "plugin-src\GameBridge.cs", "plugin-src\PanelRenderer.cs", "plugin-src\EvidenceRecorder.cs",
        "backend\main.py", "backend\catalog.bootstrap.json", "assets\barros-pizza-creator-header.png",
        "contracts\rc1.acceptance.json", "artifacts\Barros.PizzaCreator.AI.dll", "artifacts\build-provenance.json",
        "docs\ENGINEERING_PLAYBOOK.md", "docs\PROJECT_STATUS.md", "scripts\Convert-BarrosMusic.ps1", "CONVERT_BARROS_MUSIC.bat",
        "tools\build_release.py"
    )
    $missing = @($required | Where-Object { -not (Test-Path -LiteralPath (Join-Path $PackageRoot $_) -PathType Leaf) })
    if ($missing.Count -eq 0) { Add-GateResult "SRC-001" "pass" "$($required.Count) required files are present." }
    else { Add-GateResult "SRC-001" "fail" ("Missing: " + ($missing -join ", ")) }

    $python = Find-Python
    $testLog = Join-Path $runRoot "backend-tests.txt"
    if ([string]::IsNullOrWhiteSpace($python)) {
        Add-GateResult "SRC-002" "blocked" "Python 3 was not found."
    }
    else {
        # unittest's verbose runner intentionally writes progress to stderr.
        # Windows PowerShell wraps native stderr as NativeCommandError; with the
        # script-wide Stop preference that used to terminate this otherwise
        # successful gate before LASTEXITCODE could be inspected. Capture the
        # merged native streams under Continue, then restore every preference.
        $savedErrorActionPreference = $ErrorActionPreference
        $nativePreferenceExists = Test-Path Variable:PSNativeCommandUseErrorActionPreference
        if ($nativePreferenceExists) {
            $savedNativeErrorPreference = $PSNativeCommandUseErrorActionPreference
        }
        try {
            $ErrorActionPreference = "Continue"
            if ($nativePreferenceExists) {
                $PSNativeCommandUseErrorActionPreference = $false
            }
            $testLines = @(& $python -m unittest discover -s (Join-Path $PackageRoot "tests") -v 2>&1)
            $testExit = $LASTEXITCODE
        }
        finally {
            $ErrorActionPreference = $savedErrorActionPreference
            if ($nativePreferenceExists) {
                $PSNativeCommandUseErrorActionPreference = $savedNativeErrorPreference
            }
        }
        $testOutput = ($testLines | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine
        $testOutput | Set-Content -LiteralPath $testLog -Encoding UTF8
        if ($testExit -eq 0) { Add-GateResult "SRC-002" "pass" "Backend and contract tests passed." @($testLog) }
        else { Add-GateResult "SRC-002" "fail" "Unit tests exited $testExit." @($testLog) }
    }

    try {
        $catalog = Get-Content -LiteralPath (Join-Path $PackageRoot "backend\catalog.bootstrap.json") -Raw | ConvertFrom-Json
        $ids = @($catalog.ingredients | ForEach-Object { [string]$_.id })
        $categories = @($catalog.ingredients | ForEach-Object { [string]$_.type_id } | Sort-Object -Unique)
        $unique = @($ids | Sort-Object -Unique)
        if ($ids.Count -eq 87 -and $unique.Count -eq 87 -and $categories.Count -eq 6) {
            Add-GateResult "SRC-003" "pass" "87 unique ingredient IDs across 6 categories."
        }
        else { Add-GateResult "SRC-003" "fail" "$($ids.Count) records, $($unique.Count) unique IDs, $($categories.Count) categories." }
    }
    catch { Add-GateResult "SRC-003" "fail" $_.Exception.Message }

    $referenceFailures = New-Object Collections.Generic.List[string]
    foreach ($reference in $contract.reference_images) {
        $path = Join-Path $PackageRoot $reference.path
        $actual = Get-Sha256 $path
        if ($actual -ne [string]$reference.sha256) { $referenceFailures.Add("$($reference.mode):$actual") }
    }
    if ($referenceFailures.Count -eq 0) { Add-GateResult "SRC-004" "pass" "All four locked visual baselines match." }
    else { Add-GateResult "SRC-004" "fail" ($referenceFailures -join "; ") }
}

function Invoke-BuildGates {
    $managed = Join-Path $GameRoot "Pizza Connection 3 - Pizza Creator_Data\Managed"
    $assembly = Join-Path $managed "Assembly-CSharp.dll"
    $firstpass = Join-Path $managed "Assembly-CSharp-firstpass.dll"
    if (-not (Test-Path -LiteralPath $assembly) -or -not (Test-Path -LiteralPath $firstpass)) {
        Add-GateResult "BLD-101" "blocked" "Exact Managed folder is unavailable at $managed"
        Add-GateResult "BLD-102" "blocked" "Game assembly gate did not pass."
        Add-GateResult "BLD-103" "blocked" "Game assembly gate did not pass."
        Add-GateResult "BLD-104" "blocked" "Game assembly gate did not pass."
        return
    }
    $assemblyHash = Get-Sha256 $assembly
    $firstpassHash = Get-Sha256 $firstpass
    $hashEvidence = [ordered]@{
        game_root = $GameRoot
        assembly_csharp = @{ path = $assembly; sha256 = $assemblyHash }
        assembly_csharp_firstpass = @{ path = $firstpass; sha256 = $firstpassHash }
    }
    $hashPath = Join-Path $runRoot "assembly-hashes.json"
    $hashEvidence | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $hashPath -Encoding UTF8
    if ($assemblyHash -eq $contract.target.assembly_csharp_sha256 -and $firstpassHash -eq $contract.target.assembly_csharp_firstpass_sha256) {
        Add-GateResult "BLD-101" "pass" "Installed game assemblies exactly match the contract." @($hashPath)
    }
    else {
        Add-GateResult "BLD-101" "fail" "Installed assembly hash mismatch; build and install are stopped." @($hashPath)
        Add-GateResult "BLD-102" "blocked" "Game assembly hash mismatch."
        Add-GateResult "BLD-103" "blocked" "Game assembly hash mismatch."
        Add-GateResult "BLD-104" "blocked" "Game assembly hash mismatch."
        return
    }

    $prebuiltValid = $false
    try {
        $provenance = Get-Content -LiteralPath (Join-Path $PackageRoot "artifacts\build-provenance.json") -Raw | ConvertFrom-Json
        $prebuilt = Join-Path $PackageRoot ("artifacts\" + $provenance.artifact)
        $prebuiltHash = Get-Sha256 $prebuilt
        if ($prebuiltHash -eq $provenance.artifact_sha256 -and $assemblyHash -eq $provenance.target.assembly_csharp_sha256) {
            $prebuiltValid = $true
            Add-GateResult "BLD-103" "pass" "Certified plugin and provenance hashes agree: $prebuiltHash" @($prebuilt, (Join-Path $PackageRoot "artifacts\build-provenance.json"))
            Add-GateResult "BLD-102" "pass" "Certified Roslyn compile completed with zero errors against these exact assembly hashes." @($prebuilt, (Join-Path $PackageRoot "artifacts\build-provenance.json"))
        }
        else {
            Add-GateResult "BLD-103" "fail" "Certified plugin or provenance hash mismatch."
            Add-GateResult "BLD-102" "fail" "Exact-assembly compile provenance could not be authenticated."
        }
    }
    catch {
        Add-GateResult "BLD-103" "fail" $_.Exception.Message
        Add-GateResult "BLD-102" "fail" "Exact-assembly compile provenance could not be authenticated."
    }

    if ($env:OS -ne "Windows_NT") {
        Add-GateResult "BLD-104" "blocked" "Windows compiler parity must run on the target PC."
        return
    }
    $compileLog = Join-Path $runRoot "windows-compile.log"
    $compiled = Join-Path $runRoot "Barros.PizzaCreator.AI.windows.dll"
    try {
        $buildOutput = & (Join-Path $PackageRoot "scripts\Build-Plugin.ps1") -GameRoot $GameRoot -PackageRoot $PackageRoot -OutputPath $compiled 2>&1 | Out-String
        $buildExit = $LASTEXITCODE
        $buildOutput | Set-Content -LiteralPath $compileLog -Encoding UTF8
        if ($buildExit -eq 0 -and (Test-Path -LiteralPath $compiled)) {
            $hash = Get-Sha256 $compiled
            Add-GateResult "BLD-104" "pass" "Windows compiler parity build completed against installed DLLs." @($compileLog)
        }
        else {
            Add-GateResult "BLD-104" "fail" "Windows compiler parity did not complete." @($compileLog)
        }
    }
    catch {
        $_ | Out-String | Set-Content -LiteralPath $compileLog -Encoding UTF8
        Add-GateResult "BLD-104" "fail" "Windows compiler parity did not complete." @($compileLog)
    }
}

function Test-Event([string]$EventPath, [string]$Name) {
    if (-not (Test-Path -LiteralPath $EventPath -PathType Leaf)) { return $false }
    return [bool](Select-String -LiteralPath $EventPath -SimpleMatch ('"event":"' + $Name + '"') -Quiet)
}

function Add-EventAndFileGate([string]$Id, [string]$EventPath, [string]$EventName, [string]$FilePath, [string]$Success) {
    $eventPresent = Test-Event $EventPath $EventName
    $filePresent = [string]::IsNullOrWhiteSpace($FilePath) -or (Test-Path -LiteralPath $FilePath -PathType Leaf)
    if ($eventPresent -and $filePresent) { Add-GateResult $Id "pass" $Success @($EventPath, $FilePath | Where-Object { $_ }) }
    else {
        $missing = @()
        if (-not $eventPresent) { $missing += "event $EventName" }
        if (-not $filePresent) { $missing += "file $FilePath" }
        Add-GateResult $Id "blocked" ("Awaiting " + ($missing -join " and ") + ".")
    }
}

function Invoke-RuntimeGates {
    $log = Join-Path $GameRoot "BepInEx\LogOutput.log"
    $eventSource = Join-Path $GameRoot "BarrosAI\evidence\runtime-events.jsonl"
    $shots = Join-Path $GameRoot "BarrosAI\evidence\screenshots"
    $copiedLog = Join-Path $runRoot "BepInEx-LogOutput.log"
    $copiedEvents = Join-Path $runRoot "runtime-events.jsonl"
    if (-not (Test-Path -LiteralPath $log -PathType Leaf)) {
        Add-GateResult "RUN-201" "blocked" "Launch the installed game once to create $log"
        Add-GateResult "RUN-202" "blocked" "Loader log is unavailable."
    }
    else {
        Copy-Item -LiteralPath $log -Destination $copiedLog -Force
        $content = Get-Content -LiteralPath $log -Raw
        if ($content -match "BepInEx 5\.") { Add-GateResult "RUN-201" "pass" "BepInEx 5 initialization is present in the live log." @($copiedLog) }
        else { Add-GateResult "RUN-201" "fail" "The live log does not show BepInEx 5 initialization." @($copiedLog) }
        $loaded = $content -match "Barro's AI Pizza Designer 1\.0\.0-rc1 loaded"
        $relevantErrors = @($content -split "`r?`n" | Where-Object { $_ -match "Barros|Pizza Designer" -and $_ -match "Error|Exception" })
        if ($loaded -and $relevantErrors.Count -eq 0) { Add-GateResult "RUN-202" "pass" "Plugin Awake completed with no relevant logged exception." @($copiedLog) }
        elseif ($relevantErrors.Count -gt 0) { Add-GateResult "RUN-202" "fail" ("Relevant loader errors: " + ($relevantErrors -join " | ")) @($copiedLog) }
        else { Add-GateResult "RUN-202" "fail" "Plugin load marker is absent." @($copiedLog) }
    }
    if (Test-Path -LiteralPath $eventSource -PathType Leaf) { Copy-Item -LiteralPath $eventSource -Destination $copiedEvents -Force }
    else { $copiedEvents = $eventSource }

    Add-EventAndFileGate "UI-301" $copiedEvents "ui.tab_installed" (Join-Path $shots "ui-tab.png") "Fifth tab registration and screenshot are present."
    Add-EventAndFileGate "UI-302" $copiedEvents "ui.header_fitted" (Join-Path $shots "ui-header.png") "Header geometry and close-button-safe screenshot are present."
    Add-EventAndFileGate "UI-303" $copiedEvents "ui.stock_header_restored" (Join-Path $shots "ui-stock-header.png") "Stock header restoration is proven."
    Add-EventAndFileGate "ACT-401" $copiedEvents "action.preview.success" (Join-Path $shots "preview.png") "Native Preview completed."
    Add-EventAndFileGate "ACT-402" $copiedEvents "action.restore.success" (Join-Path $shots "restore.png") "Native Restore completed."
    Add-EventAndFileGate "ACT-403" $copiedEvents "action.apply.success" (Join-Path $shots "apply.png") "Native Apply completed."
    Add-EventAndFileGate "ACT-404" $copiedEvents "action.save.success" "" "Native recipe-book Save completed."
    Add-EventAndFileGate "ACT-405" $copiedEvents "action.reload.verified" (Join-Path $shots "reload.png") "Saved recipe reload comparison passed."
    Add-EventAndFileGate "VOX-501" $copiedEvents "voice.capture.success" "" "Microphone capture returned PCM."
    Add-EventAndFileGate "VOX-502" $copiedEvents "voice.transcription.success" (Join-Path $shots "voice.png") "Configured STT returned a prompt transcript."
    foreach ($visual in @(
        @{ Id = "VIS-601"; Mode = "chat" }, @{ Id = "VIS-602"; Mode = "lab" },
        @{ Id = "VIS-603"; Mode = "crew" }, @{ Id = "VIS-604"; Mode = "voice" }
    )) {
        $report = Join-Path $shots ("comparison-" + $visual.Mode + ".json")
        if (Test-Path -LiteralPath $report -PathType Leaf) {
            try {
                $comparison = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
                if ($comparison.pass -eq $true) { Add-GateResult $visual.Id "pass" "$($visual.Mode) comparison thresholds passed." @($report) }
                elseif ($comparison.state -eq "blocked") { Add-GateResult $visual.Id "blocked" "$($visual.Mode) comparison is blocked." @($report) }
                else { Add-GateResult $visual.Id "fail" "$($visual.Mode) comparison thresholds failed." @($report) }
            }
            catch { Add-GateResult $visual.Id "fail" "Invalid comparison report: $($_.Exception.Message)" @($report) }
        }
        else { Add-GateResult $visual.Id "blocked" "Awaiting $report" }
    }
}

$runStatic = $Stage -eq "Static" -or $Stage -eq "All"
$runBuild = $Stage -eq "Build" -or $Stage -eq "All"
$runRuntime = $Stage -eq "Runtime" -or $Stage -eq "All"
if ($runStatic) { Invoke-StaticGates }
if ($runBuild) { Invoke-BuildGates }
if ($runRuntime) { Invoke-RuntimeGates }

foreach ($id in $gateOrder) {
    if (-not $observed.ContainsKey($id)) { Add-GateResult $id "not_run" "Stage '$Stage' did not select this gate." }
}
$orderedResults = @($gateOrder | ForEach-Object { $observed[$_] })
$counts = [ordered]@{}
foreach ($state in @("pass", "fail", "blocked", "not_run")) { $counts[$state] = @($orderedResults | Where-Object { $_.state -eq $state }).Count }
$document = [ordered]@{
    contract_id = $contract.contract_id
    release = $contract.release
    run_id = $runId
    stage = $Stage
    game_root = $GameRoot
    package_root = $PackageRoot
    counts = $counts
    results = $orderedResults
}
$resultsPath = Join-Path $runRoot "results.json"
$document | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $resultsPath -Encoding UTF8

$summary = New-Object Collections.Generic.List[string]
$summary.Add("# Barro's RC1 proof run $runId")
$summary.Add("")
$summary.Add("Stage: **$Stage**  ")
$summary.Add("PASS: **$($counts.pass)** · FAIL: **$($counts.fail)** · BLOCKED: **$($counts.blocked)** · NOT RUN: **$($counts.not_run)**")
$summary.Add("")
$summary.Add("| Gate | Layer | State | Detail |")
$summary.Add("|---|---|---|---|")
foreach ($result in $orderedResults) {
    $safeDetail = ([string]$result.detail).Replace("|", "\|").Replace("`r", " ").Replace("`n", " ")
    $summary.Add("| $($result.gate_id) | $($result.layer) | $($result.state.ToUpperInvariant()) | $safeDetail |")
}
$summaryPath = Join-Path $runRoot "summary.md"
$summary | Set-Content -LiteralPath $summaryPath -Encoding UTF8
Write-Host "`nEvidence: $runRoot"

$hasFailure = $counts.fail -gt 0
$incomplete = @($orderedResults | Where-Object { $_.release_required -and $_.state -ne "pass" }).Count -gt 0
if ($hasFailure -or ($RequireComplete -and $incomplete)) { exit 1 }
exit 0
