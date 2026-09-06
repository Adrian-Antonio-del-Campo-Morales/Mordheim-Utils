# Modify an application

Applies to Combat Lab (`mordheim_combat_lab`) and the Campaign Manager
(`mordheim_campaign`). Prerequisites: [Architecture](../reference/architecture.md)
(package responsibilities, layer rules) and, for campaign work,
[the Campaign Manager reference](../reference/campaign-manager.md).

## Procedure

1. Model the use case in `application/` without Tkinter.
2. Reuse `mordheim_construction` for legality and `combat.vectorized` for
   analysis.
3. Return explicit types and accept cancellation/progress for long jobs.
4. Keep the thread, `after` and presentation in `ui/`.
5. Version persisted changes without breaking the reading of existing
   workbooks / `.mordheim` files.

Done when it is tested without a window and the persisted round-trips still
pass.

## Campaign-specific rules

- The GUI never reads YAML and never decides rules:
  `KB YAML → mordheim_knowledge.loader → application → ui`. Do not load files
  from `sources/knowledge/` from Tkinter, nor copy campaign tables into
  widgets, UI constants or persistence. Full data-ownership table and query
  patterns: [`catalog/campaign/README-HOWTO.md`](../../sources/knowledge/catalog/campaign/README-HOWTO.md).
- Campaign state (experience, crowns, wyrdstone, stash, injuries, rolls,
  purchases) lives in `persistence`/the campaign model, referenced through
  stable KB ids (`band_id`, `profile_id`, `item_id`, `rule_id`) — never
  serialized rules.
- The UI requests a preview and the use case applies a validated transaction;
  it does not update values directly.
- Post-battle screens present results and trigger engine actions; resolution,
  catalogue and state mutation belong to `post_battle_resolution.py`,
  `post_battle_catalogue.py` and `post_battle_engine.py`
  (see the [Campaign Manager reference](../reference/campaign-manager.md)).

Layer rule (executable in `tests/architecture/test_boundaries.py`): `ui`
never imports the KB loaders or YAML; `application` and `persistence` never
import Tkinter.

For the verification suite (`verification/`), see
[Verify rules](implement-and-verify-rules.md) — it stays out of the UI and
exercises the real engine as the system under test.
