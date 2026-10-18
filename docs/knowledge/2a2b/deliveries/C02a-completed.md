# C02a — Restricciones de equipo: reglas Mordheim (entrega)

**Cierre final del coordinador, 2026-10-17:** integradas las seis disposiciones del
remate, además de las catorce anteriores. C02a cerrado para construcción y duelo.
Snapshot completo, prepare/preview y apply --write correctos: 4.556 claves,
textos, huellas y notas conservados, evidencia previa acumulada y control
concurrente. Integración en `%TEMP%/c02a-final-coordinator-_75tjarh/`. Reutilizada
la evidencia final del ejecutor, sin repetir baterías. La observación de admisión
post-batalla queda fuera del cierre modular y no se presenta como corregida.

**Integración parcial del coordinador, 2026-10-17:** catorce propuestas aplicadas
con snapshot completo, conservación de 4.556 claves/textos/huellas/notas y control
concurrente. Consumidores y evidencia anteriores acumulados; pruebas del ejecutor
reutilizadas, sin repetir baterías. Evidencia: `%TEMP%/c02a-coordinator-1s1lalqv/`.
Tras esa primera integración quedaban seis filas pendientes: Nuttaz/loadout-prohibitions,
Ogre/equipment-restriction, Slayer/kit-restrictions, Black Orcs/no mounts,
Nuttaz/mandatory-charge y Vim-To/owned-equipment-ban. Todas se resolvieron en el
remate integrado arriba; no se cerraron anticipadamente por contratos parciales.

## Capacidades implementadas

1. **Prohibición de armas de disparo en selección directa.**
   `buildRestriction(boundEquipment)` decidía `ranged-weapons` contra una lista de dos
   pistolas de pólvora, mientras la oferta y el veredicto lo decidían por el *kind* del
   objeto. Consecuencia real: un `crossbow` seleccionado a mano sobrevivía a la cláusula
   impresa de Nuttaz, Sword Wardens, Nuttaz salvajes, Esqueletos Strigoi y Mercenarios de
   Malred. Ahora ese token usa el mismo predicado compartido (`tokenForbids` sobre los
   hechos canónicos) que la oferta, conservando los ids de mecánica de pólvora que el
   catálogo no publica como fila. Bundle regenerado con `npm run build:eligibility`.

2. **Halflings — `band--too-big`.**
   La regla era `LATER/NO` con efecto `unimplemented`, así que la prohibición no existía
   para ninguna superficie. Conectada como `profile.equipment-restrictions` con los cinco
   objetos impresos (`long_bow`, `elf_bow`, `handgun`, `hochland_long_rifle`,
   `blunderbuss`) y destinatarios explícitos: los seis perfiles Halfling. El Ogro de la
   Aldea queda fuera porque su propia lista imprime el Arco Largo (discriminador probado).

3. **Snotlings — `band--small-hands`.**
   Conectada como binding de perfil con los cinco objetos impresos y destinatarios
   Snotling + Goblin Apaleado; Shoota Teams es la única excepción nombrada y conserva su
   trabuco.

4. **Druchii — `band--disdain`.**
   Conectada como binding de perfil con el token `blackpowder`; la oferta, la selección
   directa y el kit portado rechazan trabuco y pistola, sin convertir la cláusula en una
   prohibición general de armas.

5. **Slayers y Ogre (evidencia reutilizada, sin cambios).**
   `band--slayer-rules` ya aplica `armour`, `constant-save-cloak` y `non-thrown-ranged`
   (incluye Axe Hurlers); el Amuleto de la Suerte no queda prohibido. `band--huuuuge`
   ya distingue armadura pesada (rechazada) de ligera (legal).

6. **Restricciones impresas ya conectadas y verificadas sin cambios de código.**
   Black Orc Nuttaz (armadura + disparo), Sword Wardens, Flayerkin (sólo Hooks; armadura
   del listado Madbrain legal), Madbrains (sin sección de armadura), Quartermasters,
   Daemon-Fimm (sin armas, armadura legal, ataque intrínseco intacto), Vim-To Mage (sólo
   bastón-contado-como-garrote y daga), Gobbo Boyz (arco), Wierdo (armadura), Silent
   Brotherhood (pólvora), Esqueletos Strigoi.

## Primeras catorce filas (integradas por el coordinador)

Propuesta preparada y validada con `t13_csv.py prepare` (preview; **no** se ejecutó
`--write`). Paquete: `D:\DEVEL\Mordheim\C02a-evidence\package2.json`. Se conservan
`consumer` y `verification` anteriores (unión) y las notas se anexan, nunca se reemplazan.
El coordinador ya las integró; se conservan aquí como registro de la evidencia.

| id | clause_id |
|---|---|
| `rule/mordheim/black-orcs/orc-nuttaz--savage/profile.equipment-restrictions` | `whole` |
| `rule/mordheim/halflings-mic/band--too-big/unimplemented.halflings-mic.band.too-big` | `whole` |
| `rule/mordheim/high-elves-lus/sword-wardens--equipment-restrictions/profile.equipment-restrictions` | `whole` |
| `rule/mordheim/khorne-raiders-sar/flayerkin--equipment-restrictions/profile.equipment-restrictions` | `whole` |
| `rule/mordheim/khorne-raiders-sar/madbrains--equipment-restrictions/profile.equipment-restrictions` | `whole` |
| `rule/mordheim/lords-of-the-marsh-mim/daemon-fimm--equipment-restrictions/profile.equipment-restrictions` | `whole` |
| `rule/mordheim/savage-orcs-kaz/gobbo-boyz--equipment-restrictions/profile.equipment-restrictions` | `whole` |
| `rule/mordheim/savage-orcs-kaz/nuttaz--equipment-restrictions/profile.equipment-restrictions` | `whole` |
| `rule/mordheim/silent-brotherhood-sc/band--the-silence/profile.equipment-restrictions` | `whole` |
| `rule/mordheim/strigoi-kaz/skeletons--equipment-restrictions/profile.equipment-restrictions` | `whole` |
| `rule/mordheim/snotlings-web/band--small-hands/unimplemented.snotlings-web.band.small-hands` | `whole` |
| `rule/mordheim/druchii-mic/band--disdain/unimplemented.druchii-mic.band.disdain` | `whole` |
| `rule/mordheim/dwarf-slayer-cult-web/axe-hurlers--born-marksmen/unimplemented.dwarf-slayer-cult-web.axe-hurlers.born-marksmen` | `non-thrown-missile-prohibition` |
| `source/bands/mordheim/savage-orcs-kaz/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` |

## Remate: seis filas de la selección original

1. **Nuttaz — carga obligatoria (`mandatory-charge`).** Reutiliza el contrato ya existente
   `condition.nuttaz-charge`: condición KB restringida al Orc Nuttaz nativo en
   `compiler.py` y exigida al inicio del duelo en `state.py`. Movimiento, búsqueda de
   visibilidad y selección de objetivo quedan excluidos por el propio texto del
   contrato; no se producen. Evidencia ejecutada: `test_canonical_nuttaz_only_supplied_required_attempt_is_compulsory`.
2. **Nuttaz — `whole--scope--loadout-prohibitions`.** Reutiliza la prohibición hermana
   `profile.equipment-restrictions` (armadura + disparo) ya probada; esta fila cubre solo
   ese alcance. Nada nuevo que implementar.
3. **Ogro — materiales.** El token `heavy-armour` ya decidía los materiales mediante
   `HEAVY_ARMOUR`; faltaba la prueba. Añadidos discriminadores: pesada, Ithilmar y
   Gromril rechazadas en oferta, selección directa y kit; ligera legal.
4. **Slayers — acceso legítimo a Lucky Charms.** Productor canónico determinado:
   `campaign.trading-post.lucky-charm` (sin restricciones de banda). Para que la excepción
   impresa sea seleccionable se añadió `lucky_charm` a `slayer-equipment-list` y
   `doomseeker-equipment-list` con su precio de mercado; el Amuleto se ofrece y compila
   para los cinco perfiles Slayer, la prohibición de armadura/capa constante se mantiene y
   el Memorialista queda fuera (la cláusula lo excluye).
5. **Black Orcs — prohibición de monturas.** Implementación nueva en construcción:
   `band--let-the-goons-do-the-work` declara `forbids: mounts` para `black-orc-boss`,
   `black-orcs` y `orc-nuttaz`; la etapa compartida rechaza el estado `mounted` suministrado
   y los Orcos normales conservan la montura que el mismo párrafo les concede. No se
   implementa movimiento ni combate montado.
6. **Vim-To Mage — `owned-equipment-ban`.** El `requires: profile.equipment-restrictions`
   queda satisfecho por el permiso KB (`allowed_kinds`: bastón/garrote y daga): posesión,
   selección directa y oferta rechazan espada, armadura y preparaciones, y el bastón y la
   daga compilan.

Propuesta CSV de estas seis filas preparada (preview) en
`D:\DEVEL\Mordheim\C02a-evidence\package3.json`; pendientes cerrados, `consumer` y
`verification` previos conservados y notas anexadas.

## Evidencia mínima ejecutada

- `tests/python/construction/test_c02a_equipment_restrictions.py` (72 casos): por cada
  perfil/cláusula comprueba las tres superficies — oferta (`profileOffer`), selección
  directa (etapa `boundEquipment` con los bindings automáticos que usa
  `compile_fighter`) y veredicto de kit portado (`validateConstruction`). Incluye
  discriminadores de destinatario y excepción: Ogro de la Aldea vs Halflings, Shoota
  Teams vs resto de Snotlings, Quartermasters/Flayerkin vs Madbrains, materiales Ogre,
  monturas Orco Negro vs Orco normal, Amuleto vs Memorialista y posesión del Vim-To.
- `test_canonical_nuttaz_only_supplied_required_attempt_is_compulsory` (1 caso,
  reutilizado): el contrato de carga obligatoria suministrada sigue vigente.
- `tests/python/construction/test_shared_eligibility.py` (23 casos): huella del bundle,
  fixtures de decisión y concurrencia.
- `npx tsc --noEmit` en `packages/typescript`: limpio.
- `vitest run tests/typescript/domain/shared-eligibility.test.ts`: 23/23.
- Esquema editorial de los paquetes tocados (`halflings-mic`, `savage-orcs-kaz`,
  `snotlings-web`, `druchii-mic`): 4/4.

## Archivos propios de este remate

- `packages/typescript/domain/eligibility/index.ts`: token `mounts` y su comprobación en
  la etapa `boundEquipment` (bundle regenerado con `npm run build:eligibility`).
- `sources/knowledge/bands/mordheim/black-orcs/special-rules.yaml`: `forbids: mounts`.
- `sources/knowledge/bands/mordheim/dwarf-slayer-cult-web/equipment-access.yaml`:
  `lucky_charm` en las listas Slayer y Doomseeker.
- `tests/python/construction/test_c02a_equipment_restrictions.py`: casos nuevos de
  materiales Ogre, monturas, excepción Slayer y posesión del Vim-To.

## Bloqueos y observaciones exactas

- Las catorce filas iniciales y las seis del remate están integradas. La excepción
  del Amuleto, los materiales Ogre y las demás consecuencias admitidas del bloque
  quedan resueltos en construcción y duelo.
- Fallos **ajenos y previos** en `tests/python/knowledge/test_editorial_schemas.py`
  (10): `norse-explorers-btb`, `hired-swords/core.yaml`, `combat-equipment`,
  `close-combat`, `execution`, vocabulario de execution, contrato estricto, registro de
  manuales, normalizador de nombres y gate del catálogo. Ninguno pertenece a los
  paquetes de C02a; no se tocaron.
- Varios objetos de disparo (`crossbow`, `long_bow`, `blunderbuss`, `sling`, `handgun`)
  no tienen mecánica ejecutable en el catálogo de combate, así que `compile_fighter`
  falla antes por "unknown mechanic". No es una fuga de legalidad: la prohibición se
  comprueba en la etapa de restricción que el compilador ejecuta y en el veredicto de
  kit. Implementar disparo/montura queda fuera de este encargo.
- El Amuleto de la Suerte ya está en las listas Slayer, pero el veredicto de kit de un
  objeto de mercado que no sea el Amuleto sigue siendo `equipment_not_permitted`; es el
  comportamiento general de los objetos de Trading Post en construcción, no de C02a.
- La asignación post-batalla (`KnowledgePort.warrior_equipment_restriction`) devuelve
  `null` para restricciones de etapa `profile` por diseño y no re-consulta
  `equipment_forbids`; la prohibición Slayer no se re-valida en esa ruta de campaña. Es
  un consumidor distinto del mismo binding (capa de admisión de roster) y no se modifica
  en este encargo; queda registrado como bloqueo ajeno exacto.
- Las filas CSV de `band--let-the-goons-do-the-work` y `vim-to-mage--tenants-of-the-order`
  conservan ids de efecto `unimplemented.*` que ya no existen en el KB: el binding real
  vive en la misma regla y el id permanece como identidad histórica de la fila.
