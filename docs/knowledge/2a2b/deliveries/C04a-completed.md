# C04a — Acceso a listas: Undead, Lahmia y orígenes

**Estado:** completo (17/17). Rama `2A2B`, base inicial conservada; cambios locales heredados
intactos. Sin commits ni E2E.

## Capacidad antes → después

| Capacidad | Antes | Después |
|---|---|---|
| Lahmian Foreign/Native | el contrato **añadía** la lista elegida a las dos candidatas declaradas → unión: cada trasfondo aceptaba el equipo del otro | `configuredProfile` **intersecta** las candidatas con el trasfondo seleccionado; oferta y aceptación leen la misma declaración estrechada. Una selección ausente se lee como la asignación Foreign impresa |
| Destinatarios fijos Lahmia | `Foreign background only` (Blood Slaves) podía recibir la lista Native y al revés | cada destinatario conserva sólo su candidata impresa |
| Undead (Necromancer) | la lista Undead ya se ofrecía y aceptaba | reconciliado, sin cambios |
| Mootlanders/Halfling | la lista Halfling y la pistola extra del Moot Elder ya fluían, sin alcanzar a los Warriors | reconciliado; la fila `assessment` "excluida por alcance" vuelve a ser acceso vigente |
| Sartosan base | ya rechazaba rapier, armadura pesada y handgun de las variantes | reconciliado (restricción de banda existente) |
| Estalian | ofrecía la armadura pesada de su propia lista pero la compilación la rechazaba por el "may not wear armour" heredado | la línea que la variante añade es legal; el resto de armaduras de cuerpo sigue prohibida y las defensas de mano siguen seleccionables |

## Cambios propios

- `packages/typescript/domain/eligibility/index.ts`: helper `backgroundEquipmentLists` usado por
  `configuredProfile`; el bloque `compiler.foreign-or-native-background` de `buildAccess` ya no activa
  la lista elegida si el perfil no la declara. `_eligibility.js` regenerado.
- `estalian-corsairs-sar/special-rules.yaml`: `pirates--no-armour` prohíbe `armour.light-armour` y
  `armour.toughened-leathers` (F074-pirate-variants).
- Pruebas: `test_construction_variants.py`, `test_t13_construction_recipients.py`, `canonical-choices.test.ts`.

## Comprobación

- `pytest` de los 3 archivos afectados: **81 → 84 passed** (`%TEMP%/c04a-out/final-py.txt`).
- `vitest canonical-choices.test.ts` 15 passed; `shared-eligibility.test.ts` +
  `t13-shared-eligibility-reconciliation.test.ts` 32 passed (`configuredProfile` corre en toda
  llamada canónica: riesgo compartido).
- `tsc --noEmit` limpio; `build-eligibility.mjs --check` → "current".
- Matriz oferta+aceptación en `%TEMP%/c04a_verify.py` (Lahmian foreign/native, destinatarios
  fijos, Estalian/Sartosan/Wasteland).

## CSV e integración

Propuesta preparada sólo con `query`/`prepare` (`apply` en preview, sin `--write`):
`%TEMP%/t13-c04a-prepared.json`, 17 claves `(id, clause_id)`, `pending {}`, notas añadidas
conservando textos y huellas. Pendiente: que el coordinador integre con snapshot íntegro,
conservación de 4.556 claves y control concurrente. Sin bloqueos: `eligibility/index.ts` y
`_eligibility.js` son de propiedad C01–C06 sin otro escritor detectado; `compiler.py` no se tocó.
El CSV ya figuraba modificado en el árbol antes de esta entrega.

**Integración del coordinador:** 17 filas aplicadas con conservación de las 4.556
claves/textos/huellas/notas y control concurrente, en
`%TEMP%/c04a-coordinator-integration-q7aw2lxe`. La propuesta y logs temporales citados
por el ejecutor no estaban accesibles en este host; las decisiones se prepararon
desde las claves actuales. Ejecutados únicamente los dos discriminadores de los
consumidores modificados (Foreign/Native y armadura Estalian): 2 passed,
`%TEMP%/c04a-coordinator-focused.txt`. C04a cerrado; sin E2E, commit ni push.
