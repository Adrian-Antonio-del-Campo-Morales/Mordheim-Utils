# Documentation

Reference material and procedures for the Mordheim Utils repository. Start
with the [repository overview](../README.md) for installation and the common
commands.

## Reference — how the system is built

- [Architecture](reference/architecture.md) — source layout, dependency
  boundaries and data flow.
- [Knowledge base](reference/knowledge-base.md) — canonical data, IDs,
  classification, translation and formatting policy.
- [Verification](reference/verification.md) — the certification layers,
  coverage and mutation gates, and what each one can prove.
- [Campaign Manager](reference/campaign-manager.md) — desktop/web capabilities
  and campaign lifecycle.

Contracts:

- [Campaign-file v5](../contracts/campaign-file-v5/README.md) — schema,
  fixtures and compatibility policy.
- [Knowledge-base editorial contract](../contracts/knowledge-editorial-v1/README.md)
  — one JSON Schema per maintained KB document (band packages, catalogue
  families, hireling and campaign catalogues, registry).

## Guides — how to change things

- [Modify the knowledge base](guides/modify-knowledge-base.md)
- [Implement and verify rules](guides/implement-and-verify-rules.md)
- [Modify an application](guides/modify-application.md)
- [Develop and release](guides/develop-and-release.md) — the fast loop, the
  release gates, measured performance optima and per-machine calibration.

## Decisions

- [Design rulings](decisions/design-rulings.md) — permanent design decisions
  that bind the KB, the engines or the applications.

Local orientation pages live next to the code they describe: the package
`README.md` files, `sources/knowledge/**/README.md` (catalogue modelling and
ownership rules) and `tests/specs/README.md` (verification-corpus conventions).

## Conventions

- Describe paths as they exist now (`packages/python/` and `apps/`).
- Executable commands, schemas, fixtures and tests are the source of truth for
  behaviour and status; reference pages do not copy volatile test counts,
  benchmark results or audit totals — they name the command that produces the
  live report.
- Unresolved product scope belongs in [TODO](../TODO.md).
- Generated material (`outputs/`, `build/generated/`, web `dist/`, staged
  knowledge JSON) is working data produced by commands: never hand-edit or
  commit it.
