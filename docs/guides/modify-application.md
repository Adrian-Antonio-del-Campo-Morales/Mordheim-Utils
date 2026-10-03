# Modify an application

Applies to Combat Lab (`mordheim_combat_lab`) and the web Campaign Manager.
Prerequisites:
[Architecture](../reference/architecture.md) (package responsibilities, layer
rules) and, for campaign work, [the Campaign Manager
section](../reference/architecture.md#campaign-manager).

## Procedure

1. Model the use case in the application's `application/` layer, without UI dependencies.
2. Reuse the [shared eligibility module](../reference/eligibility.md) for equipment
   and skill decisions. Warband Manager imports its TypeScript exports;
   Combat Lab uses `mordheim_construction/eligibility.py`. Keep duel compilation
   in `mordheim_construction` and analysis in `mordheim_combat.vectorized`.
3. Return explicit types and accept cancellation/progress for long jobs.
4. Keep Tkinter threads/`after` in Combat Lab `ui/`, and React presentation in
   the web shell. Selectors display the shared decisions; they do not copy rules.
5. Keep persisted formats compatible with their documented contract; add a
   fixture when a `.mordheim` or Combat Lab workbook change is intentional.

Done when the application-layer tests, relevant visible UI workflows and
persisted round-trips pass. Rebuild and check the eligibility bundle when its
source changes; test both consumers.

The module is already implemented; do not schedule its construction anew for
another application. Revalidate older findings at the
[current owning layer](../reference/eligibility.md#construction-boundary-for-phased-implementation).
Legal choices, supported combat effects and UI availability are separate facts.
If a shared decision changes, test the affected paths in both products without
reopening every previously accepted campaign flow.

## Campaign-specific rules

- The web UI reads generated knowledge through `KnowledgeReader`, not YAML:
  `KB YAML → generate_knowledge_web.py → artefact → KnowledgeReader → domain/application → React`.
  Combat Lab loads YAML through `mordheim_knowledge` behind its application
  catalogue. Neither UI decides eligibility or copies campaign tables into
  widgets, UI constants or persistence. Full data-ownership table and query
  patterns: [use campaign knowledge](campaign-knowledge.md).
- Campaign state (experience, crowns, wyrdstone, stash, injuries, rolls,
  purchases) lives in `persistence`/the campaign model, referenced through
  stable KB ids (`band_id`, `profile_id`, `item_id`, `rule_id`) — never
  serialized rules.
- The UI requests a preview and the use case applies a validated transaction;
  it does not update values directly.
- Post-battle screens present results and trigger application actions;
  resolution and state mutation belong to `packages/typescript/domain/campaign/`
  and `packages/typescript/application/campaign/features/`
  (see the [architecture reference](../reference/architecture.md#campaign-manager)).

Layer checks live in `tests/python/architecture/test_boundaries.py` and
`tests/typescript/architecture/purity.test.ts`: Python UI never imports KB
loaders or YAML, application/persistence never import Tkinter, and TypeScript
domain/application never import UI or browser storage.

For the verification suite (`verification/`), see
[Verify rules](implement-and-verify-rules.md) — it stays out of the UI and
exercises the real engine as the system under test.
