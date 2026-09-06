# Verification specifications

This directory is neither part of the KB nor of the distributed runtime.

- `structural/phase-verification.yaml`: correspondence between effects, phases and consumers.
- `semantic/rules/`: behaviour of core mechanics and basic rules.
- `semantic/grants/`: editorial grants and their recipients.
- `semantic/interactions/`: compositions between rules (one spec per required pair, batched in 9 cluster files plus the earlier authored files).
- `interactions.yaml`: required higher-order combinations.
- `interaction-policy.yaml`: risk policy, requirements and reviewed overrides for interactions.

Each semantic specification fixes the source, interpretation, category, initial
status, dice, decisions, expectations and mutations. The modular engine is the
system under test; its output is never used to generate the expected value.

Dice and decision sources are strict: an unexpected or unconsumed request
fails. Probabilities are expressed with exact fractions. Mutations are applied
temporarily in memory and restored.

## Interaction corpus

The interaction matrix of the gate is complete: `verify --require-complete`
reports `semantic_complete=True`, 217/217 required interactions covered,
0 required pending.

- `interaction-policy.yaml` records the reviewed `illegal` overrides (the
  body-armour × body-armour pairs that can never co-occur in legal
  construction). Each override keeps risk reasons and construction evidence.
  Do not add new overrides to make the report pass; they are reviewed semantic
  decisions.
- On the vectorized/native side the same corpus runs through `parity`: every
  case operation is adapted to the vectorized engine and compared against the
  modular execution of the identical case. A new spec whose operation has no
  adapter surfaces as `PENDING_ADAPTER` and must be reviewed before the rule
  enters a new execution path. Executable report, not a figure here, is the
  status source.

The design basis for every case pattern is documented in
[the verification reference](../../docs/reference/verification.md) (layered
strategy) and the per-finding rulings in
[the modular audit record](../../docs/decisions/modular-audit.md).

```powershell
python -m mordheim_combat_lab verify --inventory
python -m pytest tests/verification/test_semantics.py -q
python -m mordheim_combat_lab verify --json
python -m mordheim_combat_lab verify --require-complete
```

The last command fails while any obligation or interaction remains pending.
Full commands and report reading:
[Develop and release](../../docs/guides/develop-and-release.md).
