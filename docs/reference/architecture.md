# Architecture

## Monorepo packages and allowed dependencies

```text
mordheim_core
  ↑
mordheim_knowledge → mordheim_construction → mordheim_combat
                  ↑          ↑
                  └ mordheim_combat_lab.application ← mordheim_combat_lab.persistence
                         ↑
                         mordheim_combat_lab.ui
                         mordheim_campaign (reuses mordheim_ui)

mordheim_combat_lab.verification → mordheim_knowledge + mordheim_construction
                                   + mordheim_combat + tests/specs
```

`mordheim_core` knows no YAML, UI or verifiers. `mordheim_combat` receives
`CompiledFighter` and never loads the KB. `mordheim_combat_lab.application`
runs use cases without Tkinter. Both applications present results with the
shared `mordheim_ui` layer and coordinate their own threads. `verification`
sits outside the runtime and exercises the real engine as the system under
test.

`mordheim_campaign` is interface-first: widgets depend on view-models and the
shared UI layer; canonical warbands and profiles enter through
`mordheim_campaign.application.knowledge_port` (on top of `mordheim_knowledge`)
and campaign persistence lives in `mordheim_campaign/persistence`.

## Shared resources

The KB lives once in `sources/knowledge/`. Path resolution belongs to
`mordheim_knowledge.paths` (`knowledge_root()`), with an override via the
`MORDHEIM_COMBAT_LAB_KNOWLEDGE_PATH` environment variable and frozen-EXE
support for both applications. The verification corpus lives in `tests/specs/`
(`specifications_root()`); it is test material and is not distributed.

## Path of a rule

1. The editorial rule and its binding live in `sources/knowledge/`.
2. `mordheim_knowledge` validates and loads documents by stable ids.
3. `mordheim_construction` validates access and compiles the binding into a
   `CompiledFighter`.
4. The engine consumes the effect in a phase or stateful handler.
5. A scenario in `tests/specs/` checks granting, compilation and the observable
   result.

## Engines

### Modular (oracle)

`mordheim_combat/modular/` is the scalar reference engine and the **only
correctness oracle**. It splits responsibility into state, context preparation,
attacks, pools, aftermath effects, rounds and duel orchestration:

- `state.py` — fighter/duel state and immutable transitions.
- `contexts.py` — prepared per-attack contexts shared by orchestration and
  verification.
- `attacks.py` / `pools.py` — reference attack resolution and pooled attacks.
- `aftermath.py` — stateful post-wound effects (fire, nets, black hunger, …).
- `rounds.py` — per-round state machine; `duel.py` — the public
  `simulate_duel` API.

Changing the oracle requires an independent semantic review and is outside the
optimization flow. Its behaviour is exercised by `tests/specs/` and is
considered critical: functional changes are treated as dangerous and must never
be made casually.

### Vectorized (analysis)

`mordheim_combat/vectorized/` is the NumPy batch engine used by the UI for
analysis; it is **not** the correctness oracle. It was split into a package
without changing its public namespace:

- `_types.py` — run constants, ledger types, tag predicates and compile-time
  helpers shared by every layer.
- `_operators.py` — stateless NumPy projections of the canonical scalar phase
  operators.
- `_attacks.py` — per-weapon attack preparation, hit/parry boundaries and wound
  resolution.
- `_driver.py` — per-round state machines, the batch loop and the public
  `simulate_duel` / `available_backends` entry points.
- `__init__.py` — facade that re-exports the historical module namespace so
  existing imports keep working unchanged.

The vectorized engine is certified against the modular oracle by
`mordheim_combat_lab.verification.parity` (per-field obligations, semantic
specifications and statistical six-sigma gates). A divergence detected while
working on the vectorized engine is presumed to be a defect of the candidate:
`parity` only reads the oracle and never modifies it.

### Native (compiled)

`mordheim_combat/native/` holds the sources of the compiled Cython backend.
The built extension keeps the historical module name
`mordheim_combat._combat_native` so importers and already-compiled binaries are
unaffected by the source layout:

- `_combat_compile.py` — pure-Python folding layer that reuses the exact
  certified helpers of the vectorized engine to flatten every per-duel tag
  decision into scalar flags once per duel.
- `_combat_native.pyx` / `.pxd` — the Cython core consuming the compiled plan
  with flat structs (`FighterC`, `SourceC`, `DuelC`, `StateC`); each round runs
  over the active rows in C with the same phase order and tables as the
  vectorized engine.
- `__init__.py` — package description; the root `mordheim_combat/_combat_compile.py`
  facade keeps the historical import path of compiled binaries working.

The Python driver (`simulate_duel` in `vectorized`) exposes the backend with
`backend="native"` or `"auto"`; `available_backends()` reports it only when the
extension is compiled, so an environment without a C compiler keeps the NumPy
behaviour unchanged. The engine uses one PCG32 per batch derived from the
request seed, so the same request is reproducible (deterministic replay per
seed).

### Verification and performance

The native backend is certified against the modular oracle with the same
six-sigma statistical gate as NumPy (`compare_statistical_parity(...,
backend="native")` shares the modular sample with NumPy), and the performance
gate requires at least one scenario to improve 10 % without regressions above
5 % versus NumPy (`benchmark --backend native`). `test-report --statistical`
and `parity --statistical` include the native backend automatically when it is
available; in the semantic CSV the per-operator cases do not apply to it
(`NOT_APPLICABLE`): the native engine is a complete duel engine without
independent operators, verified on the duel (statistical) rows, with operator
semantics covered by the NumPy adapter. While the extension is not compiled,
those rows are marked `NOT_AVAILABLE` and the report stays `PENDING` — a
signal of real pending work. Core C changes pass through AddressSanitizer
before integration (uninitialised struct overwrites, array sizing and batch
accumulation have already been detected and fixed that way).

## Package details

### Shared packages (`src/`)

| Package | Responsibility | Key modules |
| --- | --- | --- |
| `mordheim_core` | Pure domain: fighter models, requests, results, injectable dice, effect composition, cancellation. No YAML, no UI, no engines. | `models.py`, `dice.py`, `effects.py` |
| `mordheim_knowledge` | Loads and validates the KB documents by stable ids; resolves resource paths (`knowledge_root()`), with env-var override and frozen-EXE support. | `loader.py`, `paths.py` |
| `mordheim_construction` | Turns canonical ids and legal choices into `CompiledFighter`; enforces every restriction, prohibition, promotion and skill access. | `compiler.py`, `restrictions.py`, `selection.py`, `contracts.py` |
| `mordheim_combat` | Phases and the three engines. Consumes `CompiledFighter`; never loads the KB. | `phases.py`, `modular/`, `vectorized/`, `native/`, `vector_dice.py` |
| `mordheim_ui` | Shared Tkinter theme, colour tokens and generic widgets reused by both applications. | `lab_theme.py`, widgets |

### `mordheim_combat` in detail

- `phases.py` — the canonical phase model and pure local contracts (hit, wound,
  armour, injury, …) shared by every engine and by verification.
- `modular/` — scalar reference engine, the **only correctness oracle**.
  `duel.py` exposes `simulate_duel`; `rounds.py`, `aftermath.py`, `pools.py`,
  `attacks.py`, `contexts.py` and `state.py` split the stateful resolution
  chain.
- `vectorized/` — NumPy batch engine for analysis (see the package facade
  `__init__.py` and its internal `_types`, `_operators`, `_attacks`,
  `_driver` modules). The facade keeps the historical module namespace.
- `native/` — Cython sources of the compiled backend plus the pure-Python
  `_combat_compile.py` folding layer. The built extension is
  `mordheim_combat._combat_native`.
- `vector_dice.py` — batch-capable dice streams (NumPy PCG32) used by the
  vectorized and native engines.

The dependency direction between engines is strict: the modular engine is the
oracle; the vectorized and native engines are candidates that must be certified
against it and may never feed it.

### Combat Lab (`mordheim_combat_lab`)

| Area | Responsibility |
| --- | --- |
| `cli/` | Command-line entry points (`commands.py`, `benchmarking.py`) for validation, verification, parity, audit, test-report and benchmarking. |
| `application/` | Tkinter-free use cases: catalogue options, duel comparisons, execution settings. |
| `ui/` | The Tkinter simulator: windows, widgets, thread coordination and result presentation. Holds no rules. |
| `persistence/` | Versioned preferences and workbook files (stable ids on a hidden sheet, readable summaries on the visible ones). |
| `verification/` | Everything that checks the engines: semantic runner, inventory, interactions, mutations, audit CSV export and `parity/`. |

`verification/` is the critical area that keeps the engines honest:

- `verify` (semantic runner) executes `tests/specs/` against the real modular
  engine — never the reverse.
- `audit.py` / `audit_export.py` combine editorial inventory, scope and executed
  evidence into the per-rule status CSV without modifying the KB or the specs.
- `parity/` is the executable oracle contract, split into layered submodules
  (`_report.py` payloads, `_specifications.py` semantic adapters,
  `_vectorized.py` obligation inventory, `_statistical.py` sampling) with a
  facade `__init__.py` that re-exports the historical single-module API.
- `mutations.py` applies deliberate isolated faults (in-memory, restored even
  on failure) to prove the tests are not vacuous.
- `test_reporting.py` writes the Excel-friendly CSVs of parity and technical
  tests to `outputs/test-report/`.

### Campaign Manager (`mordheim_campaign`)

| Area | Responsibility |
| --- | --- |
| `application/` | KB read model (`knowledge_port.py`), UI-facing controller actions (`controller.py`) and view models/builders (`state.py`); the campaign-side rule consumers (hire eligibility, post-battle resolution/catalogue/engine). No Tkinter. |
| `persistence/` | `.mordheim` JSON save/load (marker + format version, stable KB ids only, never serialised rules) and Markdown summary export. |
| `ui/` | The interface-first application: dialogs, components, panels and the timeline `views/moments/` (initial draft, immutable states, battles, post-battle). |

Layer rule (executable in `tests/architecture/test_boundaries.py`):
`ui` never imports the KB loaders or YAML; `application` and `persistence`
never import Tkinter.

### Post-battle interaction boundary

`PostBattleMoment` owns the phase composition; reusable interaction pieces live
under `mordheim_campaign.ui.components` (`PostBattleSequence` for the ordered
eight-action navigator, `DiceResolutionCard` for the app-dice vs manual-entry
choice and contextual result actions such as **Buy** / **Hire**).

The rules layer lives in `mordheim_campaign.application`, not the widgets:
`PostBattleResolver` resolves injuries, exploration and rarity tests from the
catalogues, `PostBattleCatalogue` supplies the offers and per-action KB
provenance, and `PostBattleEngine` applies the outcomes and commits the next
state. The widgets only present results and trigger engine actions. Battle
facts remain in `BattleMoment` and are linked from Post-Battle rather than
duplicated as a workflow phase.

## Central CLI (`tools/mordheim-utils.py`)

`tools/mordheim-utils.py` is the single launcher for the whole project — a
plain script, nothing is installed, so a source checkout is enough. `--help`
lists every command; a delegated command keeps its own parser, so
`<command> --help` shows the real detailed arguments. Each command simply runs
the matching module or script from the repository root:

- `combat-lab`, `warband-manager` — launch the two graphical applications
  (`python -m mordheim_combat_lab ui`, `python -m mordheim_campaign`).
- `benchmark`, `parity`, `test-report`, `verify`, `audit`, `validate` —
  forwarded verbatim to the Combat Lab CLI (`python -m mordheim_combat_lab
  <command>`), so help text and behaviour never drift.
- `tests --scope <area>` — pytest with named areas (`all`, `engines`,
  `modular`, `vectorized`, `native`, `campaign`, `knowledge`, `verification`,
  `construction`, `ui`, `cli`, `architecture`); any unknown flag is forwarded
  to pytest (`-q`, `-k`, `-x`, …).
- `combine-kb`, `build-native` — run `tools/kb/combine_kb_yaml.py` and the
  editable native rebuild.
- `doctor` — reports the environment, installed engines and KB location.

Tab completion for bash/zsh: `source tools/completions/mordheim-utils.bash`
(also `.zsh`); it reads subcommands and options live from the real argparse
parsers.

## Tooling and outputs

- `tools/mordheim-utils.py` — the central launcher (see above); the
  underlying modules and scripts remain callable directly.
- `tools/kb/combine_kb_yaml.py` — combines each KB directory into single text
  files (e.g. to feed an editor or a review pass).
- `tools/kb/price-collation.py` — regenerates the price-collation report into
  `outputs/knowledge/` (git-ignored); page-verified verdicts persist in its
  committed sidecar `price-collation-resolutions.csv`.
- `tools/format_yaml.py` — repository YAML formatter (`--check` / `--write`,
  semantic-equivalence verified; does not touch `tests/specs/` or `outputs/`).
- `tools/mutate-engine.py` — the engine-mutation catalogue (L4, see
  [Verification](verification.md)).
- `tools/update-coverage-budget.py` — regenerates the coverage budget after
  adding tests.
- `tools/windows/*.bat` + `.iss` — PyInstaller/Inno Setup packaging for the two
  standalone Windows EXEs.
- `outputs/` (git-ignored) — generated reports: `audit/`, `test-report/`,
  `benchmarks/`, and throwaway scratch used during development.

## Where a change lands

| Change | Touch |
| --- | --- |
| Rule data | `sources/knowledge/` only — see [the KB guide](../guides/modify-knowledge-base.md) |
| Rule behaviour | the responsible engine layer, never the oracle casually — see [implement and verify rules](../guides/implement-and-verify-rules.md) |
| Legality/access | `mordheim_construction` |
| Verification evidence | `tests/specs/` + `mordheim_combat_lab/verification` |
| Simulator features | `mordheim_combat_lab/application` + `ui` |
| Campaign features | `mordheim_campaign/application` + `persistence` + `ui` |

## Tests and verification corpus

```text
tests/
  specs/
    structural/            phase-verification contract (effects ↔ phases ↔ consumers)
    semantic/              rules/, grants/, interactions/ scenario corpus
    interactions.yaml      required higher-order combinations
    interaction-policy.yaml risk policy and reviewed overrides
  architecture/            executable package/executable boundaries
  combat/                  engine tests: modular/, vectorized/, native/
  knowledge/ construction/ campaign/ cli/ verification/ ui/…
```

- The corpus under `tests/specs/` is the executable contract between the
  written rules and the engines; it is test material and is not distributed.
- Semantic scenarios fix the source, interpretation, category, initial status,
  dice, decisions, expectations and mutations. Dice and decision sources are
  strict: unexpected or unconsumed requests fail. Probabilities are expressed
  as exact fractions.
- The modular engine is the system under test; its output is never used to
  generate expected values.

See [Verification](verification.md) for how the layers fit together and
[the KB guide](knowledge-base.md) for how rule data reaches the engines.
