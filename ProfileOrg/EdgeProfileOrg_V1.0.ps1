<#
.SYNOPSIS
    Organizes Microsoft Edge profiles by renaming them with numeric prefixes.

.DESCRIPTION
    This script renames Microsoft Edge profiles alphabetically, prefixing each with a two-digit number (e.g., "01 - Profile Name").
    It modifies the Local State JSON file in the Edge user data directory.

    How-to Guide:
    1. Close Microsoft Edge completely.
    2. Run this script as an administrator (recommended for access to user data).
    3. The script will:
       - Stop any running Edge processes.
       - Back up the Local State file.
       - Read and parse the JSON.
       - Sort profiles by name (after removing existing prefixes).
       - Rename profiles with new prefixes.
       - Validate the changes and apply them.
    4. Open Edge to see the updated profile list.
    5. If something goes wrong, restore from the backup file.

    Warning: Modifying browser data can be risky. Ensure you have backups. Use at your own risk.

.VERSION
    1.0

.AUTHOR
    Alexander Christensen - Using-IT.dk

.NOTES
    Requires PowerShell 5.1 or later.
#>

# Define the path to the Local State file
$LocalStatePath = Join-Path $env:LOCALAPPDATA "Microsoft\Edge\User Data\Local State"

# Stop any running Microsoft Edge processes to avoid conflicts
Stop-Process -Name msedge -Force -ErrorAction SilentlyContinue

# Check if the Local State file exists
if (-not (Test-Path $LocalStatePath)) {
    throw "Local State not found: $LocalStatePath"
}

# Generate a timestamp for backup and temp files
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupPath = "$LocalStatePath.backup-before-profile-prefix-$Timestamp"

# Create a backup of the Local State file
Copy-Item -Path $LocalStatePath -Destination $BackupPath -Force -ErrorAction Stop
Write-Host "Backup created: $BackupPath"

# Read and parse the JSON from the Local State file
try {
    $Json = Get-Content -Path $LocalStatePath -Raw -Encoding UTF8 | ConvertFrom-Json
} catch {
    throw "Failed to read or parse JSON from Local State: $_"
}

# Extract the profile info cache from the JSON
$InfoCache = $Json.profile.info_cache

# Ensure there are profiles to process
if (-not $InfoCache) {
    throw "No Edge profiles found in Local State."
}

# Initialize an array to hold profile information
$Profiles = @()

# Loop through each profile in the info cache
foreach ($Property in $InfoCache.PSObject.Properties) {
    $Folder = $Property.Name
    $Name = $Property.Value.name

    # Remove existing numeric prefix, e.g. "01 - ", "1- ", "123 -"
    $CleanName = $Name -replace '^\d+\s*-\s*', ''

    # Add profile details to the array
    $Profiles += [PSCustomObject]@{
        Folder      = $Folder
        CurrentName = $Name
        CleanName   = $CleanName
    }
}

# Sort profiles by their clean names alphabetically
$SortedProfiles = $Profiles | Sort-Object CleanName

# Display the new profile names
Write-Host ""
Write-Host "New profile names:"
Write-Host ""

# Initialize index for numbering
$Index = 1

# Apply new names to profiles
foreach ($Profile in $SortedProfiles) {
    $NewName = "{0:D2} - {1}" -f $Index, $Profile.CleanName

    Write-Host "$($Profile.CurrentName) -> $NewName"

    # Update the JSON with the new name
    $Json.profile.info_cache.$($Profile.Folder).name = $NewName

    $Index++
}

# Define a temporary path for the updated JSON
$TempPath = "$LocalStatePath.temp-$Timestamp"

# Write the updated JSON to the temp file
$Json |
    ConvertTo-Json -Depth 100 |
    Set-Content -Path $TempPath -Encoding UTF8

# Validate the written JSON by attempting to parse it back
try {
    Get-Content -Path $TempPath -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null
    # If valid, move temp file to replace the original
    Move-Item -Path $TempPath -Destination $LocalStatePath -Force
    Write-Host ""
    Write-Host "Done. Open Microsoft Edge and check the profile list."
    Write-Host "Backup file: $BackupPath"
} catch {
    # If invalid, remove temp file and throw error
    Remove-Item -Path $TempPath -ErrorAction SilentlyContinue
    throw "Validation failed: The new Local State JSON is invalid and was not applied."
}