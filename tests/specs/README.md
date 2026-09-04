# Verification specifications

This directory is neither part of the KB nor of the distributed runtime.

- `structural/phase-verification.yaml`: correspondence between effects, phases and consumers.
- `semantic/rules/`: behaviour of core mechanics and basic rules.
- `semantic/grants/`: editorial grants and their recipients.
- `semantic/interactions/`: compositions between rules.
- `interactions.yaml`: required higher-order combinations.
- `interaction-policy.yaml`: risk policy, requirements and reviewed overrides for interactions.

Each semantic specification fixes the source, interpretation, category, initial
status, dice, decisions, expectations and mutations. The modular engine is the
system under test; its output is never used to generate the expected value.

Dice and decision sources are strict: an unexpected or unconsumed request
fails. Probabilities are expressed with exact fractions. Mutations are applied
temporarily in memory and restored.

## Interaction corpus (status 2026-09-04)

The interaction matrix of the gate is complete: `verify --require-complete`
reports `semantic_complete=True`, **217/217 required interactions covered,
0 required pending**.

- `interaction-policy.yaml` records **10 `illegal` overrides**: the
  body-armour × body-armour pairs (single `armour_id` slot per
  `FighterBuild`) that can never co-occur in legal construction. Each
  override keeps risk reasons and construction evidence. Do not add new
  overrides to make the report pass; they are reviewed semantic decisions
  (see the guide below).
- `semantic/interactions/` holds one interaction spec per pair (composition
  + boundary cases, strict dice, ≥ 1 detected mutation). The bulk lives in 9
  cluster files matching shared runtime concepts:
  `armour-target.yaml` (armour matrix, weapons/materials against armour),
  `injury-conditions.yaml` (injury states, helmets, crits, injury skills),
  `damage-mitigation.yaml` (unsaved-damage family: bear hug, poisons,
  regeneration/step-aside), `parry-skills.yaml`, `attack-count.yaml`
  (two-weapons and extra-attack stacking), `priority-order.yaml`
  (initiative/acting order), `hit-rerolls.yaml`, `wound-criticals.yaml` and
  `small-clusters.yaml`; the earlier authored interaction files
  (`thick-skull-injury.yaml`, `interactions.yaml` family specs, …) remain.
  The design basis for every case pattern is documented in
  [`docs/interaction-matrix.md`](../../docs/interaction-matrix.md).
- On the vectorized/native side the same corpus runs through `parity`:
  every case operation is adapted to the vectorized engine and compared
  against the modular execution of the identical case (0 divergences, 3724
  rows PASS as of 2026-09-04). A new spec whose operation has no adapter
  would surface as `PENDING_ADAPTER` and must be reviewed before the rule
  enters a new execution path.

```powershell
python -m mordheim_combat_lab verify --inventory
python -m pytest tests/verification/test_semantics.py -q
python -m mordheim_combat_lab verify --json
python -m mordheim_combat_lab verify --require-complete
```

The last command fails while any obligation or interaction remains pending.
See [the full guide](../../docs/tasks/verify-rules.md).
