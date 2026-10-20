#!/bin/bash
# Source launcher; installed/bundled apps do not need this dependency setup.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$(uname -s)" != Darwin ]]; then
    echo 'This launcher is for macOS.' >&2
    exit 1
fi
usable_python() {
    [[ -x "$1" ]] && "$1" -c 'import sys; assert sys.version_info >= (3, 10); import tkinter' >/dev/null 2>&1
}
launch() {
    exec "$1" "$project_dir/ProfileOrg/EdgeProfileOrg_GUI.py" "${@:2}"
}
# Explicit paths also work when Finder has a minimal PATH.
for candidate in "${EDGE_ORGANIZER_PYTHON:-}" \
    /opt/homebrew/opt/python@3.14/bin/python3.14 \
    /usr/local/opt/python@3.14/bin/python3.14 \
    /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/*/bin/python3 \
    "$(command -v python3.14 || true)" "$(command -v python3 || true)"; do
    if [[ -n "$candidate" ]] && usable_python "$candidate"; then launch "$candidate" "$@"; fi
done
brew_path="$(command -v brew || true)"
for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [[ -z "$brew_path" && -x "$candidate" ]]; then brew_path="$candidate"; fi
done
if [[ -z "$brew_path" ]]; then
    /usr/bin/osascript -e 'display dialog "Python with Tk is needed for this source checkout. The standalone app includes both. To use this checkout, install Python using the official macOS installer, then double-click this launcher again." buttons {"Cancel", "Get Python"} default button "Get Python" cancel button "Cancel"' >/dev/null
    /usr/bin/open 'https://www.python.org/downloads/macos/'
    exit 0
fi
/usr/bin/osascript -e 'display dialog "Install the Python and Tk requirements with Homebrew? This runs brew install python-tk@3.14 and does not change Edge profiles." buttons {"Cancel", "Install and start"} default button "Install and start" cancel button "Cancel"' >/dev/null
if ! "$brew_path" install python-tk@3.14; then
    echo 'Dependency installation failed. Review the Homebrew error above; no Edge data was changed.' >&2
    exit 1
fi
runtime="$($brew_path --prefix python@3.14)/bin/python3.14"
if ! usable_python "$runtime"; then
    echo 'Python/Tk is still unavailable after installation. No Edge data was changed.' >&2
    exit 1
fi
launch "$runtime" "$@"
