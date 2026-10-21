# G00 — Base, admisión por backend y coordinación

## Prompt para lanzar el agente

Copia el bloque completo al lanzar el agente. Las condiciones de inicio forman parte del encargo; este prompt no autoriza saltarse sus dependencias.

```text
Realiza el encargo G00 (fase 1: implementación) del motor vectorial NumPy.

INFORMACIÓN QUE DEBES LEER
1. El fichero de trabajo completo:
   D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK\TMP_VECTORIAL_ENGINE_2A2B\G00_BASE_ADMISION_Y_COORDINACION.md
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
Etapa A. Ejecutar primero; puede coincidir con G01. Antes de G02 y de la tanda de implementación.
Comprueba la entrega de esas dependencias. Si falta alguna, comunica la dependencia concreta;
puedes avanzar con lectura o trabajo independiente, pero no inventes interfaces ni declares
completada una conexión que todavía no existe.

OBJETIVO CONCRETO
Preparar la base de implementación y la admisión independiente de NumPy y Cython. Recorre los llamadores de require_optimized_support y compile_duel_plan; mantén el nativo rechazando capacidades todavía no portadas. Ajusta únicamente las conexiones de backend autorizadas. Define y entrega los puntos de extensión que G02 necesita. No implementes las funcionalidades asignadas a G03/G04/G05 ni aproveches para rediseñar el motor.

REFERENCIAS Y COMPROBACIONES QUE DEBES REUTILIZAR
Usa kernel.py, el driver vectorial, la fachada y los llamadores enumerados en el encargo. Reutiliza test_kernel_plan.py y test_backends.py; añade solo el comprobante imprescindible para distinguir NumPy habilitado de nativo todavía rechazado.

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
TMP_VECTORIAL_ENGINE_2A2B/G00-deliverable.md
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

**Inicio:** Etapa A. Ejecutar primero; puede coincidir con G01. Antes de G02 y de la tanda de implementación.

**Cláusulas principales:** 4. **Cláusulas de apoyo:** 2.

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

Crea o actualiza `TMP_VECTORIAL_ENGINE_2A2B/G00-deliverable.md` en la raíz de tu copia de trabajo. Es la entrega persistente obligatoria de este grupo y está permitida además de los archivos de producción autorizados. No basta con un mensaje en el chat.

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

- `TMP_VECTORIAL_ENGINE_2A2B/G00-deliverable.md` — documento de entrega obligatorio, propietario exclusivo G00.
- `packages/python/combat-engine/mordheim_combat/kernel.py`
- `packages/python/combat-engine/mordheim_combat/vectorized/__init__.py`
- `packages/python/combat-engine/mordheim_combat/vectorized/_driver.py (solo adaptación inicial de admisión; cesión posterior a G02 y G06)`
- `apps/combat-lab/mordheim_combat_lab/application/settings.py (solo selección de backend)`
- `apps/combat-lab/mordheim_combat_lab/cli/calibration.py (solo llamada a admisión)`
- `apps/combat-lab/mordheim_combat_lab/verification/parity/_replay.py (solo selección de backend)`
- `tests/python/combat/test_kernel_plan.py`
- `tests/python/combat/vectorized/test_backends.py`

Cualquier archivo no enumerado queda fuera de tu propiedad. Los módulos nuevos expresamente permitidos solo se crean si el portado los necesita. Los tests compartidos que no son tuyos se pueden ejecutar, pero no editar.

## Implementación de referencia que debes seguir

- `kernel.py::require_optimized_support`
- `kernel.py::compile_duel_plan`
- `_driver.py::simulate_duel`
- `_driver.py::simulate_duel_parallel`
- `_driver.py::_simulate_batch_core`

Estas referencias son puntos de entrada; sigue sus llamadas para reproducir el comportamiento completo, sin releer las fuentes de reglas.

## Trabajo concreto

1. Separar admisión NumPy/nativa conservando las restricciones actuales en llamadas antiguas sin selección explícita. La nueva ruta NumPy habilitará cada comportamiento solo al integrarse su implementación.
2. Recorrer todos los llamadores de `require_optimized_support` y `compile_duel_plan`, incluyendo simulación, reproducción, configuración y calibración. La ruta nativa mantendrá sus rechazos aunque NumPy avance. No modificar Cython.
3. Mantener las interfaces públicas de solicitudes, compilados y resultados. Mantener las reexportaciones históricas al incorporar helpers posteriores; no inventar otra API de motor.
4. Acordar sobre la base actual los puntos de extensión de estado y los argumentos que G03/G04/G05 necesitarán. G02 implementa los campos; este grupo no escribe `_types.py`.
5. Integrar entregas, resolver cruces de cláusulas y conservar el único control del CSV. Las listas de claves son encargos, no acreditación automática.
6. Ceder explícitamente `_driver.py` a G02 cuando termine esta adaptación y, después de G02, a G06. No editarlo durante el trabajo de esos propietarios.

## Comprobación mínima

Reutilizar `test_kernel_plan.py` y `test_backends.py` con selección de casos afectados. Normalmente basta adaptar la expectativa de admisión y un comprobante que distinga NumPy habilitado de nativo rechazado. No modificar expectativas de reglas modulares.

## Criterio de entrega

La selección de backend es explícita donde corresponde, el nativo no gana soporte accidental y existe una base compatible para G02. Las capacidades sin portado continúan rechazadas.

## Claves principales asignadas

| id | clause_id | Apoyos | Referencia de asignación |
| --- | --- | --- | --- |
| `rule/mordheim/call-of-the-night-haint-mim/corpse-master--magical-void/mechanic.magical-void` | `whole` | — | consumer |
| `rule/mordheim/dreamwalkers-cult-of-morr-fbg/andanti--andanti-knowledge/mechanic.andanti-knowledge` | `whole` | — | consumer |
| `rule/mordheim/dwarf-slayer-cult-web/band--slayer-rules/profile.equipment-restrictions` | `deathwish--scope--deathwish-psychology` | — | consumer |
| `rule/mordheim/ghost-pirates-sar/sea-singer--beauty-of-the-sea/mechanic.beauty-of-the-sea` | `whole` | — | consumer |

## Claves de apoyo de otros responsables

| id | clause_id | Responsable principal | Referencia de asignación |
| --- | --- | --- | --- |
| `source/catalog/campaign/exploration-and-income.yaml/campaign.magical-artefact.count-of-ventimiglias-misericordia/unclassified` | `misericordia-injury` | G04 | consumer |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.pyromaniac.rule.crazed-firestarter/unclassified` | `never-charge` | G05 | encargo explícito; consumer vacío |

## Base de esta asignación

Preparación: 2026-10-21. HEAD: `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` más cambios locales actuales. CSV SHA-256: `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`. No es un certificado de ejecución.
