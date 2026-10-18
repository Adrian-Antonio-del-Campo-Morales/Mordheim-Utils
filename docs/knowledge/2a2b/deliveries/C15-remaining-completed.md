# C15 — residual scope and source dispositions (14 clauses)

**Final delivery, 2026-10-17: the three rows the coordinator retained are
implemented and closed; C15 is 16/16.** Warpaint and Elven Wine now have a
catalogue contract, an executable `duel_start` binding, a printed recipient
route and a compiled consumer. The eleven integrated closures and the two Dwarf
inheritance rows were not reopened.

**Final coordinator integration completed:** three remaining rows applied with a
fresh full snapshot, prepare/preview and concurrency checks; all 4,556 keys,
source texts, fingerprints and notes conserved, prior consumers and verification
accumulated. Integration evidence: `%TEMP%/c15-final-coordinator-j7ebxuai/`.
The executor's nine focused cases and thirty preparation cases were reused
without rerunning them. C15 is closed in the CSV, not merely proposed. No E2E,
commit or push.

**Coordinator integration, 2026-10-17: 11 closures accepted, 3 rows retained
pending.** (Superseded by the final delivery below: those three rows — the two
Warpaint clauses and the Elven Wine clause — are now closed, with the package
re-prepared for the coordinator.) The two single-use rows and the Warpaint
Gobbo bearer allowance were withheld because both items still lacked an
executable admitted connection; list membership alone does not establish usable
equipment. Missing schema/consumer was implementation work, not an external
source blocker. Together with the two earlier Dwarf inheritance closures, C15
was 13/16 at that point.

The duplicate wizards_staff is no longer present. The coordinator ran only
test_c15_residuals.py on the current tree: 7 passed; output retained in
`%TEMP%/c15-coordinator-final.txt`. Fourteen CSV decisions integrated (11 closures
and 3 explicit implementation pendings) with full snapshot, conservation of all
4,556 keys/source text/fingerprints/notes and concurrency checks. Evidence:
`%TEMP%/c15-residual-coordinator-9e0tuzw5/`. No broader rerun, E2E, commit or push.

Base: `2A2B` at `a1f9265`, shared working tree. These 14 clauses are the remainder
of C15 after the two `inherited-combat-rules` rows were integrated; those two
were not reopened.

## Implemented

- **Mazzalupo supplied Commands.** The compiler guard compared the promoted band
  id (`mazzalupo-web`) with the bare name `mazzalupo`, so neither supplied
  Command could be activated on the canonical recipient; only synthetic band-less
  builds reached the engine. The guard now reads the band's `canonical_family`
  (`compiler.py`), as the same file already does for other promotions. Both
  Commands now compile on `mazzalupo-web/wandering-knight` and are still refused
  on another band.
- **Snotling projection markers.** `shoota-teams--teamwork` and
  `snotling-mobs--teamwork` declared a deferred "multi-model single-unit
  abstraction" that the duel does not need: one printed profile already is one
  participant with one injury/resource state. The false marker is replaced by
  `profile.single-model-projection` (scope NO, no executable effect), with the
  printed prose and recipients preserved.
- **Machine-Ogre customisation marker.** `band--customisation-chart` was
  "provisional... pending scope refinement". It is now classified exactly: the
  2D6 roll happens in the post-battle sequence for a Skaven Hero with Tinker-Rat,
  so the chart is a campaign exclusion, not a missing duel binding.
- **Revival Sermons marker.** The deferred reason "psychology or mounts" is
  replaced by the actual excluded producer: sermon delivery, its group reception
  and the sermon list. The individual armour permission is not part of that rule.

No new combat subsystem, casting, group reception, campaign sequence, shooting,
movement, mount or E2E surface was added. No inert binding was created.

### Final delivery: Warpaint and Elven Wine

Both rows were blocked by the *same* shape, and the fix is one reused operator,
not two new ones: a declaration the build can make (`preparation_ids`), an
effect-set binding that fires at `duel_start`, and the printed recipient route
(the band's own list plus the item's market clause). "One use only" is the
single pre-battle application that covers that battle; no saving throw or Fear
test spends the object, and no consumable counter was invented.

- **Catalogue contract.** `warpaint` (`combat-equipment.yaml`) and `elven_wine`
  (`miscellaneous.yaml`, moved out of `out-of-scope.yaml`) are
  `combat_status: implemented` with `mechanic_id: preparation.warpaint` /
  `preparation.elven-wine`. Both market rows
  (`campaign.trading-post.warpaint`, `campaign.trading-post.elven-wine`) already
  carried the printed price and band restriction, so supply was not re-authored.
- **Printed clauses.** `preparation.warpaint` and `preparation.elven-wine` are
  declared in `close-combat.yaml` with the printed prose, engine option and
  source pages (Karak Azgal p59; Lustria p113 / mordheimer Shadow Warriors).
- **Execution.** `execution.yaml` binds both as `handler: effect-set`,
  `trigger: duel_start`, `application: fighter`, `stacking: once`:
  `preparation.warpaint` → `{tags: [preparation.warpaint], ward_save: 6}`;
  `preparation.elven-wine` → `{tags: [preparation.elven-wine,
  mechanic.fear-immunity]}`. No new operator, no resource, no duration field.
- **Recipients.** The shared eligibility projection (`eligibility/index.ts`,
  mirrored in `eligibility.py`) decides `preparationOptions`/`preparationIssue`
  from the same printed facts: the Savage Orc list line has no `applies_to`, so
  every Savage Orc profile (boss, weirdo, spottaz, brutes, nuttaz, boyz) *and*
  `gobbo-boyz` reach Warpaint; the wine reaches the High Elf list profiles and
  the Shadow Warrior market clause, not the Cadet list of the same band. A
  mercenary is neither offered nor accepted, and `compile_fighter` refuses with
  `printed recipients` instead of silently compiling.
- **Effect.** Warpaint's 6+ save resolves through the existing
  `prepare_special_save_context` / `resolve_special_save` path (after armour,
  unmodified by Strength or weapon modifiers — reused, not extended). Elven
  Wine's `mechanic.fear-immunity` tag is what `psychology.resolve_fear` already
  honours, so the Fear roll is simply not requested; the tag is
  Fear-specific and never `mechanic.psychology-immunity`.

`npm run check:eligibility`: **shared eligibility bundle is current**, so the
Python bridge runs the same source as the browser.

## Reused implementation

| family | existing consumer |
|---|---|
| three robes | `armour.eshin-assassin-robes`, `armour.mage-robes`, `armour.wizard-robe` + `prepare_armour_context` / `validate_loadout` |
| Commands' engine | `rounds.resolve_round` (duration) and `contexts.prepare_hit_context` / `_injury_context` |
| Snotling teams | `compiler.compile_fighter` (one participant) |
| Wheelo crew | profile `fixed_equipment: [dagger, small_pebble]` |
| Machine-Ogre attack | empty list → `weapon.natural-attacks`, S5/A3 |
| Prophet / Cleric armour | shared `profileFacts` equipment projection (`toughened_leathers`, `light_armour`) |
| preparations | `preparation.*` declaration + `execution.yaml` effect-set; Warpaint reuses the special-save path, Elven Wine the `mechanic.fear-immunity` tag (final delivery) |

## The 14 dispositions

| id | clause | disposition |
|---|---|---|
| `item/eshin_assassin_clothes` | `printed-text-missing` | closed — printed paragraph on the entry, mechanic bound, 20 tests green |
| `item/mage_robes` | `printed-text-missing` | closed — same, khemri p61, helmet refused |
| `item/wizard_robe` | `printed-text-missing` | closed — same, chaos p68/167 |
| `...follow-me-mine-pugnacious-ones` | `whole` | closed — canonical-band guard fixed; +1 hit reuse |
| `...art-thou-ready-to-die-fighting` | `whole` | closed — same; threshold 6 until next own turn |
| `R/...shoota-teams--teamwork/*` | `single-model-projection` | closed — projection is the compiled participant; marker corrected |
| `R/...snotling-mobs--teamwork/*` | `single-model-projection` | closed — same |
| `B/...snotlings-web/.../profiles/7` | `whole` | closed for the crew kit — dagger + pebble in `fixed_equipment`; movement/impact stay on their siblings |
| `B/metal-mongers-mim/.../profiles/5` | `whole` | closed — natural attack compiled; Tinker-Rat chart excluded as post-battle |
| `BT/...mordheim-inhabitants/.../profiles/0` | `armour-with-sermons` | closed — armour reachable and compiled; sermon producer excluded |
| `B/outlaws.../profiles/2/equipment_restrictions/1` | `whole` | closed — `light_armour` reaches the Cleric; no Prayer producer |
| `B/savage-orcs-kaz/.../items/13` | `whole--scope--single-use` | **closed (final)** — `preparation.warpaint` binds the printed 6+ save at `duel_start`; one use = one battle, never one saving throw |
| `B/savage-orcs-kaz/.../items/13` | `whole--scope--bearer-allowance` | **closed (final)** — every Savage Orc profile and `gobbo-boyz` are offered and compiled; a foreign mercenary is refused |
| `BT/lustria-high-elves/.../items/15` | `recipient--scope--single-use` | **closed (final)** — `preparation.elven-wine` grants battle-long Fear immunity to the individual bearer; the group reading is not simulated |

## CSV

`prepare` (preview only) produced **3 changes**, one per `(id, clause_id)`, from
a complete byte snapshot; notes and earlier evidence are appended to, never
replaced, and conservation plus untouched-row checks passed:

`C:\Users\PHOLTE~1\AppData\Local\Temp\c15-war\package.json`

Snapshot `sha256 3d2e8e349d051cb0…` still matches the current
`T13-semantic-analysis.csv` byte-for-byte (checked again after preparing). Each
row moves to `clause_scope: YES`, names its `effect_id`, `relation`,
`parameters`, `conditions`, real `consumer` paths, empties `pending` and replaces
the inspection-only `verification` with executed tests. No `apply --write` and
no direct CSV edit; integration belongs to the coordinator. The earlier
14-change package for the already-integrated rows is history, not this delivery.
The two `single-model-projection` row ids keep their frozen historical
`unimplemented...` suffix; the KB descriptor they point at is
`profile.single-model-projection`.

## Files owned by this delivery

Earlier rows:

- `packages/python/roster-construction/mordheim_construction/compiler.py`
- `sources/knowledge/bands/mordheim/snotlings-web/special-rules.yaml`
- `sources/knowledge/bands/mordheim/metal-mongers-mim/special-rules.yaml`
- `sources/knowledge/bands/trollheim/chaos-streets-mordheim-inhabitants/special-rules.yaml`
- `tests/python/construction/test_c15_residuals.py`

Final delivery:

- `sources/knowledge/catalog/mechanics/close-combat.yaml` (two preparation declarations)
- `sources/knowledge/catalog/mechanics/execution.yaml` (two `duel_start` bindings)
- `sources/knowledge/catalog/items/combat-equipment.yaml` (`warpaint` contract)
- `sources/knowledge/catalog/items/miscellaneous.yaml` (`elven_wine` contract)
- `packages/typescript/domain/eligibility/index.ts` and the regenerated
  `packages/python/roster-construction/mordheim_construction/_eligibility.js`
- `packages/python/roster-construction/mordheim_construction/eligibility.py`
- `packages/python/roster-construction/mordheim_construction/compiler.py`
  (preparation compilation and the recipient refusal)
- `tests/python/construction/test_c15_warpaint_and_wine.py`
- this document

## Evidence (green runs before the concurrent breakage)

- `tests/python/construction/test_c15_residuals.py`: **7 passed**, EXIT=0.
- `tests/python/construction/test_t13_wardrobe_variants.py`: **20 passed**, EXIT=0.
- Commands: `test_t13_hireling_command_matrix.py` + `test_local_modifier_variants.py -k "command or follow_me or ready_to_die"`: **155 passed**, EXIT=0.
- Editorial schemas for the three edited packages: **3 passed**, EXIT=0.
- `test_binding_registry.py`: **3 passed**, EXIT=0.

### Final delivery (fresh, single run each, saved outside the tree in `%TEMP%/c15-war/`)

- `test_c15_warpaint_and_wine.py`: **9 passed**, EXIT=0 (`pytest.txt`). Covers the
  printed recipients and their refusals, the 6+ save after armour against a
  Strength 5 strike, Fear immunity versus a real Fear-causing charger, the
  no-immunity control without the wine, and the single-use discriminators (two
  strikes of one duel both meet the same save; a second declaration changes
  nothing; one Fear-immunity tag).
- `test_preparation_access.py` + `test_supplied_equipment_preparations.py`:
  **30 passed**, EXIT=0 (`preparations.txt`) — the reused preparation/supply
  operators were not changed by this delivery.
- `npm run check:eligibility`: **bundle current**, EXIT=0.
- `npm run typecheck --workspace packages/typescript` (`tsc --noEmit`, covers
  the edited eligibility projection): **EXIT=0** (`typecheck.txt`).

## Exact blockers

- **Resolved concurrent catalogue duplicate.** At delivery time `wizards_staff` was declared
  twice — `sources/knowledge/catalog/items/combat-equipment.yaml:556` and the
  newly added `sources/knowledge/catalog/items/weapons-close-combat.yaml:1785`
  (both files already modified by another owner). Every item load now raises
  `ValueError: item catalogue has missing or duplicate IDs`, so the final re-run
  of the seven C15 cases fails at load, after all of them had passed. The file
  was not edited here. The three edited packages still pass their editorial
  schema checks after the breakage (**3 passed**, EXIT=0), because those checks
  do not load the item catalogue. The duplicate is now resolved; the coordinator's
  seven-case final run passes, as recorded above.
- **The two single-use clauses** — **resolved in the final delivery**, see
  above. The absence of a uses/consumption member was read as what it is: the
  items needed a declaration plus a battle-scoped binding, not a resource.
- **Elven Wine's printed group wording.** The source describes a Shadow Warrior
  *warband* that drinks the wine; the assigned clause is `recipient`-scoped and
  group reception is excluded, so the implementation grants the immunity to the
  individual bearer that legitimately receives the preparation and does not
  model shared drinking. That is the one printed aspect deliberately not
  simulated; the effect itself is not weakened.
- **Warpaint's "one use only" has no further printed definition.** It is read as
  the single pre-battle application covering that battle (the same reading the
  item's own prose supports) and never as one saving throw; nothing in the
  engine consumes the object mid-duel.
- **Foreign editorial-schema failures in the shared tree (not mine, not
  repaired).** Validating the edited documents directly shows my three catalogue
  documents pass (`miscellaneous.yaml`, `out-of-scope.yaml`, `trading-post.yaml`)
  and neither added mechanics row produces a finding. Three edited-by-others
  files still fail on changes made outside this package: `combat-equipment.yaml`
  (an `Eye Pendant` row with `kind: equipment`), `execution.yaml` (a `true_grit`
  property), `close-combat.yaml` (weapons 100/101 missing `rules_source_url`,
  skills 114 `kind: band`, skills 329 `effect_i18n`). They belong to the
  concurrent catalogue owner.
- **Web artefact.** Not regenerated: the generator still stops on the recorded
  Spanish label conflict in a foreign band file. This delivery adds no new web
  prose.
- **CSV.** The executor did not write; the coordinator completed the final
  three-row integration with its own snapshot and concurrency checks above.
- E2E was not executed, inspected or edited.
