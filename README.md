# Mordheim Utils

Monorepo with Mordheim utilities: a **knowledge-base-driven duel engine** and a
**campaign manager**, built on shared packages and a single canonical KB. The
two applications are distributed separately and share the domain, rule loading,
legal construction and the interface layer.

## Applications

| App | Package | Entry point | Description |
| --- | --- | --- | --- |
| Combat Lab | `mordheim_combat_lab` | `mordheim-combat-lab` | 1-vs-1 duel simulator with the modular engine (oracle) and the vectorized engine (analysis), semantic verification, parity and benchmarking. |
| Campaign Manager | `mordheim_campaign` | `mordheim-campaign-manager` | *Campaign-timeline-first* GUI prototype: immutable warband states, battles and the post-battle sequence. Warbands, profiles and equipment come from the canonical KB through `KnowledgePort`; campaigns are saved/loaded as `.mordheim` files. |

## Shared packages

```text
mordheim_core          pure types, injectable dice, effect composition
mordheim_knowledge     KB loading and validation (sources/knowledge), resource paths
mordheim_construction  profile compilation and equipment/choice legality
mordheim_combat        phases, modular engine (oracle), vectorized engine, kernel, native backend
mordheim_ui            shared Tkinter theme and generic widgets
```

The knowledge base lives once in `sources/knowledge/` (371 YAML files: warbands,
catalogues, mechanics and registry). The verification corpus — the structural
contract and the semantic scenarios — is test material and lives in
`tests/specs/`.

## Getting started

Requires Python 3.10 or later.

```powershell
python -m pip install -e ".[dev]"
```

### Central command line

`tools/mordheim-utils.py` is the single launcher for both applications and
every utility — a plain script, nothing to install. `--help` lists every
command; a delegated command keeps its own parser, so `... benchmark --help`
shows the exact detailed arguments of the real command:

```powershell
python tools/mordheim-utils.py --help                # overview of every command
python tools/mordheim-utils.py benchmark --help      # detailed arguments of one command
python tools/mordheim-utils.py combat-lab            # open the Combat Lab application
python tools/mordheim-utils.py warband-manager       # open the Campaign Manager application
python tools/mordheim-utils.py verify                # run the semantic specifications
python tools/mordheim-utils.py parity --require-complete
python tools/mordheim-utils.py tests --scope engines # run the engine test suites
python tools/mordheim-utils.py doctor                # environment, engines and KB location
```

The commands are `combat-lab`, `warband-manager`, `benchmark`, `parity`,
`test-report`, `verify`, `audit`, `validate`, `tests` (with `--scope` filters
and arbitrary pytest flags forwarded), `combine-kb`, `build-native` and
`doctor`. Each one just runs the matching module or script (`python -m
mordheim_combat_lab <command>` for the lab utilities, `python -m
mordheim_campaign`, `python -m pytest`, `tools/kb/combine_kb_yaml.py`), so
the underlying entry points remain callable directly and nothing drifts.

### Combat Lab

```powershell
python -m mordheim_combat_lab
python tools/mordheim-utils.py validate
python tools/mordheim-utils.py verify
python tools/mordheim-utils.py parity --require-complete
python tools/mordheim-utils.py test-report
python tools/mordheim-utils.py audit
python tools/mordheim-utils.py benchmark -n 100000
python -m pytest -q
```

`validate` checks structure and connections (including the contract of
`tests/specs/structural/phase-verification.yaml`). `verify` runs independent
semantic evidence; `verify --require-complete` is the strict gate. `audit`
writes the per-rule status CSV to `outputs/audit/`. The executable report, not a
figure copied here, is the source of the current status.

`parity` certifies the vectorized engine against the modular one. `benchmark`
measures engines with baselines and improvement/regression gates. `test-report`
writes the human CSVs of parity and technical tests into `outputs/test-report/`.

### Campaign Manager

```powershell
mordheim-campaign-manager
python -m mordheim_campaign
```

The prototype is interface-first: widgets consume view-models through
`AppController`, which in turn gets warbands, profiles, limits and equipment
offers from the canonical KB through `KnowledgePort` (`mordheim_knowledge`).
Managed campaigns are saved and loaded as self-contained `.mordheim` JSON files
(and exported as a Markdown summary) from `mordheim_campaign/persistence`. See
[the manager guide](docs/campaign-manager.md) and
[its architecture direction](docs/campaign-architecture.md).

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
docs/                     architecture, structure and task guides
tools/
  mordheim-utils.py       central launcher: both apps and every utility (no install)
  kb/                     KB helper scripts (combine_kb_yaml.py)
  windows/                Windows packaging scripts
```

See [the architecture](docs/architecture.md), the
[project structure guide](docs/structure.md) and the
[developer task guides](docs/README.md).

## Windows distribution

```powershell
tools\windows\build_MordheimCombatLab_ONEFILE.bat
tools\windows\build_MordheimCampaignManager.bat
```

Each build produces a standalone EXE that bundles the application and the
shared KB (`sources/knowledge/`); neither bundles `tests/`.
