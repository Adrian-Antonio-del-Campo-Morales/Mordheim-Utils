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
and golden rules: [the KB guide](../../docs/reference/knowledge-base.md).
Directory-level detail: [`registry/README.md`](registry/README.md),
[`catalog/hirelings/README.md`](catalog/hirelings/README.md) and
[`catalog/campaign/README.md`](catalog/campaign/README.md) (+ its HOWTO and
modelling conventions).

## Locale policy

English is **canonical and stored once**: the `name` field (and the `effect`
prose). The `name_i18n` / `effect_i18n` blocks store only *translations* for
non-canonical locales (`es`) and never carry an `en` mirror of the canonical
English. `tools/normalize_names.py` enforces this, and
`tests/knowledge/test_kb_i18n.py` guards it independently.

The KB carries a **reviewed Spanish translation**: warband rules, profiles
and band names, hired swords and campaign catalogues, and the skill / item /
mechanic catalogues fill `name_i18n.es` / `effect_i18n.es`. `es` fields are
data-only: `mordheim_knowledge.i18n` — the single sanctioned reader
(`set_locale` / `display_name` / `display_effect`, translation-first,
canonical-English-fallback) — is wired into both applications, so a filled
`es` surfaces immediately under `MORDHEIM_LOCALE=es`; an unfilled record
renders its canonical English.

Canonical glossary terms live in `catalog/translation-glossary.md`.

```powershell
python -m mordheim_combat_lab validate
python -m mordheim_combat_lab verify
```
