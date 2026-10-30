# Repository tools

`tools/` contains reproducible automation or scripts that support an active
workflow. The usual entry point is `python tools/mordheim-utils.py --help`.
Specialized scripts are grouped by purpose, not language or caller.

## Main entry point

| Tool | Purpose |
|---|---|
| `tools/mordheim-utils.py` | Launch applications and centralize tests, checks, performance measurements, reports and diagnostics. |

## Command groups

The launcher has four groups. Commands live below them, with named
subsections where a group has several maintained selections. No arguments
prints the hierarchy; nothing starts a broad run by accident.

```powershell
python tools/mordheim-utils.py --help
python tools/mordheim-utils.py app --help
python tools/mordheim-utils.py tests --help
python tools/mordheim-utils.py performance --help
python tools/mordheim-utils.py check --help
```

| Group | Purpose |
|---|---|
| `app` | Open the desktop Combat Lab or start the Campaign Manager dev server. |
| `tests` | Run a named pytest/Vitest selection or the environment diagnostics. |
| `performance` | Measure engine execution and this machine's optima. |
| `check` | Validate, measure or generate artefacts: verification, reports, parity, coverage, presentation and local CI. |

```powershell
# Independent examples, not a sequence
python tools/mordheim-utils.py app combat-lab
python tools/mordheim-utils.py app warband-manager --port 5199 --strictPort
python tools/mordheim-utils.py tests modular mechanics -n 8 --dist=load -q
python tools/mordheim-utils.py tests modular runtime -q
python tools/mordheim-utils.py tests kb -n 8 --dist=load -q
python tools/mordheim-utils.py performance benchmark --scenario basic --simulations 1000 --repeats 3
python tools/mordheim-utils.py performance calibrate --pairs mini --no-install
python tools/mordheim-utils.py check verify --json
python tools/mordheim-utils.py check report rules --output outputs/audit
python tools/mordheim-utils.py check parity --profile quick --require-complete
python tools/mordheim-utils.py check coverage --json
python tools/mordheim-utils.py check presentation
python tools/mordheim-utils.py check ci
```

Use `<group> <command> --help` for what a command executes and which parser owns
its options. Measurement, audit and report commands may run tests, simulations
or write outputs; displaying help executes none of them.

## App launchers

```powershell
python tools/mordheim-utils.py app combat-lab
python tools/mordheim-utils.py app warband-manager [vite args ...]
```

`app combat-lab` runs `python -m mordheim_combat_lab ui` (Tkinter) and takes no
arguments. `app warband-manager` runs `npm run dev` in
`apps/warband-manager-web` and forwards its arguments to Vite.

## Help at each level

The main help is a short command map. Use the next level for the actual
selection, useful options, side effects and copyable examples:

```powershell
python tools/mordheim-utils.py -h
python tools/mordheim-utils.py tests -h
python tools/mordheim-utils.py tests modular -h
python tools/mordheim-utils.py tests modular mechanics -h
python tools/mordheim-utils.py check parity -h
python tools/mordheim-utils.py performance benchmark -h
python tools/mordheim-utils.py check report tests -h
```

For the complete underlying application options, use `--help-full` on a
performance command, `check verify`, `check parity`, `check coverage` or a
report kind. This opens its parser help, not a measurement or test campaign:

```powershell
python tools/mordheim-utils.py performance benchmark --help-full
python tools/mordheim-utils.py check parity --help-full
python tools/mordheim-utils.py check report rules --help-full
```

For pytest's own help, pass it after the separator:

```powershell
python tools/mordheim-utils.py tests modular mechanics -- --help
```

`--list` reads file names only. `--collect-only` imports test modules and
collects cases but does not execute bodies. Eight-worker examples are intended
for independent tests; runtime tests with inner pools remain serial.

## Tests: purpose and selection

The testing strategy has three complementary layers:

- **Modular mechanics:** check game rules directly in the reference engine,
  where failures are easiest to isolate and debug.
- **Source-backed integration:** knowledge contracts, construction tests and
  E2E scenarios check the KB -> compiler -> modular combat path.
- **Statistical parity:** compare NumPy/native result distributions with the
  modular reference. The deterministic cross-engine replay suite was removed.

Each engine also has runtime checks for execution, observations, state,
reproducibility and parallelism. Counts-only and observed modular simulation
both remain useful. Shared tests protect common contracts and frozen inputs;
tooling tests protect the comparators and execution infrastructure. Application
behavior is tested separately. These layers are complementary: selecting one
layer does not order or imply the others.

### Selections

The hierarchy mirrors the launcher: **app launchers** (`combat-lab`,
`warband-manager`), **tests** (`env`, `combat-lab`, `warband-manager`,
`modular`, `vectorized`, `native`, `kb`) and **performance** (`benchmark`,
`calibrate`). Three cross-cutting test selections keep the integrity suites
reachable without forcing them into those categories: `parity` (statistical
comparisons and their tooling), `shared` (common engine contracts and frozen
inputs) and `tooling` (architecture, launcher and coverage checks).

Each test selection maps to maintained paths. Run `tests <selection> --help`
for its files, its subsections and copyable examples, or
`tests <selection> <subsection> --help` for one subsection.

| Selection | Subsection | Runs |
|---|---|---|
| `env` | none | Environment, dependency and engine diagnostics in process (`tests env`), not a test suite. |
| `combat-lab` | none | `pytest tests/applications/combat_lab`. |
| `warband-manager` | `python` | `pytest tests/applications/warband_manager`. |
| `warband-manager` | `web` | Vitest in `packages/typescript` and `apps/warband-manager-web`. |
| `modular` | `mechanics` | `pytest tests/engines/modular/mechanics`. |
| `modular` | `runtime` | `pytest tests/engines/modular/runtime`. |
| `vectorized` | `mechanics` | `pytest tests/engines/vectorized/mechanics`. |
| `vectorized` | `runtime` | `pytest tests/engines/vectorized/runtime`. |
| `native` | `runtime` | `pytest tests/engines/native/runtime` (the bare selection also runs `tests/engines/native/test_native_engine.py`). |
| `kb` | none | `pytest tests/knowledge`. |
| `kb` | `construction` | `pytest tests/construction`. |
| `kb` | `e2e` | `pytest tests/integration/e2e`. |
| `parity` | `statistical` | `pytest tests/engines/parity/statistical`. |
| `parity` | `tooling` | `pytest tests/tooling/parity`. |
| `shared` | none | `pytest tests/engines/shared`. |
| `tooling` | `architecture` | `pytest tests/tooling/architecture`. |
| `tooling` | `web` | Vitest `architecture` project in both workspaces (purity and web boundaries). |
| `tooling` | `launcher` | `pytest tests/tooling/launcher`. |
| `tooling` | `coverage` | `pytest tests/tooling/coverage`. |

Selection rules:

- A bare selection runs what its help says. `tests modular` runs mechanics and
  runtime; `tests tooling` runs architecture, launcher and coverage;
  `tests parity` runs statistical and tooling.
- `tests kb` runs the **knowledge** suite only; there is no `knowledge`
  subsection alias. Construction and E2E are large batteries and stay separate
  selections instead of being bundled silently.
- `tests warband-manager` has no shared default: pytest and Vitest do not accept
  the same options, so choose `python` or `web`.
- Several subsections can be named together: `tests modular mechanics runtime`.
- `tests env` is the diagnostics entry point: it runs in process and takes no
  runner options. There is no separate `doctor` command.

```powershell
python tools/mordheim-utils.py tests --help
python tools/mordheim-utils.py tests modular --help
python tools/mordheim-utils.py tests modular mechanics --help
python tools/mordheim-utils.py tests kb e2e --help
python tools/mordheim-utils.py tests kb --list
python tools/mordheim-utils.py tests kb e2e -q
python tools/mordheim-utils.py tests modular mechanics -n 8 --dist=load -q
python tools/mordheim-utils.py tests modular runtime -q
```

### Listing, collection and filtering

- `tests --list` prints every Python and Vitest test file on disk without
  importing anything. `<selection> --list` narrows it to that selection and to
  the languages its runner can execute (pytest selections list `.py` files,
  Vitest selections list `.test.ts`/`.test.tsx`/`.test.mjs` files); it does not
  apply a runner's include/exclude rules.
- `--collect-only` asks pytest to import modules, load fixtures and collect
  actual cases, without running their bodies. Keep it serial.
- `-k` filters Python test names; `file.py::function[param]` selects a precise
  Python case; quote parameterized node IDs in the shell.
- An explicit file, directory or node ID **replaces** the selection's paths, so
  no unrelated suite is appended. Everything after `--` goes to the runner
  unchanged.
- Vitest positional arguments are filename filters; use the workspace project
  names (`--project architecture|web|packaging|typescript|knowledge-parity`)
  when a project selection is clearer.

```powershell
python tools/mordheim-utils.py tests --list
python tools/mordheim-utils.py tests tooling --list
python tools/mordheim-utils.py tests modular mechanics --collect-only -q
python tools/mordheim-utils.py tests modular mechanics -k leadership -n 8 --dist=load -q
python tools/mordheim-utils.py tests parity statistical -q
python tools/mordheim-utils.py tests shared tests/engines/shared/fixtures/test_precompiled_catalog.py::test_suite_scenarios_are_admitted_by_the_frozen_corpus -q
python tools/mordheim-utils.py tests modular mechanics tests/engines/modular/mechanics/test_abdul_eye_pendant.py -q
```

### Python versus Vitest

Python/pytest is the default for selections that have Python tests.
JavaScript/TypeScript tests share the repository test tree, so choose the
language explicitly with the subsection: `warband-manager python|web` and
`tooling architecture|web`. The launcher converts repository test paths to
workspace-relative filters for Vitest; the workspace configuration keeps its
includes, exclusions and project boundaries. Do not pass Python node IDs to
Vitest.

```powershell
python tools/mordheim-utils.py tests warband-manager python -n 8 --dist=load -q
python tools/mordheim-utils.py tests warband-manager web --maxWorkers=8
python tools/mordheim-utils.py tests tooling web --maxWorkers=8
python tools/mordheim-utils.py tests warband-manager web -t "display" --maxWorkers=8
```

### Execution options and limits

| Option | Meaning |
|---|---|
| `--list` | List test files without imports or case collection |
| `--collect-only` | Pytest case collection, with imports and fixture data loading |
| `-k expression` | Filter Python names/node IDs |
| `-n 8 --dist=load` | Eight pytest workers for independent checks |
| `--maxWorkers=8` | Eight Vitest workers |
| `-t pattern` | Vitest test-name filter |
| `-q` / `-v`, `--tb=short`, `--durations=10` | Python output and failure diagnostics |
| `-x` / `--maxfail=3`, `--lf` | Python early stopping or cached failures |

Eight workers are examples, not forced defaults. Keep collection, internal
process-pool tests, shared writers and timing-sensitive measurements serial.
Do not multiply inner workers by xdist workers. A skip does not prove native
execution; exit code 5 means an empty Python selection. Listing/collection and
runner self-checks do not certify rule behavior or statistical equivalence.

| Command | Parallel option |
|---|---|
| `tests` / direct pytest | `-n 8 --dist=load` for independent tests |
| Vitest via npm | `--maxWorkers=8`; file parallelism is already built in |
| `check parity` | `--workers 8` for modular-reference sampling; `--workers auto` uses the runner's automatic policy |
| `check report tests --statistical` | `--workers 8` for its statistical reference samples |
| `performance benchmark` | `--processes 8` for explicit multicore measurements |
| `performance calibrate` | Already measures worker configurations; no extra worker option |
| `tests env`, `check verify`, `check report rules`, `check coverage`, `check presentation`, `check ci`, `app` | No worker-count option exposed by these entries; do not append unsupported flags |

Keep `tests parity statistical` serial: its cases run their own modular-oracle sampling, so an outer xdist pool multiplies workers and distorts the comparison.

For time-to-solution measurements, the benchmark command can compare strategies:

```powershell
python tools/mordheim-utils.py performance benchmark --tts --pair-set mini --backend numpy --strategies "sequential,processes=8,parallel=8"
```

Keep benchmark measurements isolated from other workloads. Do not wrap parity
or benchmarks in xdist, and do not add `-n` to tests that create inner process
pools. Broad engine selections may include those tests, so their unfiltered
examples stay serial. Collection and typechecks are not accelerated by xdist.

### Inputs and catalogues

Engine tests load checked-in `compiled-cases.json` and `compiled-builds.json`
under `tests/engines/fixtures/`. Their loaders and conftest fixtures are required;
ordinary execution does not regenerate inputs or fall back to compilation when
a frozen input is missing. Knowledge, construction and E2E tests retain their
source-backed preparation.

- `precompiled_catalog.py` defines 43 unified scenarios with stable
  `scenario/<name>` keys. The cumulative levels `small`, `normal` and `long`
  select the same inputs for parity, benchmarks and calibration; `long` includes
  all 43. Seeds, sample widths and batch sizes are execution settings.
- `battery_catalogue.py` and `battery_keys.py` describe build-based battery
  cases, variants and intended clause coverage. Their preparation still requires
  compilation; these are not additional precompiled inputs.
- `run_parity` is the unified statistical runner; round horizons, sample budgets
  and escalation are configuration, not separate execution systems.

Do not regenerate frozen inputs merely to move tests or change imports. To
maintain build snapshots explicitly, use the existing capture/publish workflow:

```powershell
python tools/verification/generate_compiled_builds.py --help
```

Review the intended inputs and diff before publishing. `compiled-cases.json`
uses the separate `tools/knowledge/export_compiled_cases.py` API; it is not an
input to the build-snapshot generator.

### TypeScript and web

Vitest runs separately in its npm workspaces. The package projects are
`architecture`, `knowledge-parity` and `typescript`; the web projects are
`architecture`, `web` and `packaging`. These are project-defined filters, not
launcher selections. Asset-dependent packaging checks require their build inputs.
`tests warband-manager web` runs every project in both workspaces, including the
TypeScript `knowledge-parity` vectors; `tests tooling web` selects only the two
`architecture` projects.

```powershell
python tools/mordheim-utils.py tests tooling web --maxWorkers=8
python tools/mordheim-utils.py tests warband-manager web --project web --maxWorkers=8
```

Vitest already parallelizes files. Do not add another parallel runner inside
individual tests. The pytest targets do not change application preparation or
select a CLI backend.

## Performance

`performance benchmark` runs `python -m mordheim_combat_lab benchmark` and
`performance calibrate` runs `python -m mordheim_combat_lab calibrate`; their
arguments belong to those commands. A small sample illustrates the command, not
performance certification. Calibration can still be costly with the `mini` pair
selection, and the saved profile changes later measurements on this machine.

## Checks and reports

Each entry explains what it executes in `<entry> --help`.

| Entry | Executes |
|---|---|
| `check verify` | `python -m mordheim_combat_lab verify`: KB structure, editorial schemas, execution contract, binding contracts and default profile compilation. It is a structural gate, not the knowledge or E2E test suites (see [Verification](verification.md#deterministic-modular-evidence)). |
| `check report rules` | `python -m mordheim_combat_lab audit`: separate combat-mechanic and editorial-rule CSVs in `outputs/audit/`. |
| `check report tests` | `python -m mordheim_combat_lab test-report`: parity and technical test reports. |
| `check parity` | `python -m mordheim_combat_lab parity`: the statistical parity campaign against the modular reference. Its pytest checks are `tests parity statistical`. |
| `check coverage` | `python -m mordheim_combat_lab coverage-gate`: measure deterministic engine coverage and check the recorded budget; `--update-budget` replaces it deliberately after review. |
| `check presentation` | `npm run check:presentation` in `apps/warband-manager-web`: detector tests, strict deep text audit and dynamic visible-completeness audit. |
| `check ci` | Local integration gate, in order: KB generation and freshness, the Python net (campaign-file, architecture and `tests/knowledge`, including its `web/` audits), shared-eligibility transport, the eligibility bundle, TypeScript typecheck/tests, and web typecheck/lint/tests/build plus bundle guards. It does not run the modular E2E battery or its non-regression control, which CI runs as separate steps; add `tests kb e2e` for integration changes. |

```powershell
python tools/mordheim-utils.py check verify --json
python tools/mordheim-utils.py check report rules --output outputs/audit
python tools/mordheim-utils.py check report tests --statistical --workers 8 --output outputs/test-report
python tools/mordheim-utils.py check parity --profile quick --backend numpy --workers 8 --require-complete
python tools/mordheim-utils.py check coverage --json
python tools/mordheim-utils.py check presentation
python tools/mordheim-utils.py check ci
```

`check ci` runs its configured checks and builds; it is not a complete
engine-certification campaign. Use `tests` for suites and `check parity` for the
comparison campaign; neither substitutes for the other.

## Selecting parity catalogues and modular-only execution

The catalogue interface selects data independently of the engine:

- `--catalog precompiled`: unified frozen scenarios loaded from
  `compiled-cases.json` with no compilation fallback. `--level small` is the
  default; `--level normal` expands the selection and `--level long` selects
  all 43 scenarios.
- `--catalog battery`: all build-based battery cases. `--profile quick`,
  `complete` or `deep` filters this catalogue; no profile selects the full deep set.
- `--catalog all`: both catalogues. A profile filters only the battery portion.
- `--catalog e2e` or `--level e2e`: frozen E2E statistical deliveries.
  With no identifiers, selects every delivery, including blocked and
  non-applicable entries; their reasons remain visible without running them.
  See [E2E campaigns](#e2e-statistical-campaigns) below.
- `--backend modular`: execute the reference only. Rows report `COMPLETED`,
  errors or input limits, with no comparison or parity approval.
- `--backend numpy`, `native` or `all`: compare those candidates against the
  modular reference using the same runner. Here `all` names both candidates.

```powershell
python tools/mordheim-utils.py check parity --catalog precompiled --level long --backend modular --workers 8
python tools/mordheim-utils.py check parity --catalog battery --backend modular --workers 8
python tools/mordheim-utils.py check parity --catalog all --backend modular --workers 8

# One duel per scenario: checks executability, not statistical equivalence
python tools/mordheim-utils.py check parity --catalog all --backend modular --workers 8 --simulations 1

# Compare a selected battery profile against NumPy
python tools/mordheim-utils.py check parity --catalog battery --profile quick --backend numpy --workers 8
```

To reuse saved modular counts, sample only the candidate with
`tools.verification.parity_samples`, then compare the stores. For the 43
stored reference scenarios at 100,000 duels each:

```bash
python -m tools.verification.parity_samples sample --engine numpy --level long --simulations 100000 --seed 2026 --chunk 2500 --workers 2 --store outputs/parity-numpy
python -m tools.verification.parity_samples compare --backend numpy --level long --simulations 100000 --store outputs/parity-numpy --reference-store tests/engines/parity/reference_samples/modular-100k
```

Sampling resumes finished chunks and refuses stale candidate records unless
`--replace` is supplied. Comparison executes neither engine. It checks fighter
fingerprints, seeds, round limits and sample coverage, and reports stored and
current engine digests in `outputs/parity-numpy/compare/parity-campaign.json`
alongside a Markdown report. Different modular digests mean the comparison
uses a historical reference; it does not certify the current modular engine.
The comparison covers first wins, second wins and unresolved duels using the
existing six-sigma gate. Native sampling and comparison remain available;
`compare` defaults to `--backend native`.

`sample --workers N` runs up to N chunks in separate processes for all three
engines (`modular`, `numpy`, `native`); the default is 1, in-process. The parent
process saves completed chunks, so seeds and counts match sequential sampling
with the same chunk size, and interrupted runs can resume. A first Ctrl+C stops
new submissions and saves in-flight chunks; a second aborts immediately.
`compare` and `status` read saved counts and do not use workers. Check coverage
with `python -m tools.verification.parity_samples status --level long --store outputs/parity-numpy`;
use `--id scenario/basic` to restrict any subcommand to one scenario.

Without `--simulations`, precompiled scenarios use the command sample default;
battery cases keep their declared row count. `--workers 8` cannot split a single duel across workers.
Round limits and contexts remain those of each case, except E2E campaigns,
which use a maximum of 50 rounds independently of the original test horizon;
`--seed` sets the sample seed. Known unsupported inputs are reported as blocked,
not silently discarded. Missing frozen entries and compilation/execution errors
are failures. Use `--require-complete` to also return failure when any selected
case is blocked. `--json` and `--output outputs/modular-scenarios.json` record
the results.

### E2E statistical campaigns

E2E campaigns reuse frozen combat configurations with random dice, rather than
replaying the original test's scripted dice and exact assertions. Combats run
until termination or 50 rounds. Preparing a delivery does not establish engine
compatibility or statistical parity. The [delivery format and admission rules](verification.md#e2e-statistical-deliveries)
define which inputs can execute.

To persist one engine's W/L/U counts for later comparison:

```powershell
python -m tools.verification.parity_samples sample --engine modular --level e2e --simulations 100000 --seed 2026 --chunk 250 --workers 14 --store outputs/parity-modular-e2e
python -m tools.verification.parity_samples status --level e2e --store outputs/parity-modular-e2e
python -m tools.verification.parity_samples sample --engine numpy --level e2e --simulations 100000 --seed 2026 --chunk 250 --workers 14 --store outputs/parity-numpy-e2e
python -m tools.verification.parity_samples compare --backend numpy --level e2e --simulations 100000 --store outputs/parity-numpy-e2e --reference-store outputs/parity-modular-e2e
```

`sample`, `status` and `compare` accept repeatable `--id` values containing an
E2E key or `audit_id::id`. `sample --rounds N` explicitly overrides the campaign
horizon. Existing records with different horizons or chunk sizes cannot be
extended into the same experiment; use another store or explicitly replace them.
Sample files use `e2e__<sha256(case_key UTF-8)>.json` names to avoid long Windows
paths. This store retains winner counts only, not wounds or condition distributions.
Sampling returns 1 if any selected cases remain unexecuted, while preserving
completed samples for resumption.

Workers share a bounded queue across scenarios, so an available worker can
start the next case before the previous case's last chunk finishes. The parent
alone writes records. Graceful interruption stops submissions and saves in-flight
chunks; completed samples remain reusable.

To execute both engines and compare distributions directly:

```powershell
python tools/mordheim-utils.py check parity --level e2e --simulations 1000 --workers 2 --backend numpy --magnitudes winner,wounds,condition --output outputs/e2e-parity/all.json --output-md outputs/e2e-parity/all.md
```

Use repeatable `--e2e <case_key|audit_id::id>` or `--e2e-selection-file FILE` to
narrow that selection; the file accepts one identifier per line and `#` comments.
E2E direct comparisons accept candidate backends `numpy`, `native` or `all`;
`modular` alone is not accepted on this path. `winner` is mandatory;
`--magnitudes` can additionally select `wounds`, `condition` and `rounds` without
changing the frozen deliveries. `--output` writes JSON only and `--output-md`
writes Markdown only; both can be requested with different paths from one run.

Reports distinguish approval, measured divergence, reference/candidate execution
failures and unexecuted deliveries. Blocked, not-applicable, stale, invalid and
incompatible cases retain their reasons. Candidate exceptions are execution
failures, not measured divergences. A small successful sample does not certify
full engine parity.

These catalogues require a source checkout with `tests/engines/fixtures` and
its frozen JSON files. The battery also requires the KB/compiler. Catalogue
selection accepts `--level small|normal|long` for precompiled scenarios.
Historical parity levels and `--pair-set` remain available outside catalogue
selection; historical pair-set names map to the shared cumulative levels.

## Knowledge base

Permanent validation and generation:

| Tool | Purpose |
|---|---|
| `tools/knowledge/export_compiled_cases.py` | Python export API for explicit compiled case plans; reads the KB during fixture generation. |
| `tools/knowledge/audit_kb_conformance.py` | Check canonical knowledge against the expected model. |
| `tools/knowledge/audit_schema_strictness.py` | Detect gaps and unintended permissiveness in editorial schemas. |
| `tools/knowledge/clause_registry.py` | Query, prepare and guarded-apply edits to the maintained clause register; previews by default and preserves the CSV when conservation checks fail. |
| `tools/knowledge/clause_registry_validation.py` | Structural checks for the clause register's fields, vocabularies, references and row conservation; imported by `clause_registry.py`. |
| `tools/knowledge/generate_knowledge_web.py` | Generate deterministic JSON consumed by the web application. |
| `tools/knowledge/artefact_document.py` | Load the complete generated web KB artefact (initial document plus prose, display-text and catalogue fragments) for tools and tests. |
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

## Verification

| Tool | Purpose |
|---|---|
| `tools/verification/compiled_cases.py` | Load and validate frozen execution cases. |
| `tools/verification/compiled_builds.py` | Load fighters by complete build identity and normalized root. |
| `tools/verification/generate_compiled_builds.py` | Capture missing build preparations and publish the union with frozen entries (`--write`); not part of ordinary test execution. |

## Web interface

| Tool | Purpose |
|---|---|
| `tools/web/build-eligibility.mjs` | Generate the versioned Python bundle from the shared TypeScript eligibility module; `--check` rejects stale output. Exposed as `npm run build:eligibility` / `npm run check:eligibility`. |
| `tools/web/presentation-audit.mjs` | Detect visible text without validated resolution or provenance. |
| `tools/web/presentation-flow-audit.mjs` | Trace raw text to presentation sinks. |
| `tools/web/presentation-type-audit.mjs` | Detect forged resolved-text types. |
| `tools/web/presentation-completeness-audit.mjs` | Dynamic visible-completeness audit: execute the real consumers against the generated artefacts and classify every visible value (step 5 of `check presentation`). |
| `tools/web/presentation-completeness-detector.mjs` | Shared pure classifier for visible completeness, used by the dynamic audit and its self-tests. |
| `tools/web/presentation-gate.mjs` | Single entry point of `npm run check:presentation`; runs every phase unconditionally and preserves each phase's output and exit status. |
| `tools/web/load-kb-artefact.mjs` | Load generated KB artefacts for the completeness tools through the same TypeScript helper the test suites use. |

Their tests live in `tests/applications/warband_manager/presentation/completeness/`, not under `tools/`.

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
reports rules that reference a shared rule and also restate its prose
(informational, not a failure), while schemas and the knowledge pipeline guards
reject the retired `summary` key. Remove one-off migrations and diagnostics
after their result is materialized.
