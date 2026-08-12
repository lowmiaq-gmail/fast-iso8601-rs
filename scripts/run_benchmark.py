#!/usr/bin/env python3
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import math
from pathlib import Path
import platform
import statistics
import sys
import time


ROOT = Path(__file__).resolve().parents[1]


def load_oracle():
    path = ROOT / "upstream" / "iso8601" / "iso8601.py"
    spec = importlib.util.spec_from_file_location("benchmark_iso8601_oracle", str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load oracle")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def percentile95(values):
    return sorted(values)[max(0, math.ceil(0.95 * len(values)) - 1)]


def measure(function, value, iterations, repeats, warmup):
    for _ in range(warmup):
        function(value)
    samples = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        for _ in range(iterations):
            function(value)
        samples.append((time.perf_counter_ns() - start) / iterations)
    return {
        "raw_ns_per_call": samples,
        "median_ns_per_call": statistics.median(samples),
        "p95_ns_per_call": percentile95(samples),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=10000)
    parser.add_argument("--repeats", type=int, default=15)
    parser.add_argument("--warmup", type=int, default=1000)
    args = parser.parse_args()
    if min(args.iterations, args.repeats, args.warmup) < 1:
        raise SystemExit("iterations, repeats and warmup must be positive")

    import iso8601 as candidate

    artifact = args.artifact.resolve()
    native = importlib.util.find_spec("iso8601._native")
    assert native and native.origin and native.origin.endswith((".so", ".pyd"))
    assert importlib.metadata.version("fast-iso8601-rs") == "0.1.0"
    oracle = load_oracle()
    workloads = {
        "parse_utc": ("2026-08-12T10:30:45Z", oracle.parse_date, candidate.parse_date),
        "parse_offset_fraction": (
            "2026-08-12T10:30:45.123456789+05:45",
            oracle.parse_date,
            candidate.parse_date,
        ),
        "is_valid_compact": ("20260812T103045Z", oracle.is_iso8601, candidate.is_iso8601),
    }
    results = {}
    for name, (value, oracle_function, candidate_function) in workloads.items():
        expected = oracle_function(value)
        actual = candidate_function(value)
        assert expected == actual
        oracle_result = measure(
            oracle_function, value, args.iterations, args.repeats, args.warmup
        )
        candidate_result = measure(
            candidate_function, value, args.iterations, args.repeats, args.warmup
        )
        results[name] = {
            "input": value,
            "oracle": oracle_result,
            "candidate": candidate_result,
            "median_speedup": oracle_result["median_ns_per_call"]
            / candidate_result["median_ns_per_call"],
        }
    evidence = {
        "artifact": artifact.name,
        "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "iterations": args.iterations,
        "repeats": args.repeats,
        "warmup": args.warmup,
        "workloads": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Exact-Artifact Benchmark",
        "",
        "- artifact: `%s`" % evidence["artifact"],
        "- artifact SHA256: `%s`" % evidence["artifact_sha256"],
        "- Python: `%s`" % sys.version.splitlines()[0],
        "- platform: `%s`" % evidence["platform"],
        "- iterations/repeats/warmup: `%d / %d / %d`"
        % (args.iterations, args.repeats, args.warmup),
        "",
        "| Workload | Oracle median ns | Candidate median ns | Oracle p95 ns | Candidate p95 ns | Median speedup |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, result in results.items():
        lines.append(
            "| %s | %.2f | %.2f | %.2f | %.2f | %.2fx |"
            % (
                name,
                result["oracle"]["median_ns_per_call"],
                result["candidate"]["median_ns_per_call"],
                result["oracle"]["p95_ns_per_call"],
                result["candidate"]["p95_ns_per_call"],
                result["median_speedup"],
            )
        )
    lines.extend(
        [
            "",
            "The JSON evidence retains every raw sample and exact input. Results are specific to this artifact and machine.",
            "",
        ]
    )
    args.markdown.write_text("\n".join(lines), encoding="utf-8")
    print("benchmark: PASS workloads=%d raw_samples=%d" % (len(results), len(results) * args.repeats * 2))


if __name__ == "__main__":
    main()

