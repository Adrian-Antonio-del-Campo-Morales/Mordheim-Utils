# C01b — Veneno intrínseco del Tomb Scorpion

**Estado: C01b cerrado, 21/21; integración CSV completada por el coordinador.** El pendiente único
de C01b y sus dos dependientes de C01c quedan cubiertos por la misma corrección.

## Implementación aplicada

La distinción se declara en el rider y no en el consumidor: el binding
`poison.black-lotus` del aguijón lleva `parameters.applies_to_own_attack: true`
en **los dos orígenes** que imprimen la frase —
`mordheim/tomb-guardians` y `trollheim/khemri-tomb-guardians` — con el contrato
correspondiente en `contracts/knowledge-editorial-v1/defs.schema.json`.
`profileEquipment` salta exactamente ese binding, de modo que el veneno deja de
entrar en `equipment_access`; `equipmentIssue` → `validateConstruction` →
`equipmentVerdictFor` niegan la posesión por acceso, sin caso especial por banda
ni por perfil. El consumidor Python se regeneró con `npm run build:eligibility`
(`--check` informa que está al día); `_eligibility.js` no se editó a mano.

Comportamientos conservados: el aguijón mantiene `poison.black-lotus` en el
ataque natural una sola vez (ausente de `global_effects`), la selección directa
del frasco se rechaza y el acceso comprado legítimo sigue intacto
(`mordheim/druchii-mic/witch-elves` ofrece y compila Black Lotus sobre su daga).
No hay filtro genérico de venenos: sólo cambia el binding que declara el rider.
El bucle de `equipmentIssue` que bloqueaba la integración lo cerró su propietario
(validaciones y `return null` fuera del bucle); no reescribí ese archivo.

## Comprobación ejecutada

- Los tres casos de C01b, en el árbol compartido:
  `test_the_sting_applies_black_lotus_without_equipping_it`,
  `test_the_intrinsic_rule_grants_no_equipment_access` y
  `test_a_profile_with_printed_access_keeps_its_purchased_poison` →
  **3 passed, 69 deselected** (exit 0), ejecutados contra el bundle regenerado.
- Sonda de ambos orígenes: ofertas `[]`, `poison.black-lotus` presente en
  `weapon.natural-attacks` y ausente de `global_effects`, veredicto
  `equipment_not_permitted` para `poison.black-lotus` y rechazo de la selección
  directa, **idéntico** en `mordheim/tomb-guardians` y en
  `trollheim/khemri-tomb-guardians`.
- Sin repetición de la comparación histórica base/trabajo; su resultado ya
  registrado (mismos fallos, tres casos nuevos verdes) sigue siendo el soporte
  del diff.

## CSV — integrado por el coordinador

`prepare` y `apply` en preview (sin `--write`) exit 0 sobre tres cambios con
`pending {}`: la fila de C01b (`…/mordheim/tomb-guardians/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified`, `whole`)
y las dos de C01c (`…/trollheim/khemri-tomb-guardians/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified`
y `rule/trollheim/khemri-tomb-guardians/tomb-scorpions--equipment-restrictions/profile.equipment-restrictions`).
El coordinador recargó el CSV y conservó un snapshot completo nuevo, acumuló la
verificación y los consumidores existentes, y ejecutó prepare, preview y apply
--write: tres filas actualizadas. Conservación de las 4.556 claves, textos,
huellas y notas y control concurrente correctos. Evidencia de integración en
`%TEMP%/c01b-final-coordinator-p51qbchj/`. Se reutilizaron los resultados focales
del ejecutor, sin repetir pruebas.

## Rutas

- Propuesta CSV: `D:\DEVEL\Mordheim\C01b-poison-evidence\c01b-poison-prepared-3.json`
  (cambios en `…\c01b-poison-changes.json`, preview en `…\apply-preview-3.txt`).
- Evidencia focal: `…\shared-3cases-final.txt` (los tres casos, ejecutados tras
  la última edición del KB; `…\shared-3cases.txt` es la misma corrida previa) y
  `…\probe-both-origins.txt` (ambos orígenes).
- Base y parche del núcleo: `D:\DEVEL\Mordheim\C01b-poison-base`,
  `…\C01b-poison-work` y `…\c01b-poison-increment.diff` (7 hunks), con huellas en
  `…\FINAL-POISON-SHA256.json`. La declaración del origen khemri se aplicó
  directamente sobre el árbol compartido y su incremento de 1 hunk está en
  `…\c01b-poison-khemri.diff` (sólo añade el parámetro; nadie más tocó ese archivo).

Sin E2E, sin suites amplias, sin commit ni push.
