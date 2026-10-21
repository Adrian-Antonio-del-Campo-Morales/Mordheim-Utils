# G04 — Pools de ataques, equipo efectivo, daño y reacciones

## Prompt para lanzar el agente

Copia el bloque completo al lanzar el agente. Las condiciones de inicio forman parte del encargo; este prompt no autoriza saltarse sus dependencias.

```text
Realiza el encargo G04 (fase 1: implementación) del motor vectorial NumPy.

INFORMACIÓN QUE DEBES LEER
1. El fichero de trabajo completo:
   D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK\TMP_VECTORIAL_ENGINE_2A2B\G04_ATAQUES_EQUIPO_Y_REACCIONES.md
   Contiene archivos permitidos, referencias modulares exactas, trabajo concreto, comprobaciones,
   criterios de entrega y anexos con las claves principales y de apoyo que te corresponden.
2. El orden de ejecución y la propiedad de archivos:
   D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK\TMP_VECTORIAL_ENGINE_2A2B\README.md
3. El plan acordado de tres fases:
   D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK\TMP_VECTORIAL_ENGINE_2A2B\PLAN_IMPLEMENTACION.md
4. AGENTS.md y las instrucciones adicionales aplicables de la copia de trabajo.

Trabaja en la copia aislada asignada por el coordinador. Las rutas anteriores identifican el
repositorio original; si tu copia está en otra ubicación, resuelve los mismos archivos respecto
a su raíz. Conserva la base completa entregada, incluidos cambios todavía sin commit.

CONDICIÓN DE INICIO
Etapa C, tras G00 y G02; paralelo con G03/G05. Las conexiones a operadores nuevos se integran al reunir la tanda.
Comprueba la entrega de esas dependencias. Si falta alguna, comunica la dependencia concreta;
puedes avanzar con lectura o trabajo independiente, pero no inventes interfaces ni declares
completada una conexión que todavía no existe.

OBJETIVO CONCRETO
Implementar los pools y la resolución real de ataques, equipo efectivo, daño y reacciones que faltan en NumPy, siguiendo modular/pools.py, attacks.py, equipment.py y las reacciones inmediatas de aftermath.py. Conecta operadores y estado; conserva orden, límites, decisiones y gasto de recursos por fila. Portar equipo perdido, sustituido o inutilizado no puede modificar todo el lote si solo cambia una simulación. Devuelve los ganchos necesarios a G06.

REFERENCIAS Y COMPROBACIONES QUE DEBES REUTILIZAR
Trabaja en _attacks.py y _equipment.py. Usa las referencias exactas de resolución y equipo del encargo, y reutiliza test_rule_families_a.py/test_shared_families.py. No edites _operators.py, _types.py ni _driver.py: comunica al propietario la conexión necesaria.

INSTRUCCIONES QUE DEBES RESPETAR
- El motor modular se considera implementado y validado. Parte de su código y de los contratos
  aceptados. No vuelvas a interpretar las reglas ni a auditar su corrección. Consulta el consumidor
  modular de cada comportamiento y traslada su efecto completo a la ruta NumPy.
- En fase 1 céntrate en implementar y conectar las funcionalidades de tu encargo. Reutiliza lo
  existente y evita refactorizaciones ajenas, optimización anticipada y documentación adicional.
- Pruebas nuevas mínimas: cero si sirven las existentes; un escenario pequeño representativo
  como referencia habitual si hay un hueco. Más solo ante un defecto o hueco concreto que ese
  escenario no distingue, explicando por qué. No hagas un test por cláusula, no copies los E2E
  y no ocultes una batería masiva bajo una sola función parametrizada.
- No desarrolles nuevas pruebas modulares para acreditar NumPy. Usa las suites y expectativas
  existentes. En fase 1 ejecuta comprobaciones enfocadas; G07 realiza la campaña de paridad.
- Limita las modificaciones a los archivos autorizados en tu fichero. Para una conexión o cambio
  de tipos que pertenece a otro grupo, devuelve una propuesta concreta al propietario. Respeta
  las cesiones secuenciales del driver y el propietario único de cada archivo.
- Mantén estado, decisiones y recursos independientes por simulación. Un bucle que llama al
  duelo modular por cada fila o un fallback al modular no acredita implementación vectorial.
- El único registro de progreso es:
  D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK\sources\knowledge\verification\clause-contracts.csv
  Usa tools/knowledge/clause_registry.py para consultar las claves de tus anexos y leer contratos,
  condiciones, consumer, verification, notes y status. Agrupa consultas y referencias repetidas;
  no ejecutes miles de lecturas independientes ni generes otro CSV o manifiesto.
- No escribas el CSV compartido: devuelve propuestas por claves al coordinador. Preserva el
  estado nativo. Implementación integrada permite proponer implemented; verified requiere
  evidencia de paridad de G07. Una etiqueta presente o una prueba modular pasada no bastan.
- Las claves de apoyo también requieren tu contribución, aunque su cierre lo lleve otro grupo.
  No marques funcionalidad completada si falta la llamada desde el driver o su dependencia.
- Conserva trabajo concurrente. Si hay una discrepancia concreta, descríbela sin cambiar las
  reglas o expectativas para conseguir aprobación. No hagas commits ni pushes.

ENTREGA OBLIGATORIA EN FICHERO
Completa el trabajo autorizado que permita la base recibida y crea o actualiza:
TMP_VECTORIAL_ENGINE_2A2B/G04-deliverable.md
La ruta es relativa a la raíz de tu copia de trabajo. Este fichero de entrega está autorizado
además de los archivos de implementación permitidos. Es de tu propiedad exclusiva; no edites
los deliverables de otros grupos. No basta con responder en el chat.
Incluye: base/revisión utilizada; resumen de cambios; archivos y funciones modificados;
claves principales y de apoyo cubiertas; conexiones pendientes y propuestas concretas a otros
propietarios; comandos realmente ejecutados y resultados; casos nuevos y justificación;
bloqueos y limitaciones. Distingue implementado, integrado y comprobado. Propón cambios del
CSV por claves, conservando el estado nativo; no escribas el registro compartido.
Si el trabajo queda parcial o bloqueado, crea igualmente el fichero con lo completado y lo que
falta. Al reanudar, actualiza ese mismo documento conservando la evidencia válida, sin crear
copias de cierre. Solo documenta resultados ejecutados; no declares paridad por anticipado.
Al terminar, comunica al coordinador la ruta del fichero y un resumen breve. No crees otro CSV,
manifiesto o sistema de seguimiento. Sigue el criterio de entrega de tu encargo.
```

**Inicio:** Etapa C, tras G00 y G02; paralelo con G03/G05. Las conexiones a operadores nuevos se integran al reunir la tanda.

**Cláusulas principales:** 280. **Cláusulas de apoyo:** 57.

## Instrucciones obligatorias para el agente

- Este es un encargo futuro, no evidencia de trabajo realizado. El motor modular se considera implementado y validado.
- Parte de la implementación modular y de los contratos existentes. No reinterpretes reglas, no reclasifiques el alcance y no hagas otra auditoría del modular.
- Lee `AGENTS.md` y el plan `TMP_VECTORIAL_ENGINE_2A2B/PLAN_IMPLEMENTACION.md`. La raíz de trabajo es `D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK`.
- Antes de editar, comprueba base, cambios existentes y propiedad. Usa la copia aislada indicada por el coordinador, incluyendo sus cambios no confirmados. No partas de un HEAD que omita la base entregada.
- Modifica solo los archivos autorizados. Otro archivo se resuelve mediante una propuesta concreta al propietario, no mediante una edición simultánea. No hagas commits ni pushes.
- Reutiliza funciones y suites existentes. Pruebas nuevas mínimas: cero si bastan las actuales, un escenario pequeño como referencia habitual si hay un hueco; más solo por un motivo concreto. No añadir tests modulares, copiar E2E ni crear un test por cláusula. Una parametrización masiva no es un único comprobante a efectos de mantenimiento.
- No optimices durante fase 1 ni ejecutes la campaña completa de paridad por cada funcionalidad. La fase 2 y la fase 3 tienen sus encargos propios.
- No modifiques el CSV compartido. Devuelve claves, rutas y cambios de estado propuestos; el coordinador aplica mediante `clause_registry.py` y preserva `status.native`. En fase 1 solo se propone `implemented` tras conexión real; `verified` requiere G07.
- Conserva el código modular, KB, E2E y cambios ajenos. Si aparece una contradicción concreta, comunícala; no cambies expectativas para acomodar el portado.
- No inventes soporte por una etiqueta. Tampoco interpretes `pending` como prueba de que falta implementación: compara y reutiliza lo existente.

## Lectura de las claves del anexo

El anexo principal asigna responsabilidad de cierre, no equivalencia semántica ni obligación de escribir código nuevo. Cada clave principal pertenece exactamente a un fichero. Las claves de apoyo pertenecen a otro responsable y requieren una contribución de esta capa antes de cerrar el conjunto.

Obtén contrato, condiciones y evidencia vigentes mediante:

```powershell
python -X utf8 tools/knowledge/clause_registry.py query --id "ID_DEL_ANEXO" --clause-id "CLAUSULA_DEL_ANEXO" --fields id,clause_id,clause_scope,semantic_contract,effect_id,parameters,conditions,consumer,verification,notes,status --limit 1
```

Para varios registros, usa una consulta de la utilidad y filtra las claves exactas en memoria. Los anexos no duplican las reglas ni el progreso: el CSV sigue siendo la autoridad. Si cambian clave, alcance o consumidor desde la preparación, coordina la asignación; una variación de estado o nota no obliga a rehacer los encargos.

## Entrega al coordinador

Crea o actualiza `TMP_VECTORIAL_ENGINE_2A2B/G04-deliverable.md` en la raíz de tu copia de trabajo. Es la entrega persistente obligatoria de este grupo y está permitida además de los archivos de producción autorizados. No basta con un mensaje en el chat.

Incluye:

- Base/revisión utilizada y resumen del trabajo.
- Archivos y funciones cambiados.
- Claves principales y de apoyo cubiertas, indicando su estado real y las propuestas para el CSV.
- Conexiones pendientes y propuestas concretas a otros propietarios.
- Comandos ejecutados, resultados y evidencia aplicable; comprobaciones no ejecutadas identificadas como tales.
- Escenarios nuevos añadidos y por qué eran imprescindibles.
- Bloqueos, limitaciones y trabajo restante, si existen.

Distingue implementación, integración y verificación. Crea el fichero también ante una entrega parcial o bloqueada. En una reanudación, actualiza el mismo documento conservando evidencia válida. No edites entregas de otros grupos. Al terminar, comunica su ruta y un resumen breve al coordinador. Este documento no sustituye el CSV canónico ni autoriza modificarlo. No crees otro registro de seguimiento.

## Archivos permitidos y propiedad

- `TMP_VECTORIAL_ENGINE_2A2B/G04-deliverable.md` — documento de entrega obligatorio, propietario exclusivo G04.
- `packages/python/combat-engine/mordheim_combat/vectorized/_attacks.py`
- `packages/python/combat-engine/mordheim_combat/vectorized/_equipment.py`
- `tests/python/combat/vectorized/test_rule_families_a.py`
- `tests/python/combat/vectorized/test_shared_families.py`

Cualquier archivo no enumerado queda fuera de tu propiedad. Los módulos nuevos expresamente permitidos solo se crean si el portado los necesita. Los tests compartidos que no son tuyos se pueden ejecutar, pero no editar.

## Implementación de referencia que debes seguir

- `packages/python/combat-engine/mordheim_combat/modular/pools.py::_resolve_attack_pool`
- `packages/python/combat-engine/mordheim_combat/modular/pools.py::allocate_attack_weapons`
- `packages/python/combat-engine/mordheim_combat/modular/pools.py::pool_attack_weapons`
- `packages/python/combat-engine/mordheim_combat/modular/pools.py::_declared_unpredictable_attack`
- `packages/python/combat-engine/mordheim_combat/modular/attacks.py::resolve_reference_attack`
- `packages/python/combat-engine/mordheim_combat/modular/attacks.py::_resolve_wound_damage_body`
- `packages/python/combat-engine/mordheim_combat/modular/equipment.py::equipment_for_state`
- `packages/python/combat-engine/mordheim_combat/modular/aftermath.py::_react_to_wound`
- `packages/python/combat-engine/mordheim_combat/vectorized/_attacks.py::resolve_attacks`
- `packages/python/combat-engine/mordheim_combat/vectorized/_attacks.py::_resolve_weapon_once`
- `packages/python/combat-engine/mordheim_combat/vectorized/_equipment.py::phase_equipment`

Estas referencias son puntos de entrada; sigue sus llamadas para reproducir el comportamiento completo, sin releer las fuentes de reglas.

## Trabajo concreto

1. Portar desde pools y attacks la asignación de armas y ataques, sus condiciones, decisiones, recursos y resolución completa. Mantener el ataque auxiliar con sus propias propiedades, sin heredar bonos indebidos.
2. Conectar los resultados de G03 con la ejecución real: repeticiones, paradas, defensas, críticos, múltiples heridas, lesiones, mitigación y reacciones inmediatas.
3. Mantener la propiedad y el gasto del recurso por combatiente y simulación, incluyendo qué repetición consume qué derecho. Los efectos causados por herir o eliminar pueden producir reacciones antes de terminar el evento actual.
4. Portar pérdida, desarme, inutilización y sustitución de equipo, cambio de mano, equipo sin veneno y armas naturales. Proyectar el equipo por fila o por grupos equivalentes, nunca para todo el lote cuando solo cambia una fila.
5. Las mutaciones físicas se representan con G02. La selección de poderes o sustituciones al comienzo de fase y la planificación de Whipcrack/Deathblow se acuerdan con G06; este paquete ejecuta sus ataques y reacciones.
6. Entregar al coordinador cualquier modificación necesaria a `_types.py`, `_operators.py` o `_driver.py`. Esos archivos pertenecen a otros propietarios: no editarlos en la copia de entrega.

## Comprobación mínima

Reutilizar familias A, familias compartidas y casos existentes de ataques. Ejecutar selección enfocada; máximo habitual un escenario nuevo para una funcionalidad sin comprobante. No duplicar el corpus E2E ni diseñar pruebas por regla. Las matrices de paridad completas son G07.

## Criterio de entrega

La resolución NumPy consume realmente operadores, equipo y estado individuales y devuelve sus consecuencias. Los ganchos de rondas quedan descritos para G06 y ninguna capacidad se acredita por etiqueta sin ejecución.

## Claves principales asignadas

| id | clause_id | Apoyos | Referencia de asignación |
| --- | --- | --- | --- |
| `core/combat-critical-hits` | `basic-table` | — | consumer |
| `core/combat-critical-hits` | `critical-trigger` | G03 | consumer |
| `core/combat-critical-hits` | `damage-stacking` | — | consumer |
| `core/combat-injury-states` | `chart` | G03 | consumer |
| `core/combat-injury-states` | `highest-result` | G03 | consumer |
| `core/combat-two-weapons` | `mixed-weapons` | — | consumer |
| `item/black_lotus` | `whole` | G03 | consumer |
| `item/blood_root` | `whole` | — | consumer |
| `item/bone_helmet` | `behaves-as-a-helmet` | G03 | consumer |
| `item/bone_helmet_skink_priest_only` | `behaves-as-a-helmet` | G03 | consumer |
| `item/chained_squig` | `whole` | G03 | consumer |
| `item/cooking_pot_helmet` | `five-plus-against-stun` | G03 | consumer |
| `item/cutlass_sword` | `whole` | G03 | consumer |
| `item/dark_elf_blade_weapon_upgrade` | `whole` | G03 | consumer |
| `item/darksteel_blade` | `whole` | G03 | consumer |
| `item/disease_dagger` | `whole` | G03 | consumer |
| `item/draich` | `whole` | G03 | consumer |
| `item/eshin_assassin_clothes` | `behaves-as-eshin-assassin-robes` | G03 | consumer |
| `item/helmet` | `four-plus-against-stun` | G03 | consumer |
| `item/kusara_kama` | `whole` | G03 | consumer |
| `item/nightshade` | `whole` | G03 | consumer |
| `item/pistol_brace` | `whole` | G03 | consumer |
| `item/rapier` | `whole` | G03 | consumer |
| `item/spider_spit` | `whole` | — | consumer |
| `item/spirit_knife` | `whole--scope--profile` | G03 | consumer |
| `item/spirit_knife` | `whole--scope--spectral-touch` | G03 | consumer |
| `item/wolf_pelt_cloak` | `six-plus-saving-throw` | G03 | consumer |
| `mechanic/armour.eshin-assassin-robes` | `light-armour-six-plus-no-combining` | G03 | consumer |
| `mechanic/defence.cooking-pot-helmet` | `five-plus-against-stun` | G03 | consumer |
| `mechanic/defence.helmet` | `four-plus-against-stun` | G03 | consumer |
| `mechanic/defence.wolf-pelt-cloak` | `six-plus-saving-throw` | G03 | consumer |
| `mechanic/material.dark-elf-blade` | `whole` | G03 | consumer |
| `mechanic/mechanic.body-slam` | `whole` | G03 | consumer |
| `mechanic/mechanic.bull-charge` | `whole` | G03 | consumer |
| `mechanic/mechanic.ethereal-hit-save` | `four-plus-save-after-the-to-hit-roll` | G03 | consumer |
| `mechanic/mechanic.ethereal-hit-save` | `magical-attacks-bypass` | G03 | consumer |
| `mechanic/mechanic.hard-to-rattle` | `hard-to-rattle` | — | consumer |
| `mechanic/mechanic.honorable` | `whole` | — | consumer |
| `mechanic/mechanic.killing-blow` | `whole` | G03 | consumer |
| `mechanic/mechanic.marine-hunter` | `whole` | — | consumer |
| `mechanic/mechanic.ravening-onslaught` | `whole` | — | consumer |
| `mechanic/mechanic.seaguard-spear-master` | `first-round-strength-and-reroll` | G03 | consumer |
| `mechanic/mechanic.spider-infested` | `whole` | G03 | consumer |
| `mechanic/mechanic.titanic-strength` | `whole` | — | consumer |
| `mechanic/mechanic.torturer` | `torturer` | — | consumer |
| `mechanic/mechanic.unpredictable-attack` | `whole` | G03 | consumer |
| `mechanic/poison.black-lotus` | `whole` | G03 | consumer |
| `mechanic/poison.bloodroot` | `whole` | — | consumer |
| `mechanic/poison.manbane` | `whole` | G03 | consumer |
| `mechanic/poison.nightshade` | `whole` | G03 | consumer |
| `mechanic/poison.wolfsbane` | `whole` | G03 | consumer |
| `mechanic/preparation.tears-of-shallaya` | `immunity-to-all-poisons` | G03 | consumer |
| `mechanic/skill.art-of-silent-death` | `critical-5-6` | G03 | consumer |
| `mechanic/skill.crack-shot` | `whole` | G03 | consumer |
| `mechanic/skill.hardy-constitution` | `critical-ignored-on-five` | — | consumer |
| `mechanic/skill.knife-fighting` | `knife-fighting-bonus` | G03 | consumer |
| `mechanic/skill.luck` | `once-per-battle-reroll` | G02 | consumer |
| `mechanic/skill.strike-to-injure` | `whole` | G03 | consumer |
| `mechanic/skill.thick-skull` | `helmet-improves-to-two-and-replaces` | G03 | consumer |
| `mechanic/skill.thick-skull` | `stun-to-knocked-down-on-three` | G03 | consumer |
| `mechanic/skill.web-of-steel` | `whole` | — | consumer |
| `mechanic/weapon.arcane-candelabrum` | `whole` | G03 | consumer |
| `mechanic/weapon.brazier-iron` | `whole` | G03 | consumer |
| `mechanic/weapon.chained-squig` | `whole` | G03 | consumer |
| `mechanic/weapon.cutlass` | `whole` | G03 | consumer |
| `mechanic/weapon.disease-dagger` | `whole` | G03 | consumer |
| `mechanic/weapon.duelling-pistol` | `whole` | G03 | consumer |
| `mechanic/weapon.kusara-kama` | `whole` | G03 | consumer |
| `mechanic/weapon.misericordia` | `whole` | G03 | consumer |
| `mechanic/weapon.pistol` | `whole` | G03 | consumer |
| `mechanic/weapon.rapier` | `barrage` | — | consumer |
| `mechanic/weapon.skull-busta` | `whole` | G03 | consumer |
| `mechanic/weapon.spirit-knife` | `whole` | G03 | consumer |
| `mechanic/weapon.sword-breaker` | `whole` | G03 | consumer |
| `rule/catalog/general/skill.web-of-steel/skill.web-of-steel` | `whole` | — | consumer |
| `rule/catalog/warband/skill.chosen-of-the-white-tower/unclassified` | `parry-unarmed-and-reroll` | G03 | encargo explícito; consumer vacío |
| `rule/catalog/warband/skill.hardy-constitution/skill.hardy-constitution` | `critical-ignored-on-five` | — | consumer |
| `rule/catalog/warband/skill.instinctive-warrior/unclassified` | `parry-with-a-double-handed-weapon` | G03 | encargo explícito; consumer vacío |
| `rule/catalog/warband/skill.knife-fighting/skill.knife-fighting` | `knife-fighting-bonus` | G03 | consumer |
| `rule/catalog/warband/skill.luck/skill.luck` | `once-per-battle-reroll` | G02 | consumer |
| `rule/catalog/warband/skill.thick-skull/skill.thick-skull` | `helmet-improves-to-two-and-replaces` | G03 | consumer |
| `rule/catalog/warband/skill.thick-skull/skill.thick-skull` | `stun-to-knocked-down-on-three` | G03 | consumer |
| `rule/mordheim/adventurers-kaz/dwarf--hard-head/trait.concussion-immune` | `stub` | G03 | consumer |
| `rule/mordheim/adventurers-kaz/dwarf--hard-to-kill/skill.hard-to-kill` | `stub` | G03 | consumer |
| `rule/mordheim/adventurers-kaz/imperial-noble--honorable/mechanic.honorable` | `whole` | — | consumer |
| `rule/mordheim/battle-monks-of-cathay/raging-peasants--downtrodden/trait.injury-profile` | `immediate-out` | — | consumer |
| `rule/mordheim/battle-monks-of-cathay/raging-peasants--unarmed/profile.fist` | `whole` | — | consumer |
| `rule/mordheim/black-dwarfs/band--chaos-dwarf-special-skills-thick-skull/skill.thick-skull` | `helmet-improves-to-two` | G03 | consumer |
| `rule/mordheim/black-dwarfs/band--chaos-dwarf-special-skills-thick-skull/skill.thick-skull` | `thick-skull-save` | G03 | consumer |
| `rule/mordheim/black-orcs/band--black-orc-special-skills-ard-ead/skill.thick-skull` | `whole` | G03 | consumer |
| `rule/mordheim/blood-dragons-mou/grave-guards--immune-to-poisons/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/blood-dragons-mou/grave-guards--killing-blow/mechanic.killing-blow` | `whole` | G03 | consumer |
| `rule/mordheim/blood-dragons-mou/hell-hounds--immune-to-poisons/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/blood-dragons-mou/skeleton-warriors--immune-to-poisons/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/blood-dragons-mou/vampire--immune-to-poisons/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/blood-dragons-mou/wights--immune-to-poisons/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/blood-dragons-mou/wights--killing-blow/mechanic.killing-blow` | `whole` | G03 | consumer |
| `rule/mordheim/brood-of-ghurash-the-sc/band--skill-titanic-strength/mechanic.titanic-strength` | `whole` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/cairn-wraith--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | G03 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/cairn-wraith--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/malignant-spirits--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | G03 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/malignant-spirits--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/mourngul--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | G03 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/mourngul--haunter-of-the-dark/unimplemented.call-of-the-night-haint-mim.mourngul.haunter-of-the-dark` | `ethereal-improved` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/mourngul--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/mourngul--ravening-onslaught/mechanic.ravening-onslaught` | `whole` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/poltergeists--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | G03 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/poltergeists--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/poltergeists--incorporeal/trait.injury-profile` | `immediate-out` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/revenants--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/spirit-hosts--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | G03 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/spirit-hosts--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/spirit-hosts--spectral-touch/trait.spectral-touch` | `whole` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/tomb-banshee--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | G03 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/tomb-banshee--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/carnival-of-chaos/band--blessings-of-nurgle-nurgles-rot/trait.poison-immune` | `poison-immunity` | G03 | consumer |
| `rule/mordheim/carnival-of-chaos/nurglings--immune-to-poison/trait.poison-immune` | `poison-immunity` | G03 | consumer |
| `rule/mordheim/carnival-of-chaos/plague-bearers--immune-to-poison/trait.poison-immune` | `poison-immunity` | G03 | consumer |
| `rule/mordheim/channel-rats-mim/domnu--bear-hug/unimplemented.channel-rats-mim.domnu.bear-hug` | `bear-hug` | — | consumer |
| `rule/mordheim/channel-rats-mim/domnu--bear-hug/unimplemented.channel-rats-mim.domnu.bear-hug` | `replaces-normal-attacks` | — | consumer |
| `rule/mordheim/clan-angrund-kep/band--dwarf-special-skills-thick-skull/skill.thick-skull` | `whole` | G03 | consumer |
| `rule/mordheim/clockworkers-sc/band--constructs/unimplemented.clockworkers-sc.band.constructs` | `constructs-ignore-pain` | G03 | encargo explícito; consumer vacío |
| `rule/mordheim/clockworkers-sc/band--constructs/unimplemented.clockworkers-sc.band.constructs` | `constructs-poison-immunity` | G03 | encargo explícito; consumer vacío |
| `rule/mordheim/crooked-moon-kep/troll--vomit-attack/weapon.vomit-attack` | `whole` | G03 | consumer |
| `rule/mordheim/cult-of-the-possessed/band--mutations-blackblood/trait.acid-blood` | `whole--scope--acid-blood` | — | consumer |
| `rule/mordheim/cursed-cavalcade/band--cursed-cavalcade-special-skills-torturer/mechanic.torturer` | `torturer` | — | consumer |
| `rule/mordheim/dwarf-rangers/band--dwarf-special-skills-thick-skull/skill.thick-skull` | `whole` | G03 | consumer |
| `rule/mordheim/dwarf-slayer-cult-web/rememberer--rememberer/unimplemented.dwarf-slayer-cult-web.rememberer.rememberer` | `once-per-game-reroll-aura` | — | consumer |
| `rule/mordheim/dwarf-slayers-kaz/rememberer--rememberer/unimplemented.dwarf-slayers-kaz.rememberer.rememberer` | `duelist-reroll` | — | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-thick-skull/skill.thick-skull` | `whole` | G03 | consumer |
| `rule/mordheim/fallen-the-rel/revenant--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/fen-guard-mim/band--hard-to-rattle/mechanic.hard-to-rattle` | `hard-to-rattle` | — | consumer |
| `rule/mordheim/fen-guard-mim/band--immune-to-drugs-and-poison/trait.poison-immune` | `immune-to-drugs-and-poison` | G03 | consumer |
| `rule/mordheim/ghost-pirates-sar/gibbets--iron-cage/profile.equipment-restrictions` | `intrinsic-save` | G03 | consumer |
| `rule/mordheim/grave-robbers-sylv/band--special-skill-hardy-constitution/trait.poison-immune` | `immune-to-disease-and-poison` | G03 | consumer |
| `rule/mordheim/halflings-mic/halfling-elder--shifty/skill.shifty` | `bonus-first-strike-when-charged` | G03 | consumer |
| `rule/mordheim/kislevites/trained-bear--bear-hug/special-rule.trained-bear--bear-hug` | `whole` | — | consumer |
| `rule/mordheim/lothern-sea-patrol-sar/seaguards--spear-master/mechanic.seaguard-spear-master` | `first-round-strength-and-reroll` | G03 | consumer |
| `rule/mordheim/lustrian-reavers/conqueror--survivor/trait.survivor` | `cannot-be-out-while-standing` | G03 | consumer |
| `rule/mordheim/maneaters/band--ogres-special-skills-bull-charge/mechanic.bull-charge` | `whole` | G03 | consumer |
| `rule/mordheim/maneaters/bulls--bull-charge/mechanic.bull-charge` | `whole` | G03 | consumer |
| `rule/mordheim/masters-of-horror-sylv/flesh-construct--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/mordheim/masters-of-horror-sylv/the-bitten--transform/unimplemented.masters-of-horror-sylv.the-bitten.transform` | `transformation-equipment-loss` | G02 | consumer |
| `rule/mordheim/masters-of-horror-sylv/thrall--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/mordheim/masters-of-horror-sylv/zombies--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/mordheim/mazzalupo-web/master-of-finances--corruption/unimplemented.mazzalupo-web.master-of-finances.corruption` | `corruption--scope--attack-reroll` | — | consumer |
| `rule/mordheim/mazzalupo-web/master-of-finances--corruption/unimplemented.mazzalupo-web.master-of-finances.corruption` | `corruption--scope--psychology-immunity-limit` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/abomination--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/necrarch-vampire--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/skeletal-warrior--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/thrall--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/zombie--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/night-goblins-kaz/troll--vomit-attack/weapon.vomit-attack` | `whole` | G03 | consumer |
| `rule/mordheim/night-goblins-mic/troll--vomit-attack/weapon.vomit-attack` | `whole` | G03 | consumer |
| `rule/mordheim/night-goblins-web/troll--vomit-attack/weapon.vomit-attack` | `whole` | G03 | consumer |
| `rule/mordheim/nipponese-expedition-web/ashigaru--wall-of-steel/unimplemented.nipponese-expedition-web.ashigaru.wall-of-steel` | `two-handed-spear-gains-parry` | G03 | encargo explícito; consumer vacío |
| `rule/mordheim/orc-mob/band--orc-special-skills-ard-ead/skill.thick-skull` | `whole` | G03 | consumer |
| `rule/mordheim/orc-mob/troll--vomit-attack/weapon.vomit-attack` | `whole` | G03 | consumer |
| `rule/mordheim/ostlanders/band--ostlander-special-skills-bull-rush/mechanic.bull-charge` | `whole` | G03 | consumer |
| `rule/mordheim/pirates/band--pirate-special-skills-hardy-constitution/skill.hardy-constitution` | `critical-ignored-on-five` | — | consumer |
| `rule/mordheim/pit-fighters/band--pit-fighter-skill-body-slam/mechanic.body-slam` | `whole` | G03 | consumer |
| `rule/mordheim/restless-dead/grave-guards--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/restless-dead/grave-guards--wight-blades/trait.wight-blades` | `whole` | G03 | consumer |
| `rule/mordheim/restless-dead/liche--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/restless-dead/scarecrows--construct/trait.injury-reroll-out` | `reroll-injury` | G03 | consumer |
| `rule/mordheim/restless-dead/scarecrows--flammable/trait.caught-fire-threshold` | `caught-fire-three-plus` | — | consumer |
| `rule/mordheim/restless-dead/scarecrows--flammable/trait.flammable` | `flammable` | — | consumer |
| `rule/mordheim/restless-dead/scarecrows--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/restless-dead/skeletons--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/restless-dead/wights--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/restless-dead/zombies--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/skaven-clan-pestilens/band--clan-pestilens-special-skills-contagious/unimplemented.skaven-clan-pestilens.band.clan-pestilens-special-skills-contagious` | `contagious-reaction` | — | consumer |
| `rule/mordheim/skaven-clan-pestilens/band--clan-pestilens-special-skills-rotten-body/trait.poison-immune` | `poison-immunity` | G03 | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-rat--plague-infested/poison.black-lotus` | `whole` | G03 | consumer |
| `rule/mordheim/snotlings-web/bullied-goblin--achilles-heel/unimplemented.snotlings-web.special.achilles-heel` | `criticals-and-charge--scope--stampede-armour-denial` | — | consumer |
| `rule/mordheim/sons-of-hashut/band--chaos-dwarfs-special-skills-thick-skull/skill.thick-skull` | `helmet-improves-to-two-and-replaces` | G03 | consumer |
| `rule/mordheim/sons-of-hashut/band--chaos-dwarfs-special-skills-thick-skull/skill.thick-skull` | `stun-to-knocked-down-on-three` | G03 | consumer |
| `rule/mordheim/strigoi-kaz/fell-bats--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/mordheim/strigoi-kaz/skeletons--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/mordheim/survivors-of-strigos-sylv/strigoi-vampire--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/mordheim/tomb-guardians/acolytes--undead/unimplemented.tomb-guardians.acolytes.undead` | `undead` | G03, G05 | encargo explícito; consumer vacío |
| `rule/mordheim/tomb-guardians/band--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/mordheim/tomb-guardians/tomb-lord--flammable/trait.flammable` | `fire-doubles-wounds` | — | consumer |
| `rule/mordheim/tomb-guardians/tomb-scorpions--scorpion-sting/poison.black-lotus` | `whole` | G03 | consumer |
| `rule/mordheim/undead/dire-wolves--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/undead/vampire--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/undead/zombies--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/mordheim/underworld-alliance-mim/goblin-stinky-gits--disgusting/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/mordheim/underworld-alliance-mim/warpstone-troll--vomit-attack/weapon.vomit-attack` | `whole` | G03 | consumer |
| `rule/mordheim/watchmen-mim/turnkeys--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-thick-skull/skill.thick-skull` | `whole` | G03 | consumer |
| `rule/trollheim/chaos-streets-greenskins/band--orc-special-skills-ard-ead/skill.thick-skull` | `whole` | G03 | consumer |
| `rule/trollheim/chaos-streets-greenskins/troll--troll-vomit/weapon.vomit-attack` | `whole` | G03 | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/band--pit-fighter-skill-body-slam/mechanic.body-slam` | `whole` | G03 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/blood-dragon-vampire--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/dire-wolf--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/lahmia-vampire--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/necrarch-vampire--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/strigoi-vampire--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/vampire-bat--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/vampire-bat--summoned-creature/trait.injury-profile` | `immediate-out-of-action` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/von-carstein-vampire--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/zombie--immune-to-poison/trait.poison-immune` | `whole` | G03 | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/shadowed--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/trollheim/khemri-hobgoblin-raiders/band--hobgoblin-special-skills-unpredictable/mechanic.unpredictable-attack` | `whole` | G03 | consumer |
| `rule/trollheim/khemri-hobgoblin-raiders/sneaky--unpredictable/mechanic.unpredictable-attack` | `whole` | G03 | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/band--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/skeleton-warriors--undead/unimplemented.khemri-lahmian-brotherhood.skeleton-warriors.undead` | `undead` | G03, G05 | encargo explícito; consumer vacío |
| `rule/trollheim/khemri-mages/mechanical-beast--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/trollheim/khemri-necromancers/band--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/trollheim/khemri-necromancers/nehekharan-vultures--fragile/trait.injury-profile` | `fragile-injury-profile` | — | consumer |
| `rule/trollheim/khemri-necromancers/skeleton-warriors--undead/unimplemented.khemri-necromancers.skeleton-warriors.undead` | `undead` | G03, G05 | encargo explícito; consumer vacío |
| `rule/trollheim/khemri-thieves-guild/band--guild-special-skills-knife-fighting/skill.knife-fighting` | `knife-fighting-bonus` | G03 | consumer |
| `rule/trollheim/khemri-tomb-guardians/band--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/trollheim/khemri-tomb-guardians/stone-golem--animated/unimplemented.khemri-tomb-guardians.stone-golem.animated` | `animated` | G03, G05 | encargo explícito; consumer vacío |
| `rule/trollheim/khemri-tomb-guardians/stone-golem--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/trollheim/khemri-tomb-guardians/tomb-lord--flammable/trait.flammable` | `fire-doubles-wounds` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/tomb-scorpions--scorpion-sting/poison.black-lotus` | `whole` | G03 | consumer |
| `rule/trollheim/lustria-clan-pestilens/band--clan-pestilens-special-skills-contagious/trait.contagious` | `contagious-reaction` | — | consumer |
| `rule/trollheim/lustria-clan-pestilens/band--clan-pestilens-special-skills-rotten-body/trait.poison-immune` | `immune-to-poison-and-disease` | G03 | consumer |
| `rule/trollheim/lustria-high-elves/band--high-elf-special-skills-luck/skill.luck` | `once-per-battle-reroll` | G02 | consumer |
| `rule/trollheim/lustria-pirates/band--pirate-special-skills-hardy-constitution/skill.hardy-constitution` | `critical-ignored-on-five` | — | consumer |
| `rule/trollheim/lustria-pygmies/cannibals--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/trollheim/lustria-savage-goblins/band--savage-goblin-special-skills-spider-infested/mechanic.spider-infested` | `whole` | G03 | consumer |
| `rule/trollheim/lustria-savage-goblins/band--savage-goblin-special-skills-unpredictable/mechanic.unpredictable-attack` | `whole` | G03 | consumer |
| `rule/trollheim/lustria-savage-goblins/zomblins--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/trollheim/lustria-savage-goblins/zomblintua--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/trollheim/trollheim-cult-of-the-possessed/band--mutations-acid-blood/trait.acid-blood` | `whole--scope--acid-blood` | — | consumer |
| `rule/trollheim/trollheim-undead/dire-wolves--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/trollheim/trollheim-undead/vampire--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `rule/trollheim/trollheim-undead/zombies--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G03 | consumer |
| `source/bands/mordheim/crooked-moon-kep/equipment-access.yaml/@/equipment_lists/1/items/0/notes/unclassified` | `whole` | G03 | consumer |
| `source/bands/mordheim/militiant-mootlanders-mim/equipment-access.yaml/@/equipment_lists/0/items/16/notes/unclassified` | `cooking-pot-counts-as-a-helmet` | G03 | consumer |
| `source/bands/mordheim/militiant-mootlanders-mim/equipment-access.yaml/@/equipment_lists/0/items/21/notes/unclassified` | `whole` | — | consumer |
| `source/bands/mordheim/militiant-mootlanders-mim/equipment-access.yaml/@/equipment_lists/1/items/9/notes/unclassified` | `cooking-pot-counts-as-a-helmet` | G03 | consumer |
| `source/bands/mordheim/skaven-of-clan-pristekk-sc/equipment-access.yaml/@/equipment_lists/2/items/0/notes/unclassified` | `weapon-note--scope--cannot-be-parried` | — | encargo explícito; consumer vacío |
| `source/bands/mordheim/skaven-of-clan-pristekk-sc/equipment-access.yaml/@/equipment_lists/2/items/0/notes/unclassified` | `weapon-note--scope--plus-one-enemy-armour-save` | G03 | encargo explícito; consumer vacío |
| `source/bands/trollheim/lustria-savage-goblins/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `equipment-prohibition--scope--equipment-loss` | — | consumer |
| `source/catalog/campaign/exploration-and-income.yaml/campaign.magical-artefact.count-of-ventimiglias-misericordia/unclassified` | `misericordia-injury` | G00, G03 | consumer |
| `source/catalog/campaign/mutations.yaml/campaign.mutation.blackblood/unclassified` | `trigger-scope` | — | consumer |
| `source/catalog/campaign/mutations.yaml/campaign.mutation.blackblood/unclassified` | `whole` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/core.yaml/hireling.dramatis.veskit.rule.no-pain/unclassified` | `ignores-knocked-down-and-stunned` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/core.yaml/hireling.dramatis.veskit.rule.no-pain/unclassified` | `remains-until-last-wound` | G03 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1a.yaml/hireling.dramatis.countess-marianna-chevaux-vampire-assassin.rule.immune-to-poison/unclassified` | `immune-to-poison` | G03 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1a.yaml/hireling.dramatis.countess-marianna-chevaux-vampire-assassin.rule.no-pain/unclassified` | `ignores-knocked-down-and-stunned` | G03 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.crow-master-the.rule.crow-master/unclassified` | `needle-and-thread--scope--mouth-sewn` | G02, G05 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.heinrich-altdorf-schmidt.rule.luck/unclassified` | `luck-re-roll` | G02 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.khar-mel-the-djinn.rule.djinn-s-luck/unclassified` | `djinn-s-luck-ward-save` | G03 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/@/profiles/4/unresolved_references/0/unclassified` | `item` | G03 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.sigmund-spindle-the-harvester-of-flesh.rule.immune-to-poison/unclassified` | `immune-to-poison` | G03 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.sigmund-spindle-the-harvester-of-flesh.rule.no-pain/unclassified` | `ignores-knocked-down-and-stunned` | G03 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.sigmund-spindle-the-harvester-of-flesh.rule.no-pain/unclassified` | `remains-until-last-wound` | G03 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-foole.rule.poison-ring/unclassified` | `whole` | G03 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-foole.rule.unhinged/unclassified` | `psychology-immunity` | G03, G05 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-headless-horseman.rule.undead/unclassified` | `undead` | G03, G05 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-1a.yaml/hireling.hired-sword.imperial-assassin.rule.backstabber/unclassified` | `unseen-charge-bonus` | G03 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/@/profiles/28/unresolved_references/0/unclassified` | `whole` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.clan-skryre-rat-ogre.rule.immune-to-poison/unclassified` | `immune-to-poison` | G03 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.gaoler.rule.inured-to-pain/unclassified` | `inured-to-pain-injury-modifier` | G03 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.snake-charmer.rule.immune-to-poison/unclassified` | `immune-to-poison` | G03 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.tomb-robber.rule.excellent-reflexes/unclassified` | `excellent-reflexes-reference` | G03 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.bone-goliath.rule.immune-to-poison/unclassified` | `immune-to-poison` | G03 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.chaos-centaur.rule.trample/unclassified` | `whole` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/@/profiles/17/unresolved_references/0/unclassified` | `equipment-access` | G02 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.chaos-fury.rule.daemonic-flesh/unclassified` | `daemonic-five-plus-save` | G03 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.chaos-fury.rule.daemonic-flesh/unclassified` | `magic-and-blessed-exceptions` | G03 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.chaos-fury.rule.daemonic-mind/unclassified` | `psychology-immunity` | G03, G05 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.cursed-hillman.rule.lycanthrope/unclassified` | `profile` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.dwarf-slayer-pirate.rule.slayer-pirate/unclassified` | `deathwish--scope--deathwish-psychology` | G03, G05 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.dwarf-slayer-pirate.rule.slayer-pirate/unclassified` | `hard-head` | G03 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.dwarf-slayer-pirate.rule.slayer-pirate/unclassified` | `hard-to-kill` | G03 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.weaponsmith.rule.maintenance/unclassified` | `equipment-maintenance-table` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr.pending-duel` | `augur-psychology-immunity` | G02, G03, G05 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr.pending-duel` | `augur-strength-reduction` | G02, G05 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.rule.strictures/defence.wolf-pelt-cloak` | `six-plus-saving-throw` | G03 | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.immune-to-poison-3/unclassified` | `poison-immunity` | G03 | encargo explícito; consumer vacío |
| `source/catalog/rules/special-rules.yaml/shared-rule.immune-to-poison/unclassified` | `whole` | G03 | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.no-pain-4/unclassified` | `ignore-pain` | G03 | encargo explícito; consumer vacío |
| `source/catalog/rules/special-rules.yaml/shared-rule.thick-skull/unclassified` | `whole` | G03 | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.undead/unclassified` | `undead` | G03, G05 | encargo explícito; consumer vacío |

## Claves de apoyo de otros responsables

| id | clause_id | Responsable principal | Referencia de asignación |
| --- | --- | --- | --- |
| `core/combat-critical-hits` | `one-per-phase` | G06 | consumer |
| `item/barbed_whip` | `whole` | G06 | consumer |
| `mechanic/dance.whirling-death` | `whole` | G06 | consumer |
| `mechanic/mechanic.anvil-head` | `whole--scope--special-attack` | G06 | consumer |
| `mechanic/mechanic.great-thirster` | `whole` | G06 | consumer |
| `mechanic/mechanic.wheelo-impact` | `whole` | G06 | consumer |
| `mechanic/mechanic.wraith-touch` | `whole` | G06 | consumer |
| `mechanic/poison.spider-spittle` | `whole` | G06 | consumer |
| `mechanic/skill.crude-belch-halfling` | `whole` | G06 | consumer |
| `mechanic/skill.shifty` | `whole` | G06 | consumer |
| `mechanic/skill.sweep` | `whole` | G06 | consumer |
| `mechanic/weapon.barbed-whip` | `whole` | G06 | consumer |
| `mechanic/weapon.beastlash` | `whipcrack` | G06 | consumer |
| `rule/mordheim/adventurers-kaz/barbarian--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/amazons-mordheim/totem-warriors--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/black-orcs/troll--vomit-attack/weapon.vomit-attack` | `whole` | G06 | consumer |
| `rule/mordheim/crooked-moon-kep/band--night-goblin-special-skills/unimplemented.crooked-moon-kep.band.night-goblin-special-skills` | `night-goblin-skills--scope--netter` | G06 | consumer |
| `rule/mordheim/cult-of-the-possessed/band--mutations-spines/trait.spines` | `whole--scope--spines` | G06 | consumer |
| `rule/mordheim/druchii-mic/witch-elves--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/grave-robbers-sylv/band--special-skill-instinctual-violence/unimplemented.grave-robbers-sylv.special-skill.instinctual-violence` | `fear-immunity` | G06 | consumer |
| `rule/mordheim/halflings-mic/halfling-elder--crude-belch/skill.crude-belch-halfling` | `whole` | G06 | consumer |
| `rule/mordheim/khorne-raiders-sar/cannibal-boys--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/masters-of-horror-sylv/the-bitten--transform/unimplemented.masters-of-horror-sylv.the-bitten.transform` | `transformed-unarmed-penalties` | G06 | consumer |
| `rule/mordheim/norse-explorers-btb/beserkers--berserkers/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/norse-explorers-lustria/beserkers--berserkers/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/ogre-hunting-party-web/band--ogre-hunting-skills/unimplemented.ogre-hunting-party-web.special.ogre-hunting-skills` | `bull-charge` | G06 | consumer |
| `rule/mordheim/ogre-hunting-party-web/ogre-hunter--dont-fight-with-eating-knives/unimplemented.ogre-hunting-party-web.ogre-hunter.dont-fight-with-eating-knives` | `unarmed-fighting-without-penalty` | G06 | consumer |
| `rule/mordheim/restless-dead/band--restless-dead-special-skills-wraith-touch/mechanic.wraith-touch` | `whole` | G06 | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-champion--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-priest--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/snotlings-web/wheelo--impact-hits/mechanic.wheelo-impact` | `whole` | G06 | consumer |
| `rule/mordheim/survivors-of-strigos-sylv/strigoi-vampire--great-thirster/mechanic.great-thirster` | `whole` | G06 | consumer |
| `rule/mordheim/watchmen-mim/private-sleuth--scryer/trait.re-roll-melee` | `melee-reroll` | G06 | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/lunatics--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/trollheim/khemri-necromancers/band--necromantic-modification-anvil-head/compiler.anvil-head` | `whole--scope--special-attack` | G06 | consumer |
| `rule/trollheim/lustria-amazons/amazon-totem-warriors--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/trollheim/lustria-norse/berserkers--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/trollheim/lustria-savage-goblins/red-teeth--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/trollheim/trollheim-cult-of-the-possessed/band--mutations-spines/trait.spines` | `whole--scope--spines` | G06 | consumer |
| `source/bands/mordheim/skaven-of-clan-pristekk-sc/equipment-access.yaml/@/equipment_lists/2/items/0/notes/unclassified` | `weapon-note--scope--whipcrack` | G06 | encargo explícito; consumer vacío |
| `source/catalog/campaign/exploration-and-income.yaml/campaign.magical-artefact.executioners-hood/unclassified` | `frenzy` | G06 | consumer |
| `source/catalog/campaign/mutations.yaml/campaign.mutation.tentacle/unclassified` | `whole` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.abdul-alhazred-the-mad-sorcerer.rule.eye-pendant/unclassified` | `eye-pendant` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.crow-master-the.rule.crow-master/unclassified` | `mantle-of-crows` | G06 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.drenok-johansen-wielder-of-the-great-axe.rule.axe-of-icefang/unclassified` | `icefang-axe` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.drenok-johansen-wielder-of-the-great-axe.rule.berserker/unclassified` | `whole` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.drenok-johansen-wielder-of-the-great-axe.rule.sabertooth-tiger-hide/unclassified` | `sabertooth-tiger-hide--scope--close-combat-save` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.heinrich-altdorf-schmidt.rule.whip-master/unclassified` | `whip-master-reroll` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.khar-mel-the-djinn.rule.djinn-s-curse/unclassified` | `djinns-curse` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-dark-jester-in-mordheim.rule.confound-and-confuse/unclassified` | `trick-babbling-banter` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-dark-jester-in-mordheim.rule.confound-and-confuse/unclassified` | `trick-sidestepper` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-dark-jester-in-mordheim.rule.confound-and-confuse/unclassified` | `trick-trip` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-dark-jester-in-mordheim.rule.trip/unclassified` | `whole` | G06 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.gaoler.rule.torturer-s-grapple/unclassified` | `whole` | G06 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.mule-skinner.rule.whip-master/unclassified` | `whip-master-reroll` | G06 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.dwarf-slayer-pirate.rule.slayer-pirate/unclassified` | `festooned-with-pistols--scope--festooned-pistols-melee` | G06 | encargo explícito; consumer vacío |
| `source/catalog/rules/conditions.yaml/campaign.condition.frenzy/trait.frenzy` | `frenzy` | G06 | consumer |

## Base de esta asignación

Preparación: 2026-10-21. HEAD: `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` más cambios locales actuales. CSV SHA-256: `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`. No es un certificado de ejecución.
