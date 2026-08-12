import copy
import datetime
import importlib.util
import inspect
import os
import pickle
from pathlib import Path

import pytest

import iso8601
import iso8601.iso8601 as candidate


def load_oracle():
    path = Path(__file__).parents[1] / "upstream" / "iso8601" / "iso8601.py"
    spec = importlib.util.spec_from_file_location("frozen_iso8601_oracle", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_namespace_and_export_contract():
    assert iso8601.__all__ == [
        "parse_date",
        "is_iso8601",
        "ParseError",
        "UTC",
        "FixedOffset",
    ]
    assert candidate.__all__ == ["parse_date", "ParseError", "UTC", "FixedOffset"]
    assert not hasattr(iso8601, "__version__")
    assert iso8601.parse_date is candidate.parse_date
    assert iso8601.is_iso8601 is candidate.is_iso8601
    assert iso8601.ParseError is candidate.ParseError
    assert iso8601.FixedOffset is candidate.FixedOffset
    assert iso8601.UTC is candidate.UTC is datetime.timezone.utc


def test_root_and_submodule_star_imports():
    root = {}
    submodule = {}
    exec("from iso8601 import *", root)
    exec("from iso8601.iso8601 import *", submodule)
    assert {key for key in root if not key.startswith("_")} == set(iso8601.__all__)
    assert {key for key in submodule if not key.startswith("_")} == set(
        candidate.__all__
    )
    assert "is_iso8601" not in submodule
    assert "parse_timezone" not in submodule
    assert "ISO8601_REGEX" not in submodule


@pytest.mark.parametrize(
    "name", ["FixedOffset", "parse_timezone", "parse_date", "is_iso8601"]
)
def test_callable_metadata_matches_frozen_source(name):
    oracle = getattr(load_oracle(), name)
    actual = getattr(candidate, name)
    assert inspect.signature(actual) == inspect.signature(oracle)
    assert actual.__doc__ == oracle.__doc__
    assert actual.__annotations__ == oracle.__annotations__
    assert actual.__defaults__ == oracle.__defaults__
    assert actual.__kwdefaults__ == oracle.__kwdefaults__
    assert actual.__name__ == oracle.__name__
    assert actual.__qualname__ == oracle.__qualname__
    assert actual.__module__ == "iso8601.iso8601"


def test_class_metadata():
    assert candidate.ParseError.__module__ == "iso8601.iso8601"
    assert candidate.ParseError.__doc__ == load_oracle().ParseError.__doc__
    assert issubclass(candidate.ParseError, ValueError)


def test_regex_object_shape_and_named_groups():
    oracle = load_oracle().ISO8601_REGEX
    actual = candidate.ISO8601_REGEX
    assert type(actual) is type(oracle)
    assert actual.pattern == oracle.pattern
    assert actual.flags == oracle.flags == 96
    assert actual.groups == oracle.groups == 26
    assert actual.groupindex == oracle.groupindex == {
        "year": 1,
        "monthdash": 5,
        "month": 6,
        "daydash": 10,
        "day": 11,
        "separator": 14,
        "hour": 15,
        "minute": 17,
        "second": 19,
        "second_fraction": 21,
        "timezone": 22,
        "tz_sign": 24,
        "tz_hour": 25,
        "tz_minute": 26,
    }


@pytest.mark.parametrize("function", [candidate.parse_date, candidate.is_iso8601])
@pytest.mark.parametrize("value", [None, 1, b"2020-01-01", object()])
def test_dynamic_invalid_input_preserves_wrapped_exception(function, value):
    with pytest.raises(candidate.ParseError) as caught:
        function(value)
    error = caught.value
    assert len(error.args) == 1
    assert isinstance(error.args[0], TypeError)
    assert str(error) == str(error.args[0])
    assert error.__cause__ is None
    assert isinstance(error.__context__, TypeError)


@pytest.mark.parametrize("value", ["", "wibble", "201402", "2013-10-"])
def test_unmatched_error_message(value):
    assert candidate.is_iso8601(value) is False
    with pytest.raises(candidate.ParseError) as caught:
        candidate.parse_date(value)
    assert str(caught.value) == "Unable to parse date string %r" % value
    assert caught.value.__cause__ is None


def test_lexical_validation_and_datetime_error_are_distinct():
    value = "2024-99-99T99:99:99Z"
    assert candidate.is_iso8601(value) is True
    with pytest.raises(candidate.ParseError) as caught:
        candidate.parse_date(value)
    assert isinstance(caught.value.args[0], ValueError)
    assert str(caught.value) == str(caught.value.args[0])
    assert caught.value.__cause__ is None


def test_fraction_is_decimal_truncated_not_rounded():
    assert candidate.parse_date("2020-01-02T03:04:05.1234569Z").microsecond == 123456
    assert candidate.parse_date("2020-01-02T03:04:05,9999999Z").microsecond == 999999
    assert candidate.parse_date("2020-01-02T03:04:05.0000009Z").microsecond == 0


def test_default_timezone_identity_and_explicit_timezone_precedence():
    custom = datetime.timezone(datetime.timedelta(hours=5, minutes=45), "custom")
    naive_source = candidate.parse_date("2020-01-02T03:04:05", custom)
    assert naive_source.tzinfo is custom
    assert candidate.parse_date("2020-01-02T03:04:05", None).tzinfo is None
    assert candidate.parse_date("2020-01-02T03:04:05Z", custom).tzinfo is candidate.UTC


def test_fixed_offset_equality_name_and_zero_identity():
    value = candidate.FixedOffset(-3, -30, "-03:30")
    assert value == datetime.timezone(datetime.timedelta(hours=-3, minutes=-30))
    assert value.tzname(None) == "-03:30"
    explicit_zero = candidate.parse_date("2020-01-02T03:04:05+00:00").tzinfo
    assert explicit_zero == candidate.UTC
    assert explicit_zero is not candidate.UTC
    assert explicit_zero.tzname(None) == "+00:00"


def test_parse_timezone_direct_dynamic_mapping_behavior():
    default = datetime.timezone(datetime.timedelta(hours=2), "default")
    assert candidate.parse_timezone({}, default) is default
    assert candidate.parse_timezone({"timezone": "Z"}, default) is candidate.UTC
    assert candidate.parse_timezone(
        {"timezone": "+02:30", "tz_sign": "+", "tz_hour": "02", "tz_minute": "30"}
    ) == datetime.timezone(datetime.timedelta(hours=2, minutes=30))
    with pytest.raises(AttributeError):
        candidate.parse_timezone(None)


def test_datetime_deepcopy_pickle_and_roundtrip():
    value = candidate.parse_date("1997-08-29T06:14:00.000123+02:30")
    assert copy.deepcopy(value) == value
    assert pickle.loads(pickle.dumps(value)) == value
    assert candidate.parse_date(value.isoformat()) == value


def test_py_typed_is_packaged_next_to_module():
    marker = Path(iso8601.__file__).with_name("py.typed")
    assert marker.is_file()


def test_native_parser_is_loaded_from_extension():
    spec = importlib.util.find_spec("iso8601._native")
    if os.environ.get("EXPECT_NATIVE", "1") == "1":
        assert spec is not None and spec.origin is not None
        assert spec.origin.endswith((".so", ".pyd")), spec.origin
    else:
        assert spec is None
        assert iso8601.__file__.endswith(".py")
