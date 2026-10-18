# C01a — Banshee de Necrarchs: Cold Steel (garrote y bendición)

**Estado: integrada y cerrada, 2026-10-17. C01a completo (27/27).** Los dos pendientes concretos están implementados y probados: el garrote
ordinario ya no se trata como metal y la excepción bendita se alcanza desde el productor
canónico suministrado, no desde una etiqueta inyectada. Se conservan íntegros la inmunidad a
drogas/venenos, Sweep y el orden de Iniciativa ausente.

## Garrote frente a maza metálica

`weapon.club` es ahora la identidad canónica del objeto: los ítems `club` y `ogre_club` la
declaran y `simulation-mappings.yaml` los mapea explícitamente. La mecánica conserva
`weapon.mace` y `concussion`, de modo que el comportamiento compartido de maza se reutiliza y
todo consumidor que lee `weapon.mace` sigue funcionando; sólo la identidad metálica es nueva.
`phases.cold_steel_metal_attack` añade `weapon.club` a las identidades no metálicas: un garrote
no puede dañar a la Banshee (sin modificador y `unharmed`), mientras maza y martillo conservan
`-1` al impacto y la capacidad de herir. La ruta selección → configuración → compilación →
ataque queda probada con el garrote que ofrece `amazons-lustria` (`offers` → ítem `club` →
`weapon.club` → contexto de ataque). Compatibilidad: `weapon.club` es la elección canónica del
garrote y `weapon.mace` sigue siendo una maza legal; los runts de snotlings actualizan su
selección canónica, sin convertir pruebas positivas en rechazos.

## Productor canónico de la bendición

El productor existente es `condition.blessed-weapon` (`catalog/rules/conditions.yaml`): la
consecuencia suministrada del Resultado 13 de Exploración, un `profile.item-modifiers` sobre el
slot nombrado (`blessed_weapon_slots`), con receptores Hermanas de Sigmar y Cazadores de Brujas.
Ese ejemplar añade ahora `attack.blessed` junto a `blessing.undead-possessed-on-two`. Cold Steel
lee el ataque entrante, así que sólo el arma bendita impacta sin el `-1` (objetivo 4 con WS
iguales) y sigue pudiendo herir; la otra mano del mismo portador conserva su tratamiento
ordinario (`-1`). No se simula lanzamiento ni campaña, y no se extiende la exención a todo el
portador.

## Admisión y archivos

La protección del coordinador se retiró de `sources/knowledge/registry/runtime-scope.yaml` y su
espejo `packages/typescript/domain/campaign/construction-tables.json` al completar ambas
consecuencias: las exclusiones vuelven a ser `gyrocopter` y `river-boat` (el recuento de
perfiles compilables recupera la Banshee). Archivos propios: `phases.py`, las cuatro piezas de
catálogo citadas, `runtime-scope.yaml`, el espejo JSON y los dos tests.

## Base, parche, CSV y evidencia

Coordinador: una fila aplicada con cierre del último pending, snapshot íntegro,
validación de conservación de 4.556 claves/textos/huellas/notas y control concurrente.
Artefactos: `C:\Users\PHOLTE~1\AppData\Local\Temp\banshee-final-integration-i5_wn8nb`.
Evidencia existente reutilizada, sin nueva batería; eliminado el problema resuelto.
La base del ejecutor fue reconstruida invirtiendo cambios y no es una instantánea
previa independiente: no se aplicó su parche completo ni se restauraron archivos.

Base y parche: `C:\Users\Pholtergate\AppData\Local\Temp\c01a-coldsteel-base\`
(`BASE-SHA256.txt`, `c01a-coldsteel.patch`; el parche aplica sobre la base y reproduce los
archivos finales, verificado en `…\c01a-coldsteel-apply`). El cambio se reconstruyó invirtiendo
las ediciones exactas de esta ronda, no desde HEAD.

CSV (sólo `query` + `prepare`, sin `--write`):
`…\t13-c01a-banshee-coldsteel-changes.json` → `…\t13-c01a-banshee-coldsteel-prepared.json`
(snapshot `4422d8e3…`, 1 cambio: `banshee--equipment-restrictions`/`whole` con `pending {}`,
verificación ejecutada y nota de cierre). El registro no tiene filas para
`banshee--immune-to-poisons` ni `banshee--cold-steel`; la herramienta no crea claves, así que
sus ids quedan anotados para el coordinador.

Evidencia: `…\c01a-coldsteel-c01a.txt` → **101 passed**;
`…\c01a-coldsteel-choices.txt` → **65 passed**; paridad del espejo (exclusiones verbatim y
perfil real) → **2 passed**. `…\c01a-coldsteel-schema.txt` → 298 passed y 10 fallos, todos en
entradas de otros escritores (`weapon.whip-tc14` y `weapon.steel-whip` sin `rules_source_url`,
`kind: equipment`, skills, `true_grit`); `simulation-mappings.yaml` sí pasa tras declarar
`engine_option: Club`. Fallos ajenos no tocados: mapeo de ítems de hirelings,
`defence.magic-acorn` y `skaven-of-clan-moulder-web/rat-ogres`. Pendientes exactos: ninguno de
Cold Steel; los ítems ambiguos `staff_club_mace`, `stone_axe_counts_as_a_club` y la llave
metálica no se reclasificaron. Sin E2E, parity, suites globales, commit ni push.
