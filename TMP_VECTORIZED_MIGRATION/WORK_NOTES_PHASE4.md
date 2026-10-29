# Phase 4 work notes — weapon profiles (2026-10-25)

Skipped-verification log per PLAN §11. One line per port: what landed, what
(if anything) was run.

| Tag | Port | Check run |
|---|---|---|
| weapon.katana | connect-only: compiles to strength_bonus/parry/two_handed | skipped (generic fields, confident) |
| weapon.kanabo | connect-only: strength_bonus/concussion/two_handed | skipped |
| weapon.knuckledusters | connect-only: paired | skipped |
| weapon.long-daggers | connect-only: parry/paired + weapon.dagger tag | skipped |
| weapon.pry-bar | connect-only: parry/concussion | skipped |
| weapon.wizards-staff | connect-only: parry/concussion/two_handed | skipped |
| weapon.skull-busta | runtime branch pre-existing in `_attacks.py:881` (helmet → 6+, not Thick Skull); fields first_round_strength_bonus/concussion generic | agent cross-read vs `modular/attacks.py:867`; no behavioural test (deferred) |
| weapon.shock-rod | `shock` branch added to `_operators.injury_conditions` (totals 1–4 → STUNNED, mirrors `phases.injury_condition:704`); `shock=has(effect,"weapon.shock-rod")` threaded into the production `InjuryContext` in `_attacks.py`; `injury_results` path already had shock | one sub-second differential: `injury_conditions` vs shared `phases.injury_condition` over totals 1–12 with/without shock |

Gate: all 8 added to `NUMPY_CONNECTED_TAGS` (kernel.py); `weapon_profile_tags`
pending 8 → 0. Native gate untouched.

Unverified until phase 8 (explicit): every connect-only tag above; skull-busta
behaviour; shock-rod through the full attack path (only the operator was
differentially checked).

Observed while scoping, NOT touched (out of phase-4 scope — candidates for the
phase-8 triage or the forked-predicate sweep):
- `_attacks.py` production `InjuryContext` merges `skill.tough-as-steel` into
  `hard_to_kill` instead of `true_grit` (oracle separates them at
  `modular/contexts.py:458`; they differ at total=3) and omits the
  `mechanic.fen-hard-to-kill` + fire exclusion.
