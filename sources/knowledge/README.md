# Knowledge base

Single source of rules and runtime data: shared catalogues, warbands, profiles,
accesses and the registry. Its editorial rules keep their own identity and link
through bindings to stable executable mechanics.

The `runtime` block is validated against `registry/runtime-schema.yaml`. `scope`
indicates whether the effect belongs to the duel; `implemented` whether it has
an implementation; `grant` how it is granted. An absent classification does not
mean out of scope.

The KB carries no evidence of correctness. The structural contract and the
semantic scenarios live in `tests/specs/`, so that the runtime does not depend
on its own tests.

Full layout, classification contract, path of a rule, YAML formatting policy
and golden rules: [the KB guide](../../../docs/reference/knowledge-base.md).
Directory-level detail: [`registry/README.md`](registry/README.md),
[`catalog/hirelings/README.md`](catalog/hirelings/README.md) and
[`catalog/campaign/README.md`](catalog/campaign/README.md) (+ its HOWTO and
modelling conventions).

## Locale policy

The KB is **canonical English only** by convention: every record carries a
`name_i18n` / `effect_i18n` block for forward compatibility, but the
non-English fields (e.g. `name_i18n.es`) stay `null`. Do not fill them
casually — a translation pass would be a dedicated, reviewed project (and the
few existing Spanish strings in the Bretonnian band are historical exceptions,
not the convention).

The KB is nevertheless **prepared for a Spanish translation**:
`mordheim_knowledge.i18n` is the single sanctioned reader of the i18n blocks
(`set_locale` / `display_name` / `display_effect`, canonical-English-first,
locale fallback); it is already wired into the Campaign Manager's read model
(`KnowledgePort` band/profile/skill/item/hireling names). Filling an
`es` field is therefore a data-only change that surfaces immediately in the
applications, and reviewed entries (such as the Bretonnian ones) take effect
without any code change. Until a reviewed pass fills the fields, the display
locale renders the canonical English names.

The **pilot band** for the reviewed Spanish pass is `bands/mordheim/bretonnian-knights`:
all ten of its rules carry complete `name_i18n.es` / `effect_i18n.es` entries
reviewed against the same printed source as the English text. New bands should
follow its in-file glossary (Caballero Andante = Questing Knight, Caballero
Novel = Knight Errant, chequeo = test, 1D6 = D6) so translations stay
consistent across the KB.

```powershell
python -m mordheim_combat_lab validate
python -m mordheim_combat_lab verify
```
