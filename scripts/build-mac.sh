#!/bin/bash
# Author: Using-IT
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
if [[ "$(uname -s)" != Darwin ]]; then echo 'Build this app on macOS.' >&2; exit 1; fi
runtime="${EDGE_ORGANIZER_PYTHON:-python3}"
"$runtime" -c 'import tkinter' || { echo 'Build Python must include Tk.' >&2; exit 1; }
"$runtime" -m venv .build-mac
.build-mac/bin/python -m pip install --disable-pip-version-check -r requirements-build.txt
.build-mac/bin/python -m PyInstaller --noconfirm --clean --windowed --onedir \
    --name 'Edge Profile Organiser' \
    --osx-bundle-identifier dk.using-it.edge-profile-organiser \
    --paths ProfileOrg ProfileOrg/EdgeProfileOrg_GUI.py
# Separate double-click demo app; no command-line arguments needed.
.build-mac/bin/python -m PyInstaller --noconfirm --clean --windowed --onedir \
    --name 'Edge Profile Organiser Demo' \
    --osx-bundle-identifier dk.using-it.edge-profile-organiser.demo \
    --paths ProfileOrg scripts/demo_entry.py
