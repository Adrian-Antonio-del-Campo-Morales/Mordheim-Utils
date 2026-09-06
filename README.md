# Mordheim Utils

Monorepo with Mordheim utilities: a **knowledge-base-driven duel engine** and a
**campaign manager**, built on shared packages and a single canonical KB. The
two applications are distributed separately and share the domain, rule loading,
legal construction and the interface layer.

## Applications

| App | Package | Entry point | Description |
| --- | --- | --- | --- |
| Combat Lab | `mordheim_combat_lab` | `mordheim-combat-lab` | 1-vs-1 duel simulator with the modular engine (oracle) and the vectorized engine (analysis), semantic verification, parity and benchmarking. |
| Campaign Manager | `mordheim_campaign` | `mordheim-campaign-manager` | *Campaign-timeline-first* GUI: immutable warband states, battles and the post-battle sequence. Warbands, profiles and equipment come from the canonical KB through `KnowledgePort`; campaigns are saved/loaded as `.mordheim` files. |

## Shared packages

```text
mordheim_core          pure types, injectable dice, effect composition
mordheim_knowledge     KB loading and validation (sources/knowledge), resource paths
mordheim_construction  profile compilation and equipment/choice legality
mordheim_combat        phases, modular engine (oracle), vectorized engine, native backend
mordheim_ui            shared Tkinter theme and generic widgets
```

The knowledge base lives once in `sources/knowledge/`. The verification
corpus — the structural contract and the semantic scenarios — is test material
and lives in `tests/specs/`.

## Getting started

Requires Python 3.10 or later.

```powershell
python -m pip install -e ".[dev]"
python tools/mordheim-utils.py --help        # overview of every command
python tools/mordheim-utils.py doctor        # environment, engines and KB location
```

### Central command line

`tools/mordheim-utils.py` is the single launcher for both applications and
every utility — a plain script, nothing to install. A delegated command keeps
its own parser, so `... benchmark --help` shows the exact detailed arguments
of the real command:

```powershell
python tools/mordheim-utils.py combat-lab                  # open the Combat Lab application
python tools/mordheim-utils.py warband-manager             # open the Campaign Manager application
python tools/mordheim-utils.py verify                      # run the semantic specifications
python tools/mordheim-utils.py parity --require-complete
python tools/mordheim-utils.py tests --scope deterministic # per-change engine gate
```

Commands: `combat-lab`, `warband-manager`, `benchmark`, `parity`,
`test-report`, `verify`, `audit`, `validate`, `coverage-gate`, `tests` (with
`--scope` filters and arbitrary pytest flags forwarded), `combine-kb`,
`build-native` and `doctor`. Each one just runs the matching module or script,
so the underlying entry points remain callable directly and nothing drifts.

Tab completion (bash/zsh): `source tools/completions/mordheim-utils.bash`
(also `.zsh`) — completion is read live from the real argparse parsers.

### Applications

```powershell
python -m mordheim_combat_lab          # Combat Lab
python -m mordheim_campaign            # Campaign Manager
```

### Validation and verification (Combat Lab side)

```powershell
python tools/mordheim-utils.py validate                  # KB structure and connections
python tools/mordheim-utils.py verify                    # semantic specifications
python tools/mordheim-utils.py parity --require-complete # vectorized/native certification
python tools/mordheim-utils.py audit                     # per-rule status CSV in outputs/audit/
python tools/mordheim-utils.py test-report               # Excel-ready CSVs in outputs/test-report/
python tools/mordheim-utils.py benchmark -n 100000
python -m pytest -q                                      # everything
```

`validate` checks structure and connections (including the contract of
`tests/specs/structural/phase-verification.yaml`). `verify` runs independent
semantic evidence; `verify --require-complete` is the strict gate. The
executable reports, not figures copied into docs, are the source of current
status. How the verification layers fit together:
[Verification](docs/reference/verification.md).

> **Warning — long-running certification.** The `--deep`/`--truncations`
> parity tiers, the full `test-report`, `coverage-gate` and
> `tools/mutate-engine.py` take minutes to hours by design. They are point
> runs — after large modifications or before a release — not the per-change
> loop. Trimmed versions for small checks are listed in
> [Verification](docs/reference/verification.md).

## Documentation

| Document | Content |
| --- | --- |
| [docs/README.md](docs/README.md) | Documentation index. |
| [Architecture](docs/reference/architecture.md) | Packages, layers, engines, central CLI. |
| [Knowledge base](docs/reference/knowledge-base.md) | `sources/knowledge/` layout and golden rules. |
| [Verification](docs/reference/verification.md) | Layered testing strategy, interaction matrix, runtime budgets. |
| [Campaign Manager](docs/reference/campaign-manager.md) | Campaign application reference. |
| [Guides](docs/guides/) | Frequent tasks (KB changes, rules, applications, release). |
| [TODO](TODO.md) | Actionable backlog. |

## Repository map

```text
sources/knowledge/        single canonical KB consumed by the runtime
src/
  mordheim_core/          shared domain (no YAML, no UI, no engines)
  mordheim_knowledge/     KB loaders + validators + resource paths
  mordheim_construction/  CompiledFighter and legality
  mordheim_combat/        phases, modular engine, vectorized engine, native backend
  mordheim_ui/            shared Tk theme and widgets
  mordheim_combat_lab/    app 1: cli, ui, application, persistence, verification
  mordheim_campaign/      app 2: application, persistence, ui
tests/
  specs/                  structural contract + semantic scenarios (verification corpus)
  architecture/           boundaries between packages and executables
docs/                     reference / guides / decisions
tools/
  mordheim-utils.py       central launcher: both apps and every utility (no install)
  kb/                     KB helper scripts (combine_kb_yaml.py, price-collation.py)
  windows/                Windows packaging scripts
```

## Windows distribution

```powershell
tools\windows\build_MordheimCombatLab_ONEFILE.bat
tools\windows\build_MordheimCampaignManager.bat
```

Each build produces a standalone EXE that bundles the application and the
shared KB (`sources/knowledge/`); neither bundles `tests/`.
