# C11 — Liderazgo y apoyo suministrado

Base: `D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK` (checkout compartido; sin commit, push ni cambios de índice/plan).

**Estado integrado: 14/14 cláusulas cerradas; Battle Tongue Norse completo.** El radio de 12″ ya estaba conectado y su evidencia se conservó; este incremento sustituye la aproximación estática `eligibility: [jarl]` por la cualificación real de líder actual.

## Capacidad implementada — Battle Tongue (`rule/trollheim/lustria-norse/band--norse-special-skills-battle-tongue`, `whole`)

| | Antes | Después |
|---|---|---|
| Cualificación | `eligibility: [jarl]`: sólo el Jarl, aproximación estática de perfil | `eligibility: [jarl]` **o** el estado suministrado `condition.current-warband-leader` (`eligible_condition_ids`), declarado por la regla y leído por la decisión compartida de destinatarios (`ruleRecipientsAdmit`) tanto al ofrecer la habilidad como al compilar |
| Líder suministrado | No admitido: otro Héroe Norse no podía seleccionar ni compilar | Un Berserker/Vasallo/Wulfen declarado líder actual selecciona, compila y presta Liderazgo a 10″; el mismo Héroe sin la condición es rechazado (`special rule is not available …`) |
| Regla Líder | La habilidad no la concedía | Igual: la posición la aporta (`condition.current-warband-leader` → `mechanic.leader-six` por el mapeo de ejecución) y la habilidad sólo enlaza `mechanic.leader-twelve`: amplía una regla Líder existente y no concede ninguna |

Transporte del hecho suministrado (reutilizable por Red Teeth, C02b, sin duplicar):
- configuración: `condition.current-warband-leader` en `catalog/rules/conditions.yaml`, su registro de mecánica en `catalog/mechanics/close-combat.yaml` y su mapeo `effect-set` → `mechanic.leader-six` en `catalog/mechanics/execution.yaml`; la regla declara `eligible_condition_ids` (miembro nuevo de `special-rules.yaml.schema.json`, con descripción);
- selección compartida: `condition_ids` viaja en los hechos del build (`eligibility.py::build_facts`) y `index.ts` la lee en `specialRuleOptions`, `selectableRuleOptions` y `specialRuleRestriction`; `bridge.ts` propaga el build y `_eligibility.js` se regeneró con `npm run build:eligibility`;
- compilación: `compile_fighter` valida la misma etapa `recipients`, así que la ruta de compilación y la de oferta coinciden;
- consumo: el laboratorio ya lista la condición nueva (`CombatCatalogue.conditions()`); ningún operador nuevo en el motor de combate.

## Archivos

Propios: `sources/knowledge/bands/trollheim/lustria-norse/special-rules.yaml` (registro Battle Tongue), `sources/knowledge/catalog/rules/conditions.yaml`, `sources/knowledge/catalog/mechanics/{close-combat,execution}.yaml`, `contracts/knowledge-editorial-v1/special-rules.yaml.schema.json`, `packages/typescript/domain/eligibility/{index,bridge}.ts`, `packages/python/roster-construction/mordheim_construction/{eligibility.py,_eligibility.js}` y `tests/python/combat/modular/test_c11_leadership_support.py`. Sin cambios en `leadership.py`: el consumo reutiliza `_supplied_provider`/`_leader_radius` existentes a través de `mechanic.leader-six`.

## Comprobación mínima (ejecutada)

`python -X utf8 -m pytest tests/python/combat/modular/test_c11_leadership_support.py -q` → **10 passed in 22.14s (exit 0)**, salida en `C:\Users\Pholtergate\AppData\Local\Temp\c11-supplied-leader-focal.txt`: el Jarl conserva su acceso normal y su radio de 12″; un Berserker declarado líder actual compila `{mechanic.leader-six, mechanic.leader-twelve}`, presta a 10″ y a 13″ no; el mismo Berserker sin la condición es rechazado; la lista de oferta (`available_special_rules`) contiene la habilidad sólo con la condición suministrada y también para el Jarl nativo. Además `test_t13_m4e_connections.py::test_leader_range_skills_widen_only_their_selected_bearer` → **1 passed (exit 0)**, `…\Temp\c11-supplied-leader-m4e.txt`, y `npm run typecheck` → **exit 0** (`…\Temp\c11-supplied-leader-typecheck.txt`). Contrato editorial: los casos seleccionados de `test_editorial_schemas.py` que validan el paquete Norse y los documentos de catálogo (incluidos `conditions.yaml`, `close-combat.yaml` y `execution.yaml`), más el gate de árboles en staging → **10 passed (exit 0)**, `…\Temp\c11-supplied-leader-schemas.txt` y `…\Temp\c11-supplied-leader-staged.txt`; el nuevo miembro `eligible_condition_ids` no aparece como declaración sin uso.

## CSV propuesto (sin `apply --write`)

**Integración del coordinador, 2026-10-16:** una fila aplicada con cierre de la condición pendiente, conservando las 4.556 claves, textos, huellas y notas mediante snapshot íntegro, preparación actualizada, preview y control concurrente. Artefactos en `C:\Users\PHOLTE~1\AppData\Local\Temp\c11-final-coordinator-uvpi5fn1`. Evidencia focal del ejecutor reutilizada, sin nueva batería. C11 queda integrado y cerrado; los fallos externos mencionados debajo no quedan certificados ni reparados por este cierre.

Solicitud `C:\Users\Pholtergate\AppData\Local\Temp\c11-supplied-leader-changes.json`; paquete validado `C:\Users\Pholtergate\AppData\Local\Temp\c11-supplied-leader-package.json` (`sha256 bce984267afc6bdfbd99aeea2f8224024812fe8ac265bdf67f298f11ba857d44`, una fila, coincidente con los bytes actuales del CSV; `prepare` exit 0 y vista previa `apply` sin `--write` exit 0, `…\Temp\c11-supplied-leader-preview.txt`). Propone `pending.work: none`, la cualificación suministrada en `parameters`/`conditions`, los consumidores de selección compartida en `consumer` y la evidencia ejecutada en `verification`, con la nota de reutilización para C02b.

## Limitaciones

- El hecho es suministrado: no se simula sucesión, elección de líder ni campaña, y no se admite una variante de líder suministrado para bandas sin la condición declarada.
- `test_t13_psychology_leadership.py::test_battle_tongue_widens_the_reikland_captains_supplied_radius` sigue fallando porque la banda `mercenaries` no publica hoy ningún registro Battle Tongue ni `leader-twelve`; es otro paquete y no se tocó.
- Fuera del encargo y no causado por este incremento: `tests/python/knowledge/test_editorial_schemas.py` informa fallos concurrentes en datos ajenos (`catalog/hirelings/hired-swords/core.yaml`, `catalog/items/combat-equipment.yaml` y entradas `skills/114`, `weapons/96-97`, `mechanics/176` de los catálogos de mecánicas, más hallazgos de estrictitud en mutaciones/`defs`/perfiles); mis registros nuevos no producen ningún problema en esa validación. No se investigan ni reparan aquí.
- Sin E2E, baterías globales, parity, cobertura, vectorial/nativo ni T14; sin commit ni push.
