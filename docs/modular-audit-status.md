# Status of original modular audit findings

Scope: the 28 findings in `outputs/modular-audit-2026-09-05/findings.json`.
The original report is historical evidence and is not rewritten. Implementation
work targets the modular engine. [Candidate ports](modular-engine-porting.md)
and [additional findings](modular-additional-findings.md) are separate backlogs.

Status meanings:

- **Corrected**: the original defect is repaired with passing focused evidence.
  This does not certify every possible interaction or either candidate engine.
- **Pending validation**: implementation exists, but a concrete part of the
  original acceptance evidence remains open. Do not mark the finding closed.
- **Documented interpretation**: implementation follows an explicitly recorded
  source/model interpretation. This is not an original FAQ or an unresolved
  request for user approval. Remaining evidence is stated separately.

All source comparisons and editorial decisions are in the
[research ledger](modular-remediation.md). The principal regression file is
[test_source_corrections.py](../tests/combat/modular/test_source_corrections.py).
Test names below refer to that file unless another location is given.

| ID | Original issue | Status | Evidence / remaining acceptance work |
| --- | --- | --- | --- |
| M01 | Missing basic critical result table | Corrected | All six results, armour and Injury bands, Web of Steel, and migrated critical/resource semantic cases. Optional family charts remain disabled. |
| M02 | Same attacker automatically finishes a newly stunned target | Corrected | `test_stun_from_first_hit_does_not_auto_finish_on_second`; pool retains initial status independently of later injuries. |
| M03 | Highest six exposes a lower hit to parry | Corrected | `test_highest_natural_six_does_not_offer_a_lower_hit_to_parry`; existing parry semantic controls retained. |
| M04 | First round erases Strike Last | Corrected | `test_m04_strike_last_controls_whole_round_order`: both charge directions and both Initiative relationships; Strongman controls also pass. |
| M05 | Charged spear receives an extra priority tier | Corrected | `test_m05_spear_order_uses_initiative_in_both_charge_directions`: both charge directions, Initiative relationships and later-round control. |
| M06 | Initialized Initiative lost by round ordering | Corrected | `test_round_consumes_initialized_initiative`; state value reaches priority without duplicating static modifiers. |
| M07 | Recovery lacks active-player ownership | Documented interpretation | One iteration represents one player-turn combat phase. `test_m07_four_player_turns_preserve_recovery_fire_and_paralysis_ownership` verifies four alternating turns with exact dice and no unused rolls. Existing automatic Black Hunger policy is preserved. |
| M08 | Pistol penetration counted twice | Corrected | Ordinary/duelling pistol total modifier tests and migrated fixed-Strength semantic controls. |
| M09 | Brace treated as ordinary extra weapon | Corrected | `test_m09_pistol_allocation_and_next_turn_fallback`: A1/A2/A3, single pistol, pistol/dagger and brace. S4/T4 wound thresholds identify actual shots; next turn verifies surviving dagger or fist fallback. |
| M10 | Rapier Strength and truncated Barrage | Corrected | Three failed continuations followed by a fourth miss/save/critical verify cumulative 6+ cap and full resolution. Explicit decline consumes no additional die. Legacy Rapier tape uses the new Barrage key without changing expected miss behaviour. |
| M11 | Missing claw/two-axe parry rerolls | Corrected | `test_equipment_parry_rerolls_do_not_require_a_skill` and existing equipment/skill controls. |
| M12 | Missing whip properties | Corrected | Charged bonus has separate timing; ordinary attacks retain priority; two-whip/Frenzy case grants one bonus. Beastlash now denies parry. |
| M13 | Missing Brass Knuckles / Cat penalties | Corrected | `test_weapon_disadvantages_reach_the_consumers`; compiled Initiative and enemy armour penalties restored. |
| M14 | Dark Elf Blade effects applied to ordinary Injury | Corrected | Separate stun boundary and critical-table bonus; no unconditional Injury bonus. Critical semantic fixtures migrated. |
| M15 | Lotus cannot attempt a critical | Corrected | Guaranteed wound survives failed attempt; accepted/declined attempts and immunity/resource semantic cases pass. |
| M16 | Ball and Chain lacks D3 damage | Corrected | All D3 faces against multi-Wound targets; critical combination uses maximum, not multiplication. |
| M17 | Disease Dagger lacks infection | Documented interpretation | Immediate hit-triggered test and separate wound implemented. General armour saves apply without a weapon Strength modifier because no denial is specified. All six Toughness-test faces and Undead/Possessed immunity now pass exact-dice acceptance tests. |
| M18 | Kusara penalty expires without effect | Documented interpretation | Original Spanish source recovered: minimum one Attack, selected weapon, upcoming reply. A1-to-zero expectation in original audit is withdrawn. Selected-hand reply tests pass; see ledger for phase mapping. |
| M19 | WS0 requires a 2+ roll | Corrected | `test_ws_zero_is_automatic_without_a_hit_die`; automatic hits carry no fabricated natural six. |
| M20 | Natural six passes characteristic tests | Corrected | Values below/at/above six covered; ordinary tests default to six failing. Opposed tests retain their distinct contract. |
| M21 | Spittle test occurs after damage | Corrected | Immediate test survives a failed wound and successful armour/ward saves. Exact-dice tests verify the test precedes wounds and saves. |
| M22 | Paralysis grants knockdown elimination | Corrected | Multi-Wound paralysis regression preserves ordinary damage; automatic hits and inability to reply are distinct from knockdown finishing. |
| M23 | Force of Will follows discarded remaining hits | Documented interpretation | Immediate rescue chosen from the source trigger; remaining prepared hit can cause final second removal. `test_force_of_will_rescues_before_the_remaining_hit` passes. |
| M24 | Fire invokes stunned melee finisher | Corrected | `test_fire_cannot_auto_finish_a_stunned_victim`; fire declares incidental damage and requires wound resolution. |
| M25 | Sword Breaker lacks Trap Blade | Documented interpretation | Break roll and persistent fallback implemented. Already-rolled hits retain original weapons; subsequent phases use surviving equipment. Failed parry, trap roll 3, unarmed exemption, prepared remaining hit and surviving off-hand cases now pass. |
| M26 | Frenzy doubles ordinary fist cap | Corrected | Final ordinary cap remains one; named unarmed exemptions and off-hand Frenzy rules remain separate. |
| M27 | Serpent Staff power omitted as intentional | Corrected | Full text restored. Active mode verifies WS4/S4, priority, one attack and no parry. Explicit-decline sequence retains three normal attacks, user stats, ordinary priority and a successful parry. |
| M28 | Untiring restores magically denied armour | Corrected | Magical denial, nonmagical denial, and ordinary magical attacks covered separately. |

## Validation record

- Final joint run after all acceptance additions: **3995 passed in 192.91s**.
  Suites: modular, phases, structural, architecture and semantic verification.
  Evidence: `outputs/modular-audit-2026-09-05/original-findings-validation.txt`.
- Final `validate`: structural completeness and **531** default profiles compile.
  Evidence: `outputs/modular-audit-2026-09-05/original-findings-validate.txt`.

Earlier checkpoints (retained to distinguish them from the final run):

- Last combined modular/phase/structure/architecture run: **180 passed**, before
  the subsequent M04/M05/M07 acceptance additions.
- Those additions pass: **12** whole-round priority cases and **2** four-turn
  ownership cases.
- Extended modular plus semantic run: **3888 passed, 1 failed**. The failure was
  the legacy Rapier dice key, not a changed expected rule result. After updating
  that key, the failing test and source regression file reached **84 passed**.
- Coverage from the extended run: **96%**, 982 statements, 38 missed. This is
  measured line coverage, not a passing L4 completeness or mutation certificate.
- Earlier `verify --json` reports `structural_complete` and `semantic_complete`.
  Historical corpus success does not close acceptance gaps listed above.

## Current closure boundary

All 28 original defects now have implemented corrections and passing focused
evidence: **23 corrected**, **5 with documented interpretations** (M07, M17,
M18, M23, M25). There is no unresolved request for a ruling in this list.
The M18 original expectation is explicitly corrected rather than reproduced.

Final joint validation passes after the acceptance additions. L4 coverage
completeness and a full modular engine-code mutation certificate remain pending;
96% coverage must not be presented as full engine certification. Candidate
certification remains deferred. Additional findings do not enlarge this queue.
