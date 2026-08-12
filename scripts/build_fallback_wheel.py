#!/usr/bin/env python3
"""Build the canonical universal fallback wheel from root metadata."""

import argparse
import base64
import csv
import hashlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def record_hash(payload):
    digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest())
    return "sha256=" + digest.rstrip(b"=").decode("ascii")


def normalize_static_metadata(wheel):
    with zipfile.ZipFile(str(wheel)) as archive:
        infos = archive.infolist()
        payloads = {info.filename: archive.read(info.filename) for info in infos}
    metadata_names = [name for name in payloads if name.endswith(".dist-info/METADATA")]
    record_names = [name for name in payloads if name.endswith(".dist-info/RECORD")]
    if len(metadata_names) != 1 or len(record_names) != 1:
        raise SystemExit("fallback wheel has invalid dist-info layout")
    metadata_name = metadata_names[0]
    lines = [
        line
        for line in payloads[metadata_name].decode("utf-8").splitlines(True)
        if not line.startswith("Dynamic:")
    ]
    payloads[metadata_name] = "".join(lines).encode("utf-8")
    record_name = record_names[0]
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    for info in infos:
        name = info.filename
        if name == record_name:
            continue
        payload = payloads[name]
        writer.writerow((name, record_hash(payload), str(len(payload))))
    writer.writerow((record_name, "", ""))
    payloads[record_name] = output.getvalue().encode("utf-8")
    normalized = wheel.with_suffix(".normalized.whl")
    with zipfile.ZipFile(str(normalized), "w") as archive:
        for info in infos:
            archive.writestr(info, payloads[info.filename])
    normalized.replace(wheel)


def fallback_pyproject():
    source = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    project = source[source.index("[project]\n") : source.index("[tool.maturin]\n")].rstrip()
    return "\n".join(
        (
            "[build-system]",
            'requires = ["setuptools>=77", "wheel"]',
            'build-backend = "setuptools.build_meta"',
            "",
            project,
            "",
            "[tool.setuptools.packages.find]",
            'where = ["."]',
            'include = ["iso8601*"]',
            "",
            "[tool.setuptools.package-data]",
            'iso8601 = ["py.typed"]',
            "",
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.out_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fast-iso8601-fallback-build-") as tmp:
        staging = Path(tmp)
        (staging / "pyproject.toml").write_text(fallback_pyproject(), encoding="utf-8")
        for relative in ("README.md", "LICENSE"):
            shutil.copy2(str(ROOT / relative), str(staging / relative))
        shutil.copytree(str(ROOT / "fallback" / "iso8601"), str(staging / "iso8601"))
        subprocess.run(
            [
                sys.executable,
                "-m",
                "build",
                "--wheel",
                "--no-isolation",
                "--outdir",
                str(output),
            ],
            cwd=str(staging),
            check=True,
        )
    wheels = sorted(output.glob("*-py3-none-any.whl"))
    if len(wheels) != 1:
        raise SystemExit("expected one fallback wheel, found: %r" % wheels)
    normalize_static_metadata(wheels[0])
    print(wheels[0])


if __name__ == "__main__":
    main()

