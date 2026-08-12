#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
python_bin=${PYTHON:-python3}
driver="$repo_root/scripts/run_upstream_full.py"
if command -v cygpath >/dev/null 2>&1; then
    driver=$(cygpath -w "$driver")
fi
exec "$python_bin" "$driver"
