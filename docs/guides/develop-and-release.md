# Develop and release

Two loops: a fast local loop after a focused change, and the certification
gates that run rarely (engine changes, releases). Commands assume an editable
Python install and installed Node dependencies; `python tools/mordheim-utils.py
doctor` reports what is actually available.

## Fast development loop

```powershell
python tools/mordheim-utils.py verify --structural   # KB change only
python tools/mordheim-utils.py tests --scope deterministic
```

For TypeScript/web changes:

```powershell
cd packages/typescript
npm run typecheck
npm test
cd ../../apps/warband-manager-web
npm run typecheck
npm run lint
npm test
npm run build
```

Narrower Python scopes: `tests --scope campaign`, `knowledge`, `construction`,
`ui`, `cli`, `architecture`. `tests --scope all` runs the complete Python
suite; anything after the scope is forwarded to pytest.

## Knowledge artefact

The browser consumes generated JSON, not YAML. Rebuild and check it when
changing canonical knowledge or the generator:

```powershell
python tools/knowledge/generate_knowledge_web.py
python tools/knowledge/generate_knowledge_web.py --check
```

Both locations (`build/generated/knowledge-web/` and the staged
`apps/warband-manager-web/public/knowledge/`) are generated and ignored;
`run-ci` performs the staging.

## Full CI-equivalent gate

```powershell
python tools/mordheim-utils.py run-ci
```

Runs the knowledge generator/check, the Python contract/campaign/architecture/
knowledge/web tests, the TypeScript typecheck/tests and the web
typecheck/lint/tests/build plus the post-build bundle guard — the same steps as
`.github/workflows/ci.yml`.

## Verification and certification

The modular engine is the scalar correctness oracle; NumPy and native are
candidates. What each layer can and cannot prove is
[Verification](../reference/verification.md).

```powershell
python tools/mordheim-utils.py verify --require-complete
python tools/mordheim-utils.py parity --require-complete
python tools/mordheim-utils.py coverage-gate
python tools/mutate-engine.py
```

`parity --level statistical` adds the standard six-sigma sample;
`parity --level deep --pair-set fast|full` runs the curated archetype matrix,
with `--truncations` for round-horizon checks. These take minutes to hours and
belong to engine changes and releases, never to the per-change loop.

Generated reports live under ignored `outputs/` — never hand-edit them:

- `audit/` — per-rule inventory (`report rules`).
- `test-report/` — semantic and technical CSVs (`report tests`).
- `parity/` — JSON/Markdown parity certificates.
- `benchmarks/` — benchmark results.

## Performance work

### Recommended configurations (measured)

A single timing configuration with a baseline gate:

```powershell
python tools/mordheim-utils.py benchmark -n 100000 --backend numpy --save-baseline outputs/benchmarks/numpy-before.json
python tools/mordheim-utils.py benchmark -n 100000 --backend numpy --baseline outputs/benchmarks/numpy-before.json --require-improvement --output outputs/benchmarks/numpy-after.json
```

The gate requires a 10% improvement in at least one scenario and no regression
above 5%; adjust thresholds only when the change justifies it.

The optima below come from the time-to-solution study (`benchmark --tts`) on the
reference development machine (Intel 8 P-cores + 4 E-cores, Windows). They are
the shared fallback constants; an installed calibration profile supersedes them
per machine (see *Calibrating a machine*).

| Use case | Backend | Batch size | Workers | Measured throughput |
| --- | --- | --- | --- | --- |
| Large battery, full 42-pair matrix | native | 5,000 | `processes=12` | ≈3.4M duels/s (5.9x its sequential) |
| Fallback battery | numpy | 25,000 | `processes=8` | ≈0.96M duels/s |
| Single-process app-scale runs | native | 5,000 | — | — |
| Single-process app-scale runs | numpy | 100,000 | — | — |

Four laws distilled from the studies:

- **Batch size is also an engine choice.** With 100k batches numpy wins;
  native only deploys its 2–3x advantage with small batches (≈5k), and below
  ≈10k numpy collapses (per-op overhead × hundreds of batches).
- **Worker count is per-engine.** Native keeps gaining through 14 workers
  (16 is level, 18-20 regress — the plateau is flat within the 3-30% noise of
  cheap pairs); numpy is memory-bandwidth bound and regresses past 8.
- **Segments are the hard ceiling of parallelism.** A 10k-sample run at batch
  5k is 2 segments, so no worker count can beat 1.7x there. A sample-size
  threshold alone misjudges workloads: numpy pays off from ≈200k samples
  (≈5.7 µs/duel against native's ≈1.4 µs), native needs a run wide enough to
  amortize its spawn.
- **Throughput is not the decision.** Measure time-to-solution (`--tts`), not
  isolated sim/s: spawn costs, batch-count ceilings and heterogeneous pair
  sets change the ranking (measurements that showed 3.9x in isolation became
  2.85x or losses at real workload scale).

Prefer `processes=N` over `parallel=N` for batteries: it balances by scenario
and amortizes the spawn.

### How the app resolves sizes at runtime

The application applies the optima without asking:

- The legacy global batch default (100k) resolves per duel to the engine
  actually running it in a **sequential** plan (native → 5k, numpy → 100k).
  NumPy fighters inside a **pooled** run switch to the measured pooled batch
  (25k, `pool_batch_size`) — its 100k sequential optimum starves the pool
  (−39% per fighter at 1M: 10 batches over 8 workers makes the wall follow the
  slowest segment).
- Comparison analyses decide the process pool **from measurement, not from a
  fixed sample size**. The baseline battery always runs sequentially (its wall
  time measures the real per-duel cost of that pair) and a pool is engaged only
  when the estimated saving across the remaining fighters beats its spawn cost
  with a 1.25x margin (`application.settings.battery_pool_plan`). One executor
  is reused for the whole run (14 workers native / 8 numpy by default, with a
  per-tab override).
- Pooled and sequential runs produce bit-identical totals — the pool reuses
  each engine's own per-batch stream derivation. The exception is numpy
  candidates in a pooled run: switching batch re-maps the per-batch streams, so
  their totals are an independent sample at the same seed rather than a replay
  of the sequential batch plan.

Measured crossover (reference machine, native batch 5k, 12 workers). `N*` is
how many fighters a run needs for the pool to pay off:

| Samples | Segments | seq/fighter | pool/fighter | Speedup | N* |
| --- | --- | --- | --- | --- | --- |
| 10,000 | 2 | 15.0 ms | 8.8 ms | 1.7x | 54 |
| 25,000 | 5 | 35.8 ms | 10.6 ms | 3.4x | 13 |
| 60,000 | 12 | 85.5 ms | 14.8 ms | 5.8x | 5 |
| 100,000 | 12 | 143.0 ms | 23.1 ms | 6.2x | 3 |
| 250,000 | 12 | 338.1 ms | 48.6 ms | 7.0x | 1 |
| 1,000,000 | 12 | 1,395.5 ms | 174.7 ms | 8.0x | 1 |

Spawn + shutdown costs ≈200-240 ms for 12-14 native workers and ≈200 ms for 8
numpy ones. End-to-end through `compare_builds`, a 96-candidate run at 25k
samples went from 3.48 s to 1.46 s (2.4x) and a 12-candidate run at 500k from
8.90 s to 2.17 s (4.1x).

At the app's usual size (1M samples per fighter, with the run-shared pool and
spawn paid once; a light duel at ≈0.7 µs/duel and heavy-grind at ≈5 µs/duel):

| Backend | Batch | Batches/worker | seq/fighter | pool/fighter | Speedup |
| --- | --- | --- | --- | --- | --- |
| native | 10k | 7-8 | 0.69 / 4.91 s | 85 / 582 ms | 8.2x / 8.4x |
| native | **5k** | 14-15 | 0.69 / 4.91 s | 79 / 556 ms | 8.8x / 8.8x |
| native | 2.5k | 28-29 | — | 76 / 552 ms | 9.1x / 8.9x |
| numpy | 100k | 1-2 | 2.55 / 13.98 s | 742 / 4532 ms | 3.4x / 3.1x |
| numpy | **25k** | 5 | — | 534 / 3254 ms | 4.8x / 4.3x |
| numpy | 12.5k | 10 | — | 531 / 3601 ms | 4.8x / 3.9x |

Native 5k/14 stands (5k is within 4% of the best measured point at 1M; 10k
only loses). All 42 deep pairs are native-eligible, so the numpy path appears
only for exotic plans or a missing native extension — but when it appears,
25k versus 100k is the difference between 3.1x and 4.3x.

Every completed analysis appends one local JSON Lines usage record
(`%LOCALAPPDATA%\Mordheim Combat Lab\usage-log.jsonl`, schema
`mordheim-combat-lab-usage/v1`): tab, requested sizes and the per-fighter
resolutions actually executed. It is purely local (no network, no identifiers,
write failures are swallowed) and is read with
`mordheim_combat_lab.persistence.usage_log.read_usage_records`.

### Calibrating a machine (`calibrate`)

The constants above are one machine's measurements. Users (and maintainers
after a hardware or engine change) measure their own machine and have the app
adopt the result:

```powershell
python tools/mordheim-utils.py calibrate                 # full sweep, ~8-10 min
python tools/mordheim-utils.py calibrate --pairs mini    # ~2 min survey
python tools/mordheim-utils.py calibrate --reset         # drop the profile
```

The command sweeps **every duel type** of the deep matrix (42 pairs; numpy
sweeps the stratified 30-pair set at smaller sizes because its duels cost
~3-5x more) across sequential batch, pooled batch and worker candidates on
both engines, plus the process-pool spawn cost, and installs
`calibration.json` next to the preferences
(`%LOCALAPPDATA%\Mordheim Combat Lab\`). Re-run it after a hardware change, an
engine update or new combat rules: it is the tool that re-tunes the app.

The Combat Lab applies the profile at startup
(`application.settings.apply_calibration`): engine batch defaults, pooled
batches, pool workers, spawn cost **and the pool speedup curve**, validated and
range-clamped section by section, falling back to the reference constants.
Measurement hygiene worth knowing when reading a profile:

- Each candidate is scored by the **geometric mean of its per-pair ratio to
  the best candidate**, so every duel type weighs the same regardless of
  absolute cost; the profile keeps the raw per-pair walls as evidence.
- Worker candidates above the batch count are skipped (the plan caps segments
  at batches, so they would measure pool size, not parallelism), and the numpy
  sequential sample size is anchored to its largest batch candidate so every
  candidate spans at least three batches.
- A candidate within **2% of the best never displaces the reference value**:
  cheap-pair run noise is 3-30%, so sub-2% wins are not signal.
- The **pool speedup model is re-derived from the saved evidence**: the worker
  sweep measures every candidate worker count at the winning pooled batch, so
  each pair yields a sequential/pooled per-duel ratio and the app gets this
  machine's `segments → speedup` curve (`measured_pool_speedups`). Anchors are
  the measured worker counts, values interpolate linearly between them, the
  lowest anchor's efficiency is held below the measured range, the largest
  measurement above it, and everything is clamped to the segment count.
  Without a profile the shared conservative curve applies unchanged.

`--no-install` measures and reports without touching the profile; `--output
PATH` writes a full copy of the report; `--json` prints it.

### Reference studies

Time-to-solution study over the full matrix (hours; use `--pair-set fast` or
`mini` and a smaller grid for a quick recalibration):

```powershell
python tools/mordheim-utils.py benchmark --tts --pair-set full --backend numpy native --simulation-sizes 250k,1M,4M --batch-sizes 5k,25k,100k --strategies "sequential,processes=4,processes=8,parallel=4,parallel=8" --repeats 2 --seed 7 --output outputs/benchmarks/estudio.json
```

`--tts` sweeps the (simulation size × batch size) grid and, inside each cell,
every (strategy × backend) combination in one run, with identical per-batch
streams gating totals per backend across strategies. A parity FAIL is an
engine determinism bug, not a timing result: fix the engine before trusting any
wall time in the report.

## Windows packaging

Install the dev extra, verify the desktop dependencies/Tkinter, then run the
relevant script:

```powershell
tools\windows\build_MordheimCombatLab_ONEFILE.bat
tools\windows\build_MordheimCampaignManager.bat
```

The scripts build standalone EXEs from the current
`packages/python`/`apps` layout and bundle `sources/knowledge/`. They are not
CI deployment commands.

## Release checklist

- [ ] Fast relevant tests pass.
- [ ] `verify --require-complete` passes (structural + semantic).
- [ ] TypeScript/web checks pass when applicable.
- [ ] Contract fixtures and generated knowledge artefacts validate when applicable.
- [ ] Engine changes have the required parity/coverage/mutation evidence.
- [ ] No generated reports, `dist/`, `build/generated/`, screenshots or temporary campaign files are staged.
- [ ] Windows packages are smoke-tested when a desktop release is required.

See [Verification](../reference/verification.md) for what each gate can and
cannot prove.
