#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
python_bin=${PYTHON:-python3}
test_file="$repo_root/upstream/iso8601/test_iso8601.py"

actual_hash=$(shasum -a 256 "$test_file" | awk '{print $1}')
test "$actual_hash" = "c66876357326d5c5ed52d7059055c41c4d89db791645d1fad05b7f5d3f9732ee"

"$python_bin" - <<'PY'
import importlib.util
import os
import iso8601

actual = os.path.realpath(iso8601.__file__)
expected = os.environ.get("CANDIDATE_EXPECTED_ROOT")
if expected and not actual.startswith(os.path.realpath(expected)):
    raise SystemExit("candidate import escaped expected root: %s" % actual)
if os.environ.get("CANDIDATE_REQUIRE_NATIVE") == "1":
    native = importlib.util.find_spec("iso8601._native")
    if not native or not native.origin or not native.origin.endswith((".so", ".pyd")):
        raise SystemExit("candidate native extension missing: %r" % (native,))
print("candidate import:", actual)
PY

# importlib mode lets the unchanged package-relative import bind to the already
# installed candidate while the frozen test bytes remain untouched.
cd "$(dirname "$repo_root")"
"$python_bin" -m pytest --import-mode=importlib -q "$test_file"

