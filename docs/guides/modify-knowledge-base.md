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
   then re-check), then `python tools/mordheim-utils.py verify --structural`.
   That gate also checks every maintained document against
   [`contracts/knowledge-editorial-v1`](../../contracts/knowledge-editorial-v1/README.md):
   when a document gains, renames or drops a field, extend its schema in the
   same change or the validation fails. A new YAML under a covered tree needs a
   schema of its own — `tests/knowledge/test_editorial_schemas.py` fails when a
   document escapes the contract. The same suite refuses a schema that admits
   more than the documents hold and a declaration the documents never exercise
   unless `tools/knowledge/audit_schema_strictness.py` can name the contract
   behind it, so a field added "just in case" is a review question, not a
   silent allowance.
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

## Fusionar reglas equivalentes

Una coincidencia de nombre o de redacción no basta para fusionar reglas. Antes
de tocar los IDs, revisa por separado estos tres niveles:

1. **Identidad editorial:** confirma que cada variante conserva exactamente el
   mismo efecto, alcance, destinatario y excepciones. Las reglas que aplican un
   efecto a otra categoría (por ejemplo, «todos los No muertos») no se fusionan
   con las reglas que describen directamente a su portador.
2. **Identidad mecánica:** compara todos los `runtime.effects[].binding`. Dos
   reglas equivalentes deben compartir `kind`, `id` y `parameters`; el runtime
   permanece en la regla local de cada banda y nunca se mueve al catálogo de
   texto compartido.
3. **Identidad persistida:** busca el ID en bandas, aplicaciones, artefactos,
   campañas guardadas y pruebas. El procedimiento normal conserva los IDs y
   comparte solo el binding. Eliminar IDs es una migración destructiva y exige
   una nueva versión del formato persistido o aliases compatibles explícitos.

Para una fusión destructiva autorizada:

- elige un único `shared-rule.*` canónico y reemplaza todos los `rule_ref`;
- conserva las reglas locales, `applies_to`, `grant`, alcance y bindings;
- escribe texto compartido neutral, sin nombres de perfiles concretos;
- actualiza consumidores que comparen IDs directamente y regenera los
  artefactos derivados, sin editarlos a mano;
- documenta qué IDs se retiran y qué versiones de campaña se aceptan;
- prueba ausencia de IDs retirados, resolución de referencias, destinatarios,
  bindings, reglas de campaña afectadas y lectura/escritura del formato;
- ejecuta formato, `verify --structural`, evidencia semántica y paridad antes de publicar.

No fusiones si cambia el destinatario, existe una excepción contextual, los
parámetros del binding difieren o la compatibilidad de datos no está decidida.
