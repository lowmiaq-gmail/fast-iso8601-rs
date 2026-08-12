import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]


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

