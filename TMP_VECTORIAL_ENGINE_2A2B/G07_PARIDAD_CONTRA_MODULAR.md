# G07 — Fase 2: paridad contra el modular aceptado

**Alcance de aceptación del plan del motor.** G07 compara NumPy contra el modular
con la batería histórica aplicable y registra la versión y los límites reales de
su evidencia. El motor se recibe como implementado; este documento no acredita
por sí solo que G07 se haya ejecutado o aprobado ni ordena repetirlo.

La [renovación estadística](parity_update/PARITY_BATTERY_RENOVATION.md) es otro
trabajo: reutiliza escenarios ampliados sin exigir instrumentación interna.
Su adaptación P03 está pendiente y P04/P05 serán campañas posteriores. **G07 no
depende de P03/P04, no equivale a P05 y no reabre su cierre para esperar al rework.**
No certificar los nuevos perfiles con evidencia de la batería histórica.

## Prompt para lanzar el agente

Copia el bloque completo al lanzar el agente. Las condiciones de inicio forman parte del encargo; este prompt no autoriza saltarse sus dependencias.

```text
Realiza el encargo G07 (fase 2: paridad) del motor vectorial NumPy.

INFORMACIÓN QUE DEBES LEER
1. El fichero de trabajo completo:
   D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK\TMP_VECTORIAL_ENGINE_2A2B\G07_PARIDAD_CONTRA_MODULAR.md
   Contiene archivos permitidos, referencias modulares exactas, trabajo concreto, comprobaciones,
   criterios de entrega y anexos con las claves principales y de apoyo que te corresponden.
2. El orden de ejecución y la propiedad de archivos:
   D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK\TMP_VECTORIAL_ENGINE_2A2B\README.md
3. El plan acordado de tres fases:
   D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK\TMP_VECTORIAL_ENGINE_2A2B\PLAN_IMPLEMENTACION.md
4. docs/reference/verification.md y las entregas integradas G00–G06.
   El plan parity_update/PARITY_BATTERY_RENOVATION.md solo delimita el rework
   independiente: sus perfiles pendientes no son una dependencia de G07.
5. AGENTS.md y las instrucciones adicionales aplicables de la copia de trabajo.

Trabaja en la copia aislada asignada por el coordinador. Las rutas anteriores identifican el
repositorio original; si tu copia está en otra ubicación, resuelve los mismos archivos respecto
a su raíz. Conserva la base completa entregada, incluidos cambios todavía sin commit.

CONDICIÓN DE INICIO
Tras la integración de fase 1 (G00–G06), con una versión fija y la batería
histórica identificada; sin implementadores escribiendo en paralelo.
Comprueba la entrega de esas dependencias. Si falta alguna, comunica la dependencia concreta;
puedes avanzar con lectura o trabajo independiente, pero no inventes interfaces ni declares
completada una conexión que todavía no existe.

OBJETIVO CONCRETO
Ejecutar la aceptación G07 con la batería histórica aplicable sobre la versión
integrada de G00–G06. El modular validado es el oráculo; selecciona NumPy
explícitamente y reutiliza evidencia vigente sin repetir campañas innecesarias.
No reconstruyas catálogo ni selección de backend existentes. Investiga
divergencias y devuelve correcciones a sus propietarios; no audites de nuevo el
modular ni optimices. Registra resultados y límites en G07-deliverable.md.
No ejecutar P05 ni esperar los perfiles renovados para cerrar este alcance.

REFERENCIAS Y COMPROBACIONES QUE DEBES REUTILIZAR
Lee docs/reference/verification.md y la infraestructura parity/_statistical.py, _deep.py, _truncations.py y cli/scenarios.py enumerada en el encargo. Ejecutar muchas pruebas existentes es parte de esta fase; desarrollar nuevas baterías no lo es. Extiende o añade solo un caso mínimo cuando demuestres un hueco. Conserva muestras y tolerancias; no las debilites ni presentes búsquedas de tags como evidencia ejecutada.

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
TMP_VECTORIAL_ENGINE_2A2B/G07-deliverable.md
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

**Inicio:** tras G00–G06 integrados, con versión fija y batería histórica
identificada; sin implementadores escribiendo en paralelo. Sin dependencia de P04.

**Cláusulas principales:** 0. **Cláusulas de apoyo:** 0.

Este encargo trabaja sobre el conjunto integrado de claves de G00–G06; no añade otra partición ni duplica su propiedad.

## Instrucciones obligatorias para el agente

- Este documento define un encargo, no evidencia de ejecución ni una orden de repetirlo. El motor modular se considera implementado y validado.
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

Crea o actualiza `TMP_VECTORIAL_ENGINE_2A2B/G07-deliverable.md` en la raíz de tu copia de trabajo. Es la entrega persistente obligatoria de este grupo y está permitida además de los archivos de producción autorizados. No basta con un mensaje en el chat.

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

- `TMP_VECTORIAL_ENGINE_2A2B/G07-deliverable.md` — documento de entrega obligatorio, propietario exclusivo G07.
- `apps/combat-lab/mordheim_combat_lab/verification/parity/*.py (solo adaptación necesaria de NumPy y evidencia)`
- `apps/combat-lab/mordheim_combat_lab/cli/commands.py (selección explícita de backend para parity)`
- `apps/combat-lab/mordheim_combat_lab/cli/scenarios.py (solo huecos de comparación demostrados)`
- `tests/python/verification/test_parity.py`
- `tests/python/verification/test_truncation_parity.py`
- `tests/python/verification/test_duel_replay.py`
- `tests/python/cli/test_benchmarking.py`

Cualquier archivo no enumerado queda fuera de tu propiedad. Los módulos nuevos expresamente permitidos solo se crean si el portado los necesita. Los tests compartidos que no son tuyos se pueden ejecutar, pero no editar.

## Implementación de referencia que debes seguir

- `apps/combat-lab/mordheim_combat_lab/verification/parity/_statistical.py`
- `apps/combat-lab/mordheim_combat_lab/verification/parity/_deep.py`
- `apps/combat-lab/mordheim_combat_lab/verification/parity/_truncations.py`
- `apps/combat-lab/mordheim_combat_lab/cli/scenarios.py::deep_test_scenarios`

Estas referencias son puntos de entrada; sigue sus llamadas para reproducir el comportamiento completo, sin releer las fuentes de reglas.

## Trabajo concreto

1. Seleccionar NumPy explícitamente en el comando histórico sin `--profile`; no cambiar defaults ni reconstruir la selección existente.
2. Reutilizar checks exactos, reproducciones, comparaciones estadísticas y horizontes de la batería histórica aplicable. Identificar selección y revisión, sin iniciar otra revisión semántica ni depender de los perfiles renovados pendientes.
3. Ejecutar G07 con muestras y horizontes de aceptación vigentes. Diagnosticar diferencias con el menor caso aplicable, sin rebajar tolerancias ni convertir búsquedas de tags en evidencia ejecutada. P05 conserva su campaña independiente.
4. Añadir cero escenarios si la batería cubre el portado. Si existe un hueco, extender un caso existente o añadir únicamente el comprobante mínimo. No construir otra batería modular.
5. Para una divergencia, reproducirla y devolver corrección concreta al propietario G02/G03/G04/G05/G06; no editar sus archivos simultáneamente. Una vez entregada, integrar y reejecutar lo afectado.
6. Entregar al coordinador evidencia por familias y claves para actualizar de implemented a verified. Los anexos de G00–G06 constituyen el universo, no nuevas filas en otro registro.

## Comprobación mínima

Esta fase compara NumPy con el modular mediante la batería histórica sobre una
base fija. Reutiliza evidencia válida de ese mismo alcance y no repite campañas
sin cambios que lo justifiquen. No añade tests modulares ni recalifica la
verificación modular aceptada. El rework y P04/P05 conservan sus propios encargos;
editar esta documentación no autoriza ejecutar ninguna campaña.

## Criterio de entrega

Comparaciones aplicables y matriz final/horizontes pasan sobre la misma versión, sin divergencias conocidas. El informe distingue evidencia estadística de comprobaciones exactas y no acredita nativo.

## Claves principales asignadas

No tiene claves en este anexo.

## Claves de apoyo de otros responsables

No tiene claves en este anexo.

## Base de esta asignación

Preparación: 2026-10-21. HEAD: `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` más cambios locales actuales. CSV SHA-256: `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`. No es un certificado de ejecución.
