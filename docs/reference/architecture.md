# Architecture

## Source layout

```text
sources/knowledge/                         canonical YAML data
packages/python/core/mordheim_core          pure domain types, dice and effects
packages/python/knowledge/mordheim_knowledge loaders, validation, paths and i18n
packages/python/roster-construction         profile/equipment legality and compilation
packages/python/combat-engine               phases plus modular, NumPy and native engines
packages/python/adapters/desktop-ui         shared Tkinter theme and widgets
packages/python/campaign                    campaign domain, application and persistence
apps/combat-lab/mordheim_combat_lab         Combat Lab UI, CLI and verification
apps/warband-manager-desktop/mordheim_desktop desktop composition root
apps/warband-manager-web                    React/Vite browser shell
packages/typescript                         shared web domain, application and adapters
contracts/campaign-file-v4                  neutral persistence contract and fixtures
tests                                      Python, TypeScript and web integration tests
```

The old `src/` package layout is retired. `pyproject.toml` and the test configuration list the package roots explicitly; editable installation from the repository root is the supported Python setup.

## Dependency boundaries

```text
knowledge YAML → mordheim_knowledge → mordheim_construction → mordheim_combat
                                         ↓
                              Combat Lab application → Tkinter UI

knowledge YAML → mordheim_knowledge → Campaign application → desktop UI
                                                    ↘ persistence

knowledge-web.json → web KnowledgeReader → TypeScript domain/application → React shell
```

- `mordheim_core` has no YAML, UI, filesystem or engine dependency.
- `mordheim_knowledge` owns path resolution, YAML loading, validation and display-name/i18n access.
- `mordheim_construction` turns canonical IDs and legal choices into `CompiledFighter`.
- `mordheim_combat` consumes compiled fighters and never loads YAML.
- Combat Lab `application` is Tkinter-free; its `ui` owns windows, widgets and thread coordination.
- Campaign `application` owns use cases and state transitions; campaign `ui` presents results and forwards actions.
- UI layers do not load YAML. `tests/architecture/test_boundaries.py` enforces that rule, as well as the ban on Tkinter imports in campaign application/persistence.
- The web app consumes generated JSON and does not use YAML, Python packages or browser storage for campaigns.

## Shared resources and entry points

`mordheim_knowledge.paths.knowledge_root()` resolves `sources/knowledge/`, including the `MORDHEIM_COMBAT_LAB_KNOWLEDGE_PATH` override and frozen-executable support. The semantic verification corpus is under `tests/specs/` and is test material, not a runtime resource.

Python entry points declared in `pyproject.toml`:

- `mordheim-combat-lab` → `mordheim_combat_lab.cli.commands:main`
- `mordheim-campaign-manager` → `mordheim_desktop.app:main`

The source-checkout launcher `tools/mordheim-utils.py` delegates to these modules and to the real web/pytest/generator commands.

## Combat engines

### Modular oracle

`packages/python/combat-engine/mordheim_combat/modular/` is the scalar reference implementation and the only correctness oracle. Its state, context, attack, pool, aftermath, round and duel modules resolve the stateful close-combat flow. Changes to it require semantic review against the written sources.

### NumPy candidate

`mordheim_combat/vectorized/` is the batch engine for analysis. `_operators.py` contains local projections, `_attacks.py` handles attack preparation and wound resolution, `_driver.py` runs the batch state machine, and the package facade preserves the public import surface. It is certified against the modular oracle by the parity tools.

### Native candidate

`mordheim_combat/native/` contains the optional Cython implementation and its pure-Python compile/folding layer. The extension is `mordheim_combat._combat_native`. Machines without a compatible compiler retain the NumPy backend. `available_backends()` reports what is actually installed.

## Campaign Manager

The campaign domain is timeline-first:

```text
Initial draft → State #0 → Battle #1 → Post-Battle #1 → State #1 → …
```

The draft is editable. Committed states are immutable snapshots. Battles preserve table facts and open a pending post-battle. The post-battle engine applies outcomes and commits the next state.

The desktop application lives in `packages/python/campaign/mordheim_campaign/`, with the Tkinter composition root in `apps/warband-manager-desktop/`. The web shell lives in `apps/warband-manager-web/` and reuses the TypeScript domain/application packages from `packages/typescript/`.

## Persistence boundary

`.mordheim` files use format v4, defined by `contracts/campaign-file-v4/campaign-file-v4.schema.json`. Both Python and TypeScript readers/writers accept only v4, reject retired v1–v3 and future versions, and preserve open payload maps. Campaign files contain stable KB IDs and campaign state, never the rule catalogues themselves.

The desktop persistence module is `packages/python/campaign/mordheim_campaign/persistence/campaigns.py`. The web adapter is `packages/typescript/adapters/campaign-file/`. PDF export is implemented independently by the desktop persistence layer and the web export feature.

## Verification corpus and reports

`tests/specs/` is the executable link between written KB rules and the modular engine. `apps/combat-lab/mordheim_combat_lab/verification/` runs semantic verification, audit export, parity, coverage and mutations.

Generated reports are written below ignored `outputs/`:

- `audit/` — rule inventory and review status.
- `test-report/` — semantic and technical CSVs.
- `parity/` — machine-readable parity certificates.
- `benchmarks/` — benchmark results.

The web knowledge artefact is generated under ignored `build/generated/knowledge-web/` and copied to the web app's ignored `public/knowledge/` staging directory by CI/`run-ci`.

## Where a change lands

| Change | Location |
| --- | --- |
| Canonical rules/data | `sources/knowledge/` |
| Profile/equipment legality | `packages/python/roster-construction/` |
| Combat behavior | `packages/python/combat-engine/` |
| Combat Lab use case/UI | `apps/combat-lab/` |
| Campaign domain/application/persistence | `packages/python/campaign/` |
| Desktop composition | `apps/warband-manager-desktop/` |
| Web domain/application/adapters | `packages/typescript/` |
| Web shell and presentation | `apps/warband-manager-web/` |
| Verification evidence | `tests/specs/`, `tests/verification/`, related test suites |
| Build/release tooling | `tools/`, `.github/workflows/` |

See [Knowledge base](knowledge-base.md), [Campaign Manager](campaign-manager.md) and [Verification](verification.md) for the detailed contracts.
