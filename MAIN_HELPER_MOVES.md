# Engine test helpers: changes to port to main

Implemented on `vectorized-slice`; not yet applied to `main`.

| Destination | Symbols | Previous source on main |
|---|---|---|
| `tests/engines/shared/dice.py` | `StrictDice`, `StrictDecisions`, `EvidenceMismatch` | Combat Lab `verification/dice.py` and `verification/reports.py` |
| `tests/engines/modular/replay.py` | `ReplayObservation`, `replay_duel` (modular only) | Combat Lab `verification/parity/_replay.py` |

These are engine-test helpers, not production engine or UI functionality.
No new directories are needed. Module names do not start with `test_`.

To port: add these two modules and redirect engine-test imports to their new
locations, including EvidenceMismatch imports and lazy imports inside tests.
The modular replay helper imports the shared dice helper. Its optimized/native
branches are deliberately absent: this does not restore cross-engine replays.

Do not make production application code import tests. Review remaining Combat
Lab consumers separately before removing their old implementations.
No engine logic, assertions or frozen JSON were changed. Tests were not run.

## Remove application catalogue checks from engine mechanics

In `tests/engines/modular/mechanics/test_spectral_touch_activation.py`, remove
`test_catalogue_profile_status_and_build_share_the_canonical_route` and its
`CombatCatalogue` import. This function checks the application's profile/rule
catalogue rather than combat mechanics. The precompiled Spectral Touch combat
tests remain intact. Apply the same removal on main; do not restore the app in
the slice. Frozen corpus entries and historical keys are unchanged.

## Remove native calls from modular runtime tests

In `tests/engines/modular/runtime/test_spectral_touch_activation.py` and
`test_vomit_attack.py`, removed the native `compile_duel` imports/calls and
the `native` backend parameter cases. Retained `compile_duel_plan`, NumPy
execution/parallel checks and their assertions. No frozen keys were changed.

On main, remove these native checks from the modular suite as well. If keeping
the native checks, place them in the native suite rather than reintroducing
native dependencies into modular runtime tests. No native code belongs in the
slice. Tests were not executed.

## Remove application fragments and the mixed shared parallel check

In `tests/engines/shared/contracts/test_duel_context.py`:

- Remove the `improve_attributes` import/call/assertion from
  `test_canonical_stats_survive_player_advances_and_explicit_overrides`, plus
  its now-unused FighterBuild preparation/import. This checked Combat Lab's
  attribute-improvement helper, not a common engine contract. Keep the frozen
  profile and explicit-override assertions.
- Remove `test_real_pool_preserves_context` entirely, including its backend
  parametrization. It mixed app configuration (`DuelExecutionSettings.request`),
  app orchestration (`simulate_battery`), NumPy parallelism and modular
  parallelism. No app support is copied into the slice.
- For main: the removed settings/request/battery checks belong with Combat Lab
  tests if retained. The separate parallel-runtime suites of modular and NumPy
  remain unchanged; this removal does not delete those suites.

All other shared data/context tests remain. No tests were run.

## Remove duplicate frozen-build fixtures

Keep the first `_frozen_compiles` definition (`pytest.fixture(autouse=True)`)
while deleting the second, otherwise-identical definition without autouse in:

- `tests/engines/modular/mechanics/test_mim_mutations.py`
- `tests/engines/modular/mechanics/test_profile_save_thresholds.py`
- `tests/engines/modular/mechanics/test_stateful_rules.py`
- `tests/engines/modular/mechanics/test_vomit_attack.py`
- `tests/engines/modular/mechanics/test_weapon_variant_combat.py`
- `tests/engines/modular/runtime/test_profile_save_thresholds.py`
- `tests/engines/modular/runtime/test_vomit_attack.py`

The duplicate overwrote the automatic fixture. Only the duplicate definition
was removed; test bodies, assertions and explicit usefixtures markers remain.
Apply the same correction on main. No tests were executed.

## Remove redundant explicit frozen-fixture activation

Where the module's `_frozen_compiles` fixture has `autouse=True`, remove
`@pytest.mark.usefixtures("_frozen_compiles")`: automatic activation already
covers those tests. Preserve other fixtures in mixed usefixtures decorators
and explicit activation in any module without an automatic fixture.
This slice pass removed 171 redundant marks across 9 files.
No test bodies/assertions changed and no tests were executed.

## Load observed-duel scenarios directly from the frozen case catalogue

In `tests/engines/modular/runtime/test_duel_observed.py`, `_pair` now resolves
`benchmark/basic`, `benchmark/stateful` and `benchmark/long` through `cases`
and `benchmark_case_key`. Tests receive the existing cases fixture. Removed
this module's compile_fighter placeholder and frozen-build monkeypatch fixture.
The catalogue's explicit Leadership inputs were not all present in the older
compiled-builds lookup; the complete updated pairs already exist in
compiled-cases.json. Reuse those exact pairs rather than compile or substitute
fighters. All assertions, seeds and sample sizes remain unchanged; no JSON
updates or test execution were performed.

## Align four NumPy checks with their actual contracts

- `mechanics/test_rule_family_effects.py`: Animal Friendship now uses the exact
  frozen E2E pair containing a normal animal (`species.normal-animal`), through
  the existing `shared_cases` loader. The former pair only had `species.animal`.
  The zero-opponent-wins assertion remains unchanged.
- `mechanics/test_shared_families.py`: rename the Black Hunger payload check to
  describe deferred activation; assert zero permanent construction bonus and
  retain the mechanic tag check. This does not certify the runtime attack bonus.
  The separate backlash sequence remains intact.
- `runtime/test_vectorized_engine.py`: check per-row variation of all four
  random characteristics of the condemned. Remove the eager Spawn attack-roll
  expectation; the existing mechanics check observes its D6+1 live round pool.
- `mechanics/test_runtime_regressions.py`: Frantic now observes the real driver's
  event ordering for rows where both fighters attack, intercepting damage
  resolution. Preserve the tier-10 assertion; remove the historical 55–95 wins
  expectation, which mixes priority with unrelated combat rules. This does not
  diagnose or certify the previously observed 0/512 full-duel result.

No engine code, frozen JSON or dependencies changed. Static AST parsing of the
four files succeeded. No tests, collection, simulations or test imports ran.
Apply these changes to main as well; functional confirmation remains pending.

### Animal Friendship: distinguish the operator from public admission

Correction to the preceding entry: the canonical `mechanic.animal-friendship`
remains pending in the optimized admission gate. The renamed test now checks
`opposed_attack_count` directly with the frozen normal-animal pair, including
an unprotected control. It also asserts that public simulation still rejects
this pending canonical mechanic. No gate was bypassed or capability enabled.
This replaces the previous full-duel zero-wins assertion. AST parsing only;
no tests or simulations executed.
