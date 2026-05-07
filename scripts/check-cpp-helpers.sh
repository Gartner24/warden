#!/usr/bin/env bash
# Fails when a C++ helper name is defined in more than one .cpp under src/attacker/.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
mapfile -t hits < <(grep -rEhoP '^\w[\w:]*\s+(\w+)\s*\(' src/attacker --include='*.cpp' \
    | grep -oP '\b\w+(?=\s*\()' | sort | uniq -d)
if (( ${#hits[@]} > 0 )); then
    echo "Duplicate C++ helper definitions:" >&2
    printf '  %s\n' "${hits[@]}" >&2
    exit 1
fi
echo "OK: no duplicate C++ helper names."
