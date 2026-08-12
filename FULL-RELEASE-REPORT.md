# Full Release Report

## Decision

Status: **Adjust / locally release-ready, not published**. All locally executable
implementation, compatibility, differential, artifact and benchmark gates pass.
No remote repository was created, no artifact was published, and no
cross-platform CI result is claimed from local macOS evidence.

## Frozen input

- upstream `iso8601==2.1.0`, commit
  `c147acc8952bf279a38d5cab1f80be71735a10cf`;
- sdist SHA256 `6b1d3829ee8921c4301998c909f7829fa9ed3cbdac0d3b16af2d743aed1ba8df`;
- wheel SHA256 `aac4145c4dcb66ad8b648a02830f5e2ff6c24af20f4f482689be402db2429242`.

## Required evidence before release

1. Rust fmt/clippy/tests and candidate tests.
2. Complete unmodified frozen upstream suite against installed candidate.
3. Isolated deterministic 10,000-case oracle/candidate differential.
4. Fresh native wheel, canonical fallback wheel and sdist reconstruction.
5. Artifact inspector, checksums and `twine check` over the immutable set.
6. Exact-wheel benchmark JSON containing raw samples, median and p95.
7. Packaged-wheel CI on Linux x86_64, macOS arm64 and Windows x86_64, plus
   Python 3.7 fallback.
8. OIDC publication followed by public-index reinstall, with GitHub Release last.

## Local evidence (2026-08-12, macOS arm64, Python 3.14.6)

- Rust: 4 tests passed; fmt and clippy with `-D warnings` passed.
- Candidate: 31 tests passed.
- Frozen upstream: 47 tests passed from unchanged
  `upstream/iso8601/test_iso8601.py` (SHA256
  `c66876357326d5c5ed52d7059055c41c4d89db791645d1fad05b7f5d3f9732ee`).
- Differential: 10,000/10,000 equal, seed `20260812`, in isolated processes.
- Fresh installs: native wheel, fallback wheel and sdist-reconstructed native
  wheel each passed candidate/upstream/differential gates.
- Immutable local set: inspector PASS, `twine check` PASS, checksum manifest
  generated. Exact values remain in ignored `dist/SHA256SUMS`; the checked-in
  exact native artifact is bound by `BENCHMARK.md` and its JSON evidence.
- Benchmark: 3 workloads, 90 raw samples. Median speedups on this exact artifact
  were 1.12x parse UTC, 1.18x offset/fraction parse and 2.65x lexical validation.
  These are artifact/machine-specific, not universal claims.

## Remaining external gates

- Linux x86_64, Windows x86_64, packaged macOS arm64 and Python 3.7 workflow runs;
- PyPI Trusted Publishing and public-index reinstall;
- GitHub Release creation last.

The workflows encode those gates, but they are intentionally unrun because this
task does not authorize a remote repository or publication.
