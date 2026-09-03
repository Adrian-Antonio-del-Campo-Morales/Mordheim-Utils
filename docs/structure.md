# Project structure

This guide explains what each part of the repository is responsible for and how
the pieces relate. Start here, then read the [Architecture](architecture.md) for
the rules and the [task guides](README.md) for frequent workflows.

## Layers at a glance

```text
                    ┌────────────────────────────────────────────┐
                    │              sources/knowledge/            │  canonical KB
                    └───────────────────┬────────────────────────┘
                                        │ load + validate
                    ┌───────────────────▼────────────────────────┐
                    │              mordheim_knowledge             │  loaders, paths
                    └───────────────────┬────────────────────────┘
                                        │ compile + legality
                    ┌───────────────────▼────────────────────────┐
                    │             mordheim_construction           │  CompiledFighter
                    └───────────────────┬────────────────────────┘
                                        │ duel request
                    ┌───────────────────▼────────────────────────┐
                    │                mordheim_combat              │  engines
                    │  modular (oracle) │ vectorized │ native     │
                    └───────────────────┬────────────────────────┘
                                        │ results, verdicts
                    ┌───────────────────▼────────────────────────┐
                    │           mordheim_combat_lab               │  app 1: Combat Lab
                    │  cli │ application │ ui │ verification      │
                    └───────────────────┬────────────────────────┘
                                        │
                    ┌───────────────────▼────────────────────────┐
                    │             mordheim_campaign               │  app 2: Manager
                    │  application │ persistence │ ui             │
                    └────────────────────────────────────────────┘
```

Pure domain types (`mordheim_core`) and the shared Tk layer (`mordheim_ui`) are
depended on from above and know nothing about the KB or the engines.

## Shared packages (`src/`)

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
  `_combat_compile.py` folding layer. The root facade
  `src/mordheim_combat/_combat_compile.py` keeps the historical import path
  used by already-compiled binaries. The built extension is
  `mordheim_combat._combat_native`.
- `vector_dice.py` — batch-capable dice streams (NumPy PCG32) used by the
  vectorized and native engines.

The dependency direction between engines is strict: the modular engine is the
oracle; the vectorized and native engines are candidates that must be certified
against it and may never feed it.

## Combat Lab (`mordheim_combat_lab`)

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

## Campaign Manager (`mordheim_campaign`)

| Area | Responsibility |
| --- | --- |
| `application/` | KB read model (`knowledge_port.py`), UI-facing controller actions (`controller.py`) and view models/builders (`state.py`). No Tkinter. |
| `persistence/` | `.mordheim` JSON save/load (marker + format version, stable KB ids only, never serialised rules) and Markdown summary export. |
| `ui/` | The interface-first prototype: dialogs, components, panels and the timeline `views/moments/` (initial draft, immutable states, battles, post-battle). |

Layer rule (executable in `tests/architecture/test_boundaries.py`):
`ui` never imports the KB loaders or YAML; `application` and `persistence`
never import Tkinter.

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

## Tooling and outputs

- `tools/kb/combine_kb_yaml.py` — combines each KB directory into single text
  files (e.g. to feed an editor or a review pass).
- `tools/windows/*.bat` + `.iss` — PyInstaller/Inno Setup packaging for the two
  standalone Windows EXEs.
- `outputs/` (git-ignored) — generated reports: `audit/`, `test-report/`,
  `benchmarks/`, and throwaway scratch used during development.

## Where a change lands

| Change | Touch |
| --- | --- |
| Rule data | `sources/knowledge/` only — see [modify-kb](tasks/modify-kb.md) |
| Rule behaviour | the responsible engine layer, never the oracle casually — see [implement-rule](tasks/implement-rule.md) |
| Legality/access | `mordheim_construction` |
| Verification evidence | `tests/specs/` + `mordheim_combat_lab/verification` |
| Simulator features | `mordheim_combat_lab/application` + `ui` |
| Campaign features | `mordheim_campaign/application` + `persistence` + `ui` |

See the [Architecture](architecture.md) for allowed dependencies and the
responsibility map, and the [task guides](README.md) for the exact workflows.
