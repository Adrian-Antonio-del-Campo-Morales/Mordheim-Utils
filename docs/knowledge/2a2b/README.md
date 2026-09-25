# 2A/2B — checklist de integración y coordinación

## Punto de inicio y alcance

- Rama de trabajo: `2A2B`; remoto: `origin/2A2B`.
- Snapshot publicado: `9118ca2` (`chore: snapshot 2A2B starting point`), 25 de septiembre de 2026. Incluye los cambios locales existentes y la historia anterior; no certifica que sus tests pasen.
- La documentación de este directorio se publica después del snapshot, en un commit separado. No se ha ejecutado la integración al redactarla.
- Alcance: 19 bandas de 2A y 60 de 2B y sus catálogos; automatizar todos los efectos aplicables a los flujos existentes de construcción, combate y campaña, en los consumidores correspondientes.
- Fuera de esta ejecución: crear sistemas de despliegue, ocultación, disparo o resolución de magia de batalla. Sus reglas se conservan completas y con limitaciones explícitas; no se marcan como implementadas.
- Mantener staging y herramientas de ingesta. La aplicación seguirá leyendo exclusivamente `sources/knowledge`.
- La ejecución de las tareas termina en commits **locales** en `2A2B`. La autorización de push del snapshot y de esta documentación no autoriza publicar implementaciones posteriores ni cambiar `main`.

El documento es una checklist viva, no un certificado. Solo el coordinador cambia sus estados. Cada tarea tiene un [documento auxiliar](tasks/) con pasos y prompts de ejecución, revisión y reanudación.

## Estado y protocolo de trabajo

Estados válidos: `pendiente`, `en progreso`, `bloqueada`, `en revisión`, `completada`. La casilla `[x]` se usa exclusivamente para `completada`; el resto permanece `[ ]`. No usar `[~]`, que no es una casilla Markdown estándar.

1. El coordinador verifica las dependencias, identifica la revisión de entrada y asigna un agente y un conjunto explícito de archivos. Anota la reserva en la tabla antes de despachar el prompt.
2. El agente lee este documento y su tarea, inspecciona instrucciones locales, rama y diff. Si el estado difiere de la entrega, informa antes de tocar archivos solapados.
3. El agente trabaja solo en los archivos asignados. Una ruta nueva o compartida necesita reasignación del coordinador; no se resuelve editando y esperando que Git lo mezcle.
4. Si necesita una decisión, registra evidencia y alternativas en su entrega. Se bloquea la unidad dependiente, no los frentes independientes. Nunca inventar reglas para cerrar un gate.
5. Al terminar entrega archivos, resultados, revisión, cambios de contrato, riesgos y tareas desbloqueadas. No marca la tarea como completada ni hace commit/push por su cuenta.
6. El coordinador pasa a `en revisión`, asigna un revisor distinto cuando haya un cambio semántico o de datos, comprueba los criterios y acepta o devuelve la tarea.
7. Solo tras aceptar registra `completada`, evidencia y commit si existe; libera los archivos. Una modificación posterior que invalide evidencia reabre las tareas afectadas.

Una tarea se puede fraccionar en lotes por mecanismo dentro de su documento auxiliar, sin crear un gestor nuevo. Cada lote tendrá responsable, entradas, archivos, prueba de cierre y estado. Si se necesita otro agente para un lote, se usa el mismo prompt con esos parámetros concretos, conservando las restricciones de la tarea madre.

### Tabla de reservas activas

Vacía al publicar el plan. Añadir una fila antes de iniciar cualquier trabajo.

| Tarea/lote | Agente | Revisión de entrada | Archivos reservados | Inicio UTC | Estado/última entrega |
|---|---|---|---|---|---|
| — | — | — | — | — | Sin trabajos de implementación iniciados |

### Plantilla de entrega del agente

```text
Tarea/lote:
Revisión de entrada y revisión probada (o HEAD + lista del diff):
Archivos modificados:
Decisiones y fuentes:
Pasos completados / pendientes:
Comandos ejecutados y códigos de salida:
Casos realmente cubiertos y omisiones:
Ubicación de evidencia reproducible:
Bloqueos y dependencias afectadas:
Archivos que pueden liberarse:
Siguiente acción recomendada al coordinador:
```

Los informes generados no se editan a mano. En la entrega registrar comando, revisión y ubicación; si viven en `build/cache` u otra ruta ignorada, conservar en el documento de tarea un resumen suficiente para reconstruir el resultado. Las interpretaciones permanentes de reglas viven en las especificaciones o decisiones existentes, no únicamente en un mensaje de agente.

## Checklist principal

La columna «depende de» determina autorización de escritura, salvo la exploración anticipada de solo lectura indicada más abajo. Una dependencia no se satisface por estar `en revisión`.

| Hecho | ID y documento de ejecución | Estado | Depende de | Responsable | Evidencia / revisión |
|---|---|---|---|---|---|
| [x] | Preparación: snapshot de todos los cambios | completada | — | Coordinador | `9118ca2`, publicado en `origin/2A2B` |
| [ ] | [T01 — Inventario y validación inicial](tasks/T01.md) | pendiente | Snapshot | Sin asignar | — |
| [ ] | [T02 — Revisión y cierre de bandas 2A](tasks/T02.md) | pendiente | T01 | Sin asignar | — |
| [ ] | [T03 — Revisión y cierre de bandas 2B](tasks/T03.md) | pendiente | T01 | Sin asignar | — |
| [ ] | [T04 — Catálogos, identidades y procedencia](tasks/T04.md) | pendiente | T01 | Sin asignar | — |
| [ ] | [T05 — Normalización y promoción reproducible](tasks/T05.md) | pendiente | T04 | Sin asignar | — |
| [ ] | [T06 — Inventario de efectos y obligaciones](tasks/T06.md) | pendiente | T01; cierre tras T02/T03/T04 | Sin asignar | — |
| [ ] | [T07 — Fusión en la KB canónica](tasks/T07.md) | pendiente | T02–T06 | Coordinador/integrador | — |
| [ ] | [T08 — Construcción y selección](tasks/T08.md) | pendiente | T07 | Sin asignar | — |
| [ ] | [T09 — Combate y paridad de motores](tasks/T09.md) | pendiente | T08 | Sin asignar | — |
| [ ] | [T10 — Automatización de campaña](tasks/T10.md) | pendiente | T08 | Sin asignar | — |
| [ ] | [T11 — Web, escritorio y presentación](tasks/T11.md) | pendiente | T07; cierre tras T10 | Sin asignar | — |
| [ ] | [T12 — Artefactos y evidencias derivadas](tasks/T12.md) | pendiente | T09/T10/T11 | Integrador | — |
| [ ] | [T13 — Validación integral de KB](tasks/T13.md) | pendiente | T12 | Sin asignar | — |
| [ ] | [T14 — Validación semántica y de producto](tasks/T14.md) | pendiente | T12 | Sin asignar | — |
| [ ] | [T15 — Cierre y commits locales](tasks/T15.md) | pendiente | T13/T14 | Coordinador | — |

## Fases, entradas y salidas

### Fase 0 — Verdad inicial (T01)

Inicio: snapshot accesible. Obtener inventario por ID y familia, baseline de validaciones y mapa de cambios previos. No tratar conteos documentados como verdad sin verificarlos.

Fin: inventario exhaustivo, fallos previos identificados y propiedad de archivos preparada. Este paso no está hecho por haber guardado el snapshot.

### Fase 1 — Contenido y diseño de integración (T02–T06)

Inicio: T01 aceptada. Revisar fuentes, traducciones, identidades y forma editorial; preparar promoción y obligaciones ejecutables. Mantener la distinción entre dato transcrito, dato validado y regla automatizada.

Fin: 79 paquetes y todos sus catálogos con destino y evidencia; colisiones resueltas; normalizador sin pérdida y repetible; todo efecto clasificado; preguntas bloqueantes resueltas. No actualizar manifiestos a `promotable` por simple existencia de YAML.

### Fase 2 — Promoción y consumidores (T07, comienzo de T11)

Inicio: barrera B1 aceptada. Fusionar catálogos y registros antes de bandas; validar el conjunto y adaptar pruebas de aislamiento al staging retenido. Ampliar categorías 2A/2B en Web y probar la vía dinámica de escritorio.

Fin: todos los registros se cargan una sola vez desde la KB; sin referencias rotas ni variantes fusionadas indebidamente. Datos activos previos preservados, salvo cambios justificados y revisados.

### Fase 3 — Comportamiento completo dentro de alcance (T08–T11)

Inicio: KB promovida y obligaciones definidas. Implementar primero construcción y selección; después combate y campaña por mecanismos comunes. Completar las interacciones de producto necesarias, traducción y persistencia.

Fin: todos los efectos aplicables tienen resultado observable y evidencia. Las reglas de sistemas ausentes permanecen documentadas, sin falsa automatización. Las elecciones nuevas tienen flujo accesible ES/EN y no se quedan en helpers.

### Fase 4 — Derivados, certificación y cierre (T12–T15)

Inicio: implementación estabilizada. Un solo agente genera derivados; validadores trabajan sobre esa misma revisión; correcciones reabren y repiten solo las comprobaciones afectadas antes del gate final.

Fin: criterios de aceptación completos, informes coherentes con la revisión final y commits locales. No push ni despliegue de esta implementación.

## Paralelismo y barreras de sincronización

Máximo cuatro agentes simultáneos: coordinador más tres trabajadores. La tabla prioriza seguridad de escritura; las dependencias no obligan a mantener agentes ociosos.

| Oleada | Paralelismo permitido | Punto de sincronización |
|---|---|---|
| A | T01; otros solo leen por encargo | B0: inventario y baseline aceptados |
| B | T02 + T03 + T04; coordinador prepara T06 en lectura | Catálogos solo T04; bandas solo su auditor |
| C | T05 + T06 + revisión pendiente de T02/T03 | B1: T02–T06 aceptadas; congelar identidades y contrato |
| D | T07 serial | B2: conjunto canónico consistente, reservar archivos de runtime |
| E | T08 + parte de categorías/presentación de T11 | B3: construcción/selección aceptadas, contratos de elecciones fijados |
| F | T09 + T10 + continuación T11 | B4: todos los comportamientos aceptados, detener escrituras de producto |
| G | T12 serial | B5: derivados y evidencias vinculados a una revisión concreta |
| H | T13 + T14 | B6: validación aceptada sin cambios posteriores no comprobados |
| I | T15 serial | Commits y estado Git final verificados |

T05 puede explorar el normalizador antes de cerrar T04, pero no escribir decisiones de identidad ni normalizar sus catálogos concurrentemente. T06 puede inventariar antes de cerrar T02–T04, pero debe reconciliar el inventario con su resultado final. T09/T10 pueden leer y diseñar antes de T08, sin modificar contratos aún inestables.

### Conflictos que requieren serialización

- Catálogos y registros compartidos: T04 durante preparación, T07 durante promoción; después asignación por archivo y lote por el coordinador.
- `runtime`, bindings, constructores y esquemas comunes: un dueño por archivo; consumidores esperan a que se acepte la ampliación común.
- T10 y T11 acuerdan las entradas y errores antes de que T11 implemente formularios; T11 no inventa una lógica de campaña alternativa.
- Generados web y manifiestos: solo T12 o el coordinador tras una corrección. Nunca varios agentes regenerando a la vez.
- Pruebas que mutan temporalmente datos, como auditorías negativas, no corren mientras otro agente los lee o edita. Ejecutarlas en una copia aislada cuando el runner no garantice aislamiento; comprobar restauración byte a byte.
- T13/T14 son revisiones independientes. Si encuentran fallos, entregan hallazgos: las reparaciones se reasignan a su propietario y se vuelve a generar antes de repetir validaciones afectadas.
- Git: solo coordinador crea commits, cambia ramas, integra o publica. Sin `reset`, `clean`, amend o rebase para ocultar trabajo concurrente.

En un checkout compartido basta esta reserva por archivos; no crear infraestructura nueva de bloqueo. Un worktree solo si es necesario para aislar una prueba o lote incompatible, creado desde la revisión acordada y con integración a cargo del coordinador.

## Herramientas y documentación común

Leer primero las guías existentes, y usar `--help` o el código para confirmar argumentos antes de ejecutar. Las rutas de los siguientes enlaces son relativas a este documento.

- [Modificar la KB](../../guides/modify-knowledge-base.md), [modelo de campaña](../../guides/campaign-knowledge.md), [implementar y verificar reglas](../../guides/implement-and-verify-rules.md).
- [Arquitectura](../../reference/architecture.md), [verificación](../../reference/verification.md), [presentación web](../../reference/web-presentation.md), [glosario](../translation-glossary.md).
- [Contrato editorial](../../../contracts/knowledge-editorial-v1/README.md), [especificaciones semánticas](../../../tests/specs/README.md).
- [Herramientas de ingesta](../../../tools/ingestion/README.md), [plan 2A](../../../sources/2A/README.md), [plan 2B](../../../sources/2B/README.md).
- [Forma de promoción](../../../sources/2B/promotion-schema-plan.md), [notas de fusión](../../../sources/2B/catalog/promotion-merge-notes.md).

Reutilizar `ingest_2a.py`, `ingest_2b.py`, `audit_2a_sources.py`, `audit_2b.py`, `audit_2ab_fidelity.py`, `normalize_staging_for_promotion.py`, `audit_staging_contract.py`, `check_hireling_sources.py` y el generador web. No restaurar herramientas retiradas porque un README antiguo aún las mencione.

Las extensiones de herramientas deben ser pequeñas y demostrar una necesidad de la tarea. Mantener el orden de normalización que exige la implementación, especialmente mercado antes de retirar hechos del ítem y campaña de mercenarios antes de retirarlos de sus perfiles. La previsualización de promoción no debe escribir la KB.

Comandos de cierre existentes, desde la raíz y con el entorno del proyecto:

```powershell
python tools/mordheim-utils.py tests --scope knowledge
python tools/mordheim-utils.py verify --structural
python tools/mordheim-utils.py verify --json
python tools/mordheim-utils.py parity --require-complete
python tools/knowledge/generate_knowledge_web.py --check --check-translations
python tools/mordheim-utils.py check-presentation
npm test
npm run typecheck
npm run build
python tools/mordheim-utils.py run-ci
```

No es una orden de ejecutar todas las suites en cada tarea. Cada documento concreta el mínimo proporcional; T15 consolida el cierre. No actualizar digests ni cantidades para apagar un fallo sin revisar qué cambió.

## Riesgos conocidos que hay que verificar

- Los manifiestos se observaron en `english-reviewed`, no `promotable`.
- El normalizador proponía eliminar `lore.prayers-of-taal-and-rhya`; verificar equivalencia y todas las asignaciones antes de aceptar o corregir esa conducta.
- El selector Web excluía grados 2A/2B; cargar el YAML no basta.
- Existen pruebas con cantidades fijas y prohibiciones de colisión entre staging y KB que requieren adaptar el contrato de promoción retenida.
- Las notas históricas pueden describir transformaciones ya hechas. La evidencia actual manda.
- La ausencia de caché puede hacer que un auditor omita comprobaciones. Registrar cobertura real, no solo código de salida.
- `NO` en una regla de campaña puede referirse al motor de duelo; no implica que deba seguir manual en el gestor de campaña.

## Criterios globales de aceptación

- [ ] Inventario completo de bandas y catálogos reconciliado con destino; no faltan familias.
- [ ] Sin IDs duplicados, referencias rotas, pérdida de variantes o cambio accidental del contenido anterior.
- [ ] Promoción repetible sin cambios adicionales y staging fuera de los cargadores de producción.
- [ ] Fuentes y traducción ES/EN completas; precios, restricciones y magia mantienen sus contextos.
- [ ] Cada efecto tiene implementación verificada o exclusión concreta de los sistemas acordados.
- [ ] Python/TypeScript y motores de combate correspondientes mantienen comportamiento, decisiones y orden RNG.
- [ ] Creación, reclutamiento, equipo, contratación, progreso, guardado/reapertura y PDF probados donde sean aplicables; todos los mecanismos nuevos tienen casos de producto.
- [ ] Categorías 2A/2B seleccionables y excluibles; presentación visible y accesible sin IDs técnicos filtrados.
- [ ] Artefactos y evidencia pertenecen a la revisión final; fallos previos y limitaciones reales de validación declarados.
- [ ] Staging retenido; commits locales revisados, sin publicar implementación ni tocar `main`.

## Registro de decisiones y sincronizaciones

| Fecha | Barrera/tarea | Decisión | Evidencia | Aprobación del coordinador |
|---|---|---|---|---|
| 2026-09-25 | Preparación | Publicar snapshot y documentos en `2A2B`; implementación posterior local | Solicitud del usuario; snapshot `9118ca2` | Sí |

Añadir aquí solo decisiones de coordinación. Para una regla, enlazar su interpretación y evidencia en el sistema semántico existente. No mantener dos versiones divergentes de una misma decisión.
