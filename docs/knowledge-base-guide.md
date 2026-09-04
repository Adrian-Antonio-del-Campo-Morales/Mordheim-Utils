# Knowledge base guide

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
rules are outside the current duel runtime and are classified as such (see
[Runtime scope](#runtime-scope)).

## Layout at a glance

```text
sources/knowledge/
├── README.md                     KB overview + commands
├── CAMPAIGN INGESTION RESULTS.md ingestion report of the campaign catalogue
├── registry/                     collections, rulesets, sources, aliases,
│                                 warband groups, runtime classification schema
├── bands/                        per-warband editorial data, by collection
│   ├── mordheim/                 ~48 warband directories
│   └── trollheim/                Trollheim/Chaos Streets/Lustria/Khemri warbands
├── catalog/                      cross-band shared data
│   ├── items/                    canonical item records (weapons, armour, …)
│   ├── skills/                   skill definitions (general + warband)
│   ├── rules/                    core combat rules, resolution tables, conditions,
│   │                             racial maximums, family trackers
│   ├── mechanics/                engine-facing mechanics + execution contracts
│   ├── hirelings/                Hired Swords and Dramatis Personae
│   └── campaign/                 campaign tables for the future campaign runtime
```

## registry/ — the lookup and constraint layer

The registry holds the small files that give the rest of the KB its shape:

| File | Content |
| --- | --- |
| `collections.yaml` | The two collections, `mordheim` and `trollheim`, both bound to the `mordheim` ruleset. |
| `rulesets.yaml` | The active ruleset (`mordheim`). |
| `sources.yaml` | Registered editorial sources (e.g. `mordheimer.net`). |
| `aliases.yaml` | Band aliases for name normalization (e.g. "Amazons (Lustria)" → `amazons-lustria`). |
| `warband-groups.yaml` | Cross-band groups by race/alignment/faction (e.g. `warband-group.orc`, `warband-group.chaotic`, `warband-group.good-aligned`) used by access and restriction logic. |
| `runtime-schema.yaml` | **The classification contract.** Defines `scope`, `implemented`, `grant`, `effects`, binding kinds and the invariants every rule must satisfy. |
| `runtime-scope.yaml` | Scope policy of the runtime: `close-combat-only`, plus a list of mechanics excluded with a reason (mounted lances, missile skills, psychology, movement…). |

### Runtime classification (`runtime-schema.yaml`)

Every classified special rule carries a `runtime` block. The block is
validated against this schema — see `src/mordheim_knowledge/loader.py`
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
| `equipment-access.yaml` | The equipment lists each profile may buy from. |
| `special-rules.yaml` | The editorial special rules of the band. |

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
| `implemented-canonical-families.yaml` / `pending-canonical-families.yaml` | Trackers of mechanic families by implementation state. |

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

- `hirelings/` — `hired-swords/` and `dramatis-personae/` catalogues.
- `campaign/` — the persistent campaign rules: post-battle sequence, trading
  post (338 entries), serious injuries, experience and advances, exploration
  and income, recruitment and veterans, warband rating, trading and rarity,
  98 scenarios, magic (45 lore↔wizard assignments, 31 lores, 188 spells),
  mutations and hired swords. These documents are **published data for the
  future campaign runtime**; no YAML of this catalogue may be loaded as rule
  implementation yet (the loaders are runtime-integration work). Campaign
  entries use namespaced kebab ids (`campaign.<family>.<detail>`) and
  reference items by canonical `item_id` without copying them.

## Where is the evidence?

The KB has no `verification/` area of its own (a previous empty placeholder
was removed): the verification corpus — the structural contract
(`tests/specs/structural/phase-verification.yaml`) and the semantic scenarios
(`tests/specs/semantic/`, ~160 files) — lives in `tests/`. It is test
material and is never distributed with the applications.

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
used to generate the expected value.

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
  the future campaign runtime; do not load it as rule implementation. The
  open migration (documented in its README): collate every `cost` in
  `equipment-access.yaml` against the Trading Post and convert real
  exceptions to explicit `price_override` entries.

## Validation loop

After any KB change run the structural validation and the affected evidence:

```powershell
python tools/mordheim-utils.py validate      # structure, connections, runtime schema
python tools/mordheim-utils.py verify        # semantic specs against the real engine
python tools/mordheim-utils.py parity        # vectorized/native certification against the oracle
python tools/mordheim-utils.py audit         # per-rule status CSV in outputs/audit/
python tools/mordheim-utils.py combine-kb    # flatten directories for a review pass
```

`verify` is green (`semantic_complete=True`, 217/217 required interactions
covered, 0 pending) and `parity` reports 0 divergences since the interaction
matrix implementation (2026-09-04); both are part of the evidence a KB change
must keep green. Every required interaction pair is covered either by a pair
spec under `tests/specs/semantic/interactions/` or by an `illegal` override in
`tests/specs/interaction-policy.yaml` — see the [interaction
matrix](interaction-matrix.md).

See also [Modify the knowledge base](tasks/modify-kb.md), [Verify
rules](tasks/verify-rules.md), and "Where a change lands" in
[structure.md](structure.md).
