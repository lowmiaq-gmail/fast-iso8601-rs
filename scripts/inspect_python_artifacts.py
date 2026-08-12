#!/usr/bin/env python3
"""Audit native/fallback wheels and sdist as one immutable release set."""

import argparse
import base64
import csv
import email.parser
import hashlib
import io
from pathlib import Path, PurePosixPath
import tarfile
import zipfile

from packaging.specifiers import SpecifierSet


EXPECTED_NAME = "fast-iso8601-rs"
EXPECTED_VERSION = "0.1.0"


def safe_paths(names):
    for name in names:
        path = PurePosixPath(name)
        assert not path.is_absolute(), name
        assert ".." not in path.parts, name


def metadata_contract(raw):
    metadata = email.parser.BytesParser().parsebytes(raw)
    assert metadata["Name"] == EXPECTED_NAME
    assert metadata["Version"] == EXPECTED_VERSION
    assert metadata["Summary"] == "Fast Rust-backed drop-in replacement for iso8601 2.1.0"
    assert metadata["Author"] == "fast-iso8601-rs contributors"
    assert metadata["License-Expression"] == "MIT"
    assert set(metadata.get_all("License-File", [])) == {"LICENSE"}
    assert SpecifierSet(metadata["Requires-Python"]) == SpecifierSet(">=3.7,<4")
    assert not metadata.get_all("Dynamic", [])
    assert not [
        value
        for value in metadata.get_all("Requires-Dist", [])
        if "extra ==" not in value
    ]
    return (
        metadata["Name"],
        metadata["Version"],
        str(SpecifierSet(metadata["Requires-Python"])),
        metadata["Summary"],
        metadata.get_payload().rstrip("\n"),
    )


def verify_record(archive, names):
    record_names = [name for name in names if name.endswith(".dist-info/RECORD")]
    assert len(record_names) == 1, record_names
    record_name = record_names[0]
    rows = list(csv.reader(io.StringIO(archive.read(record_name).decode("utf-8"))))
    assert {row[0].replace("\\", "/") for row in rows} == set(names)
    for path, encoded_hash, encoded_size in rows:
        path = path.replace("\\", "/")
        if path == record_name:
            assert encoded_hash == encoded_size == ""
            continue
        payload = archive.read(path)
        algorithm, expected = encoded_hash.split("=", 1)
        actual = base64.urlsafe_b64encode(hashlib.new(algorithm, payload).digest())
        assert actual.rstrip(b"=").decode("ascii") == expected, path
        assert len(payload) == int(encoded_size), path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--expected-native-wheels", type=int, required=True)
    args = parser.parse_args()
    root = args.repository_root.resolve()
    wheels = sorted(args.artifact_dir.glob("*.whl"))
    sdists = sorted(args.artifact_dir.glob("*.tar.gz"))
    fallback = [path for path in wheels if path.name.endswith("-py3-none-any.whl")]
    native = [path for path in wheels if path not in fallback]
    assert len(fallback) == 1, fallback
    assert len(native) == args.expected_native_wheels, native
    assert len(sdists) == 1, sdists
    assert len({path.name for path in wheels + sdists}) == len(wheels) + len(sdists)

    metadata_values = set()
    forbidden = (str(root), "/home/runner/work/", "/workspace/", "target/debug", "target/release")
    for wheel in wheels:
        with zipfile.ZipFile(str(wheel)) as archive:
            names = archive.namelist()
            safe_paths(names)
            assert "iso8601/__init__.py" in names
            assert "iso8601/iso8601.py" in names
            assert "iso8601/py.typed" in names
            assert not any(name.endswith((".pyc", ".pyo")) or "/tests/" in "/" + name for name in names)
            metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
            assert len(metadata_names) == 1
            metadata_values.add(metadata_contract(archive.read(metadata_names[0])))
            verify_record(archive, names)
            native_files = [name for name in names if name.endswith((".so", ".pyd"))]
            if wheel in fallback:
                assert not native_files
            else:
                assert len(native_files) == 1, native_files
                assert native_files[0].startswith("iso8601/_native")
                assert "-abi3-" in wheel.name
            for name in names:
                if name.endswith((".py", ".md", ".toml", ".txt", ".json")):
                    text = archive.read(name).decode("utf-8", errors="ignore")
                    assert not any(value in text for value in forbidden), name

    with tarfile.open(str(sdists[0]), "r:gz") as archive:
        names = archive.getnames()
        safe_paths(names)
        assert not any(
            marker in "/" + name
            for name in names
            for marker in ("/target/", "/.venv/", "/__pycache__/", ".egg-info/")
        )
        for suffix in (
            "/Cargo.toml",
            "/pyproject.toml",
            "/src/lib.rs",
            "/python/iso8601/__init__.py",
            "/fallback/iso8601/iso8601.py",
        ):
            assert any(name.endswith(suffix) for name in names), suffix
        members = [
            member
            for member in archive.getmembers()
            if member.name.endswith("/PKG-INFO")
            and len(PurePosixPath(member.name).parts) == 2
        ]
        assert len(members) == 1
        stream = archive.extractfile(members[0])
        assert stream is not None
        metadata_values.add(metadata_contract(stream.read()))
    assert len(metadata_values) == 1, "artifact metadata differs"
    print(
        "artifact audit: PASS native=%d fallback=1 sdist=1"
        % args.expected_native_wheels
    )


if __name__ == "__main__":
    main()
