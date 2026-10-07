# T13 reconciliation audit — LOT A (construction)

Independent reconciliation of the frozen `A-construction.csv` assignment.
Read-only with respect to KB, code, registries, shared reviews, manifests and
assignment lists. Owns only `A-construction-results.csv` and this summary.

- Repository: `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`
- Branch / HEAD at audit: `2A2B` / `820d1499a0c9ff04fd42975d3de9d97bd62d585d`
- Working tree carried large uncommitted concurrent edits (KB, TS eligibility,
  Python construction/combat, docs) before this audit; none were touched.
- No `AGENTS.md` exists at the repository root or any scanned directory.

## Input verification

| Check | Result |
| --- | --- |
| `manifest.json` `A-construction` sha256 | `54f439bf41ba6b2a5f3af66bd845cdc3c11db33269bea65922270dd98fdbce2b` |
| `A-construction.csv` sha256 (measured) | `54f439bf41ba6b2a5f3af66bd845cdc3c11db33269bea65922270dd98fdbce2b` — **match** |
| `manifest.json` rows / measured data rows | 508 / 508 — **match** |
| Distinct ids / duplicate ids | 508 / 0 |

Every assigned id was located in the current KB YAML (both the
`source/<file>/@<locator>/unclassified` and the
`source/<file>/<rule.id>/unclassified` id shapes) and its raw effect text
re-hashed. **508/508 recomputed SHA-256 values equal the assigned
`effect_sha256`.** No source drift; no `stale_input` result.

## Method

1. Re-extracted each entry with the same locator grammar `audit_export.py`
   uses, recomputed the raw-text digest and compared it with the assignment.
2. Recomputed, per profile, the applicable canonical rules/bindings
   (`applicableProfileRules` / `applicableRules`) reading `runtime.effects[].binding`,
   and the whole-set limit/forbid tokens of `profile.equipment-restrictions`
   and `profile.active-weapon-restrictions`.
3. Traced each clause to its current consumer: the shared eligibility module
   (`packages/typescript/domain/eligibility/index.ts` — `equipmentIssue`,
   `profileFactsProjection`, `buildAccess`, and the legacy `buildRestriction`
   stage `profileSelections` prose matcher) reached through
   `mordheim_construction/eligibility.py` + `restrictions.py`
   `_validate_profile_selections`; the campaign market
   (`packages/typescript/domain/campaign/kernel/market.ts`) for trading-post
   entries; `resolveHirelingKit` for hirelings.
4. Ran read-only probes: `compile_fighter` for the 162 distinct
   (collection, band, profile) targets of the profile-restriction family, with
   a representative light/heavy armour (results recorded per row in
   `validation_evidence`); `pytest tests/python/construction/test_profile_bindings.py
   tests/python/construction/test_construction_variants.py` = **15 passed**;
   `pytest tests/python/construction/test_silence_equipment.py` = **7 passed,
   1 failed** (`test_transport_uses_the_callers_root_and_isolates_catalogues`:
   "hireling catalogue declares no rules" — pre-existing/environment, unrelated
   to this lot, not counted as evidence for any row).

Scratch tooling, raw signals and probes live under
`build/audit/reconciliation/A/` (`analyze.py`, `signals.py`, `probe.py`,
`classify.py`, `signals.json`, `probes.json`).

## Result counts

508 result rows, one per assigned id, exact assigned column order, UTF-8/LF.

| Family (source node) | n | covered | metadata_gap | partial | out_of_scope | source_blocked |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `profiles.yaml` `equipment_restrictions` | 175 | 34 | 109 | 23 | 9 | |
| `equipment-access.yaml` item `notes` | 176 | 50 | 122 | | 4 | |
| `trading-post.yaml` `restrictions[].note` | 132 | 16 | 32 | | 84 | |
| hireling `unresolved_references` | 20 | | 3 | | | 17 |
| hireling intrinsic rule | 4 | | 1 | | 3 | |
| `magic.yaml` lore note | 1 | 1 | | | | |
| **Total** | **508** | **101** | **267** | **23** | **100** | **17** |

`proposed_scope` revalidated: 391 `YES`, 100 `NO`, 17 `UNCLASSIFIED`.
No `connection_gap`, `implementation_missing` or `decision_required` rows were
reproduced in this lot: the gaps found are missing canonical facts, not an
existing fact disconnected from a consumer, and no assigned entry raised a new
unanswered specification question.

## Covered — current source-to-consumer evidence

- **Equipment equivalence notes (44 rows, `covered`).** `Hammer/Mace`,
  `Club/Mace`, `Cutlass/Sword`, `Scimitar/Sword`, `Cooking pot/Helmet`,
  `Cleaver (counts as axe)`, `Tenderiser (Hammer)`, `Pairing Knife (Dagger)`,
  … The named equivalence is realised by the item record's `mechanic_id`
  (`catalog/items/*` → `weapon.mace`/`weapon.cutlass`/`weapon.sword`/
  `defence.helmet`/`weapon.axe`/…), consumed by `catalogue.mappings` /
  `carriedItemFacts`.
- **List-access clauses (22 rows, `covered`).** `Uses the Cannon Fodder
  equipment list.`, `May use weapons and armour from the Dark Elf Equipment
  List…`, `A Thrall may be equipped from the Necrarch Hero Equipment List.`
  The canonical `profiles.yaml` `equipment_lists` already realise them through
  `profileEquipmentItems`.
- **Canonical prohibition tokens + legacy prose fallback (7 rows, `covered`).**
  `horned-hunters/priest-of-taal` `May never wear heavy armour (Strictures)` →
  `priest-of-taal--strictures` binds `profile.equipment-restrictions`
  `forbids: heavy-armour`; probe:
  `compile_fighter(... armour.heavy-armour)` → `heavy armour is forbidden …`.
  The `magic.yaml` lore-21 note (Priest of Taal) is the same structured fact.
- **Compiler contracts (5 rows, `covered`).** `Saurus can never use missile
  weapons` → `compiler.saurus-skill-prohibitions`; `May never use missile
  weapons, even if an Advance…` → `compiler.no-missile-weapons`; Dark Elf
  `may not use missile weapons` → the same contract.
- **Trading-post structured restrictions (16 rows, `covered`).** Restrictions
  with a published scope (`band_ids`/`groups`) or a `structure` block are
  evaluated by `market.ts` `marketAvailabilityIssueFor` / `scopeMatches`.
- **Hero-only list membership (10 rows, `covered`).** A `Heroes only` note on
  an entry whose list is declared only by hero profiles is satisfied by
  `profileEquipmentItems` (no henchman receives the offer).

## Actionable gaps

1. **Equipment-access bearer restrictions — 122 rows (`metadata_gap`).**
   `Heroes only`, `Halfling Cooks only`, `Ruffians and Enforcers only.`,
   `Estalians only`, `Dwarf Troll Slayer only.`, `Rare N; Clan Skryre only`, …
   The item entry carries the bearer clause only as prose; `equipmentIssue`
   offers the item to every declared user of the list
   (`equipment-access.yaml` → `profiles.yaml equipment_lists`). No structured
   recipient fact exists at the equipment-access level.
   *Target:* item access / list scope, reusing the shared decision.
2. **Profile equipment prohibitions with no structured fact — 109 rows
   (`metadata_gap`) + 23 rows (`partial`).**   The KB keeps the clause as
   `profiles.yaml` prose only; no applicable special rule binds
   `profile.equipment-restrictions`. 146 of the 175 entries are not matched by
   the legacy prose patterns at all (notably
   `"May not wear armour."`, not in the `index.ts` `buildRestriction` list).
   The 23 partials are compound clauses (e.g. *"never use weapons **or**
   armour"*) where only the armour token is interpreted. **Executed probe:**
   `bretonnian-buccaneers-sar/captain` with light armour is **ACCEPTED** today,
   and for most profiles the refusal comes from equipment *access*, not from
   the restriction.
   *Target:* canonical `profile.equipment-restrictions` binding / item access.
3. **Trading-post note-only conditions — 32 rows (`metadata_gap`).**
   `condition` without `band_ids`/`groups`/`structure` (and the 14 `profile_only`
   notes) are refused by the market with `market_condition_unstructured`; the
   printed clause is surfaced but not decided.
   *Target:* publish the scope/`structure`; owner of `T13-F028`.
4. **Hireling intrinsic clauses / unresolved references — 4 + 20 rows.**
   `Johann may take Crimson Shade before a battle`, `Rides a Giant Wolf`,
   `Uses source cavalry rule`, plus 20 KB-recorded `unresolved_references`
   (equipment mappings, companion/alternate profiles, skills, patron branches).
   17 references carry no resolvable target (`source_blocked`); 3 name a target
   (`mechanic.mesmerising-dance`, `mechanic.savage-fury`,
   `skill.art-of-silent-death`) but the mapping is unreconciled.
   *Target:* `T13-F036` canonical hireling construction route.
5. **Equipment equivalences not realised — 4 rows (`metadata_gap`).**
   `Counts as a Halberd` (`shovel`), `Pitchfork (counts as Trident)`,
   `Kitchenware (counts as throwing stars)`, plus one item whose printed
   equivalence has no implemented mechanic (item record `mechanic_id: null`).
   *Target:* canonical item record/mechanic.

## Blockers

- **`T13-F036`** (hireling canonical construction route) blocks any claim over
  the 24 hireling rows.
- **`T13-F028`** (trading-post-only equipment) owns the 32 trading note-only
  conditions.
- **`T13-F041`** (restriction presentation after structured deduplication)
  remains relevant to the 132 profile rows whose canonical structured rule has
  not been authored yet.
- **No source blockers beyond the recorded KB `unresolved_references`**; no
  ambiguous full source text had to be left `UNCLASSIFIED` for interpretation
  reasons.

## Discrepancy with the reviewed scope (recorded, not rewritten)

All 508 entries were reviewed as `scope=YES, category=construction`. On the
actual clauses this audit finds: 100 entries are `out_of_scope` for the Combat
Lab 1v1 duel construction boundary — 84 trading-post notes that are pure
availability/acquisition (`availability.kind: not_sold` and rare-market
clauses, owned by the campaign market, excluded by "do not treat
prices/acquisition as duel mechanics"), 9 profile mount/casting clauses, 4
price-only equipment notes, 3 hireling acquisition/mount clauses. The
construction-relevant clause of the remaining mixed entries is the *named
recipient/access*, which stays `YES`. The reviewed reason text for the trading
family ("Named bearer/type restriction affects equipment eligibility") is
consistent with this split; the availability/acquisition subset is the part
this audit routes back to the campaign product.

## Concurrent drift / closure

- Assignment and manifest hashes re-checked at closure: unchanged.
- The KB source files backing every one of the 508 rows were read after the
  audit started; all digests matched the assignment, so no row is invalidated
  by concurrent KB edits at closure time.
- Note the open T13 follow-up `T13-F057` (coverage-budget/parity gate) and the
  uncommitted concurrent edits visible in `git status`: they do not change the
  canonical facts cited here, but a later KB edit to a `profiles.yaml`/
  `equipment-access.yaml`/`trading-post.yaml` entry would invalidate that row's
  hash and require re-review.

## Deliverables

- `A-construction-results.csv` — 508 rows, one per assigned id.
- `A-construction-summary.md` — this file.
