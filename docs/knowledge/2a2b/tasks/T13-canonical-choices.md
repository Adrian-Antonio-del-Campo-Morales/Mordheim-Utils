# L05 — Canonical choices, grants and supplied equipment

Implemented 2026-10-03 on branch `2A2B`, entry HEAD `1b7f7cf` plus the retained
working tree. This delivers construction routes, not completion of every
selected effect or certification of T13.2/T14. No agent, commit or push.

## Governing material

- [Remaining plan, L05](T13-T15-remaining-plan.md#executable-lot-list--2026-10-02),
  [original implementation contract](T13-implementation-plan.md),
  [origin ledger](T13-obligations.csv) and [follow-up register](T13-execution-follow-ups.md).
- [Shared construction contract and completed consumer migration](../../../reference/eligibility.md).
  Eligibility has one TypeScript owner; Python folds effects and transports facts.
- [F035 reconciliation](T13-shared-eligibility-reconciliation.md),
  [automatic grant evidence](T13-automatic-grants.md),
  [selectable/equipment evidence](T13-selectable-equipment.md),
  [L04 Shifty](T13-shifty.md#l04-canonical-activation--2026-10-03).
- [Karak Azgal](https://broheim.net/downloads/campaigns/karakazgal/Karak%20Azgal.pdf),
  Elf/Barbarian/Noble/Dwarf tables, printed pages 21–23; canonical table bindings
  and catalogue prose identify the individual members without a source-URL heuristic.
- [Halflings](https://mordheimer.net/docs/warbands/grade-2a-warbands/halflings),
  special skills, and [Snotlings](https://mordheimer.net/docs/warbands/grade-2a-warbands/snotlings),
  Runts / Teeny Hands: promotion supplies a Hero recipient; owned holstered
  weapons are distinct from simultaneously used weapons.
- [Outlaws source](https://mordheimer.net/docs/warbands/grade-2a-warbands/outlaws-of-stirwood-forest-redux):
  all profiles retain the one-missile limit; the Cleric is exempt only from
  carrying a compulsory bow.
- [Sea Ghosts original PDF](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Sea%20Ghosts.pdf),
  printed page 187: Shadow Dances belong to the Feast-Master, who learns one
  instead of a skill. Wayfinder was the wrong positive fixture in T13.2d.
- [Araby original PDF](https://broheim.net/downloads/warbands/supplement/sartosa/Araby%20Smugglers.pdf),
  Pirate Special skills / Pious Fury, and
  [Protectorate transcription](https://mordheimer.net/docs/warbands/grade-2a-warbands/protectorate-of-sigmar),
  the two expressly Warrior-Priest-only skills. The generic Protectorate access
  ambiguity is retained below; no Special category was invented for every Hero.

## Implemented paths

### Named skills: membership, offering, selection, compilation

`profileSkillLists` now supplies the published bounded tables to both
`catalogueSkillChoices` and the specialized profile-selection decision. The
legacy source-URL fallback remains only for profiles without a published table.
The shared neutral projection includes the category of the binding, including
empty published lists, so missing members remain an explicit knowledge gap.

Combat Lab presents named Special members with their actual text. Splitting UI
IDs preserves those members as ordinary `skill_ids`; it does not silently drop
them because `skills(None)` lacks their profile-specific table. Legality and
runtime availability are separate. A legal missing mechanic raises
`named skills have no executable duel mechanic: [...]`.

| Profile | Executable members | Visible but without a duel mechanic; behavior owner |
| --- | --- | --- |
| Barbarian | Hard to Kill; Ferocious Charge | Instinctive Warrior — L06 parry |
| Dwarf | Ferocious Charge; Monster Slayer; Berserker | Magic Resistant — battle-spell clause remains outside the declared product |
| Elf | None | Fey — battle-spell clause; Chosen of the White Tower — L06 parry; Fey Quickness — L07 save |
| Imperial Noble | None | Trading Flair — campaign clause; Taunt — L09/L10 challenge/test |

There are 12 table contributions, five executable contributions using four
existing mechanics. This lot adds no combat operator. Recipient controls reject
other table members, and each executable member reaches the compiled tags once.
The Slayer route is preserved. Knights' Feats still needs source-correct named
members and its L06/L07/L08/L14 behaviors; an empty table grants no whole catalogue.

### Supplied local promotions and active weapon positions

`FighterBuild.variant_ids=("promotion.hero",)` declares the result of a promotion
for a local participant. Shared `configuredProfile` changes a copy of the
starting Henchman row to Hero; the canonical profile and characteristics stay
unchanged. This does not roll an advance, authorize campaign promotion, choose
ordinary advance categories or persist a campaign member.

The new `applies_to.profile_types` filter is conjunctive with profile IDs in
automatic grants, offerings and selected-rule validation. Its current schema
vocabulary is the two exercised recipient classes, Hero and Henchman.

Shifty's four starting Heroes remain legal. Configured promoted Halfling Scouts
and Warriors now select, compile and execute it through actual modular rounds;
unpromoted versions and non-Halfling Piggies/Ogre controls remain excluded.
The catalogue accepts the same supplied variants for skill offering.

Teeny Hands applies only to Runt Henchmen. The existing profile binding now
contains `max_active_one_handed_weapons: 1` alongside the armour prohibition.
The shared module counts active weapon positions, including two copies of the
same weapon. Holstered possessions do not count. A supplied Hero type removes
the entire rule, including its armour prohibition; ordinary list access remains.
Canonical mechanic hand facts are transported for slot decisions. Neither
Python nor the UI implements a second Runt restriction table.

The former placeholder origin
`unimplemented.snotlings-web.runts.teeny-hands` is discharged by the source-linked
`profile.equipment-restrictions` spec and configured recipient filter. Removing
that placeholder is a binding promotion, not deletion of its admitted clause.

### Complete carried kit versus active duel loadout

The shared profile projection includes both declared item IDs and their
implemented mechanic aliases. A bow without a duel mechanic can therefore be
legal carried equipment without becoming an executable attack.

`FighterBuild.owned_item_ids=None` leaves the complete kit unknown. `()` supplies
an explicitly empty kit; a tuple supplies the owned items. When supplied,
`compile_fighter` invokes maintained final `validateConstruction` through
`configuration_context` and the installed catalogue. Owned items are never
folded into active weapon effects. Legacy unspecified-kit builds remain usable
and are not evidence that the complete kit meets mandatory requirements.

`CombatCatalogue.validate_configuration(choice, possession=..., slots=...)`
returns all shared issues/reports over the same transport projection. Ordinary
blocking versus informational policy stays in the shared module. Actual visible
editing of these new facts remains L18; no GUI workflow is certified here.

Outlaws' positive bow, missing bow, multiple missile weapons, crossbow refusal
and Cleric exception now have actual catalogue/transport/compiler witnesses.
The crossbow token is also tested independently of list exclusion so widening
access cannot hide a missing restriction. A final canonical control exposed an
existing shared bug: `exempt_profile_ids` skipped both the compulsory bow and
the missile limit. The decision now exempts only the compulsory requirement,
as the source and maintained parameter contract specify. Cleric zero/one/two-bow
cases prove the limit in the catalogue and compiler. The retained neutral
fixture for an exempt profile carrying two pistols now expects the count
refusal; it still expects no missing-bow refusal. This implements construction,
not shooting.

### Canonical access corrections and explicit gates

Seven pending origins have explicit source-backed recipients: four Sea Ghosts
dances target Feast-Master; Pious Fury targets Rais/Mates/Merchant; Utter
Determination and Rousing Sermon target Warrior Priest. They are offered but
still refuse executable selection with their published pending reason.
Q081 and the psychology/group operators remain gates for their actual effects.

Non-skill selectable choices now use shared `selectableRuleOptions`, including
profile ID and type filters. Strigoi Bloodline is offered as a configured ability
only to the Vampire, rather than to every profile or in the skill-only API.
Q095 and the individual Bloodline effects remain gated.

Unshakeable Faith retains the generic source condition “Heroes with access to
Special Skills”. The available transcription's skill table lacks a Special
column and does not establish that condition. The linked LOD3 PDF could not be
read by the web tool (size limit). No unverified all-Hero access is activated.
F018 routes that concrete source/access decision to L11 before Fear immunity
activation. The configured-ability route is not proof of Bloodline execution.

## Truthful markers and one effect route

The unreachable `SPECIAL_RULE_EFFECTS` Iron Sinews stats entry is removed.
Trollheim's source-specific selectable rule uses `skill.iron-sinews` once,
leaving base Strength unchanged and contributing exactly +1 effective Strength.
Mordheim's Iron Sinews is inside the separately gated Strigoi Bloodline clause;
no similarly named foreign rule is activated for that profile.

Eight unbound `LATER/YES` markers now say `implemented: NO`, with retained text
and explicit pending reasons. Related automatic traits remain intact.

| Canonical origins | Remaining behavior owner |
| --- | --- |
| Dwarf Slayer Cult: Hard to Kill; Hard Head | L07 injury conversion and mace/club exemptions |
| House Guard: Dueling Pride; Pikewall | L06/L08 enemy-Hero, charged and first-strike filters |
| Lords of the Marsh: Young Noble and Fimir Warrior Spiked Tail | L08 secondary owner-Strength+1 attacks |
| Underworld Alliance: One-upmanship | L06/L12 shared-combat provider condition |
| Watchmen: Private Sleuth Scryer | L09/Q104 optional close-combat rerolls; exploration remains excluded |

`validate_rule_runtime` rejects an implemented rule with no executable binding
regardless of aggregate scope. Bound `LATER/YES` records remain permitted:
they can carry a real bounded operator while their complete clause is pending.
Mixed bound/pending effects retain existing semantics. This is a narrow guard,
not a blanket prohibition of the LATER combination or a new audit framework.

Existing 2A/2B mirrors receive the same owned rule corrections. Two Dwarf Slayer
mirror aggregate scopes also become LATER to match their unbound effects and
canonical entries; unrelated mirror content is preserved.

## F028: individual unsupported equipment dispositions

None of these 17 items currently has an executable simulation mapping. The
accepted F035 classification (13 not sold; four rare, three lacking a price)
is preserved. Price omissions are campaign catalogue work, not permission to
invent acquisition or an equipment slot. `out_of_scope` data is not an exclusion
of the admitted local combat clauses.

| Item | Actual remaining owner and resume condition |
| --- | --- |
| `angel_wings` | L16/L14: Armen Abbas local identity and supplied glide/action facts |
| `arcane_candelabrum` | L16/L06/L09: specialist identity and brazier/relic composition; no lantern subsystem |
| `bear_of_the_hunt` | L17: summoned companion profile/attacks/control, then L18 choice |
| `corpse_liquor` | L06: natural-hit-six automatic wound/critical opportunity/poison composition, then L18 local coating |
| `great_eagle` | L17/L14: summoned profile and required flight facts |
| `great_stag` | L17/L08: summoned profile and charge contribution |
| `hunting_hounds` | L17: summoned profiles and actual local group ownership |
| `runic_attlas_plate_mail` | L07/L14: gromril, extra Wound and passage; spell immunity remains battle-magic boundary |
| `runic_builders_boots` | L14: supplied terrain/distance movement contract |
| `runic_eye_of_izril` | L07/L11: ward save and opponent-animal Frenzy; detection/exploration remain excluded |
| `runic_redbeards_belt_of_rage` | L11/L12/L14: persistent Frenzy, +1 Strength and forced local targets/actions |
| `runic_sword_of_snorri_elfbane` | L06: source-specific wound/critical/armour effects, then L18 item access |
| `sabre_toothed_tiger` | L17: source-backed summoned companion profile |
| `scuttling_hand` | L17/L11: local companion profile and immunity/save; hiding remains excluded |
| `wicker_man` | L17/L07/L11: construct participant, injury prevention and Zombie clauses |
| `wolf_pelt_cloak` | L16/L07: Wolf-Priest identity and source save kind; no borrowed armour mapping |
| `wolf_rat_mount` | L17/L08: rider/steed ownership and Strength-4 non-penetrating poisoned attacks |

Required product access follows each completed operator in L18. F028 stays open
for those explicit supported routes; this table replaces the blanket trading-post
premise, not their implementation. No missing item is silently enabled.

## Validation and remaining work

Evidence lives in `build/cache/t13-parallel/canonical-choices/`: entry hashes and
byte snapshots, focused/affected/TypeScript logs, exact semantic comparison,
source-pin transition, schema audit, publication and closing input check.
The maintained regression suites and semantic specs are the durable proof.

L05 does not port new stateful rules, waive historical source pins, refresh the
F057 parity expectation, write coverage budgets or modify Warband Manager UI.
F018's generic Protectorate source decision and F028's unsupported item routes
stay with the named behavior owners. Next functional lot: **L06**. Final counts
and check results are recorded below after the closing run.

### Closing results — 2026-10-03

- Focused new integration suite: **39 cases** (included in the affected run).
  Direct shared suite: seven cases; together with F017/F019/shared transport and
  F035 regressions, **82 TypeScript cases pass**, with typecheck and current bundle.
- Affected construction/application/Shifty/catalogue/schema/structural suites:
  **958 passed**. Additional catalogue and exact staging promotion: **56 passed**.
- New source-linked Teeny Hands specification: four cases and one detected
  isolated runtime fault. Only Shifty's reviewed source pin changes in the
  retained corpus; the historical 30 pins remain untouched. Authored executable
  cases increase **3786 → 3790**; F057's owning lot must use the current corpus.
- Fresh full verifier: structural complete, **1050 profiles compile**;
  **720 obligations, 570 verified, 150 pending**, with exactly the same 30
  historical source errors as L04 and no added error. The one newly verified
  obligation is Teeny Hands' profile binding. This is not an all-green semantic
  or parity certificate; inherited unclassified/pending work remains.
- Strict schema audit: **39 findings, zero hard/unjustified/stale**. Generator
  and its `--check` pass; documentation links pass. New schema vocabulary is
  exercised rather than introducing an unused enum allowance.
- Lot-owned diffs are whitespace-clean. Whole-tree `git diff --check` still
  reports retained trailing whitespace in the pre-existing Tk editor/native C
  changes, outside this lot. Those input hashes are preserved.

Entry evidence froze 70 candidate files and 1711 input hashes. The existing
restriction wrapper's supplemental entry bytes were reconstructed by reversing
only L05's three transport edits and matched its frozen entry hash; no live
restoration was performed. The old selectable matrix's four Sea Ghost positive
fixtures now use the source-backed Feast-Master. The closing check identifies
all attributable input changes, including a supplemental pre-edit capture of
the shared decision fixture, and preserves the remaining captured inputs,
HEAD, engine files, F057 parity test and coverage budget. No test manifest,
coverage budget, historical pin or generated file was hand-edited.

Final Cleric regression evidence: `cleric-before.txt` records the live invalid
two-missile acceptance before the repair. `cleric-focal.txt` passes all 60 new
and embedded shared cases; `typescript-cleric-final.txt`,
`affected-cleric-final.txt`, `typecheck-cleric.txt` and
`bundle-check-cleric.txt` record the final affected checks.
`verify-cleric-final.json` is the verifier after that shared correction.

### Reproduction from the repository root

Use the installed development environment. Rebuild the embedded bundle after
changing the maintained TypeScript source, then run the affected maintained
checks. `verify --json` currently exits 1 for the retained 30 historical pins;
compare identities rather than treating its nonzero exit as a new L05 failure.

```text
npm run build:eligibility
npm run check:eligibility
npm run typecheck --workspace campaign-web-core
npm run test --workspace campaign-web-core -- ../../tests/typescript/domain/canonical-choices.test.ts ../../tests/typescript/domain/band-rule-recipients.test.ts ../../tests/typescript/domain/silence-equipment.test.ts ../../tests/typescript/domain/shared-eligibility.test.ts ../../tests/typescript/domain/shared-construction-context.test.ts ../../tests/typescript/domain/construction-validation-transport.test.ts ../../tests/typescript/domain/t13-shared-eligibility-reconciliation.test.ts
python -X utf8 -m pytest tests/python/construction tests/python/application tests/python/combat/modular/test_shifty_activation.py tests/python/knowledge/test_catalogue_contract_regressions.py tests/python/knowledge/test_editorial_schemas.py tests/python/verification/test_structural.py -q
python -X utf8 tools/mordheim-utils.py verify --json
python -X utf8 tools/knowledge/audit_schema_strictness.py --json
python -X utf8 tools/knowledge/generate_knowledge_web.py --check
python -X utf8 -m pytest tests/python/architecture/test_documentation.py -q
```
