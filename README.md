# Mordheim Utils

Tools for managing Mordheim campaigns and exploring one-on-one close combat. This Python/TypeScript monorepo contains two applications backed by a shared, structured knowledge base.

**[Open the published Campaign Manager](https://mordheim-warband-manager.win/)** — use the web application directly in your browser, with no local installation required.

| Application | What you can do |
| --- | --- |
| **Campaign Manager** · web | Build and manage warbands, record battles and post-battle progression, browse rules and statistics, import/export `.mordheim` campaigns, and export warband PDFs. |
| **Combat Lab** · desktop and CLI | Configure duelists, simulate close-combat duels, analyse results, and run engine verification, parity checks and benchmarks. |

The applications share canonical knowledge and [equipment and skill eligibility](docs/reference/eligibility.md). Each manages its own participants and state; Combat Lab does not import Campaign Manager rosters.

[Quick start](#quick-start) · [Common commands](#common-commands) · [Development](#development) · [Documentation](docs/README.md)

## Quick start

To run the applications locally or work on the project, follow the steps below. Run commands from the repository root, preferably inside a Python virtual environment.

### Requirements

- **Python 3.10+**; CI uses Python 3.12.
- **Tkinter** for the Combat Lab desktop interface. Check availability with `python -m tkinter`.
- **Node.js 20 (20.19+) or 22.12+** and npm for the web application and TypeScript development. CI uses Node.js 22.

Combat Lab uses the checked-in eligibility JavaScript through MiniRacer, so it does not need Node.js at runtime. A C compiler is optional: installation skips the native combat backend when no compatible compiler is available.

### Install

```powershell
python -m pip install -e ".[dev]"
npm ci
python tools/mordheim-utils.py doctor
```

The editable Python install makes the packages in this source checkout importable. `npm ci` installs both npm workspaces from the root lockfile. For Combat Lab alone, omit `npm ci`.

### Run Campaign Manager locally

Generate the browser's knowledge data before the first launch:

```powershell
python tools/knowledge/generate_knowledge_web.py
python tools/mordheim-utils.py campaign-manager
```

Open the local URL printed by Vite. To choose a port, append `--port 5199 --strictPort`. Stop the server with `Ctrl+C`.

**Export your campaign before refreshing or closing the page.** Campaigns live in memory; they are not automatically saved to browser storage. Import the exported `.mordheim` file to resume later.

### Open Combat Lab

```powershell
python tools/mordheim-utils.py combat-lab
```

The installed `mordheim-combat-lab` entry point and `python -m mordheim_combat_lab` also expose the application CLI. Use `python -m mordheim_combat_lab --help` to explore its commands.

## Combat scope and verification

The duel engine resolves **one combatant against one combatant in close combat**. Group combat, terrain/weather, shooting, spellcasting and independently simulated mounts or companions are outside its scope. Supplied individual conditions and combat modifiers can affect a duelist without simulating their external producer. See the [architecture](docs/reference/architecture.md#modular-duel-scope) for the precise boundary.

The modular engine is the correctness oracle. NumPy and optional native backends are candidates checked against it by the parity tools. A rule's presence in the knowledge base does not establish runtime support or certification; consult the [verification strategy](docs/reference/verification.md) and [current backlog](TODO.md) for the acceptance boundaries and pending work.

## Common commands

The source-checkout launcher delegates to application commands and repository tools. Run `python tools/mordheim-utils.py --help` for the full list, or append `--help` to a command for its options.

| Task | Command |
| --- | --- |
| Check the local environment | `python tools/mordheim-utils.py doctor` |
| Validate KB structure | `python tools/mordheim-utils.py verify --structural` |
| Validate the KB and semantic specifications | `python tools/mordheim-utils.py verify` |
| Generate the rule inventory | `python tools/mordheim-utils.py report rules` |
| Generate test reports | `python tools/mordheim-utils.py report tests` |
| Run deterministic engine checks | `python tools/mordheim-utils.py tests --scope deterministic` |
| Check engine parity | `python tools/mordheim-utils.py parity --require-complete` |
| Measure local engine optima | `python tools/mordheim-utils.py calibrate` |
| Run the web presentation checks | `python tools/mordheim-utils.py check-presentation` |
| Run the local CI validation gates | `python tools/mordheim-utils.py run-ci` |

Reports and local working artefacts belong under ignored `outputs/`.

## Development

### Knowledge data and shared eligibility

The browser reads generated JSON from `outputs/web-public/knowledge/`, served by Vite as public assets. Regenerate it after changing canonical knowledge or its generator, and check that the output is current:

```powershell
python tools/knowledge/generate_knowledge_web.py
python tools/knowledge/generate_knowledge_web.py --check
```

Never hand-edit generated browser assets. Campaign files store canonical IDs under the [v5 contract](contracts/campaign-file-v5/README.md); they do not embed rule definitions.

After editing `packages/typescript/domain/eligibility/`, rebuild and check the Python runtime bundle:

```powershell
npm run build:eligibility
npm run check:eligibility
```

Unlike browser assets, the generated `_eligibility.js` is versioned and must be committed with its maintained TypeScript source. Both applications consume the same eligibility rules: the browser imports TypeScript directly, while Python executes the bundle through MiniRacer.

### Checks and web build

Choose checks for the area you changed. Python test scopes include `modular`, `construction`, `knowledge`, `ui`, `cli` and `architecture`; extra pytest arguments are forwarded, for example `tests --scope construction -q`.

Run npm commands from the repository root after generating the browser knowledge data:

```powershell
npm run typecheck
npm test
npm run lint
npm run build
```

`npm test` runs the TypeScript package and web suites. `npm run lint` includes the presentation gate; `npm run build` typechecks and builds the web application into `apps/warband-manager-web/dist/`.

See [Test classification and execution order](docs/reference/test-sequence.md) for the phase categories and repair order, and [Develop and release](docs/guides/develop-and-release.md) for release checks, coverage, mutation testing, benchmarks and calibration. Expensive parity and certification runs are separate from the focused edit loop.

## Repository layout

| Path | Contents |
| --- | --- |
| `apps/combat-lab/` | Combat Lab desktop interface, CLI and application services |
| `apps/warband-manager-web/` | React/Vite Campaign Manager |
| `packages/python/` | Core types, knowledge loaders, fighter construction and combat engines |
| `packages/typescript/` | Campaign domain, application services, adapters and shared eligibility |
| `sources/knowledge/` | Canonical YAML knowledge base |
| `contracts/` | Campaign-file and knowledge editorial schemas |
| `tests/python/`, `tests/typescript/`, `tests/web/` | Package and application test suites |
| `tests/specs/`, `tests/E2E/`, `tests/fixtures/` | Semantic specifications, E2E corpus and shared fixtures |
| `tools/` | Launcher, knowledge generation, verification, web checks and Windows packaging |
| `docs/` | References, guides, design decisions and backlog |

## Documentation

Start with the [documentation index](docs/README.md), or go directly to a task:

- [Understand the architecture](docs/reference/architecture.md)
- [Modify an application](docs/guides/modify-application.md)
- [Modify the knowledge base](docs/guides/modify-knowledge-base.md)
- [Implement and verify rules](docs/guides/implement-and-verify-rules.md)
- [Work with campaign knowledge](docs/guides/campaign-knowledge.md)
- [Maintain shared eligibility](docs/reference/eligibility.md)
- [Follow web presentation conventions](docs/reference/web-presentation.md)
- [Find repository tools](docs/reference/tools.md)
- [Consult permanent design rulings](docs/decisions/design-rulings.md)
- [Find pending problems and decisions](TODO.md)

## Windows packaging

After installing the Python dev dependencies, build a single-file Combat Lab executable or its installer:

```powershell
tools\windows\build_MordheimCombatLab_ONEFILE.bat
tools\windows\build_MordheimCombatLab_INSTALLER.bat
```

The packages bundle the knowledge base, generated eligibility JavaScript and MiniRacer runtime. Rebuild and check the eligibility bundle before packaging changes to its source. See [Develop and release](docs/guides/develop-and-release.md#windows-packaging) for the packaging procedure. The web application is published separately through the [GitHub Pages workflow](.github/workflows/deploy-pages.yml).

## License

See [LICENSE](LICENSE) for the project's MIT license.
