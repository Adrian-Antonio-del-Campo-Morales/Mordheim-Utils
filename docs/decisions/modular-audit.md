# Modular source audit — audit record and backlog

Development record of the 2026-09-05 modular source audit (findings M01–M28).
The original report is historical evidence in
`outputs/modular-audit-2026-09-05/` and is not rewritten. Work targets the
modular engine; candidate (NumPy/native) work is deferred to the porting
backlog below.

**Permanent design decisions that came out of this audit live in
[Design rulings](design-rulings.md)** — that page survives when this audit is
retired; this page documents the audit itself: findings, status, methodology
and remaining acceptance work. Research sources per finding (mordheimer.net
clauses, editorial comparisons) were consulted during the audit; the durable
outcome of each comparison is a ruling in the design page or a correction in
the regression file.

Scope update at the user's request (2026-09-05): finish the modular engine;
document NumPy and native work without continuing their implementation. The
basic critical table is active; optional weapon-family charts are not enabled.

## Methodology

For each finding, compare the complete source clause and exceptions,
incorporated KB, actual consumers, and recorded `question`/`ruling`/
`interpretation`. Preserve explicit editorial decisions. An interpretation
describing existing code is not by itself evidence that the code matches the
source. Expected results must be written independently before repairs.
Existing tests may need corrections where their expectations embody the
audited error; never refresh source digests without reviewing the
corresponding text and evidence.

## Per-finding status (M01–M28)

Status meanings:

- **Corrected**: the original defect is repaired with passing focused
  evidence. Does not certify every possible interaction or either candidate
  engine.
- **Interpreted** (documented interpretation): implementation follows an
  explicitly recorded source/model interpretation (recorded in
  [Design rulings](design-rulings.md)). Not an original FAQ or an unresolved
  request for user approval; remaining evidence is stated separately.
- **Pending validation**: implementation exists, but a concrete part of the
  original acceptance evidence remains open. Do not mark the finding closed.

The principal regression file is
[`tests/combat/modular/test_source_corrections.py`](../../tests/combat/modular/test_source_corrections.py).
Test names refer to that file unless another location is given.

| ID | Original issue | Status | Evidence / remaining acceptance work |
| --- | --- | --- | --- |
| M01 | Missing basic critical result table | Corrected | All six results, armour and Injury bands, Web of Steel, and migrated critical/resource semantic cases. Optional family charts remain disabled. |
| M02 | Same attacker automatically finishes a newly stunned target | Corrected | `test_stun_from_first_hit_does_not_auto_finish_on_second`; pool retains initial status independently of later injuries. |
| M03 | Highest six exposes a lower hit to parry | Corrected | `test_highest_natural_six_does_not_offer_a_lower_hit_to_parry`; existing parry semantic controls retained. |
| M04 | First round erases Strike Last | Corrected | `test_m04_strike_last_controls_whole_round_order`: both charge directions and both Initiative relationships; Strongman controls also pass. |
| M05 | Charged spear receives an extra priority tier | Corrected | `test_m05_spear_order_uses_initiative_in_both_charge_directions`: both charge directions, Initiative relationships and later-round control. |
| M06 | Initialized Initiative lost by round ordering | Corrected | `test_round_consumes_initialized_initiative`; state value reaches priority without duplicating static modifiers. |
| M07 | Recovery lacks active-player ownership | Interpreted | One iteration represents one player-turn combat phase. `test_m07_four_player_turns_preserve_recovery_fire_and_paralysis_ownership` verifies four alternating turns with exact dice and no unused rolls. |
| M08 | Pistol penetration counted twice | Corrected | Ordinary/duelling pistol total modifier tests and migrated fixed-Strength semantic controls. |
| M09 | Brace treated as ordinary extra weapon | Corrected | `test_m09_pistol_allocation_and_next_turn_fallback`: A1/A2/A3, single pistol, pistol/dagger and brace; next turn verifies surviving dagger or fist fallback. |
| M10 | Rapier Strength and truncated Barrage | Corrected | Three failed continuations followed by a fourth miss/save/critical verify cumulative 6+ cap and full resolution. Explicit decline consumes no additional die. |
| M11 | Missing claw/two-axe parry rerolls | Corrected | `test_equipment_parry_rerolls_do_not_require_a_skill` and existing equipment/skill controls. |
| M12 | Missing whip properties | Corrected | Charged bonus has separate timing; ordinary attacks retain priority; two-whip/Frenzy case grants one bonus. Beastlash now denies parry. |
| M13 | Missing Brass Knuckles / Cat penalties | Corrected | `test_weapon_disadvantages_reach_the_consumers`; compiled Initiative and enemy armour penalties restored. |
| M14 | Dark Elf Blade effects applied to ordinary Injury | Corrected | Separate stun boundary and critical-table bonus; no unconditional Injury bonus. |
| M15 | Lotus cannot attempt a critical | Corrected | Guaranteed wound survives failed attempt; accepted/declined attempts and immunity/resource semantic cases pass. |
| M16 | Ball and Chain lacks D3 damage | Corrected | All D3 faces against multi-Wound targets; critical combination uses maximum, not multiplication. |
| M17 | Disease Dagger lacks infection | Interpreted | Immediate hit-triggered test and separate wound implemented; general armour saves apply. All six Toughness-test faces and Undead/Possessed immunity pass exact-dice acceptance tests. |
| M18 | Kusara penalty expires without effect | Interpreted | Original Spanish source recovered; minimum one Attack, selected weapon, upcoming reply. A1-to-zero expectation withdrawn. Selected-hand reply tests pass. |
| M19 | WS0 requires a 2+ roll | Corrected | `test_ws_zero_is_automatic_without_a_hit_die`; automatic hits carry no fabricated natural six. |
| M20 | Natural six passes characteristic tests | Corrected | Values below/at/above six covered; ordinary tests default to six failing. Opposed tests retain their distinct contract. |
| M21 | Spittle test occurs after damage | Corrected | Immediate test survives a failed wound and successful armour/ward saves. |
| M22 | Paralysis grants knockdown elimination | Corrected | Multi-Wound paralysis regression preserves ordinary damage. |
| M23 | Force of Will follows discarded remaining hits | Interpreted | Immediate rescue chosen from the source trigger. `test_force_of_will_rescues_before_the_remaining_hit` passes. |
| M24 | Fire invokes stunned melee finisher | Corrected | `test_fire_cannot_auto_finish_a_stunned_victim`; fire declares incidental damage and requires wound resolution. |
| M25 | Sword Breaker lacks Trap Blade | Interpreted | Break roll and persistent fallback implemented; failed parry, trap roll 3, unarmed exemption and surviving off-hand cases pass. |
| M26 | Frenzy doubles ordinary fist cap | Corrected | Final ordinary cap remains one; named unarmed exemptions and off-hand Frenzy rules remain separate. |
| M27 | Serpent Staff power omitted as intentional | Corrected | Full text restored: active mode verifies WS4/S4, priority, one attack and no parry; explicit-decline sequence retains three normal attacks. |
| M28 | Untiring restores magically denied armour | Corrected | Magical denial, nonmagical denial, and ordinary magical attacks covered separately. |

**Closure boundary:** all 28 original defects have implemented corrections and
passing focused evidence — **23 corrected**, **5 with documented
interpretations** (M07, M17, M18, M23, M25). No unresolved request for a
ruling remains in this list. L4 coverage completeness and a full modular
engine-code mutation certificate remain pending; 96 % line coverage must not
be presented as full engine certification. Candidate certification remains
deferred. Final joint validation: **3995 passed** (modular, phases,
structural, architecture, semantic verification); `validate` structural
completeness with **531** default profiles compiling.

## Additional findings (A01–A07)

Discovered while implementing the original audit; recorded separately without
changing the original finding IDs. All corrected; evidence in the same
regression file unless noted.

| ID | Additional issue | Evidence |
| --- | --- | --- |
| A01 | Broadsword Strongman exception was missed because it is not two-handed. | `test_broadsword_strongman_exception_does_not_require_two_hands`. Source explicitly grants the exception. |
| A02 | Disease Dagger secondary damage reporting could lose infection damage or repeat acid reactions. | Lethal infection and combined infection/dagger regressions verify aggregate damage and exactly-once retaliation. |
| A03 | Fire delayed Force of Will rescue until after later phase events. | Successful/failed rescue regressions fail before the fix and pass afterward. |
| A04 | Burning inherited the opponent's offensive bonuses, armour denial and multiple damage. | `test_burning_hit_does_not_inherit_opponents_offensive_effects`. |
| A05 | Kusara's minimum applied separately to Whipcrack and ordinary events. | A1/A3 and selected off-hand whip cases verify phase-wide minimum and one-time suppression. |
| A06 | Spines and other synthetic hits could invoke the deliberate stunned finisher. | Spines regression and explicit incidental-hit flags for Spines, acid blood and Black Hunger backlash. Does not certify every synthetic-effect interaction. |
| A07 | Guaranteed Lotus wound was treated as a failed wound for rerolls. | Dark Steel/Sure Strike regressions retain the guaranteed wound without an extra failure reroll. |

## NumPy/native porting backlog

Existing candidate edits are retained as partial work, not certified ports.
The NumPy checkpoint of 3733 passing cases predates subsequent modular
changes. Native changes have not been built or behaviourally validated
(existing native binaries are stale; the successful Cython syntax check
predates the latest Spittle changes). Neither checkpoint certifies completion.

| Area | NumPy | Native |
| --- | --- | --- |
| Basic criticals | Verify all six results, phase limit, cancellation, maximum weapon/critical damage and independent Injury dice. | Complete/build the partial table and D3 port; test cancellation restoring eligibility and wound rerolls. |
| Automatic hits / finishers | Preserve pre-sequence condition through Spines and split events; no synthetic natural six. | Remove same-pool newly-stunned auto-removal; implement WS0 without dice; separate incidental hits from melee finishing. |
| Parry | Recheck highest-six capacity with unparryable attacks and charms. | Highest six must not offer a lower hit; preserve named exceptions and claw/two-axe rerolls. |
| Player turns | Verify active-player recovery, fire and paralysis with both fighters resetting phase resources. | Replace simultaneous recovery with alternating ownership; retain the documented Black Hunger convention. |
| Pistols / Trap Blade | Connect broken-hand state to equipment projection per row; implement breaking and original hand identity. | Port brace limits, spent-pistol fallback and persistent broken hands before priority/parry/counts. |
| Rapier | Route Barrage decisions through actual attack keys; test decline and cumulative penalties. | Replace single extra attack with optional iterative continuation through the complete pipeline. |
| Whipcrack | Split charged bonus into its own Strike First event; ordinary attacks retain priority, one bonus across hands. | Port the same event model and all whip tags; test Frenzy, two whips and staff replacement. |
| Weapon fields | Verify corrected KB consumers, magical armour denial, D3 damage and table bonuses. | Recheck shifted field indexes and all consumers, including armour denial and table bonuses. |
| Lotus / Spittle | Route optional Lotus decisions at runtime keys; guaranteed wounds do not reroll as failures. | Finish Lotus decline and immediate Spittle tests with correct recovery and dice consumption. |
| Disease Dagger | Implement immediate infection, immunity, separate wound/save and exactly-once reactions. | Port the same sequence and aggregate damage reporting, including infection killing before the dagger wound. |
| Kusara | Verify selected-hand counters and allocation across split events; keep minimum one attack. | Add selected-hand state, apply before reply and expire at the documented boundary. |
| Characteristic tests | Recheck genuine tests: natural six fails; opposed rolls differ. | Review callers still passing `six_fails=0`; do not change opposed/Leadership rolls indiscriminately. |
| Force of Will | Verify immediate rescue on relevant damage paths, including fire before later events, sustain and second removal. | Port immediate rescue, cumulative sustain penalty and spent resource; test success and failure. |
| Fist / Serpent Staff | Verify final fist cap and optional WS4/S4 single attack without parry or extra pools. | Port final cap and staff replacement before priority/count generation. |

### Shared contracts and required evidence

- `EffectSet.damage_die_sides` changed the native layout from 54 to 55 fields.
  Preserve the ABI guard and rebuild against matching fields before execution.
- Consume compiled unarmed fallback and original hand slots; no runtime KB
  reads.
- Persist broken/hampered hands and secondary-wound reaction accounting across
  events. Local operator projection alone does not prove runtime equivalence.
- Reject exhausted/unused dice and decisions. Individual NumPy attack replay
  was tightened; pool replay still needs review. Never invent missing sixes.
- Use source-derived expectations from modular regressions and semantic specs,
  then L0/L1, multi-event/multi-turn L2 and L4 coverage/mutations before
  statistics. Native requires observable deterministic behaviour, not only a
  successful build.
- Three earlier pending Averlander promoted-halfling cases depend on the Lad's
  Got Talent construction model. Keep them separately pending without
  weakening parity completeness checks.

## Validation checkpoints

Checkpoints preserved to distinguish them from the final run:

- The migrated existing semantic corpus reached **617/617**, zero errors and
  zero pending obligations at its checkpoint. Further stateful regression
  cases were added afterward.
- Eleven baseline invalidated fingerprints were proved against `681dc40`: the
  rules, profiles, band and equipment data were identical except for explicit
  `price_override` fields introduced in `5bffcca`. Only those proven
  fingerprints were refreshed; evidence is in `reviewed-context-digests.json`
  in the audit output.
- Parity replay of individual attack cases previously invented maximum dice
  when the supplied sequence ended and ignored unused dice. It now rejects
  both for attack replay (finite enumeration permits unused suffixes, but not
  exhaustion). This exposed omitted Lotus decisions, spurious helmet rolls and
  omitted injury choices; the NumPy consumers were corrected.
- NumPy parity reached 3733 passing cases and zero divergences at that
  checkpoint. Three pre-existing pending cases concern Averlander promoted
  halflings and the missing Lad's Got Talent construction model; they are
  unrelated to M01–M28 and remain explicitly pending.
- Subsequent targeted tests reached 110 passing modular tests and 158 passing
  modular/NumPy tests at their respective checkpoints. Rerun after later
  edits.
- Latest gates before the additional fire isolation: 112 modular tests and 64
  structural/architecture/phase tests passed; semantic verification reports
  `structural_complete` and `semantic_complete`. The structural snapshot
  changed 54 to 55 specifically for the new consumed `damage_die_sides`
  field, with its consumer verified in `modular/attacks.py` — not a blanket
  snapshot refresh.
- Earlier checkpoints: 180 passed before the M04/M05/M07 acceptance additions;
  3888 passed / 1 failed (legacy Rapier dice key, not a rule change; 84 passed
  after that fix); 96 % line coverage (982 statements, 38 missed) — measured
  line coverage, not an L4 completeness or mutation certificate.
