# Campaign catalogue

These templates describe persistent rules of a warband and do not take part in
the duel engine. Each file is an independent editorial source:

- it keeps stable IDs and source references;
- it separates the common Mordheim rule from each warband's exceptions;
- it uses `effect_id` so warband rules can explicitly declare which campaign
  rule they modify;
- it references existing canonical data, without duplicating profiles,
  composition, prices, rarities, equipment or special rules;
- it leaves unconfirmed rules as `status: draft`, instead of inventing data.

The exceptions are kept in `bands/<collection>/<band>/special-rules.yaml`.
When the campaign runtime is implemented, the `effect_id` identifiers will be
the linking points for its handlers and for warband persistence.

The order of `post-battle-sequence.yaml` is normative; the other documents
describe the data that each step resolves.

Companion documents in this directory:

- [`README-HOWTO.md`](README-HOWTO.md) — how to query and extend the
  catalogue from application code (responsibility boundary, data-ownership
  table, loader contract, scenario-reward schema).
- [`MODELING-CONVENTIONS.md`](MODELING-CONVENTIONS.md) — YAML shapes for
  typed effects, advancement results, rarity tests and exploration
  procedures.

## ID convention

The real entries of this catalogue use namespaced IDs with kebab-case
segments: `campaign.<family>.<detail>`. Keep the semantic outcome and, when
appropriate, the table context; the roll number is never the only identifier.
Examples: `campaign.serious-injury.hero.22-leg-wound`,
`campaign.exploration.double-2.shop` and `campaign.trading-post.sword`.

Existing IDs from other areas are not renamed: items use their canonical
snake_case `item_id` — for example `sword` — and are referenced from a
campaign entry through that field. `examples` blocks remain reserved for
`example.*` IDs.

## Data ownership

`bands/*/profiles.yaml` holds the characteristics, cost, starting experience,
equipment and rules of each profile. `bands/*/band.yaml` holds the
composition and limits of the warband. `catalog/items/` holds the record of
each item. `trading-post.yaml` is the canonical source of market price,
rarity and post-battle availability. `catalog/rules/racial-maximums.yaml` is
the only source of racial characteristic maximums (29 entries
`campaign.limit.racial-maximum.*`): warband rules and campaign advancement
reference its entries by ID and do not embed the statline, so there are no
two copies that could drift apart. The campaign catalogue only defines
procedures, campaign tables and ID links; for example, a hiring entry refers
a `profile_id` and never copies the profile record.

## Price and equipment rules

1. Consult first the price and availability in `trading-post.yaml`.
2. Use `equipment-access.yaml` only to know whether that profile may select
   the item.
3. Apply `price_override` only if it exists, is referenced and its source
   confirms an exception.
4. Represent pairs, discounts and variable costs with `purchase_options` and
   the structured Trading Post price; not with new `item_id` values or
   implicit alternative prices.

### Collation of warband-list prices (first run)

The collation tool `tools/kb/price-collation.py` compares every `cost` value
of every `equipment-access.yaml` with the Trading Post (2,152 rows across 81
warbands) and regenerates the report into `outputs/knowledge/` (git-ignored;
run `python tools/kb/price-collation.py`). A warband list is the creation/recruitment price list of its source;
the Trading Post is the market price for post-battle purchases. A difference
is therefore not itself an exception: an amount is recorded as a
`price_override` only when the warband's own source confirms that the warband
pays that amount as a market price too.

First-run result: 18 rows carry a `price_override`, all source-confirmed; 14
differing rows are page-verified as plain creation prices (the committed
sidecar `tools/kb/price-collation-resolutions.csv`), and 119 rows remain in
the review queue:

- `gunnery-school-of-nuln` — the black-powder weapons of both lists
  (Impeccable Care: "always use the reduced … costs listed in its starting
  Equipment Lists"); the `superior_blackpowder` accessory is not a weapon
  and keeps the Trading Post price;
- `hochland-bandits` — the Duelist list pistol (Powder's Expensive!: bandit
  heroes "always pay the higher black-powder weapon costs shown in its
  equipment lists");
- `lizardmen` — light armour (Armour rule: "always costs 50 gc for
  Lizardmen, including when bought from the Equipment chart").

Each `price_override` equals the list `cost` it encodes (the exception amount
is the printed list amount); the warband page in `source` is its
verification. Rows that were checked against their page and shown to be
creation prices are recorded in the resolutions sidecar (outcome
`creation-price`) and leave the queue. The remaining rows keep their `cost`
only as historical evidence and stay listed in the review queue until each
printed source is verified (the Trollheim/Lustria/Khemri rows have no
recorded source URL in the files yet). Review by `item_id`, equipment list,
profile and purchase option — never by name matching.

To record a newly confirmed exception: add `price_override: <gc>` to the
`equipment-access.yaml` row (same value as its `cost`), then regenerate the
report.

## Catalogue state

The catalogues of this directory contain real data with verifiable
`source_refs` (source: The New Mordheimer, mordheimer.net) and `status:
published`. No `examples` blocks remain: they were replaced by the real
ingestion in the main block of each file.

| File | Content | State |
|---|---|---|
| `post-battle-sequence.yaml` | The 10 post-battle steps in normative order | published |
| `trading-post.yaml` | 338 entries: base price/variable cost, availability (77 common, 183 rare, 78 not sold) and restrictions | published |
| `serious-injuries.yaml` | D66 hero (20 results) and D6 mercenary (2) tables with typed effects | published |
| `experience-and-advances.yaml` | 3 XP awards, underdog bonus, 2 advancement tables and the `advance_thresholds` ladder | published |
| `exploration-and-income.yaml` | Dice allocation, exploration result table, wyrdstone selling and magic artefacts | published |
| `recruitment-and-veterans.yaml` | 3 recruitment policies and veteran availability | published |
| `warband-rating.yaml` | Rating formula with components and exclusions | published |
| `trading-and-rarity.yaml` | Rarity test, modifiers and equipment reassignment | published |
| `scenarios.yaml` | 98 scenarios, 2 selection tables, pre-battle rules and progression rewards (`progression:`) transcribed in all 98 from each scenario's individual page | published |
| `magic.yaml` | Casting rules, 45 lore↔wizard assignments and 31 lores with 188 spells | published |
| `mutations.yaml` | Purchase rules and 9 mutations with typed effects | published |
| `hired-swords-and-dramatis.yaml` | Schema v2: 98 entries (72 Hired Swords + 26 Dramatis Personae) with per-resource fee/upkeep, search procedure and static eligibility + 18 dynamic rules | published |

The KB declares rules and tables, never their result: the accumulated
experience, crowns, wyrdstone, stash, rolls made and purchases of a concrete
warband belong to the campaign state/persistence of the applications.

Each scenario has its own page on mordheimer.net
(`/docs/campaigns/scenarios/<family>/<slug>`) publishing the `experience`,
`wyrdstone`, treasure and income sections. The KB ingests only what affects
the warband's progression in those scenarios: experience awards (referencing
the canonical `campaign.experience.award.*` entries when they match),
wyrdstone obtained, treasure/items and income in crowns, under the
`progression:` key of each entry (schema in the HOWTO). On-table game
mechanics (terrain, deployment, victory conditions, monsters, table special
rules) are not modelled by scope decision. Some Archive Pestilen sources do
not declare progression rewards (zombie invasions like Romero's Pride, The
Restless Dead or The Battle At Koleshire Keep): in those cases the absence is
documented in `progression.notes`. Point doubts about a source are documented
in the `progression.notes` of the entry.

## Runtime read path

No YAML of this catalogue is loaded as duel-rule implementation: the runtime
read path lives in `mordheim_knowledge/campaign.py` — `load_campaign_catalog`,
`load_post_battle_sequence`, `load_hirelings` and `load_warband_groups` —
whose load-time validation (schema_version, per-document id uniqueness and
reference resolution) is covered by `tests/knowledge/test_campaign_loaders.py`.
The Campaign Manager consumes them through its `KnowledgePort`
(`mordheim_campaign/application/knowledge_port.py`) without the GUI touching
YAML; its post-battle screens and engines are the current consumers (see
[the Campaign Manager reference](../../../../docs/reference/campaign-manager.md)).
The remaining runtime work is application-side (rule resolution, price
collation review), not KB data.
