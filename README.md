# fast-iso8601-rs

Rust-backed complete drop-in replacement for the frozen public and behavioral
contract of [`iso8601==2.1.0`](https://github.com/micktwomey/pyiso8601/tree/2.1.0).
It keeps the `iso8601` import namespace, call signatures, typing marker,
`datetime`/timezone semantics and exception behavior. The native wheel moves
the lexical parse and capture extraction into Rust; a universal pure-Python
wheel supports Python 3.7 and platforms without a published native wheel.

```python
import iso8601

value = iso8601.parse_date("2026-08-12T10:30:45.123456Z")
assert value.isoformat() == "2026-08-12T10:30:45.123456+00:00"
assert iso8601.is_iso8601("2026-08")
```

## Install

The project is not published from this repository yet. After a release:

```console
python -m pip install fast-iso8601-rs
```

Existing code continues to use `import iso8601`. Python 3.8+ selects a native
wheel on supported platforms. Python 3.7 selects the `py3-none-any` fallback.

## Compatibility and verification

The replacement is pinned to upstream 2.1.0, not an open-ended promise about
future versions. See [UPSTREAM-CONTRACT.md](UPSTREAM-CONTRACT.md) for the frozen
surface and [COMPATIBILITY.md](COMPATIBILITY.md) for executable gates.

```console
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-targets
python -m pytest -q tests
PYTHON=python bash scripts/run_upstream_full.sh
python scripts/run_differential.py --oracle-python ORACLE --candidate-python CANDIDATE
```

Benchmark claims are accepted only for the exact installed wheel identified by
filename and SHA256, with raw samples, median and p95 retained. No fixed speedup
is claimed before that gate passes.

## License

MIT. The frozen upstream notice and Rust dependency notices are retained in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

