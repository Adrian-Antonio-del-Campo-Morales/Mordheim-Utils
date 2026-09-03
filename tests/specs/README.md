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

```powershell
python -m mordheim_combat_lab verify --inventory
python -m pytest tests/verification/test_semantics.py -q
python -m mordheim_combat_lab verify --json
python -m mordheim_combat_lab verify --require-complete
```

The last command fails while any obligation or interaction remains pending.
See [the full guide](../../docs/tasks/verify-rules.md).
