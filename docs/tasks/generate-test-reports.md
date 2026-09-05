# Generating test and parity reports

The recommended human-readable report is produced with:

```powershell
python -m mordheim_combat_lab test-report
```

The command runs semantic parity and the whole technical suite. A live progress
bar tracks the semantic phase (one unit per specification) and the optional
statistical samples; the `pytest` phase reports its own dots. It writes two
files under `outputs/test-report/`:

- `semantic-parity.csv`: the spec cases compared between the modular engine,
  NumPy and the native backend.
- `technical-tests.csv`: all the tests collected by `pytest`, including the
  parametrized ones, their duration and any error.

The CSVs use UTF-8 with BOM and `;` as separator. They are sanitized so that
line breaks, control characters or formula prefixes never break their display
in Excel.

> **Warning — long-running.** `test-report` executes the whole semantic
> corpus (≈3 700 cases) plus the complete `pytest` suite, and
> `--statistical` adds the five 100k-duel aggregate samples — minutes in
> total. The full report is a **certification artifact**: generate it
> occasionally, after large modifications or before a release. To verify a
> small change use the trimmed alternatives listed under *Deep profiles*
> below (smaller sample sizes, targeted `pytest` files) instead of the full
> run; `parity` without `--statistical`/`--deep`/`--truncations` is the
> fast deterministic gate.

## Options

```powershell
python -m mordheim_combat_lab test-report --output outputs/my-report
python -m mordheim_combat_lab test-report --require-complete
python -m mordheim_combat_lab test-report --statistical --statistical-simulations 100000 --seed 2026
```

| Option | Use |
| --- | --- |
| `--output DIRECTORY` | Changes the directory of both CSVs. |
| `--require-complete` | Also returns an error if adapters or the native backend are missing. |
| `--statistical` | Adds the five statistical scenarios to the semantic CSV. |
| `--statistical-simulations N` | Duels per engine and scenario; 100,000 by default. |
| `--seed N` | Seed for the statistical comparisons. |
| `--workers N\|auto` | Processes for the modular-oracle samples; see *Parallel oracle samples* below. |

Without `--require-complete`, a pending item does not fail the command. A
semantic divergence, a technical failure or a `pytest` error do produce a
non-zero exit code. The files are written even when the run fails, so the
diagnostics are preserved.

## Reading `semantic-parity.csv`

Each row is one semantic case. The result columns appear together, followed by
the status columns:

```text
modular_result | numpy_result | native_result
modular_status | numpy_status | native_status | passes
```

`expected` holds the expected observable and `rules` identifies the rules or
mechanics that justify the case. `details` is only filled when there is a
limitation or an error worth explaining.

Global `passes` states:

| State | Meaning |
| --- | --- |
| `PASS` | All applicable implementations agree. |
| `FAIL` | There is a real divergence or error. |
| `PENDING` | An adapter, a semantic decision or a backend is missing. |
| `OUT_OF_SCOPE` | The rule is excluded from the current runtime. |

Specific states such as `PASS_SHARED`, `NOT_APPLICABLE`,
`PENDING_ADAPTER`, `PENDING_SEMANTIC` and `NOT_AVAILABLE` explain why the
global state was reached. `PASS_SHARED` means the engines consume the same
compiler result; it does not represent two independent implementations.
`NOT_APPLICABLE` marks a case that an engine does not execute by design: the
native backend is a full-duel engine without standalone operators, so
per-operator cases show `NOT_APPLICABLE` for it and its certification appears
in the per-scenario statistical rows. When the native extension is not
compiled those rows are marked `NOT_AVAILABLE` and the report stays `PENDING`
until the backend exists.

## Other related commands

For a quick check without running `pytest` or generating CSVs:

```powershell
python -m mordheim_combat_lab parity
```

To require full parity and save the machine certificate as JSON:

```powershell
python -m mordheim_combat_lab parity --require-complete --output outputs/parity/report.json
```

Coverage of the deterministic layer is measured separately: `coverage-gate`
runs the deterministic engine suites under `coverage` and fails when any line
of the committed budget (`tests/fixtures/coverage/budget.json`) stops being
exercised (regenerate with `tools/update-coverage-budget.py` after adding the
tests that cover new code), and `tools/mutate-engine.py` applies the
engine-mutation catalogue to staged copies to prove the deterministic tests
can tell a defective engine apart from the oracle. Both are documented in the
[testing strategy](../testing-strategy.md).

`parity --statistical` runs the same aggregate comparisons as
`test-report --statistical`. The certificate counts a sample as
certification-sized from `CERTIFICATION_SIMULATIONS` (100 000 duels per
engine); smaller samples are diagnostic.

## Certification presets: `--level` and `--help-all`

The everyday `--help` of `parity` and `benchmark` documents only the common
options; sample sizing, sweep shapes and the historical mode flags stay
accepted but are hidden from it. Select the tier with one flag, and keep the
hidden knobs for tuning:

- `python tools/mordheim-utils.py parity --level statistical` — exact checks
  plus the aggregate six-sigma samples on the five standard scenarios
  (equivalent to the historical `--statistical`).
- `python tools/mordheim-utils.py parity --level deep` — exact checks plus
  the archetype matrix and numpy↔native cross (historical `--deep`); add
  `--truncations` for the orchestration horizons.
- `python tools/mordheim-utils.py benchmark` — a single-configuration
  measurement of all engines; the sweep/deep profiles and timing knobs are
  available through `benchmark --help-all` and documented below.

`parity --help-all` and `benchmark --help-all` print the full option set;
the historical `--statistical` / `--deep` / `--deep-simulations` … flags keep
working unchanged.

The deterministic engine gate of every change runs in one shot with
`python tools/mordheim-utils.py tests --scope deterministic` — the same
suite selection the coverage gate measures (`modular + vectorized + phases +
parity corpus`).

## Deep profiles: `parity --deep` and `benchmark --deep`

Both tools ship a `--deep` mode for long-running, large-scale runs (hours are
acceptable). Both keep the modular engine on a short leash on purpose:

- the modular oracle runs at roughly 1000 duels/s (about 76 duels/s on the
  75-round `long` scenario), while the NumPy engine runs hundreds of
  thousands of duels/s;
- the six-sigma statistical gate is capped by the smaller of the two
  samples, so running millions of duels on the modular engine buys no extra
  evidence;
- therefore the optimized engines are swept at scale and the modular oracle
  is only sampled where its contribution is real.

### `parity --deep` — deep certification

```powershell
python tools/mordheim-utils.py parity --deep
```

> **Warning — long-running.** The full deep certification needs ≈2 850 000
> modular duels plus the numpy→native cross at 1 000 000 duels/pair (≈50–70
> min sequential, ≈10–15 min with `--workers auto`). It is a *point run*:
> after large modifications or before a release, never for small changes.
> For a small check, trim it — `--deep-simulations 10 000
> --deep-cross-simulations 100 000` brings the run to a few minutes (the
> CLI warns when the cross layer still dominates).

Runs the six-sigma certification over the **archetype matrix** (30 pairs:
the five standard scenarios, profile/equipment archetypes covering glass
cannons, brutes, elite fighters, tanks, dual weapons, parry duels and
Ithilmar armour, twelve mechanic-coverage pairs added 2026-09-04 for
undead/sigmarite, regeneration vs fire, natural armour vs magic, pistols,
concussion vs dwarfs, frenzy/always-strikes-first, paired poisoned blades,
two-handed weapons, ward saves, unarmed combat, fragile injury profiles
and entangle, and five timing/parry amplifiers added 2026-09-05:
`triple-weapon-vs-parry`, `a2-vs-w1-stun`, `frenzy-vs-w2`,
`durable-vs-elite` and the 75-round `heavy-grind`) and, when the native
backend is compiled, the **numpy→native cross-certification at scale**:

- `--deep-simulations` (default 100 000 per pair, 25 000 for the long
  75-round pair): duels per matrix pair and engine; the modular sample is
  computed once and shared by every backend. Passing the flag explicitly
  applies the same count to every pair. It sizes the **matrix layer only** —
  the numpy↔native cross layer keeps its own `--deep-cross-simulations`
  default, so a small `--deep-simulations` smoke run still samples the cross
  layer at 1 000 000 duels/pair unless you scale it down too (the CLI warns
  about this when it happens).
- `--deep-cross-simulations` (default 1 000 000): duels per pair for the
  numpy→native comparison; never touches the modular engine.
- `--max-modular-duels` (default 3 000 000): ceiling on the total modular
  duels a single run may request (the default split needs 2 850 000 — 28
  pairs at 100k plus the two 75-round pairs at 25k; the adaptive
  escalation below stays within the same ceiling). A plan above the
  ceiling exits with code 2 before running anything.
- **Adaptive escalation**: pairs whose first pass comes back suspicious
  (3–6σ) or timing-prone (≥1% unresolved) are re-certified at twice the
  sample, allocated most-suspicious-first and clamped by
  `--max-modular-duels`. Escalated rows carry `"escalated": true` in the
  certificate and the console prints a `DEEP: escalated N pair(s)…`
  summary line.
- Default run cost: roughly 2 850 000 modular duels (≈ 50–70 minutes
  sequentially, or ≈ 10–15 minutes with the parallel oracle enabled; see
  below) plus the cross layer when native is present; escalation may raise
  the oracle total toward the ceiling.
- Progress: `parity --deep` (and `parity --statistical`) render a live
  progress bar; pass `--json` to suppress it. `benchmark --deep` shows the
  same bar for every grid cell.
- Output: `parity --deep` saves the certificate to
  `outputs/parity/deep.json` by default (`.json`, or `.md` via `--output`);
  the report gains a `deep` block with one sample per
  pair (`reference_rates` vs `candidate_rates`, tolerances, pass) and, per
  engine, the sample's wall time (`reference_seconds`, `candidate_seconds`);
  console prints one `DEEP:` line per sample ending in
  `(duels/engine; oracle X.XXs + numpy Y.YYs)`. Every run also records its
  **total wall time** at the top level of the certificate
  (`elapsed_seconds`), shown in the Markdown header and on the console as a
  final `Elapsed: X.XXs` line. Exit-code semantics match `--statistical`: a
  failing sample fails the run only with `--require-complete`.

### Engine-level execution times in the certificate

Every statistical and deep sample in the certificate reports the wall time
of **each engine's sample** at engine level: `reference_seconds` is the
modular oracle for statistical/matrix rows and NumPy for cross rows, and
`candidate_seconds` is the certified backend (NumPy or native). The JSON
rows carry them as raw floats, the Markdown tables add a
`Time (oracle/cand, s)` / `Time (ref/cand, s)` column, and the console
`STATISTICAL:`/`DEEP:` lines print them inline. The numbers measure the
whole sample call, so a pooled sample (`--workers auto`) reports its
accelerated wall time; sequential and pooled runs are otherwise
bit-for-bit identical.

The top-level `elapsed_seconds` in the certificate is the total wall time
of the whole `parity` run (deterministic checks + samples + report
writing); `test-report` prints the same total on its console summary.

Current status of the shipped matrix (2026-09-04): a full certification
run at 100k duels/pair exposed **six** drifting archetype pairs
(`brute-vs-fencer` ~15 pp, `axes-vs-light`, `two-weapons-vs-parry`,
`glass-vs-tank`, `stateful`, `elite-vs-durable`). Triage traced them to a
single orchestration defect — the vectorized drivers derived each reply
attack phase from the primary actor's rows, so a downed primary silently
suppressed the standing opponent's attack (and its helpless auto-OOA).
The fix landed in both the NumPy driver and the native Cython port
(2026-09-04) and `brute-vs-fencer` converges to ≈0 pp at 30k duels; a
fresh full certification is the authoritative confirmation.

The matrix was then extended from 13 to 25 pairs with twelve
mechanic-targeted pairs. A 10k-duel smoke shows NumPy matching the oracle
on **all** of them (max gap ≈ 0.9 pp), but the native port still drifts
5–9 pp on six mechanics it previously never exercised: `regen-vs-fire`,
`natural-armour-vs-magic`, `concussion-vs-dwarf`, `paired-poison-vs-undead`,
`great-weapon-vs-tank` and `entangle-vs-fencer` (plus ≈5 pp on
`frenzy-vs-heavy`). Those native gaps are the next triage targets; NumPy
rows of the same pairs are already clean.

### Round-truncation samples (`--truncations`)

> **Warning — long-running.** The truncation sweep now covers the whole
> 30-pair deep matrix, so the default 10 000 duels/horizon is itself a long
> run (≈20–40 min sequential, ≈5–10 min pooled). It is part of the
> certification tiers — run it after orchestration-level modifications, not
> per small change. For a small check, trim it with
> `--truncation-simulations 2 000` (a few minutes) or run the horizons for
> one pair through the API.

The aggregate gate compares only the duel *end state*; orchestration defects
— wrong acting order, a suppressed reply phase, a stateful recovery resolved
at the wrong moment — shift *when* duels resolve without necessarily moving
the final winner rates past the gate. `parity --truncations` re-applies the
six-sigma gate at every horizon (2, 4, 6, 8, 10, 12, 15, 20 rounds) on
**every deep-matrix pair** (30 scenarios, previously only the five standard
ones): both engines run each pair truncated to `h` rounds and rows are
labelled `<scenario>@rounds=<h>` so a failing horizon names the round where
the divergence starts.

```powershell
python -m mordheim_combat_lab parity --truncations
python -m mordheim_combat_lab parity --truncations --truncation-simulations 50000 --workers auto
```

| Option | Use |
| --- | --- |
| `--truncations` | Add the round-truncation samples to the certificate. |
| `--truncation-simulations N` | Duels per engine, scenario and horizon; 10 000 by default. |

Truncation samples count towards `--require-complete` and appear in the
certificate's `truncations` block (schema `mordheim-combat-parity/v2`).
Outcome after exactly `h` rounds is engine-agnostic by construction — a duel
that has not resolved by the horizon counts as unresolved in both drivers —
so no round-counting convention leaks into the comparison. See
[the testing strategy](../testing-strategy.md) for why per-duel resolution
rounds are *not* comparable and were replaced by this sweep.

### Parallel oracle samples (`--workers`)

The scalar oracle is the bottleneck of every certification run and is
embarrassingly parallel by construction: duel `i` runs on its own
`SeededDice(seed + i)` stream and the outcome counts are additive, so a
process pool over contiguous duel chunks reproduces the sequential oracle
**duel for duel** — certificates are bit-for-bit identical whatever the pool
size. `parity --deep`, `parity --statistical` and
`test-report --statistical` accept:

- `--workers auto` (default): pool only the samples whose estimated
  sequential runtime exceeds ~20 s (a smoke run with 2 000 duels stays
  sequential; the 100k/25k deep samples are pooled).
- `--workers N`: force a pool of `N` processes for every oracle sample
  (`1` disables it).
- The default can be set once per shell with
  `MORDHEIM_PARALLEL_ORACLE_WORKERS` (e.g. `8` or `auto`).

`benchmark` intentionally has no such option: its modular cells are
*measurements* of the engine's single-process throughput, and pooling them
would make the medians and baseline comparisons meaningless. The oracle
samples of `parity`/`test-report` are evidence gathering, not measurement,
so they may be pooled freely.

### `benchmark --deep` — deep performance characterization

```powershell
python tools/mordheim-utils.py benchmark --deep
```

Sweeps the optimized engines (NumPy and, when compiled, native) over large
simulation counts and batch sizes while measuring the modular engine **only
at a small reference size**:

- `--deep-simulation-sizes` (default `10k,100k,500k,1M,5M`) and
  `--deep-batch-sizes` (default `25k,100k,200k,500k`) size the
  vectorized grid; override with the regular `--simulation-sizes` /
  `--batch-sizes` flags.
- `--deep-modular-simulations` (default 10 000): the modular reference point
  per scenario; never included in the large grid.
- Scenario and backend filters apply (`--scenario`, `--backend numpy` …);
  `--backend modular` alone is rejected (exit 2) because deep mode is about
  the optimized engines. The baseline/gate flags are not combinable with
  `--deep`.
- When native is not compiled it is reported as unavailable and skipped;
  the report payload marks `"mode": "deep"` and records the modular
  reference size.
- `--deep` saves the report to `outputs/benchmarks/deep.json` by default;
  pass `--output` to choose another path or format (.json, .csv or .md).
- Runtime scales with the largest simulation size: keep the top size and
  the number of batch sizes proportional to the question you are answering.
  The modular contribution stays negligible.

To measure performance without certifying rules:

```powershell
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy --scenario all --repeats 5 --save-baseline outputs/benchmarks/numpy-before.json
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy --scenario all --repeats 5 --baseline outputs/benchmarks/numpy-before.json --require-improvement --output outputs/benchmarks/numpy-after.json
```

`benchmark` accepts `modular`, `numpy`, `native` and `all`. Each JSON report includes the
configuration, the individual samples, the median, simulations per second and environment
data. A baseline is only compared when seed, batch size, warm-ups, repeats and number of
simulations match.

The performance gate applies the criteria of the optimized-engine development:

- at least one comparable scenario must improve by 10 %;
- no comparable scenario may regress by more than 5 %.

The thresholds can be tuned with `--min-improvement` and `--max-regression`. Without
`--require-improvement`, a failed comparison is shown and saved to the report, but does not
change the exit code. It is advisable to close intensive applications and run baseline and
candidate on the same machine under the same conditions.
