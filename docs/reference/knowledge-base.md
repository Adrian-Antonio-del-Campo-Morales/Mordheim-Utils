# Knowledge base

A single canonical **knowledge base (KB)** lives in `sources/knowledge/` and is
the source of both applications: shared catalogues, warbands, profiles,
equipment, skills, mechanics and the registry that ties them together.

Three ideas define the KB, and everything else follows from them:

1. **The KB declares rules and data, never results.** The accumulated
   experience, gold, rolls and purchases of a concrete warband belong to the
   campaign state of the applications, not to the KB.
2. **The KB carries no evidence of correctness.** Its structural contract and
   semantic scenarios live in `tests/specs/`, so the runtime never depends on
   its own tests. Editorial text is reviewed against the written sources
   (mordheimer.net / The New Mordheimer), never against engine output.
3. **Stable ids are the backbone.** Every rule, profile, item, mechanic and
   effect keeps a stable id. Equivalence between rules is *always explicit* —
   via shared bindings — and is never inferred from names or prose.

Runtime scope today is **one-against-one close combat** (`close-combat-only`):
shooting, movement, psychology, mounts, magic progression and post-battle
rules are outside the current duel runtime and are classified as such.

## Layout at a glance

```text
sources/knowledge/
├── README.md                     locale policy + validation commands
├── registry/                     collections, rulesets, sources, aliases,
│                                 warband groups, runtime classification schema
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
| `aliases.yaml` | Band aliases for name normalization (e.g. "Amazons (Lustria)" → `amazons-lustria`). |
| `warband-groups.yaml` | Cross-band groups by race/alignment/faction (e.g. `warband-group.orc`, `warband-group.chaotic`, `warband-group.good-aligned`) used by access and restriction logic. |
| `runtime-schema.yaml` | **The classification contract.** Defines `scope`, `implemented`, `grant`, `effects`, binding kinds and the invariants every rule must satisfy. |
| `runtime-scope.yaml` | Scope policy of the runtime: `close-combat-only`, plus a list of mechanics excluded with a reason (mounted lances, missile skills, psychology, movement…). |

Group IDs are namespaced `warband-group.<slug>`; eligibility and restriction
blocks of the campaign catalogues reference them exactly by that id
(`mordheim_knowledge.campaign.load_warband_groups` validates all references;
tests in `tests/python/knowledge/test_campaign_loaders.py`).

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
`tests/python/knowledge/test_editorial_schemas.py` keeps the schemas
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
`combat-equipment.yaml`, `materials-and-upgrades.yaml`,
`miscellaneous.yaml`, `trollheim.yaml` and `out-of-scope.yaml`.

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
| `special-rules.yaml` | Cross-band special rules. Kept empty (`rules: []`) — promoted here only **after** an equivalence review. |
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

- `hirelings/` — `hired-swords/` and `dramatis-personae/` catalogues, with
  their own README covering id conventions, the trait registry, out-of-scope
  entities and the pending intrinsic references.
- `campaign/` — the persistent campaign rules: post-battle sequence, trading
  post, serious injuries, experience and advances, exploration and income,
  recruitment and veterans, warband rating, trading and rarity, scenarios,
  magic, mutations and hired swords. These documents are **published data for the
  campaign runtime**; their README covers data ownership, the price-collation
  policy and the loader contract, and its HOWTO explains how to query the
  catalogue from application code. Campaign entries reference canonical
  `item_id` values without copying item records.

## Locale policy

English is **canonical and stored once**: the `name` field (and the `effect`
prose). The `name_i18n` / `effect_i18n` blocks store only *translations* for
non-canonical locales (`es`) and never carry an `en` mirror of the canonical
English — duplicating long English prose invites silent drift, and nothing
renders the copy anyway. `tools/knowledge/maintenance/normalize_names.py` enforces this (it strips
any `en` mirror and drops a locale block left without a real translation),
and `tests/python/knowledge/test_kb_i18n.py` guards the invariant independently.

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
`docs/knowledge/translation-glossary.md`; new translations should
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
`tests/python/knowledge/test_band_translation_parity.py`
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
whitespace, and a target line width of **100 characters**. Lines up to **120
characters** are accepted. URLs and unavoidable long identifiers are the only
expected exceptions.

Rule prose has **one key: `effect`** (plus its locale block `effect_i18n`).
There is no `summary` key anywhere in `sources/knowledge` — the display text
of a rule, item, skill, condition, scenario, spell or mutation is always its
`effect`, and shared rules are defined once in the catalog with band rules
referencing them (`rule_ref`) instead of restating the prose. A test guards
that no `summary` key returns.

Descriptive fields such as `effect`, `description`, `notes`, and `reason` use
folded blocks (`>-`) when they need wrapping. This keeps source text readable
while loading it as one logical line. Literal blocks (`|`) remain reserved for
text where line breaks are meaningful. Formatting must preserve key order,
anchors, aliases, IDs, URLs, scalar types, and parsed values.

Effect prose is **never quoted**: the formatter rewrites every quoted `effect`
/ `effect_i18n.es` scalar (quoting was only ever needed for content such as
`: ` or `"`) as a `>-` block rewrapped at the target width, which makes the
same content plain-safe. Plain values that spill across continuation lines —
and single lines past the target width — are folded the same way, so every
effect value ends up as either a plain single line or a `>-` block.
`python tools/knowledge/maintenance/format_yaml.py --check sources/knowledge` reports zero residual
quoted or continuation-wrapped effect prose, and the pass is idempotent.

A `>-` block already in that shape is rewrapped when its body carries a line
past the 120 maximum: a writer that folds prose without wrapping it leaves one
physical line per value, and `--write` wraps those lines at the target width,
so what `--check` reports as too long is what it repairs. The block's value is
verified by the same round-trip guard as every other scalar, so a block whose
line breaks are content (paragraphs) is left untouched. Scalars the policy
keeps plain — flow collections and single-line values of keys outside the
descriptive set — are not folded for width.

The formatter is deliberately lexical, so it preserves a flow collection instead
of rewriting it; the **collection shape** is a separate rule. The KB writes eight
keys as block collections and never as a non-empty flow collection:
`source_path`, `equipment_lists`, `rule_ids` and `skill_access` as block
sequences (dashes at the indent of their key), and `source`, `characteristics`,
`name_i18n` and `combat_traits` as block mappings (children two columns in). An
empty `[]` / `{}` stays as it is: that is the KB's shape for "nothing".
`mordheim_knowledge.staging_promotion` writes the flow form back to the block
form (`normalize_staging_for_promotion.py --write --passes shape`, idempotent and
document-verified), `audit_staging_contract.py --only shape` measures the drift
and `tests/python/knowledge/test_staging_collection_shape.py` is the gate.

Line endings are part of the policy: the maintained YAML is LF-only (`.gitattributes`
declares `*.yaml text eol=lf`), and `--check` reads raw bytes so a CRLF file is
reported as needing reformatting instead of being hidden by newline translation.
The same check gates the staging trees (`python tools/knowledge/maintenance/format_yaml.py --check
sources/2A` / `sources/2B`), so a band package already looks like a
knowledge-base document before it is promoted.

`reason` strings — the audit-taxonomy metadata such as `Deferred subsystem:
psychology.`, `Out of scope: campaign.` or `dead` — are uniformly folded `>-`
blocks, quoted or plain, short or long, so every reason value shares one
style. `description` and `notes` fold only when the prose genuinely needs
wrapping: short values that fit the accepted line width keep their single-line
quotes (required for content such as `: `), while values longer than the
target width — or a hard line past 120 characters — are folded. Plain-safe
short values of the other keys stay as plain single lines.

Use the repository formatter after changing maintained YAML:

```powershell
python tools/knowledge/maintenance/format_yaml.py --check sources/knowledge
python tools/knowledge/maintenance/format_yaml.py --write sources/knowledge
python tools/knowledge/maintenance/format_yaml.py --check sources/knowledge
```

`--check` parses every file and verifies semantic equivalence after formatting;
`--write` changes only formatting. Review its diff before committing. It does
not format `tests/specs/`, `outputs/`, generated files, or engine code. Do not
run combat tests, parity, or benchmarks for a formatting-only change.

## Contract guards

These read-only tools measure the knowledge base against itself. They are permanent
(promoted out of the Grade 2a/2b ingestion pass) and each one takes `--tree` to check a
staging tree with exactly the same rules before promotion.

```powershell
python tools/knowledge/audit_kb_conformance.py           # the KB; 0 deviations is the baseline
python tools/knowledge/audit_kb_conformance.py --tree 2B # a staging tree, same checklist
python tools/knowledge/derive_kb_contract.py             # re-measure the contract, then self-check
python tools/knowledge/audit_schema_strictness.py        # editorial JSON Schemas vs the documents
python tools/knowledge/audit_staging_contract.py         # the staged 2A/2B packages vs the same schemas
python tools/knowledge/strip_rule_ref_restatements.py    # rule_ref rules must not restate their effect
python tools/knowledge/maintenance/format_yaml.py --check sources/knowledge    # canonical formatting (LF, folded prose)
```

* `audit_kb_conformance.py` checks document, roster, profile, equipment-list and rule
  shapes, the runtime contract, the binding vocabulary, `rule_ref` resolution and the
  `rule_ids` listing. Its accepted key sets are the hand-written baseline **unioned with
  the keys the KB itself carries**, so a key the KB legitimately uses is never reported as
  invented; the tree under audit contributes nothing to that union.
* `derive_kb_contract.py` re-measures those shapes from `sources/knowledge` and diffs a
  tree against the measurement, catching a checklist that drifted from the data.
* `audit_schema_strictness.py` reports how the editorial JSON Schemas relate to the
  committed documents: loose nodes, unreachable definitions, unused enums.
* `audit_staging_contract.py` validates the four documents of every *staged* band package
  with those same schemas, names the fields the contract deliberately leaves open
  (`sources[].manual`, `categories`, `grade`, `profiles[].source_path`) whose
  values the knowledge base never uses, checks the staged catalogues — items, Hired Sword
  and Dramatis profiles, market, magic and campaign documents — against the schema of the
  KB document that will claim them at promotion (the classes
  `sources/2B/promotion-schema-plan.md` decides on, now none in either tree), and lists the
  files `normalize_names.py` would rewrite. A file promotion declares it leaves behind
  (`staging_contract_audit.NOT_PROMOTED`) is named as a decision, not as a gap. Every pass
  is a gate that stays green: `tools/ingestion/normalize_staging_for_promotion.py` closes
  the catalogue one, the way `normalize_open_fields.py` and `normalize_names.py` close the
  vocabulary and the naming.
* `strip_rule_ref_restatements.py` enforces the shared-rule invariant above. It defaults
  to every maintained tree and archives any retracted wording in
  `sources/<tree>/retired-rule-restatements.md`.

The Grade 2a/2b ingestion tooling (pipelines, source cross-audits, migrations, staged
translation fillers) lives in `tools/ingestion/` and is **temporary**: that directory is
deleted when the ingestion phase ends. See its README for the inventory, the caches it
needs and the commands.

## Where is the evidence?

The KB has no `verification/` area of its own: the verification corpus — the
structural contract (`tests/specs/structural/phase-verification.yaml`) and the
semantic scenarios under `tests/specs/semantic/` — lives in `tests/`. It is
test material and is never distributed with the applications.

Semantic scenarios reference KB targets by canonical path and **content
digest**, so the corpus breaks loudly when the referenced rule changes:

```yaml
sources:
- {target: rule/mordheim/skaven-clan-eshin/band--skaven-special-skills-art-of-silent-death/skill.art-of-silent-death, digest: 63e78902…}
depends_on: [mechanic/skill.art-of-silent-death]
```

Each case fixes the source, interpretation, category, initial status, dice,
decisions, expectations and mutations; dice and decision sources are strict
(unexpected or unconsumed requests fail), and probabilities are exact
fractions. The modular engine is the system under test — its output is never
used to generate the expected value. See [Verification](verification.md).

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
   stable ids. Path resolution goes through `knowledge_root()` with the
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
   oracle by `parity` (per-field obligations + six-sigma statistical gates),
   sharing the same modular sample. A divergence is presumed to be a defect
   of the candidate — `parity` only reads the oracle and never modifies it.
7. **Evidence.** Scenarios in `tests/specs/semantic/` pin the rule source by
   digest, exercise granting/compilation and the observable duel result with
   strict dice, and apply deliberate mutations to prove the tests are not
   vacuous. `audit` merges the editorial inventory, scope and executed
   evidence into the per-rule status CSV.

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
  `parity` against it.
- **Evidence never comes from the engine.** Semantic expectations are
  reviewed against the written sources. The engine's output is never used to
  generate expected values.
- **Campaign catalogue ≠ runtime.** `catalog/campaign/` is published data for
  the campaign runtime; do not load it as duel-rule implementation. The
  application consumes it through the validated loaders and `KnowledgePort`.
  The remaining catalogue work is the price-collation review and the deferred
  scope listed in [TODO](../TODO.md): collate every `cost` in
  `equipment-access.yaml` against the Trading Post and convert real exceptions
  to explicit `price_override` entries.

## Validation loop

After any KB change run the structural validation and the affected evidence:

```powershell
python tools/mordheim-utils.py verify --structural   # structure, connections, runtime schema, editorial JSON Schemas
python tools/mordheim-utils.py verify                # the above plus the semantic specs against the real engine
python tools/mordheim-utils.py parity                # vectorized/native certification against the oracle
python tools/mordheim-utils.py report rules          # per-rule status CSV in outputs/audit/
python tools/mordheim-utils.py combine-kb            # flatten directories for a review pass
```

See also [Modify the knowledge base](../guides/modify-knowledge-base.md),
[Implement and verify rules](../guides/implement-and-verify-rules.md), and
"Where a change lands" in [Architecture](architecture.md).
