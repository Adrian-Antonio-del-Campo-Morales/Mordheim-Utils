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
the only source of racial characteristic maximums: warband rules and campaign
advancement reference its entries (`campaign.limit.racial-maximum.*`) by ID
and do not embed the statline. The campaign catalogue only defines
procedures, campaign tables and ID links; for example, a hiring entry refers
a `profile_id` and never copies the profile record.

The `cost` values already present in `equipment-access.yaml` are kept as
evidence of the printed lists during the migration. They are not a market
price: when an amount is a real exception it must be declared explicitly as
`price_override`, with its source; otherwise the Trading Post prevails.
Multi-unit purchases — for example, pairs — are modelled in
`purchase_options`, not as another price of the same `item_id`.

## TODO: collate warband-list prices

Before using campaign prices in the runtime, compare every `cost` value of
every `equipment-access.yaml` with the Trading Post. For each difference:

1. confirm whether it is a published exception, a warband-creation rule or a
   source discrepancy;
2. if it is an exception, replace the implicit use of the cost with a
   `price_override` with verifiable `source_refs`;
3. otherwise keep the amount only as historical evidence and apply the price
   of `trading-post.yaml`.

Do not complete this migration by name matching nor assume that two different
prices describe the same purchase type: review by `item_id`, equipment list,
profile and purchase option.

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
| `experience-and-advances.yaml` | 3 XP awards, underdog bonus and 2 advancement tables | published |
| `exploration-and-income.yaml` | Dice allocation, exploration result table, wyrdstone selling and magic artefacts | published |
| `recruitment-and-veterans.yaml` | 3 recruitment policies and veteran availability | published |
| `warband-rating.yaml` | Rating formula with components and exclusions | published |
| `trading-and-rarity.yaml` | Rarity test, modifiers and equipment reassignment | published |
| `scenarios.yaml` | 98 scenarios, 2 selection tables, pre-battle rules and progression rewards (`progression:`) transcribed in all 98 from each scenario's individual page | published |
| `magic.yaml` | Casting rules, 45 lore↔wizard assignments and 31 lores with 188 spells | published |
| `mutations.yaml` | Purchase rules and 9 mutations with typed effects | published |
| `hired-swords-and-dramatis.yaml` | Schema v2: 98 entries (72 Hired Swords + 26 Dramatis Personae) with per-resource fee/upkeep, search procedure and static eligibility + 18 dynamic rules | published |

The racial characteristic maximums live outside this directory, in the shared
catalogue `catalog/rules/racial-maximums.yaml` (29 entries
`campaign.limit.racial-maximum.*` with `source_refs`). The warband rules in
`bands/*/special-rules.yaml` that describe advancement reference them by ID in
the text (`effect`/`effect_i18n.en`) instead of embedding the numeric
statline, so there are no two copies that could drift apart.

The KB declares rules and tables, never their result: the accumulated
experience, crowns, wyrdstone, stash, rolls made and purchases of a concrete
warband belong to the campaign state/persistence of the applications.

Each scenario has its own page on mordheimer.net
(`/docs/campaigns/scenarios/<family>/<slug>`) publishing the `experience`,
`wyrdstone`, treasure and income sections. The KB ingests only what affects
the warband's progression in those scenarios: experience awards (referencing
the canonical `campaign.experience.award.*` entries when they match),
wyrdstone obtained, treasure/items and income in crowns, under the
`progression:` key of each entry (see the HOWTO). On-table game mechanics
(terrain, deployment, victory conditions, monsters, table special rules) are
not modelled by scope decision. Full coverage: all 98 catalogue scenarios
(rulebook, Town Cryer, Fanatic Magazine, Fanatic Online, Archive Pestilen and
Rynn Tyrr) have `progression:` transcribed from their individual page. Some
Archive Pestilen sources do not declare progression rewards (zombie invasions
like Romero's Pride, The Restless Dead or The Battle At Koleshire Keep): in
those cases the absence is documented in `progression.notes`. Point doubts
about a source are documented in the `progression.notes` of the entry.
No YAML of this catalogue must be loaded as rule implementation: the loaders
(`load_campaign_catalog`, `load_post_battle_sequence`) and their validation
are runtime-integration work.
