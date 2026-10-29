# Handoff to the verification task

The vectorized-migration plan (`PLAN.md`) ends at implementation. This file is
the complete input to the separate verification task that follows it.

Nothing here has been verified. Under `PLAN.md` §11 the migration deliberately
traded per-step certainty for throughput: rules were connected on
implementation, not on proof. Expect real defects.

## 1. Start here

```bash
# the worktree is not the editable install -- set this first or you test the wrong tree
export PYTHONPATH=$PWD/packages/python/combat-engine:$PWD/apps/combat-lab:\
$PWD/packages/python/roster-construction:$PWD/packages/python/core:$PWD/packages/python/knowledge

python tools/mordheim-utils.py parity --require-complete   # ~250s
pytest tests/engines -q
# then the statistical layer + battery per docs/reference/verification.md
```

A filtered specification runner (seconds, no full parity) is the cheapest
triage tool; the pattern is recorded in `PLAN.md` §10.

## 2. Scale of what is unverified

| | Count |
|---|---|
| Tags connected without running their specifications | 219 (the entire gate) |
| …of which had a consumer written before the gate opened, never executed | 135 |
| …of which were ported or fixed during phases 4–7 | ~44 |
| Checks actually run during the whole migration | a handful of targeted differentials + import/batch smokes |

No parity run, battery, statistical layer or broad pytest suite was executed
during phases 4–7.

## 3. Deliberately NOT implemented — explicit scope decisions of the plan

Every item here was examined, judged, and consciously left for this task (or
for a design decision). Nothing in this section is an oversight; nothing else
is knowingly unimplemented.

**Engine behaviour:**

- **`_crude_belch_ogre` internals.** Its *ordering* now matches the oracle
  (after the dance declarations, interleaved with Sea Shanty per owner), but
  the vectorized belch still never rolls the target's close-combat Leadership
  test (oracle `modular/rounds.py:784-791`) and lacks the contact /
  stupidity-failed / grappled / lost-owner-turn guards; the penalty is
  batch-wide. A faithful port needs a per-row hit-penalty mechanism (the scalar
  `ledger.hit_penalty` fold cannot express it) — a cross-file change left to
  this task. Divergent only when a belch is actually declared.
- **Lunatics/bitten/centigor/animosity/trip D6s bypass owned-roll resources.**
  The oracle rolls these through `OwnedRollDice`, which can offer the roller's
  personal rerolls (Ranald's Luck, Oracle, Augur, Scryer). The vectorized
  driver rolls them with plain `rng.integers` — a consistent house style across
  all round-level dice. A batch owned-roll helper ALREADY EXISTS for Leadership
  tests (`_leadership.py:154`); extending it to round/attack dice is a design
  decision for this task, not a per-rule port.
- **`condition.righteous-charge` split batches.** Fear/Stupidity and the +1 To
  Hit are per-row; but on a batch whose rows disagree about charging,
  `mechanic.causes-fear` / `mechanic.psychology-immunity` are still read off
  the ungranted fighter inside `_charm_gates`, `resolve_feral_instinct` and
  `_apply_opponent_leadership`. Needs row dispatch into `_psychology.py` /
  `_leadership.py`. Uniform batches (declared snapshots, established contacts)
  are correct.
- **Decision-key drift for extra attacks.** The driver splits the Whipcrack
  bonus into its own pool and Tentacle forfeits do not shift later indices, so
  an extra attack's decision key can differ from the oracle's by one. Key
  strings only, never dice. Fixing means restructuring pool indexing; weigh
  against the replay corpus before touching.
- **Bear Hug pool-index caveat.** Selection now mirrors the oracle (attacks 0-1
  only), but index correspondence between `prepared_attacks` and the oracle's
  weapons tuple relies on both dropping zero-count allocations identically; a
  whole-batch-empty attack could in principle shift indices.

**Other backends and harness (never this plan's scope):**

- **Native/Cython backend** — `NATIVE_PENDING` is deliberately frozen at the
  full snapshot (plan §5 Q1). In particular `native/_combat_compile.py:218`
  still calls the stateless `special_save_targets` and the C state struct knows
  nothing of the 12 new `CombatState` columns.
- **Parity harness** — `_specifications.py:299,1180` binds the `special_save`
  spec to `special_save_targets`, which the live engine no longer uses; and the
  four `_prepare_weapon_attack` adapter calls pass no `decisions`/`key`, so the
  TC14 Whip Master reroll is invisible to those specs. Retargeting the harness
  is verification-task work by definition.

## 4. Engine defects found during porting — ALL FIXED

Listed so you can confirm, not chase. Each was recorded as open in an earlier
revision of this file and closed before the plan ended:

1. **`_row_equipment` short-circuit was always true**, making
   `equipment_for_rows` dead code: per-row equipment (broken hands, transforms,
   Hillman wolf, mutations, Inquisitor brands) was bypassed engine-wide. Now
   compares against the round's phase fighter, with a `_diverging_rows` gate
   preserving the fast path, and `_carry_declarations` merging the round's
   declarations onto diverging rows (the oracle's `_mutated_phase_fighter`
   merge). **Highest-attention area: this path never executed before.**
2. **`mechanic.death-blow` out-of-action replay was mis-keyed** — confirmed
   against the oracle and removed; only `mechanic.deathblow` drives it.
3. **`_crude_belch_losses` ledger inversion** — spent the singer's Leadership
   ledger for the listener's test. Swapped.
4. **Missing per-round `maximum_wounds` clamp** — added, importing the shared
   `modular.state.maximum_wounds`.
5. **`priority` drift** — the oracle's `absent_initiative` tier demotion and
   `dance.woven-mist-active` floor are now ported (the `ABSENT_INITIATIVE`
   ordering constant did NOT cover the tier demotion).
6. **`attack_count` vs `build_attacks` drift** — all four differences closed
   (unarmed-fighting accepts natural-attacks and is elif-chained; post-extra
   cap is `min(attacks, 1)`; wraith-touch joins the 1-attack clamp; the pistol
   branch gates on `off_pistol` alone). Differential vs `phases.build_attacks`
   and `resolve_priority` across the changed clauses: all match.
7. **Production `InjuryContext` drift** — tough-as-steel moved from
   `hard_to_kill` to `true_grit`; the fen-hard-to-kill fire exclusion added.
8. **`effect.no-saves`** — producer (disease-dagger infection effect) and
   consumer (ward+regeneration forced blocked) both ported.
9. **`_crude_belch_ogre` ordering** — moved to the oracle's position in the
   shanty/belch per-owner loop, hit-penalty fold moved with it (the belch's
   remaining internal divergence is a §3 scope decision).

## 4b. Newly-live code to prioritise

Not defects — correct-by-reading code whose *first-ever execution* happens in
this task, so it has the highest defect expectation:

- Everything downstream of `equipment_for_rows` (dead until the
  `_row_equipment` fix): per-row broken hands, transforms, Hillman wolf,
  mutations, brands, and the new `_carry_declarations` merge.
- Everything the `special_save_context` switch activated at once: Dodge
  Sidestepper/Jester Dodge, Excellent Reflexes / tomb-robber-dodge,
  ethereal-hit-save step-aside suppression, the Ladle branch, Ghost Pirate
  Ethereal, Shadow's Coil, Gypsy Ward, Magical Void, Djinn's Luck/Curse saves.
- The 135 consumers written ahead of the gate, executing for the first time.

## 5. Pre-existing test failures (not caused by the migration)

Recorded before phases 4–7 began; confirmed against unmodified sources:
`test_disability_guardian_unarmed_and_onogal_have_observable_runtime_effects`
(a construction-fixture blocker, not a vectorized defect), `animal_friendship`,
frantic int8 overflow, random-profile characteristics. Plus the end-state
assertions that demand the migration already be finished:
`test_parity_inventory_is_complete_and_exact_checks_pass`,
`test_report_distinguishes_smoke_samples_from_certification_samples`,
`test_report_exposes_semantic_case_statuses_and_couples_completion_to_them`.
Those three should flip to passing once the gate reaches zero and parity is
clean — treat them as the migration's acceptance test.

## 6. Reporting-layer caveats

- **61 field obligations** still pass on a loose `f".{field}"` substring test
  (`PLAN.md` §9). Never audited.
- The obligation inventory verifies tags by source scan plus an explicit
  `INDIRECT_TAG_EVIDENCE` map; it proves consumption, not correctness.
- The parity round adapter replays positionally (`_RollVectorRng` ignores roll
  keys), so a case whose engine roll *order* legitimately differs from the
  modular tape misreports as a divergence.

## 7. Process risk worth knowing

/tmp path files are shared across sibling worktree sessions and were clobbered
TWICE during this migration, silently pointing runtime checks at the wrong
tree. All edits were made by absolute path and are correct; measured claims
were re-verified in-tree afterwards. For this task: never read a PYTHONPATH
from /tmp — build it inline from the repo root and assert a module's
`__file__` resolves under this worktree before trusting any run.
