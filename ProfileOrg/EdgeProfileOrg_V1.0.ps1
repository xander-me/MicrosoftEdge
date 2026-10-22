<#
.SYNOPSIS
Preview Edge profile numbering and choose remembered favourites before the A-Z remainder.
.NOTES
Author: Using-IT
Requires PowerShell 5.1+. Run as the intended user with Edge closed.
#>
param([string]$LocalStatePath = (Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\User Data\Local State'))
$ErrorActionPreference = 'Stop'
$OriginalBytes = [IO.File]::ReadAllBytes($LocalStatePath)
$Original = [IO.File]::ReadAllText($LocalStatePath)
$Json = $Original | ConvertFrom-Json
$InfoCache = $Json.profile.info_cache
if (-not $InfoCache -or @($InfoCache.PSObject.Properties).Count -eq 0) { throw 'No Edge profiles found.' }
$SettingsPath = Join-Path (Split-Path $LocalStatePath) 'EdgeProfileOrg.settings.json'
$Starred = @()
$OriginalSettingsBytes = $null
if (Test-Path -LiteralPath $SettingsPath) {
    $OriginalSettingsBytes = [IO.File]::ReadAllBytes($SettingsPath)
    $Settings = Get-Content -LiteralPath $SettingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($null -ne $Settings.starred -and $Settings.starred -isnot [array]) { throw 'Invalid starred profile settings.' }
    $Starred = @($Settings.starred)
    if (@($Starred | Where-Object { $_ -isnot [string] }).Count -or @($Starred | Select-Object -Unique).Count -ne $Starred.Count) { throw 'Invalid starred profile settings.' }
}
$Profiles = @(@(foreach ($Property in $InfoCache.PSObject.Properties) {
    $Name = $Property.Value.name
    if ($null -eq $Name) { $Name = $Property.Name }
    if ($Name -isnot [string]) { throw "Invalid profile name: $($Property.Name)" }
    $Number = $null
    if ($Name -match '^(\d+)\s*-\s*') { $Number = [long]$Matches[1] }
    [PSCustomObject]@{ Folder = $Property.Name; Name = $Name; Clean = ($Name -replace '^\d+\s*-\s*', ''); Number = $Number }
}) | Sort-Object @{Expression={ $null -eq $_.Number }}, Number, Clean, Folder)
$Numbers = @($Profiles | Where-Object { $null -ne $_.Number } | ForEach-Object { $_.Number })
$Duplicates = $Numbers.Count - @($Numbers | Select-Object -Unique).Count
Write-Host "Existing numbering: $($Numbers.Count)/$($Profiles.Count) profiles; $Duplicates duplicate numbers."
for ($i = 0; $i -lt $Profiles.Count; $i++) {
    $Marker = ' '
    if ($Starred -contains $Profiles[$i].Folder) { $Marker = '*' }
    Write-Host "$($i + 1). $Marker $($Profiles[$i].Name) [$($Profiles[$i].Folder)]"
}
while ($true) {
    $Choice = (Read-Host 'Starred profiles in top-first order (e.g. 3,1); Enter keeps saved stars; none clears').Trim()
    if (-not $Choice) { break }
    if ($Choice -eq 'none') { $Starred = @(); break }
    $Selected = @()
    $Valid = $true
    foreach ($Value in $Choice.Split(',')) {
        $Index = 0
        if (-not [int]::TryParse($Value.Trim(), [ref]$Index) -or $Index -lt 1 -or $Index -gt $Profiles.Count -or $Selected -contains $Index) { $Valid = $false; break }
        $Selected += $Index
    }
    if ($Valid) { $Starred = @($Selected | ForEach-Object { $Profiles[$_ - 1].Folder }); break }
    Write-Host 'Enter unique list numbers separated by commas.'
}
$Starred = @($Starred | Where-Object { $Profiles.Folder -contains $_ })
$Ordered = @()
foreach ($Folder in $Starred) { $Ordered += @($Profiles | Where-Object { $_.Folder -eq $Folder }) }
$Ordered += @($Profiles | Where-Object { $Starred -notcontains $_.Folder } | Sort-Object Clean, Folder)
$Changed = $false
Write-Host 'Proposed names:'
for ($i = 0; $i -lt $Ordered.Count; $i++) {
    $NewName = '{0:D2} - {1}' -f ($i + 1), $Ordered[$i].Clean
    Write-Host "$($Ordered[$i].Name) -> $NewName"
    if ($Ordered[$i].Name -cne $NewName) { $Changed = $true }
    $InfoCache.($Ordered[$i].Folder) | Add-Member -NotePropertyName name -NotePropertyValue $NewName -Force
}
if ((Read-Host 'Close Edge completely. Apply names and save starred order? [y/N]') -ne 'y') { Write-Host 'Cancelled; no files changed.'; return }
if ([IO.File]::ReadAllText($LocalStatePath) -cne $Original) { throw 'Local State changed during preview. Run again with Edge closed.' }
if (Get-Process -Name msedge -ErrorAction SilentlyContinue) { throw 'Close Edge completely before applying changes.' }
function Write-JsonFile($Path, $Value) {
    $TempPath = "$Path.temp-$([guid]::NewGuid().ToString('N'))"
    try {
        $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $TempPath -Encoding UTF8
        Get-Content -LiteralPath $TempPath -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null
        Move-Item -LiteralPath $TempPath -Destination $Path -Force
    } finally {
        if (Test-Path -LiteralPath $TempPath) { Remove-Item -LiteralPath $TempPath }
    }
}
function Write-VerifiedBackup($Path, [byte[]]$Bytes, $Token) {
    $Backup = "$Path.backup-before-profile-prefix-$Token"
    $Stream = [IO.File]::Open($Backup, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
    try { $Stream.Write($Bytes, 0, $Bytes.Length); $Stream.Flush($true) } finally { $Stream.Dispose() }
    if ([Convert]::ToBase64String([IO.File]::ReadAllBytes($Backup)) -cne [Convert]::ToBase64String($Bytes)) {
        throw "Backup verification failed: $Backup. No changes applied."
    }
    return $Backup
}
$SavedStars = if ($null -ne $OriginalSettingsBytes) { ConvertTo-Json -InputObject @($Settings.starred) -Compress } else { '' }
$DesiredStars = ConvertTo-Json -InputObject @($Starred) -Compress
if (-not $Changed -and $SavedStars -ceq $DesiredStars) { Write-Host 'Names and favourites already match; no files changed.'; return }
$Token = [guid]::NewGuid().ToString('N')
$BackupPath = Write-VerifiedBackup $LocalStatePath $OriginalBytes $Token
if ($null -ne $OriginalSettingsBytes) { $null = Write-VerifiedBackup $SettingsPath $OriginalSettingsBytes $Token }
# Recheck after backup so a stale snapshot cannot overwrite a concurrent change.
if ([Convert]::ToBase64String([IO.File]::ReadAllBytes($LocalStatePath)) -cne [Convert]::ToBase64String($OriginalBytes)) { throw 'Local State changed during backup. No changes applied.' }
if ($null -ne $OriginalSettingsBytes) {
    if (-not (Test-Path -LiteralPath $SettingsPath) -or [Convert]::ToBase64String([IO.File]::ReadAllBytes($SettingsPath)) -cne [Convert]::ToBase64String($OriginalSettingsBytes)) { throw 'Saved favourites changed. Reload before applying.' }
} elseif (Test-Path -LiteralPath $SettingsPath) { throw 'Saved favourites changed. Reload before applying.' }
Write-Host "Backup created and verified: $BackupPath"
if ($Changed) { Write-JsonFile $LocalStatePath $Json }
try { Write-JsonFile $SettingsPath @{starred = @($Starred)} }
catch { throw "Could not save favourites. Names may already have been applied. Backup: $BackupPath. $_" }
Write-Host "Starred order saved: $SettingsPath"
