# Encargos del motor vectorial — índice y orden de ejecución

Estos ficheros conservan los encargos y la propiedad del plan del motor. Son instrucciones y referencias de diseño, no un estado actual ni evidencia de ejecución. El motor se recibe como implementado; los resultados de cada fase deben consultarse en sus entregas y en el registro vigente, sin relanzar el portado por leer estos documentos.

## Premisas

El modular se considera completado y validado. Se porta su implementación existente a NumPy y se conservan sus contratos. La fase 1 desarrolla solo las pruebas mínimas imprescindibles; fase 2 comprueba paridad reutilizando las baterías actuales; fase 3 optimiza la versión correcta. El plan general sigue en [PLAN_IMPLEMENTACION.md](PLAN_IMPLEMENTACION.md).

La [renovación de paridad](parity_update/PARITY_BATTERY_RENOVATION.md) tiene un
[encargo vigente propio](parity_update/PROMPTS_AGENTES.md): reutilizar el catálogo
ampliado y comparar estadísticamente resultados de duelos reales. No exige
sondas de eventos internos ni nuevas interfaces del motor. La adaptación está
pendiente, según [P03](parity_update/P03-deliverable.md), y su encargo inmediato
es estático. P04/P05 serán campañas posteriores con autorización de ejecución.
**G07 usa la batería histórica aplicable y no depende del rework ni equivale a
P05.** Su evidencia queda limitada a la versión y batería realmente ejecutadas;
la campaña renovada no reabre ese cierre ni hereda su cobertura automáticamente.

El registro canónico de progreso es `sources/knowledge/verification/clause-contracts.csv`. Los anexos solo asignan sus claves a responsables. No son otra clasificación semántica ni otro registro de estados.

## Ficheros asignables

| Fichero | Trabajo | Cláusulas principales |
| --- | --- | ---: |
| [G00_BASE_ADMISION_Y_COORDINACION.md](G00_BASE_ADMISION_Y_COORDINACION.md) | Base, admisión por backend y coordinación | 4 |
| [G01_COMPILACION_COMPARTIDA_Y_ENLACES.md](G01_COMPILACION_COMPARTIDA_Y_ENLACES.md) | Compilación compartida, construcción y enlaces existentes | 1396 |
| [G02_ESTADO_RECURSOS_Y_MUTACIONES.md](G02_ESTADO_RECURSOS_Y_MUTACIONES.md) | Estado por simulación, recursos, características y mutaciones | 12 |
| [G03_OPERADORES_Y_CONTEXTO_DE_ATAQUE.md](G03_OPERADORES_Y_CONTEXTO_DE_ATAQUE.md) | Operadores y contexto de ataque, defensas y prioridad | 941 |
| [G04_ATAQUES_EQUIPO_Y_REACCIONES.md](G04_ATAQUES_EQUIPO_Y_REACCIONES.md) | Pools de ataques, equipo efectivo, daño y reacciones | 280 |
| [G05_PSICOLOGIA_Y_LIDERAZGO_LOCAL.md](G05_PSICOLOGIA_Y_LIDERAZGO_LOCAL.md) | Psicología y liderazgo local vectorizados | 637 |
| [G06_RONDAS_RECUPERACION_E_INTEGRACION.md](G06_RONDAS_RECUPERACION_E_INTEGRACION.md) | Rondas, recuperación, duración e integración completa | 187 |
| [G07_PARIDAD_CONTRA_MODULAR.md](G07_PARIDAD_CONTRA_MODULAR.md) | Fase 2: paridad contra el modular aceptado | Conjunto integrado |
| [G08_OPTIMIZACION_MEDIDA.md](G08_OPTIMIZACION_MEDIDA.md) | Fase 3: optimización medida conservando paridad | Conjunto integrado |

## Orden y paralelismo real

1. **Etapa A:** G00 y G01 pueden empezar en paralelo. G00 fija admisión y base; G01 enlaza lo ya compartido y no toca producción.
2. **Etapa B:** G02 completa y congela estado e inicialización, después de G00. G01 puede continuar.
3. **Etapa C:** G03, G04 y G05 se ejecutan en paralelo desde la misma base integrada G00+G02, con tres implementadores y un coordinador. Los tres tienen propiedad de archivos disjunta. G01 debe haber entregado antes sus dependencias de runtime o continuarlas mediante el coordinador sin ocupar un cuarto implementador.
4. **Etapa D:** tras reunir la tanda, G06 integra orden de rondas y todas las conexiones. G03/G04/G05 resuelven peticiones concretas de sus archivos en turnos de escritura coordinados. No corren tres editores sobre el driver.
5. **Fase 2:** G07 ejecuta paridad sobre la revisión integrada. Las divergencias vuelven a su propietario; no se ejecuta el portado completo de nuevo.
6. **Fase 3:** G08 mide y optimiza la versión que ha pasado G07. El coordinador cede cada archivo afectado al único optimizador activo.

Los nombres de etapa no crean nuevas fases del producto: A–D pertenecen a la implementación de la fase 1.

### Archivos compartidos

- `_driver.py`: G00 solo admisión inicial → G02 solo inicialización/observación → G06 integración de rondas. La propiedad pasa en ese orden, nunca en paralelo.
- `_types.py`: G02 antes de la tanda; durante ella, los cambios adicionales se solicitan al coordinador. G03/G04/G05 no lo editan.
- `_operators.py`: G03; `_attacks.py` y `_equipment.py`: G04; `_psychology.py` y `_leadership.py`: G05.
- La fachada `vectorized/__init__.py`, las conexiones a admisión y el CSV quedan coordinados por G00. Las exportaciones posteriores se aplican al integrar entregas.
- Los archivos de tests autorizados están repartidos. Cualquier cambio a un test compartido se canaliza por su propietario.

## Cómo se asignaron las cláusulas

Se reutilizaron literalmente los consumidores existentes, normalizando únicamente sus distintas formas de referencia (`modular/foo.py::función` y `mordheim_combat.modular.foo.función`). No se infirió equivalencia de reglas ni soporte NumPy.

Para cláusulas con varias capas, el responsable principal es el que debe asegurar la consecuencia completa: rondas → ataques/equipo → psicología/liderazgo → operadores → estado → admisión → compartido. Los otros consumidores aparecen como apoyos. Esta precedencia organiza entregas; no impone el orden de las reglas en ejecución.

Las cláusulas sin consumidor se distinguen en los anexos. Los casos de runtime identificados durante la preparación tienen un encargo explícito basado en el contrato ya existente; las referencias compartidas o no concretadas están en G01 para recuperar su enlace desde la implementación/evidencia aceptadas. No se presuponen resueltas por estar en ese grupo. Si G01 localiza una consecuencia de runtime adicional, el coordinador transfiere expresamente esa clave y su referencia al propietario antes de cerrar su estado.

Las cláusulas con fuentes históricas o `proposed.*` conservan su identidad. No hay que interpretar de nuevo ni construir una funcionalidad que el modular aceptado no tenga. Se sigue el comportamiento existente.

## CSV y cierre de una entrega

El agente propone claves y evidencia; solo el coordinador escribe mediante la utilidad mantenida. Conserva `status.native` y todos los valores ajenos. `in_progress` al asignar ejecución, `implemented` solo cuando el comportamiento esté conectado e integrado, `verified` después de G07 y `blocked` con causa concreta en notas. No se cambia ningún estado por crear estos ficheros.

Una clave principal no puede cerrarse si falta su contribución de apoyo o la llamada desde el driver. Las cláusulas de construcción compartida se conservan en el alcance sin exigir código duplicado ni pruebas individuales nuevas.

## Comprobación de integridad de esta preparación

- Filas del registro consultado: **4556**.
- Cláusulas admitidas (`YES`): **3457**.
- Claves principales asignadas: **3457**, una vez cada una, sin duplicados.
- Filas de otros alcances, sin asignación de portado: **1099**.
- Cláusulas admitidas con `consumer` vacío: **189**, identificadas en sus encargos.
- Ninguna asignación es una acreditación de soporte; se mantiene el seguimiento inicial del CSV.
- CSV SHA-256 antes y después de preparar: `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`.
- HEAD de preparación: `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` **más cambios locales**; las copias de agentes deben incluir esa base completa.

Estos son recuentos de la preparación, no porcentajes actuales de implementación. Antes de lanzar agentes, comparar las claves, alcance y consumidores vigentes. Los cambios solo en estados/notas no exigen regenerar el reparto.

## Ficheros de entrega

Cada agente debe crear o actualizar su propio `TMP_VECTORIAL_ENGINE_2A2B/Gxx-deliverable.md` (G00 a G08) en la copia donde trabaja. El coordinador recoge esos documentos al integrar las entregas; no depende de copiar conversaciones. El documento es obligatorio también para resultados parciales o bloqueados y se actualiza en las reanudaciones.

Debe contener base/revisión, cambios y archivos, claves cubiertas, conexiones pendientes, comprobaciones realmente ejecutadas, casos nuevos justificados y bloqueos. Distingue implementación, integración y verificación. El CSV sigue siendo el registro canónico de progreso; estos ficheros conservan la evidencia y el traspaso de trabajo.

## Lanzamiento posterior

Cada fichero G00–G08 empieza con un **Prompt para lanzar el agente** listo para copiar. El bloque apunta a su propio encargo, al índice, al plan y al CSV, y remarca implementación desde el modular validado, pruebas nuevas mínimas, propiedad exclusiva y entrega al coordinador. Los prompts de G07 y G08 concretan su fase de paridad u optimización.

Entregar al agente el fichero completo de su grupo y una copia aislada de la base común. El propio fichero contiene instrucciones, archivos permitidos, referencias, entrega y claves. No lanzar todos los grupos a la vez ni usar solo el número de filas para repartir carga: una cláusula puede depender de varias capas y muchas filas pueden compartir una implementación.
