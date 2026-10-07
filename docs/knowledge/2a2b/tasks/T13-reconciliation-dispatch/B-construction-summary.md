# T13 reconciliation dispatch — LOT B-construction

Independent reconciliation of the construction candidates assigned to lot
**B-construction**. Entry list is the frozen `B-construction.csv`; this report
classifies every assigned clause against the current canonical facts, the shared
eligibility module and the actual consumers. It proposes repairs; it implements
none and accepts nothing.

## 1. Entry, inputs and limits

- Repository `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`, branch **`2A2B`**,
  HEAD **`820d1499a0c9ff04fd42975d3de9d97bd62d585d`**. No `AGENTS.md` exists in
  the checkout.
- **Input verified**: `B-construction.csv` SHA-256
  `79f735c6d1860a597a9c5116263f395e3d5271223fa1c22fbcc90f555a6cc403`,
  507 data rows — both match `manifest.json` (`lots.B-construction`). Hash and
  row count were re-checked at closure and are unchanged.
- **Source re-extraction**: all 507 ids were re-resolved through the maintained
  export (`build_audit_rows(inventory_only=True)`); the raw extracted effect
  text still hashes to the frozen `effect_sha256` for **507/507**, so every row
  is `source_state = current` (no drift, no stale review).
- Owned outputs: this file and `B-construction-results.csv` (507 rows, columns
  as dispatched, UTF-8, LF). Scratch and the resolver/classifier scripts live in
  `build/audit/reconciliation/B/`. No KB, code, register, assignment list or
  shared asset was modified; nothing was committed.
- **Limits**: classification is by code inspection of
  `packages/typescript/domain/eligibility/index.ts`, the canonical YAML and the
  editorial schemas. No per-row behavioural probe was run; labels distinguish
  inspection from execution. Grouping is clause-driven and heuristic at the
  edges — counts are exact per row but the *reason* of a row is a reviewer
  judgement, never a false "executed" claim.

## 2. Counts

507 assigned rows, 507 results (one per id, no extras or duplicates).

| Status | Rows |
| --- | ---: |
| `covered` | 243 |
| `metadata_gap` | 200 |
| `out_of_scope` | 57 |
| `implementation_missing` | 5 |
| `partial` | 2 |

By input family:

| Family | Rows | Status split |
| --- | ---: | --- |
| profile `equipment_restrictions` prose | 250 | covered 178, metadata_gap 65, impl_missing 5, partial 2 |
| equipment-list item `notes` | 202 | metadata_gap 116, out_of_scope 49, covered 37 |
| hireling fixed-item `notes` | 30 | covered 28, metadata_gap 2 |
| hireling `unresolved_references` | 18 | metadata_gap 15, out_of_scope 3 |
| catalogue rule placeholders | 7 | out_of_scope 5, metadata_gap 2 |

`covered` means the clause is honoured by a current consumer: the canonical
`profile.equipment_lists`/`fixed_equipment` projection, a
`profile.equipment-restrictions` `forbids` token, a `compiler.*` contract, the
legacy prose branch of `buildRestriction`, or a hardcoded band/item exclusion.
When a clause is *subsumed* because the profile cannot reach the forbidden item
itself (empty list, no armour, no ranged item), the contract column says
`subsumed: ...` so the reason is explicit rather than assumed.

## 3. Grouped actionable gaps

**G1 — per-item bearer/role qualifiers (131 rows).** 102 item-note qualifiers
(`Heroes only`, `Tinker only`, `Skaven only`, `Loremaster only`, …) and 29
profile restrictions (`May not select the Snake Whip; it is restricted to the
Lahmian Vampire and Blood Sister.`, `May not select a Helmet; that entry is
Skink Priest only.`, `The Armour section is available to Quartermasters and
Flayerkin only.`, …). `profileEquipmentItems` reads declared lists and the fixed
kit only; `equipment-access.yaml` item `notes` are never read. Hardcoded hero
exceptions cover the few cases in code (`katana`, `long_daggers`,
`darksteel_blade`, `spirit_knife`, `skull_busta`). Closure: the shared decision
refuses the item for every non-qualifying profile. Existing follow-up: **F019**.

**G2 — armour prohibition with reachable armour (22 rows).** `May not wear
armour.` on `estalian-corsairs-sar` (6), `pirates-of-the-cathayan-sea-sar` (6),
`sartosan-pirates-sar` (6), `khorne-raiders-sar` (3),
`nipponese-expedition-web` (1). The lists offer `light_armour`/`heavy_armour`/
`helmet`/`shield`, and neither a `forbids: armour` binding nor a matching legacy
phrase (`buildRestriction` matches `never wear armour`, not `may not wear
armour`) exists for these profiles. The pattern is already used by 27 bands
(e.g. `dwarf-rangers` `dwarf-troll-slayers--no-armour`, `forbids: armour`).
Closure: `equipmentIssue` refuses the reachable armour/shield items. Existing
follow-up: **F019**.

**G3 — missile/ranged prohibition (5 rows).**
`clan-angrund-kep/dwarf-troll-slayers` (`…or any form of armour`),
`dark-elf-corsairs-mou/corsairs`, `disciples-of-maldred-mou/mercenaries`,
`lustria-high-elves/sword-guardians`,
`lustria-savage-goblins/red-teeth` (`…unless they have the Thrown Weapon rule`).
No `ranged-weapons`/`non-thrown-ranged` token and no `compiler.no-missile-weapons`
contract for those profiles, while ranged items stay reachable. Closure:
`equipmentIssue` refuses every reachable ranged item. Existing follow-up: **F020**.

**G4 — other loadout/category restrictions (3 rows).** `May use only
one-handed weapons.`, `May never use polearms.`, `May not use heavy armour,
polearms or great weapons.` — no `profile.active-weapon-restrictions`/`forbids`
or `forbids: heavy-armour` binding. Closure: `activeWeaponIssues`/
`buildRestriction` refuse the category. Existing follow-up: **F019**.

**G5 — hireling unresolved references (15 rows).** Recorded under
`unresolved_references`: `skill` (`Art of Silent Death`, `Ride Tol'Agath`,
`Ride Pantomime Horse`), `equipment_choice` (`Sword or Axe`, `two Axes or
Double-handed Weapon`, `heavy chain (counts as flail) or two Hammers/Clubs`,
`Duelling Pistol or Crossbow Pistol`), `equipment_mapping` (`Lantern`,
`Repeater Crossbow`, `three Torches`), `equipment_restriction` (`blunt weapons
only except dagger; no armour except white wolf cloak`), plus
`multi_loadout_persona`, `multi_profile_entity` and `random_profile`. Closure:
each reference resolves to a canonical id and is offered by the hireling
projection. Existing follow-up: **F036–F038**.

**G6 — hireling fixed-item dangling records (2 rows).** `arcane_candelabrum`
(`MiM-specific item … deliberate dangling ref`) and the MiM axe note; the
structured `item_id` has no `catalog/items` record, so `resolveHirelingKit`
reports `equipment_unknown_item`. Closure: a canonical record or an explicit
governed placeholder.

**G7 — catalogue rule placeholders (2 rows).**
`hireling.dramatis.luthor-wolfenbaum.rule.i-am-everywhere` (`Uses source persona
rule.`) and `hireling.dramatis.rule.fixed-equipment` (a special character's
equipment is personal and cannot be transferred or bought extra) carry
`runtime.effects[].binding == null`. Closure: the rule carries an executable
binding honoured by the current consumer.

**G8 — no construction contract at all (5 rows, `implementation_missing`).**
`Must buy a weapon from the hand-to-hand combat list; a simple dagger is not
acceptable.`; `May not have more Thaggi than other Henchmen`; Feather Headdress
leader-only (3 variants across two bands). Each needs a product decision before
it can be modelled or excluded.

**G9 — mixed clauses (`partial`, 2 rows).** The plague-monk robe clause combines
a material/armour-equivalence consequence with kit access; only the kit part is
canonical. Split admitted vs excluded text; route the consequence to the
item/combat lot.

## 4. Out-of-scope decisions (57 rows)

- 44 equipment-list notes state *internal item mechanics are intentionally not
  modelled here* — explicit exclusion, no B work.
- 12 mount/ridden clauses (5 `mount_profile` references and hireling mount rules,
  7 equipment-list mount notes) — excluded by the governing 1v1 scope.
- 1 `campaign.mutation.grant.aquatic-mutants` — campaign purchase, published
  campaign data.

Purely price/rarity lines carry no construction clause and were folded into
`out_of_scope` only where they had no bearer qualifier; where they did, the
qualifier is the recorded gap.

## 5. Blockers and decisions needed

1. **Feather Headdress / Thaggi / required hand-to-hand weapon (G8):** decide
   whether these are construction restrictions (then model) or roster/campaign
   rules (then exclude with a ruling). Today they are unimplemented and their
   status is a product decision, not a code gap.
2. **Legacy phrase branch vs metadata (G2/G3):** decide between extending
   `buildRestriction`'s exact-phrase list and publishing `forbids` tokens. The
   canonical, already-established route is a `profile.equipment-restrictions`
   binding; extending the prose list would keep the wording coupling.
3. **Per-item qualifier contract (G1):** the largest group needs one agreed
   vocabulary (list `applies_to`, a qualifier field on `equipment_entry`, or a
   `forbids` token) before the shared decision can refuse non-qualifying buyers
   consistently in both products.

## 6. Recommended next implementation groups

1. **Bands with reachable armour/missile (G2/G3/G4)** — smallest, highest
   leverage: add `profile.equipment-restrictions` / `active-weapon-restrictions`
   bindings to the five pirate/raider bands; the pattern and consumers already
   exist.
2. **Equipment-note bearer qualifiers (G1)** — the largest group; depends on the
   decision in §5.3 and should ship with the shared module plus both consumer
   regressions.
3. **Hireling references and dangling items (G5/G6)** under the existing
   F036–F038 ownership.
4. **Catalogue rule bindings (G7)** with the item/mechanic lot.
5. **Decisions for G8** before any code.

## 7. Evidence, method and closure

- Checks actually run: manifest/hash verification; full re-extraction of the 507
  ids through the maintained export (507/507 hash match); static inspection of
  `packages/typescript/domain/eligibility/index.ts`
  (`profileEquipmentItems`, `profileEquipment`, `profileFactsProjection`,
  `buildRestriction`, `equipmentIssue`, `equipmentSetIssues`,
  `warriorEquipmentRestriction`), `mordheim_knowledge` loaders, the editorial
  schemas and the relevant band YAML. No behavioural suite was executed for
  individual rows; `validation_evidence` in the CSV states this per row.
- **Concurrent drift**: the working tree carried many modified files owned by
  other lots (per `git status`); the dispatch directory itself is untracked. The
  frozen input and every re-extracted source hash were re-validated at closure
  and are unchanged, so no result is marked stale. No shared file was written.
- Closure: `B-construction-results.csv` has 507 unique ids equal to the
  assignment, the exact dispatched columns, and one status from the required
  vocabulary per row.
