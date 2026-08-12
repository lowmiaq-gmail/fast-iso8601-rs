#!/usr/bin/env python3
import argparse
import json
import random
import string
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED = 20260812
DEFAULT_CASES = 10_000


def encoded(kind, value=None):
    return {"kind": kind, "value": value}


def call(function, value, default_marker=None):
    case = {"kind": "call", "function": function, "args": [value]}
    if default_marker is not None:
        case["kwargs"] = {"default_timezone": default_marker}
    return case


def valid_string(rng, index):
    year = rng.randint(1, 9999)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    precision = index % 12
    if precision == 0:
        return "%04d" % year
    if precision == 1:
        return "%04d-%d" % (year, month)
    compact = precision in (2, 5, 8, 11)
    if compact:
        result = "%04d%02d%02d" % (year, month, day)
    else:
        result = "%04d-%d-%d" % (year, month, day)
    if precision == 2:
        return result
    hour = rng.randint(0, 23)
    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)
    separator = rng.choice(["T", " "])
    style = index % 4
    if style == 0:
        time = "%02d" % hour
    elif style == 1:
        time = "%02d%02d" % (hour, minute)
    elif style == 2:
        time = "%02d:%02d:%d" % (hour, minute, second)
    else:
        digits = "".join(str(rng.randrange(10)) for _ in range(1 + index % 12))
        time = "%02d%02d%02d%s%s" % (
            hour,
            minute,
            second,
            rng.choice([".", ","]),
            digits,
        )
    zone_style = index % 5
    if zone_style == 0:
        zone = ""
    elif zone_style == 1:
        zone = "Z"
    else:
        sign = rng.choice(["+", "-"])
        zone_hour = rng.randint(0, 23)
        zone_minute = rng.randint(0, 59)
        zone = rng.choice(
            [
                "%s%02d" % (sign, zone_hour),
                "%s%02d%02d" % (sign, zone_hour, zone_minute),
                "%s%02d:%02d" % (sign, zone_hour, zone_minute),
            ]
        )
    return result + separator + time + zone


def generate_cases(count):
    rng = random.Random(SEED)
    cases = [
        {"kind": "metadata", "name": name}
        for name in ("FixedOffset", "parse_timezone", "parse_date", "is_iso8601")
    ]
    cases.append({"kind": "regex"})
    dynamic = [encoded("none"), encoded("int", 7), encoded("bytes", [50, 48, 50, 48])]
    for value in dynamic:
        cases.append(call("parse_date", value))
        cases.append(call("is_iso8601", value))
    cases.extend(
        [
            {
                "kind": "call",
                "function": "parse_timezone",
                "args": [encoded("none")],
            },
            {
                "kind": "call",
                "function": "FixedOffset",
                "args": [encoded("int", -3), encoded("int", -30), encoded("str", "-03:30")],
            },
        ]
    )

    valid_values = []
    while len(cases) < count // 2:
        value = valid_string(rng, len(valid_values))
        valid_values.append(value)
        default = None
        if len(valid_values) % 7 == 0:
            default = encoded("none")
        elif len(valid_values) % 11 == 0:
            default = encoded(
                "timezone", {"minutes": 345, "name": "custom-default"}
            )
        cases.append(call("is_iso8601", encoded("str", value)))
        if len(cases) < count // 2:
            cases.append(call("parse_date", encoded("str", value), default))

    alphabet = string.ascii_letters + string.digits + "-+:., TZ_/@\n\r"
    mutation_index = 0
    while len(cases) < count:
        base = valid_values[mutation_index % len(valid_values)]
        mutation_index += 1
        mode = mutation_index % 4
        if mode == 0:
            position = rng.randrange(len(base) + 1)
            value = base[:position] + rng.choice("X_/@") + base[position:]
        elif mode == 1:
            value = base[: rng.randrange(len(base) + 1)]
        elif mode == 2:
            value = "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 36)))
        else:
            value = base + rng.choice(["rubbish", "\n\n", ":", "+99:99"])
        function = "parse_date" if len(cases) % 2 else "is_iso8601"
        cases.append(call(function, encoded("str", value)))
    return cases[:count]


def run_probe(python, corpus, output, oracle_root=None):
    command = [
        str(python.absolute()),
        str(ROOT / "scripts" / "probe_contract.py"),
        "--corpus",
        str(corpus),
        "--output",
        str(output),
    ]
    if oracle_root is not None:
        command.extend(["--oracle-root", str(oracle_root)])
    subprocess.run(command, cwd=tempfile.gettempdir(), check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-python", type=Path, required=True)
    parser.add_argument("--candidate-python", type=Path, required=True)
    parser.add_argument("--cases", type=int, default=DEFAULT_CASES)
    args = parser.parse_args()
    if args.cases < 1:
        raise SystemExit("--cases must be positive")

    with tempfile.TemporaryDirectory(prefix="fast-iso8601-diff-") as directory:
        temporary = Path(directory)
        corpus = temporary / "corpus.jsonl"
        oracle_output = temporary / "oracle.jsonl"
        candidate_output = temporary / "candidate.jsonl"
        cases = generate_cases(args.cases)
        corpus.write_text(
            "\n".join(json.dumps(case, sort_keys=True) for case in cases) + "\n",
            encoding="utf-8",
        )
        run_probe(
            args.oracle_python,
            corpus,
            oracle_output,
            ROOT / "upstream" / "iso8601",
        )
        run_probe(args.candidate_python, corpus, candidate_output)
        oracle_lines = oracle_output.read_text(encoding="utf-8").splitlines()
        candidate_lines = candidate_output.read_text(encoding="utf-8").splitlines()
        if oracle_lines != candidate_lines:
            for index, pair in enumerate(zip(oracle_lines, candidate_lines)):
                if pair[0] != pair[1]:
                    raise AssertionError(
                        "differential mismatch at case %d:\n  oracle=%s\n  candidate=%s"
                        % (index, pair[0], pair[1])
                    )
            raise AssertionError(
                "differential cardinality mismatch: oracle=%d candidate=%d"
                % (len(oracle_lines), len(candidate_lines))
            )
        print("differential: PASS seed=%d cases=%d" % (SEED, len(cases)))


if __name__ == "__main__":
    main()
