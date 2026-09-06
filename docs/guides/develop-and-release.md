# Develop and release

> **Warning — long-running release gates.** The commands below run the whole
> engine suite and the complete semantic corpus (`python -m pytest -q` and
> `test-report` take minutes), so they are the **release procedure**, not the
> per-change loop. For a small change, run the targeted suites instead —
> `python -m pytest tests/combat/... -q` for the unit level,
> `python tools/mordheim-utils.py tests --scope deterministic` for the engine
> gate, and the trimmed parity samples described in
> [Verification](../reference/verification.md). Reserve the full `pytest -q`,
> `test-report` and `parity --deep` runs for after large modifications and
> before releases.

## Release procedure

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m mordheim_combat_lab validate
python -m mordheim_combat_lab verify
python -m mordheim_combat_lab test-report
```

`verify` accepts pending items; `--require-complete` does not. `test-report`
generates the human CSVs of parity and technical tests; use
`test-report --require-complete` as the strict gate when the optimized backend
must be fully certified.

Before optimizing, save a reproducible baseline:

```powershell
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy --save-baseline outputs/benchmarks/numpy-before.json
```

After the change, run the same configuration and enable the agreed gate:

```powershell
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy --baseline outputs/benchmarks/numpy-before.json --require-improvement --output outputs/benchmarks/numpy-after.json
```

The gate requires a 10 % improvement in some scenario without degrading
another by more than 5 %. Finally, build Windows with
`tools\windows\build_MordheimCombatLab_ONEFILE.bat` (or
`build_MordheimCampaignManager.bat`). Each build produces a standalone EXE
that bundles the application and the shared KB; neither bundles `tests/`.

Done when tests and validation pass, the semantic status does not regress,
and the package bundles the KB but neither the specifications nor historical
files.

## Test and parity reports

The recommended human-readable report is produced with:

```powershell
python -m mordheim_combat_lab test-report
```

It runs semantic parity and the whole technical suite (live progress bar) and
writes two files under `outputs/test-report/`:

- `semantic-parity.csv`: the spec cases compared between the modular engine,
  NumPy and the native backend.
- `technical-tests.csv`: all the tests collected by `pytest`, including the
  parametrized ones, their duration and any error.

The CSVs use UTF-8 with BOM and `;` as separator, sanitized so line breaks,
control characters or formula prefixes never break their display in Excel.

### Options

| Option | Use |
| --- | --- |
| `--output DIRECTORY` | Changes the directory of both CSVs. |
| `--require-complete` | Also returns an error if adapters or the native backend are missing. |
| `--statistical` | Adds the five statistical scenarios to the semantic CSV. |
| `--statistical-simulations N` | Duels per engine and scenario; 100,000 by default. |
| `--seed N` | Seed for the statistical comparisons. |
| `--workers N\|auto` | Processes for the modular-oracle samples. |

Without `--require-complete`, a pending item does not fail the command. A
semantic divergence, a technical failure or a `pytest` error do produce a
non-zero exit code. The files are written even when the run fails, so the
diagnostics are preserved.

### Reading `semantic-parity.csv`

Each row is one semantic case. `expected` holds the expected observable and
`rules` identifies the rules or mechanics that justify the case. `details` is
only filled when there is a limitation or an error worth explaining.

Global `passes` states:

| State | Meaning |
| --- | --- |
| `PASS` | All applicable implementations agree. |
| `FAIL` | There is a real divergence or error. |
| `PENDING` | An adapter, a semantic decision or a backend is missing. |
| `OUT_OF_SCOPE` | The rule is excluded from the current runtime. |

Specific states such as `PASS_SHARED`, `NOT_APPLICABLE`, `PENDING_ADAPTER`,
`PENDING_SEMANTIC` and `NOT_AVAILABLE` explain why the global state was
reached. `PASS_SHARED` means the engines consume the same compiler result; it
does not represent two independent implementations. `NOT_APPLICABLE` marks a
case that an engine does not execute by design: the native backend is a
full-duel engine without standalone operators, so per-operator cases show
`NOT_APPLICABLE` for it and its certification appears in the per-scenario
statistical rows. When the native extension is not compiled those rows are
marked `NOT_AVAILABLE` and the report stays `PENDING` until the backend
exists.

### Other related commands

For a quick check without running `pytest` or generating CSVs:

```powershell
python tools/mordheim-utils.py parity
```

To require full parity and save the machine certificate as JSON:

```powershell
python tools/mordheim-utils.py parity --require-complete --output outputs/parity/report.json
```

`parity --statistical` runs the same aggregate comparisons as
`test-report --statistical`. The certificate counts a sample as
certification-sized from `CERTIFICATION_SIMULATIONS` (100 000 duels per
engine); smaller samples are diagnostic.

### Certification presets: `--level` and `--help-all`

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
  available through `benchmark --help-all`.

`parity --help-all` and `benchmark --help-all` print the full option set; the
historical `--statistical` / `--deep` / `--deep-simulations` … flags keep
working unchanged.

The deterministic engine gate of every change runs in one shot with
`python tools/mordheim-utils.py tests --scope deterministic` — the same suite
selection the coverage gate measures (`modular + vectorized + phases + parity
corpus`).

The deep profiles (`parity --deep`, `parity --truncations`,
`benchmark --deep`), their pair sets, sample sizing, parallel-oracle pooling
and certificate fields are documented in
[Verification](../reference/verification.md) — the budgets above are the
short version.
