import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load_artifact_inspector():
    path = ROOT / "scripts" / "inspect_python_artifacts.py"
    spec = importlib.util.spec_from_file_location("artifact_inspector", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_metadata_contract_normalizes_platform_line_endings():
    inspector = load_artifact_inspector()
    headers = (
        "Metadata-Version: 2.4\n"
        "Name: fast-iso8601-rs\n"
        "Version: 0.1.0\n"
        "Summary: Fast Rust-backed drop-in replacement for iso8601 2.1.0\n"
        "Author: fast-iso8601-rs contributors\n"
        "License-Expression: MIT\n"
        "License-File: LICENSE\n"
        "Requires-Python: >=3.7,<4\n\n"
    )
    lf = (headers + "# fast-iso8601-rs\n\nEvidence.\n").encode()
    crlf = (headers + "# fast-iso8601-rs\r\n\r\nEvidence.\r\n").encode()
    assert inspector.metadata_contract(lf) == inspector.metadata_contract(crlf)


def test_artifact_inspector_help():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "inspect_python_artifacts.py"), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--expected-native-wheels" in result.stdout


def test_checksum_writer_help():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_checksums.py"), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--artifact-dir" in result.stdout


def test_benchmark_help():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_benchmark.py"), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--artifact" in result.stdout
