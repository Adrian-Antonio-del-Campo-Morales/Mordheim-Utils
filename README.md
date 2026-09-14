# Mordheim Utils

Mordheim Utils is a Python/TypeScript monorepo for Mordheim campaign management and close-combat simulation. It has two user-facing applications, a shared knowledge base, and a versioned campaign-file contract.

## What is implemented

| Surface | Package / entry point | Purpose |
| --- | --- | --- |
| **Combat Lab** | `mordheim-combat-lab` or `python -m mordheim_combat_lab` | Tkinter simulator and CLI for compiled 1-vs-1 close-combat duels, analysis, parity, verification and benchmarks. |
| **Campaign Manager — desktop** | `mordheim-campaign-manager` or `python -m mordheim_desktop` | Tkinter campaign timeline with draft construction, immutable states, battles, a canonical 10-step post-battle sequence presented through 8 UI actions, persistence and PDF export. |
| **Campaign Manager — web** | `apps/warband-manager-web` | React/Vite browser application with the campaign workflow, rules browser, statistics, `.mordheim` import/export and PDF export. Campaigns remain in memory until exported. |

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
apps/warband-manager-desktop                desktop composition root
apps/warband-manager-web                    React/Vite web shell
contracts/campaign-file-v4                  versioned campaign-file contract
tests                                     Python, TypeScript and web-contract tests
docs                                      reference, guides and design decisions
tools                                     launcher, generators, reports and packaging
```

The modular combat engine is the correctness oracle. NumPy and native backends are candidates certified against it. The campaign applications consume the same canonical IDs and the v4 campaign-file contract; rules are never serialized into campaign files.

## Requirements and installation

- Python 3.10+ with Tkinter for the desktop applications.
- Node.js 20+ for the TypeScript packages and web application.

```powershell
python -m pip install -e ".[dev]"
cd packages/typescript
npm ci
cd ../../apps/warband-manager-web
npm ci
```

The Python package uses the source layout declared in `pyproject.toml`; editable installation is the supported way to make all packages importable.

## Central launcher

`tools/mordheim-utils.py` is a source-checkout launcher. It delegates to the real application parsers, pytest, the knowledge generator or the native build instead of maintaining duplicate option definitions.

```powershell
python tools/mordheim-utils.py --help
python tools/mordheim-utils.py doctor
python tools/mordheim-utils.py combat-lab
python tools/mordheim-utils.py warband-manager
python tools/mordheim-utils.py validate
python tools/mordheim-utils.py verify
python tools/mordheim-utils.py parity --require-complete
python tools/mordheim-utils.py tests --scope deterministic
python tools/mordheim-utils.py run-ci
```

Available command groups are graphical applications, combat benchmarks/parity, knowledge-base verification, testing/CI, KB generation and native-backend building. Use `<command> --help` for delegated options. Bash and zsh completions live in `tools/completions/`.

## Validation and development loop

Fast checks for a change:

```powershell
python tools/mordheim-utils.py validate
python tools/mordheim-utils.py tests --scope deterministic
cd packages/typescript && npm run typecheck && npm test
cd ../../apps/warband-manager-web && npm run typecheck && npm run lint && npm test
```

Release-oriented checks are described in [Develop and release](docs/guides/develop-and-release.md). The expensive parity/deep, coverage and mutation commands are intentional point-in-time gates, not the default edit loop.

The web knowledge artefact is generated, never hand-edited:

```powershell
python tools/knowledge/generate_knowledge_web.py
python tools/knowledge/generate_knowledge_web.py --check
```

It is staged into `apps/warband-manager-web/public/knowledge/` by CI or `run-ci`; generated build output is ignored.

## Documentation

- [Documentation index](docs/README.md)
- [Architecture and package boundaries](docs/reference/architecture.md)
- [Campaign Manager reference](docs/reference/campaign-manager.md)
- [Knowledge-base reference](docs/reference/knowledge-base.md)
- [Verification strategy](docs/reference/verification.md)
- [Campaign-file v4 contract](contracts/campaign-file-v4/README.md)
- [Guides](docs/guides/)
- [Permanent design rulings](docs/decisions/design-rulings.md)
- [Current backlog](TODO.md)

Generated reports belong under ignored `outputs/`; they are regenerated from code and are not documentation or release assets. Screenshots, temporary campaign files and local build products are not part of the repository.

## Windows packaging

The supported build scripts are:

```powershell
tools\windows\build_MordheimCombatLab_ONEFILE.bat
tools\windows\build_MordheimCampaignManager.bat
```

They build the current package layout and bundle `sources/knowledge/`. They are Windows-only packaging helpers; CI publishes the web application separately through GitHub Pages.
