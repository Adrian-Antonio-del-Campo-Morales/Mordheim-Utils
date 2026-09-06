# Documentation

Three kinds of documents, kept apart on purpose:

- **Reference** — what things are and how they work. Descriptive, stable.
- **Guides** — step-by-step procedures for frequent tasks.
- **Decisions** — development records: audit ledgers, rulings and backlogs.

## Reference

| Document | Content |
| --- | --- |
| [Architecture](reference/architecture.md) | Packages, layers, allowed dependencies, the three engines and the central CLI. |
| [Knowledge base](reference/knowledge-base.md) | Layout of `sources/knowledge/`, rule classification, loaders, path of a rule, golden rules. |
| [Campaign Manager](reference/campaign-manager.md) | The campaign application: timeline model, layers, post-battle pipeline, features. |
| [Verification](reference/verification.md) | The layered testing strategy, the interaction matrix, reports and runtime budgets. |

## Guides

| Document | Task |
| --- | --- |
| [Modify the knowledge base](guides/modify-knowledge-base.md) | Change rule/table data safely. |
| [Implement and verify rules](guides/implement-and-verify-rules.md) | Add combat behaviour, author semantic evidence, resolve rulings, diagnose failures. |
| [Modify an application](guides/modify-application.md) | Add a use case to Combat Lab or the Campaign Manager. |
| [Develop and release](guides/develop-and-release.md) | Per-change loop, release gates, packaging, performance gate. |

## Decisions

| Document | Content |
| --- | --- |
| [Design rulings](decisions/design-rulings.md) | Permanent development decisions that bind the KB, engines or applications. |
| [Modular source audit](decisions/modular-audit.md) | Audit record: findings M01–M28 status, additional findings, NumPy/native porting backlog. Retire once resolved. |

## Generated reports

- `outputs/` (git-ignored) — audit CSVs, parity certificates, test reports,
  benchmarks, and the Trading Post price collation
  (`python tools/kb/price-collation.py` regenerates `outputs/knowledge/price-collation.md`,
  the surviving review queue of differing list prices).
  Always regenerate; never hand-edit. Page-verified verdicts for the collation
  live in the committed sidecar `tools/kb/price-collation-resolutions.csv`.

## Project-level

- Root [README](../README.md) — monorepo overview, install, central CLI.
- [TODO](../TODO.md) — actionable backlog (KB gaps, campaign integration).
