# Recorded benchmark baselines

Reference measurements kept for comparison across optimization work. Each
file is the unmodified `--save-baseline` output of `performance benchmark`,
so it carries its measurement design (`configuration`) and where it was
measured (`provenance`: commit, engine digests, machine, Python, NumPy).

Compare a current run against a stored baseline with the same design:

```powershell
python tools/mordheim-utils.py performance benchmark --backend modular -n 2000 --repeats 3 --warmups 1 --seed 2026 --baseline benchmarks/baselines/modular-2026-11-05.json --require-improvement --output outputs/benchmarks/modular-after.md
```

A baseline measured on another machine or engine revision still compares,
with a provenance warning; read its result in that light. Add a new file
when the reference point changes deliberately (an accepted optimization, a
new machine); never edit an existing one.

| File | Engine | Design | Machine | Notes |
| --- | --- | --- | --- | --- |
| `modular-2026-11-05.json` | modular | 8 standard scenarios, 2,000 duels, 3 repeats, 1 warm-up, seed 2026, sequential | i5-11400H (6C/12T, powersave governor), Linux, CPython 3.14.4 | Starting point before modular optimization work; commit `2f8a35e6`, clean tree. Aggregate 338 duels/s; run-to-run spread 0.2-2.3 % per scenario. |
