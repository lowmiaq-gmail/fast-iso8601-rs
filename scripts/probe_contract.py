#!/usr/bin/env python3
import argparse
import datetime
import importlib.util
import inspect
import json
import sys
from pathlib import Path


def load_oracle(root):
    init_path = root / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "frozen_iso8601_oracle",
        str(init_path),
        submodule_search_locations=[str(root)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen oracle")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def decode_value(value):
    kind = value["kind"]
    payload = value.get("value")
    if kind == "str":
        return payload
    if kind == "none":
        return None
    if kind == "int":
        return payload
    if kind == "bytes":
        return bytes(payload)
    if kind == "timezone":
        return datetime.timezone(
            datetime.timedelta(minutes=payload["minutes"]), payload["name"]
        )
    raise ValueError("unknown value kind: %s" % kind)


def observe_exception(error):
    return {
        "outcome": "error",
        "type": type(error).__name__,
        "message": str(error),
        "arg_types": [type(value).__name__ for value in error.args],
        "arg_messages": [str(value) for value in error.args],
        "cause": type(error.__cause__).__name__ if error.__cause__ else None,
        "context": type(error.__context__).__name__ if error.__context__ else None,
    }


def observe_value(value, module):
    if isinstance(value, datetime.datetime):
        offset = value.utcoffset()
        return {
            "outcome": "return",
            "type": "datetime",
            "isoformat": value.isoformat(),
            "fold": value.fold,
            "tz_type": type(value.tzinfo).__name__ if value.tzinfo else None,
            "tzname": value.tzname(),
            "offset_seconds": offset.total_seconds() if offset is not None else None,
            "utc_identity": value.tzinfo is module.UTC,
        }
    if isinstance(value, datetime.tzinfo):
        offset = value.utcoffset(None)
        return {
            "outcome": "return",
            "type": type(value).__name__,
            "tzname": value.tzname(None),
            "offset_seconds": offset.total_seconds() if offset is not None else None,
            "utc_identity": value is module.UTC,
        }
    return {"outcome": "return", "type": type(value).__name__, "value": value}


def observe_call(module, case):
    function = getattr(
        module.iso8601 if case["function"] == "parse_timezone" else module,
        case["function"],
    )
    args = [decode_value(value) for value in case.get("args", [])]
    kwargs = {
        key: decode_value(value) for key, value in case.get("kwargs", {}).items()
    }
    try:
        return observe_value(function(*args, **kwargs), module)
    except Exception as error:
        return observe_exception(error)


def observe_metadata(module, name):
    function = getattr(module.iso8601, name)
    return {
        "outcome": "metadata",
        "signature": str(inspect.signature(function)),
        "doc": function.__doc__,
        "annotations": repr(function.__annotations__),
        "defaults": repr(function.__defaults__),
        "kwdefaults": repr(function.__kwdefaults__),
        "name": function.__name__,
        "qualname": function.__qualname__,
    }


def observe_regex(module):
    regex = module.iso8601.ISO8601_REGEX
    return {
        "outcome": "regex",
        "pattern": regex.pattern,
        "flags": regex.flags,
        "groups": regex.groups,
        "groupindex": sorted(regex.groupindex.items()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--oracle-root", type=Path)
    args = parser.parse_args()

    if args.oracle_root:
        module = load_oracle(args.oracle_root)
    else:
        import iso8601 as module

    records = []
    with args.corpus.open(encoding="utf-8") as handle:
        for line in handle:
            case = json.loads(line)
            if case["kind"] == "call":
                records.append(observe_call(module, case))
            elif case["kind"] == "metadata":
                records.append(observe_metadata(module, case["name"]))
            elif case["kind"] == "regex":
                records.append(observe_regex(module))
            else:
                raise ValueError("unknown case: %r" % case)
    args.output.write_text(
        "\n".join(json.dumps(item, sort_keys=True) for item in records) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
