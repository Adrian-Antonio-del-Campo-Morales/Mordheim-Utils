# Documentation

This index separates stable project knowledge from generated output and historical implementation notes.

## Start here

- [Repository overview](../README.md) — applications, installation and common commands.
- [Architecture](reference/architecture.md) — source layout, dependency boundaries and data flow.
- [Campaign Manager](reference/campaign-manager.md) — desktop/web capabilities and campaign lifecycle.
- [Knowledge base](reference/knowledge-base.md) — canonical data, IDs, scope and validation.
- [Verification](reference/verification.md) — deterministic tests, parity, coverage and release gates.
- [Campaign-file v4 contract](../contracts/campaign-file-v4/README.md) — schema, fixtures and compatibility policy.

## Guides

- [Modify the knowledge base](guides/modify-knowledge-base.md)
- [Implement and verify rules](guides/implement-and-verify-rules.md)
- [Modify an application](guides/modify-application.md)
- [Develop and release](guides/develop-and-release.md)

## Decisions and local references

- [Design rulings](decisions/design-rulings.md) — permanent design decisions only.
- `sources/knowledge/**/README.md` — catalogue-specific modelling and ownership rules.
- `tests/specs/README.md` — executable verification-corpus conventions.
- Package `README.md` files — short local orientation pages.

## Generated and temporary material

`outputs/`, `build/generated/`, web `dist/`, screenshots and temporary campaign files are working data, not source documentation. They are ignored or produced by commands and must not be hand-edited or committed. Recreate them with the relevant generator when needed.

The repository intentionally does not keep GUI screenshot checklists or migration execution logs in the documentation set: those were time-bound delivery artifacts, not maintained product contracts.

## Keeping documentation accurate

- Describe paths as they exist now (`packages/python/` and `apps/`), not the retired `src/` layout.
- Treat executable commands, schemas, fixtures and tests as the source of truth for behavior and status.
- Avoid copying volatile test counts, benchmark results or audit totals into reference pages; use the command that produces the live report instead.
- Keep unresolved product scope in [TODO](../TODO.md), and keep completed historical work out of reference pages.
