# Exact-Artifact Benchmark

- artifact: `fast_iso8601_rs-0.1.0-cp38-abi3-macosx_11_0_arm64.whl`
- artifact SHA256: `e6eb97cce26dbd7c18fe6680d105afff842ef5857363eb28fb8fd36ced3f75c1`
- Python: `3.14.6 (main, Jun 10 2026, 10:03:53) [Clang 21.0.0 (clang-2100.0.123.102)]`
- platform: `macOS-26.5.2-arm64-arm-64bit-Mach-O`
- iterations/repeats/warmup: `10000 / 15 / 1000`

| Workload | Oracle median ns | Candidate median ns | Oracle p95 ns | Candidate p95 ns | Median speedup |
|---|---:|---:|---:|---:|---:|
| parse_utc | 11768.16 | 10494.77 | 13147.30 | 23075.03 | 1.12x |
| parse_offset_fraction | 17656.33 | 15006.23 | 20233.35 | 17377.76 | 1.18x |
| is_valid_compact | 3174.00 | 1199.13 | 3854.82 | 1846.22 | 2.65x |

The JSON evidence retains every raw sample and exact input. Results are specific to this artifact and machine.
