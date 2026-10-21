# G02 — Estado por simulación, recursos, características y mutaciones

## Prompt para lanzar el agente

Copia el bloque completo al lanzar el agente. Las condiciones de inicio forman parte del encargo; este prompt no autoriza saltarse sus dependencias.

```text
Realiza el encargo G02 (fase 1: implementación) del motor vectorial NumPy.

INFORMACIÓN QUE DEBES LEER
1. El fichero de trabajo completo:
   D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK\TMP_VECTORIAL_ENGINE_2A2B\G02_ESTADO_RECURSOS_Y_MUTACIONES.md
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
Etapa B, tras G00. Completar e integrar antes de lanzar G03/G04/G05; las decisiones de tipo afectan a todos.
Comprueba la entrega de esas dependencias. Si falta alguna, comunica la dependencia concreta;
puedes avanzar con lectura o trabajo independiente, pero no inventes interfaces ni declares
completada una conexión que todavía no existe.

OBJETIVO CONCRETO
Implementar el estado NumPy por simulación que necesitan las funcionalidades pendientes: inicialización, características ausentes o variables, recursos, temporizadores, equipo y mutaciones. Compara FighterState/DuelState con CombatState y traslada su comportamiento. Mantén arrays independientes por combatiente y simulación. Deja una base integrada y concreta que G03/G04/G05 puedan consumir sin editar todos el mismo archivo. No portes el control completo de rondas de G06.

REFERENCIAS Y COMPROBACIONES QUE DEBES REUTILIZAR
Usa modular/state.py, modular/mutations.py, vectorized/_types.py y los helpers autorizados de inicialización/observación del driver. Reutiliza test_observations.py. Si falta un comprobante, un caso pequeño con filas divergentes basta como referencia habitual.

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
TMP_VECTORIAL_ENGINE_2A2B/G02-deliverable.md
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

**Inicio:** Etapa B, tras G00. Completar e integrar antes de lanzar G03/G04/G05; las decisiones de tipo afectan a todos.

**Cláusulas principales:** 12. **Cláusulas de apoyo:** 129.

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

Crea o actualiza `TMP_VECTORIAL_ENGINE_2A2B/G02-deliverable.md` en la raíz de tu copia de trabajo. Es la entrega persistente obligatoria de este grupo y está permitida además de los archivos de producción autorizados. No basta con un mensaje en el chat.

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

- `TMP_VECTORIAL_ENGINE_2A2B/G02-deliverable.md` — documento de entrega obligatorio, propietario exclusivo G02.
- `packages/python/combat-engine/mordheim_combat/vectorized/_types.py`
- `packages/python/combat-engine/mordheim_combat/vectorized/_driver.py (solo _new_state, _refresh_random_characteristics y _resource_observation; antes de G06)`
- `packages/python/combat-engine/mordheim_combat/vectorized/_state.py (solo si hace falta para separar inicialización del driver)`
- `packages/python/combat-engine/mordheim_combat/vectorized/_mutations.py (solo si hace falta portar la proyección de mutaciones)`
- `tests/python/combat/vectorized/test_observations.py`

Cualquier archivo no enumerado queda fuera de tu propiedad. Los módulos nuevos expresamente permitidos solo se crean si el portado los necesita. Los tests compartidos que no son tuyos se pueden ejecutar, pero no editar.

## Implementación de referencia que debes seguir

- `packages/python/combat-engine/mordheim_combat/modular/state.py::FighterState`
- `packages/python/combat-engine/mordheim_combat/modular/state.py::DuelState`
- `packages/python/combat-engine/mordheim_combat/modular/state.py::initialize_fighter`
- `packages/python/combat-engine/mordheim_combat/modular/state.py::initialize_duel`
- `packages/python/combat-engine/mordheim_combat/modular/state.py::require_characteristics`
- `packages/python/combat-engine/mordheim_combat/modular/state.py::maximum_wounds`
- `packages/python/combat-engine/mordheim_combat/modular/mutations.py::fighter_for_mutations`
- `packages/python/combat-engine/mordheim_combat/modular/mutations.py::apply_brand`

Estas referencias son puntos de entrada; sigue sus llamadas para reproducir el comportamiento completo, sin releer las fuentes de reglas.

## Trabajo concreto

1. Contrastar los campos reales de `FighterState`/`DuelState` con `CombatState` y añadir solo los necesarios para el alcance admitido, conservando ausencias impresas y límites de heridas.
2. Representar recursos consumidos, turnos de disponibilidad, efectos de duración y decisiones mediante estado individual, sin arrays compartidos entre combatientes o simulaciones.
3. Portar inicialización y actualización de características aleatorias desde `initialize_fighter`, `require_characteristics` y `_refresh_random_characteristics`. Un valor se solicita y conserva en el mismo momento semántico que en el modular.
4. Preparar la representación de equipo, miembros mutados, armas naturales y cambios de forma. Portar las proyecciones de `mutations.py`; G04 consume el equipo efectivo y G06 decide cuándo se aplica cada transición.
5. Preservar el protocolo público de decisiones. Las decisiones dependientes del estado se aplican a las filas afectadas. No ejecutar el duelo modular una vez por fila como implementación.
6. Conservar los nombres y firmas usados por importadores existentes, añadiendo argumentos opcionales cuando haga falta. Si se extrae inicialización a `_state.py`, mantener los wrappers históricos del driver.
7. Entregar un esquema concreto de campos y helpers ya implementados con sus formas, valores iniciales y responsables de consumo; incluirlo en el mensaje de entrega para congelar la base de G03/G04/G05. Los futuros cambios a `_types.py` los integra el coordinador, no los tres agentes en paralelo.

## Comprobación mínima

Reutilizar `test_observations.py` y casos existentes de inicialización. Añadir como máximo habitual un caso pequeño con dos o más filas que compruebe independencia de estado/recurso; otro solo ante un hueco concreto. No crear pruebas modulares.

## Criterio de entrega

Estado e inicialización están integrados, la independencia entre filas está comprobada y las interfaces necesarias para operadores, ataques, psicología y rondas son utilizables. La evolución de rondas aún corresponde a G06.

## Claves principales asignadas

| id | clause_id | Apoyos | Referencia de asignación |
| --- | --- | --- | --- |
| `mechanic/mechanic.guiding-dream` | `whole` | — | consumer |
| `mechanic/mechanic.shallya-strictures` | `whole` | — | consumer |
| `rule/catalog/warband/skill.monstrous/skill.monstrous` | `whole` | — | consumer |
| `rule/mordheim/black-orcs/orc-nuttaz--savage/profile.equipment-restrictions` | `mandatory-charge` | — | consumer |
| `rule/mordheim/marauders-of-chaos/condemned--inconsistency/profile.random-characteristics` | `whole` | — | consumer |
| `rule/trollheim/khemri-necromancers/band--necromantic-modification-ogre-flesh/skill.monstrous` | `whole--scope--wound-bonus` | — | consumer |
| `source/bands/mordheim/marauders-of-chaos/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `advancement-lift` | — | consumer |
| `source/bands/mordheim/marauders-of-chaos/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole--scope--equipment-ban-variable-state` | — | consumer |
| `source/bands/mordheim/marauders-of-chaos/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole--scope--unarmed-penalty-waiver` | — | consumer |
| `source/bands/mordheim/marauders-of-chaos/profiles.yaml/@/profiles/5/equipment_restrictions/1/unclassified` | `whole` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/@/profiles/0/unresolved_references/0/unclassified` | `profile` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan.pending-duel` | `witch-finder--scope--compulsory-charge` | — | consumer |

## Claves de apoyo de otros responsables

| id | clause_id | Responsable principal | Referencia de asignación |
| --- | --- | --- | --- |
| `core/combat-critical-hits` | `one-per-phase` | G06 | consumer |
| `core/combat-parry` | `parry-attempt` | G03 | consumer |
| `core/combat-parry` | `reroll-and-capacity` | G03 | consumer |
| `item/buckler` | `parry-one-hit-per-round` | G03 | consumer |
| `item/crimson_shade` | `whole` | G06 | consumer |
| `mechanic/defence.buckler` | `parry-one-hit-per-round` | G03 | consumer |
| `mechanic/mechanic.disability` | `head-injury-stupidity` | G05 | consumer |
| `mechanic/mechanic.disability` | `no-two-weapons-or-weapon-and-shield` | G05 | consumer |
| `mechanic/mechanic.disability` | `permanent-characteristic-penalty` | G05 | consumer |
| `mechanic/mechanic.norse-shieldmaster` | `shield-parries-in-addition-to-its-save` | G03 | consumer |
| `mechanic/preparation.crimson-shade` | `whole` | G06 | consumer |
| `mechanic/skill.axe-master` | `parry-with-normal-axes` | G03 | consumer |
| `mechanic/skill.defensive-stance` | `match-with-a-parrying-weapon` | G03 | consumer |
| `mechanic/skill.defensive-stance` | `parry-with-any-weapon` | G03 | consumer |
| `mechanic/skill.head-crusher` | `whole` | G03 | consumer |
| `mechanic/skill.luck` | `once-per-battle-reroll` | G04 | consumer |
| `mechanic/skill.miniath` | `parry-with-any-weapon` | G03 | consumer |
| `mechanic/skill.miniath` | `reroll-with-a-parrying-weapon` | G03 | consumer |
| `mechanic/skill.monstrous` | `whole` | G06 | consumer |
| `mechanic/skill.shield-mastery` | `shield-parries-and-keeps-its-bonus` | G03 | consumer |
| `mechanic/skill.sword-master` | `match-parry-and-parry-a-six` | G03 | consumer |
| `mechanic/skill.sword-master` | `one-reroll-only` | G03 | consumer |
| `mechanic/skill.swordmaster` | `match-the-to-hit-roll` | G03 | consumer |
| `mechanic/skill.unbeatable-warrior` | `two-parries-with-two-weapons` | G03 | consumer |
| `mechanic/weapon.double-bladed-sword` | `whole` | G03 | consumer |
| `rule/catalog/warband/skill.axe-master/skill.axe-master` | `parry-with-normal-axes` | G03 | consumer |
| `rule/catalog/warband/skill.defensive-stance/skill.defensive-stance` | `match-with-a-parrying-weapon` | G03 | consumer |
| `rule/catalog/warband/skill.defensive-stance/skill.defensive-stance` | `parry-with-any-weapon` | G03 | consumer |
| `rule/catalog/warband/skill.luck/skill.luck` | `once-per-battle-reroll` | G04 | consumer |
| `rule/catalog/warband/skill.miniath/skill.miniath` | `parry-with-any-weapon` | G03 | consumer |
| `rule/catalog/warband/skill.miniath/skill.miniath` | `reroll-with-a-parrying-weapon` | G03 | consumer |
| `rule/catalog/warband/skill.shield-mastery/skill.shield-mastery` | `shield-parries-and-keeps-its-bonus` | G03 | consumer |
| `rule/catalog/warband/skill.sword-master/skill.sword-master` | `match-parry-and-parry-a-six` | G03 | consumer |
| `rule/catalog/warband/skill.sword-master/skill.sword-master` | `one-reroll-only` | G03 | consumer |
| `rule/catalog/warband/skill.unbeatable-warrior/skill.unbeatable-warrior` | `two-parries-with-two-weapons` | G03 | consumer |
| `rule/mordheim/adventurers-kaz/barbarian--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/amazons-mordheim/totem-warriors--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/bretonnian-chapel-guard/knights-errant--impetuous/unimplemented.bretonnian-chapel-guard.knights-errant.impetuous` | `impetuous-movement` | G06 | consumer |
| `rule/mordheim/channel-rats-mim/petru--potions/unimplemented.channel-rats-mim.petru.potions` | `random-pre-battle-potion` | G06 | consumer |
| `rule/mordheim/clan-angrund-kep/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `dwarf-axe-reroll` | G03 | consumer |
| `rule/mordheim/clan-angrund-kep/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `parry-matches` | G03 | consumer |
| `rule/mordheim/clan-angrund-kep/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `two-parries` | G03 | consumer |
| `rule/mordheim/clan-angrund-kep/band--dwarf-special-skills-master-of-blades/skill.unbeatable-warrior` | `whole` | G03 | consumer |
| `rule/mordheim/clockworkers-sc/band--constructs/unimplemented.clockworkers-sc.band.constructs` | `constructs-psychology-immunity` | G05 | consumer |
| `rule/mordheim/crooked-moon-kep/band--night-goblin-special-skills/unimplemented.crooked-moon-kep.band.night-goblin-special-skills` | `night-goblin-skills--scope--netter` | G06 | consumer |
| `rule/mordheim/druchii-mic/witch-elves--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/dwarf-rangers/band--dwarf-special-skills-combat-master/skill.unbeatable-warrior` | `whole` | G03 | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `match-the-to-hit-roll` | G03 | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `reroll-with-two-dwarf-axes` | G03 | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `two-parries-with-two-parry-weapons` | G03 | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.unbeatable-warrior` | `match-the-to-hit-roll` | G03 | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.unbeatable-warrior` | `reroll-with-two-dwarf-axes` | G03 | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.unbeatable-warrior` | `two-parries-with-two-parry-weapons` | G03 | consumer |
| `rule/mordheim/forest-goblins/red-toof-goblins--berserkers/trait.frenzy` | `frenzy` | G05 | consumer |
| `rule/mordheim/ghost-pirates-sar/ghost-captain--undead/unimplemented.ghost-pirates-sar.ghost-captain.undead` | `undead-psychology-immunity` | G05 | consumer |
| `rule/mordheim/ghost-pirates-sar/gibbets--undead/unimplemented.ghost-pirates-sar.gibbets.undead` | `undead-psychology-immunity` | G05 | consumer |
| `rule/mordheim/ghost-pirates-sar/screaming-ghosts--undead/unimplemented.ghost-pirates-sar.screaming-ghosts.undead` | `undead-psychology-immunity` | G05 | consumer |
| `rule/mordheim/ghost-pirates-sar/skeleton-mates--undead/unimplemented.ghost-pirates-sar.skeleton-mates.undead` | `undead-psychology-immunity` | G05 | consumer |
| `rule/mordheim/ghost-pirates-sar/the-bloated--undead/unimplemented.ghost-pirates-sar.the-bloated.undead` | `undead-psychology-immunity` | G05 | consumer |
| `rule/mordheim/high-elves-lus/band--skill-miniath/skill.miniath` | `parry-with-any-weapon` | G03 | consumer |
| `rule/mordheim/hochland-bandits/duelist--swordmaster/skill.swordmaster` | `match-the-to-hit-roll` | G03 | consumer |
| `rule/mordheim/khorne-raiders-sar/cannibal-boys--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/masters-of-horror-sylv/mad-scientist--alchemist/unimplemented.masters-of-horror-sylv.special.alchemist` | `start-of-game-potion--scope--addiction-state` | G06 | consumer |
| `rule/mordheim/masters-of-horror-sylv/mad-scientist--alchemist/unimplemented.masters-of-horror-sylv.special.alchemist` | `start-of-game-potion--scope--potion-characteristic-bonuses` | G06 | consumer |
| `rule/mordheim/masters-of-horror-sylv/the-bitten--transform/unimplemented.masters-of-horror-sylv.the-bitten.transform` | `transformation-equipment-loss` | G04 | consumer |
| `rule/mordheim/masters-of-horror-sylv/the-bitten--transform/unimplemented.masters-of-horror-sylv.the-bitten.transform` | `transformation-state--scope--transformation-duration` | G06 | consumer |
| `rule/mordheim/masters-of-horror-sylv/the-bitten--transform/unimplemented.masters-of-horror-sylv.the-bitten.transform` | `transformation-state--scope--transformation-state` | G06 | consumer |
| `rule/mordheim/night-goblins-mic/fanatics--looney/trait.frenzy` | `frenzy` | G05 | consumer |
| `rule/mordheim/night-goblins-web/shaman--fungus-brew/unimplemented.night-goblins-web.shaman.fungus-brew` | `fungus-brew-production` | G06 | encargo explícito; consumer vacío |
| `rule/mordheim/night-goblins-web/shaman--fungus-brew/unimplemented.night-goblins-web.shaman.fungus-brew` | `fungus-loony` | G06 | consumer |
| `rule/mordheim/norse-explorers-btb/band--norse-special-skills-shield-master/skill.shield-mastery` | `parry-with-a-shield` | G03 | consumer |
| `rule/mordheim/norse-explorers-btb/beserkers--berserkers/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/norse-explorers-lustria/band--norse-special-skills-shield-master/skill.shield-mastery` | `parry-with-a-shield` | G03 | consumer |
| `rule/mordheim/norse-explorers-lustria/beserkers--berserkers/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/savage-orcs-kaz/nuttaz--frenzy/trait.frenzy` | `frenzy` | G05 | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-champion--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-priest--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/tileans/duelists--cloak-dagger/trait.counts-as-buckler` | `counts-as-buckler` | G03 | consumer |
| `rule/trollheim/chaos-streets-deathbringers/band--deathbringer-special-skills-defensive-stance/skill.defensive-stance` | `match-with-a-parrying-weapon` | G03 | consumer |
| `rule/trollheim/chaos-streets-deathbringers/band--deathbringer-special-skills-defensive-stance/skill.defensive-stance` | `parry-with-any-weapon` | G03 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `match-the-to-hit-roll` | G03 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `reroll-with-two-dwarf-axes` | G03 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `two-parries-with-two-parry-weapons` | G03 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.unbeatable-warrior` | `match-the-to-hit-roll` | G03 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.unbeatable-warrior` | `reroll-with-two-dwarf-axes` | G03 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.unbeatable-warrior` | `two-parries-with-two-parry-weapons` | G03 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/dwarf-troll-slayers--death-oath/unimplemented.chaos-streets-dwarf-treasure-hunters.dwarf-troll-slayers.death-oath` | `psychology-immunity` | G05 | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/cripples--disability/compiler.disability` | `head-injury-stupidity` | G05 | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/cripples--disability/compiler.disability` | `no-two-weapons-or-weapon-and-shield` | G05 | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/cripples--disability/compiler.disability` | `permanent-characteristic-penalty` | G05 | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/lunatics--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/dwarf-troll-slayer--death-oath/unimplemented.chaos-streets-pit-fighters.dwarf-troll-slayer.death-oath` | `psychology-immunity` | G05 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--blood-dragon-power-sword-master/skill.sword-master` | `match-parry-and-parry-a-six` | G03 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--blood-dragon-power-sword-master/skill.sword-master` | `one-reroll-only` | G03 | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/troll-slayer--death-oath/unimplemented.khemri-cursed-of-karak-zorn.troll-slayer.death-oath` | `psychology-immunity` | G05 | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/beloved--devoted-to-the-vampire/unimplemented.khemri-lahmian-brotherhood.beloved.devoted-to-the-vampire` | `devoted-frenzy--scope--hatred-against-killer` | G06 | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/lackeys--devoted-to-the-vampire/unimplemented.khemri-lahmian-brotherhood.lackeys.devoted-to-the-vampire` | `devoted-frenzy--scope--hatred-against-killer` | G06 | consumer |
| `rule/trollheim/lustria-amazons/amazon-totem-warriors--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/trollheim/lustria-high-elves/band--high-elf-special-skills-luck/skill.luck` | `once-per-battle-reroll` | G04 | consumer |
| `rule/trollheim/lustria-high-elves/band--high-elf-special-skills-miniath/skill.miniath` | `parry-with-any-weapon` | G03 | consumer |
| `rule/trollheim/lustria-high-elves/band--high-elf-special-skills-miniath/skill.miniath` | `reroll-with-a-parrying-weapon` | G03 | consumer |
| `rule/trollheim/lustria-norse/band--norse-special-skills-shield-mastery/skill.shield-mastery` | `shield-parries-and-keeps-its-bonus` | G03 | consumer |
| `rule/trollheim/lustria-norse/berserkers--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/trollheim/lustria-savage-goblins/red-teeth--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `source/bands/mordheim/dark-elf-corsairs-mou/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `frenzy` | G05 | encargo explícito; consumer vacío |
| `source/bands/mordheim/silent-brotherhood-sc/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `cloak-counts-as-a-buckler` | G03 | consumer |
| `source/catalog/campaign/exploration-and-income.yaml/campaign.magical-artefact.executioners-hood/unclassified` | `frenzy` | G06 | consumer |
| `source/catalog/campaign/magic.yaml/@/lores/46/note/unclassified` | `trident-parries--scope--trident-parries` | G03 | consumer |
| `source/catalog/campaign/serious-injuries.yaml/@/tables/0/results/4/note/unclassified` | `madness-roll` | G05 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.crow-master-the.rule.crow-master/unclassified` | `needle-and-thread--scope--mouth-sewn` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.heinrich-altdorf-schmidt.rule.luck/unclassified` | `luck-re-roll` | G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.maximilian-the-mad.rule.religious-fervour/unclassified` | `frenzy` | G05 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/hireling.dramatis.belandysh-condemned-champion-of-chen.rule.inconsistency/unclassified` | `rule` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.busty-gwen.rule.massively-built/unclassified` | `leadership-distraction` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2b.yaml/@/profiles/2/equipment/fixed_items/1/notes/unclassified` | `short-sword-resolves-to-the-sword-item` | G03 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.witch.rule.potions/unclassified` | `potions-before-battle` | G06 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/@/profiles/17/unresolved_references/0/unclassified` | `equipment-access` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.estalian-diestro.rule.main-gauche/unclassified` | `main-gauche-modes` | G06 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/12/equipment/choices/0/options/0/items/0/notes/unclassified` | `trident-parries` | G03 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.norse-bearman-bodyguard.rule.shieldmaster/mechanic.norse-shieldmaster` | `shield-parries-in-addition-to-its-save` | G03 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr.pending-duel` | `augur-psychology-immunity` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr.pending-duel` | `augur-strength-reduction` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan.pending-duel` | `witch-finder--scope--inquisitor-judgement` | G06 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan.pending-duel` | `witch-finder--scope--inquisitor-state` | G05 | consumer |
| `source/catalog/rules/conditions.yaml/campaign.condition.frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.berserkers/unclassified` | `frenzy` | G05 | encargo explícito; consumer vacío |
| `source/catalog/rules/special-rules.yaml/shared-rule.censer-bearer/unclassified` | `frenzy` | G05 | encargo explícito; consumer vacío |
| `source/catalog/rules/special-rules.yaml/shared-rule.crushing-blow/unclassified` | `no-enemy-may-parry` | G03 | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.shield-master/unclassified` | `parry-with-a-shield` | G03 | consumer |

## Base de esta asignación

Preparación: 2026-10-21. HEAD: `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` más cambios locales actuales. CSV SHA-256: `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`. No es un certificado de ejecución.
