# Use and extend campaign knowledge

The campaign knowledge base contains immutable game rules: tables, market
costs, availability, procedures, restrictions and formulas. A campaign's
experience, crowns, wyrdstone, stash, injuries, rolls, purchases and history
belong to the campaign model and persistence, referenced through stable KB
IDs.

## Ownership and read path

```text
KB YAML → knowledge loaders → application service → UI
```

The UI never reads YAML or decides rules. Application services load and
validate knowledge, apply it to campaign state and return options or results
for presentation. Campaign files store state and stable references, not copies
of catalogue records.

| Need | Canonical source |
|---|---|
| Profile, recruit cost, experience, equipment and rules | `bands/<collection>/<band>/profiles.yaml` |
| Warband composition and limits | `bands/<collection>/<band>/band.yaml` |
| Profile equipment access and creation prices | `bands/<collection>/<band>/equipment-access.yaml` |
| Item identity and rule | `catalog/items/*.yaml` |
| Market price, rarity and availability | `catalog/campaign/trading-post.yaml` |
| Post-battle order | `catalog/campaign/post-battle-sequence.yaml` |
| Injuries, advances, exploration, trading and rating | Other files in `catalog/campaign/` |
| Racial maximums | `catalog/rules/racial-maximums.yaml` |
| Warband/profile exceptions | The band's `special-rules.yaml` |

Use `mordheim_knowledge.campaign` loaders or the relevant application
`KnowledgePort`; do not reconstruct paths in a UI. Mutable operations follow
preview → validated transaction → persisted state.

## Identity and modelling

Campaign IDs use `campaign.<family>.<detail>` with kebab-case segments. They
describe the semantic result, not only a roll number. Existing entities keep
their own IDs: a trading entry references `item_id: sword` rather than
creating another item.

Effects are typed operations, not display prose or stored campaign results.
For example:

```yaml
- type: warrior.add_condition
  condition_id: campaign.condition.frenzy
  duration: permanent
- type: equipment.disposition
  scope: carried_by_subject
  disposition: lost
- type: warrior.miss_games
  games: { kind: dice, dice: { count: 1, sides: 3 } }
- type: reward.grant
  recipient: warband
  resources:
    gold_crowns: { kind: fixed, value: 50 }
```

Create referenced conditions, items and profiles canonically before using
them. Sub-tables use `resolution.type: roll_table`, explicit dice, inclusive
`when.min`/`when.max` branches and stable branch IDs. Exploration procedures
compose `sequence`, `roll_table`, `characteristic_test`, `choose_one`,
`conditional` and `grant`; `bind` creates a local procedure variable. Rolls,
choices and rewards produced by these procedures are campaign state.

Advancement tables describe 2D6 outcomes, not XP thresholds. Results use
`characteristic_increase`, `choose_one`, `roll_table`, `choose_skill`,
`generate_spell` or `promote_henchman`. The thresholds themselves live beside
the tables in `experience-and-advances.yaml`.

## Trading and prices

The Trading Post is the source of post-battle price and availability.
`equipment-access.yaml` answers whether a profile may select an item and its
creation price. Use `price_override` only when the warband source explicitly
states a market-price exception; pairs, discounts and variable costs use
structured `purchase_options`.

Review differences with:

```powershell
python tools/knowledge/maintenance/price-collation.py
```

The generated report under `outputs/knowledge/` is the live review queue.
Reviewed non-exceptions belong in
`tools/knowledge/maintenance/price-collation-resolutions.csv`; do not copy
counts or queue contents into documentation.

## Adding campaign knowledge

1. Add or update the canonical YAML and its source references. Leave
   unconfirmed rules as `status: draft`; do not invent values.
2. Extend the matching schema in `contracts/knowledge-editorial-v1/` when the
   document shape changes.
3. Add loader validation and reference resolution for new identities.
4. Expose the data through an application port or use case, not directly to a
   UI.
5. Persist stable IDs and applied structured results.
6. Run the KB formatting and structural validation loop from
   [Modify the knowledge base](modify-knowledge-base.md).

Scenario entries model progression rewards only; deployment, terrain, victory
conditions and other on-table mechanics remain outside campaign catalogue
scope unless that product boundary is explicitly changed.
