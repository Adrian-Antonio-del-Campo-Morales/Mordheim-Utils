# Develop and release

Two loops: a fast local loop after a focused change, and the certification
gates that run rarely (engine changes, releases). Commands assume an editable
Python install and installed Node dependencies; `python tools/mordheim-utils.py
doctor` reports what is actually available.

## Fast development loop

Choose the smallest check for the changed responsibility. Moving a test or
editing a path usually needs syntax/import checks and targeted collection;
changing an adapter needs a small execution sample. Reuse valid results and
repeat only checks affected by a later edit.

```powershell
python tools/mordheim-utils.py tests --help
python tools/mordheim-utils.py verify --structural   # KB change only
python -u -m pytest tests/engines/shared/test_kernel_plan.py -q --tb=short
python tools/mordheim-utils.py tests --scope modular -k selected_test -q
```

Engine tests consume versioned snapshots under `tests/engines/fixtures/`;
ordinary execution needs no regeneration. The original E2E corpus is under
`tests/rules/integration/e2e/`, and source-backed construction/KB/integration
checks retain compiler access. See [fixture maintenance](../reference/verification.md#engine-test-fixtures)
and the [launcher scope guide](../reference/tools.md#selecting-tests-with-the-launcher).
`--scope all` is the whole Python tree; `engines` and `deterministic` are also
broad selections, not default per-edit checks. They include optimized-backend
checks whose rules may still be unimplemented.

Use direct pytest paths/node IDs for an exact selection. Independent checks may
use `-n 2 --dist=load -q --durations=10 --tb=short`; tests creating their own worker
pools and timing measurements stay serial. Collection-only runs stay serial.
For phase barriers use `test-sequence --workers N` without raw xdist flags.
Keep live output; do not hide it with `| tail` or restart a still-running process
after a tool timeout.

For TypeScript/web changes, select affected files from their workspace:

```powershell
npm run typecheck
npm test --workspace campaign-web-core -- ../../tests/applications/warband_manager/domain/shared-eligibility-reconciliation.test.ts --maxWorkers=2
```

`npm test` runs both workspaces; `npm run lint` includes presentation checks and
`npm run build` typechecks/builds the web app. These broader checks belong to the
relevant integration stage, not every documentation or fixture-path edit.

For shared equipment/skill decisions, edit the [eligibility module](../reference/eligibility.md), then run from the repository root:

```powershell
npm run build:eligibility
npm run check:eligibility
python -m pytest tests/rules/construction -q
npm test --workspace campaign-web-core -- ../../tests/applications/warband_manager/domain/shared-eligibility-reconciliation.test.ts
```

Commit the generated `_eligibility.js` with its maintained TypeScript source. The
Python runtime uses that checked-in bundle; Node is a development dependency.

## Ready-to-use test configurations

Use these configurations as alternatives, not mandatory successive gates. The
[command recipe reference](../reference/tools.md#command-recipes-and-configuration)
explains all flags and workspace/project names.

| Change | Smallest useful starting point |
|---|---|
| Test move or import/path update | `python -u -m pytest tests/engines/shared/test_kernel_plan.py --collect-only -q` (substitute the affected file) |
| One engine adapter / frozen-input connection | Run the explicit NumPy or native node below |
| Compiler behavior | Select affected files in `tests/rules/construction/`; do not regenerate fixtures just to make changed outputs pass |
| E2E scenario | Select the scenario's collected node ID in `tests/rules/integration/e2e/`; use `--collect-only` on its runner when the ID is unknown |
| Launcher behavior | Select existing checks in `tests/tooling/launcher/` |
| TypeScript domain change | Workspace typecheck and the affected Vitest file |
| Multiple construction changes | Ordered construction-only phase with a saved report |

```powershell
# Independent Python checks: two workers, short failures, slowest timings
python -u -m pytest tests/engines/shared/test_kernel_plan.py tests/tooling/launcher/test_umbrella.py -n 2 --dist=load -q --durations=10 --tb=short

# Frozen-input connection: run separately, without xdist
python -u -m pytest tests/engines/vectorized/test_parallel_numpy.py::test_single_batch_samples_are_unchanged_by_the_parallel_path -v --tb=short
python -u -m pytest tests/engines/native/test_native_engine.py::test_native_accumulates_counts_across_batches -v --tb=short

# Explicit early stop while investigating a selected failure
python -u -m pytest tests/engines/shared/test_kernel_plan.py -x -v --tb=short

# Construction phase only, parallel inside the phase, visible + saved output
python tools/mordheim-utils.py test-sequence --step 2 --scope construction --workers 2 -q --output outputs/test-runs/construction.txt
```

Default execution continues after failures. Choose `-x` or `--maxfail=3` only
when early stopping is intended. Never add raw `-n`/`--dist` to `test-sequence`;
its `--workers` option owns parallelism. A skipped native test is not a native
connection check. An explicitly unsupported mechanic or wrong optimized-engine
result needs engine triage, while missing snapshot keys and broken bindings
need fixture/preparation correction.

## Knowledge artefact

The browser consumes generated JSON, not YAML. Rebuild and check it when
changing canonical knowledge or the generator:

```powershell
python tools/knowledge/generate_knowledge_web.py
python tools/knowledge/generate_knowledge_web.py --check
```

The generated browser knowledge files live in `outputs/web-public/knowledge/`
and are ignored;
`run-ci` and CI generate them before running the browser checks.

## Full CI-equivalent gate

```powershell
python tools/mordheim-utils.py run-ci
```

Runs the knowledge generator/check, the Python contract/campaign/architecture/
knowledge/web tests and shared eligibility transport tests, the eligibility
bundle freshness check, the TypeScript typecheck/tests and the web
typecheck/lint/tests/build plus the post-build bundle guard — the steps of
`.github/workflows/ci.yml` plus `tests/rules/knowledge/web`. Those browser
artefact checks read generated knowledge data and can be expensive; select the
affected files while editing and reserve the full gate for integration.

## Verification and certification

The modular engine is the scalar correctness oracle; NumPy and native are
candidates. What each layer can and cannot prove is
[Verification](../reference/verification.md).

```powershell
python tools/mordheim-utils.py verify --require-complete
python tools/mordheim-utils.py parity --require-complete
python tools/mordheim-utils.py coverage-gate
python tools/verification/mutate-engine.py
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

Benchmark changes against a saved baseline:

```powershell
python tools/mordheim-utils.py benchmark -n 100000 --backend numpy --save-baseline outputs/benchmarks/numpy-before.json
python tools/mordheim-utils.py benchmark -n 100000 --backend numpy --baseline outputs/benchmarks/numpy-before.json --require-improvement --output outputs/benchmarks/numpy-after.json
```

The gate's thresholds belong to the command, not to this document. Store raw
results under ignored `outputs/benchmarks/`; do not copy measured throughput or
machine-specific optima into maintained documentation.

Calibrate after hardware, engine or combat-rule changes:

```powershell
python tools/mordheim-utils.py calibrate
python tools/mordheim-utils.py calibrate --pairs mini
python tools/mordheim-utils.py calibrate --reset         # drop the profile
```

The benchmark/parity/calibration CLIs retain their own scenario preparation and
may compile from the KB; frozen pytest inputs do not change those defaults.

The command installs `calibration.json` beside the local preferences. Use
`--no-install` for a read-only study, `--output PATH` for the full evidence and
`--json` for machine-readable output. A parity failure invalidates timing
results and must be fixed before interpreting performance.

## Windows packaging

Install the dev extra, verify Combat Lab dependencies/Tkinter, then run the
relevant script:

```powershell
tools\windows\build_MordheimCombatLab_ONEFILE.bat
tools\windows\build_MordheimCombatLab_INSTALLER.bat
```

The scripts build Combat Lab from the current source checkout. They are not CI
deployment commands.

Before packaging changed eligibility sources, run `npm run build:eligibility`
and `npm run check:eligibility`. The executable includes the generated JavaScript
and MiniRacer's native library; installing Node on the target machine is unnecessary.

## Release checklist

- [ ] Fast relevant tests pass.
- [ ] `verify --require-complete` passes (structural + semantic).
- [ ] TypeScript/web checks pass when applicable.
- [ ] Contract fixtures and generated knowledge artefacts validate when applicable.
- [ ] Shared eligibility bundle matches its sources and both consumer suites pass when its rules change.
- [ ] Engine changes have the required parity/coverage/mutation evidence.
- [ ] No generated reports, `outputs/`, `dist/`, screenshots or temporary campaign files are staged.
- [ ] Windows packages are smoke-tested when a Combat Lab release is required.

See [Verification](../reference/verification.md) for what each gate can and
cannot prove.
