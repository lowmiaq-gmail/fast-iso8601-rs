# Reuse Audit

## Decision

Target classification is `BUILD`: no existing implementation provides the
complete frozen drop-in contract. Engineering-asset strategy is `ADAPT/REUSE`:
reuse the proven packaging, verification, artifact-inspection, CI and release
topology from `fast-base58-rs`; implement ISO 8601 behavior from the frozen
`iso8601==2.1.0` contract only.

## Reused unchanged in principle

- gate order: Reuse -> Correctness -> Packaging -> Value -> Evidence;
- PyO3 abi3 mixed-project with a native wheel plus canonical universal fallback;
- candidate tests, complete frozen upstream suite and isolated deterministic differential;
- fresh-wheel validation, archive-safety inspection, `twine check` and checksums;
- Linux x86_64, macOS arm64 and Windows x86_64 packaged-wheel CI;
- fail-closed OIDC release flow: build once, collect immutable artifacts, publish,
  reinstall from public PyPI, then create the GitHub Release last;
- exact-artifact benchmark evidence with every raw sample, median and p95.

## Parameterized here

- upstream: `micktwomey/pyiso8601`, tag `2.1.0`, commit
  `c147acc8952bf279a38d5cab1f80be71735a10cf`;
- PyPI sdist SHA256 `6b1d3829ee8921c4301998c909f7829fa9ed3cbdac0d3b16af2d743aed1ba8df`;
- PyPI wheel SHA256 `aac4145c4dcb66ad8b648a02830f5e2ff6c24af20f4f482689be402db2429242`;
- import namespace `iso8601`, complete API/typing/exception/timezone contract;
- parser-specific corpus and workloads; no inherited benchmark numbers.

## Explicitly not reused

- base58 implementation, fixtures, CLI, encodings, dependencies or benchmark data;
- dotenv grammar, filesystem/environment behavior or fixtures;
- any compatibility claim unsupported by this repository's own gates.
