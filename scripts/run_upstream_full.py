#!/usr/bin/env python3
"""Run the exact frozen upstream suite against the installed candidate."""

import hashlib
import importlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys


EXPECTED_HASH = "c66876357326d5c5ed52d7059055c41c4d89db791645d1fad05b7f5d3f9732ee"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_within(path, root):
    path_text = os.path.normcase(str(path.resolve()))
    root_text = os.path.normcase(str(root.resolve()))
    try:
        return os.path.commonpath([path_text, root_text]) == root_text
    except ValueError:
        return False


def main():
    repo_root = Path(__file__).resolve().parent.parent
    frozen_test = repo_root / "upstream" / "iso8601" / "test_iso8601.py"
    actual_hash = sha256(frozen_test)
    if actual_hash != EXPECTED_HASH:
        raise SystemExit("frozen upstream test hash mismatch: %s" % actual_hash)

    import iso8601

    candidate_init = Path(iso8601.__file__).resolve()
    expected_root_value = os.environ.get("CANDIDATE_EXPECTED_ROOT")
    if expected_root_value and not is_within(candidate_init, Path(expected_root_value)):
        raise SystemExit("candidate import escaped expected root: %s" % candidate_init)

    if os.environ.get("CANDIDATE_REQUIRE_NATIVE") == "1":
        native = importlib.util.find_spec("iso8601._native")
        if not native or not native.origin or not native.origin.endswith((".so", ".pyd")):
            raise SystemExit("candidate native extension missing: %r" % (native,))

    candidate_package = candidate_init.parent
    installed_test = candidate_package / "_fast_iso8601_upstream_test.py"
    if installed_test.exists():
        raise SystemExit("transient upstream test already exists: %s" % installed_test)

    print("candidate import:", candidate_init)
    shutil.copyfile(str(frozen_test), str(installed_test))
    try:
        installed_hash = sha256(installed_test)
        if installed_hash != actual_hash:
            raise SystemExit("installed upstream test hash mismatch: %s" % installed_hash)

        test_module = importlib.import_module("iso8601._fast_iso8601_upstream_test")
        bound = test_module.iso8601
        bound_path = Path(bound.__file__).resolve()
        if not is_within(bound_path, candidate_package):
            raise SystemExit("upstream test escaped installed candidate: %s" % bound_path)
        if bound is not importlib.import_module("iso8601.iso8601"):
            raise SystemExit("upstream test did not bind candidate submodule")
        print("upstream test binding:", bound_path)

        return subprocess.call(
            [
                sys.executable,
                "-m",
                "pytest",
                "--import-mode=importlib",
                "-q",
                str(installed_test),
            ],
            cwd=str(candidate_package.parent),
        )
    finally:
        try:
            installed_test.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    sys.exit(main())
