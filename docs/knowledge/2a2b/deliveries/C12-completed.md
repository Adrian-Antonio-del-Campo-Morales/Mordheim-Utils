# C12 — Carga y acciones alternativas

**Cierre de los tres pendientes Netter, 2026-10-15.** La revisión del coordinador
(fila superior, histórico) queda atendida: se retiró todo enlace a
`mechanic.netter`/`aftermath._netter` y ninguna prueba invoca ya el helper
privado. Animal Fury, Bull Charge y las cláusulas compartidas de carga no se
reabrieron.

## Qué se implementó, qué se conectó y qué queda excluido

| Cláusula | Conectado | Excluido (por contenido de la fuente) |
|---|---|---|
| Kaz `whole--scope--netter` | registro propio `band--night-goblin-special-skills-netter` que declara la única consecuencia individual admitida, la víctima atrapada como `condition.netted` canónico (`catalog/rules/conditions.yaml`), consumido por estado, ataque y recuperación | lanzamiento de red (BS), prueba de Fuerza para escapar, carga fallida a 1" y colocación en el tablero: productor `scope NO` con motivo explícito |
| Crooked Moon `night-goblin-skills--scope--netter` | idéntico al anterior en su propia banda | idéntico |
| Ogre `netter` | cantidad/procedencia/destinatarios de las tres redes conservados como hechos impresos; retirado el binding incorrecto a la técnica goblin | suministro, reposición y transferencia no conceden por sí solos efecto de combate; su uso requiere el lanzamiento excluido. No se excluye por falta de binding/lista. La víctima ya atrapada puede suministrarse independientemente como condition.netted |

No se inventó estado ni acción: se reutiliza el contrato equivalente ya existente.
Los dos registros Night Goblin se declaran sin `grant` seleccionable, de modo que
la opción no aparece como elegible y la tirada excluida nunca se fabrica.

## Archivos propios

`special-rules.yaml` de las tres bandas,
`tests/python/construction/test_c12_charge_and_netter.py` y
`C12-completed.md`. `implemented-canonical-families.yaml` conserva sólo hunks de
Animal Fury/Bull Charge de la entrega anterior.

## Comprobación mínima

`pytest tests/python/construction/test_c12_charge_and_netter.py -q` → **16 passed,
EXIT=0** (`C:/Users/Pholtergate/AppData/Local/Temp/c12-netter-evidence.txt`):
víctima atrapada suministrada = derribada e impactada automáticamente con tirada
para herir, y corte de red con golpe último en su recuperación; los tres
registros no conceden técnica y son denegados al elegirse; el suministro Ogro no
enlaza binding y su posesión se rechaza como «not on any equipment list».
Esquema editorial de las tres bandas: 3 passed. `test_catalog.py` mantiene fallos
heredados de trabajo concurrente (recuentos y `band--fear-elves`), ninguno
menciona estas bandas ni Netter.

## CSV (sólo `query` + `prepare`)

Tres filas por `(id, clause_id)` en
`C:/Users/Pholtergate/AppData/Local/Temp/c12-netter-package.json` (cambios:
`…/c12-netter-changes.json`): Kaz y Crooked Moon pasan a
`condition.netted`/`related`/`pending {}` con consumidores reales y verificación
`executed`; Ogre pasa a `clause_scope NO`, `effect_id` vacío, `consumer []`,
`pending {}` y contrato semántico corregido. Huellas, textos y notas se
conservan (sólo se anexa nota). **No se ejecutó `apply --write`.**

**Integración del coordinador, 2026-10-16:** las tres filas fueron aplicadas con
propuesta nueva, snapshot íntegro, conservación de las 4.556 claves/textos/huellas/notas
y control concurrente (`%TEMP%/c12-netter-final-integration-zbvovs2j`). Corregido el
motivo de exclusión Ogre por contenido; pruebas focales reutilizadas sin repetirlas.
C12 cerrado, sin E2E, commit ni push.
