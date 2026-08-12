#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
python_bin=${PYTHON:-python3}
python_bin=$($python_bin -c 'import sys; print(sys.executable)')
test_file="$repo_root/upstream/iso8601/test_iso8601.py"

actual_hash=$(shasum -a 256 "$test_file" | awk '{print $1}')
test "$actual_hash" = "c66876357326d5c5ed52d7059055c41c4d89db791645d1fad05b7f5d3f9732ee"

candidate_package=$(
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
print(os.path.dirname(actual))
PY
)

printf '%s\n' "$candidate_package" | sed -n '1p'
candidate_package=$(printf '%s\n' "$candidate_package" | tail -n 1)
test -d "$candidate_package"

# The frozen test uses `from . import iso8601`. Running it in the frozen
# package would silently bind that relative import to the oracle itself. Copy
# the exact, hash-checked test bytes next to the installed candidate so pytest
# resolves the relative import against the wheel under test. The copy is a
# transient test fixture and is always removed.
installed_test="$candidate_package/_fast_iso8601_upstream_test.py"
test ! -e "$installed_test"
cp "$test_file" "$installed_test"
cleanup() { rm -f "$installed_test"; }
trap cleanup EXIT HUP INT TERM

installed_hash=$(shasum -a 256 "$installed_test" | awk '{print $1}')
test "$installed_hash" = "$actual_hash"

CANDIDATE_PACKAGE="$candidate_package" "$python_bin" - <<'PY'
import importlib
import os

test_module = importlib.import_module("iso8601._fast_iso8601_upstream_test")
bound = test_module.iso8601
expected = os.path.realpath(os.environ["CANDIDATE_PACKAGE"])
actual = os.path.realpath(bound.__file__)
if not actual.startswith(expected + os.sep):
    raise SystemExit("upstream test escaped installed candidate: %s" % actual)
if bound is not importlib.import_module("iso8601.iso8601"):
    raise SystemExit("upstream test did not bind candidate submodule")
print("upstream test binding:", actual)
PY

cd "$(dirname "$candidate_package")"
"$python_bin" -m pytest --import-mode=importlib -q "$installed_test"
