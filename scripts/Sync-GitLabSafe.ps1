param(
    [string]$RemoteName = "gitlab",
    [string]$RemoteUrl = "",
    [string]$Branch = "main",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-GitChecked {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed with exit code $LASTEXITCODE"
    }
}

$root = (& git rev-parse --show-toplevel 2>$null).Trim()
if (-not $root) { throw "Run this from a Git checkout." }
Set-Location $root

$status = (& git status --porcelain).Trim()
if ($status) {
    throw "Refusing GitLab publication with uncommitted/untracked changes. Commit or intentionally remove them first."
}

$currentBranch = (& git branch --show-current).Trim()
if ($currentBranch -ne $Branch) {
    throw "Current branch is '$currentBranch', expected '$Branch'. Refusing to publish an unintended branch."
}

$localSha = (& git rev-parse HEAD).Trim()
if ($localSha -notmatch '^[0-9a-f]{40}$') { throw "Could not resolve local HEAD SHA." }

$remoteNames = @(& git remote)
$remoteExists = $remoteNames -contains $RemoteName
if (-not $remoteExists) {
    if (-not $RemoteUrl) {
        throw "Git remote '$RemoteName' does not exist. Re-run with -RemoteUrl <your GitLab project URL>. No URL is guessed."
    }
    if ($DryRun) {
        Write-Host "[dry-run] would add remote '$RemoteName' (URL intentionally not echoed)"
    } else {
        Invoke-GitChecked remote add $RemoteName $RemoteUrl
    }
} elseif ($RemoteUrl) {
    $existing = (& git remote get-url $RemoteName).Trim()
    if ($existing -ne $RemoteUrl) {
        throw "Remote '$RemoteName' already exists with a different URL. Refusing to rewrite it automatically."
    }
}

Write-Host "Local $Branch SHA: $localSha"
Write-Host "GitLab remote name: $RemoteName"

if ($DryRun -and -not $remoteExists) {
    Write-Host "[dry-run] remote does not exist yet, so ancestry/remote-SHA verification cannot run."
    exit 0
}

# Fetch first so we never erase GitLab-only history.
& git fetch $RemoteName $Branch --prune
$fetchExit = $LASTEXITCODE
if ($fetchExit -ne 0) {
    # An empty/new project may not have the branch yet. Verify with ls-remote before deciding.
    $remoteProbe = (& git ls-remote --heads $RemoteName "refs/heads/$Branch" 2>$null)
    if ($LASTEXITCODE -ne 0) { throw "Could not contact GitLab remote '$RemoteName'." }
    if ($remoteProbe) { throw "Fetch from existing GitLab branch failed; refusing to push." }
}

$remoteLine = (& git ls-remote --heads $RemoteName "refs/heads/$Branch" 2>$null)
if ($LASTEXITCODE -ne 0) { throw "Could not read GitLab branch SHA." }
$remoteSha = ""
if ($remoteLine) { $remoteSha = ($remoteLine -split '\s+')[0].Trim() }

if ($remoteSha) {
    & git merge-base --is-ancestor $remoteSha $localSha
    if ($LASTEXITCODE -ne 0) {
        throw "GitLab $Branch ($remoteSha) is not an ancestor of local HEAD. Histories diverged or GitLab is ahead; refusing force-push. Merge/review explicitly first."
    }
    if ($remoteSha -eq $localSha) {
        Write-Host "PASS: GitLab already matches local HEAD."
        exit 0
    }
} else {
    Write-Host "GitLab branch '$Branch' does not exist yet; a normal create-only push is safe."
}

if ($DryRun) {
    Write-Host "[dry-run] would push $localSha to $RemoteName/$Branch without force."
    exit 0
}

Invoke-GitChecked push $RemoteName "$localSha`:refs/heads/$Branch"
$verifyLine = (& git ls-remote --heads $RemoteName "refs/heads/$Branch")
if ($LASTEXITCODE -ne 0 -or -not $verifyLine) { throw "Push returned but remote verification failed." }
$verifySha = ($verifyLine -split '\s+')[0].Trim()
if ($verifySha -ne $localSha) {
    throw "Remote SHA mismatch after push. Expected $localSha, got $verifySha."
}

Write-Host "PASS: GitLab $Branch verified at $verifySha"
