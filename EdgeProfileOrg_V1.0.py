#!/usr/bin/env python3
"""
Script to rename Microsoft Edge profiles with alphabetically sorted numeric prefixes.
This script organizes Microsoft Edge profiles on macOS by renaming them with numeric prefixes
based on alphabetical order of their names. For example, "Profile A" becomes "01 - Profile A",
"Profile B" becomes "02 - Profile B", and so on.

Features:
- Automatically detects existing profiles from Edge's Local State file.
- Removes any existing numeric prefixes before re-applying them in sorted order.
- Creates a timestamped backup of the Local State file before making changes.
- Sorts profiles case-insensitively for consistent ordering.

Prerequisites:
- macOS operating system.
- Python 3 installed.
- Microsoft Edge browser installed and configured with profiles.

Usage:
1. Close Microsoft Edge completely to avoid conflicts:
   Run: osascript -e 'quit app "Microsoft Edge"'

2. Run the script:
   python3 the below script as: EdgeProfileOrg_V1.0.py

3. After the script completes, reopen Microsoft Edge and verify the profile names in the profile switcher.

Warnings:
- This script modifies Edge's configuration files. 
- If Edge is running while the script executes, changes may not take effect or could cause issues.
- Test on a non-critical setup first.

Troubleshooting:
- If "Local State not found" error occurs, ensure Edge is installed and has been run at least once.
- If no profiles are found, check that profiles exist in Edge.
- In case of errors, restore from the backup file created by the script.

Version: 1.0 - 11.05.2026
Author: Alexander Christensen - www.using-it.dk
"""
import json
import shutil
from pathlib import Path
from datetime import datetime

# Path to Microsoft Edge's Local State configuration file
local_state = Path.home() / "Library/Application Support/Microsoft Edge/Local State"

# Verify the Local State file exists
if not local_state.exists():
    raise SystemExit(f"Local State not found: {local_state}")

# Create a timestamped backup before making changes
backup = local_state.with_name(
    f"Local State.backup-before-profile-prefix-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
)

shutil.copy2(local_state, backup)
print(f"Backup created: {backup}")

# Load the Local State JSON file
with local_state.open("r", encoding="utf-8") as f:
    data = json.load(f)

# Extract profile info cache from the config
info_cache = data.get("profile", {}).get("info_cache", {})

if not info_cache:
    raise SystemExit("No Edge profiles found in Local State.")

profiles = []

def has_numeric_prefix(name):
    """Check if the name starts with a numeric prefix like '01 - '."""
    return len(name) > 5 and name[:2].isdigit() and name[2:5] == " - "

# Extract profile information and clean up existing prefixes
for folder, info in info_cache.items():
    name = info.get("name", folder)
    clean_name = name

    # Remove existing numeric prefix, e.g. "01 - "
    if has_numeric_prefix(name):
        clean_name = name[5:]

    profiles.append({
        "folder": folder,
        "current_name": name,
        "clean_name": clean_name
    })

# Sort profiles alphabetically by clean name (case-insensitive)
profiles_sorted = sorted(profiles, key=lambda x: x["clean_name"].casefold())

print("\nNew profile names:\n")

# Assign new numeric prefixes (01, 02, 03...) based on alphabetical order
for idx, profile in enumerate(profiles_sorted, 1):
    new_name = f"{idx:02d} - {profile['clean_name']}"
    folder = profile["folder"]
    print(f"{profile['current_name']} -> {new_name}")
    try:
        # Update the profile name in the data structure
        data["profile"]["info_cache"][folder]["name"] = new_name
    except (KeyError, TypeError):
        print(f"Warning: Could not update name for profile folder '{folder}'. Structure missing or malformed.")

# Write the updated configuration back to the Local State file
with local_state.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)

print("\nDone. Open Microsoft Edge and check the profile list.")
print(f"Backup file: {backup}") 