# Web parity gap report

Short audit of the desktop `tests/campaign/` suites against the web port's tests
(`packages/typescript/`). Companion to `web-parity-coverage-map.md`; scope is
test/behaviour coverage, not the parity manifest.

Date: 2026-09-11. Web core suite at the time of writing: 64 files / 526 tests green.

## Suite coverage

"Covered" means a web test file targets the same desktop suite or its behaviour;
the desktop suites are larger, so this is not a 1:1 assertion count.

| Desktop suite | Web counterpart | Status |
|---|---|---|
| `test_advancement_sequence_matrix.py` | `advancement.test.ts`, `post_battle_advancements.test.ts` | covered |
| `test_audit_regressions.py` | `audit.test.ts` | covered |
| `test_battle_creation.py` | `battle_creation.test.ts` | covered |
| `test_campaign_sequence_matrix.py` | `campaign_sequence.test.ts` | covered |
| `test_dice_resolution.py` | `dice_resolution.test.ts` | covered |
| `test_draft.py` | `draft.test.ts`, `draft-workflow.test.ts` | covered |
| `test_economy_sequence_matrix.py` | `economy.test.ts` | covered |
| `test_equipment_editor.py` | `equipment_editor.test.ts` | covered |
| `test_exploration_sequence_matrix.py` | `exploration.test.ts`, `exploration-followup-workflow.test.ts` | covered |
| `test_extended_audit_regressions.py` | `extended_audit.test.ts` | covered |
| `test_gui_interaction_regressions.py` | none direct; behaviour equivalents ported ad hoc (`beforeunload`, rare-search once-only) | **partial** |
| `test_hire_eligibility.py` | `hire_eligibility.test.ts` | covered |
| `test_injury_sequence_matrix.py` | `injury_sequence.test.ts` | covered |
| `test_knowledge_port.py` | `adapters/knowledge-reader/*` | covered |
| `test_malformed_save_matrix.py` | `adapters/campaign-file/corpus.test.ts` | covered |
| `test_out_of_action_tracking.py` | `out_of_action_tracking.test.ts` | covered |
| `test_persistence.py` | `persistence_parity.test.ts`, campaign-file tests | covered |
| `test_post_battle_advancements.py` | `post_battle_advancements.test.ts` | covered |
| `test_post_battle_engine.py` | `post_battle_engine.test.ts` + feature workflow tests | covered |
| `test_post_battle_resolution.py` | `post_battle_resolution.test.ts` | covered |
| `test_rules_catalogue.py` | `rules-catalogue.test.ts`, `rules_catalogue_parity.test.ts` | covered |
| `test_third_audit_regressions.py` | `third_audit.test.ts` | covered |
| `test_undo.py` | `undo.test.ts` | covered |
| `test_variable_prices_and_restrictions.py` | `variable_prices_and_restrictions.test.ts` | covered |
| `test_warband_pdf.py` | `warband_pdf_parity.test.ts` | covered |

## Known functional gaps

These are behaviours the desktop implements that the web port does not yet, or
implements differently. They are not test-only gaps.

1. **GUI interaction suite.** Desktop `test_gui_interaction_regressions.py` drives
   the Tk UI (modal grab, numeric inputs, ctrl-z, save dialogs). The web has a
   different UI harness; only the behaviour-level cases with a web seam were ported.
   Not a functional gap by itself, but most of its 16 cases have no web counterpart.

## Non-functional

- The parity manifest (`tests/web/parity/campaign-test-manifest.json`) still holds
  1,209 `pending` rows (per `INTEGRATION_BASELINE.md`); it is the migration
  completion gate, not a behaviour gap.

## Fixed while auditing

- **Conditional-hire acceptance roll.** `hireHireling` now takes `roll_ge` +
  `acceptance_roll` and rejects a missing roll (prerequisite) or a roll below
  `roll_ge` (failed); `hirelings-workflow` surfaces each offer's `roll_ge` (from
  the dynamic hire-eligibility rules) and passes the roll through. Covered by
  `hireling-hire.test.ts` and `hire-passthrough-workflow.test.ts`.
- **Variable (dice) hire fee.** `hireHireling` now takes `fee_base` / `fee_dice` /
  `fee_roll`: a dice fee requires the roll, rejects a roll below the dice count,
  and records `fee_base + fee_roll` as `cost`. `hirelings-workflow.hire` passes
  them through. Covered by the same two test files.
- **`Returning a Favour` upkeep cleanup.** Desktop `resolve_hireling_upkeep` strips
  every `Returning a Favour:` rule once the upkeep is paid
  (`post_battle_engine.py:2122`). `resolveHirelingUpkeep` now does the same when
  paying (keeping other rules); covered by `upkeep-workflow.test.ts`.
- `exploration-workflow.ts` `processQueue` matched the parked follow-up by object
  identity, but the first processing pass passes a spread copy, so the queue never
  advanced (broke `applyExploration` → `continueExploration`). Matching by `id`
  restores the desktop flow; covered by `exploration-followup-workflow.test.ts`.
