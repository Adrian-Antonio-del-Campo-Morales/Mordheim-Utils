# G05 — Psicología y liderazgo local vectorizados

## Prompt para lanzar el agente

Copia el bloque completo al lanzar el agente. Las condiciones de inicio forman parte del encargo; este prompt no autoriza saltarse sus dependencias.

```text
Realiza el encargo G05 (fase 1: implementación) del motor vectorial NumPy.

INFORMACIÓN QUE DEBES LEER
1. El fichero de trabajo completo:
   D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK\TMP_VECTORIAL_ENGINE_2A2B\G05_PSICOLOGIA_Y_LIDERAZGO_LOCAL.md
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
Etapa C, tras G00 y G02. Paralelo con G03/G04; no escribir en el driver mientras se prepara la tanda.
Comprueba la entrega de esas dependencias. Si falta alguna, comunica la dependencia concreta;
puedes avanzar con lectura o trabajo independiente, pero no inventes interfaces ni declares
completada una conexión que todavía no existe.

OBJETIVO CONCRETO
Implementar psicología y liderazgo local por lotes siguiendo modular/psychology.py y modular/leadership.py. Usa el contexto local suministrado y el estado de G02. Conserva Fear, Stupidity, Frenzy, inmunidades, excepciones, proveedores de Leadership, repeticiones y sus recursos. Las consecuencias deben afectar a las filas correspondientes. Entrega a G06 los helpers implementados y su momento exacto de llamada; no amplíes a psicología de grupo.

REFERENCIAS Y COMPROBACIONES QUE DEBES REUTILIZAR
Usa resolve_fear, resolve_stupidity, causes_fear y resolve_local_leadership como referencia. Los módulos vectoriales autorizados _psychology.py/_leadership.py permiten trabajar sin competir por el driver. Reutiliza casos aceptados; añade solo un escenario vectorial representativo si no existe comprobación aplicable.

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
TMP_VECTORIAL_ENGINE_2A2B/G05-deliverable.md
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

**Inicio:** Etapa C, tras G00 y G02. Paralelo con G03/G04; no escribir en el driver mientras se prepara la tanda.

**Cláusulas principales:** 637. **Cláusulas de apoyo:** 42.

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

Crea o actualiza `TMP_VECTORIAL_ENGINE_2A2B/G05-deliverable.md` en la raíz de tu copia de trabajo. Es la entrega persistente obligatoria de este grupo y está permitida además de los archivos de producción autorizados. No basta con un mensaje en el chat.

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

- `TMP_VECTORIAL_ENGINE_2A2B/G05-deliverable.md` — documento de entrega obligatorio, propietario exclusivo G05.
- `packages/python/combat-engine/mordheim_combat/vectorized/_psychology.py (nuevo, propietario exclusivo)`
- `packages/python/combat-engine/mordheim_combat/vectorized/_leadership.py (nuevo, propietario exclusivo)`
- `tests/python/combat/vectorized/test_psychology_vectorized.py (solo si se necesita un comprobante nuevo)`

Cualquier archivo no enumerado queda fuera de tu propiedad. Los módulos nuevos expresamente permitidos solo se crean si el portado los necesita. Los tests compartidos que no son tuyos se pueden ejecutar, pero no editar.

## Implementación de referencia que debes seguir

- `packages/python/combat-engine/mordheim_combat/modular/psychology.py::resolve_stupidity`
- `packages/python/combat-engine/mordheim_combat/modular/psychology.py::resolve_fear`
- `packages/python/combat-engine/mordheim_combat/modular/psychology.py::causes_fear`
- `packages/python/combat-engine/mordheim_combat/modular/psychology.py::fears_opponent_fire`
- `packages/python/combat-engine/mordheim_combat/modular/leadership.py::resolve_local_leadership`
- `packages/python/combat-engine/mordheim_combat/modular/leadership.py::_supplied_provider`
- `packages/python/combat-engine/mordheim_combat/modular/leadership.py::_relayed_leader`
- `packages/python/combat-engine/mordheim_combat/modular/leadership.py::_instructing_leader`
- `packages/python/core/mordheim_core/context.py::prepare_duel_context`

Estas referencias son puntos de entrada; sigue sus llamadas para reproducir el comportamiento completo, sin releer las fuentes de reglas.

## Trabajo concreto

1. Portar literalmente las decisiones de elegibilidad y resultados de `psychology.py` y `leadership.py` a helpers de lote. Los dos módulos nuevos separan esta propiedad del driver de G06; no constituyen otro motor.
2. Usar el contexto local ya preparado: participantes, rangos y contactos suministrados, proveedor utilizable, valor propio/prestado y exclusiones. No producir posiciones, buscar una banda completa ni ampliar a psicología de grupo.
3. Reproducir Fear, Stupidity, inmunidades y excepciones, Frenzy y resultados que impidan carga, ataques o acciones. Mantener sus máscaras por fila y cambios en los momentos que dicta `resolve_round`.
4. Portar las repeticiones y modificadores de Leadership, límites por turno/combate y prohibiciones de préstamo. Usar los recursos de G02; no efectuar elecciones o gasto globales para el lote.
5. Proveer a G03/G04 resultados o máscaras cuando cambien impacto, ataques o acciones. G06 conecta los helpers en el orden de ronda; devolver la lista exacta de llamadas, argumentos, máscaras modificadas y momento de aplicación.
6. No importar `resolve_round`, `resolve_fear` o `resolve_local_leadership` escalares como ruta de ejecución de cada simulación. Se consultan como referencia de portado, conservando el procesamiento numérico por lotes.

## Comprobación mínima

Reutilizar ejemplos y resultados aceptados de psicología/liderazgo como referencias sin reescribir sus tests. Si falta comprobación NumPy, un escenario pequeño representativo que produzca filas con resultados distintos; añadir otro solo si un hueco concreto lo requiere. La certificación estadística corresponde a G07.

## Criterio de entrega

Helpers NumPy implementados y comprobados de forma enfocada, con contrato de conexión preciso para G06. Las filas principales siguen pendientes de integración hasta que el driver ejecute esos helpers.

## Claves principales asignadas

| id | clause_id | Apoyos | Referencia de asignación |
| --- | --- | --- | --- |
| `item/beastlash` | `beastbane` | — | consumer |
| `item/beastlash` | `whole` | G03 | consumer |
| `item/chainsaw_sword` | `whole` | G03 | consumer |
| `item/holy_relic` | `first-leadership-pass--scope--first-leadership-pass` | — | consumer |
| `item/holy_relic` | `first-leadership-pass--scope--single-relic-rule` | — | consumer |
| `item/holy_relic_pilgrim_only` | `first-leadership-pass--scope--first-leadership-pass` | — | consumer |
| `item/holy_relic_pilgrim_only` | `first-leadership-pass--scope--single-relic-rule` | — | consumer |
| `mechanic/defence.holy-relic` | `first-leadership-pass--scope--first-leadership-pass` | — | consumer |
| `mechanic/defence.holy-relic` | `first-leadership-pass--scope--single-relic-rule` | — | consumer |
| `mechanic/mechanic.automatic-leadership` | `automatic-leadership` | — | consumer |
| `mechanic/mechanic.brood-mentality` | `brood-mentality` | — | consumer |
| `mechanic/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `mechanic/mechanic.cold-blooded-leadership` | `cold-blooded-leadership` | — | consumer |
| `mechanic/mechanic.cold-blooded-psychology` | `cold-blooded-psychology` | — | consumer |
| `mechanic/mechanic.craven` | `craven` | — | consumer |
| `mechanic/mechanic.disability` | `head-injury-stupidity` | G02 | consumer |
| `mechanic/mechanic.disability` | `no-two-weapons-or-weapon-and-shield` | G02 | consumer |
| `mechanic/mechanic.disability` | `permanent-characteristic-penalty` | G02 | consumer |
| `mechanic/mechanic.fear-human` | `fear-human` | — | consumer |
| `mechanic/mechanic.fear-immunity` | `fear-immunity` | — | consumer |
| `mechanic/mechanic.fear-reroll` | `fear-reroll` | — | consumer |
| `mechanic/mechanic.first-failed-leadership-reroll` | `first-failed-leadership-reroll` | — | consumer |
| `mechanic/mechanic.handler-leadership` | `handler-leadership` | — | consumer |
| `mechanic/mechanic.leader-six` | `leader-six` | — | consumer |
| `mechanic/mechanic.leadership-reroll` | `leadership-reroll` | — | consumer |
| `mechanic/mechanic.mandatory-leadership-reroll` | `mandatory-leadership-reroll` | — | consumer |
| `mechanic/mechanic.morrs-servant` | `whole` | — | consumer |
| `mechanic/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `mechanic/mechanic.stupidity` | `stupidity` | — | consumer |
| `mechanic/mechanic.undead` | `undead` | — | consumer |
| `mechanic/mechanic.undivided-leader` | `undivided-leader--scope--leadership-reroll-aura` | — | consumer |
| `mechanic/mechanic.wizened-halfling` | `whole` | — | consumer |
| `mechanic/skill.fearsome` | `fearsome` | — | consumer |
| `mechanic/weapon.beastlash` | `beastbane-fear` | — | consumer |
| `mechanic/weapon.chainsaw-sword` | `whole` | G03 | consumer |
| `rule/catalog/general/skill.fearsome/skill.fearsome` | `fearsome` | — | consumer |
| `rule/mordheim/adventurers-kaz/barbarian--dim-witted/unimplemented.adventurers-kaz.barbarian.dim-witted` | `dim-witted--scope--leader-leadership-supply` | — | consumer |
| `rule/mordheim/amazons-lustria/serpent-priestess--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/amazons-mordheim/priestess--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/arabian-tomb-raiders/sheikh--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/araby-smugglers-sar/rais--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/averlanders/captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/battle-monks-of-cathay/emissary--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/battle-monks-of-cathay/raging-peasants--mob/unimplemented.battle-monks-of-cathay.raging-peasants.mob` | `individual-leadership-bonus` | — | consumer |
| `rule/mordheim/battle-monks-of-cathay/raging-peasants--mob/unimplemented.battle-monks-of-cathay.raging-peasants.mob` | `no-leader-benefit` | — | consumer |
| `rule/mordheim/beastmen-raiders/band--beastmen-special-skills-fearless/mechanic.fear-immunity` | `fear-immunity` | — | consumer |
| `rule/mordheim/beastmen-raiders/beastmen-chieftain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/beastmen-raiders/minotaur--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/black-dwarfs/gaolers--nasty-reputation/mechanic.fear-human` | `fear-human` | — | consumer |
| `rule/mordheim/black-dwarfs/sorcerer--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/black-orcs/band--black-orc-special-skills-ere-we-go/unimplemented.black-orcs.band.black-orc-special-skills-ere-we-go` | `ere-we-go` | — | consumer |
| `rule/mordheim/black-orcs/black-orc-boss--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/black-orcs/orc-nuttaz--crazy/mechanic.automatic-leadership` | `automatic-leadership` | — | consumer |
| `rule/mordheim/black-orcs/troll--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/black-orcs/troll--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/blood-dragons-mou/grave-guards--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/blood-dragons-mou/hell-hounds--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/blood-dragons-mou/hell-hounds--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/blood-dragons-mou/skeleton-warriors--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/blood-dragons-mou/skeleton-warriors--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/blood-dragons-mou/vampire--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/blood-dragons-mou/vampire--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/blood-dragons-mou/wights--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/blood-dragons-mou/wights--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/bretonnian-brigands-mou/scarface--horribly-scarred/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/bretonnian-buccaneers-sar/captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/bretonnian-chapel-guard/battle-pilgrims--holy-relics/unimplemented.bretonnian-chapel-guard.battle-pilgrims.holy-relics` | `holy-relic-frenzy` | G03 | consumer |
| `rule/mordheim/bretonnian-chapel-guard/battle-pilgrims--stubborn/mechanic.mandatory-leadership-reroll` | `mandatory-leadership-reroll` | — | consumer |
| `rule/mordheim/bretonnian-chapel-guard/knights-errant--impetuous/unimplemented.bretonnian-chapel-guard.knights-errant.impetuous` | `impetuous-charge-psychology` | — | consumer |
| `rule/mordheim/bretonnian-chapel-guard/questing-knight--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/bretonnian-knights/questing-knight--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/brood-of-ghurash-the-sc/band--brood-mentality/mechanic.brood-mentality` | `brood-mentality--scope--stupidity` | — | consumer |
| `rule/mordheim/brood-of-ghurash-the-sc/band--brood-mentality/mechanic.stupidity` | `stupidity--scope--stupidity` | — | consumer |
| `rule/mordheim/brood-of-ghurash-the-sc/band--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/brood-of-ghurash-the-sc/broodmother--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/cairn-wraith--causes-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/cairn-wraith--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/malignant-spirits--causes-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/malignant-spirits--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/mourngul--causes-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/mourngul--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/poltergeists--causes-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/poltergeists--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/revenants--causes-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/revenants--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/spirit-hosts--causes-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/spirit-hosts--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/tomb-banshee--causes-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/tomb-banshee--ghostly-howl/unimplemented.call-of-the-night-haint-mim.tomb-banshee.ghostly-howl` | `ghostly-howl` | — | consumer |
| `rule/mordheim/call-of-the-night-haint-mim/tomb-banshee--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/carnival-of-chaos/band--blessings-of-nurgle-hideous/mechanic.causes-fear` | `cause-fear--scope--cause-fear` | — | consumer |
| `rule/mordheim/carnival-of-chaos/carnival-master--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/carnival-of-chaos/nurglings--immune-to-psychology/mechanic.automatic-leadership` | `automatic-leadership` | — | consumer |
| `rule/mordheim/carnival-of-chaos/plague-bearers--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/carnival-of-chaos/plague-bearers--immune-to-psychology/mechanic.automatic-leadership` | `automatic-leadership` | — | consumer |
| `rule/mordheim/carnival-of-chaos/plague-cart--immune-to-psychology/mechanic.automatic-leadership` | `automatic-leadership` | — | consumer |
| `rule/mordheim/channel-rats-mim/domnu--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/channel-rats-mim/fugitives--charismatic/unimplemented.channel-rats-mim.fugitive.charismatic` | `charismatic` | — | consumer |
| `rule/mordheim/clan-angrund-kep/dwarf-noble--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/clan-angrund-kep/dwarf-troll-slayers--deathwish/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/clockworkers-sc/band--constructs/unimplemented.clockworkers-sc.band.constructs` | `constructs-psychology-immunity` | G02, G03 | consumer |
| `rule/mordheim/clockworkers-sc/clockwork-fiend--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/clockworkers-sc/clockwork-fiend--construct/unimplemented.clockworkers-sc.clockwork-fiend.construct` | `construct-psychology-immunity` | — | consumer |
| `rule/mordheim/clockworkers-sc/clockwork-soldiers--construct/unimplemented.clockworkers-sc.clockwork-soldiers.construct` | `construct-psychology-immunity` | — | consumer |
| `rule/mordheim/clockworkers-sc/master-of-clocks--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/crooked-moon-kep/big-boss--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/crooked-moon-kep/fanatics--looney/unimplemented.crooked-moon-kep.fanatics.looney` | `frenzy` | — | consumer |
| `rule/mordheim/crooked-moon-kep/troll--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/crooked-moon-kep/troll--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/cult-of-the-possessed/band--mutations-hideous/mechanic.causes-fear` | `cause-fear--scope--cause-fear` | — | consumer |
| `rule/mordheim/cult-of-the-possessed/darksouls--crazed/mechanic.automatic-leadership` | `automatic-leadership` | — | consumer |
| `rule/mordheim/cult-of-the-possessed/magister--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/cult-of-the-possessed/the-possessed--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/cursed-cavalcade/aristocrat--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/cursed-cavalcade/band--cursed-cavalcade-special-skills-noblesse-obliges/unimplemented.cursed-cavalcade.band.cursed-cavalcade-special-skills-noblesse-obliges` | `noblesse-fear-immunity` | — | consumer |
| `rule/mordheim/dark-elves/cold-one-beasthounds--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/dark-elves/cold-one-beasthounds--stupidity/mechanic.handler-leadership` | `handler-leadership` | — | consumer |
| `rule/mordheim/dark-elves/cold-one-beasthounds--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/dark-elves/high-born--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/dreamwalkers-cult-of-morr-fbg/band--special-skill-inspiring-presence/unimplemented.dreamwalkers-cult-of-morr-fbg.special-skill.inspiring-presence` | `inspiring-presence-borrow` | — | consumer |
| `rule/mordheim/dreamwalkers-cult-of-morr-fbg/band--special-skill-inured-to-horror/unimplemented.dreamwalkers-cult-of-morr-fbg.special-skill.inured-to-horror` | `fear-immunity` | — | consumer |
| `rule/mordheim/dreamwalkers-cult-of-morr-fbg/band--undead-foes-no-fear/unimplemented.dreamwalkers-cult-of-morr-fbg.band.undead-foes-no-fear` | `fear-immunity` | — | consumer |
| `rule/mordheim/dreamwalkers-cult-of-morr-fbg/dreamer--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/druchii-mic/noble--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/druchii-mic/slavehounds--beastmaster/mechanic.handler-leadership` | `handler-leadership--scope--handler-leadership` | — | consumer |
| `rule/mordheim/druchii-mic/slavehounds--beastmaster/mechanic.handler-leadership` | `handler-leadership--scope--handler-leadership-source-limits` | — | consumer |
| `rule/mordheim/dwarf-guildsmen-kaz/band--brewers/unimplemented.dwarf-guildsmen-kaz.band.brewers` | `brew-fear-immunity` | — | consumer |
| `rule/mordheim/dwarf-guildsmen-kaz/band--brewers/unimplemented.dwarf-guildsmen-kaz.band.brewers` | `brew-frenzy` | — | consumer |
| `rule/mordheim/dwarf-guildsmen-kaz/master-craftsman--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/dwarf-rangers/dwarf-longbeards--stubborn/mechanic.leadership-reroll` | `leadership-reroll` | — | consumer |
| `rule/mordheim/dwarf-rangers/dwarf-troll-slayers--deathwish/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/dwarf-rangers/runesmith--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/dwarf-slayer-cult-web/band--rememberer-skills/unimplemented.dwarf-slayer-cult-web.special.rememberer-skills` | `rememberer-skills--scope--leadership-reroll-aura` | — | consumer |
| `rule/mordheim/dwarf-slayer-cult-web/band--slayer-rules/mechanic.psychology-immunity` | `psychology-immunity--scope--psychology-coverage` | — | consumer |
| `rule/mordheim/dwarf-slayer-cult-web/band--slayer-rules/mechanic.psychology-immunity` | `psychology-immunity--scope--psychology-immunity` | — | consumer |
| `rule/mordheim/dwarf-slayer-cult-web/giant-slayer--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/dwarf-slayers-kaz/giant-slayer--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/dwarf-treasure-hunters/dwarf-noble--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/dwarf-treasure-hunters/dwarf-troll-slayers--deathwish/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/fallen-the-rel/butcher--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/fallen-the-rel/ghouls--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/fallen-the-rel/revenant--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/fallen-the-rel/revenant--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/fallen-the-rel/sgulls--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/fen-guard-mim/branchnymph--instinctual/mechanic.causes-fear` | `cause-fear--scope--fear-of-fire-rider` | — | encargo explícito; consumer vacío |
| `rule/mordheim/fen-guard-mim/branchnymph--instinctual/mechanic.causes-fear` | `cause-fear--scope--immunity-and-fear` | — | encargo explícito; consumer vacío |
| `rule/mordheim/fen-guard-mim/branchnymph--instinctual/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/fen-guard-mim/branchwych--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/fen-guard-mim/branchwych--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/fen-guard-mim/dryads--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/fen-guard-mim/treekin--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/fen-guard-mim/treekin--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/forest-goblins-lus/chieftain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/forest-goblins-lus/gigantic-spider--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/forest-goblins-lus/gigantic-spider--nonsentient/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/forest-goblins-lus/red-toof-clan-goblins--berserkers/unimplemented.forest-goblins-lus.red-toof-clan-goblins.berserkers` | `frenzy--scope--frenzy` | — | consumer |
| `rule/mordheim/forest-goblins/chieftain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/forest-goblins/gigantic-spider--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/forest-goblins/gigantic-spider--non-sentient/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/forest-goblins/red-toof-goblins--berserkers/trait.frenzy` | `frenzy` | G02 | consumer |
| `rule/mordheim/ghost-pirates-sar/ghost-captain--undead/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/ghost-captain--undead/unimplemented.ghost-pirates-sar.ghost-captain.undead` | `undead-psychology-immunity` | G02, G03 | consumer |
| `rule/mordheim/ghost-pirates-sar/gibbets--undead/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/gibbets--undead/unimplemented.ghost-pirates-sar.gibbets.undead` | `undead-psychology-immunity` | G02, G03 | consumer |
| `rule/mordheim/ghost-pirates-sar/screaming-ghosts--undead/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/screaming-ghosts--undead/unimplemented.ghost-pirates-sar.screaming-ghosts.undead` | `undead-psychology-immunity` | G02, G03 | consumer |
| `rule/mordheim/ghost-pirates-sar/skeleton-mates--undead/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/skeleton-mates--undead/unimplemented.ghost-pirates-sar.skeleton-mates.undead` | `undead-psychology-immunity` | G02, G03 | consumer |
| `rule/mordheim/ghost-pirates-sar/the-bloated--undead/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/the-bloated--undead/unimplemented.ghost-pirates-sar.the-bloated.undead` | `undead-psychology-immunity` | G02, G03 | consumer |
| `rule/mordheim/ghutani-rel/emir--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/ghutani-rel/scholar--field-of-scholarship/unimplemented.ghutani-rel.scholar.field-of-scholarship` | `field-of-scholarship--scope--leader-leadership` | — | consumer |
| `rule/mordheim/guild-of-disgraced-engineers-mim/expelled-engineer--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/gunnery-school-of-nuln/senior-gunnery-officer--leader/unimplemented.gunnery-school-of-nuln.senior-gunnery-officer.leader` | `leader-twelve` | — | consumer |
| `rule/mordheim/halflings-mic/halfling-elder--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/halflings-mic/village-ogre--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/high-elves-lus/loremaster--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/hochland-bandits/bandit-prince--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/hochland-bandits/blackhearts--hardened/unimplemented.hochland-bandits.blackhearts.hardened` | `fear-immunity` | — | consumer |
| `rule/mordheim/horned-hunters/drunken-gang--drunk/unimplemented.horned-hunters.drunken-gang.drunk` | `automatic-leadership` | — | consumer |
| `rule/mordheim/horned-hunters/horned-hunter--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/house-guard-sc/adjutant--relay-orders/unimplemented.house-guard-sc.adjutant.relay-orders` | `relay-orders` | — | consumer |
| `rule/mordheim/house-guard-sc/commander--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/imperial-outriders/knight--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/khorne-raiders-sar/madbrains--immune-to-psychology/mechanic.automatic-leadership` | `automatic-leadership` | — | consumer |
| `rule/mordheim/kislevites/bear-tamer--bear-handler/unimplemented.kislevites.bear-tamer.bear-handler` | `handler-leadership--scope--stupidity-waiver` | — | encargo explícito; consumer vacío |
| `rule/mordheim/kislevites/druzhina-captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/kislevites/trained-bear--fearsome/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/kislevites/trained-bear--trained/mechanic.handler-leadership` | `handler-leadership--scope--stupidity` | — | encargo explícito; consumer vacío |
| `rule/mordheim/kislevites/trained-bear--trained/mechanic.stupidity` | `stupidity--scope--stupidity` | — | consumer |
| `rule/mordheim/knights-of-the-bitter-moors-mim/questing-knight--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/lizardmen-lus/band--cold-blooded/mechanic.cold-blooded-psychology` | `cold-blooded-psychology` | — | consumer |
| `rule/mordheim/lizardmen-lus/kroxigor--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/lizardmen-lus/skink-priest--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/lizardmen/band--cold-blooded/mechanic.cold-blooded-psychology` | `cold-blooded-psychology` | — | consumer |
| `rule/mordheim/lizardmen/kroxigor--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/lizardmen/skink-priest--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/lords-of-the-marsh-mim/band--cold-blooded/mechanic.cold-blooded-leadership` | `cold-blooded-leadership` | — | consumer |
| `rule/mordheim/lords-of-the-marsh-mim/daemon-fimm--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/lords-of-the-marsh-mim/draich--craven/mechanic.craven` | `craven--scope--craven` | — | consumer |
| `rule/mordheim/lords-of-the-marsh-mim/draich--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/lords-of-the-marsh-mim/draich--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/lords-of-the-marsh-mim/fimir-warriors--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/lords-of-the-marsh-mim/fimir-warriors--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/lords-of-the-marsh-mim/shearls--craven/mechanic.craven` | `craven--scope--craven` | — | consumer |
| `rule/mordheim/lords-of-the-marsh-mim/shearls--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/lords-of-the-marsh-mim/young-nobles--craven/mechanic.craven` | `craven--scope--craven` | — | consumer |
| `rule/mordheim/lords-of-the-marsh-mim/young-nobles--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/low-kings-mim/racketeer--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/lustrian-reavers/barbary-monkey--beastmaster-leadership/unimplemented.lustrian-reavers.barbary-monkey.beastmaster-leadership` | `handler-leadership` | — | consumer |
| `rule/mordheim/lustrian-reavers/estalian-warhound--beastmaster-leadership/unimplemented.lustrian-reavers.estalian-warhound.beastmaster-leadership` | `handler-leadership` | — | consumer |
| `rule/mordheim/maneaters/band--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/maneaters/captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/maneaters/sabretusks--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/maneaters/sabretusks--trained/unimplemented.maneaters.sabretusks.trained` | `trained--scope--handler-leadership` | — | consumer |
| `rule/mordheim/marauders-of-chaos/band--mark-of-chaos-undivided/mechanic.undivided-leader` | `undivided-leader--scope--leadership-reroll-aura` | — | consumer |
| `rule/mordheim/marauders-of-chaos/condemned--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/marauders-of-chaos/marauder-chieftain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/marauders-of-chaos/spawn-of-chaos--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/marauders-of-chaos/spawn-of-chaos--psychology/mechanic.automatic-leadership` | `automatic-leadership` | — | consumer |
| `rule/mordheim/masters-of-horror-sylv/flesh-construct--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/masters-of-horror-sylv/flesh-construct--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/masters-of-horror-sylv/mad-scientist--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/masters-of-horror-sylv/mad-scientist--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/masters-of-horror-sylv/mad-scientist--lunatic/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/masters-of-horror-sylv/mad-scientist--lunatic/mechanic.leadership-reroll` | `cause-fear` | — | consumer |
| `rule/mordheim/masters-of-horror-sylv/mad-scientist--lunatic/mechanic.leadership-reroll` | `leadership-reroll` | — | consumer |
| `rule/mordheim/masters-of-horror-sylv/thrall--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/masters-of-horror-sylv/thrall--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/masters-of-horror-sylv/zombies--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/masters-of-horror-sylv/zombies--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/mazzalupo-web/black-sheep--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/mazzalupo-web/wandering-knight--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/mercenaries/band--reikland-command-radius/unimplemented.mercenaries.band.reikland-command-radius` | `leader-twelve` | — | consumer |
| `rule/mordheim/mercenaries/mercenary-captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/merchant-caravans/band--merchant-leadership/unimplemented.merchant-caravans.band.merchant-leadership` | `merchant-leadership--scope--leader-leadership-supply` | — | consumer |
| `rule/mordheim/metal-mongers-mim/engineer-adept--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/metal-mongers-mim/machine-ogre--bio-machinery/unimplemented.metal-mongers-mim.machine-ogre.bio-machinery` | `psychology-immunity` | — | consumer |
| `rule/mordheim/metal-mongers-mim/machine-ogre--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/militiant-mootlanders-mim/burgermeister--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/mootlanders/moot-elder--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/muzil-rel/emir--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/muzil-rel/scholar--field-of-scholarship/unimplemented.muzil-rel.scholar.field-of-scholarship` | `field-of-scholarship--scope--leader-leadership` | — | consumer |
| `rule/mordheim/necrarchs-mou/abomination--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/necrarchs-mou/banshee--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/necrarchs-mou/defiled--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/necrarchs-mou/nosferatu--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/necrarchs-mou/nosferatu--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/necrarchs-mou/skeleton--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/necrarchs-mou/skeleton--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/necrarchs-mou/wight--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/necrarchs-mou/wight--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/abomination--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/abomination--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/necrarch-vampire--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/necrarch-vampire--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/necrarch-vampire--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/skeletal-warrior--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/skeletal-warrior--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/thrall--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/thrall--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/zombie--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/necrarchs-the-soul-stealers-lotd1/zombie--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/night-goblins-kaz/big-boss--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/night-goblins-kaz/fanatics--looney/unimplemented.night-goblins-kaz.fanatics.looney` | `frenzy` | — | consumer |
| `rule/mordheim/night-goblins-kaz/troll--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/night-goblins-kaz/troll--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/night-goblins-mic/big-boss--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/night-goblins-mic/fanatics--looney/trait.frenzy` | `frenzy` | G02 | consumer |
| `rule/mordheim/night-goblins-mic/troll--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/night-goblins-mic/troll--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/night-goblins-web/band--fear-elves/unimplemented.night-goblins-web.band.fear-elves` | `fear-of-elves` | — | consumer |
| `rule/mordheim/night-goblins-web/boss--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/night-goblins-web/great-squig--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/night-goblins-web/shaman--fungus-brew/unimplemented.night-goblins-web.shaman.fungus-brew` | `fungus-fearless-fear` | — | consumer |
| `rule/mordheim/night-goblins-web/squig-herder--handle-animal-squig/unimplemented.night-goblins-web.squig-herder.handle-animal-squig` | `handler-leadership` | — | consumer |
| `rule/mordheim/night-goblins-web/troll--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/night-goblins-web/troll--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/nipponese-expedition-web/hatamoto--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/norse-explorers-btb/band--norse-special-skills-barbarian-courage/mechanic.fear-reroll` | `fear-reroll` | — | consumer |
| `rule/mordheim/norse-explorers-btb/jarl--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/norse-explorers-btb/wulfen--bestial/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/norse-explorers-btb/wulfen--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/norse-explorers-lustria/band--norse-special-skills-barbarian-courage/mechanic.fear-reroll` | `fear-reroll` | — | consumer |
| `rule/mordheim/norse-explorers-lustria/jarl--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/norse-explorers-lustria/wulfen--bestial/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/norse-explorers-lustria/wulfen--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/ogre-hunting-party-web/band--huuuuge/mechanic.causes-fear` | `cause-fear--scope--cause-fear` | — | consumer |
| `rule/mordheim/ogre-hunting-party-web/band--huuuuge/profile.equipment-restrictions` | `cause-fear` | — | consumer |
| `rule/mordheim/ogre-hunting-party-web/ogre-hunter--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/ogre-hunting-party-web/sabretusks--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/orc-mob/band--orc-special-skills-ere-we-go/unimplemented.orc-mob.band.orc-special-skills-ere-we-go` | `ere-we-go` | — | consumer |
| `rule/mordheim/orc-mob/orc-boss--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/orc-mob/troll--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/orc-mob/troll--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/order-of-the-mare-web/paragon--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/ostlanders/elder--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/ostlanders/ogre--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/ostlanders/ruffians--drunk/unimplemented.ostlanders.ruffians.drunk` | `automatic-leadership` | — | consumer |
| `rule/mordheim/outlaws-of-stirwood-forest-redux-fbg/bandit-leader--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/outlaws-of-stirwood-forest/bandit-leader--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/pirates/pirate-captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/pit-fighters/band--pit-fighter-skill-grizzled-veteran/unimplemented.pit-fighters.band.pit-fighter-skill-grizzled-veteran` | `psychology-immunity` | — | consumer |
| `rule/mordheim/pit-fighters/dwarf-troll-slayer--death-wish/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/pit-fighters/ogre-pit-fighter--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/pit-fighters/pit-king--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/protectorate-of-sigmar-lotd3/band--special-skill-unshakeable-faith/unimplemented.protectorate-of-sigmar-lotd3.band.unshakeable-faith` | `fear-immunity` | — | consumer |
| `rule/mordheim/protectorate-of-sigmar-lotd3/hound--devoted/unimplemented.protectorate-of-sigmar-lotd3.hound.devoted` | `devoted` | — | consumer |
| `rule/mordheim/protectorate-of-sigmar-lotd3/huntsman--beastmaster/unimplemented.protectorate-of-sigmar-lotd3.huntsman.beastmaster` | `handler-leadership` | — | consumer |
| `rule/mordheim/protectorate-of-sigmar-lotd3/warrior-priest--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/restless-dead/grave-guards--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/restless-dead/grave-guards--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/restless-dead/liche--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/restless-dead/liche--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/restless-dead/scarecrows--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/restless-dead/scarecrows--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/restless-dead/skeletons--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/restless-dead/skeletons--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/restless-dead/wights--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/restless-dead/wights--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/restless-dead/zombies--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/restless-dead/zombies--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/sartosan-pirates-sar/captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/savage-orcs-kaz/boss--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/savage-orcs-kaz/nuttaz--frenzy/trait.frenzy` | `frenzy` | G02 | consumer |
| `rule/mordheim/sea-ghosts-mim/feast-master--bestial/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/sea-ghosts-mim/minstrels--songster/unimplemented.sea-ghosts-mim.minstrels.songster` | `songster` | — | consumer |
| `rule/mordheim/sea-ghosts-mim/wayfinder--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/shadow-warriors/shadow-master--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/shallows-beasts-mim/buccaneer--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/silent-brotherhood-sc/silent-master--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/sisters-of-sigmar/band--special-skills-absolute-faith/mechanic.fear-reroll` | `fear-reroll` | — | consumer |
| `rule/mordheim/sisters-of-sigmar/sigmarite-matriarch--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/skaven-clan-eshin/assassin-adept--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/skaven-clan-eshin/rat-ogre--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/skaven-clan-eshin/rat-ogre--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/skaven-clan-pestilens/plague-priest--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/skaven-clan-pestilens/rat-ogre--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/skaven-clan-pestilens/rat-ogre--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/skaven-of-clan-mors-kaz/claw-leader--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/skaven-of-clan-mors-kaz/rat-ogre--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/skaven-of-clan-mors-kaz/rat-ogre--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/skaven-of-clan-moulder-web/band--clan-moulder-special-skills/unimplemented.skaven-of-clan-moulder-web.special.clan-moulder-special-skills` | `hypnotic-musk--scope--hypnotic-musk` | — | consumer |
| `rule/mordheim/skaven-of-clan-moulder-web/packmaster--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/skaven-of-clan-moulder-web/rat-ogres--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/skaven-of-clan-moulder-web/rat-ogres--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-lus/plague-priest--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-priest--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/skaven-of-clan-pristekk-sc/chieftain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/skaven-of-clan-pristekk-sc/rat-ogres--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/skaven-of-clan-pristekk-sc/rat-ogres--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/skaven-of-clan-skryre-kaz/master-engineer--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/skaven-of-clan-skryre-rel/overseer--slave-driver/unimplemented.skaven-of-clan-skryre-rel.overseer.slave-driver` | `slave-driver` | — | consumer |
| `rule/mordheim/skaven-of-clan-skryre-rel/warlock-engineer--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/slave-uprising-kep/demagogue--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/slavers-rel/eunuchs--broken-spirit/unimplemented.slavers-rel.eunuchs.broken-spirit` | `broken-spirit--scope--automatic-leadership` | — | consumer |
| `rule/mordheim/slavers-rel/ogre-bodyguard--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/slavers-rel/overseer--slave-driver/unimplemented.slavers-rel.overseer.slave-driver` | `slave-driver` | — | consumer |
| `rule/mordheim/slavers-rel/slave-merchant--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/snotlings-web/bullied-goblin--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/sons-of-hashut/apprentice-sorcerer--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/sorcerous-society-lotd4/magus--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/strigoi-kaz/charnel-guard--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/strigoi-kaz/fell-bats--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/strigoi-kaz/fell-bats--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/strigoi-kaz/ghouls--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/strigoi-kaz/skeletons--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/strigoi-kaz/skeletons--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/strigoi-kaz/vampire--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/survivors-of-strigos-sylv/ghouls--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/survivors-of-strigos-sylv/strigoi-vampire--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/survivors-of-strigos-sylv/strigoi-vampire--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/survivors-of-strigos-sylv/strigoi-vampire--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/tileans/captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/tomb-guardians/band--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/tomb-guardians/band--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/tomb-guardians/liche-priest--undead/mechanic.undead` | `undead` | — | consumer |
| `rule/mordheim/tomb-guardians/skeleton-warriors--undead/mechanic.undead` | `undead` | — | consumer |
| `rule/mordheim/tomb-guardians/tomb-guardians--undead/mechanic.undead` | `undead` | — | consumer |
| `rule/mordheim/tomb-guardians/tomb-lord--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/tomb-guardians/tomb-lord--undead/mechanic.undead` | `undead` | — | consumer |
| `rule/mordheim/tomb-guardians/tomb-scorpions--living/unimplemented.tomb-guardians.tomb-scorpions.living` | `living` | — | consumer |
| `rule/mordheim/turjuk-rel/emir--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/turjuk-rel/scholar--field-of-scholarship/unimplemented.turjuk-rel.scholar.field-of-scholarship` | `field-of-scholarship--scope--leader-leadership` | — | consumer |
| `rule/mordheim/undead/dire-wolves--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/undead/dire-wolves--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/undead/ghouls--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/undead/vampire--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/undead/vampire--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/undead/vampire--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/undead/zombies--cause-fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/undead/zombies--immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `rule/mordheim/underworld-alliance-mim/goblin-bully--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/underworld-alliance-mim/skaven-slum-lord--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/underworld-alliance-mim/warpstone-troll--fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `rule/mordheim/underworld-alliance-mim/warpstone-troll--stupidity/mechanic.stupidity` | `stupidity` | — | consumer |
| `rule/mordheim/vampire-hunters-of-sylvania-lotd5/band--special-skill-iron-will/mechanic.fear-immunity` | `fear-immunity` | — | consumer |
| `rule/mordheim/vampire-hunters-of-sylvania-lotd5/vampire-hunter--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/wasteland-privateers-sar/captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/watchmen-mim/band--fanatical/unimplemented.watchmen-mim.band.fanatical` | `fanatical-autopass--scope--automatic-leadership` | — | consumer |
| `rule/mordheim/watchmen-mim/watch-captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/witch-hunters/flagellants--fanatical/mechanic.automatic-leadership` | `automatic-leadership` | — | consumer |
| `rule/mordheim/witch-hunters/witch-hunter-captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/mordheim/wood-elves-of-athel-loren-web/hunt-master--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-arcane-society/grand-wizard--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-bretonnian-knights/questing-knight--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-deathbringers/shadow-blade--fear/unimplemented.chaos-streets-deathbringers.shadow-blade.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/chaos-streets-deathbringers/shadow-blade--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/dwarf-noble--leader/unimplemented.chaos-streets-dwarf-treasure-hunters.dwarf-noble.leader` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-dwarf-treasure-hunters/dwarf-troll-slayers--death-oath/unimplemented.chaos-streets-dwarf-treasure-hunters.dwarf-troll-slayers.death-oath` | `psychology-immunity` | G02, G03 | consumer |
| `rule/trollheim/chaos-streets-greenskins/band--orc-special-skills-ere-we-go/unimplemented.chaos-streets-greenskins.band.orc-special-skills-ere-we-go` | `ere-we-go` | — | consumer |
| `rule/trollheim/chaos-streets-greenskins/goblin-warriors--fear-elves/unimplemented.chaos-streets-greenskins.goblin-warriors.fear-elves` | `fear-of-elves` | — | consumer |
| `rule/trollheim/chaos-streets-greenskins/orc-boss--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-greenskins/troll--fear/unimplemented.chaos-streets-greenskins.troll.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/chaos-streets-greenskins/troll--stupidity/unimplemented.chaos-streets-greenskins.troll.stupidity` | `stupidity` | — | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/cripples--disability/compiler.disability` | `head-injury-stupidity` | G02 | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/cripples--disability/compiler.disability` | `no-two-weapons-or-weapon-and-shield` | G02 | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/cripples--disability/compiler.disability` | `permanent-characteristic-penalty` | G02 | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/desolate-soul--fanatic/unimplemented.chaos-streets-mordheim-inhabitants.desolate-soul.fanatic` | `automatic-leadership` | — | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/prophet--fanatic/unimplemented.chaos-streets-mordheim-inhabitants.prophet.fanatic` | `automatic-leadership` | — | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/prophet--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/band--pit-fighter-skill-grizzled-veteran/unimplemented.chaos-streets-pit-fighters.band.pit-fighter-skill-grizzled-veteran` | `psychology-immunity` | — | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/dwarf-troll-slayer--death-oath/unimplemented.chaos-streets-pit-fighters.dwarf-troll-slayer.death-oath` | `psychology-immunity` | G02, G03 | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/ogre-pit-fighter--fear/unimplemented.chaos-streets-pit-fighters.ogre-pit-fighter.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/chaos-streets-pit-fighters/pit-king--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-sigmar-protectorate/band--protectorate-special-skills-absolute-faith/unimplemented.chaos-streets-sigmar-protectorate.band.protectorate-special-skills-absolute-faith` | `fear-immunity` | — | consumer |
| `rule/trollheim/chaos-streets-sigmar-protectorate/ranger--animal-tamer/unimplemented.chaos-streets-sigmar-protectorate.ranger.animal-tamer` | `handler-leadership` | — | consumer |
| `rule/trollheim/chaos-streets-sigmar-protectorate/warrior-priest--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-sons-of-nagarythe/shadow-master--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/band--von-carstein-power-dark-majesty/unimplemented.band-von-carstein-power-dark-majesty` | `leader-range` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/blood-dragon-vampire--fear/unimplemented.chaos-streets-undead-bloodlines.blood-dragon-vampire.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/blood-dragon-vampire--immune-to-psychology/unimplemented.chaos-streets-undead-bloodlines.blood-dragon-vampire.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/blood-dragon-vampire--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/carrion-ghoul--fear/unimplemented.chaos-streets-undead-bloodlines.carrion-ghoul.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/dire-wolf--fear/unimplemented.chaos-streets-undead-bloodlines.dire-wolf.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/dire-wolf--immune-to-psychology/unimplemented.chaos-streets-undead-bloodlines.dire-wolf.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/ghoul--fear/unimplemented.chaos-streets-undead-bloodlines.ghoul.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/lahmia-vampire--fear/unimplemented.chaos-streets-undead-bloodlines.lahmia-vampire.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/lahmia-vampire--immune-to-psychology/unimplemented.chaos-streets-undead-bloodlines.lahmia-vampire.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/lahmia-vampire--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/necrarch-vampire--fear/unimplemented.chaos-streets-undead-bloodlines.necrarch-vampire.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/necrarch-vampire--immune-to-psychology/unimplemented.chaos-streets-undead-bloodlines.necrarch-vampire.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/necrarch-vampire--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/strigoi-vampire--fear/unimplemented.chaos-streets-undead-bloodlines.strigoi-vampire.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/strigoi-vampire--immune-to-psychology/unimplemented.chaos-streets-undead-bloodlines.strigoi-vampire.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/strigoi-vampire--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/vampire-bat--fear/unimplemented.chaos-streets-undead-bloodlines.vampire-bat.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/vampire-bat--immune-to-psychology/unimplemented.chaos-streets-undead-bloodlines.vampire-bat.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/von-carstein-vampire--fear/unimplemented.chaos-streets-undead-bloodlines.von-carstein-vampire.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/von-carstein-vampire--immune-to-psychology/unimplemented.chaos-streets-undead-bloodlines.von-carstein-vampire.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/von-carstein-vampire--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/zombie--fear/unimplemented.chaos-streets-undead-bloodlines.zombie.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/zombie--immune-to-psychology/unimplemented.chaos-streets-undead-bloodlines.zombie.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/band--karak-zorn-special-skills-fearless/unimplemented.khemri-cursed-of-karak-zorn.band.karak-zorn-special-skills-fearless` | `fear-immunity` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/cannibal-dwarfs--fear/unimplemented.khemri-cursed-of-karak-zorn.cannibal-dwarfs.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/karak-zorn-noble--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/shadowed--fear/unimplemented.khemri-cursed-of-karak-zorn.shadowed.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/shadowed--immune-to-psychology/unimplemented.khemri-cursed-of-karak-zorn.shadowed.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/khemri-cursed-of-karak-zorn/troll-slayer--death-oath/unimplemented.khemri-cursed-of-karak-zorn.troll-slayer.death-oath` | `psychology-immunity` | G02, G03 | consumer |
| `rule/trollheim/khemri-hobgoblin-raiders/khann--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/band--cause-fear/unimplemented.khemri-lahmian-brotherhood.band.cause-fear` | `cause-fear` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/band--immune-to-psychology/unimplemented.khemri-lahmian-brotherhood.band.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/beloved--accustomed-to-fear/unimplemented.khemri-lahmian-brotherhood.beloved.accustomed-to-fear` | `accustomed-to-fear` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/black-hounds--fear/unimplemented.khemri-lahmian-brotherhood.black-hounds.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/blood-sister--accustomed-to-fear/unimplemented.khemri-lahmian-brotherhood.blood-sister.accustomed-to-fear` | `accustomed-to-fear` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/blood-slaves--accustomed-to-fear/unimplemented.khemri-lahmian-brotherhood.blood-slaves.accustomed-to-fear` | `accustomed-to-fear` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/lackeys--accustomed-to-fear/unimplemented.khemri-lahmian-brotherhood.lackeys.accustomed-to-fear` | `accustomed-to-fear` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/lahmian-vampire--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/lahmian-vampire--undead/mechanic.undead` | `undead` | — | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/spirits--undead/mechanic.undead` | `undead` | — | consumer |
| `rule/trollheim/khemri-mages/archmage--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/khemri-mages/mechanical-beast--immune-to-psychology/unimplemented.khemri-mages.mechanical-beast.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/khemri-necromancers/band--cause-fear/unimplemented.khemri-necromancers.band.cause-fear` | `cause-fear` | — | consumer |
| `rule/trollheim/khemri-necromancers/band--immune-to-psychology/unimplemented.khemri-necromancers.band.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/khemri-necromancers/necromancer--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/khemri-necromancers/necromantic-abomination--undead/mechanic.undead` | `undead` | — | consumer |
| `rule/trollheim/khemri-necromancers/nehekharan-vultures--undead/mechanic.undead` | `undead` | — | consumer |
| `rule/trollheim/khemri-nomads-of-araby/sheikh--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/khemri-thieves-guild/guild-chief--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/band--cause-fear/unimplemented.khemri-tomb-guardians.band.cause-fear` | `cause-fear` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/band--immune-to-psychology/unimplemented.khemri-tomb-guardians.band.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/mortuary-acolytes--undead/mechanic.undead` | `undead` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/mortuary-priest--undead/mechanic.undead` | `undead` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/necrotect--undead/mechanic.undead` | `undead` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/skeleton-warriors--undead/mechanic.undead` | `undead` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/stone-golem--fear/unimplemented.khemri-tomb-guardians.stone-golem.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/stone-golem--immune-to-psychology/unimplemented.khemri-tomb-guardians.stone-golem.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/tomb-guardians--undead/mechanic.undead` | `undead` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/tomb-lord--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/tomb-lord--undead/mechanic.undead` | `undead` | — | consumer |
| `rule/trollheim/khemri-tomb-guardians/tomb-scorpions--living/unimplemented.khemri-tomb-guardians.tomb-scorpions.living` | `living` | — | consumer |
| `rule/trollheim/lustria-amazons/amazon-priestess--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/lustria-amazons/band--amazon-special-skills-animal-fury/unimplemented.lustria-amazons.band.amazon-special-skills-animal-fury` | `fear-immunity--scope--fear-immunity` | — | consumer |
| `rule/trollheim/lustria-clan-pestilens/plague-priest--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/lustria-clan-pestilens/rat-ogre--fear/unimplemented.lustria-clan-pestilens.rat-ogre.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/lustria-clan-pestilens/rat-ogre--stupidity/unimplemented.lustria-clan-pestilens.rat-ogre.stupidity` | `stupidity` | — | consumer |
| `rule/trollheim/lustria-dark-elves/cold-ones--fear/unimplemented.lustria-dark-elves.cold-ones.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/lustria-dark-elves/cold-ones--stupidity/unimplemented.lustria-dark-elves.cold-ones.stupidity` | `stupidity` | — | consumer |
| `rule/trollheim/lustria-dark-elves/dark-prince--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/lustria-high-elves/loremaster--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/lustria-lizardmen/band--cold-blooded/unimplemented.lustria-lizardmen.band.cold-blooded` | `cold-blooded--scope--psychology-test` | G03 | consumer |
| `rule/trollheim/lustria-lizardmen/kroxigor--fear/unimplemented.lustria-lizardmen.kroxigor.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/lustria-lizardmen/skink-priest--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/lustria-norse/jarl--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/lustria-norse/wulfen--fear/unimplemented.lustria-norse.wulfen.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/lustria-norse/wulfen--immune-to-psychology/unimplemented.lustria-norse.wulfen.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/lustria-pirates/pirate-captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/lustria-pygmies/cannibals--fear/unimplemented.lustria-pygmies.cannibals.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/lustria-pygmies/great-headhunter--fear/unimplemented.lustria-pygmies.great-headhunter.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/lustria-pygmies/great-headhunter--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/lustria-pygmies/silent-walker--fear/unimplemented.lustria-pygmies.silent-walker.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/lustria-pygmies/silent-walker--immune-to-psychology/unimplemented.lustria-pygmies.silent-walker.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/lustria-pygmies/wild-lunatics--immune-to-psychology/unimplemented.lustria-pygmies.wild-lunatics.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/lustria-savage-goblins/band--fear-of-pointy-ears/unimplemented.lustria-savage-goblins.band.fear-of-pointy-ears` | `fear-of-elves` | — | consumer |
| `rule/trollheim/lustria-savage-goblins/big-boss--second-in-command/unimplemented.lustria-savage-goblins.big-boss.second-in-command` | `leader-four--scope--leader-four` | — | consumer |
| `rule/trollheim/lustria-savage-goblins/witch-doctor--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/lustria-savage-goblins/zomblins--fear/unimplemented.lustria-savage-goblins.zomblins.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/lustria-savage-goblins/zomblins--immune-to-psychology/unimplemented.lustria-savage-goblins.zomblins.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/lustria-savage-goblins/zomblintua--fear/unimplemented.lustria-savage-goblins.zomblintua.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/lustria-savage-goblins/zomblintua--immune-to-psychology/unimplemented.lustria-savage-goblins.zomblintua.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/lustria-tileans/mercenary-captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/trollheim-cult-of-the-possessed/band--mutations-hideous/unimplemented.band-mutations-hideous` | `cause-fear--scope--cause-fear` | — | consumer |
| `rule/trollheim/trollheim-cult-of-the-possessed/darksouls--crazed/unimplemented.trollheim-cult-of-the-possessed.darksouls.crazed` | `automatic-leadership` | — | consumer |
| `rule/trollheim/trollheim-cult-of-the-possessed/magister--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/trollheim-cult-of-the-possessed/the-possessed--fear/unimplemented.trollheim-cult-of-the-possessed.the-possessed.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/trollheim-mercenaries/band--reikland-command-radius/unimplemented.trollheim-mercenaries.band.reikland-command-radius` | `leader-twelve` | — | consumer |
| `rule/trollheim/trollheim-mercenaries/mercenary-captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/trollheim-skaven-clan-eshin/assassin-adept--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/trollheim-skaven-clan-eshin/rat-ogre--fear/unimplemented.trollheim-skaven-clan-eshin.rat-ogre.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/trollheim-skaven-clan-eshin/rat-ogre--stupidity/unimplemented.trollheim-skaven-clan-eshin.rat-ogre.stupidity` | `stupidity` | — | consumer |
| `rule/trollheim/trollheim-undead/dire-wolves--fear/unimplemented.trollheim-undead.dire-wolves.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/trollheim-undead/dire-wolves--immune-to-psychology/unimplemented.trollheim-undead.dire-wolves.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/trollheim-undead/ghouls--fear/unimplemented.trollheim-undead.ghouls.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/trollheim-undead/vampire--fear/unimplemented.trollheim-undead.vampire.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/trollheim-undead/vampire--immune-to-psychology/unimplemented.trollheim-undead.vampire.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/trollheim-undead/vampire--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `rule/trollheim/trollheim-undead/zombies--fear/unimplemented.trollheim-undead.zombies.fear` | `cause-fear` | — | consumer |
| `rule/trollheim/trollheim-undead/zombies--immune-to-psychology/unimplemented.trollheim-undead.zombies.immune-to-psychology` | `psychology-immunity` | — | consumer |
| `rule/trollheim/trollheim-witch-hunters/flagellants--fanatical/unimplemented.trollheim-witch-hunters.flagellants.fanatical` | `automatic-leadership--scope--automatic-leadership` | — | consumer |
| `rule/trollheim/trollheim-witch-hunters/witch-hunter-captain--leader/mechanic.leader-six` | `leader-six` | — | consumer |
| `source/bands/mordheim/dark-elf-corsairs-mou/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified` | `frenzy` | G02, G03 | encargo explícito; consumer vacío |
| `source/bands/trollheim/lustria-high-elves/equipment-access.yaml/@/equipment_lists/0/items/15/notes/unclassified` | `recipient--scope--single-use` | — | consumer |
| `source/catalog/campaign/mutations.yaml/campaign.mutation.hideous/unclassified` | `hideous` | — | consumer |
| `source/catalog/campaign/serious-injuries.yaml/@/tables/0/results/16/note/unclassified` | `hardened` | — | consumer |
| `source/catalog/campaign/serious-injuries.yaml/@/tables/0/results/17/note/unclassified` | `horrible-scars` | — | consumer |
| `source/catalog/campaign/serious-injuries.yaml/@/tables/0/results/4/note/unclassified` | `madness-roll` | G02 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/core.yaml/hireling.dramatis.veskit.rule.unfeeling/unclassified` | `psychology-immunity` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1a.yaml/hireling.dramatis.countess-marianna-chevaux-vampire-assassin.rule.causes-fear/unclassified` | `cause-fear` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1a.yaml/hireling.dramatis.countess-marianna-chevaux-vampire-assassin.rule.immune-to-psychology/unclassified` | `psychology-immunity` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.abdul-alhazred-the-mad-sorcerer.rule.psychology/unclassified` | `psychology-immunity` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.khar-mel-the-djinn.rule.fear/unclassified` | `cause-fear` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.maximilian-the-mad.rule.fear/unclassified` | `cause-fear` | G03 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.maximilian-the-mad.rule.religious-fervour/unclassified` | `frenzy` | G02, G03 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/@/profiles/2/unresolved_references/1/unclassified` | `grizzled-veteran` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/@/profiles/2/unresolved_references/2/unclassified` | `death-without-a-face` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/hireling.dramatis.belandysh-condemned-champion-of-chen.rule.immune-to-psychology/unclassified` | `automatic-leadership` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/hireling.dramatis.belandysh-condemned-champion-of-chen.rule.immune-to-psychology/unclassified` | `psychology-immunity` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/hireling.dramatis.grand-master-ippan-shu.rule.immune-to-psychology/unclassified` | `psychology-immunity` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.aksho-akhash-the-vile-dreadwing-lord-of-the-carrion-throne.rule.coward-king/unclassified` | `coward-king` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.aksho-akhash-the-vile-dreadwing-lord-of-the-carrion-throne.rule.fear/unclassified` | `cause-fear` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.busty-gwen.rule.massively-built/unclassified` | `massively-built-optional-leadership` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.sigmund-spindle-the-harvester-of-flesh.rule.causes-fear/unclassified` | `cause-fear` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.sigmund-spindle-the-harvester-of-flesh.rule.maddened/unclassified` | `maddened` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-headless-horseman.rule.causes-fear/unclassified` | `cause-fear` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-headless-horseman.rule.immune-to-psychology/unclassified` | `psychology-immunity` | — | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.william-schakestange-master-bard.rule.songster/unclassified` | `songster-leadership-reroll` | — | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-2b.yaml/hireling.dramatis.snorri-nosebiter.rule.slayer-rules/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `source/catalog/hirelings/hired-swords/core.yaml/hireling.hired-sword.dwarf-troll-slayer.rule.deathwish/unclassified` | `psychology-immunity` | — | consumer |
| `source/catalog/hirelings/hired-swords/core.yaml/hireling.hired-sword.ogre-bodyguard.rule.fear/unclassified` | `cause-fear` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1a.yaml/hireling.hired-sword.beast-hunter.rule.beastmen-vengeance/unclassified` | `beastmen-vengeance` | G03 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-1a.yaml/hireling.hired-sword.roadwarden.rule.stern/unclassified` | `stern-rule` | — | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.bard.rule.songster/unclassified` | `songster-leadership-reroll` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.chameleon-skink.rule.cold-blooded/unclassified` | `cold-blooded` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.clan-skryre-rat-ogre.rule.fear/unclassified` | `cause-fear` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.old-prospector.rule.hardened/unclassified` | `fear-immunity` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.witch-hunter.rule.burn-the-witch/unclassified` | `burn-the-witch` | G03 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.witch-hunter.rule.in-sigmar-s-name/unclassified` | `fear-reroll` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.bone-goliath.rule.cause-fear/unclassified` | `cause-fear` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.bone-goliath.rule.immune-to-psychology/unclassified` | `psychology-immunity` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.hobgoblin-scout.rule.traitor/unclassified` | `traitor-hatred` | G03 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.pyromaniac.rule.crazed-firestarter/unclassified` | `never-charge` | G00 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.chaos-fury.rule.fear/unclassified` | `cause-fear` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.emissary-of-chaos.rule.patron/unclassified` | `patron-nurgle-fear` | G03 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.knight-of-the-white-wolf.rule.pride/unclassified` | `leader-ability` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.ogre-slave-master.rule.fear/unclassified` | `cause-fear` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.swashbuckler.rule.charismatic/unclassified` | `opposite-sex-charge-test` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.the-fallen-sister.rule.ashamed-and-afraid/unclassified` | `ashamed-and-afraid` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/1/equipment/fixed_items/0/notes/unclassified` | `beastlash-beastbane` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.albino-stormvermin.rule.hardened/mechanic.fear-immunity` | `fear-immunity` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.grave-warden.rule.hardened/mechanic.fear-immunity` | `fear-immunity` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.ogre-treasure-hunter.rule.fear/mechanic.causes-fear` | `cause-fear` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan.pending-duel` | `witch-finder--scope--inquisitor-state` | G02 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.sister-of-sigmar.rule.candle-tree/hireling.hired-sword.sister-of-sigmar.rule.candle-tree.relic` | `counts-as-holy-relic` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.war-priestess-of-myrmidia.rule.war-honed/mechanic.fear-immunity` | `fear-immunity` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.war-priestess-of-myrmidia.rule.war-honed/mechanic.fear-immunity` | `first-failed-leadership-reroll` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.war-priestess-of-myrmidia.rule.war-honed/mechanic.first-failed-leadership-reroll` | `fear-immunity` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.war-priestess-of-myrmidia.rule.war-honed/mechanic.first-failed-leadership-reroll` | `first-failed-leadership-reroll` | — | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.whaler.rule.hardened/mechanic.fear-immunity` | `fear-immunity` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/14/traits/1/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/14/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/15/traits/1/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/15/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/16/traits/1/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/16/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/17/traits/0/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/17/traits/1/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/17/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/18/traits/0/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/18/traits/1/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/18/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/19/traits/0/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/19/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/20/traits/0/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/20/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/21/traits/0/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/21/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/5/traits/2/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/hirelings/traits.yaml/@/traits/5/unclassified` | `trait-fact` | — | consumer |
| `source/catalog/rules/conditions.yaml/campaign.condition.causes-fear/trait.causes-fear` | `cause-fear` | — | consumer |
| `source/catalog/rules/conditions.yaml/campaign.condition.immune-to-fear/mechanic.fear-immunity` | `fear-immunity` | — | consumer |
| `source/catalog/rules/conditions.yaml/campaign.condition.stupidity/trait.stupidity` | `stupidity` | — | consumer |
| `source/catalog/rules/conditions.yaml/condition.cold-blooded/mechanic.cold-blooded-leadership` | `cold-blooded-leadership` | — | consumer |
| `source/catalog/rules/conditions.yaml/condition.cold-blooded/mechanic.cold-blooded-psychology` | `cold-blooded-psychology` | — | consumer |
| `source/catalog/rules/conditions.yaml/condition.immune-to-psychology/mechanic.psychology-immunity` | `psychology-immunity` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.barbarian-courage/unclassified` | `barbarian-courage--scope--fear-reroll` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.berserkers/unclassified` | `frenzy` | G02, G03 | encargo explícito; consumer vacío |
| `source/catalog/rules/special-rules.yaml/shared-rule.bestial/unclassified` | `psychology-immunity--scope--psychology-immunity` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.cause-fear-2/unclassified` | `cause-fear` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.censer-bearer/unclassified` | `frenzy` | G02, G03 | encargo explícito; consumer vacío |
| `source/catalog/rules/special-rules.yaml/shared-rule.deathwish/unclassified` | `psychology-immunity--scope--psychology-immunity` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.ere-we-go/unclassified` | `ere-we-go` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.fear/unclassified` | `cause-fear` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.immune-to-psychology-4/unclassified` | `psychology-immunity` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.immune-to-psychology/unclassified` | `psychology-immunity` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.leader/unclassified` | `leader-six` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.stupidity-2/unclassified` | `stupidity` | — | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.stupidity/unclassified` | `stupidity` | — | consumer |

## Claves de apoyo de otros responsables

| id | clause_id | Responsable principal | Referencia de asignación |
| --- | --- | --- | --- |
| `mechanic/mechanic.beauty-of-the-sea` | `whole` | G06 | consumer |
| `mechanic/mechanic.mesmerising-dance` | `whole` | G06 | consumer |
| `mechanic/mechanic.savage-fury` | `whole` | G06 | consumer |
| `rule/mordheim/adventurers-kaz/barbarian--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/amazons-mordheim/totem-warriors--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/bretonnian-chapel-guard/knights-errant--impetuous/unimplemented.bretonnian-chapel-guard.knights-errant.impetuous` | `impetuous-avoid-compulsion` | G06 | consumer |
| `rule/mordheim/bretonnian-chapel-guard/knights-errant--impetuous/unimplemented.bretonnian-chapel-guard.knights-errant.impetuous` | `impetuous-movement` | G06 | consumer |
| `rule/mordheim/druchii-mic/witch-elves--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/grave-robbers-sylv/band--special-skill-instinctual-violence/unimplemented.grave-robbers-sylv.special-skill.instinctual-violence` | `fear-immunity` | G06 | consumer |
| `rule/mordheim/khorne-raiders-sar/cannibal-boys--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/maneaters/sabretusks--feral-instinct/unimplemented.maneaters.sabretusks.feral-instinct` | `feral-instinct--scope--leadership-test` | G06 | consumer |
| `rule/mordheim/masters-of-horror-sylv/the-bitten--transform/unimplemented.masters-of-horror-sylv.the-bitten.transform` | `transformation-state--scope--transformation-state` | G06 | consumer |
| `rule/mordheim/night-goblins-web/band--mad-cap-masters/unimplemented.night-goblins-web.band.mad-cap-masters` | `mad-cap-masters` | G06 | consumer |
| `rule/mordheim/night-goblins-web/shaman--fungus-brew/unimplemented.night-goblins-web.shaman.fungus-brew` | `fungus-loony` | G06 | consumer |
| `rule/mordheim/norse-explorers-btb/beserkers--berserkers/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/norse-explorers-lustria/beserkers--berserkers/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-champion--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/skaven-of-clan-pestilens-mou/plague-priest--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/mordheim/snotlings-web/wheelo--combat/mechanic.wheelo-impact` | `whole` | G06 | consumer |
| `rule/mordheim/tomb-guardians/acolytes--undead/unimplemented.tomb-guardians.acolytes.undead` | `undead` | G04 | encargo explícito; consumer vacío |
| `rule/mordheim/watchmen-mim/private-sleuth--scryer/trait.re-roll-melee` | `melee-reroll` | G06 | consumer |
| `rule/trollheim/chaos-streets-mordheim-inhabitants/lunatics--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/trollheim/chaos-streets-undead-bloodlines/lahmia-vampire--enchanting-beauty/unimplemented.chaos-streets-undead-bloodlines.lahmia-vampire.enchanting-beauty` | `enchanting-beauty` | G06 | consumer |
| `rule/trollheim/khemri-lahmian-brotherhood/skeleton-warriors--undead/unimplemented.khemri-lahmian-brotherhood.skeleton-warriors.undead` | `undead` | G04 | encargo explícito; consumer vacío |
| `rule/trollheim/khemri-necromancers/skeleton-warriors--undead/unimplemented.khemri-necromancers.skeleton-warriors.undead` | `undead` | G04 | encargo explícito; consumer vacío |
| `rule/trollheim/khemri-tomb-guardians/stone-golem--animated/unimplemented.khemri-tomb-guardians.stone-golem.animated` | `animated` | G04 | encargo explícito; consumer vacío |
| `rule/trollheim/lustria-amazons/amazon-totem-warriors--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/trollheim/lustria-norse/berserkers--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `rule/trollheim/lustria-pygmies/wild-lunatics--lunatics/unimplemented.lustria-pygmies.wild-lunatics.lunatics` | `frenzy` | G06 | consumer |
| `rule/trollheim/lustria-savage-goblins/red-teeth--frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `source/catalog/campaign/magic.yaml/spell.commands.raise-our-insignia/unclassified` | `raise-our-insignia--scope--supplied-reroll` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.crow-master-the.rule.crow-master/unclassified` | `needle-and-thread--scope--mouth-sewn` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.heinrich-altdorf-schmidt.rule.snake-fear/unclassified` | `snake-fear` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.busty-gwen.rule.massively-built/unclassified` | `leadership-distraction` | G06 | consumer |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-foole.rule.unhinged/unclassified` | `psychology-immunity` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/dramatis-personae/grade-2a.yaml/hireling.dramatis.the-headless-horseman.rule.undead/unclassified` | `undead` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.chaos-fury.rule.daemonic-mind/unclassified` | `psychology-immunity` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-2a.yaml/hireling.hired-sword.dwarf-slayer-pirate.rule.slayer-pirate/unclassified` | `deathwish--scope--deathwish-psychology` | G04 | encargo explícito; consumer vacío |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr.pending-duel` | `augur-psychology-immunity` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr/hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr.pending-duel` | `augur-strength-reduction` | G04 | consumer |
| `source/catalog/rules/conditions.yaml/campaign.condition.frenzy/trait.frenzy` | `frenzy` | G06 | consumer |
| `source/catalog/rules/special-rules.yaml/shared-rule.undead/unclassified` | `undead` | G04 | encargo explícito; consumer vacío |

## Base de esta asignación

Preparación: 2026-10-21. HEAD: `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` más cambios locales actuales. CSV SHA-256: `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`. No es un certificado de ejecución.
