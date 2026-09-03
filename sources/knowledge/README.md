# Knowledge base

Single source of rules and runtime data: shared catalogues, warbands, profiles, accesses and the registry. Its editorial rules keep their own identity and link through bindings to stable executable mechanics.

The `runtime` block is validated against `registry/runtime-schema.yaml`. `scope` indicates whether the effect belongs to the duel; `implemented` whether it has an implementation; `grant` how it is granted. An absent classification does not mean out of scope.

The KB carries no evidence of correctness. The structural contract and the semantic scenarios live in `tests/specs/`, so that the runtime does not depend on its own tests. See [Modify the KB](../../docs/tasks/modify-kb.md) and [Verify rules](../../docs/tasks/verify-rules.md).

```powershell
python -m mordheim_combat_lab validate
python -m mordheim_combat_lab verify
```
