# B04 — Contratos del catálogo: corrección acotada

**Integrado por el coordinador, 2026-10-18.** Aceptadas las cuatro correcciones
en datos/contrato y la restauración de destinatarios Wulfen/Wolves; reutilizada
la evidencia del ejecutor, sin repetir validaciones ni ampliar a suites.
Este encargo acotado queda cerrado; no equivale al cierre de todo el bloque 4.
Persisten las expectativas de veneno y el formato previo señalados abajo para
la integración final. Sin cambios al CSV, commits ni pushes.

**Estado: corregido y validado, 2026-10-17.** Los cinco documentos asignados
validan sin hallazgos; `banshee--cold-steel` ya estaba resuelto y no se tocó.
No se ejecutaron baterías integradas, E2E, parity, cobertura ni comparaciones
con HEAD. Base exacta en `%TEMP%/b04/base-sha.txt` (seis archivos copiados antes
de editar). Sin commits ni pushes.

## Correcciones frente a lo ya resuelto

| Error asignado | Capa | Corrección |
|---|---|---|
| Eye Pendant `kind: equipment` | dato | `kind: combat-equipment`, la misma familia que las demás defensas llevadas (Lucky Charm, Magic Acorn, Wolf Pelt Cloak, All-Seeing Eye). El `mechanic_id: defence.eye-pendant` no cambia. |
| `true_grit` fuera del contrato | contrato | El campo es legítimo (`EffectSet.true_grit`, consumido por `phases.py`/`contexts.py` y declarado por `skill.tough-as-steel`), así que se añadió `"true_grit": {"type": "boolean"}` al vocabulario cerrado de `parameters`. No se tocó `execution.yaml`. |
| close-combat: `skills/114 kind` | dato | `mechanic.undead-foes-no-fear`: `kind: band` → `warband`, el vocabulario del contrato y el que usan las demás reglas de banda (`mechanic.amazon-isolationists`, `mechanic.mesmerising-dance`). El runtime y sus tags no cambian. |
| close-combat: `skills/329 effect_i18n` | dato | La cadena española de Drenok estaba sin comillas dentro de un flow mapping: la coma la partía en una segunda clave con valor nulo. Se entrecomilló la oración completa sin cambiar su texto. |
| close-combat: `weapons/100` y `101` | metadatos | Se añadió `rules_source_url` a `weapon.whip-tc14` y `weapon.icefang-axe` con la URL ya presente en su único `source_refs` (Town Cryer 14 y 15). |
| `wolves--animals` (Norse btb) | dato | El `runtime` NO y el `rule_ref: shared-rule.animal` estaban colgados por error de `wulfen--equipment-restrictions` (clave `runtime` duplicada; YAML conservaba la última). Se devolvieron a `wolves--animals`; `wulfen` recupera su `runtime` YES con `profile.equipment-restrictions` (`forbids: weapons, armour`), igual que su gemelo de Lustria. |
| `banshee--cold-steel` | — | **Ya resuelto**: el documento y el paquete `necrarchs-mou` validan con 0 hallazgos y el contrato `special-rule.banshee--cold-steel` existe; el Banshee compila con `defence.cold-steel`. No se editó. |

## Archivos propios

- `sources/knowledge/catalog/items/combat-equipment.yaml` — 1 línea.
- `sources/knowledge/catalog/mechanics/close-combat.yaml` — 4 cambios (1 kind, 1 i18n, 2 URLs).
- `sources/knowledge/bands/mordheim/norse-explorers-btb/special-rules.yaml` — traslado del bloque `runtime`/`rule_ref` (sin cambios semánticos).
- `contracts/knowledge-editorial-v1/catalog-mechanics-execution.yaml.schema.json` — 1 propiedad.
- `docs/knowledge/2a2b/deliveries/B04-catalogue-contracts-completed.md` — este documento.

No se modificaron `execution.yaml` ni `necrarchs-mou/special-rules.yaml`: validan
sin cambios y su capacidad implementada se conserva.

## Validaciones ejecutadas

| Comprobación | Resultado |
|---|---|
| Validación por documento de los cinco archivos asignados (esquema editorial) | **0 problemas** en cada uno; salida en `%TEMP%/b04/` |
| `test_editorial_schemas.py -k execution_parameter_vocabulary` | **1 passed**, 305 deselected (`%TEMP%/b04/schema-vocab.txt`) |
| `test_c01b_intrinsic_profile_declarations.py -k wulfen` | **4 passed**, 2 failed, 66 deselected (`%TEMP%/b04/wulfen.txt`) |
| `test_abdul_eye_pendant.py` | **6 passed** (`%TEMP%/b04/abdul.txt`) |
| `test_c05a_deathblow.py -k true_grit` | **1 passed**, 8 deselected (`%TEMP%/b04/truegrit.txt`) |
| Compilación directa | Banshee conserva `defence.cold-steel`; Wulfen conserva S4/A2 con `weapon.natural-attacks` y **rechaza** espada, armadura ligera y casco |

El vocabulario del esquema ahora coincide exactamente con `fields(EffectSet)`
(la única diferencia anterior era `true_grit`).

## Bloqueos concretos

- Los 2 fallos de `-k wulfen` son la expectativa de **legalidad de veneno**
  (`compiled(..., main_poison_id="poison.black-lotus")` lanza para líneas
  `weapons-armour`), no las prohibiciones restauradas: los tres rechazos de
  wulfen se comprobaron directamente. El mismo defecto afecta a Zombies y queda
  fuera de B04; no se editó ni se debilitó la prueba.
- El gate `format_yaml --check` ya marcaba los tres YAML como «would change» en
  la base (16 avisos en `close-combat.yaml`); las ediciones no añaden avisos
  nuevos, pero no se normalizaron los archivos completos por estar fuera del
  encargo.
