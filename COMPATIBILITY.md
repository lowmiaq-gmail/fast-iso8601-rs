# Compatibility Gates

This is an executable checklist. A box is checked only when the cited local
command has passed against the current commit/artifact.

- [x] `cargo fmt --all -- --check`
- [x] `cargo clippy --all-targets --all-features -- -D warnings`
- [x] `cargo test --all-targets` (4 passed)
- [x] `python -m pytest -q tests` (31 passed)
- [x] `PYTHON=python bash scripts/run_upstream_full.sh` (47 passed, frozen test SHA256 checked)
- [x] `python scripts/run_differential.py --cases 10000 ...` (`seed=20260812`)
- [x] fresh native wheel, universal fallback wheel and sdist build/install gates
- [x] `python scripts/inspect_python_artifacts.py ...` and `python -m twine check dist/*`
- [x] exact-artifact benchmark with 90 raw samples, median and p95

The candidate scope is the complete frozen 2.1.0 contract: imports/re-exports,
signatures/docs/annotations/defaults, `parse_date`, `is_iso8601`,
`parse_timezone`, `FixedOffset`, `ParseError`, `UTC`, `ISO8601_REGEX`, timezone
identity/equality, Decimal truncation, exception chains/messages, dynamic invalid
input, custom/default tzinfo, deepcopy/pickle, `py.typed`, star imports and
platform-specific packaged wheels. CI-only platforms remain pending until CI
runs; local success is not reported as cross-platform proof.

Local artifacts and benchmark evidence are ignored build products except for
the checked-in benchmark JSON/Markdown. Linux x86_64, Windows x86_64 and Python
3.7 are workflow-defined but remain unverified until CI runs.
