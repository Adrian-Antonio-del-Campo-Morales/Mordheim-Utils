# Knowledge base

A single canonical **knowledge base (KB)** lives in `sources/knowledge/` and is
the source of both applications: shared catalogues, warbands, profiles,
equipment, skills, mechanics and the registry that ties them together.

Three ideas define the KB, and everything else follows from them:

1. **The KB declares rules and data, never results.** The accumulated
   experience, gold, rolls and purchases of a concrete warband belong to the
   campaign state of the applications, not to the KB.
2. **The KB carries no evidence of correctness.** Its structural contract is
   checked by `check verify`; behavioural evidence lives in modular mechanics and E2E
   tests. Runtime does not depend on its own tests. Editorial text is reviewed against the written sources
   (mordheimer.net / The New Mordheimer), never against engine output.
3. **Stable ids are the backbone.** Every rule, profile, item, mechanic and
   effect keeps a stable id. Equivalence between rules is *always explicit* —
   via shared bindings — and is never inferred from names or prose.

Runtime scope today is **one-against-one close combat** (`close-combat-only`):
shooting, movement, mounted combat, group psychology, magic progression and
post-battle rules are outside the current duel runtime and are classified as
such. Individual combat psychology with an executable contract (Fear,
Stupidity, Leadership tests) is inside the runtime.

## Layout at a glance

```text
sources/knowledge/
├── README.md                     locale policy + validation commands
├── registry/                     collections, rulesets, sources and their
│                                 documents, aliases, warband groups, runtime
│                                 classification schema
├── bands/                        per-warband editorial data, by collection
│   ├── mordheim/                 one directory per Mordheim warband
│   └── trollheim/                Trollheim/Chaos Streets/Lustria/Khemri warbands
├── catalog/                      cross-band shared data
│   ├── items/                    canonical item records (weapons, armour, …)
│   ├── skills/                   skill definitions (general + warband)
│   ├── rules/                    core combat rules, resolution tables, conditions,
│   │                             racial maximums, family trackers
│   ├── mechanics/                engine-facing mechanics + execution contracts
│   ├── hirelings/                Hired Swords and Dramatis Personae (see its README)
│   └── campaign/                 campaign tables for the campaign runtime (see its README)
```

## registry/ — the lookup and constraint layer

| File | Content |
| --- | --- |
| `collections.yaml` | The two collections, `mordheim` and `trollheim`, both bound to the `mordheim` ruleset. |
| `rulesets.yaml` | The active ruleset (`mordheim`). |
| `sources.yaml` | Registered editorial sources (e.g. `mordheimer.net`). |
| `source-documents.yaml` | The source documents the catalogues cite: every URL a document is cited by, how it is read (`pdf`/`page`) and where the offline mirror keeps its copy. It is what resolves a record's `source_refs` without guessing file names (`tools/knowledge/source_documents.py`). |
| `aliases.yaml` | Band aliases for name normalization (e.g. "Amazons (Lustria)" → `amazons-lustria`). |
| `warband-groups.yaml` | Cross-band groups by race/alignment/faction (e.g. `warband-group.orc`, `warband-group.chaotic`, `warband-group.good-aligned`) used by access and restriction logic. |
| `runtime-schema.yaml` | **The classification contract.** Defines `scope`, `implemented`, `grant`, `effects`, binding kinds and the invariants every rule must satisfy. |
| `runtime-scope.yaml` | Scope policy of the runtime: `close-combat-only`, plus a list of mechanics excluded with a reason (mounted lances, missile skills, psychology, movement…). |

Group IDs are namespaced `warband-group.<slug>`; eligibility and restriction
blocks of the campaign catalogues reference them exactly by that id
(`mordheim_knowledge.campaign.load_warband_groups` validates all references;
tests in `tests/knowledge/test_campaign_loaders.py`).

### Runtime classification (`runtime-schema.yaml`)

Every classified special rule carries a `runtime` block. The block is
validated against this schema — see `packages/python/knowledge/mordheim_knowledge/loader.py`
(`validate_rule_runtime`).

| Field | Meaning | Values |
| --- | --- | --- |
| `scope` | Does the effect belong to the current duel runtime? | `YES` / `NO` / `LATER` |
| `implemented` | Does it have an executable implementation? | `YES` / `NO` |
| `grant` | How is it granted? | `profile` / `band` / `selectable` / `none` |
| `effects[].id` | Stable effect id (a shared mechanic id or `unimplemented.*`). | string |
| `effects[].binding` | The executable link (`kind` + `id` + optional `parameters`). | binding or `null` |
| `effects[].reason` | Required explanation when there is no binding. | string |

A rule with `grant: band` and `applies_to.band: true` may also restrict its
recipients with `applies_to.profile_ids`. The grant identifies its band ownership;
the profile filter identifies which warriors receive it, and its IDs must resolve.

`selectable` rules (warband skills, mutations, blessings…) additionally declare
`kind` (`warband_skill`, `mutation`, `blessing`, `virtue`, `mark`,
`modification`, `profile_ability`, `warband_variant`).

Binding kinds:

- `mechanic` — a shared executable mechanic (see `catalog/mechanics/`).
- `trait` — a shared trait.
- `profile` — executable construction data already normalized in
  `profiles.yaml` (characteristics, skill access, restrictions, natural
  attacks, random characteristics).
- `compiler` — transitional; should be replaced by `mechanic`/`trait` when
  possible.

Key invariants (abridged — the full list is in the schema file):

- A rule keeps its own KB id; *equivalent* rules share
  `binding.kind`, `binding.id` and `binding.parameters`.
- Equivalence is never inferred from rule names or prose.
- `implemented: YES` only when **every** `YES` effect has an executable
  binding; an unbound effect must explain why in `reason`.
- Rules **without** a `runtime` block are not classified yet and must not be
  treated as implemented.

## bands/ — the editorial warband data

Each collection (`mordheim`, `trollheim`) contains one directory per warband.
A band directory is typically four files:

| File | Content |
| --- | --- |
| `band.yaml` | Canonical band: id, name, publication, sources, roster (min/max models, starting gold, members per profile with per-group sizes) and the band's `rule_ids`. |
| `profiles.yaml` | Each profile: id, name, type (`hero`/henchmen), cost, starting experience, characteristics (`M WS BS S T W I A Ld`), `equipment_lists`, `equipment_restrictions`, `skill_access`, inherent `rule_ids` and `combat_traits`. |
| `equipment-access.yaml` | The equipment lists each profile may buy from (creation prices; the Trading Post is the market price — see below). |
| `special-rules.yaml` | The editorial special rules of the band. |

**Every document has a formal format.**
`contracts/knowledge-editorial-v1/` holds one JSON Schema per document (plus
the shared `defs.schema.json`) describing its fields, types and editorial
conventions: the four files of a band package, the catalogue families
(`items`, `skills`, `rules`, `mechanics`), the hireling catalogue
(`hired-swords`, `dramatis-personae`, their `rules.yaml`, `traits.yaml`) and the
campaign catalogue (the thirteen documents of `catalog/campaign/`, including the
typed campaign effects and the exploration procedure tree).
`mordheim_knowledge.editorial_schemas` validates them all, the structural
layer of `verify` fails on any mismatch, and
`tests/knowledge/test_editorial_schemas.py` keeps the schemas
in step with the code contracts they mirror (`EffectSet`, `TRAIT_TYPES`,
`runtime-schema.yaml`, the documents a post-battle step may resolve, the band
skill-list vocabulary). The suite also fails when a maintained YAML document
appears that no schema claims. See
[the contract README](../../contracts/knowledge-editorial-v1/README.md) for the
document map and the single document declared outside the contract.

**The schemas describe the knowledge base, not a shape it might have.**
`mordheim_knowledge.editorial_schema_audit` compares every schema with the
documents it claims and fails the suite on a hole — a node that leaves keys
undescribed, a tautological subschema, a key the documents carry and the
contract never names, a definition nothing can reach — and on a declaration no
document exercises unless it is listed with the contract that keeps it alive.
`python tools/knowledge/audit_schema_strictness.py` prints the same report, so a
curator can see which declarations the data backs before touching a schema.

Example — `bands/mordheim/orc-mob/band.yaml` declares the Orc Mob (Town
Cryer #6 / Mordheim Annual 2002): 500 starting gold, 3–20 models, required
Orc Boss, henchmen groups sized 1–5, and its ten `band--*` rule ids.

### Anatomy of an editorial special rule

Each entry in `special-rules.yaml` is human editorial text plus a machine
classification:

```yaml
- id: troll--regeneration
  name: Regeneration
  effect: '…editorial prose…'            # + name_i18n / effect_i18n
  source: { manual: mordheimer.net, section: …, url: … }
  applies_to: { profile_ids: [troll] }
  runtime:
    scope: 'YES'          # part of the duel runtime
    implemented: 'YES'    # has an executable binding
    grant: profile        # granted by the profile itself
    effects:
    - id: skill.regeneration
      scope: 'YES'
      binding: { kind: mechanic, id: skill.regeneration }
```

The three classification states show up constantly in the real files:

- **Implemented** — `troll--regeneration` above: bound to the shared mechanic
  `skill.regeneration`.
- **Deferred** — e.g. Orc Boss `Leader` (any warrior within 6" uses his
  Leadership): `scope: LATER`, `implemented: 'NO'`,
  `reason: 'Deferred subsystem: psychology or mounts.'`
- **Out of scope** — e.g. Orc Shaman `Wizard`: `scope: 'NO'` with a reason
  such as campaign/shooting/movement context.

## catalog/ — shared cross-band data

This is where reusable data lives so that band files reference it instead of
duplicating it.

### items/

Canonical item records, split by category: `weapons-close-combat.yaml`,
`weapons-ranged.yaml`, `armour.yaml`, `shields-and-defences.yaml`,
`combat-equipment.yaml`, `druchii-equipment.yaml`,
`materials-and-upgrades.yaml`, `miscellaneous.yaml`, `trollheim.yaml` and
`out-of-scope.yaml`.

Items use **snake_case ids** (`broadsword`, `crimson_shade`) and carry
`kind`, i18n names, `source_refs`, a `combat_status`
(`implemented`/…), and the executable link:

```yaml
- id: broadsword
  kind: close-combat-weapon
  name: Broadsword
  source_refs: [ … ]
  combat_status: implemented
  mechanic_id: weapon.broadsword
```

### skills/

Skill definitions for `general.yaml` (common skill lists) and `warband.yaml`.
Shared skills are the reference target of many band rules, e.g.
`skill.regeneration` here is the *same id* the Orc Mob Troll binds to.

### rules/

| File | Content |
| --- | --- |
| `core-combat.yaml` | Canonical combat rules as editorial text (combat order, two weapons, parry, critical hits, injury states). |
| `resolution.yaml` | The numeric local contracts consumed by the engines: to-hit, to-wound, strength→armour modifier, injury table, critical-hit and parry rules. |
| `conditions.yaml` | Conditions shared by rules. |
| `special-rules.yaml` | Cross-band shared rules, promoted here only **after** an equivalence review; band rules reference them with `rule_ref` and keep their own runtime. |
| `racial-maximums.yaml` | The only source of racial characteristic maximums (`campaign.limit.racial-maximum.*`); warband rules reference them by id instead of embedding statlines. |
| `implemented-canonical-families.yaml` | Tracker of the shared mechanic families that already have executable bindings; update it when bindings evolve. |

### mechanics/

The engine-facing layer of the KB:

- `close-combat.yaml` — weapon/mechanic descriptions under the `weapon.*`
  namespace: hands, paired, `engine_option` (the option the engine
  understands), source refs.
- `execution.yaml` — the **execution contract**: each mechanic id maps to a
  `handler` plus `parameters`, with `trigger` / `application` / `stacking`.
  Example: `skill.regeneration` → `handler: effect-set` with
  `regeneration_save: 4` and `regeneration_blocked_by_fire: true`.
- `simulation-mappings.yaml` — the item→engine bridge: every `item_id` maps
  to `status: implemented | out_of_scope` and, when implemented, its
  `engine_option` (e.g. `axe` → `Axe`, `battle_axe` → `Axe`).

So the layers of the same weapon are: item record (`items/`, snake_case id)
→ mechanic id (`mechanic_id: weapon.broadsword`) → engine option
(`engine_option` in `mechanics/close-combat.yaml`) → parameters
(`mechanics/execution.yaml`).

### hirelings/ and campaign/

- `hirelings/` — `hired-swords/` and `dramatis-personae/` catalogues own
  intrinsic identity, characteristics, equipment, skills, rules and rating.
  Hiring fees, upkeep, search and eligibility belong to
  `campaign/hired-swords-and-dramatis.yaml`; reusable group facts belong to
  `registry/warband-groups.yaml`.
- `campaign/` — the persistent campaign rules: post-battle sequence, trading
  post, serious injuries, experience and advances, exploration and income,
  recruitment and veterans, warband rating, trading and rarity, scenarios,
  magic, mutations and hired swords. These documents are **published data for the
  campaign runtime**; their README covers data ownership and the loader
  contract, and its HOWTO explains how to query the
  catalogue from application code. Campaign entries reference canonical
  `item_id` values without copying item records.


Profile IDs are `hireling.hired-sword.<slug>` or `hireling.dramatis.<slug>`;
`campaign.hireling.<slug>` entries reference a `profile_id`. A matching name
alone does not justify reusing a band profile or equating items/skills. Unknown
concepts stay in the profile's `unresolved_references`; remove only references
that resolve after adding the canonical catalogue/schema. Do not invent IDs.
Campaign rolls, choices and rewards are runtime state, not KB facts. Dynamic
roster/variant restrictions use `*.rule.campaign-eligibility` and canonical
traits rather than application-maintained sets. Composite warriors, mounts or
selectable personas remain `status: out_of_scope` until a schema can represent
them without flattening their rules.

`mordheim_knowledge.campaign.load_hirelings(ruleset)` is the authorized read
path: it validates IDs, rule references and items; campaign loaders additionally
resolve hiring `profile_id` references. Editorial schemas in
`contracts/knowledge-editorial-v1/` validate structure before loader contracts;
`tests/knowledge/test_campaign_loaders.py` covers the loader boundary.

### Source provenance and catalogue comparison

Records cite manuals, printed pages, sections and URLs through `source_refs`.
`registry/source-documents.yaml` resolves each cited URL to its document and
to its local mirror copy under the unversioned `sources/origins/` directory;
undeclared citations fail `tests/knowledge/test_source_documents.py`. Use
`tools/knowledge/source_documents.py` to resolve a record's document and
`tools/knowledge/printed_entries.py` to read the printed entry. Missing offline
copies are reported as missing, never compared against an empty page.
`tools/knowledge/check_hireling_sources.py` applies this comparison to both
published hireling catalogues across all grades.

Printed wording is evidence, not a global alias or permission to rename a
canonical item. Preserve the following reviewed correspondences only in their
stated source context (slugs identify the source warband):

| Printed wording | Catalogue key | Source context |
|---|---|---|
| Double-handed weapon / Double handed weapon / Two-handed weapon | `great_weapon` | Rulebook and supplements. |
| Holy Water | `blessed_water` | `protectorate-of-sigmar-lotd3`, Protectorate list; `vampire-hunters-of-sylvania-lotd5`, hero list. Miracle Workers separately prints Blessed water. |
| Sigmarite Warhammer | `sigmarite_hammer` | `protectorate-of-sigmar-lotd3`, Protectorate list. |
| Long Bow Heroes only | `long_bow` | `outlaws-of-stirwood-forest-redux-fbg`; Heroes only is availability, not part of the item name. |
| Halbard | `halberd` | `forest-goblins-lus`; printed typo, not a general spelling. |
| Wardog | `warhound` | `bretonnian-knights-errant-mou`. |
| Double-handed weapon | `two_handed_weapon` | `channel-rats-mim`. |
| Horsemens Hammer | `horsemans_hammer` | `knights-of-the-bitter-moors-mim`. |
| Toughened leather | `toughened_leathers` | `silent-brotherhood-sc`. |
| Rope and Hook | `rope_hook` | `guild-of-disgraced-engineers-mim`. |
| Superiour Black Powder | `superior_blackpowder` | `guild-of-disgraced-engineers-mim`; printed typo. |
| Ball and Chain | `ball_chain` | `underworld-alliance-mim`. |
| Plague Censor | `plague_censer` | `skaven-of-clan-pestilens-lus` and `skaven-of-clan-pestilens-mou`; printed typo. |
| Jezzail (175GC) | `jezzail` | `skaven-of-clan-skryre-kaz`. |
| Warplock Pistol | `warp_pistol` | `skaven-of-clan-pestilens-lus`; paired by `campaign.trading-post.warplock-pistol`. |

A source may delegate an equipment list instead of printing its rows. KAZ's
Clan Mors and Clan Skryre say that all rulebook equipment lists apply; their
`skaven-hero-equipment-list` rows therefore come from the rulebook list
transcribed under `skaven-clan-eshin`. KAZ's Dwarf Guildsmen names the Dwarf
Thunderers equipment list but prints no handgun price; use the rulebook's
`thunderer-equipment-list` for that price. These are explicit delegations,
not missing rows or invented source prices.

## Locale policy

English is **canonical and stored once**: the `name` field (and the `effect`
prose). The `name_i18n` / `effect_i18n` blocks store only *translations* for
non-canonical locales (`es`) and never carry an `en` mirror of the canonical
English — duplicating long English prose invites silent drift, and nothing
renders the copy anyway. `tools/knowledge/maintenance/normalize_names.py` enforces this (it strips
any `en` mirror and drops a locale block left without a real translation),
and `tests/knowledge/test_kb_i18n.py` guards the invariant independently.

The KB carries a **reviewed Spanish translation**: every warband's rules,
profiles and band names, the hired swords and campaign catalogues, and the
skill / item / mechanic catalogues fill `name_i18n.es` / `effect_i18n.es`
with text reviewed against the same printed sources as the English. `es`
fields are data-only: `mordheim_knowledge.i18n` — the single sanctioned
reader (`set_locale` / `display_name` / `display_effect`, translation-first,
canonical-English-fallback) — is wired into both applications, so a filled
`es` surfaces immediately under `MORDHEIM_LOCALE=es`. An unfilled record
simply renders its canonical English.

Canonical glossary terms and the resolved edge cases live in
[the translation glossary](translation-glossary.md); new translations should
follow it (Caballero Andante = Questing Knight, Caballero Novel = Knight
Errant, chequeo = test, 1D6 = D6) so Spanish stays consistent across the KB.

### Binding-based name consistency

A rule's `binding` (`kind` + `id`, plus optional `parameters`) declares
semantic identity for the engines: two rules bound to the same mechanic are
simulated identically. The binding does **not** constrain the display name —
`name_i18n` is never read by the engine, and different source rules may
legitimately carry different English names for the same mechanic (e.g.
`mechanic/skill.tough-as-steel` appears as "True Grit", "Extra Tough" and
"Hard as Steel").

Spanish translation policy therefore follows the English source: a shared
Spanish name is required only when both the binding **and** the English name
match. When rules share a binding but their English names differ, each rule
translates its own English name directly. This mirrors the `trait.*`
exception (the trait is shared but the flavour rule name is band-specific).
`tests/knowledge/test_band_translation_parity.py`
(`test_equivalent_rules_share_the_same_spanish_name`) enforces exactly this:
consistency gated on `(binding kind, binding id, English name)`.

### Name capitalization

Every display name — the canonical `name` field and the `name_i18n.es`
translation — is **title case**: the first letter of every significant word
is capitalised, while minor words (English and Spanish prepositions, articles
and conjunctions) stay lowercase unless they open or close the name
(`A Night in the Graveyard`, `Flechas de Plata de Arha`). Hyphenated
compounds capitalise each segment except preposition-like parts
(`Men-at-Arms`, `Two-Handed Sword`). All-caps abbreviations, digits, proper
nouns, Orcish-dialect names (`Waaagh!`, `'Ere We Go!`) and domains
(`mordheimer.net`) are preserved.

Scalar quoting of names is canonicalised too — safe values are plain, quotes
are kept only when YAML requires them. Run it idempotently after editing any
maintained YAML names:

```powershell
python tools/knowledge/maintenance/normalize_names.py --check sources/knowledge
python tools/knowledge/maintenance/normalize_names.py --write sources/knowledge
```

It edits only name scalars lexically — comments, anchors, aliases and key
order are preserved — and verifies that only name fields changed.

## YAML formatting policy

Maintained YAML uses UTF-8, LF line endings, two-space indentation, no trailing
whitespace and the line-width policy enforced by the formatter. URLs and
unavoidable long identifiers are the expected exceptions.

Rule prose has **one key: `effect`** (plus its locale block `effect_i18n`).
There is no `summary` key anywhere in `sources/knowledge` — the display text
of a rule, item, skill, condition, scenario, spell or mutation is always its
`effect`, and shared rules are defined once in the catalog with band rules
referencing them (`rule_ref`) instead of restating the prose. A test guards
that no `summary` key returns.

Descriptive prose uses folded blocks (`>-`) when wrapping is needed; literal
blocks (`|`) are reserved for meaningful line breaks. Formatting preserves
parsed values, IDs, key order, comments, anchors and aliases. Collection-shape
rules are enforced by tests rather than repeated here.

Use the repository formatter after changing maintained YAML:

```powershell
python tools/knowledge/maintenance/format_yaml.py --check sources/knowledge
python tools/knowledge/maintenance/format_yaml.py --write sources/knowledge
python tools/knowledge/maintenance/format_yaml.py --check sources/knowledge
```

`--check` parses every file and verifies semantic equivalence; `--write`
changes only formatting. Review its diff before committing.

## Contract guards

These read-only tools measure the canonical knowledge base and its schemas.

```powershell
python tools/knowledge/audit_kb_conformance.py
python tools/knowledge/audit_schema_strictness.py
python tools/knowledge/maintenance/format_yaml.py --check sources/knowledge
```

The conformance audit checks document shapes, runtime classification,
bindings and references; it reports (without failing) a rule that references a
shared rule while also restating its prose. Schema strictness finds loose or
unused declarations. See
[Repository tools](tools.md) for maintained tool ownership.

## Clause register

[The clause register CSV](../../sources/knowledge/verification/clause-contracts.csv) stores
clause contracts, scope, consumers and evidence. Its 4,556 keys are
`(id, clause_id)`, using current IDs; earlier IDs and pre-compaction data remain
in Git (pre-compaction checkpoint `cee529cd`). `pending` omits defaults
`work=none`, `review=reviewed`, `requires=[]`; `verification` retains inspection,
executed or absent evidence separately. A closed row is not certification.
The final JSON object `status` tracks NumPy and native independently: rows with
`clause_scope=YES` require both `numpy` and `native`; all other scopes require `{}`.
Each backend accepts `pending`, `in_progress`, `implemented`, `verified` or `blocked`.
`implemented` means integrated awaiting parity; `verified` means applicable parity
passed, not universal certification. Scope remains authoritative: changing scope
requires an explicit matching status update, without inferred closure or reset.
Reuse `consumer` for references to either engine, and `verification`/`notes` for
engine-qualified evidence and context. Identify the engine in notes or the linked
report; modular tests or a NumPy fallback do not establish native verification.
[The source scope review](../../sources/knowledge/verification/source-scope-review.csv)
feeds `verification/audit_export.py`; a source-text change invalidates an old
review. Applications read exclusively from consolidated `sources/knowledge`.

Access the clause register only through `python -X utf8 tools/knowledge/clause_registry.py`:

```powershell
python -X utf8 tools/knowledge/clause_registry.py query --id "ID_EXACTO" --clause-id "CLAUSULA"
python -X utf8 tools/knowledge/clause_registry.py query --pending --consumer contexts.py --limit 5
python -X utf8 tools/knowledge/clause_registry.py query --backend numpy --status pending --fields id,clause_id,status
python -X utf8 tools/knowledge/clause_registry.py prepare "$env:TEMP/clause-changes.json" --out "$env:TEMP/clause-prepared.json"
python -X utf8 tools/knowledge/clause_registry.py apply "$env:TEMP/clause-prepared.json"
# Authorized writer only, after reviewing the preview:
python -X utf8 tools/knowledge/clause_registry.py apply "$env:TEMP/clause-prepared.json" --write
```

`--id`/`--clause-id` are exact; `--source`/`--consumer` match fragments;
`--work`, `--review`, `--pending`, `--fields` and `--limit` narrow queries.
`--backend numpy|native` selects rows containing that backend; `--status` requires
`--backend` and filters its state. Existing `--pending` retains its original meaning.
To append `status` to the legacy schema, run `clause_registry.py migrate` for a
preview, then `clause_registry.py migrate --write` explicitly. Migration uses the
same lock, snapshot checks and external byte backup as apply, preserves all
original cells and line endings, and initializes admitted rows to both `pending`.
Repeating it preserves existing statuses. Packages prepared for the old schema
are rejected; prepare them again after migration.
Keep proposals/packages outside the repository. A proposal is a JSON array:

```json
[{"id":"ID_EXACTO","clause_id":"CLAUSULA","set":{"pending":{},"verification":["executed","path::test"]},"append_notes":"Explicit decision and evidence."}]
```

Structured cells take JSON objects/arrays, other cells take strings. Notes are
append-only by default; `replace_note_references` permits explicit existing
`completed.md` reference substitutions while preserving all other note text.
Do not infer semantics or bulk-close rows from status flags.

Before integration, preserve the complete current bytes outside the repository.
`prepare` validates the candidate and records the snapshot hash and full before/
after rows. `apply` previews by default; only the authorized writer uses
`--write`. It preserves keys, protected source fields, unrelated cells and record
line endings, creates a full temporary backup, acquires an exclusive `.csv.lock`
and rechecks bytes immediately before replacement. Retain the backup until
acceptance. Do not delete another writer's lock, alter packages to bypass checks,
or force an obsolete snapshot: reload and prepare explicit decisions again.
No direct CSV edits or alternative rewrite scripts. Failed conservation means
no write; after damage, suspend writes and notify the coordinator, never rebuild
from HEAD or old exports. The tool does not repair or certify earlier damage.
Tool tests use synthetic CSVs: `python -m pytest tests/knowledge/test_clause_registry.py -q`;
do not rerun them for rule-only changes.

## Where is the evidence?

Structural verification is the `check verify` entry point. Rule behaviour is
checked by `tests/engines/modular/mechanics/`, and connected construction/combat
by `tests/integration/e2e/`. Construction and KB contracts have their own suites.
Expectations come from written sources and adopted rulings, not engine output.

The semantic YAML test system is retired. Existing CSV evidence columns and
frozen-corpus provenance remain historical records; exports do not manufacture
passing evidence for the removed suite. See [Verification](verification.md).

## Path of a rule: from YAML to the engines

The canonical example is Troll **Regeneration** (`bands/mordheim/orc-mob/
special-rules.yaml` → `troll--regeneration`), which is granted to identical
mechanics across many bands (black-orcs, night-goblins, undead bloodlines…)
that all bind the same mechanic id — reuse without duplication.

1. **Editorial rule + classification.** The prose rule lives in the band's
   `special-rules.yaml` with sources and a `runtime` block (`scope: YES`,
   `implemented: YES`, `grant: profile`). Equivalence is declared by binding
   every variant to the same mechanic:
   `binding: {kind: mechanic, id: skill.regeneration}`.
2. **Shared mechanic.** `catalog/mechanics/execution.yaml` defines
   `skill.regeneration`: handler `effect-set`, parameters
   (`regeneration_save: 4`, `regeneration_blocked_by_fire: true`), passive
   trigger, fighter application. The numeric combat contracts the engines
   need live in `catalog/rules/resolution.yaml` and the phase model in
   `mordheim_combat.phases`.
3. **Loading and validation.** `mordheim_knowledge` (`loader.py`,
   `paths.py`) validates every rule runtime block and loads documents by
   stable ids. Path resolution goes through
   `mordheim_knowledge.loader.knowledge_root()` with the
   `MORDHEIM_COMBAT_LAB_KNOWLEDGE_PATH` override and frozen-EXE support.
4. **Compilation and legality.** `mordheim_construction` compiles canonical
   ids and legal choices into a `CompiledFighter`, enforcing equipment lists
   and restrictions, skill access, racial maximums and warband-group rules.
5. **Consumption.** The engines of `mordheim_combat` consume the compiled
   fighter. Effects are composed in `mordheim_core.effects`; the modular
   engine (the only correctness oracle) resolves the stateful flow — in this
   case a regeneration save in the wound/aftermath handling. Dice come from
   injected `DiceSource`, never from global randomness.
6. **Candidates.** The NumPy vectorized engine and the native Cython backend
   replicate the same phase order and tables and are certified against the
   oracle by `check parity` (per-field obligations + six-sigma statistical gates),
   sharing the same modular sample. A divergence is presumed to be a defect
   of the candidate — `check parity` only reads the oracle and never modifies it.
7. **Evidence.** Source-derived modular mechanics tests check rule consequences;
   E2E scenarios exercise actual granting/compilation and observable duel results.
   Statistical scenarios compare optimized engines with the reference. The audit
   export reports inventory and structural/planning status, not an automatically
   passed semantic scenario suite.

For items the same path holds with the extra indirection step: band
`equipment-access.yaml` lists item ids → `catalog/items/` record
(`combat_status`, `mechanic_id`) → mechanic → engine option.

## Golden rules for developers

- **Keep stable ids.** Never rename a rule, profile, item or mechanic id:
  scenarios pin their sources by id and content digest, and campaign files
  reference stable KB ids only. Add a band alias to `registry/aliases.yaml`
  instead of renaming.
- **Equivalence is explicit.** Two rules that do the same thing share
  `binding.kind` + `binding.id` (+ `binding.parameters`). Never reuse a rule
  name or copy prose and call it equivalent.
- **Classify everything.** A rule without a `runtime` block is
  *unclassified*, not implemented. `implemented: YES` requires every `YES`
  effect to have a binding; an unbound effect always needs a `reason`.
- **Prefer shared mechanics.** Bind to existing mechanics
  (`catalog/mechanics/execution.yaml`) or promote a cross-band rule into
  `catalog/rules/special-rules.yaml` only after an equivalence review.
  `compiler` bindings are transitional.
- **Protect the oracle.** The modular engine is the only correctness oracle.
  Changing it requires an independent semantic review and is outside the
  optimization flow; work on vectorized/native candidates is certified by
  `check parity` against it.
- **Evidence never comes from the engine.** Semantic expectations are
  reviewed against the written sources. The engine's output is never used to
  generate expected values.
- **Campaign catalogue ≠ runtime.** `catalog/campaign/` is published data for
  the campaign runtime; do not load it as duel-rule implementation. The
  application consumes it through the validated loaders and `KnowledgePort`.
  See the [campaign knowledge guide](../guides/campaign-knowledge.md) for
  ownership rules.

## Validation loop

After any KB change run the structural validation and the affected evidence:

```powershell
python tools/mordheim-utils.py check verify   # structure, connections, runtime schema and editorial JSON Schemas
python tools/mordheim-utils.py check parity   # vectorized/native certification against the oracle
python tools/mordheim-utils.py check report rules   # per-rule status CSV in outputs/audit/
```

See also [Modify the knowledge base](../guides/modify-knowledge-base.md),
[Implement and verify rules](../guides/implement-and-verify-rules.md), and
"Where a change lands" in [Architecture](architecture.md).
