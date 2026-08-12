#!/usr/bin/env python3
import argparse
import hashlib
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifacts = sorted(
        path
        for path in args.artifact_dir.iterdir()
        if path.suffix == ".whl" or path.name.endswith(".tar.gz")
    )
    if not artifacts:
        raise SystemExit("no Python artifacts found")
    lines = [
        "%s  %s" % (hashlib.sha256(path.read_bytes()).hexdigest(), path.name)
        for path in artifacts
    ]
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("checksums: PASS artifacts=%d" % len(artifacts))


if __name__ == "__main__":
    main()

