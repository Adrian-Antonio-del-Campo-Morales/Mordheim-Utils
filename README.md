# Mordheim Utils

Mordheim Utils is a Python/TypeScript monorepo for Mordheim campaign management and close-combat simulation. It has a Combat Lab application, a web campaign manager, a shared knowledge base, and a versioned campaign-file contract.

## What is implemented

| Surface | Package / entry point | Purpose |
| --- | --- | --- |
| **Combat Lab** | `mordheim-combat-lab` or `python -m mordheim_combat_lab` | Tkinter simulator and CLI for compiled 1-vs-1 close-combat duels, analysis, parity, verification and benchmarks. |
| **Campaign Manager — web** | `apps/warband-manager-web` | React/Vite application with the campaign workflow, rules browser, statistics, `.mordheim` import/export and PDF export. Campaigns remain in memory until exported. |

The active runtime scope of the duel engine is **one-against-one close combat**. Shooting, movement, psychology, mounts and magic are classified in the knowledge base but are not duel-engine features.

## Repository layout

```text
sources/knowledge/                         canonical YAML knowledge base
packages/python/core/mordheim_core          pure domain types and dice
packages/python/knowledge/mordheim_knowledge KB loaders, validation and paths
packages/python/roster-construction         legal profile/equipment compilation
packages/python/combat-engine               phases, modular, NumPy and native engines
packages/python/adapters/desktop-ui         shared Tkinter theme and widgets
packages/python/campaign                    campaign domain, application and persistence
apps/combat-lab                             Combat Lab application and CLI
apps/warband-manager-web                    React/Vite web shell
contracts/campaign-file-v5                  versioned campaign-file contract
contracts/knowledge-editorial-v1             JSON Schemas of the KB documents (bands, catalogue, registry)
tests/python                                Python suites, one directory per package, app or contract
tests/web                                   web app suite (Vitest + Testing Library), mirrors the app's `src/`
tests/typescript                            TypeScript package suite, mirrors `packages/typescript`
tests/fixtures                              shared versioned fixtures: parity vectors and campaign corpus
tests/specs                                 the semantic verification corpus
docs                                        reference, guides, decisions, module pages and KB modelling docs
tools                                       every support script: KB passes, verification, web audits, ingestion, launcher
```

Support code lives in `tools/` (runnable scripts), `docs/` (prose) and `tests/`
(the suites and the shared fixtures they read); the application and package
directories carry product code only. `tools/` is grouped by what the script
works on — `kb/`, `verification/`, `web/`, `knowledge/`, `ingestion/`,
`windows/` — and the tests mirror the tree they exercise:
`tests/python/<package|app|contract>/`, `tests/web/` and `tests/typescript/`.
The root [`package.json`](package.json) is an npm workspace over
`packages/typescript` and `apps/warband-manager-web`: one `npm ci` at the root
installs both and writes the single `package-lock.json`.

The modular combat engine is the correctness oracle. NumPy and native backends are candidates certified against it. The campaign applications consume the same canonical IDs and the v5 campaign-file contract; rules are never serialized into campaign files.

## Requirements and installation

- Python 3.10+ with Tkinter for the desktop applications.
- Node.js 20+ for the TypeScript packages and web application.

```powershell
python -m pip install -e ".[dev]"
npm ci                          # from the repository root: installs both npm workspaces
```

The Python package uses the source layout declared in `pyproject.toml`; editable installation is the supported way to make all packages importable.

## Central launcher

`tools/mordheim-utils.py` is a source-checkout launcher. It delegates to the real application parsers, pytest, the knowledge generator or the native build instead of maintaining duplicate option definitions.

```powershell
python tools/mordheim-utils.py --help
python tools/mordheim-utils.py doctor
python tools/mordheim-utils.py combat-lab
python tools/mordheim-utils.py verify        # KB gate: --structural for structure only
python tools/mordheim-utils.py report rules  # or `report tests` for the test CSVs
python tools/mordheim-utils.py parity --require-complete
python tools/mordheim-utils.py calibrate     # measure this machine's optima
python tools/mordheim-utils.py tests --scope deterministic
python tools/mordheim-utils.py run-ci
```

The commands are grouped by task (applications, knowledge base, engines,
repository); `--help` lists them and `<command> --help` opens the delegated
parser.

## Validation and development loop

Fast checks for a change:

```powershell
python tools/mordheim-utils.py verify --structural
python tools/mordheim-utils.py tests --scope deterministic
npm run typecheck               # TypeScript packages and web app
npm test                        # both Vitest suites (packages/typescript and tests/web)
npm run lint                    # ESLint over the workspace + the presentation gate
cd apps/warband-manager-web && npm run build   # typecheck + Vite build
```

The npm commands run from the repository root and fan out to the workspaces;
`npm test` covers `tests/typescript/` and `tests/web/`, so the web suite needs
the generated KB artefact (`outputs/web-public/knowledge/`) as described below.

Release-oriented checks are described in [Develop and release](docs/guides/develop-and-release.md). The expensive parity/deep, coverage and mutation commands are intentional point-in-time gates, not the default edit loop.

The web knowledge artefact is generated, never hand-edited:

```powershell
python tools/knowledge/generate_knowledge_web.py
python tools/knowledge/generate_knowledge_web.py --check
```

It is generated into `outputs/web-public/knowledge/`; Vite serves that directory as its public assets. Generated output is ignored.

## Documentation

- [Documentation index](docs/README.md)
- [Architecture and package boundaries](docs/reference/architecture.md)
- [Architecture and package ownership](docs/reference/architecture.md)
- [Knowledge-base reference](docs/reference/knowledge-base.md)
- [Verification strategy](docs/reference/verification.md)
- [Campaign-file v5 contract](contracts/campaign-file-v5/README.md)
- [Guides](docs/guides/)
- [Permanent design rulings](docs/decisions/design-rulings.md)
- [Current backlog](docs/TODO.md)

Generated reports belong under ignored `outputs/`; they are regenerated from code and are not documentation or release assets. Screenshots, temporary campaign files and local build products are not part of the repository.

## Windows packaging

The supported build scripts are:

```powershell
tools\windows\build_MordheimCombatLab_ONEFILE.bat
```

They build the current package layout and bundle `sources/knowledge/`. They are Windows-only packaging helpers; CI publishes the web application separately through GitHub Pages.
