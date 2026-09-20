# Knowledge base editorial documents — format v1

**Status:** current contract for the maintained YAML of the knowledge base.
**Schemas:** one per document, JSON Schema draft 2020-12, plus the shared
[`defs.schema.json`](./defs.schema.json).

## Purpose

Every maintained YAML document of `sources/knowledge/` has a format defined
here — which fields exist, their types, and the editorial conventions the
knowledge base follows — so the loaders, the review tooling and future
contributors share a single definition instead of inferring it from examples.

The schemas describe the **document envelope**. They complement, and never
replace, the semantic validation of `mordheim_knowledge.loader`, which stays
the authority on cross-document references, id grammar, the runtime
classification contract and legal construction.

## Document map

| Document | Schema | Content |
| --- | --- | --- |
| `bands/<collection>/<band-id>/band.yaml` | [`band.yaml`](./band.yaml.schema.json) | Identity, collection/grade, sources, roster frame (size, gold, member slots), band-level `rule_ids` and optional variants. |
| `…/profiles.yaml` | [`profiles.yaml`](./profiles.yaml.schema.json) | Every hero, henchman, animal and summoned creature: cost, experience, characteristic line, equipment and skill access, inherent rules and traits. |
| `…/equipment-access.yaml` | [`equipment-access.yaml`](./equipment-access.yaml.schema.json) | The equipment lists a warband buys from at creation, with the prices printed for it. |
| `…/special-rules.yaml` | [`special-rules.yaml`](./special-rules.yaml.schema.json) | The editorial special rules: source prose plus the classification that binds them to the engines. |
| `catalog/items/*.yaml` | [`catalog-items.yaml`](./catalog-items.yaml.schema.json) | Canonical item records by category; one shared shape for the whole family. |
| `catalog/skills/*.yaml` | [`catalog-skills.yaml`](./catalog-skills.yaml.schema.json) | Skill definitions of the general and warband tables. |
| `catalog/rules/conditions.yaml` | [`catalog-rules-conditions.yaml`](./catalog-rules-conditions.yaml.schema.json) | Conditions rules reference instead of restating. |
| `catalog/rules/core-combat.yaml`, `catalog/rules/special-rules.yaml` | [`catalog-rules-prose.yaml`](./catalog-rules-prose.yaml.schema.json) | Rule text without runtime classification; band rules point at it with `rule_ref`. |
| `catalog/rules/racial-maximums.yaml` | [`catalog-rules-racial-maximums.yaml`](./catalog-rules-racial-maximums.yaml.schema.json) | The only source of racial characteristic maximums. |
| `catalog/rules/resolution.yaml` | [`catalog-rules-resolution.yaml`](./catalog-rules-resolution.yaml.schema.json) | The numeric contracts the engines roll against: to-hit, to-wound, armour modifier, injury, critical hits, parry. |
| `catalog/rules/implemented-canonical-families.yaml` | [`catalog-rules-implemented-canonical-families.yaml`](./catalog-rules-implemented-canonical-families.yaml.schema.json) | Tracker of the shared executable families and their member rules. |
| `catalog/mechanics/close-combat.yaml` | [`catalog-mechanics-close-combat.yaml`](./catalog-mechanics-close-combat.yaml.schema.json) | Engine-facing weapon, armour, defence, material, preparation, poison and skill mechanics with their engine options. |
| `catalog/mechanics/execution.yaml` | [`catalog-mechanics-execution.yaml`](./catalog-mechanics-execution.yaml.schema.json) | The execution contract: handler, trigger, application, stacking and parameters per mechanic id. |
| `catalog/mechanics/simulation-mappings.yaml` | [`catalog-mechanics-simulation-mappings.yaml`](./catalog-mechanics-simulation-mappings.yaml.schema.json) | The item→engine bridge. |
| `registry/aliases.yaml` | [`registry-aliases.yaml`](./registry-aliases.yaml.schema.json) | Band aliases for name normalization. |
| `registry/collections.yaml` | [`registry-collections.yaml`](./registry-collections.yaml.schema.json) | Collections and the rulesets each one allows. |
| `registry/rulesets.yaml` | [`registry-rulesets.yaml`](./registry-rulesets.yaml.schema.json) | The rulesets of the repository. |
| `registry/sources.yaml` | [`registry-sources.yaml`](./registry-sources.yaml.schema.json) | Registered editorial sources. |
| `registry/warband-groups.yaml` | [`registry-warband-groups.yaml`](./registry-warband-groups.yaml.schema.json) | Cross-band groups by race, alignment, faction and culture. |
| `registry/runtime-scope.yaml` | [`registry-runtime-scope.yaml`](./registry-runtime-scope.yaml.schema.json) | Scope policy, exclusions with reasons, supported combat traits. |
| `registry/runtime-schema.yaml` | [`registry-runtime-schema.yaml`](./registry-runtime-schema.yaml.schema.json) | The classification contract itself. |
| `catalog/hirelings/hired-swords/*.yaml` | [`hireling-profile-hired-sword.yaml`](./hireling-profile-hired-sword.yaml.schema.json) | The Hired Swords: characteristics, intrinsic equipment, skill access, starting skills, intrinsic rules and rating contribution. |
| `catalog/hirelings/dramatis-personae/*.yaml` | [`hireling-profile-dramatis-personae.yaml`](./hireling-profile-dramatis-personae.yaml.schema.json) | The Dramatis Personae, including the entries published `out_of_scope` with their reason. |
| `catalog/hirelings/*/rules.yaml` | [`hireling-rules.yaml`](./hireling-rules.yaml.schema.json) | The shared hiring rules the profiles point at with `rule_ids`. |
| `catalog/hirelings/traits.yaml` | [`hirelings-traits.yaml`](./hirelings-traits.yaml.schema.json) | The closed trait vocabulary the hiring eligibility rules reason about. |
| `catalog/campaign/post-battle-sequence.yaml` | [`campaign-post-battle-sequence.yaml`](./campaign-post-battle-sequence.yaml.schema.json) | The post-battle steps in normative order, each naming the document it resolves. |
| `catalog/campaign/serious-injuries.yaml` | [`campaign-serious-injuries.yaml`](./campaign-serious-injuries.yaml.schema.json) | The injury tables and their typed effects (`roster.remove_warrior`, `warrior.add_condition`, `equipment.disposition`, `prisoner.create`, `relationship.add_hatred`, …). |
| `catalog/campaign/experience-and-advances.yaml` | [`campaign-experience-and-advances.yaml`](./campaign-experience-and-advances.yaml.schema.json) | Experience awards, the underdog bonus, the advance tables and the threshold ladder. |
| `catalog/campaign/exploration-and-income.yaml` | [`campaign-exploration-and-income.yaml`](./campaign-exploration-and-income.yaml.schema.json) | Dice allocation, the shards chart, the exploration results and the `follow_up` procedure tree that resolves them. |
| `catalog/campaign/trading-post.yaml` | [`campaign-trading-post.yaml`](./campaign-trading-post.yaml.schema.json) | Market price, availability, typed restrictions and purchase options. |
| `catalog/campaign/trading-and-rarity.yaml` | [`campaign-trading-and-rarity.yaml`](./campaign-trading-and-rarity.yaml.schema.json) | The rarity test and the equipment allocation rules. |
| `catalog/campaign/magic.yaml` | [`campaign-magic.yaml`](./campaign-magic.yaml.schema.json) | Casting rules, the wizard-to-lore assignments and the lores with their spells. |
| `catalog/campaign/scenarios.yaml` | [`campaign-scenarios.yaml`](./campaign-scenarios.yaml.schema.json) | Scenarios, selection tables and the `progression` block they award. |
| `catalog/campaign/scenario-rewards.yaml` | [`campaign-scenario-rewards.yaml`](./campaign-scenario-rewards.yaml.schema.json) | The rewards of a scenario as resources, loot charts or exploration bonuses. |
| `catalog/campaign/hired-swords-and-dramatis.yaml` | [`campaign-hired-swords-and-dramatis.yaml`](./campaign-hired-swords-and-dramatis.yaml.schema.json) | Fees, upkeep, availability, static eligibility and its semantics. |
| `catalog/campaign/mutations.yaml` | [`campaign-mutations.yaml`](./campaign-mutations.yaml.schema.json) | The mutation purchase rules and the mutation list. |
| `catalog/campaign/recruitment-and-veterans.yaml` | [`campaign-recruitment-and-veterans.yaml`](./campaign-recruitment-and-veterans.yaml.schema.json) | Recruitment policies and the veteran availability procedure. |
| `catalog/campaign/warband-rating.yaml` | [`campaign-warband-rating.yaml`](./campaign-warband-rating.yaml.schema.json) | The rating formula, its components and exclusions. |

Every maintained YAML document of `sources/knowledge/` is claimed: the test
suite fails when a new file appears without a schema, and when a document is
claimed by two schemas. One document is declared outside the contract
(`registry/bindings.yaml`, the staging binding registry of the 2A/2B ingestion
workflow, gated by `tests/knowledge/test_binding_registry.py`); the exception is
listed in `editorial_schemas.UNCOVERED_DOCUMENTS` and the suite fails if it goes
stale.

## Conventions the schemas encode

- **Stable ids.** Band, profile, item, skill, rule, effect and mechanic ids
  match `^[a-z0-9][a-z0-9._-]*$`; band rule ids use the `<owner>--<name>`
  grammar. Ids are never renamed — scenarios pin sources by id and content
  digest, and campaign files reference stable KB ids only.
- **Locale policy.** English is canonical and stored once in `name`/`effect`;
  `name_i18n`/`effect_i18n` carry translations only and never mirror `en`.
- **Provenance.** Records carry `source_refs` (or a single `source`) with the
  manual, printed page, section and, when available, the URL.
- **Runtime classification.** The `runtime` block of a rule is defined as
  `registry/runtime-schema.yaml` defines it: `scope` (`YES`/`NO`/`LATER`),
  `implemented` (`YES`/`NO`), `grant` (`profile`/`band`/`selectable`/`none`),
  one or more `effects` with an executable `binding` or a `reason` explaining
  its absence, and `kind` whenever the rule is `selectable`.
- **Executable traits.** `profiles.yaml` `combat_traits` mirrors the key
  registry of `mordheim_construction.contracts.TRAIT_TYPES`, and
  `registry/runtime-scope.yaml` may only support traits the compiler knows.
- **Execution parameters.** `execution.yaml` parameters are keyed by the fields
  of `mordheim_core.models.EffectSet`; a parameter outside that set is a
  contract violation.
- **One text, one place.** A rule carries its own `effect` prose **or** a
  `rule_ref` into the rules catalogue — never both, never neither. Equivalence
  is declared by sharing a binding, never by repeating prose.
- **Implemented means linked.** An item marked `implemented` names its
  `mechanic_id`; an implemented mapping names its `engine_option`.
- **Catalogue envelope.** Every document of `catalog/hirelings/` and
  `catalog/campaign/` declares `schema_version`, `ruleset`, `catalog` and
  `status`; `status` is the shared `catalog_status` definition, so the editorial
  lifecycle means the same thing in every catalogue. The version is part of the
  format: `hired-swords-and-dramatis.yaml` and `scenario-rewards.yaml` are at
  version 2, the rest of the campaign catalogue at version 1.
- **Typed effects, never prose.** A campaign outcome that changes a warband is a
  typed operation with a closed key set: `warrior.add_condition`,
  `roster.remove_warrior`, `reward.grant`, `grant_rule`, `roll_table`,
  `conditional`, `sequence` … The schema rejects a key no application reads,
  and an unknown `type` is not a valid node.
- **One record, one owner.** A campaign entry points at another catalogue with
  an id (`profile_id`, `item_id`, `scenario_id`, `lore`) and never copies the
  record it points at. A hireling profile holds what belongs to the warrior, and
  `hired-swords-and-dramatis.yaml` holds the fee, the upkeep and the eligibility.
- **Numbers as data, state outside.** Rolls travel as structured values
  (`dice`, `amount`, `interval`), not as text, and the state a rule produces —
  injuries, crowns, wyrdstone, purchases, accumulated Experience — is never
  stored in these documents.
- **Closed vocabularies.** The values a rule branches on are enums, not free
  text: scenario tags and settings, restriction kinds, reward kinds, rarity
  targets, item `kind`, trait names, characteristic names. A new value is a
  contract change, made on purpose.
- **A post-battle step names a real document.** The `resolves` of a step is the
  enum of the files of `catalog/campaign/`, and the test suite keeps that enum
  equal to the directory.

## Deliberate allowances

These are source facts or documented conventions, not defects, and the schemas
accept them explicitly:

- `equipment-access.yaml` `cost` may be `null` (the source prices the item
  relative to another one, e.g. gromril weapons) or a dice expression
  (`25+1D6`); both require the `notes` explaining the price.
- `equipment_lists[].items` may be empty when the list is made of `loadouts`
  alone (Pit Fighter styles), and a loadout entry may offer a `choose_one`
  whose options bundle several items (`sword + sword`).
- `band.yaml` `grade` is `null` for the Trollheim collection, and
  `source_ref.printed_page` is text when the source is a page range (`74-80`).
- `source_ref.manual` is normally a registered source id; a few rules-catalogue
  records still carry the printed manual name (`Mordheim Rulebook`).
- `source_refs` may be empty: the provenance has not been collated yet.
- `special-rules.yaml` still carries the legacy `runtime_selectable` and
  `skill_category` fields; `runtime.grant: selectable` supersedes the first.
  They are accepted, documented and awaiting removal in an editorial pass.
- `implemented-canonical-families.yaml` still declares `schema_version: 1`
  while the other editorial documents are at 2.
- `trading-post.yaml` `price` is `null` for the entries the source lists without
  printing a market price (the four common entries such as `fist`, and every
  `not_sold` entry), and the price of a record being upgraded may be a
  `multiplier` instead of a `base_gc`.
- `availability.rarity` is declared exactly for a `rare` item, and a rolled
  surcharge is `price.optional_variable_cost` (`{ dice, multiplier? }`), so
  `10 + 1D6` and `D6 x 25` are both structured.
- An amount may carry a `multiplier` (`D6 x 10`) or an `offset` (`D6+1`) next to
  its `value`/`dice`, because the source prints those outside the dice.
- `scenarios.yaml` declares `number` only for the scenarios whose source prints
  one, and `progression` may consist of `notes` alone: a scenario that grants
  nothing documents the absence instead of leaving it to be inferred.
- `magic.yaml` assigns a lore to a hireling wizard with `band: null`, because a
  Hired Sword or a Dramatis Persona belongs to no warband.
- `exploration-and-income.yaml` uses `$parameters` (`$searching_hero`) and
  `trading-and-rarity.yaml` the caller's `$requested_item_id`: a parameter is
  not an id and the schema accepts it only where the procedure binds one.
- `dramatis-personae` entries may be published with
  `normalization_status: out_of_scope` and an `out_of_scope_reason`, and are then
  absent from the hiring catalogue. A Hired Sword has no such status.
- A hiring entry may charge no upkeep (`upkeep: null`) and a Dramatis entry no
  fee (`hiring_fee: null`), because some characters are summoned or granted
  rather than paid for.
- An empty list is the declared convention for `nothing pending` /
  `no restriction`: `restrictions`, `unresolved_references`, `tags`,
  `effects`, `exclusions` and `modifiers` are written as `[]` where the source
  declares nothing.
- `registry/bindings.yaml` belongs to the 2A/2B staging workflow and is the one
  document outside the contract, listed explicitly in
  `editorial_schemas.UNCOVERED_DOCUMENTS`.

## Validation

The contract is enforced by the structural gate and by the test suite:

```powershell
python tools/mordheim-utils.py validate          # structure, connections, editorial schemas
python tools/knowledge/audit_schema_strictness.py  # how the schemas relate to the data
python -m pytest tests/knowledge/test_editorial_schemas.py
```

`mordheim_knowledge.editorial_schemas` reads the schemas from this directory,
merges `defs.schema.json` into the document schema before validating (so the
files stay modular without a schema registry at run time) and walks the band
packages, the catalogue and the registry. The tests also fail when a document
escapes the contract, when the committed knowledge base stops matching the
schemas, and when the schemas drift from the code-level contracts they mirror.

## Strictness: the schemas against the data

A schema describes the shape the knowledge base has, not a shape it might have.
`mordheim_knowledge.editorial_schema_audit` checks that in both directions over
every document the contract claims, and the suite fails on a finding it cannot
classify:

- **Hard findings** — a node that leaves keys undescribed
  (`additionalProperties: true`, or declared `properties` with nothing closing
  the object), a tautological subschema, a key present in the documents and
  described nowhere, or a definition no schema can reach. There are none: a
  schema that accepts more than the knowledge base holds is a hole, not a
  liberty.
- **Soft findings** — a declared property, JSON type, enum value or
  `oneOf`/`anyOf` branch that no document exercises. These are decisions, not
errors, and each one lives in `editorial_schema_audit.JUSTIFIED_FINDINGS` with
the contract that keeps it alive: a field of `EffectSet`, a value of
`registry/runtime-schema.yaml`, a trait of `TRAIT_TYPES`, a recipient the
post-battle engine dispatches on, a shape the two hireling families share, or
`status: draft`, which `catalog/campaign/README.md` prescribes. An entry that
stops matching a finding fails the suite, so the list cannot rot.

The audit reads the same merged schemas the validators use, aggregates evidence
by definition instead of by use site, and counts a branch's vocabulary only when
the branch matches — so "nothing uses it" means the whole knowledge base, not
one document.

## Ownership

A format change is a contract change: update the schema **and** the knowledge
base in the same change, or the gate fails. Adding a field to a document
without extending its schema is a validation error by construction.
