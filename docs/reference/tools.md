# Repository tools

`tools/` contains reproducible automation or scripts that support an active
workflow. The usual entry point is `python tools/mordheim-utils.py --help`.
Specialized scripts are grouped by purpose, not language or caller.

## Main entry point

| Tool | Purpose |
|---|---|
| `tools/mordheim-utils.py` | Launch applications and centralize tests, local CI, verification, reports, benchmarks, parity and diagnostics. |

The [test classification reference](test-sequence.md) defines the phase
categories and their dependency order. `test-sequence` executes Python in that
order; the TypeScript/web suites select the same categories through native
Vitest projects from their own commands.

## Selecting tests with the launcher

Run commands from the repository root. `tests --help` lists the actual scope
paths without collecting tests; `tests -- --help` displays pytest's options.
The launcher prepares Python package paths and forwards pytest's exit status.

| Scope | Selection |
|---|---|
| `modular`, `vectorized`, `native`, `shared`, `parity` | The corresponding directory under `tests/engines/`; parity also includes its benchmark tests |
| `engines` | All five engine suites, including parity and benchmark checks |
| `rules` | Knowledge, construction and integration, including E2E |
| `knowledge` | `tests/rules/knowledge` and declarative integration specs |
| `construction`, `e2e` | `tests/rules/construction` or `tests/rules/integration/e2e` |
| `applications` | All Python application tests; Vitest is run separately |
| `tooling`, `architecture` | All Python tooling tests, or only tooling architecture |
| `ui` | Combat Lab UI checks |
| `cli` | Launcher, Combat Lab CLI and parity benchmark checks |
| `verification` | Parity, verification tooling and semantic/structural integration runners |
| `deterministic` | Broad modular/vectorized/shared/replay/parity selection used by the coverage workflow |
| `all` (default) | The complete `tests/` Python selection |

Scopes select paths, not an engine backend or a phase. They may overlap and do
not run prerequisites. In particular, `deterministic` is a broad selection, not
a promise of a fast or passing optimized-engine run. Full campaigns are not a
routine prerequisite for editing a fixture or moving a test.

```powershell
python tools/mordheim-utils.py tests --help
python tools/mordheim-utils.py tests --scope shared --collect-only -q
python tools/mordheim-utils.py tests --scope modular -k selected_test -q
python -u -m pytest tests/engines/native/test_native_engine.py::test_native_accumulates_counts_across_batches -v --tb=short
python tools/mordheim-utils.py test-sequence --scope modular --workers 2 -q --output outputs/test-runs/modular.txt
```

For a specific file or node ID, call pytest directly: appending a path after
`--scope` adds to the scope selection, rather than replacing it. Use
`-n 2 --dist=load` for independent focused checks, without nested process pools.
Run process-pool and timing-sensitive tests serially; collection stays serial.
For phase ordering use `test-sequence --workers N`, never raw `-n`/`--dist`.
Vitest already parallelizes files; limit selected workspace runs with
`--maxWorkers=2` while other work is active. Keep output visible and reuse valid
results instead of repeating large selections.

### Command recipes and configuration

All examples below run from the repository root in PowerShell. Choose one
selection for the work at hand; this is a menu, not a checklist to run in full.

**Inspect or collect without executing test bodies.** Collection still imports
modules and loads data; E2E/semantic collection can be substantial.

```powershell
python tools/mordheim-utils.py tests --help
python tools/mordheim-utils.py test-sequence --steps
python -u -m pytest tests/engines/shared/test_kernel_plan.py --collect-only -q
python tools/mordheim-utils.py tests --scope e2e --collect-only -q
```

**One file, a named test, or a filtered component.** A pytest node ID has the
form `path.py::function`; quote the whole node ID when selecting a parameter
such as `path.py::function[parameter-id]`.

```powershell
python -u -m pytest tests/engines/shared/test_kernel_plan.py -q --tb=short
python -u -m pytest tests/engines/native/test_native_engine.py::test_native_accumulates_counts_across_batches -v --durations=5 --tb=short
python tools/mordheim-utils.py tests --scope modular -k "leadership and not parallel" -q --tb=short
python tools/mordheim-utils.py tests --scope construction -m phase2_construction -q --tb=short
```

`-k` matches names; `-m` matches category markers. Neither guarantees a nonempty
selection. Pytest exit code 5 means no tests were collected, not a successful
validation. `--scope modular` selects test files; it is not a backend override
for individual mixed tests.

**Independent checks with two workers.** This example runs only the two named
files. Increase to four workers for an integrated run when resources are free;
avoid `-n auto` and concurrent writers to shared generated data.

```powershell
python -u -m pytest tests/engines/shared/test_kernel_plan.py tests/tooling/launcher/test_umbrella.py -n 2 --dist=load -q --durations=10 --tb=short
```

**Inner process pools stay serial at the pytest level.** These existing tests
load frozen inputs and exercise the NumPy or native path. Run them separately,
without `-n`; do not multiply internal workers by xdist workers.

```powershell
python -u -m pytest tests/engines/vectorized/test_parallel_numpy.py::test_single_batch_samples_are_unchanged_by_the_parallel_path -v --durations=5 --tb=short
python -u -m pytest tests/engines/modular/test_parallel_oracle.py -q --durations=5 --tb=short
```

**Selected phases and saved output.** `--step 2` executes only construction;
it does not run phases 0 and 1 first. `--workers 2` parallelizes within a phase
and waits for it to finish before starting the next selected phase. Reports
remain visible and are stored under ignored `outputs/`.

```powershell
python tools/mordheim-utils.py test-sequence --step 2 --scope construction --workers 2 -q --output outputs/test-runs/construction.txt
python tools/mordheim-utils.py test-sequence --scope modular --sequence-plan -qq
python tools/mordheim-utils.py test-sequence --scope modular --workers 2 -q --output outputs/test-runs/modular.txt
```

Do not add `-n` or `--dist` to these commands. `--sequence-plan` is serial and
collects without running bodies; `--steps` is the fast static list.

| Option | Purpose / limit |
|---|---|
| `-q` / `-v` | Compact output / individual test outcomes, including skips |
| `--tb=short` | Short failure tracebacks without hiding the failure |
| `--durations=10` | Show the ten slowest setup/call/teardown durations |
| `-n 2 --dist=load` | Raw pytest: distribute independent tests across two workers |
| `--workers 2` | `test-sequence` only: preserve barriers between phase sessions |
| `-x` / `--maxfail=3` | Explicit early stop after one / three failures; default continues |
| `--lf` | Rerun last failures from local pytest cache; not a complete selection or certification |
| `--collect-only` | Discover/import tests without executing their bodies; keep serial |
| `--output PATH` | `test-sequence` only: overwrite a UTF-8 combined-output report and preserve exit status |

**TypeScript/web selections and project configuration.** npm runs in the chosen
workspace; file filters below are relative to that workspace. Vitest already
parallelizes files. `--project` selects a configured project, not a Python scope.

```powershell
npm run typecheck --workspace campaign-web-core
npm run typecheck --workspace warband-manager-web
npm test --workspace campaign-web-core -- ../../tests/applications/warband_manager/domain/shared-eligibility-reconciliation.test.ts --maxWorkers=2
npm test --workspace campaign-web-core -- --project phase0_preflight --maxWorkers=2
npm test --workspace warband-manager-web -- --project phase0_preflight --maxWorkers=2
```

The package projects are `phase0_preflight`, `phase1_kb_contracts` and
`phase7_warband`; the web projects are `phase0_preflight`, `phase7_warband` and
`packaging`. Web packaging checks need their generated/build assets; choosing a
project does not build them. Use `npm run build` before selecting post-build
bundle checks. Ordinary web/KB checks may also need
`python tools/knowledge/generate_knowledge_web.py`.

**Maintain build snapshots only when inputs are missing or intentionally
changed.** Ordinary test runs do not need these commands. Capture can read the
KB and compile missing configurations even without `--write`; it is not a
read-only check of the frozen document. `--file` takes a test file stem.

```powershell
python tools/verification/generate_compiled_builds.py --help
python tools/verification/generate_compiled_builds.py --file test_leadership_providers
python tools/verification/generate_compiled_builds.py --file test_leadership_providers --write
```

The second command captures preparations and writes its diagnostic report under
`outputs/`, without publishing the snapshot. The third publishes to
`tests/engines/fixtures/compiled-builds.json`, retaining the union of existing
frozen entries. Use one writer and inspect the diff; neither command refreshes
all existing fighters against a changed KB automatically. `compiled-cases.json`
uses the separate `export_cases(...)` API and its manifest; do not pass it to
the build-snapshot generator.

### Precompiled inputs and source-backed integration

Engine execution tests load `compiled-cases.json` and `compiled-builds.json`
from `tests/engines/fixtures/`; their loaders and conftest fixtures are required
as well. Existing test runs need no regeneration. See the
[fixture workflow](verification.md#engine-test-fixtures) for maintenance and
explicit compiler exceptions. Construction/KB/E2E checks remain under
`tests/rules/` and continue to test the original source-backed path.

A successful connection check proves that a frozen input reaches the selected
backend. It does not establish support for pending rules or statistical parity.
Missing snapshots, invalid fixtures and broken paths are preparation defects;
wrong results and explicitly unsupported mechanics need separate engine triage.
Native skips are not execution evidence.

`verify`, `parity`, `benchmark` and `calibrate` delegate to their own application
commands. Migrating their pytest tests to frozen inputs does not change the
CLI's default preparation: those commands may still compile against the KB.
Consult each command's help before a campaign; there is no launcher switch that
makes all commands read precompiled fixtures.

## Knowledge base

Permanent validation and generation:

| Tool | Purpose |
|---|---|
| `tools/knowledge/export_compiled_cases.py` | Python export API for explicit compiled case plans; reads the KB during fixture generation. |
| `tools/knowledge/audit_kb_conformance.py` | Check canonical knowledge against the expected model. |
| `tools/knowledge/audit_schema_strictness.py` | Detect gaps and unintended permissiveness in editorial schemas. |
| `tools/knowledge/generate_knowledge_web.py` | Generate deterministic JSON consumed by the web application. |
| `tools/knowledge/normalize_open_fields.py` | Normalize controlled vocabulary in open editorial fields. |
| `tools/knowledge/presentation_contract.py` | Build the presentable-text contract used by UI audits. |

Comparison of published catalogues against their printed sources:

| Tool | Purpose |
|---|---|
| `tools/knowledge/printed_entries.py` | Read a printed entry as the document prints it: geometry, currency and per-check coverage. |
| `tools/knowledge/source_documents.py` | Resolve a record's `source_refs` to the document that prints it and to its copy in the mirror, through `sources/knowledge/registry/source-documents.yaml`. |
| `tools/knowledge/check_hireling_sources.py` | Compare the published hireling catalogues — Hired Swords and Dramatis Personae, every grade — with the documents that print them. |

Reproducible editorial maintenance:

| Tool | Purpose |
|---|---|
| `tools/knowledge/maintenance/format_yaml.py` | Check or apply canonical YAML formatting without semantic changes. |
| `tools/knowledge/maintenance/normalize_names.py` | Check or fix names and IDs according to KB conventions. |
| `tools/knowledge/maintenance/price-collation.py` | Compare catalogue prices and produce reports using reviewed resolutions. |

## Verification

| Tool | Purpose |
|---|---|
| `tools/verification/compiled_cases.py` | Load and validate frozen execution cases. |
| `tools/verification/compiled_builds.py` | Load fighters by complete build identity and normalized root. |
| `tools/verification/generate_compiled_builds.py` | Capture missing build preparations and publish the union with frozen entries (`--write`); not part of ordinary test execution. |
| `tools/verification/mutate-engine.py` | Run controlled mutations to prove tests detect faults. |
| `tools/verification/refresh_spec_digests.py` | Refresh or check executable-specification digests. |
| `tools/verification/update-coverage-budget.py` | Recalculate the versioned deterministic coverage budget. |

## Web interface

| Tool | Purpose |
|---|---|
| `tools/web/build-eligibility.mjs` | Generate the versioned Python bundle from the shared TypeScript eligibility module; `--check` rejects stale output. Exposed as `npm run build:eligibility` / `npm run check:eligibility`. |
| `tools/web/presentation-audit.mjs` | Detect visible text without validated resolution or provenance. |
| `tools/web/presentation-flow-audit.mjs` | Trace raw text to presentation sinks. |
| `tools/web/presentation-type-audit.mjs` | Detect forged resolved-text types. |

Their tests live in `tests/tooling/web/`, not under `tools/`.

## Windows packaging

| Tool | Purpose |
|---|---|
| `tools/windows/build_MordheimCombatLab_ONEFILE.bat` | Build the single-file Combat Lab executable. |
| `tools/windows/build_MordheimCombatLab_INSTALLER.bat` | Build the installer from that executable. |
| `tools/windows/MordheimCombatLab.iss` | Inno Setup recipe used by the installer script. |

## Retention rule

Keep a tool only when it is owned by a current documented workflow, a test or
CI gate, the central launcher, or a repeatable operation over active data.
Permanent audits own invariants after a migration: `audit_kb_conformance.py`
rejects duplicated `rule_ref` prose, while schemas and
the knowledge pipeline guards reject the retired `summary` key. Remove one-off
migrations and diagnostics after their result is materialized.
