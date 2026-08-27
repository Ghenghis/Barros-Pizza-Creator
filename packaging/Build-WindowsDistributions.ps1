[CmdletBinding()]
param(
    [string]$Python = 'py',
    [string]$Iscc = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    & $Python -3 -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Python test suite failed.' }
    & $Python -3 tools\build_release.py
    if ($LASTEXITCODE -ne 0) { throw 'Portable package build failed.' }
    & $Python -3 tools\build_vps_bundle.py
    if ($LASTEXITCODE -ne 0) { throw 'VPS package build failed.' }

    if ([string]::IsNullOrWhiteSpace($Iscc)) {
        $candidates = @(
            (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
            (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe')
        )
        $Iscc = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
    }
    if (-not $Iscc -or -not (Test-Path -LiteralPath $Iscc)) {
        throw 'Inno Setup 6 ISCC.exe was not found. Portable and VPS ZIPs passed; installer EXE remains not built.'
    }
    & $Iscc packaging\CreatorInstaller.iss
    if ($LASTEXITCODE -ne 0) { throw 'Inno Setup build failed.' }

    Get-ChildItem releases -File | Sort-Object Name | ForEach-Object {
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
        Write-Host "$hash  $($_.Name)"
    }
}
finally {
    Pop-Location
}
