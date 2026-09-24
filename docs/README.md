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
- [Tools](reference/tools.md) — maintained scripts, their purpose and the
  directory that owns each one.
- [Components](reference/components.md) — applications, packages and ownership
  boundaries.
- [Web presentation](reference/web-presentation.md) — localization, provenance
  and output-boundary rules.

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
- [Use the campaign knowledge base](guides/use-campaign-knowledge.md)
- [Develop and release](guides/develop-and-release.md) — the fast loop, the
  release gates, measured performance optima and per-machine calibration.

## Decisions

- [Design rulings](decisions/design-rulings.md) — permanent design decisions
  that bind the KB, the engines or the applications.

## Knowledge base — modelling documents

The catalogue and registry rules of the canonical data:

- [Campaign catalogue](knowledge/campaign-catalogue.md)
- [Campaign modelling](knowledge/campaign-modeling.md)
- [Hirelings](knowledge/hirelings.md)
- [Translation glossary](knowledge/translation-glossary.md)
- [Registry](knowledge/registry.md)

## Where documents live

Every document lives under `docs/`; the exceptions, each for a reason the tool
that owns it enforces:

- [`README.md`](../README.md) at the repository root — the entry point, and the
  file the Windows installer packages.
- `contracts/*/README.md` — `tests/python/knowledge/test_editorial_schemas.py`
  requires each contract README next to its schemas.
- `sources/2A/*.md`, `sources/2B/*.md` — the active staging trees; their tools
  read and write those verdict documents in place.
- [`tests/specs/README.md`](../tests/specs/README.md) — the conventions of the
  verification corpus, published beside the corpus itself.

## Conventions

- Describe paths as they exist now (`packages/python/` and `apps/`).
- Executable commands, schemas, fixtures and tests are the source of truth for
  behaviour and status; reference pages do not copy volatile test counts,
  benchmark results or audit totals — they name the command that produces the
  live report.
- Unresolved product scope belongs in [TODO](TODO.md).
- Generated material (`outputs/`, web `dist/`, staged
  knowledge JSON) is working data produced by commands: never hand-edit or
  commit it.
