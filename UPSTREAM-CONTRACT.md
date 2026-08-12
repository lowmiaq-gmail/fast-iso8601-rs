# Frozen Upstream Contract

## Provenance

- distribution/import: `iso8601==2.1.0` / `iso8601`;
- repository/tag/commit: `micktwomey/pyiso8601`, `2.1.0`,
  `c147acc8952bf279a38d5cab1f80be71735a10cf`;
- local oracle: `upstream/`, independently extracted from the fixed PyPI sdist;
- sdist SHA256: `6b1d3829ee8921c4301998c909f7829fa9ed3cbdac0d3b16af2d743aed1ba8df`;
- wheel SHA256: `aac4145c4dcb66ad8b648a02830f5e2ff6c24af20f4f482689be402db2429242`;
- license: MIT; Python: `>=3.7,<4.0`; runtime dependencies: none.

## Namespace and exports

- `iso8601.__all__ == ["parse_date", "is_iso8601", "ParseError", "UTC", "FixedOffset"]`;
- `iso8601.iso8601.__all__ == ["parse_date", "ParseError", "UTC", "FixedOffset"]`;
- `parse_timezone`, `is_iso8601` and `ISO8601_REGEX` remain directly importable
  from `iso8601.iso8601`, but submodule star import excludes all three;
- there is no `__version__`; root re-exports are identical objects from the submodule;
- `py.typed` is shipped.

## Callable and object contract

- `FixedOffset(offset_hours: float, offset_minutes: float, name: str) -> datetime.timezone`;
- `parse_timezone(matches: Dict[str, str], default_timezone: Optional[datetime.timezone] = UTC) -> Optional[datetime.timezone]`;
- `parse_date(datestring: str, default_timezone: Optional[datetime.timezone] = UTC) -> datetime.datetime`;
- `is_iso8601(datestring: str) -> bool`;
- source signatures, defaults, annotations, docs and `__module__` metadata are preserved;
- `ParseError` is a `ValueError` subclass defined in `iso8601.iso8601`;
- `UTC is datetime.timezone.utc`, and root/submodule `UTC` have object identity;
- explicit numeric offsets are `datetime.timezone` instances with normalized names;
- caller-provided default tzinfo is returned by identity when no timezone is present;
- returned datetimes retain standard equality, deepcopy and pickle behavior.

## Regex and parsing semantics

- `ISO8601_REGEX` is a real `re.Pattern`, flags `96`, groups `26`, with exact
  named-group indexes for year/month/day/time/fraction/timezone components;
- supported forms include reduced year/month precision, compact and dashed dates,
  space or `T`, compact/colon time, dot/comma fractions, `Z`, `+hh`, `+hhmm`,
  `+hh:mm`, and their negative forms;
- fractional seconds use `Decimal` then `int`, preserving truncation beyond six digits;
- `is_iso8601` is lexical: calendar-invalid but regex-shaped strings can be true;
- datetime construction failures become `ParseError(original_exception)`;
- regex/type failures become `ParseError(original_exception)`, retaining
  `args == (original_exception,)`, `__cause__ is None`, and implicit context;
- unmatched strings become `ParseError("Unable to parse date string ...")`.

## Frozen suite

`upstream/iso8601/test_iso8601.py` is run unchanged against the installed
candidate. It contains fixed examples plus Hypothesis naive/timezone-aware
round trips. Candidate-only tests cover metadata and edge behavior absent there.

