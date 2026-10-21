# G06 — Rondas, recuperación, duración e integración completa

## Prompt para lanzar el agente

Copia el bloque completo al lanzar el agente. Las condiciones de inicio forman parte del encargo; este prompt no autoriza saltarse sus dependencias.

```text
Realiza el encargo G06 (fase 1: implementación) del motor vectorial NumPy.

INFORMACIÓN QUE DEBES LEER
1. El fichero de trabajo completo:
   D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK\TMP_VECTORIAL_ENGINE_2A2B\G06_RONDAS_RECUPERACION_E_INTEGRACION.md
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
Etapa D. Preparación de lectura permitida antes; empezar escritura del driver tras integrar G00/G02 y reunir G03/G04/G05.
Comprueba la entrega de esas dependencias. Si falta alguna, comunica la dependencia concreta;
puedes avanzar con lectura o trabajo independiente, pero no inventes interfaces ni declares
completada una conexión que todavía no existe.

OBJETIVO CONCRETO
Integrar el recorrido completo de rondas NumPy y portar la recuperación y efectos persistentes pendientes. Sigue modular/rounds.py::resolve_round, aftermath.py y alchemy.py. Conecta efectivamente G02/G03/G04/G05, en el orden del modular y con máscaras de acciones válidas. Mantén efectos de inicio/final, decisiones, caducidad, cargas, recursos, ataques especiales y respuestas. Un helper implementado que el driver no llama no completa la funcionalidad.

REFERENCIAS Y COMPROBACIONES QUE DEBES REUTILIZAR
Trabaja en _driver.py tras la cesión de sus propietarios anteriores. Reutiliza test_runtime_regressions.py/test_vectorized_engine.py y observaciones/replay existentes si hacen falta. Ejecuta comprobación de integración enfocada; la campaña estadística completa corresponde a G07, no a este encargo.

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
TMP_VECTORIAL_ENGINE_2A2B/G06-deliverable.md
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

**Inicio:** Etapa D. Preparación de lectura permitida antes; empezar escritura del driver tras integrar G00/G02 y reunir G03/G04/G05.

**Cláusulas principales:** 187. **Cláusulas de apoyo:** 0.

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

Crea o actualiza `TMP_VECTORIAL_ENGINE_2A2B/G06-deliverable.md` en la raíz de tu copia de trabajo. Es la entrega persistente obligatoria de este grupo y está permitida además de los archivos de producción autorizados. No basta con un mensaje en el chat.

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

- `TMP_VECTORIAL_ENGINE_2A2B/G06-deliverable.md` — documento de entrega obligatorio, propietario exclusivo G06.
- `packages/python/combat-engine/mordheim_combat/vectorized/_driver.py (propiedad exclusiva tras las cesiones de G00/G02)`
- `packages/python/combat-engine/mordheim_combat/vectorized/_recovery.py (solo si se necesita para separar recuperación)`
- `packages/python/combat-engine/mordheim_combat/vectorized/_alchemy.py (solo si se necesita para portar esa fase)`
- `tests/python/combat/vectorized/test_runtime_regressions.py`
- `tests/python/combat/vectorized/test_vectorized_engine.py`

Cualquier archivo no enumerado queda fuera de tu propiedad. Los módulos nuevos expresamente permitidos solo se crean si el portado los necesita. Los tests compartidos que no son tuyos se pueden ejecutar, pero no editar.

## Implementación de referencia que debes seguir

- `packages/python/combat-engine/mordheim_combat/modular/rounds.py::resolve_round`
- `packages/python/combat-engine/mordheim_combat/modular/rounds.py::select_shadow_dance`
- `packages/python/combat-engine/mordheim_combat/modular/rounds.py::select_shifty_weapon`
- `packages/python/combat-engine/mordheim_combat/modular/rounds.py::select_attack_replacement`
- `packages/python/combat-engine/mordheim_combat/modular/rounds.py::apply_opponent_leadership`
- `packages/python/combat-engine/mordheim_combat/modular/rounds.py::apply_round_weapon_attack_modifiers`
- `packages/python/combat-engine/mordheim_combat/modular/aftermath.py::_start_round_state`
- `packages/python/combat-engine/mordheim_combat/modular/aftermath.py::_fire_recovery`
- `packages/python/combat-engine/mordheim_combat/modular/aftermath.py::_force_of_will`
- `packages/python/combat-engine/mordheim_combat/modular/aftermath.py::_revenant_recovery`
- `packages/python/combat-engine/mordheim_combat/modular/alchemy.py::resolve_alchemist`
- `packages/python/combat-engine/mordheim_combat/vectorized/_driver.py::_simulate_batch_core`

Estas referencias son puntos de entrada; sigue sus llamadas para reproducir el comportamiento completo, sin releer las fuentes de reglas.

## Trabajo concreto

1. Reproducir el orden completo de `resolve_round` con los helpers y operadores entregados, incluyendo carga, jugador activo, contacto, fallos de carga, recuperaciones, psicología, selección de modos y ataques.
2. Conectar G02, G03, G04 y G05 a la ruta real. Conservar máscaras de combatientes activos y volver a evaluar elegibilidad después de fases que hieren, eliminan o bloquean acciones.
3. Portar recuperación y efectos temporales: fuego, Force of Will, regeneración de recuperación, pociones/alquimia, transformaciones, fases extra y consecuencias al inicio/final. Copiar el momento semántico y los límites del modular.
4. Integrar decisiones opcionales y duraciones/reutilización por simulación: Electrical Touch, Shifty, danzas, poderes, reemplazos y reacciones. Evitar efectos globales cuando las filas eligen o evolucionan de forma distinta.
5. Mantener Whipcrack, prioridad, ataques especiales, respuestas y consumo de slots en su orden correcto. Las cantidades/cálculos proceden de G03 y la ejecución de G04.
6. Mantener el resultado agregado y las observaciones públicas, simulación directa y paralela, límites de rondas y cancelación existentes. No confundir contar una ronda con haber ejecutado sus consecuencias.
7. Devolver propuestas al coordinador para retirar los rechazos NumPy de cada capacidad efectivamente conectada. Revisar todas las claves cruzadas antes de proponer `implemented`: ningún helper sin llamar cuenta como integrado.

## Comprobación mínima

Reutilizar los casos de runtime y simulación existentes, y observaciones/replay si es necesario. Como máximo habitual un caso nuevo que discrimine la secuencia faltante; no desplegar baterías exhaustivas. Ejecutar las comprobaciones de integración afectadas, no la campaña estadística completa de G07.

## Criterio de entrega

El alcance admitido queda conectado de extremo a extremo en NumPy. No quedan funciones implementadas pero sin llamar, efectos ignorados o fallback modular encubierto. Se entrega el conjunto integrado a G07 con filas propuestas como implemented.

## Claves principales asignadas

| id | clause_id | Apoyos | Referencia de asignación |
| --- | --- | --- | --- |
| `core/combat-critical-hits` | `one-per-phase` | G02, G04 | consumer |
| `core/combat-order` | `charge-before-initiative` | G03 | consumer |
| `core/combat-order` | `stood-up-strikes-last` | G03 | consumer |
| `item/barbed_whip` | `unprinted-modifiers` | — | consumer |
| `item/barbed_whip` | `whole` | G04 | consumer |
| `item/cat_o_nine_tails` | `whole` | G03 | consumer |
| `item/crimson_shade` | `whole` | G02, G03 | consumer |
| `item/obsidian_weapon` | `bearer-prohibition` | — | consumer |
| `item/serpent_staff` | `whole` | G03 | consumer |
| `item/steel_whip` | `whole` | G03 | consumer |
| `mechanic/dance.storm-of-blades` | `whole` | G03 | consumer |
| `mechanic/dance.the-shadows-coil` | `whole` | G03 | consumer |
| `mechanic/dance.whirling-death` | `whole` | G03, G04 | consumer |
| `mechanic/dance.woven-mist` | `whole` | G03 | consumer |
| `mechanic/mechanic.animal-friendship` | `whole--scope--animal-attack-protection` | — | consumer |
| `mechanic/mechanic.anvil-head` | `whole--scope--special-attack` | G03, G04 | consumer |
| `mechanic/mechanic.beauty-of-the-sea` | `whole` | G05 | consumer |
| `mechanic/mechanic.black-hunger` | `backlash` | — | consumer |
| `mechanic/mechanic.centigor-drunken` | `drunken` | — | consumer |
| `mechanic/mechanic.curse-of-the-revenant` | `whole` | — | consumer |
| `mechanic/mechanic.death-blow` | `optional-use` | — | consumer |
| `mechanic/mechanic.force-of-will` | `force-of-will` | — | consumer |
| `mechanic/mechanic.great-thirster` | `whole` | G04 | consumer |
| `mechanic/mechanic.hypnotist` | `hypnotist` | — | consumer |
| `mechanic/mechanic.mark-of-shornaal` | `whole` | — | consumer |
| `mechanic/mechanic.mesmerising-dance` | `whole` | G05 | consumer |
| `mechanic/mechanic.myrmidia-eagle-friend` | `whole` | — | consumer |
| `mechanic/mechanic.questing-vow` | `whole` | — | consumer |
| `mechanic/mechanic.rousing-sermon` | `self-attack-bonus` | — | consumer |
| `mechanic/mechanic.savage-fury` | `whole` | G03, G05 | consumer |
| `mechanic/mechanic.sigmar-enlightened` | `whole` | — | consumer |
| `mechanic/mechanic.spawn-special-attacks` | `whole` | G03 | consumer |
| `mechanic/mechanic.taal-tranquil-fauna` | `tranquil-fauna` | — | consumer |
| `mechanic/mechanic.wheelo-impact` | `charger-immunity--scope--charger-immunity` | — | consumer |
| `mechanic/mechanic.wheelo-impact` | `whole` | G04 | consumer |
| `mechanic/mechanic.wheelo-skill-modifications` | `whole--scope--mighty-blow` | — | consumer |
| `mechanic/mechanic.wheelo-skill-modifications` | `whole--scope--weapons-training-impact-modifications` | — | consumer |
| `mechanic/mechanic.wraith-touch` | `whole` | G03, G04 | consumer |
| `mechanic/poison.spider-spittle` | `whole` | G03, G04 | consumer |
| `mechanic/preparation.crimson-shade` | `whole` | G02, G03 | consumer |
| `mechanic/skill.blessed-sight` | `whole` | G03 | consumer |
| `mechanic/skill.crude-belch-halfling` | `whole` | G04 | consumer |
| `mechanic/skill.monstrous` | `whole` | G02 | consumer |
| `mechanic/skill.shifty` | `whole` | G03, G04 | consumer |
| `mechanic/skill.sigmar-s-sign` | `sigmar-s-sign` | — | consumer |
| `mechanic/skill.sweep` | `whole` | G03, G04 | consumer |
| `mechanic/weapon.barbed-whip` | `whole` | G04 | consumer |
| `mechanic/weapon.beastlash` | `whipcrack` | G04 | consumer |
| `mechanic/weapon.boar-spear` | `whole--scope--charging-enemy-loses-one-attack` | G03 | consumer |
| `mechanic/weapon.boar-spear` | `whole--scope--strikes-first` | G03 | consumer |
| `mechanic/weapon.long-daggers` | `whole` | G03 | consumer |
| `mechanic/weapon.pirate-scourge` | `whole` | G03 | consumer |
| `mechanic/weapon.serpent-staff` | `whole` | G03 | consumer |
| `mechanic/weapon.serpent-whip` | `whole` | G03 | consumer |
| `mechanic/weapon.steel-whip` | `whole` | G03 | consumer |
| `mechanic/weapon.vomit-attack` | `optional-declaration` | — | consumer |
| `mechanic/weapon.vomit-attack` | `whole` | G03 | consumer |
| `rule/catalog/warband/skill.head-crusher/skill.head-crusher` | `whole` | G03 | consumer |
| `rule/catalog/warband/skill.sigmar-s-sign/skill.sigmar-s-sign` | `sigmar-s-sign` | — | consumer |
| `rule/catalog/warband/skill.sweep/skill.sweep` | `whole` | G03 | consumer |
| `rule/mordheim/adventurers-kaz/barbarian--frenzy/trait.frenzy` | `frenzy` | G02, G03, G04, G05 | consumer |
| `rule/mordheim/amazons-lustria/band--amazon-special-skills-mesmerising-dance/mechanic.mesmerising-dance` | `whole` | — | consumer |
| `rule/mordheim/amazons-lustria/band--amazon-special-skills-savage-fury/mechanic.savage-fury` | `whole` | G03 | consumer |
| `rule/mordheim/amazons-mordheim/totem-warriors--frenzy/trait.frenzy` | `frenzy` | G02, G03, G04, G05 | consumer |
| `rule/mordheim/beastmen-raiders/centigors--drunken/mechanic.centigor-drunken` | `drunken` | — | consumer |
| `rule/mordheim/black-orcs/band--black-orc-special-skills-eadbasher/skill.head-crusher` | `whole` | G03 | consumer |
| `rule/mordheim/black-orcs/troll--vomit-attack/weapon.vomit-attack` | `whole` | G03, G04 | consumer |
| `rule/mordheim/bretonnian-chapel-guard/band--questing-vow/mechanic.questing-vow` | `whole` | — | consumer |
| `rule/mordheim/bretonnian-chapel-guard/knights-errant--impetuous/unimplemented.bretonnian-chapel-guard.knights-errant.impetuous` | `impetuous-avoid-compulsion` | G05 | consumer |
| `rule/mordheim/bretonnian-chapel-guard/knights-errant--impetuous/unimplemented.bretonnian-chapel-guard.knights-errant.impetuous` | `impetuous-movement` | G02, G05 | consumer |
| `rule/mordheim/channel-rats-mim/petru--potions/unimplemented.channel-rats-mim.petru.potions` | `random-pre-battle-potion` | G02 | consumer |
| `rule/mordheim/crooked-moon-kep/band--night-goblin-special-skills/unimplemented.crooked-moon-kep.band.night-goblin-special-skills` | `night-goblin-skills--scope--netter` | G02, G04 | consumer |
| `rule/mordheim/cult-of-the-possessed/band--mutations-spines/trait.spines` | `whole--scope--spines` | G04 | consumer |
| `rule/mordheim/cursed-cavalcade/band--cursed-cavalcade-special-skills-noblesse-obliges/unimplemented.cursed-cavalcade.band.cursed-cavalcade-special-skills-noblesse-obliges` | `noblesse-stomp` | — | consumer |
| `rule/mordheim/cursed-cavalcade/cursed-piper--danse-macabre/unimplemented.cursed-cavalcade.cursed-piper.danse-macabre` | `control-enemy--scope--danse-state` | — | consumer |
| `rule/mordheim/druchii-mic/witch-elves--frenzy/trait.frenzy` | `frenzy` | G02, G03, G04, G05 | consumer |
| `rule/mordheim/grave-robbers-sylv/band--special-skill-instinctual-violence/unimplemented.grave-robbers-sylv.special-skill.instinctual-violence` | `fear-immunity` | G04, G05 | consumer |
| `rule/mordheim/halflings-mic/halfling-elder--crude-belch/skill.crude-belch-halfling` | `whole` | G04 | consumer |
| `rule/mordheim/halflings-mic/halfling-elder--wizened-halfling/mechanic.wizened-halfling` | `whole` | — | consumer |
| `rule/mordheim/horned-hunters/band--horned-hunter-special-skills-animal-friendship/trait.animal-friendship` | `whole--scope--animals-never-attack` | — | consumer |
| `rule/mordheim/khorne-raiders-sar/cannibal-boys--frenzy/trait.frenzy` | `frenzy` | G02, G03, G04, G05 | consumer |
| `rule/mordheim/maneaters/band--ogres-special-skills-crude-belch/unimplemented.maneaters.band.ogres-special-skills-crude-belch` | `whole` | — | consumer |
| `rule/mordheim/maneaters/sabretusks--feral-instinct/unimplemented.maneaters.sabretusks.feral-instinct` | `feral-instinct--scope--leadership-test` | G05 | consumer |
| `rule/mordheim/marauders-of-chaos/band--mark-of-shornaal/mechanic.mark-of-shornaal` | `whole` | — | consumer |
| `rule/mordheim/marauders-of-chaos/spawn-of-chaos--special-attacks/mechanic.spawn-special-attacks` | `whole` | G03 | consumer |
| `rule/mordheim/masters-of-horror-sylv/mad-scientist--alchemist/unimplemented.masters-of-horror-sylv.special.alchemist` | `start-of-game-potion--scope--addiction-state` | G02 | consumer |
| `rule/mordheim/masters-of-horror-sylv/mad-scientist--alchemist/unimplemented.masters-of-horror-sylv.special.alchemist` | `start-of-game-potion--scope--potion-characteristic-bonuses` | G02 | consumer |
| `rule/mordheim/masters-of-horror-sylv/the-bitten--transform/unimplemented.masters-of-horror-sylv.the-bitten.transform` | `transformation-state--scope--transformation-duration` | G02 | consumer |
| `rule/mordheim/masters-of-horror-sylv/the-bitten--transform/unimplemented.masters-of-horror-sylv.the-bitten.transform` | `transformation-state--scope--transformation-state` | G02, G05 | consumer |
| `rule/mordheim/masters-of-horror-sylv/the-bitten--transform/unimplemented.masters-of-horror-sylv.the-bitten.transform` | `transformed-unarmed-penalties` | G04 | consumer |
| `rule/mordheim/night-goblins-web/band--mad-cap-masters/unimplemented.night-goblins-web.band.mad-cap-masters` | `mad-cap-masters` | G05 | consumer |
| `rule/mordheim/night-goblins-web/shaman--fungus-brew/unimplemented.night-goblins-web.shaman.fungus-brew` | `fungus-brew-production` | G02 | encargo explícito; consumer vacío |
| `rule/mordheim/night-goblins-web/shaman--fungus-brew/unimplemented.night-goblins-web.shaman.fungus-brew` | `fungus-loony` | G02, G05 | consumer |
| `rule/mordheim/night-goblins-web/shaman--fungus-brew/unimplemented.night-goblins-web.shaman.fungus-brew` | `fungus-rowdy` | — | consumer |
| `rule/mordheim/norse-explorers-btb/beserkers--berserkers/trait.frenzy` | `frenzy` | G02, G03, G04, G05 | consumer |
| `rule/mordheim/norse-explorers-lustria/beserkers--berserkers/trait.frenzy` | `frenzy` | G02, G03, G04, G05 | consumer |
| `rule/mordheim/ogre-hunting-party-web/band--ogre-hunting-skills/unimplemented.ogre-hunting-party-web.special.ogre-hunting-skills` | `bull-charge` | G04 | consumer |
| `rule/mordheim/ogre-hunting-party-web/band--ogre-hunting-skills/unimplemented.ogre-hunting-party-web.special.ogre-hunting-skills` | `crude-belch` | — | consumer |
| `rule/mordheim/ogre-hunting-party-web/ogre-hunter--dont-fight-with-eating-knives/unimplemented.ogre-hunting-party-web.ogre-hunter.dont-fight-with-eating-knives` | `unarmed-fighting-without-penalty` | G03, G04 | consumer |
| `rule/mordheim/orc-mob/band--orc-special-skills-eadbasher/skill.head-crusher` | `whole` | G03 | consumer |
| `rule/mordheim/ostlanders/band--ostlander-special-skills-animal-friendship/mechanic.animal-friendship` | `whole--scope--animal-attack-protection` | — | consumer |
| `rule/mordheim/pirates/band--pirate-special-skills-sea-shanty-singer/unimplemented.pirates.band.pirate-special-skills-sea-shanty-singer` | `sea-shanty-singer` | — | consumer |
| `rule/mordheim/pit-fighters/band--pit-fighter-skill-force-of-will/mechanic.force-of-will` | `force-of-will` | — | consumer |
| `rule/mordheim/protectorate-of-sigmar-lotd3/band--special-skill-rousing-sermon/mechanic.rousing-sermon` | `self-attack-bonus` | — | consumer |
| `rule/mordheim/restless-dead/band--restless-dead-special-skills-wraith-touch/mechanic.wraith-touch` | `whole` | G03, G04 | consumer |
| `rule/mordheim/sea-ghosts-mim/band--dance-storm-of-blades/dance.storm-of-blades` | `whole` | G03 | consumer |
| `rule/mordheim/shallows-beasts-mim/swampers--herb-lore/unimplemented.shallows-beasts-mim.swampers.herb-lore` | `heal-in-recovery-phase--scope--self-heal` | — | consumer |
| `rule/mordheim/sisters-of-sigmar/augur--blessed-sight/skill.blessed-sight` | `whole` | G03 | consumer |
| `rule/mordheim/sisters-of-sigmar/band--special-skills-sign-of-sigmar/skill.sigmar-s-sign` | `sigmar-s-sign` | — | consumer |
| `rule/mordheim/skaven-clan-eshin/band--skaven-special-skills-black-hunger/mechanic.black-hunger` | `attack-and-backlash` | G03 | consumer |
| `rule/mordheim/skaven-clan-pestilens/band--clan-pestilens-special-skills-black-hunger/mechanic.black-hunger` | `attack-and-backlash` | G03 | consumer |
| `rule/mordheim/skaven-of-clan-moulder-web/band--clan-moulder-special-skills/unimplemented.skaven-of-clan-moulder-web.special.clan-moulder-special-skills` | `black-hunger--scope--black-hunger-attack` | — | consumer |
| `rule/mordheim/skaven-of-clan-moulder-web/band--clan-moulder-special-skills/unimplemented.skaven-of-clan-moulder-web.special.clan-moulder-special-skills` | `black-hunger--scope--black-hunger-backlash` | — | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-champion--frenzy/trait.frenzy` | `frenzy` | G02, G03, G04, G05 | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-priest--frenzy/trait.frenzy` | `frenzy` | G02, G03, G04, G05 | consumer |
| `rule/mordheim/snotlings-web/wheelo--combat/mechanic.wheelo-impact` | `whole` | G03, G05 | consumer |
| `rule/mordheim/snotlings-web/wheelo--impact-hits/mechanic.wheelo-impact` | `whole` | G04 | consumer |
| `rule/mordheim/snotlings-web/wheelo--special-skill-modifications/mechanic.wheelo-skill-modifications` | `whole--scope--weapons-training-and-mighty-blow` | — | consumer |
| `rule/mordheim/survivors-of-strigos-sylv/strigoi-vampire--curse-of-the-revenant/mechanic.curse-of-the-revenant` | `whole` | — | consumer |
| `rule/mordheim/survivors-of-strigos-sylv/strigoi-vampire--great-thirster/mechanic.great-thirster` | `whole` | G04 | consumer |
| `rule/mordheim/vampire-hunters-of-sylvania-lotd5/band--special-skill-righteous-aura/skill.sigmar-s-sign` | `sigmar-s-sign` | — | consumer |
| `rule/mordheim/watchmen-mim/private-sleuth--hypnotist/mechanic.hypnotist` | `hypnotist` | — | consumer |
| `rule/mordheim/watchmen-mim/private-sleuth--scryer/trait.re-roll-melee` | `melee-reroll` | G03, G04, G05 | consumer |
| `rule/trollheim/chaos-streets-deathbringers/band--deathbringer-special-skills-death-blow/mechanic.death-blow` | `optional-use` | — | consumer |
| `rule/trollheim/chaos-streets-greenskins/band--orc-special-skills-eadbasher/skill.head-crusher` | `whole` | G03 | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/lunatics--frenzy/trait.frenzy` | `frenzy` | G02, G03, G04, G05 | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/band--pit-fighter-skill-force-of-will/mechanic.force-of-will` | `force-of-will` | — | consumer |
| `rule/trollheim/chaos-streets-sigmar-protectorate/band--protectorate-special-skills-rousing-sermon/skill.inspiring-sermon` | `self-attack-bonus` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--lahmia-power-deceive/unimplemented.band-lahmia-power-deceive` | `deceive` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--lahmia-power-seduction/unimplemented.band-lahmia-power-seduction` | `seduction` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--vampire-power-hypnotic-gaze/unimplemented.band-vampire-power-hypnotic-gaze` | `hypnotic-gaze` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/lahmia-vampire--enchanting-beauty/unimplemented.chaos-streets-undead-bloodlines.lahmia-vampire.enchanting-beauty` | `enchanting-beauty` | G05 | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/band--lahmian-special-skills-hypnotize/unimplemented.khemri-lahmian-brotherhood.band.lahmian-special-skills-hypnotize` | `hypnotize` | G03 | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/band--lahmian-special-skills-seduction/unimplemented.khemri-lahmian-brotherhood.band.lahmian-special-skills-seduction` | `seduction` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/beloved--devoted-to-the-vampire/unimplemented.khemri-lahmian-brotherhood.beloved.devoted-to-the-vampire` | `devoted-frenzy--scope--devoted-frenzy` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/beloved--devoted-to-the-vampire/unimplemented.khemri-lahmian-brotherhood.beloved.devoted-to-the-vampire` | `devoted-frenzy--scope--hatred-against-killer` | G02, G03 | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/lackeys--devoted-to-the-vampire/unimplemented.khemri-lahmian-brotherhood.lackeys.devoted-to-the-vampire` | `devoted-frenzy--scope--devoted-frenzy` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/lackeys--devoted-to-the-vampire/unimplemented.khemri-lahmian-brotherhood.lackeys.devoted-to-the-vampire` | `devoted-frenzy--scope--hatred-against-killer` | G02, G03 | consumer |
| `rule/trollheim/khemri-necromancers/band--necromantic-modification-anvil-head/compiler.anvil-head` | `whole--scope--special-attack` | G03, G04 | consumer |
| `rule/trollheim/lustria-amazons/amazon-totem-warriors--frenzy/trait.frenzy` | `frenzy` | G02, G03, G04, G05 | consumer |
| `rule/trollheim/lustria-amazons/band--amazon-special-skills-hypnotic-dance/unimplemented.lustria-amazons.band.amazon-special-skills-hypnotic-dance` | `hypnotic-dance` | — | consumer |
| `rule/trollheim/lustria-clan-pestilens/band--clan-pestilens-special-skills-black-hunger/mechanic.black-hunger` | `attack-and-backlash` | G03 | consumer |
| `rule/trollheim/lustria-norse/berserkers--frenzy/trait.frenzy` | `frenzy` | G02, G03, G04, G05 | consumer |
| `rule/trollheim/lustria-pirates/band--pirate-special-skills-sea-shanty-singer/unimplemented.lustria-pirates.band.pirate-special-skills-sea-shanty-singer` | `sea-shanty-singer` | — | consumer |
| `rule/trollheim/lustria-pygmies/wild-lunatics--lunatics/unimplemented.lustria-pygmies.wild-lunatics.lunatics` | `frenzy` | G05 | consumer |
| `rule/trollheim/lustria-savage-goblins/red-teeth--frenzy/trait.frenzy` | `frenzy` | G02, G03, G04, G05 | consumer |
| `rule/trollheim/trollheim-cult-of-the-possessed/band--mutations-spines/trait.spines` | `whole--scope--spines` | G04 | consumer |
| `rule/trollheim/trollheim-skaven-clan-eshin/band--skaven-special-skills-black-hunger/mechanic.black-hunger` | `attack-and-backlash` | G03 | consumer |
| `source/bands/mordheim/skaven-of-clan-pristekk-sc/equipment-access.yaml/@/equipment_lists/2/items/0/notes/unclassified` | `weapon-note--scope--whipcrack` | G03, G04 | encargo explícito; consumer vacío |
| `source/catalog/campaign/exploration-and-income.yaml/campaign.magical-artefact.executioners-hood/unclassified` | `frenzy` | G02, G04 | consumer |
| `source/catalog/campaign/magic.yaml/spell.commands.art-thou-ready-to-die-fighting/unclassified` | `whole` | G03 | consumer |
| `source/catalog/campaign/magic.yaml/spell.commands.follow-me-mine-pugnacious-ones/unclassified` | `whole` | G03 | consumer |
| `source/catalog/campaign/magic.yaml/spell.commands.raise-our-insignia/unclassified` | `raise-our-insignia--scope--supplied-reroll` | G05 | consumer |
| `source/catalog/campaign/mutations.yaml/campaign.mutation.spines/unclassified` | `whole` | — | consumer |
| `source/catalog/campaign/mutations.yaml/campaign.mutation.tentacle/unclassified` | `whole` | G04 | consumer |
| `source/catalog/campaign/serious-injuries.yaml/@/tables/0/results/10/note/unclassified` | `permanent-weapon-skill-penalty` | — | consumer |
| `source/catalog/campaign/serious-injuries.yaml/@/tables/0/results/6/note/unclassified` | `permanent-toughness-penalty` | — | consumer |
| `source/catalog/campaign/serious-injuries.yaml/@/tables/0/results/9/note/unclassified` | `injury-consequence` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.abdul-alhazred-the-mad-sorcerer.rule.eye-pendant/unclassified` | `eye-pendant` | G03, G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.crow-master-the.rule.crow-master/unclassified` | `mantle-of-crows` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.drenok-johansen-wielder-of-the-great-axe.rule.axe-of-icefang/unclassified` | `icefang-axe` | G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.drenok-johansen-wielder-of-the-great-axe.rule.berserker/unclassified` | `whole` | G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.drenok-johansen-wielder-of-the-great-axe.rule.sabertooth-tiger-hide/unclassified` | `sabertooth-tiger-hide--scope--close-combat-save` | G03, G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.heinrich-altdorf-schmidt.rule.snake-fear/unclassified` | `snake-fear` | G05 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.heinrich-altdorf-schmidt.rule.whip-master/unclassified` | `whip-master-reroll` | G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.khar-mel-the-djinn.rule.djinn-s-curse/unclassified` | `djinns-curse` | G03, G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/hireling.dramatis.belandysh-condemned-champion-of-chen.rule.inconsistency/unclassified` | `rule` | G02 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.busty-gwen.rule.massively-built/unclassified` | `leadership-distraction` | G02, G05 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-dark-jester-in-mordheim.rule.babbling-banter/unclassified` | `whole` | G03 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-dark-jester-in-mordheim.rule.confound-and-confuse/unclassified` | `trick-babbling-banter` | G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-dark-jester-in-mordheim.rule.confound-and-confuse/unclassified` | `trick-sidestepper` | G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-dark-jester-in-mordheim.rule.confound-and-confuse/unclassified` | `trick-trip` | G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-dark-jester-in-mordheim.rule.sidestepper/unclassified` | `rule` | G03 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-dark-jester-in-mordheim.rule.trip/unclassified` | `whole` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.gaoler.rule.torturer-s-grapple/unclassified` | `whole` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.kislev-ranger.rule.herb-lore/unclassified` | `herb-lore-self-heal` | — | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.mule-skinner.rule.whip-master/unclassified` | `whip-master-reroll` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.witch.rule.potions/unclassified` | `potions-before-battle` | G02 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.dwarf-slayer-pirate.rule.slayer-pirate/unclassified` | `festooned-with-pistols--scope--festooned-pistols-melee` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.estalian-diestro.rule.main-gauche/unclassified` | `main-gauche-modes` | G02 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.estalian-diestro.rule.rapier/unclassified` | `rapier-barrage` | G03 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.druid-priest-of-taal.skill.tranquil-fauna/mechanic.taal-tranquil-fauna` | `tranquil-fauna` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.norse-bearman-bodyguard.rule.drunken/mechanic.centigor-drunken` | `drunken` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr.pending-duel` | `haunted-mien-skill-access` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr.pending-duel` | `haunted-mien-strictures` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan.pending-duel` | `witch-finder--scope--inquisitor-judgement` | G02 | consumer |
| `source/catalog/rules/conditions.yaml/campaign.condition.frenzy/trait.frenzy` | `frenzy` | G02, G03, G04, G05 | consumer |

## Claves de apoyo de otros responsables

No tiene claves en este anexo.

## Base de esta asignación

Preparación: 2026-10-21. HEAD: `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` más cambios locales actuales. CSV SHA-256: `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`. No es un certificado de ejecución.
