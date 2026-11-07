# Recorded benchmark baselines

Reference measurements kept for comparison across optimization work. Each
file is the unmodified `--save-baseline` output of `performance benchmark`,
so it carries its measurement design (`configuration`) and where it was
measured (`provenance`: commit, engine digests, machine, Python, NumPy).

Compare a current run against a stored baseline with the same design:

```powershell
python tools/mordheim-utils.py performance benchmark --backend modular --scenarios small --simulations 2000 --repeats 3 --warmups 1 --seed 2026 --baseline benchmarks/baselines/modular-2026-11-05.json --require-improvement --output outputs/benchmarks/modular-after.md
python tools/mordheim-utils.py performance benchmark --backend numpy --scenarios big --simulations 200000 --batch-size 100000 --repeats 3 --warmups 1 --seed 2026 --baseline benchmarks/baselines/numpy-big-2026-11-06.json --require-improvement --output outputs/benchmarks/numpy-after.md
```

A baseline measured on another machine or engine revision still compares,
with a provenance warning; read its result in that light. Add a new file
when the reference point changes deliberately (an accepted optimization, a
new machine); never edit an existing one. A gate compares like designs:
the same `--scenarios`, `--simulations`, `--batch-size`, `--seed`,
`--warmups`, `--repeats`, `--workers` and `--backend` as the baseline.

| File | Engine | Design | Machine | Notes |
| --- | --- | --- | --- | --- |
| `modular-2026-11-05.json` | modular | 8 `small` scenarios, 2,000 duels, 3 repeats, 1 warm-up, seed 2026, sequential | i5-11400H (6C/12T, powersave governor), Linux, CPython 3.14.4 | Starting point before modular optimization work; commit `2f8a35e6`, clean tree. Aggregate 338 duels/s; run-to-run spread 0.2-2.3 % per scenario. |
| `numpy-big-2026-11-06.json` | numpy | 43 `big` scenarios, 200,000 duels, batch 100,000, 3 repeats, 1 warm-up, seed 2026, sequential | i5-11400H (6C/12T, powersave governor), Linux, CPython 3.14.4, NumPy 2.5.4 | Starting point before the rule-algorithm optimization work; commit `bf433764`, clean tree. Aggregate 161,792 duels/s (sum of medians 53.15 s). Spread across the 3 repeats: median 1.9 %, up to 7.0 % on the cheapest scenarios (`basic`, `defences`), so a per-scenario gain under that is not separable from run noise in one run. The outcomes of the same engine and level are stored separately in `tests/engines/parity/reference_samples/numpy-big-200k`. Recorded as `numpy-long-2026-11-06.json` when the level was named `long`; renamed, contents unchanged. |
