<#
.SYNOPSIS
    Packs KIP KEPLER for handing out: dist\KipKepler-<version>-windows-x64.zip and, through WSL, the Linux archive
    (which also runs on the Steam Deck).

.DESCRIPTION
    .\Deploy\build_release.ps1 [-NoBuild] [-NoLinux]

    Builds the Release (build.ps1), stages KipKepler.exe with its assets, the player's readme, the credits and the
    licence in work\release and
    zips them into dist. The Linux archive comes from Deploy/build_linux.sh in WSL (GCC 12, glibc 2.35 and newer,
    SteamOS included); without WSL it is skipped.

    -NoBuild   pack what bin\msvc holds
    -NoLinux   only the Windows archive

.EXAMPLE
    .\Deploy\build_release.ps1
#>
param(
    [switch]$NoBuild,
    [switch]$NoLinux
)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$version = (Select-String -Path (Join-Path $root "CMakeLists.txt") -Pattern 'project\( KipKepler VERSION ([0-9.]+)').Matches[0].Groups[1].Value
Write-Host "KIP KEPLER $version"

if (-not $NoBuild) {
    & (Join-Path $root "build.ps1")
    if ($LASTEXITCODE -ne 0) { throw "build failed" }
}

# Windows: the exe (static runtime) and the assets beside it.
$name = "KipKepler-$version-windows-x64"
$stage = Join-Path $root "work\release\$name"
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force $stage | Out-Null
Copy-Item (Join-Path $root "bin\msvc\KipKepler.exe") (Join-Path $stage "KipKepler.exe")
& robocopy (Join-Path $root "assets") (Join-Path $stage "assets") /E /NFL /NDL /NJH /NJS /NP | Out-Null
$readme = Join-Path $root "docs\README-player.txt"
if (Test-Path $readme) { Copy-Item $readme (Join-Path $stage "README.txt") }
foreach ($f in "LICENSE", "docs\CREDITS.txt") {
    if (Test-Path (Join-Path $root $f)) { Copy-Item (Join-Path $root $f) $stage }
}
$dist = Join-Path $root "dist"
New-Item -ItemType Directory -Force $dist | Out-Null
$zip = Join-Path $dist "$name.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
# System32's tar makes zips that Explorer opens (another tar may come first on the PATH).
& "$env:SystemRoot\System32\tar.exe" -a -c -f $zip -C (Join-Path $root "work\release") $name
if ($LASTEXITCODE -ne 0) { throw "zip failed" }
Write-Host $zip

if (-not $NoLinux) {
    $wsl = Get-Command wsl -ErrorAction SilentlyContinue
    if ($wsl) {
        $linuxRoot = "/mnt/" + $root.Substring(0, 1).ToLower() + $root.Substring(2).Replace("\", "/")
        & wsl -e bash "$linuxRoot/Deploy/build_linux.sh"
        if ($LASTEXITCODE -ne 0) { throw "linux build failed" }
    } else {
        Write-Host "no WSL: the Linux archive is skipped"
    }
}
