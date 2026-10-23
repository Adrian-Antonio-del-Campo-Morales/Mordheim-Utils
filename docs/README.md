# Documentation

Reference material and procedures for the Mordheim Utils repository. Start
with the [repository overview](../README.md) for installation and the common
commands.

Current follow-ups are in [the backlog](../TODO.md); the
[modular verification sequence](reference/verification.md#modular-integration-closure)
distinguishes implementation closure from certification.

## Reference — how the system is built

- [Architecture](reference/architecture.md) — source layout, dependency
  boundaries and data flow.
- [Shared warrior eligibility](reference/eligibility.md) — the single equipment
  and skill rule module already used by both products, its Python/browser
  adapters, bundle maintenance and boundary with combat compilation.
- [Knowledge base](reference/knowledge-base.md) — canonical data, IDs,
  classification, translation and formatting policy.
- [Verification](reference/verification.md) — the certification layers,
  coverage and mutation gates, and what each one can prove.
- [Test classification and execution order](reference/test-sequence.md) — the
  phase categories, assignment criteria and dependency-based repair order.
- [Tools and launcher](reference/tools.md) — `mordheim-utils.py` scope selection,
  focused/parallel execution and maintained scripts.
- [Frozen engine inputs](reference/verification.md#engine-test-fixtures) — loaders,
  regeneration and the boundary with source-backed rules/E2E checks.
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
- [Implement the warband reference template](guides/warband-reference-template.md)
  — the Rules → Warbands sheet: read model, fixed section order and the
  generator metadata it reads.
- [Use and extend campaign knowledge](guides/campaign-knowledge.md)
- [Develop and release](guides/develop-and-release.md) — the fast loop, the
  release gates, measured performance optima and per-machine calibration.

## Decisions

- [Design rulings](decisions/design-rulings.md) — permanent design decisions
  that bind the KB, the engines or the applications.

## Knowledge base — modelling documents

The catalogue and registry rules of the canonical data:

- [Campaign knowledge](guides/campaign-knowledge.md)
- [Hirelings](reference/knowledge-base.md#hirelings-and-campaign)
- [Translation glossary](reference/translation-glossary.md)

## Where documents live

Most maintained documentation lives under `docs/`. Project-level entry
points and documents owned by a specific artefact live beside them:

- [`README.md`](../README.md) at the repository root — the entry point, and the
  file the Windows installer packages.
- [`TODO.md`](../TODO.md) at the repository root — unresolved project defects,
  verification work and deferred capabilities.
- [`AGENTS.md`](../AGENTS.md) — repository instructions, which agents read from
  the checkout root.
- `contracts/*/README.md` — `tests/rules/knowledge/test_editorial_schemas.py`
  requires each contract README next to its schemas.
- [`tests/rules/integration/specs/README.md`](../tests/rules/integration/specs/README.md) — the conventions of the
  verification corpus, published beside the corpus itself.
- `tests/rules/integration/e2e/README.md` and
  `tests/rules/integration/e2e/cases/grants/INVENTORY.md` — the E2E battery's own
  contract, procedure notes and grant inventory, owned with the corpus they
  describe.

Only the contract READMEs are checked by a test; the installer consumes the root
README, and the rest are placed by the subtree that owns them.

## Conventions

- Describe paths as they exist now (`packages/python/` and `apps/`).
- Executable commands, schemas, fixtures and tests are the source of truth for
  behaviour and status; reference pages do not copy volatile test counts,
  benchmark results or audit totals — they name the command that produces the
  live report.
- Unresolved product scope belongs in [TODO](../TODO.md).
- Generated material (`outputs/`, web `dist/`, staged
  knowledge JSON) is working data produced by commands: never hand-edit or
  commit it. The generated eligibility bundle is an exception: it is a
  versioned Python runtime resource; regenerate it from its TypeScript source
  and commit both together.
