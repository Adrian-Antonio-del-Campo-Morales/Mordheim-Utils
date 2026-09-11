# Web parity coverage map

Short index of the desktop → web test ports completed for the campaign/post-battle
workflows. Each row names the web test file, the web seam it exercises, and the
desktop Python source it was ported from.

- Scope: application/domain workflow seams (no React, no service).
- Total: 20 files, 146 tests, all green; TypeScript core suite 526/526 green.
- Baseline reference: `INTEGRATION_BASELINE.md`.
- "No dedicated desktop test" means the web test was grounded in the desktop
  implementation (`post_battle_engine.py`, `controller.py` or `domain/models.py`)
  rather than a named `tests/campaign/` function.

| Web test file | Web seam(s) | Desktop source |
|---|---|---|
| `domain/campaign/injury_sequence.test.ts` | `resolveSoldToPits`, `resolvePrisoner`, `applyInjuryOutcome`, `resolveInjuryTableFollowUp` | `tests/campaign/test_injury_sequence_matrix.py` (pit-loss, captive, injury subtable, follow-up id uniqueness) |
| `application/campaign/features/injuries/injuries-workflow.test.ts` | `recordFollowUp`, `resolveFollowUp` | `tests/campaign/test_injury_sequence_matrix.py` (follow-up id scheme) |
| `application/campaign/features/injuries/injury-decisions-workflow.test.ts` | `resolveHatred`, `resolveEyeInjury` | `tests/campaign/test_post_battle_engine.py` (`test_bitter_enmity_records_the_selected_target`); `resolve_lost_eye` impl (no dedicated test) |
| `application/campaign/features/recruitment/recruitment-workflow.test.ts` | `recruitGroupMember`, `dismissRecruit`, `recruitBandProfile`, `applyVeteranPool` | `tests/campaign/test_post_battle_engine.py`, `test_extended_audit_regressions.py`, `test_economy_sequence_matrix.py`, `test_campaign_sequence_matrix.py` |
| `application/campaign/features/advances/promotion-workflow.test.ts` | `promoteHenchman`, `setPromotionSkillTables`, `resolveAdvanceRoll`, `commitAdvanceChoice` | `tests/campaign/test_post_battle_advancements.py` (`promote_henchman`, `set_promotion_skill_tables`, `resolve_pending_advance`, `reroll_exclude_promotion`) |
| `application/campaign/features/advances/experience-workflow.test.ts` | `experienceAwards`, `applyBattleExperience` | `tests/campaign/test_post_battle_advancements.py`, `test_extended_audit_regressions.py` (`apply_battle_experience`, `sync_pending_advances`) |
| `application/campaign/features/advances/manual-skill-workflow.test.ts` | `setManualSkill` | `controller.py` `set_manual_skill` (no dedicated test) |
| `application/campaign/features/advances/advance-commit-workflow.test.ts` | `commitAdvanceChoice`, `resolveAdvanceRoll` | `tests/campaign/test_post_battle_advancements.py` (`commit_pending_advance` choose_skill/generate_spell/duplicate_spell; roll-11 options) |
| `application/campaign/features/advances/racial-max-workflow.test.ts` | `resolveAdvanceRoll` → `applyCharacteristic` | `tests/campaign/test_post_battle_advancements.py` (`test_racial_maximum_blocks_further_increases`) |
| `application/campaign/features/review/finalize-post-battle-workflow.test.ts` | `finalizePostBattle` | `tests/campaign/test_post_battle_engine.py` (projections + commit gates) |
| `application/campaign/features/review/follow-up-acknowledgement-workflow.test.ts` | `acknowledgeFollowUp`, `canAcknowledgeFollowUp`, `followUpNeedsResolution` | `mordheim_campaign/domain/models.py` (`acknowledge`, `is_acknowledged`, `unacknowledged_follow_ups`) — no dedicated test |
| `application/campaign/features/exploration/exploration-followup-workflow.test.ts` | `continueExploration` (Returning a Favour free hire) | `tests/campaign/test_post_battle_engine.py` (`test_returning_a_favour_adds_the_selected_hired_sword_for_free`) |
| `application/campaign/features/exploration/scenario-followups-workflow.test.ts` | `resolveScenarioSpellReward`, `resolveScenarioEncampment`, `scenarioSpellOptions` | `tests/campaign/test_battle_creation.py` (`test_tome_reward_grants_exactly_two_selected_spells`, `test_encampment_reward_requires_destroy_or_occupy_choice`) |
| `application/campaign/features/hirelings/hire-passthrough-workflow.test.ts` | `createHirelingsWorkflow` hire wiring (variable fee, conditional acceptance) | `tests/campaign/test_variable_prices_and_restrictions.py`, `test_post_battle_engine.py` |
| `application/campaign/features/hirelings/upkeep-workflow.test.ts` | `resolveHirelingUpkeep` | `tests/campaign/test_post_battle_engine.py` (`test_hired_sword_upkeep_must_be_paid_or_the_hireling_leaves`) |
| `application/campaign/features/economy/wyrdstone-sale-workflow.test.ts` | `quoteWyrdstoneSale`, `sellWyrdstone` | `tests/campaign/test_post_battle_engine.py` (`test_wyrdstone_sale_value_comes_from_the_kb_table`, `test_sell_wyrdstone_applies_once`, `test_sell_wyrdstone_rejects_more_than_hoard`) |
| `application/campaign/features/equipment/transfer-workflow.test.ts` | `transferEquippedItem` | `controller.py` `transfer_equipped_item` (no dedicated test) |
| `application/campaign/features/economy/manual-corrections-workflow.test.ts` | `correctResource`, `addManualStashItem` | `controller.py` `adjust_resource`, `manually_add_item` (no dedicated test) |
| `domain/campaign/kernel/hireling-hire.test.ts` | `hireHireling` | `tests/campaign/test_post_battle_engine.py` (`test_hire_hireling_from_catalogue`, `test_hired_swords_use_separate_capacity_income_and_rating_counts`) |
| `application/campaign/features/searches/search-workflow.test.ts` | `resolveRareSearch`, `buyRareSearch`, `upgradeRareSearch`, `assignRareSearch`, `assignDramatisSearch`, `resolveDramatisSearch`, `hireDramatisSearch` | `tests/campaign/test_gui_interaction_regressions.py` (`test_rare_search_cannot_be_consumed_twice`, `test_failed_rare_purchase_keeps_search_available`), `test_hire_eligibility.py` (dramatis eligibility); engine impl in `post_battle_engine.py` / `controller.py` |

## Notes

- Paths are relative to `packages/typescript/` for the web tests and to the repo
  root for the desktop `tests/campaign/` suites.
- `resolveEyeInjury`, `setManualSkill`, `transferEquippedItem` and the follow-up
  acknowledgement row have no dedicated desktop test; they are pinned against
  the desktop implementation instead.
- This map covers the workflows ported by the coordination-tracked test units; it
  is not the parity manifest (`tests/web/parity/campaign-test-manifest.json`).
- Production fix found while porting the Returning-a-Favour test:
  `exploration-workflow.ts` `processQueue` matched the parked follow-up by object
  identity, but the first processing pass passes a spread copy, so the queue never
  advanced. Matching by `id` restores the desktop apply → advance flow.
