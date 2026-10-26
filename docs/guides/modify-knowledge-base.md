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
   [campaign knowledge guide](campaign-knowledge.md)
   and its HOWTO — the KB declares rules and tables, never a concrete
   campaign's state.
5. Run `python tools/knowledge/maintenance/format_yaml.py --check sources/knowledge` (or `--write`,
   then re-check), then `python tools/mordheim-utils.py check verify`.
   That gate also checks every maintained document against
   [`contracts/knowledge-editorial-v1`](../../contracts/knowledge-editorial-v1/README.md):
   when a document gains, renames or drops a field, extend its schema in the
   same change or the validation fails. A new YAML under a covered tree needs a
   schema of its own — `tests/knowledge/test_editorial_schemas.py` fails when a
   document escapes the contract. The same suite refuses a schema that admits
   more than the documents hold and a declaration the documents never exercise
   unless `tools/knowledge/audit_schema_strictness.py` can name the contract
   behind it, so a field added "just in case" is a review question, not a
   silent allowance (see
   [Verification](../reference/verification.md#deterministic-modular-evidence)).
6. If a reviewed obligation changes, review the corresponding modular mechanics,
   construction and E2E expectations against the new text. Preserve adopted
   rulings and source traceability; do not replace an expected result with current
   engine output. The retired semantic YAML corpus is not a validation step.
7. Regenerate the generated reports you touched instead of hand-editing them.

Done when legal cases compile, illegal ones are rejected, and the affected
evidence is reviewed or explicitly pending. See
[Implement and verify rules](implement-and-verify-rules.md) for the evidence
side.

## Merging equivalent rules

A matching name or wording is not enough to merge rules. Before touching IDs,
review these three levels separately:

1. **Editorial identity:** confirm that every variant keeps exactly the same
   effect, scope, recipient and exceptions. Rules that apply an effect to
   another category (for example, "all Undead") do not merge with the rules that
   describe their bearer directly.
2. **Mechanical identity:** compare every `runtime.effects[].binding`. Two
   equivalent rules must share `kind`, `id` and `parameters`; the runtime stays
   in each band's local rule and never moves to the shared text catalogue.
3. **Persisted identity:** search for the ID in bands, applications, artefacts,
   saved campaigns and tests. The normal procedure preserves IDs and shares
   only the binding. Removing IDs is a destructive migration and requires a new
   persisted-format version or explicit compatible aliases.

For an authorized destructive merge:

- choose one canonical `shared-rule.*` and replace every `rule_ref`;
- keep the local rules, `applies_to`, `grant`, scope and bindings;
- write neutral shared text, without concrete profile names;
- update consumers that compare IDs directly and regenerate derived artefacts,
  never editing them by hand;
- document which IDs are retired and which campaign versions are accepted;
- test the absence of retired IDs, reference resolution, recipients, bindings,
  affected campaign rules and read/write of the format;
- run formatting, structural `verify`, the authorized mechanics/E2E checks and parity before
  publishing.

Do not merge when the recipient changes, a contextual exception exists, the
binding parameters differ or data compatibility is undecided.
