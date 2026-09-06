# Modify the knowledge base

Prerequisites: read [the KB guide](../reference/knowledge-base.md) (layout,
classification, golden rules). After any change, run the validation loop from
that guide's last section.

## Procedure

1. Modify `sources/knowledge/catalog/`, `bands/` or `registry/` keeping stable
   ids. Never rename a rule, profile, item or mechanic id — add a band alias
   to `registry/aliases.yaml` instead.
2. Classify every effect with `scope`, `implemented`, `grant` and `binding`
   per the `runtime-schema.yaml` contract. `implemented: YES` requires every
   `YES` effect to carry a binding; unbound effects need a `reason`.
3. Reuse shared mechanics (`catalog/mechanics/execution.yaml`); do not
   introduce editorial names into the combat loop. Equivalence is declared by
   sharing `binding.kind` + `binding.id` (+ `parameters`), never inferred from
   names or prose.
4. For campaign catalogue data, follow the modelling conventions and
   data-ownership table in
   [`catalog/campaign/README.md`](../../sources/knowledge/catalog/campaign/README.md)
   and its HOWTO — the KB declares rules and tables, never a concrete
   campaign's state.
5. Run `python tools/format_yaml.py --check sources/knowledge` (or `--write`,
   then re-check), then `python tools/mordheim-utils.py validate`.
6. If you change a reviewed obligation, review its scenario and footprint:
   semantic specs pin KB targets by path and content digest, so a text edit
   invalidates them loudly (`verify` reports the exact mismatch). Refresh
   `sources[].digest` / `scope_digest` only after reviewing the changed text.
7. Regenerate the generated reports you touched
   (e.g. `python tools/kb/price-collation.py`) instead of hand-editing them.

Done when legal cases compile, illegal ones are rejected, and the affected
evidence is reviewed or explicitly pending. See
[Implement and verify rules](implement-and-verify-rules.md) for the evidence
side.
