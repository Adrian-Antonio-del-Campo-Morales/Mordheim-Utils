# HOWTO: using the campaign KB

This guide explains how to consult and extend the post-battle rules without
creating a second source of truth. It is aimed at developers implementing
screens, use cases or campaign ingestions.

## Responsibility boundary

The KB contains exclusively immutable game rules: tables, market costs,
availability, procedures, restrictions and formulas. It never contains a
concrete campaign nor the result of applying a rule to one.

Outside the KB live, among other things, the current experience of each
warrior, a warband's crowns and wyrdstone, its stash, received injuries, rolls
made, purchases, recruitments and the post-battle history. That state belongs
to the campaign model/persistence and is identified through stable KB IDs
(`band_id`, `profile_id`, `item_id`, `rule_id`).

## Basic principle

The GUI never reads YAML and never decides rules. The correct path is:

```text
KB YAML → knowledge.loader → application → ui
```

The `knowledge` area loads and validates documents; `application` turns them
into options and results for a use case; `ui` only presents those results
and forwards the user's actions to `application`.

Do not load files from `sources/knowledge/` from Tkinter, nor copy campaign
tables into widgets, UI constants or persistence.

## Where each piece of data lives

| Need | Canonical source | Query by |
|---|---|---|
| Profile, recruit cost, starting experience, equipment and own rules | `bands/<collection>/<band>/profiles.yaml` | `profile_id` |
| Limits and composition of a warband | `bands/<collection>/<band>/band.yaml` | `band_id` |
| A profile's access to an equipment list | `bands/<collection>/<band>/equipment-access.yaml` | `equipment_list_id` + `item_id` |
| Identity and rule of an item | `catalog/items/*.yaml` | `item_id` |
| Market price, rarity and availability | `campaign/trading-post.yaml` | `item_id` |
| Post-battle order | `campaign/post-battle-sequence.yaml` | `campaign.step.*` |
| Injuries, experience, exploration, trading and rating | The sibling files of this directory | `campaign.*` |
| Racial characteristic maximums (advancement) | `catalog/rules/racial-maximums.yaml` | `campaign.limit.racial-maximum.*` |
| Exception of a warband or of a profile | `bands/<collection>/<band>/special-rules.yaml` | `rule_id` / `effect_id` |

A campaign entry may reference `item_id`, `profile_id`, `band_id` or
`rule_id`, but it does not redeclare the record it points to.

Campaign-owned IDs follow `campaign.<family>.<detail>`, with kebab-case
segments. For example, `campaign.serious-injury.hero.22-leg-wound` and
`campaign.trading-post.sword`. The object of the second entry is still
`item_id: sword`; no second item ID is created. For purchase options, use an
explicit child ID such as `campaign.trading-post.pistol.brace`.

Derived rolls are structured, not expressed as text. A sub-table declares
`resolution.type: roll_table`, the dice and the branches with `when.min`/
`when.max`; each branch has its own ID and effects. For values like D3 use
`games: { kind: dice, dice: { count: 1, sides: 3 } }`; for a fixed value,
`games: { kind: fixed, value: 1 }`. Obtained results stay outside the KB, in
the campaign state.

For an exploration reward that is an item, use `rewards.item_ids`. Existing
examples: `lucky_charm` in `catalog/items/combat-equipment.yaml`, `axe`,
`dagger` and `sword` in `catalog/items/weapons-close-combat.yaml`, and
`light_armour` in `catalog/items/armour.yaml`. If the item does not exist in
the catalogue — as happened with Mordheim Map before adding its canonical
record in `catalog/items/out-of-scope.yaml` — stop that result's ingestion and
first add the canonical record of the item with its source.

## How to query the existing KB from code

For warband and profile information use the existing loaders. Never rebuild
paths by hand from the GUI:

```python
from mordheim_knowledge.loader import load_bands

packages = load_bands("mordheim")
package = next(row for row in packages if row.band["id"] == "pit-fighters")
profile = next(row for row in package.profiles if row["id"] == "pit-king")
```

For a selector or screen that already belongs to the combat simulator, use
`application.catalogue.CombatCatalogue`. For example, `bands`, `profiles`,
`profile`, `weapons` and `cost` already offer data prepared for the UI. This
class is combat-only: it must not be extended with post-battle state.

## Pattern for a campaign feature

When implementing campaign, create a use case in `application` — for example
`CampaignCatalogue` or `PostBattleService` — that receives IDs and campaign
state, loads the rules through `knowledge.loader` and returns simple DTOs for
the UI.

```text
UI: "resolve exploration"
  → application: resolve_exploration(campaign_state, band_id)
    → knowledge: exploration tables + applicable special rules
    → application: ExplorationResult
  → UI: shows dice, result and proposed changes
```

Mutable state — gold, wyrdstone, injuries, accumulated experience, stash and
assigned equipment — belongs entirely to `persistence`/the campaign model,
never to the YAML. The KB only defines how to transform it. The UI requests a
preview and the use case applies a validated transaction; it does not update
values directly.

## Minimum reading contract to implement

Before connecting a campaign screen, add loaders to `knowledge.loader` with
this responsibility:

```text
load_campaign_catalog("serious-injuries", ruleset)
load_campaign_catalog("trading-post", ruleset)
load_post_battle_sequence(ruleset)
```

Each loader must check `schema_version`, `ruleset`, unique IDs and that the
references (`item_id`, `profile_id`, `rule_id`) exist. The use case must never
interpret raw YAML nor silently tolerate missing references.

## Price and equipment rules

1. Consult first the price and availability in `trading-post.yaml`.
2. Use `equipment-access.yaml` only to know whether that profile may select
   the item.
3. Apply `price_override` only if it exists, is referenced and its source
   confirms an exception.
4. Represent pairs, discounts and variable costs with `purchase_options` and
   the structured Trading Post price; not with new `item_id` values or implicit
   alternative prices.

The historical `cost` values of the equipment lists were collated against
the Trading Post (first run; see [README.md](README.md) and
`docs/knowledge/price-collation.md`): `price_override` is recorded on the
`equipment-access.yaml` row as a flat gc amount equal to the printed list
cost, only for exceptions confirmed by the warband source (Nuln black-powder
weapons, Hochland Duelist pistol, Lizardmen light armour). Regenerate the
report with `python tools/kb/price-collation.py`.

## How to add knowledge

1. First locate the owner of the data in the table above.
2. Add the rule or table to the canonical file and keep a stable ID.
3. Add verifiable `source_refs`; do not turn examples into real data.
4. For an exception, create or extend the warband's special rule and link the
   relevant campaign `effect_id`.
5. Add reference validation and a semantic case before making the data
   executable. The validation of the current campaign ingestion (headers,
   absence of fictional examples, canonical counts and reference resolution
   against items, warbands, groups, conditions, skills and profiles) lives in
   `tests/knowledge/test_campaign_catalogs.py`.
6. Run `python -m mordheim_combat_lab validate`.

## Adding or reviewing scenario rewards

Every scenario with transcribed progression data carries the `progression:`
key with these sub-keys (all optional except `experience` when the key
exists; if the source does not declare progression rewards — e.g. certain
zombie invasions of the Archive Pestilen — the absence must be documented in
`notes`):

- `experience`: list of awards. Each row has **either** `ref` (a canonical
  `campaign.experience.award.*` id from `experience-and-advances.yaml` when
  the line matches the standard award) **or** `summary` (text faithful to the
  source for scenario-specific awards), never both. When the amount is numeric
  it is declared as `amount`; when the source gives it in dice,
  `amount_dice` (e.g. `D6`). Never both.
- `wyrdstone`: text with the wyrdstone the warband gets at the end (e.g. per
  shard in possession, with a cap if the source declares one).
- `income`: text with income in crowns or fixed payments.
- `loot`: treasure/items. `summary` describes when it is obtained;
  `contents` (optional) lists rows with `reward`, `roll` (e.g. `4D6`),
  `when.min`/`when.max` (optional, if the roll discriminates) and `item_id`
  (optional, canonical item-catalogue id when the reward is a concrete Trading
  Post item).
- `exploration`: (optional) text with bonuses on the later exploration phase
  (extra dice or rerolls).
- `notes`: doubts or clarifications of the source for later steps (suspected
  errata, amount/label discrepancies, assumed conventions not declared on the
  page, non-explicit counter conversions).

The `source_refs` URL of a transcribed scenario points to the individual page
(`…/scenarios/<family>/<slug>`), not to the index.

The shape and reference tests live in
`tests/knowledge/test_campaign_catalogs.py` (Scenarios section).

## Current state

The catalogues of this directory are ingested from The New Mordheimer
(mordheimer.net) as declarative data with `source_refs` and `status:
published`: trading post (338 entries with price, rarity and restrictions),
injury tables, experience, exploration, recruitment, rating, scenarios (98,
all 98 with `progression:` transcribed from their individual page: rulebook,
Town Cryer, Fanatic Magazine, Fanatic Online, Archive Pestilen and Rynn Tyrr),
magic (31 lores with 188 spells, with the 15 `spell_list` references of the
mercenary profiles linked by `lore_id` in `lore_assignments`) and mutations.
They are rules and tables, not implementation: no YAML encodes how to apply a
rule nor saves the state of a concrete campaign.

The runtime loaders are implemented in `mordheim_knowledge/campaign.py`:
`load_campaign_catalog`, `load_post_battle_sequence`, `load_hirelings` and
`load_warband_groups` validate `schema_version`, `ruleset`, per-document ID
uniqueness and that the references (`item_id`, `profile_id`, `band_id`,
`condition_id`, `skill_id`, `lore`, `warband-group.*`) exist. The Campaign
Manager consumes them through its `KnowledgePort`
(`mordheim_campaign/application/knowledge_port.py`) — which also exposes the
warband-market price rule (`price_override`) for the Trading Post offers of
its post-battle screens (`PostBattleCatalogue` in
`mordheim_campaign/application/post_battle_catalogue.py`), without the GUI
touching YAML. The mercenary catalogue (`hired-swords-and-dramatis.yaml`, 98
entries, see `../hirelings/README.md`) is integrated with schema v2
and published; the 18 dynamic eligibility rules (dependent on roster,
mercenary variant or conditional roll) are declared in `catalog/hirelings/**`
and are evaluated by the application, like the 4 out-of-scope Dramatis and
the 59 pending intrinsic references of the profile catalogues (they do not
block cost or eligibility).

The Campaign Manager consumes the KB for warbands, profiles and campaign
content: its `KnowledgePort` (`mordheim_campaign/application/knowledge_port.py`) uses
`load_bands`, `load_items`, `load_skills` and the campaign loaders to feed
warband creation and the post-battle screens without the GUI touching YAML,
and its persistence (`.mordheim`) references the
canonical IDs (`band_id`, `profile_id`, `item_id`) without duplicating rules.
