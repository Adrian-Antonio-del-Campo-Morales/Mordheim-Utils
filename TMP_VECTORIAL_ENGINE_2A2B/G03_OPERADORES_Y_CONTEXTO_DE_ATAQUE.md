# G03 — Operadores y contexto de ataque, defensas y prioridad

## Prompt para lanzar el agente

Copia el bloque completo al lanzar el agente. Las condiciones de inicio forman parte del encargo; este prompt no autoriza saltarse sus dependencias.

```text
Realiza el encargo G03 (fase 1: implementación) del motor vectorial NumPy.

INFORMACIÓN QUE DEBES LEER
1. El fichero de trabajo completo:
   D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK\TMP_VECTORIAL_ENGINE_2A2B\G03_OPERADORES_Y_CONTEXTO_DE_ATAQUE.md
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
Etapa C, tras G00 y G02. Ejecutable en paralelo con G04 y G05 en copias aisladas de la misma base.
Comprueba la entrega de esas dependencias. Si falta alguna, comunica la dependencia concreta;
puedes avanzar con lectura o trabajo independiente, pero no inventes interfaces ni declares
completada una conexión que todavía no existe.

OBJETIVO CONCRETO
Implementar los cálculos y condiciones que faltan en los operadores NumPy partiendo de modular/contexts.py y phases.py: impacto, fuerza, herida, armadura, salvaciones, paradas, lesiones, cantidades de ataques y prioridad. Incluye las condiciones reales del oponente, turno, recurso y contexto; no basta con reconocer etiquetas. Reutiliza _operators.py. Entrega al coordinador los cambios concretos de llamada que necesiten G04/G06, sin editar sus archivos.

REFERENCIAS Y COMPROBACIONES QUE DEBES REUTILIZAR
Lee las funciones prepare_* y los helpers _attack_strength, _hit_reroll, _parry_context y _injury_context enumerados en el encargo. Reutiliza los checks exactos existentes y test_rule_families_b.py. No crees una matriz nueva de pruebas por cláusula.

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
TMP_VECTORIAL_ENGINE_2A2B/G03-deliverable.md
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

**Inicio:** Etapa C, tras G00 y G02. Ejecutable en paralelo con G04 y G05 en copias aisladas de la misma base.

**Cláusulas principales:** 941. **Cláusulas de apoyo:** 309.

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

Crea o actualiza `TMP_VECTORIAL_ENGINE_2A2B/G03-deliverable.md` en la raíz de tu copia de trabajo. Es la entrega persistente obligatoria de este grupo y está permitida además de los archivos de producción autorizados. No basta con un mensaje en el chat.

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

- `TMP_VECTORIAL_ENGINE_2A2B/G03-deliverable.md` — documento de entrega obligatorio, propietario exclusivo G03.
- `packages/python/combat-engine/mordheim_combat/vectorized/_operators.py`
- `tests/python/combat/vectorized/test_rule_families_b.py`

Cualquier archivo no enumerado queda fuera de tu propiedad. Los módulos nuevos expresamente permitidos solo se crean si el portado los necesita. Los tests compartidos que no son tuyos se pueden ejecutar, pero no editar.

## Implementación de referencia que debes seguir

- `packages/python/combat-engine/mordheim_combat/modular/contexts.py::prepare_hit_context`
- `packages/python/combat-engine/mordheim_combat/modular/contexts.py::prepare_wound_context`
- `packages/python/combat-engine/mordheim_combat/modular/contexts.py::prepare_armour_context`
- `packages/python/combat-engine/mordheim_combat/modular/contexts.py::prepare_special_save_context`
- `packages/python/combat-engine/mordheim_combat/modular/contexts.py::_parry_context`
- `packages/python/combat-engine/mordheim_combat/modular/contexts.py::_injury_context`
- `packages/python/combat-engine/mordheim_combat/modular/contexts.py::_attack_strength`
- `packages/python/combat-engine/mordheim_combat/modular/contexts.py::_hit_reroll`
- `packages/python/combat-engine/mordheim_combat/phases.py`
- `packages/python/combat-engine/mordheim_combat/vectorized/_operators.py`

Estas referencias son puntos de entrada; sigue sus llamadas para reproducir el comportamiento completo, sin releer las fuentes de reglas.

## Trabajo concreto

1. Portar los cálculos y cualificadores del modular a los operadores existentes: impacto, fuerza, herida, armadura, salvaciones, paradas, lesión, ataques y prioridad.
2. Trasladar las condiciones y modificadores que hoy preparan los contextos modulares. No basta con leer un campo del efecto si la condición de aplicabilidad depende del oponente, turno, recurso o contexto local.
3. Mantener los límites, ausencia de características, excepciones de arma y orden de las salvaciones definidos por el modular. Los arrays deben reflejar estados distintos por fila.
4. Para cantidad y prioridad, reproducir la contribución numérica de pools y rondas. La asignación y consumo de ataques es G04; el orden de eventos y la recuperación que lo afecta es G06.
5. Para paradas, resultados de lesión y defensas especiales, implementar el cálculo en operadores; G04 mantiene consumo de recursos, secuencias y resolución de daño. No editar `_attacks.py` ni `_types.py`.
6. Reutilizar las funciones actuales y sus firmas. Entregar cambios de llamada concretos para G04/G06 si requiere parámetros nuevos; el coordinador integra esos llamadores tras reunir la tanda.

## Comprobación mínima

Reutilizar los checks exactos de operadores y los casos existentes de familias B. Ejecutar solo los afectados. Cero casos nuevos si bastan; normalmente un caso representativo por funcionalidad no cubierta, nunca uno por cláusula. No ampliar matrices ni tocar tests modulares.

## Criterio de entrega

Los operadores representan el comportamiento de sus consumidores modulares y las comprobaciones enfocadas pasan. Las claves cruzadas solo podrán cerrarse cuando G04/G05/G06 hayan integrado su consumo.

## Claves principales asignadas

| id | clause_id | Apoyos | Referencia de asignación |
| --- | --- | --- | --- |
| `core/combat-injury-states` | `stand-up-strikes-last` | — | consumer |
| `core/combat-parry` | `parry-attempt` | G02 | consumer |
| `core/combat-parry` | `reroll-and-capacity` | G02 | consumer |
| `core/combat-two-weapons` | `extra-attack` | — | consumer |
| `item/ankus` | `whole` | — | consumer |
| `item/arcane_candelabrum` | `whole` | — | consumer |
| `item/axe` | `whole` | — | consumer |
| `item/bagh_nakh` | `whole` | — | consumer |
| `item/ball_chain` | `whole` | — | consumer |
| `item/battle_axe` | `whole` | — | consumer |
| `item/boar_spear_aristocrat_only` | `whole--scope--charging-enemy-loses-one-attack` | — | consumer |
| `item/boar_spear_aristocrat_only` | `whole--scope--strikes-first` | — | consumer |
| `item/boat_hook` | `whole` | — | consumer |
| `item/broadsword` | `whole` | — | consumer |
| `item/buckler` | `does-not-improve-armour` | — | consumer |
| `item/buckler` | `parry-one-hit-per-round` | G02 | consumer |
| `item/cathayan_longsword` | `armour-penetration-discrepancy` | — | consumer |
| `item/cathayan_longsword` | `whole` | — | consumer |
| `item/cathayan_quilted_silk_armour` | `plus-one-to-armour-saves` | — | consumer |
| `item/censer` | `whole` | — | consumer |
| `item/ceremonial_scythe` | `whole` | — | consumer |
| `item/chain_sticks` | `whole` | — | consumer |
| `item/choppa` | `whole` | — | consumer |
| `item/choppa_counts_as_a_morning_star` | `whole` | — | consumer |
| `item/claw_of_the_old_ones` | `whole` | — | consumer |
| `item/cleaver` | `whole` | — | consumer |
| `item/cleaver_counts_as_axe` | `whole` | — | consumer |
| `item/club` | `whole` | — | consumer |
| `item/dagger` | `whole` | — | consumer |
| `item/dagger_jambiya` | `whole` | — | consumer |
| `item/dark_steel_weapon` | `whole` | — | consumer |
| `item/dark_venom` | `whole` | — | consumer |
| `item/death_knife` | `whole` | — | consumer |
| `item/devil_toxin` | `whole` | — | consumer |
| `item/dragon_sword` | `whole--scope--two-handed-loadout` | — | consumer |
| `item/duelling_pistol` | `whole--scope--close-combat-hit-bonus` | — | consumer |
| `item/dwarf_axe` | `whole` | — | consumer |
| `item/elven_greatsword` | `whole` | — | consumer |
| `item/enchanted_skins` | `six-plus-special-save` | — | consumer |
| `item/fighting_claws` | `whole` | — | consumer |
| `item/flail` | `whole` | — | consumer |
| `item/great_axe` | `whole--scope--two-handed-loadout` | — | consumer |
| `item/great_scimitar` | `whole` | — | consumer |
| `item/great_weapon` | `whole` | — | consumer |
| `item/gromril_armour` | `four-plus-basic-save` | — | consumer |
| `item/gromril_weapon` | `whole--scope--extra-armour-modifier` | — | consumer |
| `item/halberd` | `whole--scope--two-handed-loadout` | — | consumer |
| `item/hammer` | `whole` | — | consumer |
| `item/hammer_or_mace` | `whole` | — | consumer |
| `item/heavy_armour` | `five-plus-basic-save` | — | consumer |
| `item/hellblade` | `whole--scope--combat-profile` | — | consumer |
| `item/hellblade` | `whole--scope--deadly` | — | consumer |
| `item/hellblade` | `whole--scope--soulseeking` | — | consumer |
| `item/hellblade` | `whole--scope--two-handed-loadout` | — | consumer |
| `item/hobgoblin_poisoned_daggers` | `whole` | — | consumer |
| `item/iron_fist` | `whole` | — | consumer |
| `item/ithilmar_armour` | `five-plus-basic-save` | — | consumer |
| `item/ithilmar_weapon` | `whole` | — | consumer |
| `item/kanabo` | `whole--scope--combat-profile` | — | consumer |
| `item/kanabo` | `whole--scope--concussion` | — | consumer |
| `item/katana` | `whole--scope--combat-profile` | — | consumer |
| `item/katana` | `whole--scope--parry` | — | consumer |
| `item/katana` | `whole--scope--two-handed-loadout` | — | consumer |
| `item/katar` | `whole` | — | consumer |
| `item/kitchen_knife` | `whole` | — | consumer |
| `item/kite_shield` | `plus-two-on-foot-plus-one-mounted` | — | consumer |
| `item/knuckledusters` | `whole--scope--pair` | — | consumer |
| `item/ladle` | `whole` | — | consumer |
| `item/light_armour` | `six-plus-basic-save` | — | consumer |
| `item/long_boathook` | `whole` | — | consumer |
| `item/long_daggers` | `whole--scope--pair-and-parry` | — | consumer |
| `item/lucky_charm` | `first-hit-discarded-on-four` | — | consumer |
| `item/lucky_charm` | `two-charms-do-not-stack` | — | consumer |
| `item/mace` | `whole` | — | consumer |
| `item/mace_hammer` | `whole` | — | consumer |
| `item/mage_robes` | `behaves-as-a-wizards-robe` | — | consumer |
| `item/main_gauche` | `whole` | — | consumer |
| `item/manbane` | `whole` | — | consumer |
| `item/misericordia` | `coup-de-grace` | — | consumer |
| `item/misericordia` | `whole` | — | consumer |
| `item/morning_star` | `whole` | — | consumer |
| `item/obsidian_weapon` | `whole--scope--combat-profile` | — | consumer |
| `item/ogre_club` | `whole` | — | consumer |
| `item/pike` | `first-turn-scope` | — | consumer |
| `item/pike` | `whole` | — | consumer |
| `item/poison_daggers` | `whole` | — | consumer |
| `item/pry_bar` | `whole` | — | consumer |
| `item/quarter_staff` | `whole` | — | consumer |
| `item/scythe` | `whole` | — | consumer |
| `item/sea_dragon_cloak` | `armour-choice-five-plus-in-close-combat` | — | consumer |
| `item/shield` | `plus-one-combined-save` | — | consumer |
| `item/shock_rod` | `whole--scope--combat-profile` | — | consumer |
| `item/shortsword` | `whole` | — | consumer |
| `item/sigmarite_hammer` | `whole` | — | consumer |
| `item/skull_busta` | `whole--scope--basha` | — | consumer |
| `item/skull_busta` | `whole--scope--combat-profile` | — | consumer |
| `item/skull_busta` | `whole--scope--feelin-wobbly` | — | consumer |
| `item/spear` | `whole` | — | consumer |
| `item/spear_stave` | `whole--scope--counts-as-halberd` | — | consumer |
| `item/spiked_gauntlet` | `whole` | — | consumer |
| `item/squig_prodder` | `whole` | — | consumer |
| `item/staff` | `whole` | — | consumer |
| `item/staff_club_mace` | `whole` | — | consumer |
| `item/starblade` | `whole` | — | consumer |
| `item/starsword` | `whole` | — | consumer |
| `item/stone_axe` | `whole` | — | consumer |
| `item/stone_axe_counts_as_a_club` | `whole` | — | consumer |
| `item/sunstaff_lustria` | `whole` | — | consumer |
| `item/sword` | `whole` | — | consumer |
| `item/sword_gnoblar` | `whole` | — | consumer |
| `item/sword_heroes_only` | `whole` | — | consumer |
| `item/sword_scimitar` | `whole` | — | consumer |
| `item/tenderiser` | `whole` | — | consumer |
| `item/toughened_leathers` | `six-plus-and-compatibility` | — | consumer |
| `item/two_handed_club` | `whole` | — | consumer |
| `item/two_handed_weapon` | `whole` | — | consumer |
| `item/weeping_blades` | `whole` | — | consumer |
| `item/witch_sword` | `whole` | — | consumer |
| `item/wizard_robe` | `behaves-as-a-wizards-robe` | — | consumer |
| `item/wizards_staff` | `whole--scope--combat-profile` | — | consumer |
| `item/wizards_staff` | `whole--scope--concussion` | — | consumer |
| `item/wolfsbane` | `whole` | — | consumer |
| `item/wrench` | `whole--scope--counts-as-club` | — | consumer |
| `mechanic/armour.cathayan-quilted-silk` | `plus-one-to-armour-saves` | — | consumer |
| `mechanic/armour.gromril-armour` | `four-plus-basic-save` | — | consumer |
| `mechanic/armour.heavy-armour` | `five-plus-basic-save` | — | consumer |
| `mechanic/armour.ithilmar-armour` | `five-plus-basic-save` | — | consumer |
| `mechanic/armour.light-armour` | `six-plus-basic-save` | — | consumer |
| `mechanic/armour.ninja-robes` | `six-plus-no-shield` | — | consumer |
| `mechanic/armour.no-armour` | `no-body-armour` | — | consumer |
| `mechanic/armour.plate-armour` | `four-plus-and-shield` | — | consumer |
| `mechanic/armour.toughened-leathers` | `six-plus-and-compatibility` | — | consumer |
| `mechanic/armour.wizard-s-robe` | `six-plus-and-no-spellcasting-penalty--scope--six-plus-and-no-combining` | — | consumer |
| `mechanic/defence.buckler` | `does-not-improve-armour` | — | consumer |
| `mechanic/defence.buckler` | `parry-one-hit-per-round` | G02 | consumer |
| `mechanic/defence.enchanted-skins` | `six-plus-special-save` | — | consumer |
| `mechanic/defence.kite-shield` | `plus-two-on-foot-plus-one-mounted` | — | consumer |
| `mechanic/defence.lucky-charm` | `first-hit-discarded-on-four` | — | consumer |
| `mechanic/defence.lucky-charm` | `two-charms-do-not-stack` | — | consumer |
| `mechanic/defence.sea-dragon-cloak` | `armour-choice-five-plus-in-close-combat` | — | consumer |
| `mechanic/defence.shield` | `plus-one-combined-save` | — | consumer |
| `mechanic/material.dark-steel` | `whole` | — | consumer |
| `mechanic/material.gromril` | `whole` | — | consumer |
| `mechanic/material.ithilmar` | `whole` | — | consumer |
| `mechanic/material.normal` | `whole` | — | consumer |
| `mechanic/material.obsidian` | `whole` | — | consumer |
| `mechanic/mechanic.amazon-isolationists` | `whole` | — | consumer |
| `mechanic/mechanic.andanti-knowledge` | `whole` | — | consumer |
| `mechanic/mechanic.armour-save-bonus` | `plus-one-to-armour-saves` | — | consumer |
| `mechanic/mechanic.bat-injury-chart` | `bat-injury-chart` | — | consumer |
| `mechanic/mechanic.bestial` | `bestial` | — | consumer |
| `mechanic/mechanic.black-hunger` | `attack-bonus` | — | consumer |
| `mechanic/mechanic.black-hunger` | `invocation` | — | consumer |
| `mechanic/mechanic.blessing-of-morr` | `whole` | — | consumer |
| `mechanic/mechanic.death-blow` | `single-attack-with-bonuses` | — | consumer |
| `mechanic/mechanic.dueling-pride` | `whole` | — | consumer |
| `mechanic/mechanic.energy-focus` | `whole` | — | consumer |
| `mechanic/mechanic.fen-hard-to-kill` | `fire-cancels-the-rule` | — | consumer |
| `mechanic/mechanic.fen-hard-to-kill` | `out-of-action-only-on-six` | — | consumer |
| `mechanic/mechanic.foul-odour` | `foul-odour` | — | consumer |
| `mechanic/mechanic.frantic` | `frantic` | — | consumer |
| `mechanic/mechanic.frustratingly-tiny` | `minus-one-to-hit-in-melee` | — | consumer |
| `mechanic/mechanic.ghost-pirate-ethereal` | `four-plus-unmodifiable-save` | — | consumer |
| `mechanic/mechanic.ghost-pirate-ethereal` | `magical-attacks-bypass` | — | consumer |
| `mechanic/mechanic.gypsy-ward` | `five-plus-ward-against-magic` | — | consumer |
| `mechanic/mechanic.hatred-chaotic-warband` | `hatred` | — | consumer |
| `mechanic/mechanic.hatred-dark-elves` | `hatred` | — | consumer |
| `mechanic/mechanic.hatred-dwarfs` | `hatred` | — | consumer |
| `mechanic/mechanic.hatred-dwarfs-skaven` | `hatred` | — | consumer |
| `mechanic/mechanic.hatred-high-elves` | `hatred` | — | consumer |
| `mechanic/mechanic.hatred-human-warband` | `hatred` | — | consumer |
| `mechanic/mechanic.hatred-orcs-goblins` | `hatred` | — | consumer |
| `mechanic/mechanic.hatred-skaven` | `hatred` | — | consumer |
| `mechanic/mechanic.hatred-skaven-orcs-goblins` | `hatred` | — | consumer |
| `mechanic/mechanic.hatred-undead` | `hatred` | — | consumer |
| `mechanic/mechanic.iron-cage` | `five-plus-armour-save` | — | consumer |
| `mechanic/mechanic.kindred-hatred` | `hatred` | — | consumer |
| `mechanic/mechanic.magical-void` | `whole` | — | consumer |
| `mechanic/mechanic.mark-of-the-old-ones` | `whole` | — | consumer |
| `mechanic/mechanic.noble-disdain` | `hatred` | — | consumer |
| `mechanic/mechanic.norse-bulwark` | `plus-one-armour-in-close-combat-with-axe-and-shield` | — | consumer |
| `mechanic/mechanic.norse-shieldmaster` | `shield-parries-in-addition-to-its-save` | G02 | consumer |
| `mechanic/mechanic.pikewall` | `reroll-failed-hits-when-charged` | — | consumer |
| `mechanic/mechanic.retain-flail-morning-star-strength-bonus` | `whole` | — | consumer |
| `mechanic/mechanic.sabretusk-charge` | `whole` | — | consumer |
| `mechanic/mechanic.sea-troll-slime` | `minus-one-to-hit-in-melee` | — | consumer |
| `mechanic/mechanic.shallya-tranquil-aura` | `whole--scope--weapon-skill-penalty` | — | consumer |
| `mechanic/mechanic.sigmar-symbol-of-unity` | `whole` | — | consumer |
| `mechanic/mechanic.snorri-lucky` | `five-plus-ward-save` | — | consumer |
| `mechanic/mechanic.strike-first-vs-skinks-always` | `whole` | — | consumer |
| `mechanic/mechanic.strike-first-vs-skinks-first-round` | `whole` | — | consumer |
| `mechanic/mechanic.thirst-for-vengeance` | `charge-attack-bonus` | — | consumer |
| `mechanic/mechanic.thirst-for-vengeance` | `hatred-undead` | — | consumer |
| `mechanic/mechanic.ulric-intense-rivals` | `hatred` | — | consumer |
| `mechanic/mechanic.unholy-stink` | `unholy-stink` | — | consumer |
| `mechanic/mechanic.untiring` | `non-magical-immunity` | — | consumer |
| `mechanic/mechanic.untiring` | `save-floor` | — | consumer |
| `mechanic/mechanic.wolf-rat-bite` | `whole` | — | consumer |
| `mechanic/poison.black-venom` | `whole` | — | consumer |
| `mechanic/poison.devil-s-toxin` | `whole` | — | consumer |
| `mechanic/preparation.mandrake-root` | `toughness-bonus-and-stun-to-knocked-down` | — | consumer |
| `mechanic/rule.squishy` | `squishy-overrides-no-pain` | — | consumer |
| `mechanic/skill.always-strikes-first` | `whole` | — | consumer |
| `mechanic/skill.art-of-silent-death` | `fighting-claws-second-attack` | — | consumer |
| `mechanic/skill.art-of-silent-death` | `unarmed-penalty-and-extra-attack` | — | consumer |
| `mechanic/skill.axe-expert` | `whole` | — | consumer |
| `mechanic/skill.axe-master` | `parry-with-normal-axes` | G02 | consumer |
| `mechanic/skill.bellowing-battle-roar` | `bellowing-battle-roar` | — | consumer |
| `mechanic/skill.berserker` | `whole` | — | consumer |
| `mechanic/skill.crushing-blow` | `whole` | — | consumer |
| `mechanic/skill.cutthroat` | `minus-one-enemy-armour-with-paired-daggers` | — | consumer |
| `mechanic/skill.defensive-stance` | `match-with-a-parrying-weapon` | G02 | consumer |
| `mechanic/skill.defensive-stance` | `parry-with-any-weapon` | G02 | consumer |
| `mechanic/skill.duellist` | `whole` | — | consumer |
| `mechanic/skill.elven-agility` | `six-plus-avoidance` | — | consumer |
| `mechanic/skill.expert-fighter` | `whole` | — | consumer |
| `mechanic/skill.expert-swordsman` | `whole` | — | consumer |
| `mechanic/skill.extra-attack` | `whole` | — | consumer |
| `mechanic/skill.ferocious-charge` | `whole` | — | consumer |
| `mechanic/skill.hard-to-kill` | `whole` | — | consumer |
| `mechanic/skill.hatred` | `hatred` | — | consumer |
| `mechanic/skill.head-crusher` | `whole` | G02 | consumer |
| `mechanic/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `mechanic/skill.infallible` | `whole` | — | consumer |
| `mechanic/skill.infinite-hatred` | `infinite-hatred` | — | consumer |
| `mechanic/skill.inspiring-sermon` | `inspiring-sermon` | — | consumer |
| `mechanic/skill.iron-sinews` | `plus-one-strength` | — | consumer |
| `mechanic/skill.jump-up` | `ignores-knocked-down-results` | — | consumer |
| `mechanic/skill.jump-up` | `not-after-no-pain` | — | consumer |
| `mechanic/skill.lightning-reflexes` | `strike-first-when-charged` | — | consumer |
| `mechanic/skill.mighty-biceps` | `whole` | — | consumer |
| `mechanic/skill.mighty-blow` | `whole` | — | consumer |
| `mechanic/skill.miniath` | `parry-with-any-weapon` | G02 | consumer |
| `mechanic/skill.miniath` | `reroll-with-a-parrying-weapon` | G02 | consumer |
| `mechanic/skill.monster-slayer` | `whole` | — | consumer |
| `mechanic/skill.monster-slayer-effective-strength-armour` | `whole` | — | consumer |
| `mechanic/skill.red-fury` | `whole` | — | consumer |
| `mechanic/skill.regeneration` | `four-plus-regeneration` | — | consumer |
| `mechanic/skill.regeneration-5-plus` | `five-plus-regeneration-except-fire` | — | consumer |
| `mechanic/skill.regeneration-blocked-by-blessed` | `blessed-attacks-block-regeneration` | — | consumer |
| `mechanic/skill.resilient` | `minus-one-strength-in-close-combat` | — | consumer |
| `mechanic/skill.righteous-fury` | `whole` | — | consumer |
| `mechanic/skill.shield-mastery` | `shield-parries-and-keeps-its-bonus` | G02 | consumer |
| `mechanic/skill.shield-strike` | `whole` | — | consumer |
| `mechanic/skill.step-aside` | `five-plus-save-after-armour` | — | consumer |
| `mechanic/skill.strength-of-steel` | `whole` | — | consumer |
| `mechanic/skill.strongman` | `whole` | — | consumer |
| `mechanic/skill.sure-strike` | `whole` | — | consumer |
| `mechanic/skill.sword-master` | `match-parry-and-parry-a-six` | G02 | consumer |
| `mechanic/skill.sword-master` | `one-reroll-only` | G02 | consumer |
| `mechanic/skill.swordmaster` | `match-the-to-hit-roll` | G02 | consumer |
| `mechanic/skill.tireless` | `retains-heavy-weapon-strength` | — | consumer |
| `mechanic/skill.tough-as-steel` | `out-of-action-only-on-six` | — | consumer |
| `mechanic/skill.unarmed-critical-strikes` | `whole` | — | consumer |
| `mechanic/skill.unarmed-fighting` | `whole` | — | consumer |
| `mechanic/skill.unbeatable-warrior` | `two-parries-with-two-weapons` | G02 | consumer |
| `mechanic/skill.unstoppable-charge` | `whole` | — | consumer |
| `mechanic/skill.vampire-reflexes` | `combines-with-step-aside-to-four` | — | consumer |
| `mechanic/skill.vampire-reflexes` | `six-plus-unmodifiable-save` | — | consumer |
| `mechanic/skill.virtue-of-valour` | `whole` | — | consumer |
| `mechanic/skill.weapons-of-the-north` | `whole` | — | consumer |
| `mechanic/skill.wound-valour` | `whole` | — | consumer |
| `mechanic/weapon.ankus` | `whole` | — | consumer |
| `mechanic/weapon.axe` | `whole` | — | consumer |
| `mechanic/weapon.bagh-nakh` | `whole` | — | consumer |
| `mechanic/weapon.ball-and-chain` | `whole` | — | consumer |
| `mechanic/weapon.beastlash` | `cannot-be-parried` | — | consumer |
| `mechanic/weapon.beastlash` | `whole` | — | consumer |
| `mechanic/weapon.bo` | `whole` | — | consumer |
| `mechanic/weapon.brass-knuckles` | `whole` | — | consumer |
| `mechanic/weapon.broadsword` | `whole` | — | consumer |
| `mechanic/weapon.cathayan-longsword` | `armour-penetration-discrepancy` | — | consumer |
| `mechanic/weapon.cathayan-longsword` | `whole` | — | consumer |
| `mechanic/weapon.censer` | `whole` | — | consumer |
| `mechanic/weapon.ceremonial-scythe` | `whole` | — | consumer |
| `mechanic/weapon.chain-sticks` | `whole` | — | consumer |
| `mechanic/weapon.choppa` | `whole` | — | consumer |
| `mechanic/weapon.claw-of-the-old-ones` | `whole` | — | consumer |
| `mechanic/weapon.cleaver` | `whole` | — | consumer |
| `mechanic/weapon.dagger` | `whole` | — | consumer |
| `mechanic/weapon.death-knife` | `whole` | — | consumer |
| `mechanic/weapon.double-bladed-sword` | `whole` | G02 | consumer |
| `mechanic/weapon.double-handed-weapon` | `whole` | — | consumer |
| `mechanic/weapon.dragon-sword` | `whole--scope--two-handed-loadout` | — | consumer |
| `mechanic/weapon.draich` | `whole` | — | consumer |
| `mechanic/weapon.dwarf-axe` | `whole` | — | consumer |
| `mechanic/weapon.elven-greatsword` | `whole` | — | consumer |
| `mechanic/weapon.fighting-claws` | `whole` | — | consumer |
| `mechanic/weapon.fist` | `whole` | — | consumer |
| `mechanic/weapon.flail` | `whole` | — | consumer |
| `mechanic/weapon.great-scimitar` | `whole` | — | consumer |
| `mechanic/weapon.halberd` | `whole` | — | consumer |
| `mechanic/weapon.hellblade` | `whole--scope--combat-profile-and-soulseeking` | — | consumer |
| `mechanic/weapon.hellblade` | `whole--scope--deadly` | — | consumer |
| `mechanic/weapon.hellblade` | `whole--scope--two-handed-loadout` | — | consumer |
| `mechanic/weapon.kanabo` | `whole` | — | consumer |
| `mechanic/weapon.katana` | `whole` | — | consumer |
| `mechanic/weapon.katar` | `whole` | — | consumer |
| `mechanic/weapon.knuckledusters` | `whole` | — | consumer |
| `mechanic/weapon.ladle` | `whole` | — | consumer |
| `mechanic/weapon.long-boat-hook` | `whole` | — | consumer |
| `mechanic/weapon.mace` | `whole` | — | consumer |
| `mechanic/weapon.misericordia` | `coup-de-grace` | — | consumer |
| `mechanic/weapon.morning-star` | `whole` | — | consumer |
| `mechanic/weapon.natural-attacks` | `whole` | — | consumer |
| `mechanic/weapon.pike` | `first-turn-scope` | — | consumer |
| `mechanic/weapon.pike` | `whole` | — | consumer |
| `mechanic/weapon.poisoned-daggers` | `whole` | — | consumer |
| `mechanic/weapon.pry-bar` | `whole` | — | consumer |
| `mechanic/weapon.quarter-staff` | `whole` | — | consumer |
| `mechanic/weapon.rapier` | `whole` | — | consumer |
| `mechanic/weapon.scimitar` | `whole` | — | consumer |
| `mechanic/weapon.scythe` | `whole` | — | consumer |
| `mechanic/weapon.shock-rod` | `whole` | — | consumer |
| `mechanic/weapon.sigmarite-hammer` | `whole` | — | consumer |
| `mechanic/weapon.spear` | `whole` | — | consumer |
| `mechanic/weapon.spiked-gauntlet` | `whole` | — | consumer |
| `mechanic/weapon.squig-prodder` | `whole` | — | consumer |
| `mechanic/weapon.starblade` | `whole` | — | consumer |
| `mechanic/weapon.starsword` | `dodge-exception` | — | consumer |
| `mechanic/weapon.starsword` | `whole` | — | consumer |
| `mechanic/weapon.stiletto` | `whole` | — | consumer |
| `mechanic/weapon.stone-axe` | `whole` | — | consumer |
| `mechanic/weapon.sun-gauntlet` | `whole` | — | consumer |
| `mechanic/weapon.sword` | `whole` | — | consumer |
| `mechanic/weapon.trident` | `whole` | — | consumer |
| `mechanic/weapon.unholy-sword` | `whole` | — | consumer |
| `mechanic/weapon.war-maul` | `whole` | — | consumer |
| `mechanic/weapon.weeping-blades` | `whole` | — | consumer |
| `mechanic/weapon.witch-sword` | `whole` | — | consumer |
| `mechanic/weapon.wizards-staff` | `whole` | — | consumer |
| `mechanic/weapon.yambiya` | `whole` | — | consumer |
| `mechanic/weapon.yari-one-handed` | `whole` | — | consumer |
| `mechanic/weapon.yari-two-handed` | `whole` | — | consumer |
| `rule/catalog/general/skill.expert-swordsman/skill.expert-swordsman` | `whole` | — | consumer |
| `rule/catalog/general/skill.jump-up/skill.jump-up` | `ignores-knocked-down-results` | — | consumer |
| `rule/catalog/general/skill.jump-up/skill.jump-up` | `not-after-no-pain` | — | consumer |
| `rule/catalog/general/skill.lightning-reflexes/skill.lightning-reflexes` | `strike-first-when-charged` | — | consumer |
| `rule/catalog/general/skill.mighty-blow/skill.mighty-blow` | `whole` | — | consumer |
| `rule/catalog/general/skill.resilient/skill.resilient` | `minus-one-strength-in-close-combat` | — | consumer |
| `rule/catalog/general/skill.step-aside/skill.step-aside` | `five-plus-save-after-armour` | — | consumer |
| `rule/catalog/general/skill.strike-to-injure/skill.strike-to-injure` | `whole` | — | consumer |
| `rule/catalog/general/skill.strongman/skill.strongman` | `whole` | — | consumer |
| `rule/catalog/general/skill.unstoppable-charge/skill.unstoppable-charge` | `whole` | — | consumer |
| `rule/catalog/warband/skill.always-strikes-first/skill.always-strikes-first` | `whole` | — | consumer |
| `rule/catalog/warband/skill.axe-expert/skill.axe-expert` | `whole` | — | consumer |
| `rule/catalog/warband/skill.axe-master/skill.axe-master` | `parry-with-normal-axes` | G02 | consumer |
| `rule/catalog/warband/skill.bellowing-battle-roar/skill.bellowing-battle-roar` | `bellowing-battle-roar` | — | consumer |
| `rule/catalog/warband/skill.berserker/skill.berserker` | `whole` | — | consumer |
| `rule/catalog/warband/skill.crushing-blow/skill.crushing-blow` | `whole` | — | consumer |
| `rule/catalog/warband/skill.defensive-stance/skill.defensive-stance` | `match-with-a-parrying-weapon` | G02 | consumer |
| `rule/catalog/warband/skill.defensive-stance/skill.defensive-stance` | `parry-with-any-weapon` | G02 | consumer |
| `rule/catalog/warband/skill.elven-agility/skill.elven-agility` | `six-plus-avoidance` | — | consumer |
| `rule/catalog/warband/skill.expert-fighter/skill.expert-fighter` | `whole` | — | consumer |
| `rule/catalog/warband/skill.ferocious-charge/skill.ferocious-charge` | `whole` | — | consumer |
| `rule/catalog/warband/skill.fey-quickness/unclassified` | `six-plus-avoidance` | — | consumer |
| `rule/catalog/warband/skill.hard-to-kill/skill.hard-to-kill` | `whole` | — | consumer |
| `rule/catalog/warband/skill.ignore-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/catalog/warband/skill.infallible/skill.infallible` | `whole` | — | consumer |
| `rule/catalog/warband/skill.infinite-hatred/skill.infinite-hatred` | `infinite-hatred` | — | consumer |
| `rule/catalog/warband/skill.inspiring-sermon/skill.inspiring-sermon` | `inspiring-sermon` | — | consumer |
| `rule/catalog/warband/skill.iron-sinews/skill.iron-sinews` | `plus-one-strength` | — | consumer |
| `rule/catalog/warband/skill.mighty-biceps/skill.mighty-biceps` | `whole` | — | consumer |
| `rule/catalog/warband/skill.miniath/skill.miniath` | `parry-with-any-weapon` | G02 | consumer |
| `rule/catalog/warband/skill.miniath/skill.miniath` | `reroll-with-a-parrying-weapon` | G02 | consumer |
| `rule/catalog/warband/skill.monster-slayer/skill.monster-slayer` | `whole` | — | consumer |
| `rule/catalog/warband/skill.red-fury/skill.red-fury` | `whole` | — | consumer |
| `rule/catalog/warband/skill.regeneration/skill.regeneration` | `four-plus-regeneration` | — | consumer |
| `rule/catalog/warband/skill.righteous-fury/skill.righteous-fury` | `whole` | — | consumer |
| `rule/catalog/warband/skill.shield-mastery/skill.shield-mastery` | `shield-parries-and-keeps-its-bonus` | G02 | consumer |
| `rule/catalog/warband/skill.shield-strike/skill.shield-strike` | `whole` | — | consumer |
| `rule/catalog/warband/skill.strength-of-steel/skill.strength-of-steel` | `whole` | — | consumer |
| `rule/catalog/warband/skill.sure-strike/skill.sure-strike` | `whole` | — | consumer |
| `rule/catalog/warband/skill.sword-master/skill.sword-master` | `match-parry-and-parry-a-six` | G02 | consumer |
| `rule/catalog/warband/skill.sword-master/skill.sword-master` | `one-reroll-only` | G02 | consumer |
| `rule/catalog/warband/skill.tireless/skill.tireless` | `retains-heavy-weapon-strength` | — | consumer |
| `rule/catalog/warband/skill.tough-as-steel/skill.tough-as-steel` | `out-of-action-only-on-six` | — | consumer |
| `rule/catalog/warband/skill.unarmed-fighting/skill.unarmed-fighting` | `whole` | — | consumer |
| `rule/catalog/warband/skill.unbeatable-warrior/skill.unbeatable-warrior` | `two-parries-with-two-weapons` | G02 | consumer |
| `rule/catalog/warband/skill.vampire-reflexes/skill.vampire-reflexes` | `combines-with-step-aside-to-four` | — | consumer |
| `rule/catalog/warband/skill.vampire-reflexes/skill.vampire-reflexes` | `six-plus-unmodifiable-save` | — | consumer |
| `rule/catalog/warband/skill.virtue-of-valour/skill.virtue-of-valour` | `whole` | — | consumer |
| `rule/catalog/warband/skill.weapons-of-the-north/skill.weapons-of-the-north` | `whole` | — | consumer |
| `rule/mordheim/adventurers-kaz/elf--hatred/mechanic.hatred-dark-elves` | `hatred` | — | consumer |
| `rule/mordheim/amazons-lustria/band--amazon-special-skills-skink-hunter/mechanic.strike-first-vs-skinks-first-round` | `whole` | — | consumer |
| `rule/mordheim/amazons-lustria/band--special-rules/mechanic.amazon-isolationists` | `isolationists` | — | consumer |
| `rule/mordheim/arabian-tomb-raiders/band--hate-undead/mechanic.hatred-undead` | `hatred` | — | consumer |
| `rule/mordheim/battle-monks-of-cathay/band--battle-monks-special-skills-energy-focus/compiler.energy-focus` | `whole` | — | consumer |
| `rule/mordheim/battle-monks-of-cathay/dragon-monks--art-of-silent-death/skill.unarmed-critical-strikes` | `whole` | — | consumer |
| `rule/mordheim/battle-monks-of-cathay/dragon-monks--unarmed-fighting/skill.unarmed-fighting` | `whole` | — | consumer |
| `rule/mordheim/battle-monks-of-cathay/warrior-monks--unarmed-fighting/skill.unarmed-fighting` | `whole` | — | consumer |
| `rule/mordheim/beastmen-raiders/band--beastmen-special-skills-horned-one/special-rule.band--beastmen-special-skills-horned-one` | `whole` | — | consumer |
| `rule/mordheim/beastmen-raiders/band--beastmen-special-skills-manhater/mechanic.hatred-human-warband` | `hatred` | — | consumer |
| `rule/mordheim/beastmen-raiders/band--beastmen-special-skills-shaggy-hide/trait.natural-armour-save` | `combines-with-armour` | — | consumer |
| `rule/mordheim/beastmen-raiders/band--beastmen-special-skills-shaggy-hide/trait.natural-armour-save` | `six-plus-save` | — | consumer |
| `rule/mordheim/beastmen-raiders/band--beastmen-special-skills-shaggy-hide/trait.natural-armour-save` | `stacks-per-hide` | — | consumer |
| `rule/mordheim/beastmen-raiders/band--beastmen-special-skills-shaggy-hide/trait.natural-armour-stacks` | `whole` | — | consumer |
| `rule/mordheim/black-dwarfs/band--chaos-dwarf-special-skills-true-grit/skill.tough-as-steel` | `injury-table` | — | consumer |
| `rule/mordheim/black-dwarfs/band--hard-head/trait.concussion-immune` | `concussion-immunity` | — | consumer |
| `rule/mordheim/black-dwarfs/band--hard-to-kill/skill.hard-to-kill` | `out-only-on-six` | — | consumer |
| `rule/mordheim/black-orcs/black-orc-boss--black-orc/trait.natural-armour-save` | `combines-with-equipment` | — | consumer |
| `rule/mordheim/black-orcs/black-orc-boss--black-orc/trait.natural-armour-save` | `six-plus-save` | — | consumer |
| `rule/mordheim/black-orcs/black-orc-boss--black-orc/trait.natural-armour-stacks` | `whole` | — | consumer |
| `rule/mordheim/black-orcs/black-orcs--black-orc/trait.natural-armour-save` | `combines-with-equipment` | — | consumer |
| `rule/mordheim/black-orcs/black-orcs--black-orc/trait.natural-armour-save` | `six-plus-save` | — | consumer |
| `rule/mordheim/black-orcs/black-orcs--black-orc/trait.natural-armour-stacks` | `whole` | — | consumer |
| `rule/mordheim/black-orcs/orc-nuttaz--savage/profile.equipment-restrictions` | `extra-attack` | — | consumer |
| `rule/mordheim/black-orcs/orc-nuttaz--savage/skill.extra-attack` | `whole` | — | consumer |
| `rule/mordheim/black-orcs/troll--regeneration/skill.regeneration` | `fire-exception` | — | consumer |
| `rule/mordheim/black-orcs/troll--regeneration/skill.regeneration` | `regenerate-wound` | — | consumer |
| `rule/mordheim/blood-dragons-mou/grave-guards--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/blood-dragons-mou/hell-hounds--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/blood-dragons-mou/skeleton-warriors--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/blood-dragons-mou/vampire--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/blood-dragons-mou/wights--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/bretonnian-chapel-guard/band--bulging-muscles/mechanic.retain-flail-morning-star-strength-bonus` | `whole` | — | consumer |
| `rule/mordheim/bretonnian-chapel-guard/band--untiring/mechanic.untiring` | `non-magical-immunity` | — | consumer |
| `rule/mordheim/bretonnian-chapel-guard/band--untiring/mechanic.untiring` | `save-floor` | — | consumer |
| `rule/mordheim/bretonnian-chapel-guard/battle-pilgrims--hatred/skill.hatred` | `hatred` | — | consumer |
| `rule/mordheim/bretonnian-knights/band--virtue-of-noble-disdain/mechanic.noble-disdain` | `hatred` | — | consumer |
| `rule/mordheim/bretonnian-knights/band--virtue-of-valour/skill.virtue-of-valour` | `whole` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/cairn-wraith--no-pain/skill.ignore-pain` | `whole` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/malignant-spirits--no-pain/skill.ignore-pain` | `whole` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/malignant-spirits--violent-entry/unimplemented.call-of-the-night-haint-mim.malignant-spirits.violent-entry` | `whole` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/mourngul--no-pain/skill.ignore-pain` | `whole` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/poltergeists--no-pain/skill.ignore-pain` | `whole` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/revenants--no-pain/skill.ignore-pain` | `whole` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/spirit-hosts--no-pain/skill.ignore-pain` | `whole` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/tomb-banshee--no-pain/skill.ignore-pain` | `whole` | — | consumer |
| `rule/mordheim/carnival-of-chaos/band--blessings-of-nurgle-cloud-of-flies/trait.cloud-of-flies` | `whole--scope--melee-hit-penalty` | — | consumer |
| `rule/mordheim/carnival-of-chaos/brutes--unnatural-strength/skill.strongman` | `whole` | — | consumer |
| `rule/mordheim/carnival-of-chaos/nurglings--cloud-of-flies/trait.cloud-of-flies` | `whole` | — | consumer |
| `rule/mordheim/carnival-of-chaos/nurglings--daemonic-aura/trait.magical-attacks` | `whole` | — | consumer |
| `rule/mordheim/carnival-of-chaos/nurglings--daemonic-aura/trait.natural-armour-negated-by-magic` | `whole` | — | consumer |
| `rule/mordheim/carnival-of-chaos/nurglings--daemonic-aura/trait.natural-armour-save` | `five-plus-save` | — | consumer |
| `rule/mordheim/carnival-of-chaos/nurglings--daemonic-aura/trait.natural-armour-save` | `magic-negation` | — | consumer |
| `rule/mordheim/carnival-of-chaos/plague-bearers--cloud-of-flies/trait.cloud-of-flies` | `whole` | — | consumer |
| `rule/mordheim/carnival-of-chaos/plague-bearers--daemonic-aura/trait.magical-attacks` | `whole` | — | consumer |
| `rule/mordheim/carnival-of-chaos/plague-bearers--daemonic-aura/trait.natural-armour-negated-by-magic` | `whole` | — | consumer |
| `rule/mordheim/carnival-of-chaos/plague-bearers--daemonic-aura/trait.natural-armour-save` | `five-plus-save` | — | consumer |
| `rule/mordheim/carnival-of-chaos/plague-bearers--daemonic-aura/trait.natural-armour-save` | `magic-negation` | — | consumer |
| `rule/mordheim/carnival-of-chaos/plague-cart--guardian-unarmed/mechanic.guardian-unarmed` | `whole` | — | consumer |
| `rule/mordheim/channel-rats-mim/domnu--prize-fighter/skill.unarmed-fighting` | `whole` | — | consumer |
| `rule/mordheim/clan-angrund-kep/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `dwarf-axe-reroll` | G02 | consumer |
| `rule/mordheim/clan-angrund-kep/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `parry-matches` | G02 | consumer |
| `rule/mordheim/clan-angrund-kep/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `two-parries` | G02 | consumer |
| `rule/mordheim/clan-angrund-kep/band--dwarf-special-skills-master-of-blades/skill.unbeatable-warrior` | `whole` | G02 | consumer |
| `rule/mordheim/clan-angrund-kep/band--dwarf-special-skills-true-grit/skill.tough-as-steel` | `whole` | — | consumer |
| `rule/mordheim/clan-angrund-kep/band--hard-head/trait.concussion-immune` | `whole` | — | consumer |
| `rule/mordheim/clan-angrund-kep/band--hard-to-kill/skill.hard-to-kill` | `whole` | — | consumer |
| `rule/mordheim/clan-angrund-kep/band--hate-skavens-orcs-and-goblins/mechanic.hatred-skaven-orcs-goblins` | `hatred` | — | consumer |
| `rule/mordheim/clan-angrund-kep/band--slayer-special-skills-berserker/skill.berserker` | `whole` | — | consumer |
| `rule/mordheim/clan-angrund-kep/band--slayer-special-skills-ferocious-charge/skill.ferocious-charge` | `whole` | — | consumer |
| `rule/mordheim/clan-angrund-kep/band--slayer-special-skills-monster-slayer/skill.monster-slayer` | `effective-strength-for-armour` | — | consumer |
| `rule/mordheim/clan-angrund-kep/band--slayer-special-skills-monster-slayer/skill.monster-slayer` | `wounds-on-four-plus` | — | consumer |
| `rule/mordheim/clockworkers-sc/clockwork-fiend--construct/unimplemented.clockworkers-sc.clockwork-fiend.construct` | `construct-no-pain` | — | consumer |
| `rule/mordheim/clockworkers-sc/clockwork-fiend--construct/unimplemented.clockworkers-sc.clockwork-fiend.construct` | `construct-poison-immunity` | — | consumer |
| `rule/mordheim/clockworkers-sc/clockwork-soldiers--construct/unimplemented.clockworkers-sc.clockwork-soldiers.construct` | `construct-no-pain` | — | consumer |
| `rule/mordheim/clockworkers-sc/clockwork-soldiers--construct/unimplemented.clockworkers-sc.clockwork-soldiers.construct` | `construct-poison-immunity` | — | consumer |
| `rule/mordheim/clockworkers-sc/dwarf-engineer--hard-head/trait.concussion-immune` | `whole` | — | consumer |
| `rule/mordheim/clockworkers-sc/dwarf-engineer--hard-to-kill/skill.hard-to-kill` | `whole` | — | consumer |
| `rule/mordheim/crooked-moon-kep/band--hate-stunties-and-skaven/mechanic.hatred-dwarfs-skaven` | `hatred` | — | consumer |
| `rule/mordheim/crooked-moon-kep/fanatics--frantic/mechanic.frantic` | `frantic` | — | consumer |
| `rule/mordheim/crooked-moon-kep/snotling-mob--weedy/trait.injury-profile` | `whole` | — | consumer |
| `rule/mordheim/crooked-moon-kep/troll--regeneration/skill.regeneration` | `fire-exception` | — | consumer |
| `rule/mordheim/crooked-moon-kep/troll--regeneration/skill.regeneration` | `regenerate-wound` | — | consumer |
| `rule/mordheim/cult-of-the-possessed/band--mutations-scorpion-tail/trait.scorpion-tail` | `whole--scope--scorpion-tail` | — | consumer |
| `rule/mordheim/cursed-cavalcade/companions--expert-swordsman/skill.expert-swordsman` | `whole` | — | consumer |
| `rule/mordheim/cursed-cavalcade/great-bear--maddened-with-pain/trait.maddened-with-pain` | `extra-attack-after-wound` | — | consumer |
| `rule/mordheim/cursed-cavalcade/wild-beasts--charge/trait.first-round-charge-attack-bonus` | `whole` | — | consumer |
| `rule/mordheim/dark-elves/band--dark-elf-special-skills-fey-quickness/skill.elven-agility` | `combination-upgrades` | — | consumer |
| `rule/mordheim/dark-elves/band--dark-elf-special-skills-fey-quickness/skill.elven-agility` | `six-plus-avoid` | — | consumer |
| `rule/mordheim/dark-elves/band--kindred-hatred/mechanic.hatred-high-elves` | `hatred` | — | consumer |
| `rule/mordheim/dark-elves/cold-one-beasthounds--scaly-skin/trait.natural-armour-save` | `six-plus-save` | — | consumer |
| `rule/mordheim/dark-elves/cold-one-beasthounds--scaly-skin/trait.natural-armour-save` | `unmodified-six` | — | consumer |
| `rule/mordheim/dark-elves/cold-one-beasthounds--scaly-skin/trait.natural-armour-unmodified` | `critical-negation` | — | consumer |
| `rule/mordheim/dark-elves/cold-one-beasthounds--scaly-skin/trait.natural-armour-unmodified` | `no-strength-reduction` | — | consumer |
| `rule/mordheim/dreamwalkers-cult-of-morr-fbg/andanti--estalian-tecnique/unimplemented.dreamwalkers-cult-of-morr-fbg.andanti.estalian-tecnique` | `parry-rolls-under-ws` | — | consumer |
| `rule/mordheim/dreamwalkers-cult-of-morr-fbg/band--hate-undead/mechanic.hatred-undead` | `hatred` | — | consumer |
| `rule/mordheim/druchii-mic/band--kindred-hatred/mechanic.hatred-high-elves` | `hatred` | — | consumer |
| `rule/mordheim/druchii-mic/noble--fey-quickness/skill.elven-agility` | `whole` | — | consumer |
| `rule/mordheim/dwarf-guildsmen-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-guildsmen-kaz.band.town-crier-6-inheritance` | `inherited-combat-rules` | — | consumer |
| `rule/mordheim/dwarf-rangers/band--dwarf-special-skills-combat-master/skill.unbeatable-warrior` | `whole` | G02 | consumer |
| `rule/mordheim/dwarf-rangers/band--dwarf-special-skills-true-grit/skill.tough-as-steel` | `whole` | — | consumer |
| `rule/mordheim/dwarf-rangers/band--hard-head/trait.concussion-immune` | `whole` | — | consumer |
| `rule/mordheim/dwarf-rangers/band--hard-to-kill/skill.hard-to-kill` | `whole` | — | consumer |
| `rule/mordheim/dwarf-rangers/band--hate-orcs-and-goblins/mechanic.hatred-orcs-goblins` | `hatred` | — | consumer |
| `rule/mordheim/dwarf-rangers/band--slayer-special-skills-berserker/skill.berserker` | `whole` | — | consumer |
| `rule/mordheim/dwarf-rangers/band--slayer-special-skills-ferocious-charge/skill.ferocious-charge` | `whole` | — | consumer |
| `rule/mordheim/dwarf-rangers/band--slayer-special-skills-monster-slayer/skill.monster-slayer` | `whole` | — | consumer |
| `rule/mordheim/dwarf-slayer-cult-web/band--hard-head/trait.concussion-immune` | `whole` | — | consumer |
| `rule/mordheim/dwarf-slayer-cult-web/band--hard-to-kill/skill.hard-to-kill` | `whole` | — | consumer |
| `rule/mordheim/dwarf-slayer-cult-web/band--hatred-orcs-and-goblins/mechanic.hatred-orcs-goblins` | `hatred` | — | consumer |
| `rule/mordheim/dwarf-slayers-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-slayers-kaz.band.town-crier-6-inheritance` | `inherited-combat-rules` | — | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `match-the-to-hit-roll` | G02 | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `reroll-with-two-dwarf-axes` | G02 | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `two-parries-with-two-parry-weapons` | G02 | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.unbeatable-warrior` | `match-the-to-hit-roll` | G02 | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.unbeatable-warrior` | `reroll-with-two-dwarf-axes` | G02 | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.unbeatable-warrior` | `two-parries-with-two-parry-weapons` | G02 | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-true-grit/skill.tough-as-steel` | `whole` | — | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--hard-head/trait.concussion-immune` | `whole` | — | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--hard-to-kill/skill.hard-to-kill` | `whole` | — | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--hate-orcs-and-goblins/mechanic.hatred-orcs-goblins` | `hatred` | — | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--slayer-special-skills-berserker/skill.berserker` | `whole` | — | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--slayer-special-skills-ferocious-charge/skill.ferocious-charge` | `whole` | — | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--slayer-special-skills-monster-slayer/skill.monster-slayer` | `whole` | — | consumer |
| `rule/mordheim/fallen-the-rel/revenant--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/fen-guard-mim/band--bark-skin/trait.natural-armour-save` | `no-save-and-fire-negation` | — | encargo explícito; consumer vacío |
| `rule/mordheim/fen-guard-mim/band--bark-skin/trait.natural-armour-save` | `six-plus-natural-save` | — | consumer |
| `rule/mordheim/fen-guard-mim/band--bark-skin/trait.natural-armour-save` | `strength-cap-at-six` | — | consumer |
| `rule/mordheim/fen-guard-mim/band--hard-to-kill/mechanic.fen-hard-to-kill` | `fire-cancels-the-rule` | — | consumer |
| `rule/mordheim/fen-guard-mim/band--hard-to-kill/mechanic.fen-hard-to-kill` | `out-of-action-only-on-six` | — | consumer |
| `rule/mordheim/fen-guard-mim/treekin--redwood/trait.natural-armour-save` | `four-plus-save` | — | consumer |
| `rule/mordheim/forest-goblins-lus/gigantic-spider--poisonous/trait.poisonous-injury` | `whole` | — | consumer |
| `rule/mordheim/forest-goblins/gigantic-spider--chitin-armour/trait.natural-armour-save` | `four-plus-save` | — | consumer |
| `rule/mordheim/forest-goblins/gigantic-spider--poisonous/trait.poisonous-injury` | `whole` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/band--ethereal/mechanic.ghost-pirate-ethereal` | `four-plus-unmodifiable-save` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/band--ethereal/mechanic.ghost-pirate-ethereal` | `magical-attacks-bypass` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/ghost-captain--undead/unimplemented.ghost-pirates-sar.ghost-captain.undead` | `undead-poison-immunity` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/gibbets--iron-cage/mechanic.iron-cage` | `five-plus-armour-save` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/gibbets--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/gibbets--undead/unimplemented.ghost-pirates-sar.gibbets.undead` | `undead-poison-immunity` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/screaming-ghosts--undead/unimplemented.ghost-pirates-sar.screaming-ghosts.undead` | `undead-poison-immunity` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/skeleton-mates--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/skeleton-mates--undead/unimplemented.ghost-pirates-sar.skeleton-mates.undead` | `undead-poison-immunity` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/the-bloated--squishy/rule.squishy` | `squishy-suppresses-no-pain` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/the-bloated--undead/unimplemented.ghost-pirates-sar.the-bloated.undead` | `undead-poison-immunity` | — | consumer |
| `rule/mordheim/grave-robbers-sylv/band--undead-foes/mechanic.hatred-undead` | `hatred` | — | consumer |
| `rule/mordheim/guild-of-disgraced-engineers-mim/band--hard-head/trait.concussion-immune` | `ignore-concussion` | — | consumer |
| `rule/mordheim/guild-of-disgraced-engineers-mim/band--hard-to-kill/skill.hard-to-kill` | `out-of-action-only-on-six` | — | consumer |
| `rule/mordheim/gunnery-school-of-nuln/pistoliers--crack-shot/skill.crack-shot` | `whole` | — | consumer |
| `rule/mordheim/halflings-mic/halfling-elder--layers-of-fat/trait.natural-armour-save` | `regardless-of-strength` | — | consumer |
| `rule/mordheim/halflings-mic/halfling-elder--layers-of-fat/trait.natural-armour-save` | `six-plus-basic-save` | — | consumer |
| `rule/mordheim/high-elves-lus/band--skill-fey-quickness/skill.elven-agility` | `six-plus-avoidance` | — | consumer |
| `rule/mordheim/high-elves-lus/band--skill-miniath/skill.miniath` | `additional-attempt` | — | consumer |
| `rule/mordheim/high-elves-lus/band--skill-miniath/skill.miniath` | `parry-with-any-weapon` | G02 | consumer |
| `rule/mordheim/high-elves-lus/band--skill-unerring-strike/skill.sure-strike` | `whole` | — | consumer |
| `rule/mordheim/hochland-bandits/duelist--swordmaster/skill.swordmaster` | `match-the-to-hit-roll` | G02 | consumer |
| `rule/mordheim/horned-hunters/band--horned-hunter-special-skills-foul-odour/mechanic.foul-odour` | `foul-odour` | — | consumer |
| `rule/mordheim/horned-hunters/horned-hunter--hang-the-bandit/unimplemented.horned-hunters.horned-hunter.hang-the-bandit` | `hang-the-bandit` | — | consumer |
| `rule/mordheim/horned-hunters/initiates--hang-the-bandit/unimplemented.horned-hunters.initiates.hang-the-bandit` | `hang-the-bandit` | — | consumer |
| `rule/mordheim/house-guard-sc/band--dueling-pride/mechanic.dueling-pride` | `whole` | — | consumer |
| `rule/mordheim/house-guard-sc/pikemen--pikewall/mechanic.pikewall` | `reroll-when-charged-with-first-strike` | — | consumer |
| `rule/mordheim/kislevites/cossacks--hate-chaos/mechanic.hatred-chaotic-warband` | `hatred` | — | consumer |
| `rule/mordheim/knights-of-the-bitter-moors-mim/band--virtue-of-noble-disdain/mechanic.noble-disdain` | `hatred` | — | consumer |
| `rule/mordheim/knights-of-the-bitter-moors-mim/band--virtue-of-valour/skill.wound-valour` | `whole` | — | consumer |
| `rule/mordheim/lizardmen-lus/band--lizardmen-special-skills-saurus-only-bellowing-battle-roar/skill.bellowing-battle-roar` | `bellowing-battle-roar` | — | consumer |
| `rule/mordheim/lizardmen-lus/kroxigor--scaly-skin/trait.natural-armour-save` | `four-plus-natural-save` | — | consumer |
| `rule/mordheim/lizardmen/band--lizardmen-special-skills-saurus-only-bellowing-battle-roar/skill.bellowing-battle-roar` | `bellowing-battle-roar` | — | consumer |
| `rule/mordheim/lizardmen/kroxigor--scaly-skin/trait.natural-armour-save` | `four-plus-natural-save` | — | consumer |
| `rule/mordheim/lords-of-the-marsh-mim/fimir-warriors--spiked-tail/profile-rule.fimir-warriors--spiked-tail` | `whole` | — | consumer |
| `rule/mordheim/lords-of-the-marsh-mim/young-nobles--spiked-tail/profile-rule.young-nobles--spiked-tail` | `whole` | — | consumer |
| `rule/mordheim/lothern-sea-patrol-sar/sea-rangers--hate-dark-elves/mechanic.hatred-dark-elves` | `hatred` | — | consumer |
| `rule/mordheim/lustrian-reavers/barbary-monkey--nimble/trait.ward-save` | `five-plus-ward-save` | — | consumer |
| `rule/mordheim/lustrian-reavers/estalian-warhound--armoured/trait.natural-armour-save` | `five-plus-armour-save` | — | consumer |
| `rule/mordheim/lustrian-reavers/saurus-slayer--duellist/skill.duellist` | `whole` | — | consumer |
| `rule/mordheim/masters-of-horror-sylv/flesh-construct--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/masters-of-horror-sylv/thrall--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/masters-of-horror-sylv/zombies--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/mazzalupo-web/fallen-noble--ye-give-way/unimplemented.mazzalupo-web.fallen-noble.ye-give-way` | `individual-modifiers` | — | consumer |
| `rule/mordheim/mercenaries/swordsmen--expert-swordsmen/skill.expert-swordsman` | `whole` | — | consumer |
| `rule/mordheim/merchant-caravans/blackguards--strongman/skill.strongman` | `whole` | — | consumer |
| `rule/mordheim/merchant-caravans/knights-vanguard--lightning-reflexes/skill.lightning-reflexes` | `strike-first-when-charged` | — | consumer |
| `rule/mordheim/metal-mongers-mim/machine-ogre--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/mootlanders/band--fragile-halflings/trait.fragile-halflings` | `injury-roll-of-two-is-stunned` | — | consumer |
| `rule/mordheim/necrarchs-mou/abomination--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/necrarchs-mou/defiled--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/necrarchs-mou/nosferatu--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/necrarchs-mou/skeleton--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/abomination--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/necrarch-vampire--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/skeletal-warrior--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/thrall--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/zombie--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/night-goblins-kaz/band--hate-stunties/unimplemented.night-goblins-kaz.band.hate-stunties` | `hatred` | — | consumer |
| `rule/mordheim/night-goblins-kaz/fanatics--frantic/mechanic.frantic` | `whole` | — | consumer |
| `rule/mordheim/night-goblins-kaz/snotling-mob--weedy/trait.injury-profile` | `whole` | — | consumer |
| `rule/mordheim/night-goblins-kaz/troll--regeneration/skill.regeneration` | `fire-exception` | — | consumer |
| `rule/mordheim/night-goblins-kaz/troll--regeneration/skill.regeneration` | `regenerate-wound` | — | consumer |
| `rule/mordheim/night-goblins-mic/band--hate-stunties/unimplemented.night-goblins-mic.band.hate-stunties` | `hatred` | — | consumer |
| `rule/mordheim/night-goblins-mic/snotling-mob-consists-of-5-snotlings--weedy/trait.injury-profile` | `whole` | — | consumer |
| `rule/mordheim/night-goblins-mic/troll--regeneration/skill.regeneration` | `fire-exception` | — | consumer |
| `rule/mordheim/night-goblins-mic/troll--regeneration/skill.regeneration` | `regenerate-wound` | — | consumer |
| `rule/mordheim/night-goblins-web/band--hate-stunties/unimplemented.night-goblins-web.band.hate-stunties` | `hatred` | — | consumer |
| `rule/mordheim/night-goblins-web/shaman--fungus-brew/unimplemented.night-goblins-web.shaman.fungus-brew` | `fungus-belligerent` | — | consumer |
| `rule/mordheim/night-goblins-web/shaman--fungus-brew/unimplemented.night-goblins-web.shaman.fungus-brew` | `fungus-numbed` | — | consumer |
| `rule/mordheim/night-goblins-web/snotlings--dodgy/trait.cloud-of-flies` | `whole--scope--melee-hit-penalty` | — | consumer |
| `rule/mordheim/night-goblins-web/snotlings--weedy/trait.injury-profile` | `whole` | — | consumer |
| `rule/mordheim/night-goblins-web/troll--regeneration/skill.regeneration` | `fire-exception` | — | consumer |
| `rule/mordheim/night-goblins-web/troll--regeneration/skill.regeneration` | `regenerate-wound` | — | consumer |
| `rule/mordheim/norse-explorers-btb/band--norse-special-skills-berserk-charge/special-rule.band--norse-special-skills-berserk-charge` | `whole` | — | consumer |
| `rule/mordheim/norse-explorers-btb/band--norse-special-skills-crushing-blow/skill.crushing-blow` | `whole` | — | consumer |
| `rule/mordheim/norse-explorers-btb/band--norse-special-skills-shield-master/skill.shield-mastery` | `parry-with-a-shield` | G02 | consumer |
| `rule/mordheim/norse-explorers-btb/band--norse-special-skills-shield-master/skill.shield-mastery` | `six-plus-save` | — | consumer |
| `rule/mordheim/norse-explorers-lustria/band--norse-special-skills-berserk-charge/special-rule.band--norse-special-skills-berserk-charge` | `whole` | — | consumer |
| `rule/mordheim/norse-explorers-lustria/band--norse-special-skills-crushing-blow/skill.crushing-blow` | `whole` | — | consumer |
| `rule/mordheim/norse-explorers-lustria/band--norse-special-skills-shield-master/skill.shield-mastery` | `parry-with-a-shield` | G02 | consumer |
| `rule/mordheim/norse-explorers-lustria/band--norse-special-skills-shield-master/skill.shield-mastery` | `six-plus-save` | — | consumer |
| `rule/mordheim/ogre-hunting-party-web/band--greenskins/unimplemented.ogre-hunting-party-web.band.greenskins` | `greenskin-classification` | — | consumer |
| `rule/mordheim/ogre-hunting-party-web/sabretusks--charge/mechanic.sabretusk-charge` | `whole` | — | consumer |
| `rule/mordheim/ogre-hunting-party-web/sabretusks--tough-hide/trait.natural-armour-save` | `five-plus-armour-save` | — | consumer |
| `rule/mordheim/orc-mob/band--orc-special-skills-well-ard/mechanic.armour-save-bonus` | `plus-one-to-armour-saves` | — | consumer |
| `rule/mordheim/orc-mob/troll--regeneration/skill.regeneration` | `fire-exception` | — | consumer |
| `rule/mordheim/orc-mob/troll--regeneration/skill.regeneration` | `regenerate-wound` | — | consumer |
| `rule/mordheim/orc-pirates-sar/sea-troll--slimy/mechanic.sea-troll-slime` | `minus-one-to-hit-in-melee` | — | consumer |
| `rule/mordheim/orc-pirates-sar/sea-troll--slimy/mechanic.sea-troll-slime` | `natural-six-always-hits` | — | consumer |
| `rule/mordheim/order-of-the-mare-web/dame-of-the-mare--ancient-armour/trait.natural-armour-negated-by-magic` | `five-plus-unmodifiable-save` | — | consumer |
| `rule/mordheim/order-of-the-mare-web/dame-of-the-mare--ancient-armour/trait.natural-armour-negated-by-magic` | `negated-by-magical-attacks` | — | consumer |
| `rule/mordheim/order-of-the-mare-web/dame-of-the-mare--ancient-armour/trait.natural-armour-save` | `five-plus-unmodifiable-save` | — | consumer |
| `rule/mordheim/order-of-the-mare-web/dame-of-the-mare--ancient-armour/trait.natural-armour-save` | `negated-by-magical-attacks` | — | consumer |
| `rule/mordheim/order-of-the-mare-web/dame-of-the-mare--ancient-armour/trait.natural-armour-unmodified` | `five-plus-unmodifiable-save` | — | consumer |
| `rule/mordheim/order-of-the-mare-web/dame-of-the-mare--ancient-armour/trait.natural-armour-unmodified` | `negated-by-magical-attacks` | — | consumer |
| `rule/mordheim/order-of-the-mare-web/pilgrims--hatred/skill.hatred` | `hatred` | — | consumer |
| `rule/mordheim/ostlanders/band--ostlander-special-skills-foul-odour/mechanic.foul-odour` | `foul-odour` | — | consumer |
| `rule/mordheim/pirates-of-the-cathayan-sea-sar/dragon-monk--unarmed-mastery/skill.unarmed-fighting` | `whole` | — | consumer |
| `rule/mordheim/pit-fighters/band--free-the-slaves/unimplemented.pit-fighters.band.free-the-slaves` | `hate-slavers` | — | consumer |
| `rule/mordheim/pit-fighters/band--pit-fighter-skill-bulging-biceps/skill.mighty-biceps` | `whole` | — | consumer |
| `rule/mordheim/pit-fighters/band--troll-slayer-special-skills-berserker/skill.berserker` | `whole` | — | consumer |
| `rule/mordheim/pit-fighters/band--troll-slayer-special-skills-ferocious-charge/skill.ferocious-charge` | `whole` | — | consumer |
| `rule/mordheim/pit-fighters/band--troll-slayer-special-skills-monster-slayer/skill.monster-slayer` | `whole` | — | consumer |
| `rule/mordheim/pit-fighters/dwarf-troll-slayer--hard-head/trait.concussion-immune` | `whole` | — | consumer |
| `rule/mordheim/pit-fighters/dwarf-troll-slayer--hard-to-kill/skill.hard-to-kill` | `whole` | — | consumer |
| `rule/mordheim/pit-fighters/dwarf-troll-slayer--hate-orcs-and-goblins/unimplemented.pit-fighters.dwarf-troll-slayer.hate-orcs-and-goblins` | `hatred` | — | consumer |
| `rule/mordheim/pit-fighters/dwarf-troll-slayer--pit-fighter/trait.pit-fighter` | `whole` | G01 | encargo explícito; consumer vacío |
| `rule/mordheim/pit-fighters/ogre-pit-fighter--pit-fighter/trait.pit-fighter` | `whole` | G01 | encargo explícito; consumer vacío |
| `rule/mordheim/pit-fighters/pit-fighters--pit-fighter/trait.pit-fighter` | `whole` | G01 | encargo explícito; consumer vacío |
| `rule/mordheim/pit-fighters/pit-king--pit-fighter/trait.pit-fighter` | `whole` | G01 | encargo explícito; consumer vacío |
| `rule/mordheim/pit-fighters/pit-veterans--pit-fighter/trait.pit-fighter` | `whole` | G01 | encargo explícito; consumer vacío |
| `rule/mordheim/pit-fighters/pursuers--pit-fighter/trait.pit-fighter` | `whole` | G01 | encargo explícito; consumer vacío |
| `rule/mordheim/protectorate-of-sigmar-lotd3/templar--zealous/mechanic.hatred-chaotic-warband` | `hatred` | — | consumer |
| `rule/mordheim/restless-dead/grave-guards--no-pain/skill.ignore-pain` | `whole` | — | consumer |
| `rule/mordheim/restless-dead/liche--no-pain/skill.ignore-pain` | `whole` | — | consumer |
| `rule/mordheim/restless-dead/scarecrows--no-pain/skill.ignore-pain` | `whole` | — | consumer |
| `rule/mordheim/restless-dead/skeletons--no-pain/skill.ignore-pain` | `whole` | — | consumer |
| `rule/mordheim/restless-dead/wights--no-pain/skill.ignore-pain` | `whole` | — | consumer |
| `rule/mordheim/restless-dead/zombies--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/sea-ghosts-mim/band--dance-the-shadows-coil/dance.the-shadows-coil` | `whole` | — | consumer |
| `rule/mordheim/sea-ghosts-mim/band--dance-whirling-death/dance.whirling-death` | `whole` | — | consumer |
| `rule/mordheim/sea-ghosts-mim/band--dance-woven-mist/dance.woven-mist` | `whole` | — | consumer |
| `rule/mordheim/sea-ghosts-mim/band--sundering/mechanic.hatred-dark-elves` | `hatred` | — | consumer |
| `rule/mordheim/sea-ghosts-mim/feast-master--talismanic-tattoos/trait.ward-save` | `tattoo-save` | — | consumer |
| `rule/mordheim/shadow-warriors/band--hate-dark-elves/mechanic.hatred-dark-elves` | `hatred` | — | consumer |
| `rule/mordheim/silent-brotherhood-sc/band--skill-cutthroat/skill.cutthroat` | `dagger-pair-penalty` | — | consumer |
| `rule/mordheim/silent-brotherhood-sc/silent-master--perfect-killer/trait.perfect-killer` | `whole` | — | consumer |
| `rule/mordheim/sisters-of-sigmar/band--special-skills-righteous-fury/skill.righteous-fury` | `whole` | — | consumer |
| `rule/mordheim/skaven-clan-eshin/assassin-adept--perfect-killer/trait.perfect-killer` | `whole` | — | consumer |
| `rule/mordheim/skaven-clan-eshin/band--skaven-special-skills-art-of-silent-death/skill.art-of-silent-death` | `whole` | — | consumer |
| `rule/mordheim/skaven-clan-pestilens/band--clan-pestilens-special-skills-ignore-pain/skill.ignore-pain` | `ignore-pain` | — | consumer |
| `rule/mordheim/skaven-of-clan-moulder-web/wolf-rats--poisoned-attack/mechanic.wolf-rat-bite` | `whole` | — | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-champion--resilient/skill.resilient` | `whole` | — | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-priest--plague-monk-robes/trait.natural-armour-save` | `soft-leather-equivalent` | — | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-priest--resilient/skill.resilient` | `whole` | — | consumer |
| `rule/mordheim/slave-uprising-kep/band--hate-skaven/mechanic.hatred-skaven` | `hatred` | — | consumer |
| `rule/mordheim/slave-uprising-kep/goblin-leader--hate-dwarfs/mechanic.hatred-dwarfs` | `hatred` | — | consumer |
| `rule/mordheim/slave-uprising-kep/goblin-slaves--hate-dwarfs/mechanic.hatred-dwarfs` | `hatred` | — | consumer |
| `rule/mordheim/slayer-pirates-sar/band--slayer-rules/skill.hard-to-kill` | `whole--scope--hard-to-kill` | — | consumer |
| `rule/mordheim/slayer-pirates-sar/band--slayer-rules/trait.concussion-immune` | `whole` | — | consumer |
| `rule/mordheim/snotlings-web/band--dodgy/skill.elven-agility` | `whole` | — | consumer |
| `rule/mordheim/snotlings-web/band--not-so-tough-gits/trait.injury-profile` | `injury-ladder` | — | consumer |
| `rule/mordheim/snotlings-web/band--pointy-stick/unimplemented.snotlings-web.item.pointy-stick` | `armour-penalty` | — | consumer |
| `rule/mordheim/snotlings-web/bullied-goblin--achilles-heel/unimplemented.snotlings-web.special.achilles-heel` | `criticals-and-charge--scope--criticals-on-six` | — | consumer |
| `rule/mordheim/snotlings-web/bullied-goblin--frustratingly-tiny/mechanic.frustratingly-tiny` | `minus-one-to-hit` | — | consumer |
| `rule/mordheim/snotlings-web/bullied-goblin--not-a-snotling/trait.injury-profile` | `exempt-from-snotling-rules` | — | consumer |
| `rule/mordheim/snotlings-web/snotling-mobs--not-so-small-surprisingly-tough/trait.injury-profile` | `normal-table` | — | consumer |
| `rule/mordheim/snotlings-web/wheelo--tough-machine/trait.injury-profile` | `normal-table` | — | consumer |
| `rule/mordheim/sons-of-hashut/band--chaos-dwarfs-special-skills-true-grit/skill.tough-as-steel` | `injury-table-1-3-4-5-6` | — | consumer |
| `rule/mordheim/sons-of-hashut/band--chaos-dwarfs-special-skills-unlimited-hatred/skill.hatred` | `hatred` | — | consumer |
| `rule/mordheim/sons-of-hashut/band--hard-head/trait.concussion-immune` | `ignore-concussion` | — | consumer |
| `rule/mordheim/sons-of-hashut/band--hard-to-kill/skill.hard-to-kill` | `out-of-action-only-on-six` | — | consumer |
| `rule/mordheim/strigoi-kaz/bats--squishy/mechanic.bat-injury-chart` | `bat-injury-chart` | — | consumer |
| `rule/mordheim/strigoi-kaz/fell-bats--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/strigoi-kaz/skeletons--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/strigoi-kaz/vampire--bestial/mechanic.bestial` | `bestial` | — | consumer |
| `rule/mordheim/survivors-of-strigos-sylv/domnu--gypsy-ward/mechanic.gypsy-ward` | `five-plus-ward-against-magic` | — | consumer |
| `rule/mordheim/survivors-of-strigos-sylv/strigoi-vampire--kindred-hatred/mechanic.kindred-hatred` | `hatred` | — | consumer |
| `rule/mordheim/survivors-of-strigos-sylv/strigoi-vampire--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/tileans/band--miraglean-hatred-skaven/mechanic.hatred-skaven` | `hatred` | — | consumer |
| `rule/mordheim/tileans/duelists--cloak-dagger/trait.counts-as-buckler` | `counts-as-buckler` | G02 | consumer |
| `rule/mordheim/tomb-guardians/band--no-pain/skill.ignore-pain` | `undead-class-no-pain` | — | consumer |
| `rule/mordheim/undead/dire-wolves--charge/trait.charge-attack-bonus` | `whole` | — | consumer |
| `rule/mordheim/undead/dire-wolves--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/undead/vampire--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/undead/zombies--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/mordheim/underworld-alliance-mim/boglars--regeneration/skill.regeneration-5-plus` | `five-plus-regeneration` | — | consumer |
| `rule/mordheim/underworld-alliance-mim/warpstone-troll--regeneration/skill.regeneration` | `four-plus-regeneration` | — | consumer |
| `rule/mordheim/vampire-hunters-of-sylvania-lotd5/band--special-skill-blessing-of-morr/mechanic.blessing-of-morr` | `whole` | — | consumer |
| `rule/mordheim/vampire-hunters-of-sylvania-lotd5/band--special-skill-thirst-for-vengeance/mechanic.thirst-for-vengeance` | `charge-attack-bonus` | — | consumer |
| `rule/mordheim/vampire-hunters-of-sylvania-lotd5/band--special-skill-thirst-for-vengeance/mechanic.thirst-for-vengeance` | `hatred-undead` | — | consumer |
| `rule/mordheim/witch-hunters/witch-hunter-captain--burn-the-witch/unimplemented.witch-hunters.witch-hunter-captain.burn-the-witch` | `burn-the-witch` | — | consumer |
| `rule/mordheim/witch-hunters/witch-hunters--burn-the-witch/unimplemented.witch-hunters.witch-hunters.burn-the-witch` | `burn-the-witch` | — | consumer |
| `rule/mordheim/wood-elves-of-athel-loren-web/band--hate-dark-elves/mechanic.hatred-dark-elves` | `hatred` | — | consumer |
| `rule/trollheim/chaos-streets-bretonnian-knights/band--virtue-of-noble-disdain/mechanic.noble-disdain` | `hatred` | — | consumer |
| `rule/trollheim/chaos-streets-bretonnian-knights/band--virtue-of-valour/skill.virtue-of-valour` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-deathbringers/band--deathbringer-special-skills-art-of-unarmed-combat/skill.art-of-silent-death` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-deathbringers/band--deathbringer-special-skills-death-blow/mechanic.death-blow` | `single-attack-with-bonuses` | — | consumer |
| `rule/trollheim/chaos-streets-deathbringers/band--deathbringer-special-skills-defensive-stance/skill.defensive-stance` | `match-with-a-parrying-weapon` | G02 | consumer |
| `rule/trollheim/chaos-streets-deathbringers/band--deathbringer-special-skills-defensive-stance/skill.defensive-stance` | `parry-with-any-weapon` | G02 | consumer |
| `rule/trollheim/chaos-streets-deathbringers/knives--dagger-master/trait.dagger-master` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-deathbringers/shadow-blade--consummate-fighter/trait.perfect-killer` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `match-the-to-hit-roll` | G02 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `reroll-with-two-dwarf-axes` | G02 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.sword-master` | `two-parries-with-two-parry-weapons` | G02 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.unbeatable-warrior` | `match-the-to-hit-roll` | G02 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.unbeatable-warrior` | `reroll-with-two-dwarf-axes` | G02 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-master-of-blades/skill.unbeatable-warrior` | `two-parries-with-two-parry-weapons` | G02 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-true-grit/skill.tough-as-steel` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--hard-head/trait.concussion-immune` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--hard-to-kill/skill.hard-to-kill` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--hate-orcs-and-goblins/mechanic.hatred-orcs-goblins` | `hatred` | — | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--slayer-special-skills-berserker/skill.berserker` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--slayer-special-skills-ferocious-charge/skill.ferocious-charge` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--slayer-special-skills-monster-slayer/skill.monster-slayer` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-greenskins/band--orc-special-skills-well-ard/mechanic.armour-save-bonus` | `plus-one-to-armour-saves` | — | consumer |
| `rule/trollheim/chaos-streets-greenskins/troll--regeneration/skill.regeneration` | `fire-exception` | — | consumer |
| `rule/trollheim/chaos-streets-greenskins/troll--regeneration/skill.regeneration` | `regenerate-wound` | — | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/desolate-soul--profound-hatred/unimplemented.chaos-streets-mordheim-inhabitants.desolate-soul.profound-hatred` | `profound-hatred` | — | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/band--free-the-slaves/unimplemented.chaos-streets-pit-fighters.band.free-the-slaves` | `hate-slavers` | — | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/band--pit-fighter-skill-bulging-biceps/skill.mighty-biceps` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/band--troll-slayer-special-skills-berserker/skill.berserker` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/band--troll-slayer-special-skills-ferocious-charge/skill.ferocious-charge` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/band--troll-slayer-special-skills-monster-slayer/skill.monster-slayer` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/dwarf-troll-slayer--hard-head/trait.concussion-immune` | `ignore-concussion` | — | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/dwarf-troll-slayer--hard-to-kill/skill.hard-to-kill` | `out-of-action-only-on-six` | — | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/dwarf-troll-slayer--hate-orcs-and-goblins/unimplemented.chaos-streets-pit-fighters.dwarf-troll-slayer.hate-orcs-and-goblins` | `hatred` | — | consumer |
| `rule/trollheim/chaos-streets-sigmar-protectorate/templar--devout/unimplemented.chaos-streets-sigmar-protectorate.templar.devout` | `hatred` | — | consumer |
| `rule/trollheim/chaos-streets-sons-of-nagarythe/band--hate-dark-elves/unimplemented.chaos-streets-sons-of-nagarythe.band.hate-dark-elves` | `hatred` | — | consumer |
| `rule/trollheim/chaos-streets-sons-of-nagarythe/band--shadow-warrior-special-skills-elven-agility/skill.elven-agility` | `six-plus-avoidance` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--blood-dragon-power-infallible/skill.infallible` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--blood-dragon-power-red-fury/skill.red-fury` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--blood-dragon-power-strength-of-steel/skill.strength-of-steel` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--blood-dragon-power-sword-master/skill.sword-master` | `match-parry-and-parry-a-six` | G02 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--blood-dragon-power-sword-master/skill.sword-master` | `one-reroll-only` | G02 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--lahmia-power-lost-innocence/skill.always-strikes-first` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--strigoi-power-curse-of-the-reborn/skill.regeneration` | `blocked-by-fire-and-blessed` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--strigoi-power-curse-of-the-reborn/skill.regeneration` | `four-plus-regeneration` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--strigoi-power-curse-of-the-reborn/skill.regeneration-blocked-by-blessed` | `blocked-by-fire-and-blessed` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--strigoi-power-curse-of-the-reborn/skill.regeneration-blocked-by-blessed` | `four-plus-regeneration` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--strigoi-power-infinite-hatred/skill.infinite-hatred` | `infinite-hatred` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--strigoi-power-iron-sinews/skill.iron-sinews` | `plus-one-strength` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/blood-dragon-vampire--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/dire-wolf--charge/trait.charge-attack-bonus` | `whole` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/dire-wolf--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/lahmia-vampire--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/necrarch-vampire--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/strigoi-vampire--hatred-everyone/skill.hatred` | `hatred` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/strigoi-vampire--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/vampire-bat--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/von-carstein-vampire--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/zombie--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/band--hard-head/trait.concussion-immune` | `whole` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/band--hard-to-kill/skill.hard-to-kill` | `whole` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/band--hate-greenskins/unimplemented.khemri-cursed-of-karak-zorn.band.hate-greenskins` | `hatred` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/band--karak-zorn-special-skills-hard-as-steel/skill.tough-as-steel` | `whole` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/band--troll-slayer-special-skills-berserker/skill.berserker` | `whole` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/band--troll-slayer-special-skills-ferocious-charge/skill.ferocious-charge` | `whole` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/band--troll-slayer-special-skills-monster-slayer/skill.monster-slayer` | `whole` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/band--troll-slayer-special-skills-monster-slayer/skill.monster-slayer-effective-strength-armour` | `whole` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/shadowed--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/band--lahmian-special-skills-lost-innocence/skill.always-strikes-first` | `whole` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/band--lahmian-special-skills-vampire-reflexes/skill.vampire-reflexes` | `combines-with-step-aside-to-four` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/band--lahmian-special-skills-vampire-reflexes/skill.vampire-reflexes` | `six-plus-unmodifiable-save` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/band--no-pain/skill.ignore-pain` | `undead-class-no-pain` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/spirits--spiritual-weapons/trait.spiritual-weapons` | `whole` | — | consumer |
| `rule/trollheim/khemri-mages/mechanical-beast--mechanical-armour/trait.natural-armour-save` | `five-plus-armour-save` | — | consumer |
| `rule/trollheim/khemri-necromancers/band--necromantic-modification-putrid-stench/special-rule.band--necromantic-modification-putrid-stench` | `whole` | — | consumer |
| `rule/trollheim/khemri-necromancers/band--necromantic-modification-tremendous-strength/skill.iron-sinews` | `plus-one-strength` | — | consumer |
| `rule/trollheim/khemri-necromancers/band--no-pain/skill.ignore-pain` | `undead-class-no-pain` | — | consumer |
| `rule/trollheim/khemri-nomads-of-araby/band--hate-undead/unimplemented.khemri-nomads-of-araby.band.hate-undead` | `hatred` | — | consumer |
| `rule/trollheim/khemri-thieves-guild/guild-hashashiyyin--consummate-fighter/trait.perfect-killer` | `whole` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/band--no-pain/skill.ignore-pain` | `undead-class-no-pain` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/necrotect--hatred/skill.hatred` | `first-round-reroll` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/stone-golem--stone-body/trait.natural-armour-save` | `four-plus-armour-save` | — | consumer |
| `rule/trollheim/lustria-amazons/band--amazon-special-skills-animal-fury/unimplemented.lustria-amazons.band.amazon-special-skills-animal-fury` | `fear-immunity--scope--charge-attack` | — | consumer |
| `rule/trollheim/lustria-amazons/band--amazon-special-skills-lizard-hunter/mechanic.strike-first-vs-skinks-always` | `whole` | — | consumer |
| `rule/trollheim/lustria-amazons/band--isolationists/unimplemented.lustria-amazons.band.isolationists` | `hatred` | — | consumer |
| `rule/trollheim/lustria-clan-pestilens/band--clan-pestilens-special-skills-ignore-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/lustria-dark-elves/band--dark-elf-special-skills-elven-agility/skill.elven-agility` | `six-plus-avoidance` | — | consumer |
| `rule/trollheim/lustria-dark-elves/band--hatred-high-elves/unimplemented.lustria-dark-elves.band.hatred-high-elves` | `hatred` | — | consumer |
| `rule/trollheim/lustria-dark-elves/cold-ones--scaly-skin/trait.natural-armour-save` | `six-plus-armour-save` | — | consumer |
| `rule/trollheim/lustria-high-elves/band--high-elf-special-skills-elven-agility/skill.elven-agility` | `six-plus-avoidance` | — | consumer |
| `rule/trollheim/lustria-high-elves/band--high-elf-special-skills-infallible-strike/skill.sure-strike` | `whole` | — | consumer |
| `rule/trollheim/lustria-high-elves/band--high-elf-special-skills-miniath/skill.miniath` | `parry-with-any-weapon` | G02 | consumer |
| `rule/trollheim/lustria-high-elves/band--high-elf-special-skills-miniath/skill.miniath` | `reroll-with-a-parrying-weapon` | G02 | consumer |
| `rule/trollheim/lustria-lizardmen/band--lizardmen-special-skills-battle-roar/skill.bellowing-battle-roar` | `bellowing-battle-roar` | — | consumer |
| `rule/trollheim/lustria-lizardmen/band--lizardmen-special-skills-hardened-skin/skill.hard-to-kill` | `out-of-action-only-on-six` | — | consumer |
| `rule/trollheim/lustria-lizardmen/band--sacred-mark-huge-jaws/trait.huge-jaws` | `whole--scope--bite-strength` | — | consumer |
| `rule/trollheim/lustria-lizardmen/band--sacred-mark-of-the-old-ones/compiler.mark-of-the-old-ones` | `whole` | — | consumer |
| `rule/trollheim/lustria-lizardmen/kroxigor--scaly-skin-4plus/trait.natural-armour-save` | `four-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/kroxigor--scaly-skin-4plus/trait.natural-armour-save` | `strength-cannot-go-beyond-six` | — | consumer |
| `rule/trollheim/lustria-lizardmen/kroxigor--scaly-skin-4plus/trait.natural-armour-stacks` | `four-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/kroxigor--scaly-skin-4plus/trait.natural-armour-stacks` | `strength-cannot-go-beyond-six` | — | consumer |
| `rule/trollheim/lustria-lizardmen/kroxigor--scaly-skin-4plus/trait.natural-armour-worst-save` | `four-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/kroxigor--scaly-skin-4plus/trait.natural-armour-worst-save` | `strength-cannot-go-beyond-six` | — | consumer |
| `rule/trollheim/lustria-lizardmen/saurus-braves--scaly-skin-5plus/trait.natural-armour-save` | `five-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/saurus-braves--scaly-skin-5plus/trait.natural-armour-stacks` | `five-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/saurus-braves--scaly-skin-5plus/trait.natural-armour-worst-save` | `five-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/saurus-totem-warrior--scaly-skin-5plus/trait.natural-armour-save` | `five-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/saurus-totem-warrior--scaly-skin-5plus/trait.natural-armour-stacks` | `five-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/saurus-totem-warrior--scaly-skin-5plus/trait.natural-armour-worst-save` | `five-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/skink-braves--scaly-skin-6plus/trait.natural-armour-save` | `six-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/skink-braves--scaly-skin-6plus/trait.natural-armour-stacks` | `six-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/skink-braves--scaly-skin-6plus/trait.natural-armour-worst-save` | `six-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/skink-great-crests--scaly-skin-6plus/trait.natural-armour-save` | `six-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/skink-great-crests--scaly-skin-6plus/trait.natural-armour-stacks` | `six-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/skink-great-crests--scaly-skin-6plus/trait.natural-armour-worst-save` | `six-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/skink-priest--scaly-skin-6plus/trait.natural-armour-save` | `six-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/skink-priest--scaly-skin-6plus/trait.natural-armour-stacks` | `six-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-lizardmen/skink-priest--scaly-skin-6plus/trait.natural-armour-worst-save` | `six-plus-scaly-skin` | — | consumer |
| `rule/trollheim/lustria-norse/band--norse-special-skills-crushing-blow/skill.crushing-blow` | `whole` | — | consumer |
| `rule/trollheim/lustria-norse/band--norse-special-skills-northern-weapons/skill.weapons-of-the-north` | `whole` | — | consumer |
| `rule/trollheim/lustria-norse/band--norse-special-skills-shield-mastery/skill.shield-mastery` | `shield-parries-and-keeps-its-bonus` | G02 | consumer |
| `rule/trollheim/lustria-norse/wulfen--hardened-hide/trait.natural-armour-save` | `six-plus-armour-save` | — | consumer |
| `rule/trollheim/lustria-pygmies/silent-walker--ethereal/trait.ward-save` | `five-plus-ward-against-mundane` | — | consumer |
| `rule/trollheim/lustria-pygmies/silent-walker--ethereal/trait.ward-save` | `negated-by-magic` | — | consumer |
| `rule/trollheim/lustria-pygmies/silent-walker--ethereal/trait.ward-save-mundane-only` | `five-plus-ward-against-mundane` | — | consumer |
| `rule/trollheim/lustria-pygmies/silent-walker--ethereal/trait.ward-save-mundane-only` | `negated-by-magic` | — | consumer |
| `rule/trollheim/lustria-savage-goblins/zomblins--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/lustria-savage-goblins/zomblintua--blunt-attacks/weapon.mace` | `whole` | — | consumer |
| `rule/trollheim/lustria-savage-goblins/zomblintua--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/lustria-savage-goblins/zomblintua--regeneration/skill.regeneration-5-plus` | `five-plus-regeneration` | — | consumer |
| `rule/trollheim/lustria-tileans/band--miragliano-hatred-skaven/unimplemented.lustria-tileans.band.miragliano-hatred-skaven` | `hatred` | — | consumer |
| `rule/trollheim/lustria-tileans/duelists--cloak-and-dagger/trait.counts-as-shield` | `counts-as-shield` | — | consumer |
| `rule/trollheim/trollheim-cult-of-the-possessed/band--mutations-scorpion-tail/trait.scorpion-tail` | `whole--scope--scorpion-tail` | — | consumer |
| `rule/trollheim/trollheim-cult-of-the-possessed/band--mutations-tentacle/special-rule.band--mutations-tentacle` | `whole` | — | consumer |
| `rule/trollheim/trollheim-mercenaries/swordsmen--expert-swordsmen/skill.expert-swordsman` | `whole` | — | consumer |
| `rule/trollheim/trollheim-skaven-clan-eshin/assassin-adept--consummate-fighter/trait.perfect-killer` | `minus-one-to-enemy-armour` | — | consumer |
| `rule/trollheim/trollheim-skaven-clan-eshin/band--skaven-special-skills-art-of-silent-death/skill.art-of-silent-death` | `whole` | — | consumer |
| `rule/trollheim/trollheim-undead/dire-wolves--charge/trait.charge-attack-bonus` | `whole` | — | consumer |
| `rule/trollheim/trollheim-undead/dire-wolves--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/trollheim-undead/vampire--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/trollheim-undead/zombies--no-pain/skill.ignore-pain` | `stunned-becomes-knocked-down` | — | consumer |
| `rule/trollheim/trollheim-witch-hunters/witch-hunter-captain--burn-the-witch/unimplemented.trollheim-witch-hunters.witch-hunter-captain.burn-the-witch` | `burn-the-witch` | — | consumer |
| `rule/trollheim/trollheim-witch-hunters/witch-hunters--burn-the-witch/unimplemented.trollheim-witch-hunters.witch-hunters.burn-the-witch` | `burn-the-witch` | — | consumer |
| `source/bands/mordheim/call-of-the-night-haint-mim/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `whole` | — | consumer |
| `source/bands/mordheim/dark-elf-corsairs-mou/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `weapons-and-save` | — | consumer |
| `source/bands/mordheim/marauders-of-chaos/profiles.yaml/@/profiles/4/equipment_restrictions/0/unclassified` | `whole` | — | consumer |
| `source/bands/mordheim/order-of-the-mare-web/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `five-plus-unmodifiable-save` | — | consumer |
| `source/bands/mordheim/order-of-the-mare-web/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `negated-by-magical-attacks` | — | consumer |
| `source/bands/mordheim/order-of-the-mare-web/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `fights-with-hooves-without-penalty--scope--fights-with-hooves-without-penalty` | — | consumer |
| `source/bands/mordheim/order-of-the-mare-web/profiles.yaml/@/profiles/7/equipment_restrictions/0/unclassified` | `five-plus-unmodifiable-save-negated-by-magic` | — | consumer |
| `source/bands/mordheim/pirates-of-the-cathayan-sea-sar/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `unarmed-penalty` | — | consumer |
| `source/bands/mordheim/pirates-of-the-cathayan-sea-sar/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | consumer |
| `source/bands/mordheim/savage-orcs-kaz/equipment-access.yaml/@/equipment_lists/0/items/13/notes/unclassified` | `whole--scope--single-use` | — | consumer |
| `source/bands/mordheim/silent-brotherhood-sc/equipment-access.yaml/@/equipment_lists/0/items/12/notes/unclassified` | `cloak-counts-as-a-buckler` | G02 | consumer |
| `source/bands/mordheim/skaven-of-clan-pestilens-mou/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` | `whole` | — | consumer |
| `source/bands/mordheim/skaven-of-clan-pestilens-mou/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` | `whole` | — | consumer |
| `source/bands/mordheim/skaven-of-clan-pristekk-sc/equipment-access.yaml/@/equipment_lists/2/items/2/notes/unclassified` | `shock-weapon--scope--first-strike` | — | consumer |
| `source/bands/mordheim/skaven-of-clan-pristekk-sc/equipment-access.yaml/@/equipment_lists/2/items/2/notes/unclassified` | `shock-weapon--scope--shock-stun` | — | consumer |
| `source/bands/mordheim/skaven-of-clan-pristekk-sc/equipment-access.yaml/@/equipment_lists/2/items/2/notes/unclassified` | `shock-weapon--scope--two-handed` | — | consumer |
| `source/bands/mordheim/undead/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` | `whole` | — | consumer |
| `source/bands/mordheim/undead/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `no-unarmed-penalty` | — | consumer |
| `source/bands/trollheim/chaos-streets-arcane-society/equipment-access.yaml/@/equipment_lists/0/items/4/notes/unclassified` | `balanced-melee-staff` | — | consumer |
| `source/bands/trollheim/lustria-norse/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` | `whole` | — | consumer |
| `source/catalog/campaign/exploration-and-income.yaml/@/exploration/results/13/description/unclassified` | `blessed-weapon--scope--blessed-weapon` | — | consumer |
| `source/catalog/campaign/exploration-and-income.yaml/campaign.magical-artefact.all-seeing-eye-of-numas/unclassified` | `six-plus-additional-save` | — | consumer |
| `source/catalog/campaign/magic.yaml/@/lores/46/note/unclassified` | `trident-parries--scope--trident-parries` | G02 | consumer |
| `source/catalog/campaign/magic.yaml/@/lores/46/note/unclassified` | `trident-strikes-first-when-charged` | — | consumer |
| `source/catalog/campaign/mutations.yaml/campaign.mutation.great-claw/unclassified` | `whole` | — | consumer |
| `source/catalog/campaign/mutations.yaml/campaign.mutation.scorpion-tail/unclassified` | `extra-strength-five-poisoned-attack` | — | consumer |
| `source/catalog/campaign/serious-injuries.yaml/@/tables/0/results/14/note/unclassified` | `vengeful-hatred` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/core.yaml/hireling.dramatis.aenur.item.ienh-khain.rule.critical/unclassified` | `whole` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/core.yaml/hireling.dramatis.aenur.item.ienh-khain.rule.parry/unclassified` | `ienh-khain-parry` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/core.yaml/hireling.dramatis.aenur.item.ienh-khain.rule.strength/unclassified` | `whole` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/core.yaml/hireling.dramatis.aenur.rule.invincible-swordsman/unclassified` | `rule` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/core.yaml/hireling.dramatis.veskit.rule.integrated-warplock-pistols/unclassified` | `claw-strength-and-save-modifier` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/core.yaml/hireling.dramatis.veskit.rule.integrated-warplock-pistols/unclassified` | `extra-attack-already-in-profile` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/core.yaml/hireling.dramatis.veskit.rule.metallic-body/unclassified` | `metallic-body-three-plus-save` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1a.yaml/@/profiles/2/unresolved_references/0/unclassified` | `marquand-profile-reference` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1a.yaml/@/profiles/2/unresolved_references/1/unclassified` | `named-consequences` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1a.yaml/hireling.dramatis.countess-marianna-chevaux-vampire-assassin.rule.fighting-undead/unclassified` | `anti-undead` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/@/profiles/8/unresolved_references/1/unclassified` | `whole` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.dijin-katal-the-renegade-assassin.rule.kindred-hatred/unclassified` | `kindred-hatred` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.khar-mel-the-djinn.rule.ethereal/unclassified` | `ethereal-five-plus-unmodifiable-save` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.maximilian-the-mad.rule.fanatical/unclassified` | `automatic-leadership` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.maximilian-the-mad.rule.fanatical/unclassified` | `hates-listed-warbands` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.maximilian-the-mad.rule.strongman/unclassified` | `whole` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.penthesilea-mark-of-the-serpent.rule.amazon/unclassified` | `amazon-isolationists` | — | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.penthesilea-mark-of-the-serpent.rule.man-hater/unclassified` | `man-hater` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/hireling.dramatis.belandysh-condemned-champion-of-chen.rule.regeneration/unclassified` | `regeneration-four-plus-blocked-by-fire` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/hireling.dramatis.grand-master-ippan-shu.rule.bare-handed/unclassified` | `whole` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/hireling.dramatis.grand-master-ippan-shu.rule.iron-fan/unclassified` | `iron-fan` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2b.yaml/@/profiles/2/equipment/fixed_items/1/notes/unclassified` | `short-sword-resolves-to-the-sword-item` | G02 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2b.yaml/hireling.dramatis.aldred-fellblade.rule.righteous-fury-orcs-goblins/mechanic.hatred-orcs-goblins` | `hatred` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2b.yaml/hireling.dramatis.snorri-nosebiter.rule.drunk/mechanic.snorri-drunk` | `snorri-drunk--scope--drinking-table` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2b.yaml/hireling.dramatis.snorri-nosebiter.rule.lucky/mechanic.snorri-lucky` | `five-plus-ward-save` | — | consumer |
| `source/catalog/hirelings/hired-swords/core.yaml/hireling.hired-sword.dwarf-troll-slayer.rule.hard-head/unclassified` | `hard-head-ignores-mace-and-club-rules` | — | consumer |
| `source/catalog/hirelings/hired-swords/core.yaml/hireling.hired-sword.dwarf-troll-slayer.rule.hard-to-kill/unclassified` | `hard-to-kill-injury-chart` | — | consumer |
| `source/catalog/hirelings/hired-swords/core.yaml/hireling.hired-sword.dwarf-troll-slayer.skill.berserker/unclassified` | `whole` | — | consumer |
| `source/catalog/hirelings/hired-swords/core.yaml/hireling.hired-sword.dwarf-troll-slayer.skill.ferocious-charge/unclassified` | `whole` | — | consumer |
| `source/catalog/hirelings/hired-swords/core.yaml/hireling.hired-sword.dwarf-troll-slayer.skill.monster-slayer/unclassified` | `monster-slayer-wounds-on-four` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.dark-elf-assassin.rule.kindred-hatred/unclassified` | `kindred-hatred` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.duellist.rule.darting-steel/unclassified` | `parry-with-sword-and-buckler` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.dwarf-pathfinder.rule.hard-head/unclassified` | `hard-head-references-the-dwarf-rule` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.dwarf-pathfinder.rule.hard-to-kill/unclassified` | `hard-to-kill-references-the-dwarf-rule` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.dwarf-pathfinder.rule.hate-orcs-and-goblins/unclassified` | `hatred-orcs-goblins` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.dwarf-treasure-hunter.rule.hard-head/unclassified` | `hard-head-references-the-dwarf-rule` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.dwarf-treasure-hunter.rule.hard-to-kill/unclassified` | `hard-to-kill-references-the-dwarf-rule` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.dwarf-treasure-hunter.rule.hate-orcs-and-goblins/unclassified` | `hatred-orcs-goblins` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.gaoler.rule.hatred/unclassified` | `gaoler-hatred` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.shadow-warrior.rule.hate-dark-elves/unclassified` | `hatred-dark-elves` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.wolf-priest-of-ulric.rule.hatred/unclassified` | `intense-rivals` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.bone-goliath.rule.no-pain/unclassified` | `no-pain-converts-stunned-to-knocked-down` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.grave-robber.rule.hatred/unclassified` | `hatred-undead` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.swordsmith.rule.honing/unclassified` | `honing-blades` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.cursed-hillman.rule.thin-flesh/unclassified` | `minus-one-toughness-in-melee` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.dark-mage.rule.despise-despoilers/unclassified` | `despise-despoilers` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.emissary-of-chaos.rule.patron/unclassified` | `patron-khorne` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.emissary-of-chaos.rule.patron/unclassified` | `patron-nurgle-poison` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.emissary-of-chaos.rule.patron/unclassified` | `patron-slaanesh-charge-test` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.emissary-of-chaos.rule.patron/unclassified` | `patron-slaanesh-melee-penalty` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.halfling-knight.rule.slay-large-creature/unclassified` | `charge-large-creature-strength` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/12/equipment/choices/0/options/0/items/0/notes/unclassified` | `trident-parries` | G02 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/12/equipment/choices/0/options/0/items/0/notes/unclassified` | `trident-strikes-first-when-charged` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/19/equipment/fixed_items/1/notes/unclassified` | `white-wolf-pelt-distinct-from-the-middenheim-wolfcloak--scope--six-plus-saving-throw` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.bog-hunter.rule.unholy-stink/mechanic.unholy-stink` | `unholy-stink` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.norse-bearman-bodyguard.rule.bulwark/mechanic.norse-bulwark` | `plus-one-armour-in-close-combat-with-axe-and-shield` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.norse-bearman-bodyguard.rule.shieldmaster/mechanic.norse-shieldmaster` | `shield-parries-in-addition-to-its-save` | G02 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr.pending-duel` | `augur-one-roll-reroll` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.trickster-priest-of-ranald.rule.marks-of-ranald/hireling.hired-sword.trickster-priest-of-ranald.rule.marks-of-ranald.pending-duel` | `ducks-past-hits-on-six` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.trickster-priest-of-ranald.rule.marks-of-ranald/hireling.hired-sword.trickster-priest-of-ranald.rule.marks-of-ranald.pending-duel` | `ranald-s-luck-roll-influence` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.war-priestess-of-myrmidia.rule.marks-of-myrmidia/hireling.hired-sword.war-priestess-of-myrmidia.rule.marks-of-myrmidia.pending-duel` | `whole` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.rule.intense-rivals/mechanic.ulric-intense-rivals` | `hatred` | — | consumer |
| `source/catalog/rules/conditions.yaml/condition.hatred/skill.hatred` | `hatred` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.berserk-charge/unclassified` | `whole` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.burn-the-witch/unclassified` | `burn-the-witch` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.charge/unclassified` | `whole` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.crushing-blow/unclassified` | `no-enemy-may-parry` | G02 | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.eadbasher/unclassified` | `knocked-down-results-become-stunned` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.elven-agility/unclassified` | `six-plus-avoidance` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.free-the-slaves/unclassified` | `hate-slavers` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.hard-as-steel/unclassified` | `whole` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.hard-to-kill/unclassified` | `whole` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.hate-orcs-and-goblins/unclassified` | `hatred-orcs-goblins` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.natural-weapons/unclassified` | `whole` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.no-pain/unclassified` | `stunned-becomes-knocked-down` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.regeneration/unclassified` | `whole--scope--regen-and-fire` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.shield-master/unclassified` | `parry-with-a-shield` | G02 | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.shield-master/unclassified` | `six-plus-save` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.vomit-attack/unclassified` | `automatic-strength-five-hit-ignoring-armour-and-parry` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.weedy/unclassified` | `whole` | — | consumer |

## Claves de apoyo de otros responsables

| id | clause_id | Responsable principal | Referencia de asignación |
| --- | --- | --- | --- |
| `core/combat-critical-hits` | `critical-trigger` | G04 | consumer |
| `core/combat-injury-states` | `chart` | G04 | consumer |
| `core/combat-injury-states` | `highest-result` | G04 | consumer |
| `core/combat-order` | `charge-before-initiative` | G06 | consumer |
| `core/combat-order` | `stood-up-strikes-last` | G06 | consumer |
| `item/beastlash` | `whole` | G05 | consumer |
| `item/black_lotus` | `whole` | G04 | consumer |
| `item/bone_helmet` | `behaves-as-a-helmet` | G04 | consumer |
| `item/bone_helmet_skink_priest_only` | `behaves-as-a-helmet` | G04 | consumer |
| `item/cat_o_nine_tails` | `whole` | G06 | consumer |
| `item/chained_squig` | `whole` | G04 | consumer |
| `item/chainsaw_sword` | `whole` | G05 | consumer |
| `item/cooking_pot_helmet` | `five-plus-against-stun` | G04 | consumer |
| `item/crimson_shade` | `whole` | G06 | consumer |
| `item/cutlass_sword` | `whole` | G04 | consumer |
| `item/dark_elf_blade_weapon_upgrade` | `whole` | G04 | consumer |
| `item/darksteel_blade` | `whole` | G04 | consumer |
| `item/disease_dagger` | `whole` | G04 | consumer |
| `item/draich` | `whole` | G04 | consumer |
| `item/eshin_assassin_clothes` | `behaves-as-eshin-assassin-robes` | G04 | consumer |
| `item/helmet` | `four-plus-against-stun` | G04 | consumer |
| `item/kusara_kama` | `whole` | G04 | consumer |
| `item/nightshade` | `whole` | G04 | consumer |
| `item/pistol_brace` | `whole` | G04 | consumer |
| `item/rapier` | `whole` | G04 | consumer |
| `item/serpent_staff` | `whole` | G06 | consumer |
| `item/spirit_knife` | `whole--scope--profile` | G04 | consumer |
| `item/spirit_knife` | `whole--scope--spectral-touch` | G04 | consumer |
| `item/steel_whip` | `whole` | G06 | consumer |
| `item/wolf_pelt_cloak` | `six-plus-saving-throw` | G04 | consumer |
| `mechanic/armour.eshin-assassin-robes` | `light-armour-six-plus-no-combining` | G04 | consumer |
| `mechanic/dance.storm-of-blades` | `whole` | G06 | consumer |
| `mechanic/dance.the-shadows-coil` | `whole` | G06 | consumer |
| `mechanic/dance.whirling-death` | `whole` | G06 | consumer |
| `mechanic/dance.woven-mist` | `whole` | G06 | consumer |
| `mechanic/defence.cooking-pot-helmet` | `five-plus-against-stun` | G04 | consumer |
| `mechanic/defence.helmet` | `four-plus-against-stun` | G04 | consumer |
| `mechanic/defence.wolf-pelt-cloak` | `six-plus-saving-throw` | G04 | consumer |
| `mechanic/material.dark-elf-blade` | `whole` | G04 | consumer |
| `mechanic/mechanic.anvil-head` | `whole--scope--special-attack` | G06 | consumer |
| `mechanic/mechanic.body-slam` | `whole` | G04 | consumer |
| `mechanic/mechanic.bull-charge` | `whole` | G04 | consumer |
| `mechanic/mechanic.ethereal-hit-save` | `four-plus-save-after-the-to-hit-roll` | G04 | consumer |
| `mechanic/mechanic.ethereal-hit-save` | `magical-attacks-bypass` | G04 | consumer |
| `mechanic/mechanic.killing-blow` | `whole` | G04 | consumer |
| `mechanic/mechanic.savage-fury` | `whole` | G06 | consumer |
| `mechanic/mechanic.seaguard-spear-master` | `first-round-strength-and-reroll` | G04 | consumer |
| `mechanic/mechanic.spawn-special-attacks` | `whole` | G06 | consumer |
| `mechanic/mechanic.spider-infested` | `whole` | G04 | consumer |
| `mechanic/mechanic.unpredictable-attack` | `whole` | G04 | consumer |
| `mechanic/mechanic.wraith-touch` | `whole` | G06 | consumer |
| `mechanic/poison.black-lotus` | `whole` | G04 | consumer |
| `mechanic/poison.manbane` | `whole` | G04 | consumer |
| `mechanic/poison.nightshade` | `whole` | G04 | consumer |
| `mechanic/poison.spider-spittle` | `whole` | G06 | consumer |
| `mechanic/poison.wolfsbane` | `whole` | G04 | consumer |
| `mechanic/preparation.crimson-shade` | `whole` | G06 | consumer |
| `mechanic/preparation.tears-of-shallaya` | `immunity-to-all-poisons` | G04 | consumer |
| `mechanic/skill.art-of-silent-death` | `critical-5-6` | G04 | consumer |
| `mechanic/skill.blessed-sight` | `whole` | G06 | consumer |
| `mechanic/skill.crack-shot` | `whole` | G04 | consumer |
| `mechanic/skill.knife-fighting` | `knife-fighting-bonus` | G04 | consumer |
| `mechanic/skill.shifty` | `whole` | G06 | consumer |
| `mechanic/skill.strike-to-injure` | `whole` | G04 | consumer |
| `mechanic/skill.sweep` | `whole` | G06 | consumer |
| `mechanic/skill.thick-skull` | `helmet-improves-to-two-and-replaces` | G04 | consumer |
| `mechanic/skill.thick-skull` | `stun-to-knocked-down-on-three` | G04 | consumer |
| `mechanic/weapon.arcane-candelabrum` | `whole` | G04 | consumer |
| `mechanic/weapon.boar-spear` | `whole--scope--charging-enemy-loses-one-attack` | G06 | consumer |
| `mechanic/weapon.boar-spear` | `whole--scope--strikes-first` | G06 | consumer |
| `mechanic/weapon.brazier-iron` | `whole` | G04 | consumer |
| `mechanic/weapon.chained-squig` | `whole` | G04 | consumer |
| `mechanic/weapon.chainsaw-sword` | `whole` | G05 | consumer |
| `mechanic/weapon.cutlass` | `whole` | G04 | consumer |
| `mechanic/weapon.disease-dagger` | `whole` | G04 | consumer |
| `mechanic/weapon.duelling-pistol` | `whole` | G04 | consumer |
| `mechanic/weapon.kusara-kama` | `whole` | G04 | consumer |
| `mechanic/weapon.long-daggers` | `whole` | G06 | consumer |
| `mechanic/weapon.misericordia` | `whole` | G04 | consumer |
| `mechanic/weapon.pirate-scourge` | `whole` | G06 | consumer |
| `mechanic/weapon.pistol` | `whole` | G04 | consumer |
| `mechanic/weapon.serpent-staff` | `whole` | G06 | consumer |
| `mechanic/weapon.serpent-whip` | `whole` | G06 | consumer |
| `mechanic/weapon.skull-busta` | `whole` | G04 | consumer |
| `mechanic/weapon.spirit-knife` | `whole` | G04 | consumer |
| `mechanic/weapon.steel-whip` | `whole` | G06 | consumer |
| `mechanic/weapon.sword-breaker` | `whole` | G04 | consumer |
| `mechanic/weapon.vomit-attack` | `whole` | G06 | consumer |
| `rule/catalog/warband/skill.chosen-of-the-white-tower/unclassified` | `parry-unarmed-and-reroll` | G04 | encargo explícito; consumer vacío |
| `rule/catalog/warband/skill.head-crusher/skill.head-crusher` | `whole` | G06 | consumer |
| `rule/catalog/warband/skill.instinctive-warrior/unclassified` | `parry-with-a-double-handed-weapon` | G04 | encargo explícito; consumer vacío |
| `rule/catalog/warband/skill.knife-fighting/skill.knife-fighting` | `knife-fighting-bonus` | G04 | consumer |
| `rule/catalog/warband/skill.sweep/skill.sweep` | `whole` | G06 | consumer |
| `rule/catalog/warband/skill.thick-skull/skill.thick-skull` | `helmet-improves-to-two-and-replaces` | G04 | consumer |
| `rule/catalog/warband/skill.thick-skull/skill.thick-skull` | `stun-to-knocked-down-on-three` | G04 | consumer |
| `rule/mordheim/adventurers-kaz/barbarian--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/adventurers-kaz/dwarf--hard-head/trait.concussion-immune` | `stub` | G04 | consumer |
| `rule/mordheim/adventurers-kaz/dwarf--hard-to-kill/skill.hard-to-kill` | `stub` | G04 | consumer |
| `rule/mordheim/amazons-lustria/band--amazon-special-skills-savage-fury/mechanic.savage-fury` | `whole` | G06 | consumer |
| `rule/mordheim/amazons-mordheim/totem-warriors--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/black-dwarfs/band--chaos-dwarf-special-skills-thick-skull/skill.thick-skull` | `helmet-improves-to-two` | G04 | consumer |
| `rule/mordheim/black-dwarfs/band--chaos-dwarf-special-skills-thick-skull/skill.thick-skull` | `thick-skull-save` | G04 | consumer |
| `rule/mordheim/black-orcs/band--black-orc-special-skills-ard-ead/skill.thick-skull` | `whole` | G04 | consumer |
| `rule/mordheim/black-orcs/band--black-orc-special-skills-eadbasher/skill.head-crusher` | `whole` | G06 | consumer |
| `rule/mordheim/black-orcs/troll--vomit-attack/weapon.vomit-attack` | `whole` | G06 | consumer |
| `rule/mordheim/blood-dragons-mou/grave-guards--immune-to-poisons/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/blood-dragons-mou/grave-guards--killing-blow/mechanic.killing-blow` | `whole` | G04 | consumer |
| `rule/mordheim/blood-dragons-mou/hell-hounds--immune-to-poisons/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/blood-dragons-mou/skeleton-warriors--immune-to-poisons/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/blood-dragons-mou/vampire--immune-to-poisons/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/blood-dragons-mou/wights--immune-to-poisons/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/blood-dragons-mou/wights--killing-blow/mechanic.killing-blow` | `whole` | G04 | consumer |
| `rule/mordheim/bretonnian-chapel-guard/battle-pilgrims--holy-relics/unimplemented.bretonnian-chapel-guard.battle-pilgrims.holy-relics` | `holy-relic-frenzy` | G05 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/cairn-wraith--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | G04 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/cairn-wraith--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/malignant-spirits--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | G04 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/malignant-spirits--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/mourngul--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | G04 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/mourngul--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/poltergeists--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | G04 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/poltergeists--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/revenants--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/spirit-hosts--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | G04 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/spirit-hosts--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/tomb-banshee--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | G04 | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/tomb-banshee--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/carnival-of-chaos/band--blessings-of-nurgle-nurgles-rot/trait.poison-immune` | `poison-immunity` | G04 | consumer |
| `rule/mordheim/carnival-of-chaos/nurglings--immune-to-poison/trait.poison-immune` | `poison-immunity` | G04 | consumer |
| `rule/mordheim/carnival-of-chaos/plague-bearers--immune-to-poison/trait.poison-immune` | `poison-immunity` | G04 | consumer |
| `rule/mordheim/clan-angrund-kep/band--dwarf-special-skills-thick-skull/skill.thick-skull` | `whole` | G04 | consumer |
| `rule/mordheim/clockworkers-sc/band--constructs/unimplemented.clockworkers-sc.band.constructs` | `constructs-ignore-pain` | G04 | encargo explícito; consumer vacío |
| `rule/mordheim/clockworkers-sc/band--constructs/unimplemented.clockworkers-sc.band.constructs` | `constructs-poison-immunity` | G04 | encargo explícito; consumer vacío |
| `rule/mordheim/clockworkers-sc/band--constructs/unimplemented.clockworkers-sc.band.constructs` | `constructs-psychology-immunity` | G05 | consumer |
| `rule/mordheim/crooked-moon-kep/troll--vomit-attack/weapon.vomit-attack` | `whole` | G04 | consumer |
| `rule/mordheim/druchii-mic/witch-elves--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/dwarf-rangers/band--dwarf-special-skills-thick-skull/skill.thick-skull` | `whole` | G04 | consumer |
| `rule/mordheim/dwarf-treasure-hunters/band--dwarf-special-skills-thick-skull/skill.thick-skull` | `whole` | G04 | consumer |
| `rule/mordheim/fallen-the-rel/revenant--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/fen-guard-mim/band--immune-to-drugs-and-poison/trait.poison-immune` | `immune-to-drugs-and-poison` | G04 | consumer |
| `rule/mordheim/ghost-pirates-sar/ghost-captain--undead/unimplemented.ghost-pirates-sar.ghost-captain.undead` | `undead-psychology-immunity` | G05 | consumer |
| `rule/mordheim/ghost-pirates-sar/gibbets--iron-cage/profile.equipment-restrictions` | `intrinsic-save` | G04 | consumer |
| `rule/mordheim/ghost-pirates-sar/gibbets--undead/unimplemented.ghost-pirates-sar.gibbets.undead` | `undead-psychology-immunity` | G05 | consumer |
| `rule/mordheim/ghost-pirates-sar/screaming-ghosts--undead/unimplemented.ghost-pirates-sar.screaming-ghosts.undead` | `undead-psychology-immunity` | G05 | consumer |
| `rule/mordheim/ghost-pirates-sar/skeleton-mates--undead/unimplemented.ghost-pirates-sar.skeleton-mates.undead` | `undead-psychology-immunity` | G05 | consumer |
| `rule/mordheim/ghost-pirates-sar/the-bloated--undead/unimplemented.ghost-pirates-sar.the-bloated.undead` | `undead-psychology-immunity` | G05 | consumer |
| `rule/mordheim/grave-robbers-sylv/band--special-skill-hardy-constitution/trait.poison-immune` | `immune-to-disease-and-poison` | G04 | consumer |
| `rule/mordheim/halflings-mic/halfling-elder--shifty/skill.shifty` | `bonus-first-strike-when-charged` | G04 | consumer |
| `rule/mordheim/khorne-raiders-sar/cannibal-boys--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/lothern-sea-patrol-sar/seaguards--spear-master/mechanic.seaguard-spear-master` | `first-round-strength-and-reroll` | G04 | consumer |
| `rule/mordheim/lustrian-reavers/conqueror--survivor/trait.survivor` | `cannot-be-out-while-standing` | G04 | consumer |
| `rule/mordheim/maneaters/band--ogres-special-skills-bull-charge/mechanic.bull-charge` | `whole` | G04 | consumer |
| `rule/mordheim/maneaters/bulls--bull-charge/mechanic.bull-charge` | `whole` | G04 | consumer |
| `rule/mordheim/marauders-of-chaos/spawn-of-chaos--special-attacks/mechanic.spawn-special-attacks` | `whole` | G06 | consumer |
| `rule/mordheim/masters-of-horror-sylv/flesh-construct--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/mordheim/masters-of-horror-sylv/thrall--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/mordheim/masters-of-horror-sylv/zombies--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/abomination--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/necrarch-vampire--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/skeletal-warrior--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/thrall--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/zombie--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/night-goblins-kaz/troll--vomit-attack/weapon.vomit-attack` | `whole` | G04 | consumer |
| `rule/mordheim/night-goblins-mic/troll--vomit-attack/weapon.vomit-attack` | `whole` | G04 | consumer |
| `rule/mordheim/night-goblins-web/troll--vomit-attack/weapon.vomit-attack` | `whole` | G04 | consumer |
| `rule/mordheim/nipponese-expedition-web/ashigaru--wall-of-steel/unimplemented.nipponese-expedition-web.ashigaru.wall-of-steel` | `two-handed-spear-gains-parry` | G04 | encargo explícito; consumer vacío |
| `rule/mordheim/norse-explorers-btb/beserkers--berserkers/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/norse-explorers-lustria/beserkers--berserkers/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/ogre-hunting-party-web/ogre-hunter--dont-fight-with-eating-knives/unimplemented.ogre-hunting-party-web.ogre-hunter.dont-fight-with-eating-knives` | `unarmed-fighting-without-penalty` | G06 | consumer |
| `rule/mordheim/orc-mob/band--orc-special-skills-ard-ead/skill.thick-skull` | `whole` | G04 | consumer |
| `rule/mordheim/orc-mob/band--orc-special-skills-eadbasher/skill.head-crusher` | `whole` | G06 | consumer |
| `rule/mordheim/orc-mob/troll--vomit-attack/weapon.vomit-attack` | `whole` | G04 | consumer |
| `rule/mordheim/ostlanders/band--ostlander-special-skills-bull-rush/mechanic.bull-charge` | `whole` | G04 | consumer |
| `rule/mordheim/pit-fighters/band--pit-fighter-skill-body-slam/mechanic.body-slam` | `whole` | G04 | consumer |
| `rule/mordheim/restless-dead/band--restless-dead-special-skills-wraith-touch/mechanic.wraith-touch` | `whole` | G06 | consumer |
| `rule/mordheim/restless-dead/grave-guards--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/restless-dead/grave-guards--wight-blades/trait.wight-blades` | `whole` | G04 | consumer |
| `rule/mordheim/restless-dead/liche--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/restless-dead/scarecrows--construct/trait.injury-reroll-out` | `reroll-injury` | G04 | consumer |
| `rule/mordheim/restless-dead/scarecrows--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/restless-dead/skeletons--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/restless-dead/wights--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/restless-dead/zombies--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/sea-ghosts-mim/band--dance-storm-of-blades/dance.storm-of-blades` | `whole` | G06 | consumer |
| `rule/mordheim/sisters-of-sigmar/augur--blessed-sight/skill.blessed-sight` | `whole` | G06 | consumer |
| `rule/mordheim/skaven-clan-eshin/band--skaven-special-skills-black-hunger/mechanic.black-hunger` | `attack-and-backlash` | G06 | consumer |
| `rule/mordheim/skaven-clan-pestilens/band--clan-pestilens-special-skills-black-hunger/mechanic.black-hunger` | `attack-and-backlash` | G06 | consumer |
| `rule/mordheim/skaven-clan-pestilens/band--clan-pestilens-special-skills-rotten-body/trait.poison-immune` | `poison-immunity` | G04 | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-champion--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-priest--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-rat--plague-infested/poison.black-lotus` | `whole` | G04 | consumer |
| `rule/mordheim/snotlings-web/wheelo--combat/mechanic.wheelo-impact` | `whole` | G06 | consumer |
| `rule/mordheim/sons-of-hashut/band--chaos-dwarfs-special-skills-thick-skull/skill.thick-skull` | `helmet-improves-to-two-and-replaces` | G04 | consumer |
| `rule/mordheim/sons-of-hashut/band--chaos-dwarfs-special-skills-thick-skull/skill.thick-skull` | `stun-to-knocked-down-on-three` | G04 | consumer |
| `rule/mordheim/strigoi-kaz/fell-bats--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/mordheim/strigoi-kaz/skeletons--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/mordheim/survivors-of-strigos-sylv/strigoi-vampire--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/mordheim/tomb-guardians/acolytes--undead/unimplemented.tomb-guardians.acolytes.undead` | `undead` | G04 | encargo explícito; consumer vacío |
| `rule/mordheim/tomb-guardians/band--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/mordheim/tomb-guardians/tomb-scorpions--scorpion-sting/poison.black-lotus` | `whole` | G04 | consumer |
| `rule/mordheim/undead/dire-wolves--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/undead/vampire--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/undead/zombies--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/mordheim/underworld-alliance-mim/goblin-stinky-gits--disgusting/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/mordheim/underworld-alliance-mim/warpstone-troll--vomit-attack/weapon.vomit-attack` | `whole` | G04 | consumer |
| `rule/mordheim/watchmen-mim/private-sleuth--scryer/trait.re-roll-melee` | `melee-reroll` | G06 | consumer |
| `rule/mordheim/watchmen-mim/turnkeys--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/band--dwarf-special-skills-thick-skull/skill.thick-skull` | `whole` | G04 | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/dwarf-troll-slayers--death-oath/unimplemented.chaos-streets-dwarf-treasure-hunters.dwarf-troll-slayers.death-oath` | `psychology-immunity` | G05 | consumer |
| `rule/trollheim/chaos-streets-greenskins/band--orc-special-skills-ard-ead/skill.thick-skull` | `whole` | G04 | consumer |
| `rule/trollheim/chaos-streets-greenskins/band--orc-special-skills-eadbasher/skill.head-crusher` | `whole` | G06 | consumer |
| `rule/trollheim/chaos-streets-greenskins/troll--troll-vomit/weapon.vomit-attack` | `whole` | G04 | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/lunatics--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/band--pit-fighter-skill-body-slam/mechanic.body-slam` | `whole` | G04 | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/dwarf-troll-slayer--death-oath/unimplemented.chaos-streets-pit-fighters.dwarf-troll-slayer.death-oath` | `psychology-immunity` | G05 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/blood-dragon-vampire--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/dire-wolf--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/lahmia-vampire--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/necrarch-vampire--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/strigoi-vampire--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/vampire-bat--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/von-carstein-vampire--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/zombie--immune-to-poison/trait.poison-immune` | `whole` | G04 | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/shadowed--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/troll-slayer--death-oath/unimplemented.khemri-cursed-of-karak-zorn.troll-slayer.death-oath` | `psychology-immunity` | G05 | consumer |
| `rule/trollheim/khemri-hobgoblin-raiders/band--hobgoblin-special-skills-unpredictable/mechanic.unpredictable-attack` | `whole` | G04 | consumer |
| `rule/trollheim/khemri-hobgoblin-raiders/sneaky--unpredictable/mechanic.unpredictable-attack` | `whole` | G04 | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/band--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/band--lahmian-special-skills-hypnotize/unimplemented.khemri-lahmian-brotherhood.band.lahmian-special-skills-hypnotize` | `hypnotize` | G06 | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/beloved--devoted-to-the-vampire/unimplemented.khemri-lahmian-brotherhood.beloved.devoted-to-the-vampire` | `devoted-frenzy--scope--hatred-against-killer` | G06 | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/lackeys--devoted-to-the-vampire/unimplemented.khemri-lahmian-brotherhood.lackeys.devoted-to-the-vampire` | `devoted-frenzy--scope--hatred-against-killer` | G06 | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/skeleton-warriors--undead/unimplemented.khemri-lahmian-brotherhood.skeleton-warriors.undead` | `undead` | G04 | encargo explícito; consumer vacío |
| `rule/trollheim/khemri-mages/mechanical-beast--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/trollheim/khemri-necromancers/band--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/trollheim/khemri-necromancers/band--necromantic-modification-anvil-head/compiler.anvil-head` | `whole--scope--special-attack` | G06 | consumer |
| `rule/trollheim/khemri-necromancers/skeleton-warriors--undead/unimplemented.khemri-necromancers.skeleton-warriors.undead` | `undead` | G04 | encargo explícito; consumer vacío |
| `rule/trollheim/khemri-thieves-guild/band--guild-special-skills-knife-fighting/skill.knife-fighting` | `knife-fighting-bonus` | G04 | consumer |
| `rule/trollheim/khemri-tomb-guardians/band--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/trollheim/khemri-tomb-guardians/stone-golem--animated/unimplemented.khemri-tomb-guardians.stone-golem.animated` | `animated` | G04 | encargo explícito; consumer vacío |
| `rule/trollheim/khemri-tomb-guardians/stone-golem--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/trollheim/khemri-tomb-guardians/tomb-scorpions--scorpion-sting/poison.black-lotus` | `whole` | G04 | consumer |
| `rule/trollheim/lustria-amazons/amazon-totem-warriors--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/trollheim/lustria-clan-pestilens/band--clan-pestilens-special-skills-black-hunger/mechanic.black-hunger` | `attack-and-backlash` | G06 | consumer |
| `rule/trollheim/lustria-clan-pestilens/band--clan-pestilens-special-skills-rotten-body/trait.poison-immune` | `immune-to-poison-and-disease` | G04 | consumer |
| `rule/trollheim/lustria-lizardmen/band--cold-blooded/unimplemented.lustria-lizardmen.band.cold-blooded` | `cold-blooded--scope--psychology-test` | G05 | consumer |
| `rule/trollheim/lustria-norse/berserkers--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/trollheim/lustria-pygmies/cannibals--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/trollheim/lustria-savage-goblins/band--savage-goblin-special-skills-spider-infested/mechanic.spider-infested` | `whole` | G04 | consumer |
| `rule/trollheim/lustria-savage-goblins/band--savage-goblin-special-skills-unpredictable/mechanic.unpredictable-attack` | `whole` | G04 | consumer |
| `rule/trollheim/lustria-savage-goblins/red-teeth--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/trollheim/lustria-savage-goblins/zomblins--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/trollheim/lustria-savage-goblins/zomblintua--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/trollheim/trollheim-skaven-clan-eshin/band--skaven-special-skills-black-hunger/mechanic.black-hunger` | `attack-and-backlash` | G06 | consumer |
| `rule/trollheim/trollheim-undead/dire-wolves--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/trollheim/trollheim-undead/vampire--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `rule/trollheim/trollheim-undead/zombies--immune-to-poison/trait.poison-immune` | `immune-to-poison` | G04 | consumer |
| `source/bands/mordheim/crooked-moon-kep/equipment-access.yaml/@/equipment_lists/1/items/0/notes/unclassified` | `whole` | G04 | consumer |
| `source/bands/mordheim/dark-elf-corsairs-mou/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `frenzy` | G05 | encargo explícito; consumer vacío |
| `source/bands/mordheim/militiant-mootlanders-mim/equipment-access.yaml/@/equipment_lists/0/items/16/notes/unclassified` | `cooking-pot-counts-as-a-helmet` | G04 | consumer |
| `source/bands/mordheim/militiant-mootlanders-mim/equipment-access.yaml/@/equipment_lists/1/items/9/notes/unclassified` | `cooking-pot-counts-as-a-helmet` | G04 | consumer |
| `source/bands/mordheim/skaven-of-clan-pristekk-sc/equipment-access.yaml/@/equipment_lists/2/items/0/notes/unclassified` | `weapon-note--scope--plus-one-enemy-armour-save` | G04 | encargo explícito; consumer vacío |
| `source/bands/mordheim/skaven-of-clan-pristekk-sc/equipment-access.yaml/@/equipment_lists/2/items/0/notes/unclassified` | `weapon-note--scope--whipcrack` | G06 | encargo explícito; consumer vacío |
| `source/catalog/campaign/exploration-and-income.yaml/campaign.magical-artefact.count-of-ventimiglias-misericordia/unclassified` | `misericordia-injury` | G04 | consumer |
| `source/catalog/campaign/magic.yaml/spell.commands.art-thou-ready-to-die-fighting/unclassified` | `whole` | G06 | consumer |
| `source/catalog/campaign/magic.yaml/spell.commands.follow-me-mine-pugnacious-ones/unclassified` | `whole` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/core.yaml/hireling.dramatis.veskit.rule.no-pain/unclassified` | `remains-until-last-wound` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1a.yaml/hireling.dramatis.countess-marianna-chevaux-vampire-assassin.rule.immune-to-poison/unclassified` | `immune-to-poison` | G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1a.yaml/hireling.dramatis.countess-marianna-chevaux-vampire-assassin.rule.no-pain/unclassified` | `ignores-knocked-down-and-stunned` | G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.abdul-alhazred-the-mad-sorcerer.rule.eye-pendant/unclassified` | `eye-pendant` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.drenok-johansen-wielder-of-the-great-axe.rule.sabertooth-tiger-hide/unclassified` | `sabertooth-tiger-hide--scope--close-combat-save` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.khar-mel-the-djinn.rule.djinn-s-curse/unclassified` | `djinns-curse` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.khar-mel-the-djinn.rule.djinn-s-luck/unclassified` | `djinn-s-luck-ward-save` | G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.maximilian-the-mad.rule.fear/unclassified` | `cause-fear` | G05 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.maximilian-the-mad.rule.religious-fervour/unclassified` | `frenzy` | G05 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/@/profiles/4/unresolved_references/0/unclassified` | `item` | G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.sigmund-spindle-the-harvester-of-flesh.rule.immune-to-poison/unclassified` | `immune-to-poison` | G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.sigmund-spindle-the-harvester-of-flesh.rule.no-pain/unclassified` | `ignores-knocked-down-and-stunned` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.sigmund-spindle-the-harvester-of-flesh.rule.no-pain/unclassified` | `remains-until-last-wound` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-dark-jester-in-mordheim.rule.babbling-banter/unclassified` | `whole` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-dark-jester-in-mordheim.rule.sidestepper/unclassified` | `rule` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-foole.rule.poison-ring/unclassified` | `whole` | G04 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-foole.rule.unhinged/unclassified` | `psychology-immunity` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-headless-horseman.rule.undead/unclassified` | `undead` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-1a.yaml/hireling.hired-sword.beast-hunter.rule.beastmen-vengeance/unclassified` | `beastmen-vengeance` | G05 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-1a.yaml/hireling.hired-sword.imperial-assassin.rule.backstabber/unclassified` | `unseen-charge-bonus` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.clan-skryre-rat-ogre.rule.immune-to-poison/unclassified` | `immune-to-poison` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.gaoler.rule.inured-to-pain/unclassified` | `inured-to-pain-injury-modifier` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.snake-charmer.rule.immune-to-poison/unclassified` | `immune-to-poison` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.tomb-robber.rule.excellent-reflexes/unclassified` | `excellent-reflexes-reference` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.witch-hunter.rule.burn-the-witch/unclassified` | `burn-the-witch` | G05 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.bone-goliath.rule.immune-to-poison/unclassified` | `immune-to-poison` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.hobgoblin-scout.rule.traitor/unclassified` | `traitor-hatred` | G05 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.chaos-fury.rule.daemonic-flesh/unclassified` | `daemonic-five-plus-save` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.chaos-fury.rule.daemonic-flesh/unclassified` | `magic-and-blessed-exceptions` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.chaos-fury.rule.daemonic-mind/unclassified` | `psychology-immunity` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.dwarf-slayer-pirate.rule.slayer-pirate/unclassified` | `deathwish--scope--deathwish-psychology` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.dwarf-slayer-pirate.rule.slayer-pirate/unclassified` | `hard-head` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.dwarf-slayer-pirate.rule.slayer-pirate/unclassified` | `hard-to-kill` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.emissary-of-chaos.rule.patron/unclassified` | `patron-nurgle-fear` | G05 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.estalian-diestro.rule.rapier/unclassified` | `rapier-barrage` | G06 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr.pending-duel` | `augur-psychology-immunity` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.rule.strictures/defence.wolf-pelt-cloak` | `six-plus-saving-throw` | G04 | consumer |
| `source/catalog/rules/conditions.yaml/campaign.condition.frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.berserkers/unclassified` | `frenzy` | G05 | encargo explícito; consumer vacío |
| `source/catalog/rules/special-rules.yaml/shared-rule.censer-bearer/unclassified` | `frenzy` | G05 | encargo explícito; consumer vacío |
| `source/catalog/rules/special-rules.yaml/shared-rule.immune-to-poison-3/unclassified` | `poison-immunity` | G04 | encargo explícito; consumer vacío |
| `source/catalog/rules/special-rules.yaml/shared-rule.immune-to-poison/unclassified` | `whole` | G04 | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.no-pain-4/unclassified` | `ignore-pain` | G04 | encargo explícito; consumer vacío |
| `source/catalog/rules/special-rules.yaml/shared-rule.thick-skull/unclassified` | `whole` | G04 | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.undead/unclassified` | `undead` | G04 | encargo explícito; consumer vacío |

## Base de esta asignación

Preparación: 2026-10-21. HEAD: `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` más cambios locales actuales. CSV SHA-256: `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`. No es un certificado de ejecución.
