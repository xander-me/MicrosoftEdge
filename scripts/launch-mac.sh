#!/bin/bash
# Author: Using-IT
# Terminal launcher: Python standard library only; no Tk, pip or Homebrew setup.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$(uname -s)" != Darwin ]]; then echo 'This launcher is for macOS.' >&2; exit 1; fi
usable_python() {
    [[ -x "$1" ]] && "$1" -c 'import sys; assert sys.version_info >= (3, 10)' >/dev/null 2>&1
}
for candidate in "${EDGE_ORGANIZER_PYTHON:-}" "$(command -v python3 || true)" \
    /opt/homebrew/bin/python3 /usr/local/bin/python3 \
    /opt/homebrew/opt/python@3.14/bin/python3.14 \
    /usr/local/opt/python@3.14/bin/python3.14 \
    /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/*/bin/python3; do
    if [[ -n "$candidate" ]] && usable_python "$candidate"; then
        exec "$candidate" "$project_dir/ProfileOrg/EdgeProfileOrg_V1.0.py" "$@"
    fi
done
echo 'Python 3.10+ is required. Install Python from https://www.python.org/downloads/macos/ and run this launcher again.' >&2
exit 1
