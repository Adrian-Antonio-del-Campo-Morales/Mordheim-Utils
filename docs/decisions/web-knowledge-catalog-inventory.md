# Web Warband Manager — inventory of required knowledge catalogues

**Status:** P4.1 deliverable of [`web-migration-parallel-plan.md`](../../web-migration-parallel-plan.md).
**Source of truth:** `sources/knowledge/` (single canonical KB; this document
inventories what the web consumes, it never copies rules).
**Related:** `docs/decisions/web-migration-preparation.md` (scope),
`contracts/campaign-file-v4/README.md` (stable IDs travelling in saves).

## Scope

The web Warband Manager consumes only the catalogues the Campaign Manager
reads today through `mordheim_campaign.application.knowledge_port.KnowledgePort`
(the verified read boundary of the desktop application). Everything the
Campaign Manager never queries is excluded from the web artefact, which
specifically removes the Combat Lab and combat-simulation surface.

## Required catalogues (versioned list)

Read model derived from every public `KnowledgePort` method:

| # | Catalogue | Source | Stable IDs consumed by the web |
| --- | --- | --- | --- |
| 1 | Collections | `registry/collections.yaml` | `collection.id` |
| 2 | Warband packages | `bands/<collection>/*.yaml` | `band_id` (`band.id`), roster `members[].profile_id` |
| 3 | Roster profiles | same band packages | `profile_id` (`profile.id`), `equipment_lists`, `fixed_equipment`, `combat_traits.starting_skills` |
| 4 | Items | `catalog/items/*.yaml` | `item_id` (`item.id`) — 335 rows for `mordheim` |
| 5 | Skills | `catalog/skills/*.yaml` | skill id (`skill.id`), `category` (skill table) |
| 6 | Weapon mechanics | `catalog/mechanics/*.yaml` | `mechanic_id` → `weapons[].hands` |
| 7 | Trading post | `catalog/campaign/trading-post.yaml` | `item_id`, price, restrictions, sections |
| 8 | Scenarios | `catalog/campaign/scenarios.yaml` | `scenario.id`, `player_mode` |
| 9 | Post-battle sequence | `catalog/campaign/post-battle-sequence.yaml` | `campaign.step.*` ids, `resolves` catalogue refs |
| 10 | Serious injuries | `catalog/campaign/serious-injuries.yaml` | injury ids referenced by post-battle engine |
| 11 | Experience & advances | `catalog/campaign/experience-and-advances.yaml` | advance tables, skill references |
| 12 | Exploration & income | `catalog/campaign/exploration-and-income.yaml` | exploration tables |
| 13 | Magic | `catalog/campaign/magic.yaml` | `lore` ids, `lore_assignments[].profile_id`, spell rows |
| 14 | Mutations | `catalog/campaign/mutations.yaml` | mutation rows |
| 15 | Hired swords & dramatis | `catalog/campaign/hired-swords-and-dramatis.yaml` | `campaign.hireling.*` hiring entries |
| 16 | Hireling profiles & rules | `catalog/hirelings/**` | hireling `profile_id` pool, `rule_ids`, `warband_rating` |
| 17 | Hireling traits | `catalog/hirelings/traits.yaml` | `profile_id` → trait set |
| 18 | Warband groups | `registry/warband-groups.yaml` | `warband-group.*` ids |
| 19 | Racial maximums | `catalog/rules/racial-maximums.yaml` | per-characteristic caps |
| 20 | Shared special rules (display) | `catalog/rules/**` | rule ids/names resolved for display by the RULES browser |
| 21 | Scenario rewards | `catalog/campaign/scenario-rewards.yaml` | reward tables keyed by `scenario.id` |
| 22 | Warband rating | `catalog/campaign/warband-rating.yaml` | rating composition rules |
| 23 | Recruitment & veterans | `catalog/campaign/recruitment-and-veterans.yaml` | veteran advance tables |
| 24 | Trading & rarity | `catalog/campaign/trading-and-rarity.yaml` | rarity availability tables |

Item kinds included: `armour`, `close-combat-weapon`, `combat-equipment`,
`material-or-upgrade`, `ranged-weapon`, `shield-or-defence`,
`trollheim-equipment` (required by Trollheim bands).

## Explicitly excluded (Combat Lab / simulation surface)

These stay out of the web artefact; the generator must not emit them:

- `catalog/rules/rule-runtime.yaml` mechanics used only by the combat engine
  (execution contract, runtime scope, simulation mappings —
  `load_simulation_mappings`, `load_execution_contract`, `load_runtime_scope`
  are desktop/simulation-only);
- item kind `out-of-scope` (57 rows: steeds, chaos spawns, … explicitly marked
  out of campaign scope in `catalog/items/out-of-scope.yaml`);
- everything under `mordheim_combat_lab/` and any combat-simulation-derived
  index (benchmarks, analysis pairs);
- PDF export assets and desktop-only display catalogues
  (`persistence/warband_pdf.py` dependencies).

## Web artefact JSON shape (agreed output of P4.2)

Deterministic JSON, no timestamps, ordered by ID:

```json
{
  "schema_version": 1,
  "ruleset": "mordheim",
  "collections": [{"id": "mordheim", "name": {"en": "Mordheim", "es": "Mordheim"}}],
  "bands": [{"collection": "mordheim", "band_id": "sisters-of-sigmar", "roster": {"...": "..."}}],
  "profiles": [{"collection": "mordheim", "band_id": "...", "profile_id": "...", "...": "..."}],
  "items": [{"item_id": "...", "kind": "...", "names": {"en": "...", "es": "..."}}],
  "skills": [{"skill_id": "...", "category": "...", "names": {"...": "..."}}],
  "weapon_hands": {"mechanic_id": 2},
  "campaign": {
    "trading_post": [...],
    "scenarios": [...],
    "post_battle_sequence": [...],
    "serious_injuries": [...],
    "experience": [...],
    "exploration": [...],
    "magic": {"lores": [...], "lore_assignments": [...]},
    "mutations": [...],
    "hirelings": {"profiles": [...], "rules": [...], "traits": {...}},
    "warband_groups": [...],
    "racial_maximums": [...],
    "shared_rules_display": [...],
    "scenario_rewards": [...],
    "warband_rating": [...],
    "recruitment": [...],
    "trading_rarity": [...]
  },
  "indexes": {
    "bands_by_collection": {"mordheim": ["sisters-of-sigmar", "..."]},
    "profiles_by_band": {"mordheim/sisters-of-sigmar": ["..."]},
    "items_by_id": {"dagger": {"index": 12}}
  }
}
```

Policy points agreed with the contract README:

- **Display names travel per locale** (`names: {en, es}`) instead of being
  resolved through `mordheim_knowledge.i18n` at read time — this resolves
  coupling #2 of the preparation doc. The web resolves the locale client-side.
- **Stable IDs are byte-identical to the KB** (`band_id`, `profile_id`,
  `item_id`, `rule_id`, scenario/lore ids). No name-based inference anywhere.
- **Payload maps stay verbatim** for anything the port carries opaquely, same
  preserve-in-place policy as the v4 contract.

## Verification duty (implemented in this task)

`tests/web/test_kb_artefact_inventory.py` keeps this inventory honest:

1. every `KnowledgePort`-consumed catalogue appears in the inventory table
   source list (catalogue inventory coverage);
2. every band referenced by the v4 fixtures resolves against the artefact
   source list (fixture ↔ KB coherence);
3. excluded Combat Lab surfaces are absent from the generator inputs.

The test reads the YAML sources directly — it does not depend on P4.2's
generator existing yet, so P4.2 can be built against this contract in parallel.
