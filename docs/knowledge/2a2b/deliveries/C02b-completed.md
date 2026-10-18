# C02b — Restricciones de equipo Trollheim

**Estado integrado: 2026-10-16 — ambos pendientes cerrados.** Ocho cláusulas ya cerradas en la
integración anterior; este incremento conecta la excepción Feather Headdress del líder actual
(Red Teeth) y la resolución de tokens de objeto en `band_forbids`.
Base: `D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK` (checkout compartido, rama `2A2B`); snapshot de
base de los archivos propios en `D:\DEVEL\Mordheim\_c02b-out\base-20261016`. Sin commit ni push.

## Capacidades implementadas

### 1. Excepción de Feather Headdress por líder actual (`rule/…/red-teeth--equipment-restrictions`, `whole`)

La excepción impresa se conecta **reutilizando el contrato canónico ya existente**
`condition.current-warband-leader` (el mismo estado suministrado que Battle Tongue Norse lee por
`eligible_condition_ids`, C11), sin representación paralela:

- la línea del tocado publica la posición como destinatario alternativo:
  `applies_to: {profile_ids: [witch-doctor], eligible_condition_ids: [condition.current-warband-leader]}`
  (el Witch Doctor obligatorio sigue siendo el líder inicial impreso);
- `entryReachesProfile` lee las condiciones declaradas del miembro (`EditorialProfile.conditions`,
  que `configuredProfile` adjunta junto a las variantes) y `recipientView` las adjunta también desde
  `build.condition_ids` cuando una compilación canónica pasa la fila con el build; así oferta,
  veredicto de kit completo y compilación deciden un solo hecho;
- sin la condición, el mismo perfil sigue rechazado como antes (el tocado no llega a su lista); las
  otras dos mitades de la cláusula conservan su veredicto.

### 2. Tokens canónicos en prohibiciones de nivel de banda (`band--foreign-variant-equipment`, Sartosan Pirates, `handgun`)

Cierra el defecto registrado en `REMAINING_MODULAR_ENGINE_PROBLEMS.md`: un token de banda que nombra
un objeto canónico ya no provoca `construction_clause_unstructured` al seleccionar otro objeto legal.

- `campaign/construction.ts`: `BandFacts.equipment_forbid_items` (misma lectura que
  `ProfileFacts.equipment_forbid_items`) y `equipmentIssueFor` lo publica como `band_forbid_items`;
- `eligibility/index.ts`: `resolvedBandForbids` resuelve el subconjunto contra los hechos de objeto
  que ya porta el contexto (`context.items`, que el transporte completa desde el catálogo instalado)
  y `equipmentIssue` lo une a los tokens resueltos del perfil al decidir el informe. Sin segundo
  validador y sin adivinar: un token que ningún registro responde sigue informándose, y el objeto
  nombrado conserva su rechazo por su propio token.

## Archivos propios

- `sources/knowledge/bands/trollheim/lustria-savage-goblins/equipment-access.yaml` (destinatario por condición en la línea del tocado)
- `contracts/knowledge-editorial-v1/equipment-access.yaml.schema.json` (miembro `eligible_condition_ids` con su consumidor documentado)
- `packages/typescript/domain/eligibility/index.ts` (`applies_to.eligible_condition_ids`, `entryReachesProfile`, `configuredProfile`, `recipientView`, `resolvedBandForbids`, `band_forbid_items`)
- `packages/typescript/domain/eligibility/bridge.ts` (`configuredProfile` recibe `condition_ids` del build)
- `packages/typescript/domain/campaign/construction.ts` (`BandFacts.equipment_forbid_items`, `bandFactsOf`, `equipmentIssueFor`)
- `packages/python/roster-construction/mordheim_construction/_eligibility.js` (bundle regenerado con `npm run build:eligibility`; `npm run check:eligibility` → *Shared eligibility bundle is current*)
- `tests/python/construction/test_t13_construction_recipients.py`, `tests/typescript/domain/campaign/construction-blockers.test.ts`

Sin `npm run typecheck` propio: `npx tsc -p packages/typescript/tsconfig.json` → **exit 0**.

## Evidencia focal (ejecutada)

- `python -X utf8 -m pytest tests/python/construction/test_t13_construction_recipients.py -q` → **53 passed, exit 0** (`C:\Users\Pholtergate\AppData\Local\Temp\c02b-pytest-recipients2.txt`), con los nuevos discriminadores: oferta/rechazo del tocado según la condición, Witch Doctor sin estado, kit compilado (rechazo sin la condición, compilación con ella), tokens de banda conocido/legal/desconocido.
- `npx vitest run tests/typescript/domain/campaign/t13-construction-restrictions.test.ts` → **17 passed, exit 0** (`…\Temp\c02b-vitest-t13.txt`); `…/construction-blockers.test.ts -t expresses` → **2 passed, exit 0** (`…\Temp\c02b-vitest-c02b.txt`).
- `…/test_c03b_equipment_obligations.py` → **2 passed** (la obligación del líder inicial no cambia).
- Contrato editorial: `test_equipment_access_schema_contract.py` + `test_editorial_schemas.py` + `test_schema_strictness_cli.py` (`…\Temp\c02b-pytest-schemas.txt`) validan `equipment-access.yaml` y su esquema sin ningún hallazgo atribuible a este incremento.
- **Control concurrente:** un hunk ajeno posterior en `eligibility/index.ts` (cláusula 'sin equipo' sobre materiales/preparaciones y kit impreso, `buildRestriction`) se preservó intacto. Tras él se repitieron los checks afectados sobre el árbol fusionado: `npx tsc -p packages/typescript/tsconfig.json` → **exit 0** (`…\Temp\c02b-tsc2.txt`), `npm run check:eligibility` → *bundle current*, `pytest …/test_t13_construction_recipients.py` → **53 passed** (`…\Temp\c02b-pytest-recipients3.txt`) y `vitest run t13-construction-restrictions + construction-blockers` → **42 passed, 1 failed** (`…\Temp\c02b-vitest-final.txt`), ese único fallo siendo el rojo previo ajeno descrito abajo. Los hunks propios se aplicaron por sustitución de cadenas sobre los archivos compartidos (snapshot de base en `…\_c02b-out\base-20261016`), sin restaurar archivos completos.

## CSV propuesto (sin `apply --write`)

**Integración final del coordinador:** tres filas aplicadas sobre el CSV actual (un cierre y dos actualizaciones de evidencia), con snapshot íntegro, conservación de las 4.556 claves/textos/huellas/notas y control concurrente. Artefactos: `C:\Users\PHOLTE~1\AppData\Local\Temp\c02b-final-coordinator-j4sold84`. Remate: `resolvedBandForbids` exige un registro no nulo; el caso existente de token desconocido comprueba además un lookup `null` mediante `validateConstruction`. Bundle reconstruido; cinco casos afectados correctos, 48 deseleccionados (`%TEMP%\c02b-coordinator-close.txt`). Retirado el problema resuelto de band_forbids. Sin E2E, commit ni push.

`python -X utf8 tools/knowledge/t13_csv.py prepare … --out …` → **exit 0**, snapshot `sha256 2d1cfe63ee8b6e4a4a496305ed3557cb1d41072d1b92dbbcd7435728e15ded9e` (4.556 claves):

- cambios: `D:\DEVEL\Mordheim\_c02b-out\c02b-changes.json`
- paquete validado: `D:\DEVEL\Mordheim\_c02b-out\c02b-proposal.json` (vista previa, sin escritura)

Propone: fila Red Teeth `pending → {}`, evidencia ejecutada en `verification` y nota de conexión; nota en la fila `recipient--scope--leader-only` del tocado; nota y evidencia en la fila band-level de Sartosan. La validación de conservación y el control concurrente quedan para el coordinador, que es el único escritor autorizado.

## Bloqueos y limitaciones concretas

- **Fallos externos, no causados por este incremento:** `tests/typescript/domain/campaign/construction-blockers.test.ts` tiene una expectativa obsoleta frente al artefacto generado (`dwarf-slayers-kaz` `troll-slayers`: espera `["armour","ranged-weapons"]`, el artefacto publica `constant-save-cloak`/`non-thrown-ranged`); la misma expectativa existe en `HEAD` y el artefacto generado es anterior, así que es rojo previo, de otro paquete, y no se tocó. `test_editorial_schemas.py` informa además fallos concurrentes en documentos ajenos (`catalog/items/combat-equipment.yaml`, `hirelings/hired-swords/core.yaml`, `close-combat.yaml`, `execution.yaml`, mutaciones/`defs`) ya registrados por C11; ninguno menciona `equipment-access`.
- **Fuera del encargo:** la ruta de campaña (`DraftWorkspace`/artefacto generado) no publica un estado de líder actual, así que la excepción se decide en la ruta canónica de oferta/veredicto/compilación (transporte desktop y `compile_fighter`); no se simula sucesión, campaña ni movimiento, y no se añadió entrada de líder en el borrador de campaña (infraestructura especulativa).
- **Generación web:** el artefacto `build/generated/knowledge-web/` sigue siendo el previo (la generación está bloqueada por el defecto Mer-Creature registrado, ajeno a C02b); no se regeneró ni se editó a mano.
- Sin E2E, parity, cobertura, vectorial/nativo ni T14; sin commit ni push.
