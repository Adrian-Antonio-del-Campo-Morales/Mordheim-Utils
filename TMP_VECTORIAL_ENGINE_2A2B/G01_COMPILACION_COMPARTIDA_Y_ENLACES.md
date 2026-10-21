# G01 — Compilación compartida, construcción y enlaces existentes

## Prompt para lanzar el agente

Copia el bloque completo al lanzar el agente. Las condiciones de inicio forman parte del encargo; este prompt no autoriza saltarse sus dependencias.

```text
Realiza el encargo G01 (fase 1: implementación) del motor vectorial NumPy.

INFORMACIÓN QUE DEBES LEER
1. El fichero de trabajo completo:
   D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK\TMP_VECTORIAL_ENGINE_2A2B\G01_COMPILACION_COMPARTIDA_Y_ENLACES.md
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
Etapa A, en paralelo con G00. Puede continuar mientras se implementan otros grupos: no posee archivos del motor.
Comprueba la entrega de esas dependencias. Si falta alguna, comunica la dependencia concreta;
puedes avanzar con lectura o trabajo independiente, pero no inventes interfaces ni declares
completada una conexión que todavía no existe.

OBJETIVO CONCRETO
Resolver el enlace de las cláusulas de construcción compartida con la entrada real de NumPy. Parte del compilador, la elegibilidad, los contratos y evidencia ya existentes. Reutiliza la ruta común de CompiledFighter. Las cláusulas sin consumer requieren recuperar la referencia de implementación aceptada, no investigar otra vez qué dice la regla. Si una consecuencia necesita runtime NumPy, devuelve al coordinador su clave y función modular para asignarla al propietario. Agrupa referencias repetidas y evita revisar individualmente cientos de veces la misma ruta. Este encargo no autoriza editar producción ni construir otro compilador.

REFERENCIAS Y COMPROBACIONES QUE DEBES REUTILIZAR
Usa compile_fighter, contracts.py, los consumidores de elegibilidad y CompiledFighter enumerados en el encargo. Cero pruebas nuevas previstas: reutiliza evidencia vigente. No marques todas las filas resueltas por compartir compilador; demuestra el enlace aplicable.

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
TMP_VECTORIAL_ENGINE_2A2B/G01-deliverable.md
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

**Inicio:** Etapa A, en paralelo con G00. Puede continuar mientras se implementan otros grupos: no posee archivos del motor.

**Cláusulas principales:** 1396. **Cláusulas de apoyo:** 6.

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

Crea o actualiza `TMP_VECTORIAL_ENGINE_2A2B/G01-deliverable.md` en la raíz de tu copia de trabajo. Es la entrega persistente obligatoria de este grupo y está permitida además de los archivos de producción autorizados. No basta con un mensaje en el chat.

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

- `TMP_VECTORIAL_ENGINE_2A2B/G01-deliverable.md` — documento de entrega obligatorio, propietario exclusivo G01.
- `Ningún archivo de producción. Devolver al coordinador referencias y propuestas de actualización del CSV.`

Cualquier archivo no enumerado queda fuera de tu propiedad. Los módulos nuevos expresamente permitidos solo se crean si el portado los necesita. Los tests compartidos que no son tuyos se pueden ejecutar, pero no editar.

## Implementación de referencia que debes seguir

- `packages/python/roster-construction/mordheim_construction/compiler.py::compile_fighter`
- `packages/python/roster-construction/mordheim_construction/contracts.py`
- `packages/python/roster-construction/mordheim_construction/eligibility.py`
- `packages/typescript/domain/eligibility/index.ts`
- `packages/python/core/mordheim_core/models.py::CompiledFighter`

Estas referencias son puntos de entrada; sigue sus llamadas para reproducir el comportamiento completo, sin releer las fuentes de reglas.

## Trabajo concreto

1. Reutilizar la clasificación, contratos y evidencia de construcción existentes. Agrupar las referencias iguales para no revisar cientos de veces la misma ruta.
2. Para cada grupo, localizar qué selección, característica, efecto, equipo o contexto ya produce `compile_fighter` y cómo llega al mismo `CompiledFighter` que consume NumPy.
3. Distinguir cláusulas resueltas completamente en la frontera compartida de consecuencias que aún necesitan consumidor de ejecución. Compartir compilador no certifica el consumo de un efecto nuevo.
4. Las cláusulas sin `consumer` se señalan explícitamente en el anexo. Recuperar el enlace desde su evidencia, las referencias de implementación y los contratos existentes. No reabrir fuentes ni clasificar de nuevo la regla. Las referencias viejas y `proposed.*` son pistas históricas, no mandatos para implementar una mecánica nueva.
5. Para datos de acceso o campaña compartidos, conservar su resolución existente; no construir otro servicio de campaña ni portar TypeScript a NumPy. Para consecuencias de ejecución que aparezcan sin ruta explícita, devolver al coordinador la clave y la función modular real, para encargar la conexión al propietario correcto antes de cerrar la fila.
6. Entregar por claves las rutas compartidas acreditadas y las dependencias de runtime identificadas. No marcar toda esta lista como implementada o verificada por el solo nombre del paquete.

## Comprobación mínima

Cero pruebas nuevas previstas. Reutilizar evidencia vigente del compilador y comprobaciones existentes de construcción/contexto. No volver a ejecutar la batería modular ni revisar todos sus tests; una discrepancia concreta se comunica al coordinador.

## Criterio de entrega

Cada clave tiene una explicación técnica de su reutilización o una dependencia de ejecución explícita entregada al propietario. No queda una consecuencia de runtime oculta bajo “compilación compartida”.

## Claves principales asignadas

| id | clause_id | Apoyos | Referencia de asignación |
| --- | --- | --- | --- |
| `item/boar_spear_aristocrat_only` | `aristocrat-only` | — | referencias de compilación, construcción o enlace compartido |
| `item/bone_helmet` | `behaves-as-a-wizards-robe` | — | enlace compartido; consumer vacío |
| `item/bone_helmet` | `behaves-as-eshin-assassin-robes` | — | enlace compartido; consumer vacío |
| `item/bone_helmet` | `printed-text-missing` | — | enlace compartido; consumer vacío |
| `item/bone_helmet_skink_priest_only` | `behaves-as-a-wizards-robe` | — | enlace compartido; consumer vacío |
| `item/bone_helmet_skink_priest_only` | `behaves-as-eshin-assassin-robes` | — | enlace compartido; consumer vacío |
| `item/bone_helmet_skink_priest_only` | `printed-text-missing` | — | enlace compartido; consumer vacío |
| `item/eshin_assassin_clothes` | `behaves-as-a-helmet` | — | enlace compartido; consumer vacío |
| `item/eshin_assassin_clothes` | `behaves-as-a-wizards-robe` | — | enlace compartido; consumer vacío |
| `item/eshin_assassin_clothes` | `printed-text-missing` | — | enlace compartido; consumer vacío |
| `item/hellblade` | `bearer-and-material-restrictions--scope--material-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `item/hellblade` | `bearer-and-material-restrictions--scope--recipients` | — | referencias de compilación, construcción o enlace compartido |
| `item/katana` | `whole--scope--heroes-only` | — | enlace compartido; consumer vacío |
| `item/knuckledusters` | `whole--scope--concealable-loadout` | — | enlace compartido; consumer vacío |
| `item/lance_not_questing_knight` | `recipient-variant` | — | referencias de compilación, construcción o enlace compartido |
| `item/long_daggers` | `whole--scope--recipients` | — | enlace compartido; consumer vacío |
| `item/mad_cap_mushrooms` | `frenzy` | — | referencias de compilación, construcción o enlace compartido |
| `item/mage_robes` | `behaves-as-a-helmet` | — | enlace compartido; consumer vacío |
| `item/mage_robes` | `behaves-as-eshin-assassin-robes` | — | enlace compartido; consumer vacío |
| `item/mage_robes` | `printed-text-missing` | — | enlace compartido; consumer vacío |
| `item/man_catcher` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `item/shock_rod` | `whole--scope--recipients` | — | enlace compartido; consumer vacío |
| `item/skull_busta` | `bearer-prohibitions--scope--goblin-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `item/skull_busta` | `bearer-prohibitions--scope--no-other-weapons-but-shields` | — | referencias de compilación, construcción o enlace compartido |
| `item/sun_gauntlet` | `whole` | — | enlace compartido; consumer vacío |
| `item/sword_heroes_only` | `heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `item/wizard_robe` | `behaves-as-a-helmet` | — | enlace compartido; consumer vacío |
| `item/wizard_robe` | `behaves-as-eshin-assassin-robes` | — | enlace compartido; consumer vacío |
| `item/wizard_robe` | `printed-text-missing` | — | enlace compartido; consumer vacío |
| `item/wolf_pelt_cloak` | `may-not-carry-blackpowder-weapons` | — | referencias de compilación, construcción o enlace compartido |
| `item/wolf_pelt_cloak` | `may-not-wear-armour` | — | referencias de compilación, construcción o enlace compartido |
| `mechanic/defence.wolf-pelt-cloak` | `may-not-carry-blackpowder-weapons` | — | referencias de compilación, construcción o enlace compartido |
| `mechanic/defence.wolf-pelt-cloak` | `may-not-wear-armour` | — | referencias de compilación, construcción o enlace compartido |
| `mechanic/mechanic.curse-of-the-revenant` | `requires-great-thirster` | — | referencias de compilación, construcción o enlace compartido |
| `mechanic/mechanic.flesh-peddler` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `mechanic/mechanic.frustratingly-tiny` | `cannot-combine-with-big-bully` | — | enlace compartido; consumer vacío |
| `mechanic/mechanic.mark-of-arkhar` | `whole--scope--bloodfather-role` | — | referencias de compilación, construcción o enlace compartido |
| `mechanic/mechanic.mark-of-arkhar` | `whole--scope--frenzy` | — | referencias de compilación, construcción o enlace compartido |
| `mechanic/mechanic.snorri-drunk` | `snorri-drunk` | — | referencias de compilación, construcción o enlace compartido |
| `mechanic/preparation.head-splitter-mushrooms` | `frenzy` | — | referencias de compilación, construcción o enlace compartido |
| `mechanic/preparation.mad-cap-mushrooms` | `frenzy` | — | referencias de compilación, construcción o enlace compartido |
| `mechanic/weapon.boar-spear` | `shield-only` | — | referencias de compilación, construcción o enlace compartido |
| `mechanic/weapon.hellblade` | `material-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/adventurers-kaz/band--barbarian-special-skills/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/adventurers-kaz/band--dwarf-special-skills/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/adventurers-kaz/band--elf-special-skills/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/adventurers-kaz/band--noble-special-skills/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/amazons-lustria/band--amazon-special-skills/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/arabian-tomb-raiders/band--arabian-tomb-raiders-special-skills/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/averlanders/halflings-scouts--promotion/compiler.promoted-hero-no-strength-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/battle-monks-of-cathay/band--battle-monks-special-skills/profile.skill-access` | `emissary-limit` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/battle-monks-of-cathay/band--battle-monks-special-skills/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/battle-monks-of-cathay/band--distaste-for-poison/compiler.forbid-item-categories` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/battle-monks-of-cathay/band--strictures/compiler.strictures` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/beastmen-raiders/beastmen-shaman--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/beastmen-raiders/centigors--trample/profile-rule.centigors--trample` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/beastmen-raiders/warhounds-of-chaos--natural-weapons/profile.natural-attacks` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/black-dwarfs/band--chaos-dwarf-special-skills-chaos-engineer/mechanic.chaos-engineer` | `whole--scope--armour-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/black-dwarfs/band--chaos-dwarf-special-skills/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/black-dwarfs/band--hard-head/trait.concussion-immune` | `bearer-scope` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/black-dwarfs/band--hard-to-kill/skill.hard-to-kill` | `bearer-scope` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/black-dwarfs/bull-centaur--no-missile-weapons/compiler.no-missile-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/black-orcs/band--black-orc-special-skills-proven-warrior/compiler.proven-warrior` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/black-orcs/band--black-orc-special-skills/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/black-orcs/band--da-boss-is-dead/unimplemented.black-orcs.band.da-boss-is-dead` | `da-boss-is-dead--scope--rule-grant` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/black-orcs/band--let-the-goons-do-the-work/unimplemented.black-orcs.band.let-the-goons-do-the-work` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/black-orcs/orc-boyz--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/black-orcs/orc-nuttaz--savage/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/black-orcs/orc-nuttaz--savage/psychology.leadership-restrictions` | `whole--scope--loadout-prohibitions` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/bretonnian-buccaneers-sar/pirates--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/bretonnian-chapel-guard/band--chivalry/mechanic.chivalry` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/bretonnian-chapel-guard/band--renowned-virtue/compiler.renowned-virtue` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/bretonnian-chapel-guard/band--shield-bash/special-rule.band--shield-bash` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/bretonnian-chapel-guard/knights-errant--vain/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/bretonnian-chapel-guard/questing-knight--vow-of-poverty/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/bretonnian-chapel-guard/squires--equipment-restrictions/profile.equipment-restrictions` | `holy-relic` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/bretonnian-chapel-guard/squires--equipment-restrictions/profile.equipment-restrictions` | `list-access` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/bretonnian-chapel-guard/squires--knighthood/compiler.knighthood` | `whole--scope--knight-errant-construction` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/bretonnian-chapel-guard/squires--knighthood/compiler.knighthood` | `whole--scope--squire-construction` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/bretonnian-knights-errant-mou/band--knights-feats/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/bretonnian-knights-errant-mou/knights-errant--hand-to-hand-weapon/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/carnival-of-chaos/band--blessings-of-nurgle-bloated-foulness/special-rule.band--blessings-of-nurgle-bloated-foulness` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/carnival-of-chaos/band--blessings-of-nurgle-mark-of-nurgle/special-rule.band--blessings-of-nurgle-mark-of-nurgle` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/carnival-of-chaos/band--blessings-of-nurgle/mechanic.blessings-of-nurgle` | `whole--scope--blessing-construction` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/carnival-of-chaos/nurglings--daemonic-aura/trait.natural-armour-save` | `magical-attacks` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/carnival-of-chaos/plague-bearers--daemonic-aura/trait.natural-armour-save` | `magical-attacks` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/carnival-of-chaos/plague-cart--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/carnival-of-chaos/tainted-ones--nurgles-blessings/compiler.nurgle-s-blessings` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/channel-rats-mim/band--strigany-special-skills-list/unimplemented.channel-rats-mim.band.strigany-special-skills-list` | `strigany-skills` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/clan-angrund-kep/dwarf-troll-slayers--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/clan-angrund-kep/dwarf-troll-slayers--slayer-skills/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/clockworkers-sc/band--constructs/unimplemented.clockworkers-sc.band.constructs` | `in-built-equipment` | — | enlace compartido; consumer vacío |
| `rule/mordheim/clockworkers-sc/clockwork-fiend--construct/unimplemented.clockworkers-sc.clockwork-fiend.construct` | `construct-drug-immunity` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/clockworkers-sc/clockwork-fiend--construct/unimplemented.clockworkers-sc.clockwork-fiend.construct` | `construct-equipment-slot-capacity` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/clockworkers-sc/clockwork-fiend--construct/unimplemented.clockworkers-sc.clockwork-fiend.construct` | `construct-excluded-producers--scope--in-built-equipment` | — | enlace compartido; consumer vacío |
| `rule/mordheim/clockworkers-sc/clockwork-soldiers--construct/unimplemented.clockworkers-sc.clockwork-soldiers.construct` | `construct-drug-immunity` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/clockworkers-sc/clockwork-soldiers--construct/unimplemented.clockworkers-sc.clockwork-soldiers.construct` | `construct-equipment-slot-capacity` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/clockworkers-sc/clockwork-soldiers--construct/unimplemented.clockworkers-sc.clockwork-soldiers.construct` | `construct-excluded-producers--scope--in-built-equipment` | — | enlace compartido; consumer vacío |
| `rule/mordheim/crooked-moon-kep/snotling-mob--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/crooked-moon-kep/squig-hopper--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/crooked-moon-kep/troll--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/cult-of-the-possessed/band--mutations-extra-arm/special-rule.band--mutations-extra-arm` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/cult-of-the-possessed/band--mutations-great-claw/special-rule.band--mutations-great-claw` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/cult-of-the-possessed/band--mutations-tentacle/special-rule.band--mutations-tentacle` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/cult-of-the-possessed/band--mutations/compiler.mutation-purchase-at-recruitment` | `whole--scope--mutation-construction` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/cult-of-the-possessed/mutants--mutations/compiler.mutant-requires-mutation-at-recruitment` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/cult-of-the-possessed/the-possessed--mutations/compiler.possessed-optional-mutations-at-recruitment` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/cursed-cavalcade/band--cursed-cavalcade-special-skills/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/cursed-cavalcade/fighting-ape--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dark-elf-corsairs-mou/corsairs--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dark-elves/band--black-powder-weapons/compiler.no-blackpowder-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dark-elves/band--dark-elf-special-skills-powerful-build/profile.skill-access` | `whole--scope--skill-access` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dark-elves/cold-one-beasthounds--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dark-elves/fellblades--melee-specialists/compiler.no-missile-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/disciples-of-maldred-mou/mercenaries--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dreamwalkers-cult-of-morr-fbg/dreamer--guiding-dream/mechanic.guiding-dream` | `whole--scope--guiding-dream-table` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/druchii-mic/band--disdain/unimplemented.druchii-mic.band.disdain` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/druchii-mic/slavehounds--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/druchii-mic/witch-elves--maibd-poison/unimplemented.druchii-mic.witch-elves.maibd-poison` | `whole--scope--witch-elves-only` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-guildsmen-kaz/band--brewers/unimplemented.dwarf-guildsmen-kaz.band.brewers` | `brew-characteristic` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-guildsmen-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-guildsmen-kaz.band.town-crier-6-inheritance` | `inherited-dwarf-axe` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-guildsmen-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-guildsmen-kaz.band.town-crier-6-inheritance` | `inherited-equipment-lists` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-guildsmen-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-guildsmen-kaz.band.town-crier-6-inheritance` | `inherited-special-skill-access` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-rangers/band--no-arcane-lore/compiler.no-arcane-lore` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-rangers/dwarf-troll-slayers--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-rangers/dwarf-troll-slayers--no-missile-weapons/compiler.no-missile-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-slayer-cult-web/axe-hurlers--born-marksmen/unimplemented.dwarf-slayer-cult-web.axe-hurlers.born-marksmen` | `non-thrown-missile-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-slayer-cult-web/axe-hurlers--born-marksmen/unimplemented.dwarf-slayer-cult-web.axe-hurlers.born-marksmen` | `promotion-shooting-skill-choice--scope--skill-list-access` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-slayer-cult-web/band--slayer-rules/mechanic.psychology-immunity` | `psychology-immunity--scope--kit-restrictions` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-slayer-cult-web/band--slayer-rules/profile.equipment-restrictions` | `no-armour-no-toys` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-slayer-cult-web/band--slayer-special-skills/unimplemented.dwarf-slayer-cult-web.special.slayer-special-skills` | `slayer-skills` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-slayer-cult-web/rememberer--not-a-slayer/unimplemented.dwarf-slayer-cult-web.rememberer.not-a-slayer` | `no-slayer-skill-access` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-slayer-cult-web/rememberer--not-a-slayer/unimplemented.dwarf-slayer-cult-web.rememberer.not-a-slayer` | `not-a-slayer` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-slayers-kaz/band--slayer-special-skills/unimplemented.dwarf-slayers-kaz.band.slayer-special-skills` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-slayers-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-slayers-kaz.band.town-crier-6-inheritance` | `inherited-dwarf-axe` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-slayers-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-slayers-kaz.band.town-crier-6-inheritance` | `inherited-special-skill-access` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-slayers-kaz/giant-slayer--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-slayers-kaz/slayers--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-slayers-kaz/slayers--no-armour-or-missile-weapons/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-slayers-kaz/troll-slayers--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-treasure-hunters/dwarf-troll-slayers--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-treasure-hunters/dwarf-troll-slayers--no-missile-weapons/compiler.no-missile-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/dwarf-treasure-hunters/dwarf-troll-slayers--slayer-skills/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/estalian-corsairs-sar/pirates--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/forest-goblins-lus/gigantic-spider--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/ghost-pirates-sar/gibbets--iron-cage/profile.equipment-restrictions` | `armour-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/gunnery-school-of-nuln/band--proud-to-a-fault/compiler.proud-to-a-fault` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/gunnery-school-of-nuln/marksmen--quick-reload/compiler.quick-reload` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/halflings-mic/band--too-big/unimplemented.halflings-mic.band.too-big` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/halflings-mic/piggies--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/halflings-mic/village-ogre--skills/unimplemented.halflings-mic.village-ogre.skills` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/high-elves-lus/loremaster--tower-of-hoeth/profile.active-weapon-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/high-elves-lus/sword-wardens--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/hochland-bandits/band--powders-expensive/compiler.powder-s-expensive` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/hochland-bandits/duelist--weapon-knowledge/compiler.weapon-knowledge` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/horned-hunters/initiates--strictures/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/horned-hunters/priest-of-taal--strictures/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/horned-hunters/warhounds--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/horned-hunters/zealots--strictures/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/khorne-raiders-sar/flayerkin--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/khorne-raiders-sar/madbrains--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/khorne-raiders-sar/pirates--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/lizardmen-lus/band--bite-attack/compiler.bite-attack` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/lizardmen-lus/band--saurus-poison-application/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/lizardmen-lus/band--saurus-skill-prohibitions/compiler.saurus-skill-prohibitions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/lizardmen-lus/band--scaly-skin/compiler.lizardmen-scaly-skin` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/lizardmen-lus/band--skink-poison-application/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/lizardmen/band--bite-attack/compiler.bite-attack` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/lizardmen/band--saurus-skill-prohibitions/compiler.saurus-skill-prohibitions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/lizardmen/band--scaly-skin/compiler.lizardmen-scaly-skin` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/lords-of-the-marsh-mim/band--scaly-skin/compiler.lizardmen-scaly-skin` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/lords-of-the-marsh-mim/daemon-fimm--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/lost-the-mou/greycoats--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/lustrian-reavers/barbary-monkey--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/lustrian-reavers/estalian-warhound--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/maneaters/band--ogres-special-skills-master-of-arms/mechanic.master-of-arms` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/maneaters/bulls--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/maneaters/captain--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/maneaters/half-growns--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/maneaters/mountain-guide--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/maneaters/sabretusks--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/maneaters/youngbloods--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/marauders-of-chaos/band--mark-of-arkhar/mechanic.mark-of-arkhar` | `whole--scope--frenzy` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/marauders-of-chaos/band--mark-of-onogal/trait.mark-of-onogal-the-crow` | `mark-admitted-effects` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/marauders-of-chaos/warhounds-of-chaos--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/marauders-of-chaos/warhounds-of-chaos--natural-weapons/profile.natural-attacks` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/mazzalupo-web/black-sheep--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/mercenaries/band--middenheim-physical-prowess/profile.characteristics` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/mootlanders/moot-elder--halfling-list/weapon.pistol` | `whole--scope--halfling-list-access` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/necrarchs-mou/abomination--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/necrarchs-mou/banshee--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/necrarchs-mou/skeleton--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/abomination--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/zombie--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/night-goblins-mic/cave-squigs--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/night-goblins-mic/fanatics--frantic/profile-rule.fanatics--frantic` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/night-goblins-mic/snotling-mob-consists-of-5-snotlings--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/night-goblins-mic/troll--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/night-goblins-web/band--promoted-henchmen-no-strength/compiler.promoted-hero-no-strength-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/night-goblins-web/boss--da-biggest-boss/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/night-goblins-web/shaman--fungus-brew/unimplemented.night-goblins-web.shaman.fungus-brew` | `fungus-dizzy` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/nipponese-expedition-web/band--nippon-special-skills/unimplemented.nipponese-expedition-web.special.nippon-special-skills` | `nippon-skills` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/nipponese-expedition-web/vim-to-mage--tenants-of-the-order/unimplemented.nipponese-expedition-web.vim-to-mage.tenants-of-the-order` | `owned-equipment-ban` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/nipponese-expedition-web/warrior-monks--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/norse-explorers-btb/beserkers--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/norse-explorers-btb/wolves--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/norse-explorers-btb/wulfen--natural-weapons/profile.natural-attacks` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/norse-explorers-lustria/beserkers--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/norse-explorers-lustria/wulfen--natural-weapons/profile.natural-attacks` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/ogre-hunting-party-web/band--huuuuge/mechanic.causes-fear` | `cause-fear--scope--equipment-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/ogre-hunting-party-web/band--huuuuge/profile.equipment-restrictions` | `armour-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/ogre-hunting-party-web/band--ogre-hunting-skills/unimplemented.ogre-hunting-party-web.special.ogre-hunting-skills` | `ogre-skill-list-rest` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/ogre-hunting-party-web/ogre-hunter--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/ogre-hunting-party-web/trappers--veteran-tracker/unimplemented.ogre-hunting-party-web.trappers.veteran-tracker` | `starting-skill-choice` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/orc-mob/orc-shaman--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/order-of-the-mare-web/paragon--vow-of-poverty/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/ostlanders/ogre--skills/compiler.promoted-hero-skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/ostlanders/priest-of-taal--strictures/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/ostlanders/ruffians--no-missile-weapons/compiler.no-missile-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/outlaws-of-stirwood-forest-redux-fbg/band--bow-restrictions/mechanic.bow-discipline` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/outlaws-of-stirwood-forest-redux-fbg/band--bow-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/outlaws-of-stirwood-forest/band--bow-discipline/mechanic.bow-discipline` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/outlaws-of-stirwood-forest/band--bow-discipline/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/outlaws-of-stirwood-forest/cleric--disciple-of-sigmar/mechanic.disciple-of-sigmar` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/pirates-of-the-cathayan-sea-sar/pirates--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/pirates/swabbies--rabble/compiler.swabbie-rabble-loadout` | `whole--scope--equipment-list-access` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/pit-fighters/band--pit-fighter-skill-arms-master/compiler.ignore-difficult-to-use-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/pit-fighters/band--troll-slayer-special-skills-berserker/compiler.berserker-incompatible-with-ferocious-charge` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/pit-fighters/dwarf-troll-slayer--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/pit-fighters/dwarf-troll-slayer--no-missile-weapons/compiler.no-missile-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/pit-fighters/ogre-pit-fighter--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/pit-fighters/ogre-pit-fighter--skills/compiler.promoted-hero-skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/protectorate-of-sigmar-lotd3/hound--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/restless-dead/liche--warrior-wizard/compiler.warrior-wizard` | `whole--scope--armour-allowance` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/sartosan-pirates-sar/band--foreign-variant-equipment/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/sartosan-pirates-sar/pirates--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/savage-orcs-kaz/band--orc-special-skills/unimplemented.savage-orcs-kaz.band.orc-special-skills` | `orc-special-skill-access` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/savage-orcs-kaz/gobbo-boyz--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/savage-orcs-kaz/nuttaz--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/shadow-warriors/band--distaste-for-poison/compiler.forbid-item-categories` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/shadow-warriors/band--shadow-warrior-special-skills-powerful-build/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/shallows-beasts-mim/mutant-priest--bite-attack/compiler.strikes-last-bite` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/silent-brotherhood-sc/band--the-silence/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/sisters-of-sigmar/augur--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/sisters-of-sigmar/band--sigmarite-hammer-pair/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/skaven-clan-eshin/band--skaven-special-skills-tail-fighting/special-rule.band--skaven-special-skills-tail-fighting` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/skaven-clan-pestilens/band--clan-pestilens-special-skills-censer-bearer/compiler.censer-bearer-loadout` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/skaven-clan-pestilens/band--clan-pestilens-special-skills-contagious/unimplemented.skaven-clan-pestilens.band.clan-pestilens-special-skills-contagious` | `contagious-rotten-body-prerequisite` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/skaven-clan-pestilens/band--clan-pestilens-special-skills-ignore-pain/skill.ignore-pain` | `requires-resilient` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/skaven-of-clan-mors-kaz/band--rulebook-inheritance/unimplemented.skaven-of-clan-mors-kaz.band.rulebook-inheritance` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/skaven-of-clan-moulder-web/band--clan-moulder-special-skills/unimplemented.skaven-of-clan-moulder-web.special.clan-moulder-special-skills` | `black-hunger--scope--skill-list-access` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/skaven-of-clan-moulder-web/band--mutations/unimplemented.skaven-of-clan-moulder-web.band.mutations` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/skaven-of-clan-moulder-web/rat-ogres--its-alive/unimplemented.skaven-of-clan-moulder-web.rat-ogres.its-alive` | `starting-mutation` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/skaven-of-clan-skryre-kaz/band--rulebook-inheritance/unimplemented.skaven-of-clan-skryre-kaz.band.rulebook-inheritance` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/skaven-of-clan-skryre-rel/giant-rats--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/skaven-of-clan-skryre-rel/skaven-slaves--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/slavers-rel/hounds--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/snotlings-web/band--small-hands/unimplemented.snotlings-web.band.small-hands` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/snotlings-web/bigsnotz--big-bully/unimplemented.snotlings-web.special.big-bully` | `whole` | — | enlace compartido; consumer vacío |
| `rule/mordheim/snotlings-web/runts--teeny-hands/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/snotlings-web/shoota-teams--one-missile-weapon/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/snotlings-web/shoota-teams--teamwork/unimplemented.snotlings-web.shoota-teams.teamwork` | `single-model-projection` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/snotlings-web/snotling-mobs--teamwork/unimplemented.snotlings-web.snotling-mobs.teamwork` | `single-model-projection` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/sons-of-hashut/blunderbuss-chaos-dwarfs--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/strigoi-kaz/bats--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/strigoi-kaz/charnel-guard--cunning/unimplemented.strigoi-kaz.charnel-guard.cunning` | `weapons-training-permission` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/strigoi-kaz/charnel-guard--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/strigoi-kaz/fell-bats--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/strigoi-kaz/ghouls--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/strigoi-kaz/skeletons--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/strigoi-kaz/vampire--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/survivors-of-strigos-sylv/strigoi-vampire--iron-sinews/profile.characteristics` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/tileans/band--remasen-officer-leadership/unimplemented.tileans.band.remasen-officer-leadership` | `leadership-characteristic-bonus` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/tomb-guardians/liche-priest--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/tomb-guardians/tomb-scorpions--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/underworld-alliance-mim/band--power-grab/unimplemented.underworld-alliance-mim.band.power-grab` | `supplied-leadership-adjustment` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/wasteland-privateers-sar/pirates--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/watchmen-mim/band--fanatical/unimplemented.watchmen-mim.band.fanatical` | `fanatical-advance--scope--automatic-leadership` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/witch-hunters/flagellants--no-missile-weapons/compiler.no-missile-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/witch-hunters/war-hounds--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/wood-elves-of-arden-mou/ivy-ferret--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/mordheim/woodsmen-de-artois-mou/band--quarterstaff/compiler.woodsmen-quarterstaff` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-deathbringers/band--no-noise/compiler.no-blackpowder-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/dwarf-troll-slayers--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/dwarf-troll-slayers--no-missile-weapons/compiler.no-missile-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/dwarf-troll-slayers--slayer-skills/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-greenskins/cave-squigs--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-greenskins/orc-shaman--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-greenskins/troll--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-pit-fighters/band--pit-fighter-skill-arms-master/compiler.ignore-difficult-to-use-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-pit-fighters/dwarf-troll-slayer--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-pit-fighters/dwarf-troll-slayer--no-missile-weapons/compiler.no-missile-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-pit-fighters/dwarf-troll-slayer--slayer-skill-options/compiler.slayer-skill-options` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-pit-fighters/ogre-pit-fighter--skills/compiler.promoted-hero-skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-sons-of-nagarythe/band--honourable/compiler.forbid-item-categories` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-sons-of-nagarythe/band--shadow-warrior-special-skills-powerful-build/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--strigoi-power-monstrosity/special-rule.band--strigoi-power-monstrosity` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--vampiric-powers/compiler.vampiric-powers` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-undead-bloodlines/blood-dragon-vampire--warriors-code/compiler.warrior-s-code` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-undead-bloodlines/lahmia-vampire--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-undead-bloodlines/necrarch-vampire--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/chaos-streets-undead-bloodlines/necrarch-vampire--no-strength-skills/compiler.forbid-skill-categories` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-cursed-of-karak-zorn/cannibal-dwarfs--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-cursed-of-karak-zorn/shadowed--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-cursed-of-karak-zorn/troll-slayer--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-cursed-of-karak-zorn/troll-slayer--no-missile-weapons/compiler.no-missile-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-lahmian-brotherhood/band--background-selection/compiler.foreign-or-native-background` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-lahmian-brotherhood/blood-slaves--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-lahmian-brotherhood/lackeys--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-lahmian-brotherhood/necromancer--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-lahmian-brotherhood/skeleton-warriors--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-lahmian-brotherhood/spirits--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-mages/archmage--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-mages/mage--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-mages/witch--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-necromancers/band--necromantic-modification-bone-armour/profile.characteristics` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-necromancers/band--necromantic-modification-enhanced-reflexes/profile.characteristics` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-necromancers/band--necromantic-modification-killers-precision/profile.characteristics` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-necromancers/band--necromantic-modification-multiple-limbs/special-rule.band--necromantic-modification-multiple-limbs` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-necromancers/band--necromantic-modification-paladin-of-horror/unimplemented.khemri-necromancers.band.necromantic-modification-paladin-of-horror` | `leadership-characteristic-bonus` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-thieves-guild/guild-chief--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-thieves-guild/guild-enforcer--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-thieves-guild/guild-hashashiyyin--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-thieves-guild/guild-master-thief--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-thieves-guild/guild-ruffian--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-thieves-guild/guild-thief--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-tomb-guardians/mortuary-acolytes--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-tomb-guardians/mortuary-priest--no-armour/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/khemri-tomb-guardians/tomb-scorpions--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-clan-pestilens/band--clan-pestilens-special-skills-censer-bearer/compiler.censer-bearer-loadout` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-clan-pestilens/band--clan-pestilens-special-skills-contagious/trait.contagious` | `contagious-rotten-body-prerequisite` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-dark-elves/band--ancestral-customs/compiler.no-blackpowder-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-dark-elves/band--dark-elf-special-skills-strong-constitution/profile.skill-access` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-dark-elves/corsairs--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-dark-elves/dark-elf-sorceress--equipment-restrictions/profile.equipment-restrictions` | `whole--scope--equipment-bars` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-dark-elves/dark-prince--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-dark-elves/darkblades--close-combat-specialists/compiler.no-missile-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-dark-elves/darkblades--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-high-elves/band--ancestral-customs/compiler.no-blackpowder-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-high-elves/band--haughty/compiler.haughty` | `whole--scope--dwarf-equipment-bar` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-high-elves/band--honourable/compiler.forbid-item-categories` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-high-elves/explorers--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-high-elves/sea-guard--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-high-elves/sword-guardians--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-lizardmen/band--sacred-mark-huge-jaws/trait.huge-jaws` | `whole--scope--recipients` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-lizardmen/band--sacred-mark-venom-glands/special-rule.band--sacred-mark-venom-glands` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-lizardmen/band--sacred-marks/compiler.sacred-marks` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-lizardmen/band--scaly-skin/compiler.lizardmen-scaly-skin` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-lizardmen/kroxigor--scaly-skin-4plus/trait.natural-armour-save` | `stacks-with-armour-but-not-hardened-leather` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-lizardmen/kroxigor--scaly-skin-4plus/trait.natural-armour-stacks` | `stacks-with-armour-but-not-hardened-leather` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-lizardmen/kroxigor--scaly-skin-4plus/trait.natural-armour-worst-save` | `stacks-with-armour-but-not-hardened-leather` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-lizardmen/saurus-braves--bite-attack/compiler.bite-attack` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-lizardmen/saurus-braves--no-missile-weapons/compiler.no-missile-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-lizardmen/saurus-totem-warrior--bite-attack/compiler.bite-attack` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-lizardmen/saurus-totem-warrior--no-academic-skills/compiler.forbid-skill-categories` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-lizardmen/saurus-totem-warrior--no-missile-weapons/compiler.no-missile-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-lizardmen/skink-braves--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-lizardmen/skink-great-crests--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-norse/marauders--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-pirates/band--hired-swords/compiler.pirate-human-mercenary-equipment-access` | `whole--scope--equipment-access` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-pirates/boatswains--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-pirates/cabin-boys--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-pirates/crew--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-pirates/ships-mates--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-pirates/swabbies--rabble/compiler.swabbie-rabble-loadout` | `whole--scope--equipment-list-access` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-savage-goblins/band--savage-goblin-special-skills-master-of-throwing-weapons/mechanic.master-of-throwing-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-savage-goblins/big-boss--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-savage-goblins/red-teeth--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-savage-goblins/trackers--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-savage-goblins/trackers--tracker-gear/compiler.tracker-gear` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/lustria-tileans/band--remas-officer-leadership/unimplemented.lustria-tileans.band.remas-officer-leadership` | `leadership-characteristic-bonus` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/trollheim-cult-of-the-possessed/band--mutation-purchase/compiler.mutation-purchase-at-recruitment` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/trollheim-cult-of-the-possessed/band--mutations-extra-arm/special-rule.band--mutations-extra-arm` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/trollheim-cult-of-the-possessed/band--mutations-great-claw/special-rule.band--mutations-great-claw` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/trollheim-cult-of-the-possessed/mutants--mutations/compiler.mutant-requires-mutation-at-recruitment` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/trollheim-cult-of-the-possessed/the-possessed--mutations/compiler.possessed-optional-zero-to-two-mutations-at-recruitment` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/trollheim-mercenaries/band--middenheim-physical-prowess/profile.characteristics` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/trollheim-skaven-clan-eshin/band--skaven-special-skills-tail-fighting/special-rule.band--skaven-special-skills-tail-fighting` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/trollheim-undead/dire-wolves--equipment-restrictions/profile.equipment-restrictions` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `rule/trollheim/trollheim-witch-hunters/flagellants--no-missile-weapons/compiler.no-missile-weapons` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/adventurers-kaz/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/adventurers-kaz/profiles.yaml/@/profiles/5/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/araby-smugglers-sar/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/araby-smugglers-sar/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/araby-smugglers-sar/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/araby-smugglers-sar/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/araby-smugglers-sar/equipment-access.yaml/@/equipment_lists/1/items/3/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/araby-smugglers-sar/equipment-access.yaml/@/equipment_lists/2/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/araby-smugglers-sar/equipment-access.yaml/@/equipment_lists/2/items/4/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/averlanders/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/averlanders/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/battle-monks-of-cathay/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/beastmen-raiders/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/black-dwarfs/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/black-dwarfs/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/black-orcs/equipment-access.yaml/@/equipment_lists/1/items/5/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/black-orcs/equipment-access.yaml/@/equipment_lists/1/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/black-orcs/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/black-orcs/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/black-orcs/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/black-orcs/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/blood-dragons-mou/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/blood-dragons-mou/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/blood-dragons-mou/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/blood-dragons-mou/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/blood-dragons-mou/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-brigands-mou/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-brigands-mou/equipment-access.yaml/@/equipment_lists/0/items/11/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-brigands-mou/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-brigands-mou/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-brigands-mou/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-brigands-mou/equipment-access.yaml/@/equipment_lists/0/items/17/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-brigands-mou/equipment-access.yaml/@/equipment_lists/0/items/18/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-brigands-mou/equipment-access.yaml/@/equipment_lists/0/items/19/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-buccaneers-sar/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/bretonnian-buccaneers-sar/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-buccaneers-sar/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/bretonnian-buccaneers-sar/equipment-access.yaml/@/equipment_lists/2/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/bretonnian-buccaneers-sar/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-buccaneers-sar/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-buccaneers-sar/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-buccaneers-sar/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-buccaneers-sar/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-buccaneers-sar/profiles.yaml/@/profiles/5/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-chapel-guard/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-chapel-guard/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-chapel-guard/profiles.yaml/@/profiles/3/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/bretonnian-knights-errant-mou/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole--scope--armour-upgrade` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/bretonnian-knights-errant-mou/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/brood-of-ghurash-the-sc/equipment-access.yaml/@/equipment_lists/0/items/0/notes/unclassified` | `whole--scope--brood-dagger-bearer` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/brood-of-ghurash-the-sc/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/call-of-the-night-haint-mim/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `ethereal-heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/call-of-the-night-haint-mim/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/call-of-the-night-haint-mim/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/call-of-the-night-haint-mim/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/call-of-the-night-haint-mim/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/carnival-of-chaos/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/carnival-of-chaos/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/carnival-of-chaos/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/channel-rats-mim/equipment-access.yaml/@/equipment_lists/0/items/11/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/channel-rats-mim/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/channel-rats-mim/equipment-access.yaml/@/equipment_lists/0/items/17/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/channel-rats-mim/equipment-access.yaml/@/equipment_lists/0/items/18/notes/unclassified` | `whole--scope--tinker-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/channel-rats-mim/equipment-access.yaml/@/equipment_lists/0/items/19/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/channel-rats-mim/equipment-access.yaml/@/equipment_lists/0/items/3/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/channel-rats-mim/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/channel-rats-mim/equipment-access.yaml/@/equipment_lists/1/items/2/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/clan-angrund-kep/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole--scope--bearer-restriction` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/clan-angrund-kep/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole--scope--item-identity` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/clan-angrund-kep/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` | `whole--scope--gromril-allowance` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/clan-angrund-kep/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/clan-angrund-kep/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/clockworkers-sc/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/clockworkers-sc/equipment-access.yaml/@/equipment_lists/0/items/8/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/clockworkers-sc/equipment-access.yaml/@/equipment_lists/2/items/0/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/clockworkers-sc/equipment-access.yaml/@/equipment_lists/2/items/1/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/clockworkers-sc/equipment-access.yaml/@/equipment_lists/2/items/2/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/clockworkers-sc/equipment-access.yaml/@/equipment_lists/2/items/3/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/clockworkers-sc/equipment-access.yaml/@/equipment_lists/2/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/clockworkers-sc/equipment-access.yaml/@/equipment_lists/2/items/5/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/clockworkers-sc/equipment-access.yaml/@/equipment_lists/2/items/6/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/clockworkers-sc/equipment-access.yaml/@/equipment_lists/2/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/clockworkers-sc/equipment-access.yaml/@/equipment_lists/2/items/8/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/clockworkers-sc/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/clockworkers-sc/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/crooked-moon-kep/equipment-access.yaml/@/equipment_lists/0/items/8/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/crooked-moon-kep/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/crooked-moon-kep/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/crooked-moon-kep/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/crooked-moon-kep/profiles.yaml/@/profiles/8/equipment_restrictions/0/unclassified` | `pointy-stick-counts-as-a-dagger` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/cult-of-the-possessed/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/cursed-cavalcade/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/cursed-cavalcade/profiles.yaml/@/profiles/3/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/cursed-cavalcade/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/cursed-cavalcade/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/cursed-cavalcade/profiles.yaml/@/profiles/8/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dark-elf-corsairs-mou/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole--scope--kit` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/dark-elf-corsairs-mou/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole--scope--kit` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/dark-elf-corsairs-mou/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dark-elves/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dark-elves/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dark-elves/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dark-elves/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dark-elves/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole--scope--equipment-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dark-elves/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/disciples-of-maldred-mou/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/disciples-of-maldred-mou/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/disciples-of-maldred-mou/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/disciples-of-maldred-mou/profiles.yaml/@/profiles/3/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/disciples-of-maldred-mou/profiles.yaml/@/profiles/4/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dreamwalkers-cult-of-morr-fbg/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dreamwalkers-cult-of-morr-fbg/equipment-access.yaml/@/equipment_lists/0/items/8/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dreamwalkers-cult-of-morr-fbg/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/druchii-mic/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `whole--scope--beastmaster-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/druchii-mic/equipment-access.yaml/@/equipment_lists/3/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/druchii-mic/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/druchii-mic/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `fights-with-claws-and-needs-no-weapons` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dwarf-rangers/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dwarf-slayer-cult-web/equipment-access.yaml/@/equipment_lists/1/items/7/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dwarf-slayer-cult-web/equipment-access.yaml/@/equipment_lists/2/items/3/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dwarf-slayers-kaz/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `whole--scope--missile-bar` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dwarf-slayers-kaz/equipment-access.yaml/@/equipment_lists/0/items/11/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dwarf-slayers-kaz/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dwarf-slayers-kaz/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dwarf-slayers-kaz/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dwarf-slayers-kaz/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dwarf-slayers-kaz/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dwarf-slayers-kaz/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dwarf-slayers-kaz/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `supplied-human-rememberer` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/dwarf-slayers-kaz/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/estalian-corsairs-sar/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/estalian-corsairs-sar/equipment-access.yaml/@/equipment_lists/0/items/16/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/estalian-corsairs-sar/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/estalian-corsairs-sar/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/estalian-corsairs-sar/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/estalian-corsairs-sar/equipment-access.yaml/@/equipment_lists/2/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/estalian-corsairs-sar/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/estalian-corsairs-sar/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/estalian-corsairs-sar/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/estalian-corsairs-sar/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/estalian-corsairs-sar/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/estalian-corsairs-sar/profiles.yaml/@/profiles/5/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/fallen-the-rel/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/fallen-the-rel/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/fallen-the-rel/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/fen-guard-mim/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/fen-guard-mim/equipment-access.yaml/@/equipment_lists/0/items/11/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/fen-guard-mim/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/fen-guard-mim/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/fen-guard-mim/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/fen-guard-mim/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/fen-guard-mim/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/fen-guard-mim/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/fen-guard-mim/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/fen-guard-mim/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/forest-goblins-lus/equipment-access.yaml/@/equipment_lists/2/items/0/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/forest-goblins-lus/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/forest-goblins/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/forest-goblins/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/forest-goblins/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/forest-goblins/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/ghost-pirates-sar/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/ghost-pirates-sar/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/ghost-pirates-sar/equipment-access.yaml/@/equipment_lists/0/items/8/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/ghost-pirates-sar/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/ghost-pirates-sar/equipment-access.yaml/@/equipment_lists/2/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/ghutani-rel/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/ghutani-rel/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/grave-robbers-sylv/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/grave-robbers-sylv/equipment-access.yaml/@/equipment_lists/0/items/16/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/grave-robbers-sylv/equipment-access.yaml/@/equipment_lists/0/items/17/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/grave-robbers-sylv/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/grave-robbers-sylv/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/grave-robbers-sylv/equipment-access.yaml/@/equipment_lists/1/items/5/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/guild-of-disgraced-engineers-mim/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/halflings-mic/equipment-access.yaml/@/equipment_lists/0/items/0/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/halflings-mic/equipment-access.yaml/@/equipment_lists/0/items/0/notes/unclassified` | `whole--scope--name-alias` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/halflings-mic/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/halflings-mic/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `halfling-cooks-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/halflings-mic/equipment-access.yaml/@/equipment_lists/0/items/11/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/halflings-mic/equipment-access.yaml/@/equipment_lists/0/items/2/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/halflings-mic/equipment-access.yaml/@/equipment_lists/0/items/3/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/halflings-mic/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/halflings-mic/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/halflings-mic/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/halflings-mic/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/high-elves-lus/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/high-elves-lus/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/high-elves-lus/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/high-elves-lus/equipment-access.yaml/@/equipment_lists/1/items/6/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/high-elves-lus/equipment-access.yaml/@/equipment_lists/2/items/0/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/high-elves-lus/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/high-elves-lus/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/horned-hunters/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/horned-hunters/profiles.yaml/@/profiles/1/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/horned-hunters/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/horned-hunters/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/house-guard-sc/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/house-guard-sc/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/house-guard-sc/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/house-guard-sc/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/house-guard-sc/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/house-guard-sc/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/house-guard-sc/equipment-access.yaml/@/equipment_lists/2/items/0/notes/unclassified` | `item-note--scope--plus-four-save` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/house-guard-sc/equipment-access.yaml/@/equipment_lists/2/items/1/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/house-guard-sc/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/khorne-raiders-sar/equipment-access.yaml/@/equipment_lists/0/items/16/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/equipment-access.yaml/@/equipment_lists/0/items/3/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/equipment-access.yaml/@/equipment_lists/1/items/6/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/equipment-access.yaml/@/equipment_lists/1/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/equipment-access.yaml/@/equipment_lists/1/items/8/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/profiles.yaml/@/profiles/5/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/khorne-raiders-sar/profiles.yaml/@/profiles/5/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/kislevites/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/kislevites/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/kislevites/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/kislevites/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/knights-of-the-bitter-moors-mim/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/knights-of-the-bitter-moors-mim/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lizardmen-lus/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lizardmen-lus/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lizardmen-lus/equipment-access.yaml/@/equipment_lists/1/items/10/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lizardmen-lus/equipment-access.yaml/@/equipment_lists/1/items/3/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lizardmen-lus/equipment-access.yaml/@/equipment_lists/2/items/0/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lizardmen-lus/equipment-access.yaml/@/equipment_lists/2/items/1/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lizardmen-lus/equipment-access.yaml/@/equipment_lists/2/items/3/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lizardmen-lus/equipment-access.yaml/@/equipment_lists/2/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lizardmen-lus/equipment-access.yaml/@/equipment_lists/2/items/5/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lizardmen-lus/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lizardmen/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lizardmen/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lizardmen/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lords-of-the-marsh-mim/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/lords-of-the-marsh-mim/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lost-the-mou/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lost-the-mou/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/low-kings-mim/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/low-kings-mim/equipment-access.yaml/@/equipment_lists/0/items/20/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/low-kings-mim/equipment-access.yaml/@/equipment_lists/0/items/21/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/low-kings-mim/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lustrian-reavers/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/lustrian-reavers/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/maneaters/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/maneaters/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/maneaters/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/maneaters/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/maneaters/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/maneaters/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/maneaters/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/marauders-of-chaos/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/marauders-of-chaos/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/masters-of-horror-sylv/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/masters-of-horror-sylv/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/masters-of-horror-sylv/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/mazzalupo-web/equipment-access.yaml/@/equipment_lists/2/items/13/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/mazzalupo-web/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/mercenaries/equipment-access.yaml/@/equipment_lists/0/items/18/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/merchant-caravans/equipment-access.yaml/@/equipment_lists/0/items/11/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/merchant-caravans/equipment-access.yaml/@/equipment_lists/1/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/merchant-caravans/equipment-access.yaml/@/equipment_lists/1/items/5/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/metal-mongers-mim/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/metal-mongers-mim/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/metal-mongers-mim/equipment-access.yaml/@/equipment_lists/0/items/2/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/metal-mongers-mim/equipment-access.yaml/@/equipment_lists/0/items/8/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/metal-mongers-mim/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/metal-mongers-mim/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/metal-mongers-mim/equipment-access.yaml/@/equipment_lists/1/items/2/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/metal-mongers-mim/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/militiant-mootlanders-mim/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/militiant-mootlanders-mim/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/militiant-mootlanders-mim/equipment-access.yaml/@/equipment_lists/0/items/2/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/militiant-mootlanders-mim/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/militiant-mootlanders-mim/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/militiant-mootlanders-mim/equipment-access.yaml/@/equipment_lists/1/items/2/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/mootlanders/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/muzil-rel/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-mou/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-mou/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-mou/equipment-access.yaml/@/equipment_lists/1/items/12/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-mou/equipment-access.yaml/@/equipment_lists/1/items/13/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-mou/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-mou/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-mou/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-mou/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-the-soul-stealers-lotd1/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-the-soul-stealers-lotd1/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-the-soul-stealers-lotd1/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-the-soul-stealers-lotd1/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-the-soul-stealers-lotd1/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-the-soul-stealers-lotd1/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/necrarchs-the-soul-stealers-lotd1/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/night-goblins-kaz/equipment-access.yaml/@/equipment_lists/1/items/0/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/night-goblins-kaz/equipment-access.yaml/@/equipment_lists/1/items/2/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/night-goblins-kaz/equipment-access.yaml/@/equipment_lists/1/items/3/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/night-goblins-kaz/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/night-goblins-kaz/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/night-goblins-kaz/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `pointy-stick-counts-as-a-dagger` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/night-goblins-mic/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/night-goblins-mic/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/night-goblins-mic/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/night-goblins-web/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/night-goblins-web/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/night-goblins-web/profiles.yaml/@/profiles/8/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/night-goblins-web/profiles.yaml/@/profiles/9/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/nipponese-expedition-web/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/nipponese-expedition-web/profiles.yaml/@/profiles/1/equipment_restrictions/1/unclassified` | `label` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/nipponese-expedition-web/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/norse-explorers-btb/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/norse-explorers-btb/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/norse-explorers-lustria/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/norse-explorers-lustria/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/ogre-hunting-party-web/equipment-access.yaml/@/equipment_lists/0/items/0/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/ogre-hunting-party-web/equipment-access.yaml/@/equipment_lists/1/items/13/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/ogre-hunting-party-web/equipment-access.yaml/@/equipment_lists/1/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/ogre-hunting-party-web/equipment-access.yaml/@/equipment_lists/1/items/8/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/ogre-hunting-party-web/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/ogre-hunting-party-web/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/orc-mob/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/orc-mob/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/orc-pirates-sar/equipment-access.yaml/@/equipment_lists/0/items/2/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/orc-pirates-sar/equipment-access.yaml/@/equipment_lists/1/items/12/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/orc-pirates-sar/equipment-access.yaml/@/equipment_lists/1/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/orc-pirates-sar/equipment-access.yaml/@/equipment_lists/1/items/7/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/orc-pirates-sar/equipment-access.yaml/@/equipment_lists/1/items/8/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/order-of-the-mare-web/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/order-of-the-mare-web/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/order-of-the-mare-web/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/order-of-the-mare-web/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/order-of-the-mare-web/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/order-of-the-mare-web/equipment-access.yaml/@/equipment_lists/1/items/10/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/order-of-the-mare-web/equipment-access.yaml/@/equipment_lists/1/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/order-of-the-mare-web/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `fights-with-hooves-without-penalty--scope--may-never-take-equipment` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/ostlanders/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/ostlanders/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest-redux-fbg/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest-redux-fbg/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `whole--scope--outlaws-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest-redux-fbg/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest-redux-fbg/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest/equipment-access.yaml/@/equipment_lists/0/items/11/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest/equipment-access.yaml/@/equipment_lists/0/items/8/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest/profiles.yaml/@/profiles/2/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/outlaws-of-stirwood-forest/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pirates-of-the-cathayan-sea-sar/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/pirates-of-the-cathayan-sea-sar/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pirates-of-the-cathayan-sea-sar/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pirates-of-the-cathayan-sea-sar/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/pirates-of-the-cathayan-sea-sar/equipment-access.yaml/@/equipment_lists/2/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/pirates-of-the-cathayan-sea-sar/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pirates-of-the-cathayan-sea-sar/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pirates-of-the-cathayan-sea-sar/profiles.yaml/@/profiles/2/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pirates-of-the-cathayan-sea-sar/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pirates-of-the-cathayan-sea-sar/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pirates-of-the-cathayan-sea-sar/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pirates-of-the-cathayan-sea-sar/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pirates/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pirates/profiles.yaml/@/profiles/5/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pit-fighters/equipment-access.yaml/@/equipment_lists/2/items/10/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pit-fighters/equipment-access.yaml/@/equipment_lists/2/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pit-fighters/equipment-access.yaml/@/equipment_lists/2/items/8/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pit-fighters/equipment-access.yaml/@/equipment_lists/2/items/9/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pit-fighters/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/pit-fighters/profiles.yaml/@/profiles/5/equipment_restrictions/1/unclassified` | `equipment-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/protectorate-of-sigmar-lotd3/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/protectorate-of-sigmar-lotd3/equipment-access.yaml/@/equipment_lists/0/items/16/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/protectorate-of-sigmar-lotd3/equipment-access.yaml/@/equipment_lists/0/items/17/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/protectorate-of-sigmar-lotd3/equipment-access.yaml/@/equipment_lists/0/items/18/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/protectorate-of-sigmar-lotd3/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/protectorate-of-sigmar-lotd3/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `protectorate-equipment-list` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/protectorate-of-sigmar-lotd3/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `protectorate-equipment-list` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/protectorate-of-sigmar-lotd3/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole--scope--equipment-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/protectorate-of-sigmar-lotd3/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `protectorate-equipment-list` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/protectorate-of-sigmar-lotd3/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `protectorate-equipment-list` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/protectorate-of-sigmar-lotd3/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `protectorate-equipment-list` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/protectorate-of-sigmar-lotd3/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/restless-dead/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/restless-dead/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/restless-dead/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sartosan-pirates-sar/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/sartosan-pirates-sar/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sartosan-pirates-sar/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sartosan-pirates-sar/equipment-access.yaml/@/equipment_lists/0/items/18/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sartosan-pirates-sar/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sartosan-pirates-sar/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sartosan-pirates-sar/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/sartosan-pirates-sar/equipment-access.yaml/@/equipment_lists/2/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/sartosan-pirates-sar/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sartosan-pirates-sar/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sartosan-pirates-sar/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sartosan-pirates-sar/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sartosan-pirates-sar/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sartosan-pirates-sar/profiles.yaml/@/profiles/5/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/savage-orcs-kaz/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `whole--scope--bearer-bar` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/savage-orcs-kaz/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `whole--scope--combination-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/savage-orcs-kaz/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `whole--scope--bearer-allowance` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/savage-orcs-kaz/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `orc-only-item-restriction--scope--not-with-warpaint-or-light-armour` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/savage-orcs-kaz/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `orc-only-item-restriction--scope--orc-bearers-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/savage-orcs-kaz/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/savage-orcs-kaz/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/savage-orcs-kaz/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/savage-orcs-kaz/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/savage-orcs-kaz/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/savage-orcs-sar/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/savage-orcs-sar/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/savage-orcs-sar/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sea-ghosts-mim/equipment-access.yaml/@/equipment_lists/0/items/17/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sea-ghosts-mim/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/sea-ghosts-mim/equipment-access.yaml/@/equipment_lists/1/items/2/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/sea-ghosts-mim/equipment-access.yaml/@/equipment_lists/1/items/3/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sea-ghosts-mim/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/shadow-warriors/equipment-access.yaml/@/equipment_lists/0/items/11/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/shadow-warriors/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/shadow-warriors/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/shadow-warriors/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/shadow-warriors/equipment-access.yaml/@/equipment_lists/0/items/16/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/shadow-warriors/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/shadow-warriors/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole--scope--equipment-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/shallows-beasts-mim/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/shallows-beasts-mim/equipment-access.yaml/@/equipment_lists/0/items/18/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/shallows-beasts-mim/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/shallows-beasts-mim/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/shallows-beasts-mim/equipment-access.yaml/@/equipment_lists/1/items/4/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/silent-brotherhood-sc/equipment-access.yaml/@/equipment_lists/0/items/3/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/silent-brotherhood-sc/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/silent-brotherhood-sc/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/silent-brotherhood-sc/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/silent-brotherhood-sc/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/silent-brotherhood-sc/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sisters-of-sigmar/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sisters-of-sigmar/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sisters-of-sigmar/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sisters-of-sigmar/equipment-access.yaml/@/equipment_lists/0/items/3/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-clan-eshin/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-clan-eshin/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-clan-pestilens/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-clan-pestilens/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-mors-kaz/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-moulder-web/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/skaven-of-clan-moulder-web/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-moulder-web/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-moulder-web/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-moulder-web/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-moulder-web/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-pestilens-lus/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/skaven-of-clan-pestilens-lus/equipment-access.yaml/@/equipment_lists/1/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-pestilens-lus/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-pestilens-mou/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/skaven-of-clan-pestilens-mou/equipment-access.yaml/@/equipment_lists/1/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-pestilens-mou/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-pristekk-sc/equipment-access.yaml/@/equipment_lists/2/items/1/notes/unclassified` | `whole--scope--item-nature` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/skaven-of-clan-pristekk-sc/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-pristekk-sc/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-skryre-kaz/equipment-access.yaml/@/equipment_lists/0/items/11/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-skryre-rel/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-skryre-rel/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-skryre-rel/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-skryre-rel/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/skaven-of-clan-skryre-rel/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slavers-rel/equipment-access.yaml/@/equipment_lists/0/items/19/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slavers-rel/equipment-access.yaml/@/equipment_lists/0/items/19/notes/unclassified` | `whole--scope--slavers-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slavers-rel/equipment-access.yaml/@/equipment_lists/0/items/20/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slavers-rel/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slavers-rel/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/slayer-pirates-sar/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/slayer-pirates-sar/equipment-access.yaml/@/equipment_lists/2/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/slayer-pirates-sar/equipment-access.yaml/@/equipment_lists/2/items/11/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/profiles.yaml/@/profiles/0/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/profiles.yaml/@/profiles/1/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/profiles.yaml/@/profiles/2/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/profiles.yaml/@/profiles/3/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/profiles.yaml/@/profiles/4/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/slayer-pirates-sar/profiles.yaml/@/profiles/5/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/snotlings-web/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/snotlings-web/equipment-access.yaml/@/equipment_lists/0/items/8/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/snotlings-web/equipment-access.yaml/@/equipment_lists/1/items/6/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/snotlings-web/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/snotlings-web/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sons-of-hashut/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole--scope--equipment-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sons-of-hashut/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sorcerous-society-lotd4/equipment-access.yaml/@/equipment_lists/0/items/17/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sorcerous-society-lotd4/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sorcerous-society-lotd4/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sorcerous-society-lotd4/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sorcerous-society-lotd4/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/sorcerous-society-lotd4/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/strigoi-kaz/equipment-access.yaml/@/equipment_lists/0/items/8/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/strigoi-kaz/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/strigoi-kaz/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/strigoi-kaz/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/strigoi-kaz/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/strigoi-kaz/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/strigoi-kaz/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/strigoi-kaz/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/survivors-of-strigos-sylv/equipment-access.yaml/@/equipment_lists/0/items/17/notes/unclassified` | `whole--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/survivors-of-strigos-sylv/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `whole--scope--strigany-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/survivors-of-strigos-sylv/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/survivors-of-strigos-sylv/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `bones-primitive-weapon` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/survivors-of-strigos-sylv/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/survivors-of-strigos-sylv/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/tomb-guardians/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/tomb-guardians/equipment-access.yaml/@/equipment_lists/0/items/11/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/tomb-guardians/equipment-access.yaml/@/equipment_lists/1/items/6/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/tomb-guardians/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/turjuk-rel/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/undead/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `equipment-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/undead/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/undead/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/underworld-alliance-mim/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/underworld-alliance-mim/equipment-access.yaml/@/equipment_lists/0/items/8/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/underworld-alliance-mim/equipment-access.yaml/@/equipment_lists/1/items/5/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/underworld-alliance-mim/equipment-access.yaml/@/equipment_lists/1/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/underworld-alliance-mim/equipment-access.yaml/@/equipment_lists/2/items/3/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/underworld-alliance-mim/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/underworld-alliance-mim/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/underworld-alliance-mim/profiles.yaml/@/profiles/8/equipment_restrictions/0/unclassified` | `big-club` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/underworld-alliance-mim/profiles.yaml/@/profiles/8/equipment_restrictions/0/unclassified` | `no-weapons-required` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/vampire-hunters-of-sylvania-lotd5/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/vampire-hunters-of-sylvania-lotd5/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/vampire-hunters-of-sylvania-lotd5/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/vampire-hunters-of-sylvania-lotd5/equipment-access.yaml/@/equipment_lists/0/items/16/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/vampire-hunters-of-sylvania-lotd5/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/vampire-hunters-of-sylvania-lotd5/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/vampire-hunters-of-sylvania-lotd5/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `armour-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/vampire-hunters-of-sylvania-lotd5/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `permitted-weapons` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/vampire-hunters-of-sylvania-lotd5/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/vampire-hunters-of-sylvania-lotd5/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/vampire-hunters-of-sylvania-lotd5/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/vampire-hunters-of-sylvania-lotd5/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/wasteland-privateers-sar/equipment-access.yaml/@/equipment_lists/0/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/wasteland-privateers-sar/equipment-access.yaml/@/equipment_lists/0/items/11/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/wasteland-privateers-sar/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/wasteland-privateers-sar/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/wasteland-privateers-sar/equipment-access.yaml/@/equipment_lists/2/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/wasteland-privateers-sar/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/wasteland-privateers-sar/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/wasteland-privateers-sar/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/wasteland-privateers-sar/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/wasteland-privateers-sar/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/wasteland-privateers-sar/profiles.yaml/@/profiles/5/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/watchmen-mim/equipment-access.yaml/@/equipment_lists/0/items/16/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/watchmen-mim/equipment-access.yaml/@/equipment_lists/0/items/17/notes/unclassified` | `falconer-requirement` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/watchmen-mim/equipment-access.yaml/@/equipment_lists/0/items/17/notes/unclassified` | `sergeants-recipient--scope--falconer-requirement` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/watchmen-mim/equipment-access.yaml/@/equipment_lists/0/items/17/notes/unclassified` | `sergeants-recipient--scope--sergeants-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/watchmen-mim/equipment-access.yaml/@/equipment_lists/1/items/1/notes/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/bands/mordheim/witch-hunters/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/witch-hunters/profiles.yaml/@/profiles/3/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/witch-hunters/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/witch-hunters/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/wood-elves-of-arden-mou/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/wood-elves-of-athel-loren-web/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `heroes-only--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/wood-elves-of-athel-loren-web/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `heroes-only--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/wood-elves-of-athel-loren-web/equipment-access.yaml/@/equipment_lists/1/items/4/notes/unclassified` | `heroes-only--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/wood-elves-of-athel-loren-web/equipment-access.yaml/@/equipment_lists/1/items/9/notes/unclassified` | `heroes-only--scope--heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/mordheim/woodsmen-de-artois-mou/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-arcane-society/equipment-access.yaml/@/equipment_lists/0/items/19/notes/unclassified` | `spellcasters-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-arcane-society/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `spellcasters-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-deathbringers/equipment-access.yaml/@/equipment_lists/0/items/11/notes/unclassified` | `band-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-deathbringers/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `whole--scope--bearer-restriction` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/chaos-streets-deathbringers/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `band-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-deathbringers/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `hero-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-deathbringers/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `hero-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-deathbringers/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `yari-definition` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/chaos-streets-deathbringers/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `hero-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-deathbringers/equipment-access.yaml/@/equipment_lists/0/items/8/notes/unclassified` | `band-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-deathbringers/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` | `band-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-deathbringers/equipment-access.yaml/@/equipment_lists/1/items/5/notes/unclassified` | `band-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-greenskins/equipment-access.yaml/@/equipment_lists/1/items/3/notes/unclassified` | `species-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-greenskins/equipment-access.yaml/@/equipment_lists/1/items/4/notes/unclassified` | `species-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-greenskins/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-greenskins/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `natural-mouths` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-greenskins/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-mordheim-inhabitants/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `armour-with-sermons` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/chaos-streets-mordheim-inhabitants/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-mordheim-inhabitants/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `natural-jaws` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-sigmar-protectorate/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `items-not-modelled--scope--protectorate-recipients` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/chaos-streets-sigmar-protectorate/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `items-not-modelled--scope--protectorate-recipients` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/chaos-streets-sigmar-protectorate/equipment-access.yaml/@/equipment_lists/1/items/11/notes/unclassified` | `items-not-modelled--scope--protectorate-recipients` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/chaos-streets-sigmar-protectorate/equipment-access.yaml/@/equipment_lists/1/items/6/notes/unclassified` | `items-not-modelled--scope--protectorate-recipients` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/chaos-streets-sigmar-protectorate/equipment-access.yaml/@/equipment_lists/2/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-sigmar-protectorate/equipment-access.yaml/@/equipment_lists/2/items/6/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-sigmar-protectorate/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole--scope--armour-allowance` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/chaos-streets-sigmar-protectorate/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-sigmar-protectorate/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-sigmar-protectorate/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `natural-jaws` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-sons-of-nagarythe/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `band-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-sons-of-nagarythe/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `band-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-sons-of-nagarythe/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `hero-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-sons-of-nagarythe/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `band-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-sons-of-nagarythe/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `list-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/10/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/11/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/3/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/3/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `no-unarmed-penalty` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/6/equipment_restrictions/1/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/6/equipment_restrictions/1/unclassified` | `no-unarmed-penalty` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/8/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/8/equipment_restrictions/0/unclassified` | `no-unarmed-penalty` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/9/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/chaos-streets-undead-bloodlines/profiles.yaml/@/profiles/9/equipment_restrictions/0/unclassified` | `no-unarmed-penalty` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-cursed-of-karak-zorn/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `band-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-cursed-of-karak-zorn/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `bones-as-clubs` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-cursed-of-karak-zorn/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-cursed-of-karak-zorn/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-cursed-of-karak-zorn/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `no-unarmed-penalty` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-hobgoblin-raiders/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `list-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-hobgoblin-raiders/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-hobgoblin-raiders/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `no-unarmed-penalty` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `whole--scope--recipient-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/equipment-access.yaml/@/equipment_lists/2/items/7/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `equipment-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `equipment-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/1/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `equipment-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `equipment-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/4/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `equipment-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/5/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/6/equipment_restrictions/1/unclassified` | `equipment-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/6/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/7/equipment_restrictions/1/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/7/equipment_restrictions/1/unclassified` | `no-unarmed-penalty` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/8/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/8/equipment_restrictions/1/unclassified` | `equipment-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/8/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/9/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/9/equipment_restrictions/1/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-lahmian-brotherhood/profiles.yaml/@/profiles/9/equipment_restrictions/1/unclassified` | `no-unarmed-penalty` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-mages/equipment-access.yaml/@/equipment_lists/0/items/3/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-mages/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `creation-buyer--scope--creation-buyer` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/khemri-mages/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `prayer-users-prohibition` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/khemri-mages/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-mages/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-mages/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-mages/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-mages/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `no-unarmed-penalty` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-necromancers/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-thieves-guild/equipment-access.yaml/@/equipment_lists/0/items/16/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-thieves-guild/equipment-access.yaml/@/equipment_lists/0/items/19/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-thieves-guild/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-thieves-guild/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-thieves-guild/equipment-access.yaml/@/equipment_lists/0/items/8/notes/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-thieves-guild/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `equipment-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-thieves-guild/profiles.yaml/@/profiles/0/equipment_restrictions/1/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-thieves-guild/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `equipment-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-thieves-guild/profiles.yaml/@/profiles/1/equipment_restrictions/1/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-thieves-guild/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-thieves-guild/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `equipment-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-thieves-guild/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `equipment-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-thieves-guild/profiles.yaml/@/profiles/4/equipment_restrictions/1/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-thieves-guild/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-tomb-guardians/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `hero-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-tomb-guardians/equipment-access.yaml/@/equipment_lists/0/items/11/notes/unclassified` | `hero-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-tomb-guardians/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-tomb-guardians/equipment-access.yaml/@/equipment_lists/1/items/5/notes/unclassified` | `hero-recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-tomb-guardians/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `armour-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-tomb-guardians/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `list-contents` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-tomb-guardians/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-tomb-guardians/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/khemri-tomb-guardians/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `no-unarmed-penalty` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-amazons/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-amazons/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-amazons/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-amazons/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-amazons/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole--scope--armour-allowance` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-amazons/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-clan-pestilens/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-clan-pestilens/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-clan-pestilens/equipment-access.yaml/@/equipment_lists/0/items/16/notes/unclassified` | `cost-condition--scope--censer-requirement` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-clan-pestilens/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-clan-pestilens/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-clan-pestilens/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole--scope--scroll-bar` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-clan-pestilens/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole--scope--scroll-bar` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-clan-pestilens/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole--scope--scroll-bar` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-clan-pestilens/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-clan-pestilens/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `equipment-prohibition--scope--equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-clan-pestilens/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `equipment-prohibition--scope--natural-attacks` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-dark-elves/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `whole--scope--recipient-restriction` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-dark-elves/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `recipient--scope--recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-dark-elves/equipment-access.yaml/@/equipment_lists/0/items/16/notes/unclassified` | `recipient--scope--heroes-only` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-dark-elves/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `recipient--scope--beastmaster-only` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-dark-elves/equipment-access.yaml/@/equipment_lists/0/items/7/notes/unclassified` | `cost-condition--scope--base-weapon-rules` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/0/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/1/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/1/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/3/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/4/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/4/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/4/equipment_restrictions/3/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `recipient--scope--high-elves-only` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-high-elves/equipment-access.yaml/@/equipment_lists/0/items/16/notes/unclassified` | `recipient--scope--loremaster-only` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-high-elves/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `recipient--scope--loremaster-only` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/0/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/0/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/1/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/1/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/1/equipment_restrictions/3/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/1/equipment_restrictions/4/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/2/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/2/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/2/equipment_restrictions/3/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/3/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/3/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/3/equipment_restrictions/3/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/4/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/4/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-lizardmen/equipment-access.yaml/@/equipment_lists/0/items/11/notes/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-lizardmen/equipment-access.yaml/@/equipment_lists/0/items/3/notes/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-lizardmen/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-lizardmen/profiles.yaml/@/profiles/1/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-lizardmen/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `no-helmet-for-skinks` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-lizardmen/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-lizardmen/profiles.yaml/@/profiles/3/equipment_restrictions/1/unclassified` | `no-helmet-for-skinks` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-lizardmen/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-lizardmen/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-norse/equipment-access.yaml/@/equipment_lists/0/items/3/notes/unclassified` | `recipient--scope--heroes-only` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-norse/equipment-access.yaml/@/equipment_lists/0/items/3/notes/unclassified` | `recipient--scope--pirate-and-norse-heroes` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-norse/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-norse/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-pirates/equipment-access.yaml/@/equipment_lists/0/items/18/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-pirates/equipment-access.yaml/@/equipment_lists/0/items/19/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-pirates/equipment-access.yaml/@/equipment_lists/0/items/20/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-pirates/equipment-access.yaml/@/equipment_lists/0/items/21/notes/unclassified` | `recipient--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-pirates/equipment-access.yaml/@/equipment_lists/0/items/3/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-pirates/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `recipient--scope--heroes-only` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-pirates/equipment-access.yaml/@/equipment_lists/0/items/8/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-pirates/equipment-access.yaml/@/equipment_lists/1/items/3/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-pirates/equipment-access.yaml/@/equipment_lists/1/items/7/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-pirates/equipment-access.yaml/@/equipment_lists/2/items/11/notes/unclassified` | `recipient--scope--recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-pirates/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-pirates/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-pirates/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-pirates/profiles.yaml/@/profiles/3/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-pirates/profiles.yaml/@/profiles/3/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-pirates/profiles.yaml/@/profiles/5/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-pirates/profiles.yaml/@/profiles/5/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-pygmies/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `equipment-access--scope--recipient-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-pygmies/equipment-access.yaml/@/equipment_lists/0/items/8/notes/unclassified` | `whole--scope--recipient-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-savage-goblins/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-savage-goblins/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `recipient--scope--inheritance-and-wear` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-savage-goblins/equipment-access.yaml/@/equipment_lists/0/items/14/notes/unclassified` | `recipient--scope--leader-only` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-savage-goblins/equipment-access.yaml/@/equipment_lists/0/items/2/notes/unclassified` | `recipient--scope--recipient` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-savage-goblins/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-savage-goblins/profiles.yaml/@/profiles/1/equipment_restrictions/1/unclassified` | `equipment-access--scope--recipient-restriction` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/lustria-savage-goblins/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-savage-goblins/profiles.yaml/@/profiles/2/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-savage-goblins/profiles.yaml/@/profiles/2/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-savage-goblins/profiles.yaml/@/profiles/3/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-savage-goblins/profiles.yaml/@/profiles/3/equipment_restrictions/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-savage-goblins/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `equipment-prohibition--scope--equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/lustria-savage-goblins/profiles.yaml/@/profiles/8/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/trollheim-cult-of-the-possessed/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/trollheim-skaven-clan-eshin/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` | `recipient--scope--skaven-only` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/trollheim-skaven-clan-eshin/equipment-access.yaml/@/equipment_lists/0/items/5/notes/unclassified` | `whole--scope--recipient-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/trollheim-skaven-clan-eshin/equipment-access.yaml/@/equipment_lists/0/items/6/notes/unclassified` | `recipient--scope--skaven-only` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/trollheim-skaven-clan-eshin/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` | `whole--scope--recipient-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/trollheim-skaven-clan-eshin/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/trollheim-skaven-clan-eshin/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/trollheim-undead/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/trollheim-undead/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `no-unarmed-penalty` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/trollheim-undead/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `equipment-prohibition--scope--equipment-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/trollheim-undead/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `equipment-prohibition--scope--improvised-bones` | — | enlace compartido; consumer vacío |
| `source/bands/trollheim/trollheim-undead/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/trollheim-witch-hunters/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `list-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/trollheim-witch-hunters/profiles.yaml/@/profiles/3/equipment_restrictions/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/trollheim-witch-hunters/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `list-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/bands/trollheim/trollheim-witch-hunters/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/exploration-and-income.yaml/campaign.magical-artefact.attlas-plate-mail/unclassified` | `rune-of-fortitude` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/exploration-and-income.yaml/campaign.magical-artefact.attlas-plate-mail/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/exploration-and-income.yaml/campaign.magical-artefact.executioners-hood/unclassified` | `strength-bonus` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/magic.yaml/@/lores/21/note/unclassified` | `priest-armour-clarification--scope--priest-heavy-armour-stricture` | — | enlace compartido; consumer vacío |
| `source/catalog/campaign/mutations.yaml/campaign.mutation.extra-arm/unclassified` | `extra-arm` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/mutations.yaml/campaign.mutation.grant.aquatic-mutants/unclassified` | `mutation-grant--scope--mutation-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/mutations.yaml/campaign.mutation.grant.aquatic-mutants/unclassified` | `mutation-grant--scope--mutation-pool` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/mutations.yaml/campaign.mutation.great-claw/unclassified` | `arm-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/serious-injuries.yaml/@/tables/0/results/3/note/unclassified` | `injury-consequence--scope--injury-consequence` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/130/restrictions/0/note/unclassified` | `recipient--scope--recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/132/restrictions/0/note/unclassified` | `wolf-cloak-identity-note--scope--bearman-starting-equipment-only` | — | enlace compartido; consumer vacío |
| `source/catalog/campaign/trading-post.yaml/@/items/133/restrictions/0/note/unclassified` | `recipient--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/137/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/138/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/144/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/15/restrictions/2/note/unclassified` | `recipient--scope--gnoblar-heroes-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/162/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/186/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/21/restrictions/1/note/unclassified` | `recipient--scope--gnoblars-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/213/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/237/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/249/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/258/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/264/restrictions/0/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/272/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/277/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/32/restrictions/1/note/unclassified` | `recipient--scope--slayers-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/320/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/327/restrictions/0/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/35/restrictions/0/note/unclassified` | `recipient--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/367/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/37/restrictions/0/note/unclassified` | `recipient--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/374/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/377/restrictions/1/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/434/restrictions/0/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/441/restrictions/0/note/unclassified` | `cost--scope--item-identity` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/460/restrictions/0/note/unclassified` | `recipient` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/campaign/trading-post.yaml/@/items/49/restrictions/0/note/unclassified` | `recipient--scope--bearer-restriction` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/core.yaml/@/profiles/0/equipment/unique_equipment/0/rules/1/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/core.yaml/@/profiles/0/equipment/unique_equipment/0/rules/2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/core.yaml/@/profiles/1/unresolved_references/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/core.yaml/hireling.dramatis.johann-the-knife.rule.crimson-shade/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/core.yaml/hireling.dramatis.johann-the-knife.rule.poisoned-weapons/unclassified` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-1a.yaml/@/profiles/0/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-1a.yaml/@/profiles/2/unresolved_references/1/unclassified` | `whole` | — | enlace compartido; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1a.yaml/hireling.dramatis.nicodemus-the-cursed-pilgrim.rule.wizard-s-staff/unclassified` | `staff-modes--scope--staff-modes` | — | enlace compartido; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/@/profiles/3/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/@/profiles/5/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/@/profiles/8/unresolved_references/0/unclassified` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/@/profiles/8/unresolved_references/3/unclassified` | `weapon-master-skill` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.dijin-katal-the-renegade-assassin.rule.perfect-killer/unclassified` | `perfect-killer` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.penthesilea-mark-of-the-serpent.rule.mark-of-the-serpent/unclassified` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/@/profiles/1/unresolved_references/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/@/profiles/1/unresolved_references/1/unclassified` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/@/profiles/3/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/@/profiles/3/unresolved_references/0/unclassified` | `profile--scope--horseman-profile` | — | enlace compartido; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.aksho-akhash-the-vile-dreadwing-lord-of-the-carrion-throne.rule.daemonic-flesh/unclassified` | `daemonic-five-plus-save` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.aksho-akhash-the-vile-dreadwing-lord-of-the-carrion-throne.rule.daemonic-flesh/unclassified` | `magical-attacks` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-2b.yaml/@/profiles/0/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-2b.yaml/@/profiles/2/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-2b.yaml/hireling.dramatis.aldred-fellblade.rule.fellblade/compiler.aldred-fellblade` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/grade-2b.yaml/hireling.dramatis.snorri-nosebiter.rule.slayer-rules/profile.equipment-restrictions` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/dramatis-personae/rules.yaml/hireling.dramatis.rule.fixed-equipment/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/core.yaml/@/profiles/0/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/core.yaml/hireling.hired-sword.elf-ranger.skill.luck/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1a.yaml/@/profiles/4/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1a.yaml/hireling.hired-sword.beast-hunter.rule.skull-rack/unclassified` | `causes-fear-vs-beastmen` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1a.yaml/hireling.hired-sword.imperial-assassin.rule.poisoner/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1a.yaml/hireling.hired-sword.imperial-assassin.rule.weapons-master/unclassified` | `blackpowder-prohibition` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/@/profiles/11/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/@/profiles/17/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/@/profiles/2/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/@/profiles/28/unresolved_references/1/unclassified` | `garlic-mapping` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/@/profiles/29/unresolved_references/1/unclassified` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/@/profiles/3/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/@/profiles/6/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.clan-skryre-rat-ogre.rule.bio-machinery/unclassified` | `psychology-immunity` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.dark-elf-assassin.rule.perfect-killer/unclassified` | `perfect-killer` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.mule-skinner.rule.animal-handler/unclassified` | `animal-handler-skill` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/@/profiles/2/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/@/profiles/4/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/@/profiles/6/unresolved_references/0/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.bone-goliath.rule.undead-construct/unclassified` | `undead-construct-ignores-injuries-on-four` | — | enlace compartido; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.chaos-centaur.rule.drunken/unclassified` | `drunken-turn-roll` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/@/profiles/19/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/@/profiles/2/unresolved_references/0/unclassified` | `profile` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/@/profiles/4/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/@/profiles/5/unresolved_references/0/unclassified` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/@/profiles/7/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/@/profiles/8/unresolved_references/0/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/10/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/10/equipment/fixed_items/3/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/11/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/11/equipment/fixed_items/1/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/12/equipment/choices/0/options/0/items/0/notes/unclassified` | `priest-of-manann-only-price-and-rarity--scope--priest-of-manann-only` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/12/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/13/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/13/equipment/fixed_items/1/notes/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/14/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/15/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/15/equipment/fixed_items/1/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/15/equipment/fixed_items/2/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/16/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/16/equipment/fixed_items/1/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/17/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/18/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/19/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/2/equipment/fixed_items/2/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/2/equipment/fixed_items/3/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/20/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/20/equipment/fixed_items/1/notes/unclassified` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/21/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/22/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/22/equipment/fixed_items/1/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/3/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/3/equipment/fixed_items/1/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/3/equipment/fixed_items/2/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/4/equipment/fixed_items/0/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/6/equipment/fixed_items/1/notes/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.druid-priest-of-taal.rule.strictures/profile.equipment-restrictions` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.halfling-pimp.rule.flesh-peddler/mechanic.flesh-peddler` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-morr-miracle-workers.rule.morrs-servant/mechanic.morrs-servant` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-morr-miracle-workers.rule.strictures/profile.equipment-restrictions` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan.pending-duel` | `witch-finder--scope--skill-access` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-verena.rule.strictures/profile.active-weapon-restrictions` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priestess-of-shallya.rule.strictures/mechanic.shallya-strictures` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priestess-of-shallya.rule.strictures/profile.active-weapon-restrictions` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priestess-of-shallya.rule.strictures/profile.equipment-restrictions` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priestess-of-shallya.skill.tranquil-aura/mechanic.shallya-tranquil-aura` | `rule--scope--weapon-skill-penalty` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.sister-of-sigmar.rule.blessing-of-sigmar/hireling.hired-sword.sister-of-sigmar.rule.blessing-of-sigmar.choice` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.trickster-priest-of-ranald.rule.strictures/profile.equipment-restrictions` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.war-priestess-of-myrmidia.skill.eagle-friend/mechanic.myrmidia-eagle-friend` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers.skill.enlightened/mechanic.sigmar-enlightened` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers.skill.symbol-of-unity/mechanic.sigmar-symbol-of-unity` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.whaler.rule.marine-hunter/mechanic.marine-hunter` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.rule.strictures/defence.wolf-pelt-cloak` | `may-not-carry-blackpowder-weapons` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.rule.strictures/defence.wolf-pelt-cloak` | `may-not-wear-armour` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.rule.strictures/profile.equipment-restrictions` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.skill.son-of-ulric/profile.fist` | `rule` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/hired-swords/rules.yaml/hireling.hired-sword.rule.fixed-equipment/unclassified` | `item` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/0/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/1/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/1/traits/1/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/1/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/10/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/10/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/11/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/11/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/12/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/12/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/13/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/13/traits/1/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/13/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/14/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/15/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/16/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/17/traits/2/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/18/traits/2/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/19/traits/1/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/19/traits/2/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/2/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/2/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/20/traits/1/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/21/traits/1/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/22/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/22/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/23/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/23/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/24/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/24/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/25/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/25/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/26/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/26/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/27/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/27/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/28/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/28/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/29/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/29/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/3/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/3/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/30/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/30/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/31/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/31/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/32/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/32/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/4/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/4/traits/1/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/4/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/5/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/5/traits/1/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/6/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/6/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/7/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/7/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/8/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/8/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/9/traits/0/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/hirelings/traits.yaml/@/traits/9/unclassified` | `trait` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/rules/special-rules.yaml/shared-rule.hard-head-2/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/rules/special-rules.yaml/shared-rule.living/unclassified` | `living` | — | enlace compartido; consumer vacío |
| `source/catalog/rules/special-rules.yaml/shared-rule.middenheim-physical-prowess/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/rules/special-rules.yaml/shared-rule.skills/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |
| `source/catalog/rules/special-rules.yaml/shared-rule.strictures/unclassified` | `whole` | — | referencias de compilación, construcción o enlace compartido |

## Claves de apoyo de otros responsables

| id | clause_id | Responsable principal | Referencia de asignación |
| --- | --- | --- | --- |
| `rule/mordheim/pit-fighters/dwarf-troll-slayer--pit-fighter/trait.pit-fighter` | `whole` | G03 | encargo explícito; consumer vacío |
| `rule/mordheim/pit-fighters/ogre-pit-fighter--pit-fighter/trait.pit-fighter` | `whole` | G03 | encargo explícito; consumer vacío |
| `rule/mordheim/pit-fighters/pit-fighters--pit-fighter/trait.pit-fighter` | `whole` | G03 | encargo explícito; consumer vacío |
| `rule/mordheim/pit-fighters/pit-king--pit-fighter/trait.pit-fighter` | `whole` | G03 | encargo explícito; consumer vacío |
| `rule/mordheim/pit-fighters/pit-veterans--pit-fighter/trait.pit-fighter` | `whole` | G03 | encargo explícito; consumer vacío |
| `rule/mordheim/pit-fighters/pursuers--pit-fighter/trait.pit-fighter` | `whole` | G03 | encargo explícito; consumer vacío |

## Base de esta asignación

Preparación: 2026-10-21. HEAD: `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` más cambios locales actuales. CSV SHA-256: `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`. No es un certificado de ejecución.
