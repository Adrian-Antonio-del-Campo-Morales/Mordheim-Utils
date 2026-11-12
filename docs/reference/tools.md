# Repository tools

`tools/` contains reproducible automation or scripts that support an active
workflow. The usual entry point is `python tools/mordheim-utils.py --help`.
Specialized scripts are grouped by purpose, not language or caller.

## Main entry point

| Tool | Purpose |
|---|---|
| `tools/mordheim-utils.py` | Launch applications and centralize tests, checks, performance measurements, reports and diagnostics. |
| `tools/setup_worktree.py` | Give a checkout or git worktree its own `.venv` (editable install with the `dev` extra, native extension built in place, optional `npm ci` with `--node`) and verify that every project package and the native extension import from that checkout; `--check` only verifies. Standard library only, so it runs before a venv exists. |

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
python tools/mordheim-utils.py performance benchmark --scenarios basic --simulations 1000 --repeats 3
python tools/mordheim-utils.py performance benchmark --scenarios realistic-50 --simulations 300k --backend numpy
python tools/mordheim-utils.py performance calibrate --scenarios small --no-install
python tools/mordheim-utils.py check verify --json
python tools/mordheim-utils.py check report rules --output outputs/audit
python tools/mordheim-utils.py check parity --scenarios small --workers 4
python tools/mordheim-utils.py check samples status --scenarios big
python tools/mordheim-utils.py check coverage --json
python tools/mordheim-utils.py check presentation
python tools/mordheim-utils.py check ci
```

Use `<group> <command> --help` for what a command executes and which parser owns
its options. Measurement, audit and report commands may run tests, simulations
or write outputs; displaying help executes none of them.

## Shared options

Every engine tool — `performance benchmark`, `performance calibrate`,
`check parity` and `check samples` — spells one concept one way, with one
meaning. A tool that does not need an option does not offer it, and an option
a tool does not know is an error (`unrecognized arguments`).

| Option | Meaning |
|---|---|
| `--scenarios NAME...` | What runs; the same values in every tool (below). |
| `--simulations N` | Duels per scenario. Accepts `k`/`m` suffixes (`100k`, `1m`). |
| `--backend ENGINE...` | Engine(s): `modular`, `numpy`, `native`. |
| `--workers N` | Worker processes. |
| `--batch-size N` | Duels per engine batch. The batch selects the random streams, so a re-run must repeat it. |
| `--rounds N` | Round limit, replacing each scenario's own. |
| `--seed N` | Random seed. |
| `--output PATH` | Where the report is written. |
| `--json` | Print the report as JSON. |

`--scenarios` values (several values run their union, in the order given):

| Value | Selects |
|---|---|
| `small`, `normal`, `big` | The cumulative levels of the 43 precompiled scenarios: 8, 30 and all 43. |
| `basic`, `long`, … or `scenario/<name>` | One precompiled scenario. `long` is the 75-round stalemate scenario, never a level. |
| `realistic-50`, `realistic-100` | The cumulative curated sets of realistic duels; `realistic-50` is contained in `realistic-100`. Use them to measure performance. |
| `realistic/<nnn>` | One curated realistic duel (`realistic/000` … `realistic/099`). |
| `deliveries` | Every parity delivery (frozen configuration of a conformance scenario). |
| `delivery/<audit_id>/<id>` or `<audit_id>::<id>` | One parity delivery. |
| `battery` | Every case of the statistical battery. |
| `battery/<id>` | One battery case. |

Nothing narrows anything else: `--scenarios small heavy-grind` runs nine
scenarios. Precompiled scenarios and realistic duels load frozen fighters (no compilation), parity
deliveries pass their admission rules and run to 50 rounds, and battery cases
are compiled from the knowledge base. A selected case a tool cannot run is
listed with its reason, never dropped silently: a blocked or not-applicable
delivery, inputs no runner can express (initial-state overrides, auxiliary
participants, scripted dice) and — everywhere except `check parity`, whose
per-duel comparison passes them on — battery cases with scripted decisions.
An unknown token is reported as unknown immediately: only `deliveries`,
`delivery/...` keys and `<audit_id>::<id>` ids consult the delivery catalogue.

Under `tests`, `-n` is pytest-xdist's worker count: that option belongs to
pytest, not to these tools.

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
collects cases but does not execute bodies. Use `-n 6 --dist=load` to distribute
engine tests; concurrency contracts retain real inner pools capped at two workers.

## Tests: purpose and selection

The testing strategy has three complementary layers:

- **Modular mechanics:** check game rules directly in the reference engine,
  where failures are easiest to isolate and debug.
- **Source-backed integration:** knowledge contracts, construction tests and
  the rules-conformance suite check the KB -> compiler -> modular combat path.
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
`modular`, `vectorized`, `native`, `kb`, `conformance`) and **performance** (`benchmark`,
`calibrate`). Three cross-cutting test selections keep the integrity suites
reachable without forcing them into those categories: `parity` (statistical
comparisons and their tooling), `shared` (common engine contracts and frozen
inputs) and `tooling` (architecture, launcher, coverage and verification-tool
checks).

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
| `conformance` | none | `pytest tests/conformance` (the rules-conformance suite). |
| `conformance` | `scenarios` | `pytest tests/conformance/execution`. |
| `conformance` | `integrity` | `pytest tests/conformance/integrity`. |
| `parity` | `statistical` | `pytest tests/engines/parity/statistical`. |
| `parity` | `tooling` | `pytest tests/tooling/parity`. |
| `shared` | none | `pytest tests/engines/shared`. |
| `tooling` | `architecture` | `pytest tests/tooling/architecture`. |
| `tooling` | `web` | Vitest `architecture` project in both workspaces (purity and web boundaries). |
| `tooling` | `launcher` | `pytest tests/tooling/launcher`. |
| `tooling` | `coverage` | `pytest tests/tooling/coverage`. |
| `tooling` | `verification` | `pytest tests/tooling/verification`. |

Selection rules:

- A bare selection runs what its help says. `tests modular` runs mechanics and
  runtime; `tests tooling` runs architecture, launcher, coverage and
  verification; `tests parity` runs statistical and tooling.
- Each path group of a selection runs as its own pytest process, so options
  apply per group. `tests/engines/modular/runtime` and
  `tests/engines/vectorized/runtime` own inner process pools and always run
  serially: xdist options (`-n`, `--dist`, ...) are dropped for them with a
  notice. Every pytest call adds `-rfEs`, so skip reasons stay visible; a
  later `-r` of yours overrides it.
- `tests native` first imports the native extension with the same interpreter
  and paths; without it the launcher exits 1 instead of reporting a run in
  which every test was skipped.
- `tests kb` runs the **knowledge** suite only; there is no `knowledge`
  subsection alias. Construction is a large battery and stays a separate
  subsection instead of being bundled silently; the rules-conformance suite is
  its own `conformance` selection.
- `tests warband-manager` has no shared default: pytest and Vitest do not accept
  the same options, so choose `python` or `web`.
- Several subsections can be named together: `tests modular mechanics runtime`.
- `tests env` is the diagnostics entry point: it runs in process and takes no
  runner options. There is no separate `doctor` command. It also imports the
  project packages and the native extension with the current interpreter in a
  clean process, without the launcher's path set-up, and exits 1 when they
  resolve to another checkout; an interpreter outside this checkout's `.venv`
  is only noted, since CI installs into its own Python. Fix a failure with
  `python3 tools/setup_worktree.py`.

```powershell
python tools/mordheim-utils.py tests --help
python tools/mordheim-utils.py tests modular --help
python tools/mordheim-utils.py tests modular mechanics --help
python tools/mordheim-utils.py tests conformance --help
python tools/mordheim-utils.py tests kb --list
python tools/mordheim-utils.py tests conformance -q
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
  no unrelated suite is appended. It must lie inside the selection (the chosen
  subsection's paths, otherwise the section's directories); anything else is
  refused with exit code 2, so `tests vectorized tests/engines/modular/...`
  cannot run the modular engine under another label. Everything after `--`
  goes to the runner unchanged, apart from the serial-group rule above.
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

Worker counts are examples, not forced defaults. Keep collection, shared
writers and timing-sensitive measurements serial. Engine concurrency contracts
use inner pools of at most two workers; other test execution is distributed by
xdist. A skip does not prove native
execution; exit code 5 means that every Python group of the selection was
empty. Listing/collection and
runner self-checks do not certify rule behavior or statistical equivalence.

| Command | Parallel option |
|---|---|
| `tests` / direct pytest | `-n 8 --dist=load` for independent tests |
| Vitest via npm | `--maxWorkers=8`; file parallelism is already built in |
| `check parity` | `--workers 8` for modular-reference sampling; `--workers auto` uses the runner's automatic policy |
| `check samples sample` | `--workers 8` chunks in parallel, for any engine |
| `performance benchmark` | `--workers 8` for explicit multicore measurements |
| `performance calibrate` | Already measures worker configurations; no extra worker option |
| `tests env`, `check verify`, `check report rules`, `check coverage`, `check presentation`, `check ci`, `app` | No worker-count option exposed by these entries; do not append unsupported flags |

`tests parity statistical -n 6 --dist=load -q` is supported. Ordinary sampling
checks use sequential inner execution; tests specifically verifying concurrent
queues or process scheduling retain pools capped at two workers.

For time-to-solution measurements, `--strategies` makes the benchmark compare
execution strategies per engine, modular oracle included:

```powershell
python tools/mordheim-utils.py performance benchmark --scenarios small --backend numpy --strategies "sequential,processes=8,parallel=8"
python tools/mordheim-utils.py performance benchmark --scenarios big --backend modular --simulations 5000 --strategies "sequential,processes=12,parallel=12,parallel=12:48"
```

`sequential` and `processes=N` (one scenario per worker) apply to every
engine; `parallel=N` splits each scenario inside a pool (NumPy by batch plan,
modular by duel range through `mordheim_combat.modular.parallel`, with
`parallel=N:C` choosing the modular chunk count); native runs whole samples
only. The summary lists the best strategy per engine and cell with its
speedup over that engine's sequential pass; the modular oracle ignores the
batch axis and runs once per simulation size. Pool workers receive the
precompiled fighters, so catalogue loading never enters a pooled wall time.

Keep benchmark measurements isolated from other workloads. Do not wrap real
parity campaigns or benchmarks in xdist; their CLI worker controls remain
independent of pytest. Engine pytest selections can run together with `-n 6`.
Collection and typechecks are not accelerated by xdist.

### Inputs and catalogues

Engine tests load checked-in `compiled-cases.json` and `compiled-builds.json`
under `tests/engines/fixtures/`. Their loaders and conftest fixtures are required;
ordinary execution does not regenerate inputs or fall back to compilation when
a frozen input is missing. Knowledge, construction and conformance tests retain their
source-backed preparation.

- `precompiled_catalog.py` defines 43 unified scenarios with stable
  `scenario/<name>` keys. The cumulative levels `small`, `normal` and `big`
  select the same inputs for parity, benchmarks and calibration; `big` includes
  all 43. Its `select_scenarios` resolves every tool's `--scenarios` values.
  Seeds, sample widths and batch sizes are execution settings.
- `realistic_sets.py` lists the curated realistic duels by their stable
  `realistic/<nnn>` keys in `compiled-cases.json`: `realistic-50` and
  `realistic-100` (cumulative). See [Realistic performance sets](#realistic-performance-sets).
- `mordheim_combat_lab/verification/parity/_battery_cases.py` declares the
  122 battery cases (`--scenarios battery`): short duels built from the
  knowledge base, so they are compiled rather than frozen.
- `run_parity` is the one statistical runner: every selection, every engine
  and every round limit goes through it.

### Realistic performance sets

The 43 precompiled scenarios were chosen to cover rules: they over-represent
rare fighters and edge cases, so a speedup measured on them need not transfer
to the duels the application actually runs. Measure performance on
`realistic-50` (day-to-day) or `realistic-100` (confirmation); keep the 43
scenarios for correctness and parity.

No usage data exists yet, so the sets come from a synthetic population that
`tools/verification/realistic_population.py` draws from the rosters, the
equipment lists and a game expert's answers (all warbands, Mordheim and
Trollheim, equally likely; members weighted by how many a warband can field;
campaigns of 4-8 games with heroes averaging under three advances and
henchmen half as many; the expert's frequent skills; two weapons and the
dagger dominant, armour uncommon; every duel opens with a charge; no Hired
Swords). The curator then selects the duels whose feature shares (heroes,
wounds, attacks, loadout, armour, skills, advances, parry, saves, large
creatures, Trollheim …) track that population within about 1.5 points, so a
plain mean over a set is representative without weights. 300,000 simulations
per duel is the expected application width; on the NumPy engine
`realistic-50` takes about five minutes and `realistic-100` about ten.

The sets are frozen: the duels are ordinary cases in `compiled-cases.json`
(campaign advances are applied to the compiled characteristics, bounded by the
racial maximum, because the compiler has no advance input), and
`benchmarks/reference/realistic-population.json` keeps the whole population,
each duel's build, features and set membership for review. Regenerate only to
change the population model; the same seed reproduces the same sets:

```powershell
python -m tools.verification.realistic_population --draws 1200 --seed 1          # fidelity table only
python -m tools.verification.realistic_population --draws 1200 --seed 1 --write  # rewrite corpus, registry, reference
```

`--write` re-exports every existing case through the corpus exporter, so their
fingerprints are reproduced, and replaces only the `realistic/*` cases.
Benchmark baselines measured on the earlier sets are not comparable afterwards.

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
performance certification. Calibration can still be costly with
`--scenarios small`, and the saved profile changes later measurements on this machine.
Its batch sizes also change the NumPy and native sampled results for a given
seed, because each batch draws its own random stream. The profile records the
machine, engine digests, native build and source revision; one applied on
another machine or engine prints a provenance warning and is still used.

`performance benchmark` options:

| Option | Meaning |
|---|---|
| `--scenarios`, `--backend`, `--seed` | Shared options; without `--scenarios` a run measures `small`. |
| `--simulations N[,N...]` | Duels per scenario (default 100: a smoke size). |
| `--batch-size N[,N...]` | NumPy/native batch (default 100,000). A list in either option sweeps every combination. |
| `--warmups N`, `--repeats N` | Untimed and timed runs; the median is reported. |
| `--workers N` | One scenario per worker; reports the pool's wall time and concurrency. |
| `--strategies LIST` | Time-to-solution study (below). |
| `--profile` | cProfile one sequential configuration; saves `.pstats` beside `--output`. |
| `--baseline PATH` | Compare with a saved single-configuration report. |
| `--require-improvement [PCT]` | Fail unless some scenario improves by PCT % (default 10) and none regresses past `--max-regression` (default 5). |
| `--output PATH`, `--json` | `.json` (also the baseline file), `.csv` or `.md`; print JSON. |

The default `--simulations 100` is a smoke size: pass real simulation counts
for measurements. The sequential wall-time summary separates timed engine
samples, warm-up executions and genuine setup overhead (interpreter start and
catalogue load).

A baseline is just a saved `--output <file>.json`. The gate compares only like
measurements: simulations, batch size, seed, warmups, repeats, `--workers` and
the backend list must match, or the gate exits 2. All three engines participate — a modular baseline gates
modular optimization work the same way as the optimized backends. A
(scenario, backend) pair the baseline measured but the current run did not,
such as a native unit that failed, fails the gate. Differences in machine,
engine digests, build or revision are reported as provenance warnings and
never fail it. With `--workers N` the report gives the pool's wall time and
sample concurrency, which is not a speedup over a sequential run.

`benchmark --profile` runs the timed repeats under cProfile on a
single-configuration sequential run, prints each backend's top functions and
writes per-backend `.pstats` files beside `--output` (default
`outputs/benchmarks/`). Profiled timings include instrumentation overhead, so
they locate hotspots and cannot feed a gate.

`performance calibrate` takes `--scenarios` (default `big`; the NumPy sweeps
narrow `big` to `normal`, because a NumPy duel costs 3-5x a native one),
`--simulations` (the sequential sweep; the worker sweep runs twice as many),
`--seed`, `--output`, `--json`, `--no-install` and `--reset`.

## Checks and reports

Each entry explains what it executes in `<entry> --help`.

| Entry | Executes |
|---|---|
| `check verify` | `python -m mordheim_combat_lab verify`: KB structure, editorial schemas, execution contract, binding contracts and default profile compilation. It is a structural gate, not the knowledge or rules-conformance test suites (see [Verification](verification.md#deterministic-modular-evidence)). |
| `check report rules` | `python -m tools.knowledge.clauses report`: every classified rule effect, mechanic and item with its scope, binding and declared clause coverage (`rules-inventory.csv`, `clause-coverage.csv`, `summary.json` in `outputs/audit/`). |
| `check report tests` | `python -m mordheim_combat_lab test-report`: runs the test suite and writes an Excel-friendly technical CSV (`--output DIR`). |
| `check parity` | `python -m mordheim_combat_lab parity`: compare the optimized engines with the modular oracle now (or, without `--scenarios`, the exact obligation checks). Its pytest checks are `tests parity statistical`. |
| `check samples` | `python -m tools.verification.parity_samples`: sample one engine into a store; compare stored samples later. |
| `check coverage` | `python -m mordheim_combat_lab coverage-gate`: measure deterministic engine coverage and check the recorded budget; `--update-budget` replaces it deliberately after review. |
| `check presentation` | `npm run check:presentation` in `apps/warband-manager-web`: detector tests, strict deep text audit and dynamic visible-completeness audit. |
| `check ci` | Local integration gate, in order: KB generation and freshness, the Python net (campaign-file, architecture and `tests/knowledge`, including its `web/` audits), shared-eligibility transport, the eligibility bundle, TypeScript typecheck/tests, and web typecheck/lint/tests/build plus bundle guards. It does not run the rules-conformance suite or its coverage non-regression control, which CI runs as separate steps; add `tests conformance` for integration changes. |

```powershell
python tools/mordheim-utils.py check verify --json
python tools/mordheim-utils.py check report rules --output outputs/audit
python tools/mordheim-utils.py check report tests --output outputs/test-report
python tools/mordheim-utils.py check parity --scenarios battery --simulations 7200 --workers 4 --require-complete
python tools/mordheim-utils.py check coverage --json
python tools/mordheim-utils.py check presentation
python tools/mordheim-utils.py check ci
```

A strict `--require-complete` parity gate needs `--simulations 7200` or more:
below that a passing case is `UNDERPOWERED`; see the
[verification reference](verification.md) for the power rule.

`check ci` runs its configured checks and builds; it is not a complete
engine-certification campaign. Use `tests` for suites and `check parity` for the
comparison; neither substitutes for the other.

## Comparing engines: `check parity`

`check parity` runs the modular oracle and the selected candidates now and
compares their outcome distributions with the six-sigma gate. Without
`--scenarios` only the exact obligation checks of the vectorized engine run
(no sampling, about a second); `--require-complete` then fails unless every
obligation is verified.

| Option | Meaning |
|---|---|
| `--scenarios` | What runs (shared values); scenarios, parity deliveries and battery cases can be mixed. |
| `--backend` | `numpy` (default), `native` or both. `modular` alone only executes the oracle: rows report `COMPLETED` or the error, with no comparison and no approval. |
| `--simulations` | Duels per scenario and engine (default 10,000). Below 7,200 a passing case is `UNDERPOWERED`: compared, never approved. |
| `--rounds N[,N...]` | Each value replaces every case's round limit; a list runs each case once per value, which shows defects that only shift *when* duels resolve. |
| `--seed`, `--workers N\|auto` | Sample seed; worker processes for the oracle (`auto` pools only samples estimated over ~20 s). |
| `--require-complete` | Fail unless every selected case passed. |
| `--output`, `--json` | Report as `.json` or `.md`; print JSON. |

A case that cannot run is `INCOMPATIBLE` (a declared limitation: listed, not a
failure, but the run is not complete) or `NOT_RUN` (a missing frozen case or a
preparation crash: a failure). The report records the provenance of the run:
engine digests, native build, commit and dirty state.

```powershell
python tools/mordheim-utils.py check parity
python tools/mordheim-utils.py check parity --scenarios small --workers 4
python tools/mordheim-utils.py check parity --scenarios big --backend numpy native --simulations 100k --workers 4 --output outputs/parity/big.md

# Executability only: one duel per scenario on the oracle
python tools/mordheim-utils.py check parity --scenarios big deliveries battery --backend modular --simulations 1 --workers 4

# Round horizons, and the battery at an acceptance width
python tools/mordheim-utils.py check parity --scenarios basic heavy-grind --rounds 2,4,8,15
python tools/mordheim-utils.py check parity --scenarios battery --simulations 7200 --require-complete
```

`--workers 8` cannot split a single duel across workers. Engine samples are
seeded per case, so the totals do not depend on the worker count.

## Stored samples: `check samples`

`check samples` (`python -m tools.verification.parity_samples`) samples one
engine at a time into a store, chunk by chunk, and compares stored samples
later without running either engine again — so the expensive oracle sample is
taken once and reused. Its sub-commands:

| Command | Options |
|---|---|
| `sample` | `--backend` (required), `--scenarios`, `--simulations` (default 10,000), `--batch-size`, `--rounds`, `--seed`, `--workers`, `--replace`, `--store` |
| `compare` | `--backend` candidate (default `numpy`), `--reference` engine (default `modular`), `--reference-store`, `--scenarios`, `--simulations` (compared width; default the widest common coverage), `--output` (report directory), `--store` |
| `status` | `--scenarios`, `--store` |

The store defaults to `outputs/parity-store`. Records are written as lossless
`.json.gz`; readers accept `.json` and `.json.gz` (plain JSON wins when both
exist), and a resumed record keeps its format.

```bash
python tools/mordheim-utils.py check samples sample --backend numpy --scenarios big --simulations 100k --batch-size 2500 --workers 2 --store outputs/parity-numpy
python tools/mordheim-utils.py check samples compare --backend numpy --scenarios big --simulations 100k --store outputs/parity-numpy --reference-store tests/engines/parity/reference_samples/modular-100k
python tools/mordheim-utils.py check samples status --scenarios big --store outputs/parity-numpy
```

`--reference` chooses what the candidate is judged against. `modular` is the
oracle. `numpy` with `--backend numpy` compares the engine with its own earlier
sample in `--reference-store`: the same seed and batch draw the same duels, so a
change meant to preserve results must leave every stored chunk count equal.
The six-sigma gate only approves; compare the records' chunk counts for equality.
`--backend native --reference numpy` cross-checks the native port; native was
ported from NumPy, so their agreement never exonerates a shared deviation —
only the oracle does.

`tests/engines/parity/reference_samples/numpy-big-200k` stores the NumPy
engine's own outcomes over the 43 scenarios at 200,000 duels each (batch
100,000, seed 2026), recorded before the rule-algorithm optimization work. It
carries no oracle, so it detects whether a later revision moved the engine's
results; it never establishes that those results are correct. Its own README
gives the self-check command.

The stored delivery parity campaigns at 100,000 duels per delivery are also versioned:
`tests/engines/parity/reference_samples/modular-deliveries-100k` (oracle) and
`tests/engines/parity/reference_samples/numpy-deliveries-100k` (candidate). Each store
contains 2,678 records with seed 2026 and a 50-round limit. Modular retains its
original oracle samples. The NumPy and Native candidate stores were refreshed
on 2026-11-04 from the stores under
`D:/DEVEL/CC CLI/outputs BCKPU/parity-refresh-20261104-c10000/e2e/`,
preserving the original compressed files byte for byte, including counts,
chunks, timestamps, environment and engine digests. Each candidate record has
100,000 duels in ten 10,000-duel chunks, produced from clean commit `38f4c12f`.

`tests/engines/parity/reference_samples/native-deliveries-100k` holds the corresponding
Native candidate store. Both candidate scenario sets match the 2,678-record
Modular oracle. The refreshed comparisons report 2,677 approved and 1 divergent
for NumPy, and 2,567 approved and 111 divergent for Native. Another 2,485 parity
deliveries are rejected before sampling and remain explicit in the reports.
These are stored candidate results, not parity acceptance.
The import was verified with the sample-store reader for all 5,356 candidate
records, checking byte-for-byte copies, input fingerprints, seed, round limits,
contiguous chunks, outcome totals and current engine digests. All stored
Modular references remained byte-identical; no simulations were rerun.

```bash
python tools/mordheim-utils.py check samples compare --backend numpy --scenarios deliveries --simulations 100k --store tests/engines/parity/reference_samples/numpy-deliveries-100k --reference-store tests/engines/parity/reference_samples/modular-deliveries-100k --output outputs/parity-deliveries-stored/compare
python tools/mordheim-utils.py check samples sample --backend modular --scenarios deliveries --simulations 100k --batch-size 500 --workers 2 --store outputs/parity-modular-deliveries
```

Sampling resumes finished chunks. Comparison executes neither engine. It
checks fighter fingerprints, seeds, round limits and sample coverage, and
decides every pair with the six-sigma gate over first wins, second wins and
unresolved duels. A row whose sample cannot detect a 5-point shift (fewer than
7,200 duels) is `underpowered`, compared but never approved.

Stored samples are meant to outlive engine changes, so provenance never blocks.
Each record keeps the source digest of everything its engine executes (a
modular change moves all three digests, because the candidates import modular
helpers), the source commit, whether the checkout was dirty and, for native,
the built extension's SHA-256. `compare` still decides samples taken by another
engine version, from uncommitted sources or before revisions were recorded,
and prints each such difference as a `PROVENANCE WARNING` grouped per engine
with the number of samples it affects; the report repeats them under
`provenance_warnings` and lists recorded and current digests in its config.
A comparison against a historical reference does not certify the current
engine. `sample` extends a record from another engine version with a warning,
and each new chunk then records its own provenance; `--replace` discards such
a record instead. Only a different experiment identity (fighters, seed, round
limit or batch size) is refused, so a new `--rounds` value needs another store
or `--replace`.

The sampled engine is digested where it was imported from, with a warning when
that is not this checkout. Pool workers must import exactly the parent's engine
files; otherwise the run stops with exit code 2, because a single sample would
mix engines.

`sample --workers N` runs up to N chunks in separate processes for all three
engines; the default is 1, in-process. Workers share a bounded queue across
scenarios and the parent alone writes records, so seeds and counts match
sequential sampling with the same `--batch-size`. A first Ctrl+C stops new
submissions and saves in-flight chunks; a second aborts immediately; rerun the
same command to resume. Sampling prints one start and one completion line per
case (the completion line carries that case's elapsed wall time; concurrent
cases overlap, so do not sum them) and returns 1 while any selected case is
unfinished. Delivery sample files use `delivery__<sha256(case_key)>.json.gz` names to
avoid long Windows paths; stores keep winner counts only.

On Windows, access/sharing locks during the atomic sample-file replacement
trigger up to six retries with increasing waits (2.55 seconds total). A persistent
lock still fails, leaving the previous sample intact and the new temporary file
available; unrelated I/O errors fail immediately. Retrying the replacement does
not rerun duels or change the sample counts.

### Delivery parity campaigns

Delivery parity campaigns reuse frozen combat configurations with random dice, rather than
replaying the original test's scripted dice and exact assertions. Combats run
until termination or 50 rounds. Preparing a delivery does not establish engine
compatibility or statistical parity. The [delivery format and admission rules](verification.md#parity-deliveries)
define which inputs can execute; blocked, not-applicable, stale, invalid and
incompatible deliveries keep their reasons in every report. A failed or
disagreeing decision-policy probe or a corrupt delivery catalogue stops the run
(exit 2) before anything is sampled. A small successful sample does not certify
full engine parity. The [parity charter](../../tests/engines/parity/README.md)
explains deliveries, stored samples and reference stores in one place.

These catalogues require a source checkout with `tests/engines/fixtures` and
its frozen JSON files; the battery also requires the KB/compiler.

## Knowledge base

Permanent validation and generation:

| Tool | Purpose |
|---|---|
| `tools/knowledge/export_compiled_cases.py` | Python export API for explicit compiled case plans; reads the KB during fixture generation. |
| `tools/knowledge/audit_kb_conformance.py` | Check canonical knowledge against the expected model. |
| `tools/knowledge/audit_schema_strictness.py` | Detect gaps and unintended permissiveness in editorial schemas. |
| `tools/knowledge/clauses.py` | Clause inventory of the knowledge base and its declared test coverage: `inventory`, `coverage [--pending]`, `check` (unknown references, inconsistencies) and `report` (the CSVs behind `check report rules`). Engine-free. |
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
| `tools/diagnostics/zscores.py` | Rank a saved `parity-campaign.json` by gate ratio (difference over the campaign tolerance; above 1 is a failed comparison) and raw z-score, over every compared magnitude. Reads the report only; runs no engine. |
| `tools/verification/generate_compiled_builds.py` | Capture missing build preparations and publish the union with frozen entries (`--write`); not part of ordinary test execution. Records a KB and compiler fingerprint, warns when frozen entries were compiled from other sources, and exits 1 on compile failures or blocked consumers. |

## Web interface

| Tool | Purpose |
|---|---|
| `tools/web/build-eligibility.mjs` | Generate the versioned Python bundle from the shared TypeScript eligibility module; `--check` rejects stale output. Exposed as `npm run build:eligibility` / `npm run check:eligibility`. |
| `tools/web/presentation-audit.mjs` | Static GUI text audit (single mode: all GUI sources, resolved types, full flow trace); `--check` exits 1 on any finding. Exposed as `npm run audit:gui`; its leak/control corpus is `presentation-audit-corpus.test.mjs`. |
| `tools/web/presentation-flow-audit.mjs` | Trace raw text to presentation sinks. |
| `tools/web/presentation-type-audit.mjs` | Detect forged resolved-text types. |
| `tools/web/presentation-completeness-audit.mjs` | Dynamic visible-completeness audit: execute the real consumers against the generated artefacts and classify every visible value (phase 3 of `check presentation`). |
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
