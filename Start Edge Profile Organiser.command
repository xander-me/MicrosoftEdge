#!/bin/bash
# Author: Using-IT
project_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
"$project_dir/scripts/launch-mac.sh" "$@"
result=$?
if [[ $result -ne 0 ]]; then read -r -p 'Press Enter to close… ' unused; fi
exit "$result"
