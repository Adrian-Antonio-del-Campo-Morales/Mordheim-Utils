# Components

This page summarizes application and package ownership. See
[Architecture](architecture.md) for the complete dependency structure.

## Combat Lab

The desktop simulator separates three layers:

- `application/` prepares catalogues, comparisons and settings without Tkinter.
- `ui/` owns windows, widgets, thread coordination and visual adaptation. It
  contains no rules, construction validation or simulation loops.
- `verification/` runs `tests/specs/` against the modular engine and generates
  inventories and reports without modifying their sources.

`persistence` stores versioned preferences and workbooks; `construction`
compiles configurations; `mordheim_combat` runs simulations. Workbooks keep
stable IDs on a hidden sheet and readable summaries on visible sheets.

The modular engine is the semantic oracle. NumPy and native backends are
certified separately with `python -m mordheim_combat_lab parity`; a candidate
divergence does not authorize changing the oracle. Generate reports with
`python -m mordheim_combat_lab test-report`. See [Verification](verification.md)
and [Develop and release](../guides/develop-and-release.md).

## Warband Manager

The web application is the active campaign-management product. Its React shell
lives in `apps/warband-manager-web/`; shared domain and use-case code lives in
`packages/typescript/` and is not duplicated in the shell.

Campaigns use v5 documents, immutable history and editable drafts. Rules and
knowledge are resolved through application ports. The UI does not load YAML or
bypass the campaign service. It does not depend on Combat Lab, NumPy, Cython or
Tkinter, and browser storage is not a substitute for campaign files.

Common root commands:

| Command | Purpose |
|---|---|
| `npm ci` | Install the locked workspace. |
| `npm test` | Run TypeScript and web tests. |
| `npm run typecheck` | Check both workspaces. |
| `npm run lint` | Run ESLint and the presentation contract. |
| `npm run build` | Build the production web application. |
| `python tools/mordheim-utils.py run-ci` | Run local pre-publication gates. |

See [Modify an application](../guides/modify-application.md), the
[campaign contract](../../contracts/campaign-file-v5/README.md) and
[web presentation](web-presentation.md).

## Python packages

| Package | Responsibility |
|---|---|
| `mordheim_core` | Pure types, dice and composition; no KB, engine, UI or verifier loading. |
| `mordheim_construction` | Convert IDs and legal choices into `CompiledFighter`. |
| `mordheim_combat` | Modular, vectorized and native phases and engines; consumes compiled fighters and does not load YAML. |
| `mordheim_knowledge` | Load and validate canonical knowledge. |
| `mordheim_campaign` | Campaign domain, use cases and v5 persistence. |
| `mordheim_ui` | Shared desktop presentation adapters. |

See [Implement and verify rules](../guides/implement-and-verify-rules.md) when
adding behavior.
