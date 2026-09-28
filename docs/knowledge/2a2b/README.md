# 2A/2B — checklist de integración y coordinación

## Punto de inicio y alcance

- Rama de trabajo: `2A2B`; remoto: `origin/2A2B`.
- Snapshot publicado: `9118ca2` (`chore: snapshot 2A2B starting point`), 25 de septiembre de 2026. Incluye los cambios locales existentes y la historia anterior; no certifica que sus tests pasen.
- La documentación de este directorio se publica después del snapshot, en un commit separado. No se ha ejecutado la integración al redactarla.
- Alcance: 19 bandas de 2A y 60 de 2B y sus catálogos; integrarlas primero en la KB, después en `warband-manager-web` y por último en `combat-simulator`.
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

El coordinador revisa la entrega y reutiliza sus resultados. No repite la tarea completa: solo realiza comprobaciones puntuales cuando detecta una contradicción, falta evidencia para un criterio de cierre o existe un riesgo material no cubierto. Si hace una comprobación adicional, registra qué duda concreta resolvió.

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
| [x] | [T01 — Inventario y validación inicial](tasks/T01.md) | completada | Snapshot | Agente ejecutor | Entrega en T01 sobre `a31bd8d`; aceptada 2026-09-25 |
| [x] | [T02 — Revisión y cierre de bandas 2A](tasks/T02.md) | completada | T01 | Agente ejecutor | Entrega y gate mantenido sobre `101ca5d`; aceptada 2026-09-25 |
| [x] | [T03 — Revisión y cierre de bandas 2B](tasks/T03.md) | completada | T01; T04 completada | Agente ejecutor | Seis re-puntos y gates afectados sobre `5105860`; aceptada 2026-09-25 |
| [x] | [T04 — Catálogos, identidades y procedencia](tasks/T04.md) | completada | T01 | Agente ejecutor | Mapa y decisiones sobre `b2e437c`; aceptada 2026-09-25 |
| [x] | [T05 — Normalización y promoción reproducible](tasks/T05.md) | completada | T04 | Agente ejecutor | Promoción explícita e idempotente sobre `cd04931`; aceptada 2026-09-25 |
| [x] | [T06 — Inventario y reparto de obligaciones](tasks/T06.md) | completada | T01–T05 | Agente ejecutor | 1692 efectos y 2295 obligaciones reconciliados; aceptada 2026-09-25 |
| [x] | [T07 — Fusión en la KB canónica](tasks/T07.md) | completada | T02–T06 | Agente ejecutor | KB promovida, estructural e idempotente; aceptada 2026-09-25 |
| [x] | [T08 — Validación y cierre de la KB](tasks/T08.md) | completada | T07 | Coordinador/integrador | 2399 IDs reconciliados, carga canónica única y gates de KB aceptados 2026-09-26 |
| [x] | [T09 — Construcción y selección para Web](tasks/T09.md) | completada | T08 | Agente ejecutor | Contratos de construcción aceptados; 161/161 bandas construibles y T10/T11 liberadas 2026-09-27 |
| [x] | [T10 — Automatización de campaña Web](tasks/T10.md) | completada | T09 | Agente ejecutor | 567 obligaciones reconciliadas; automatización de campaña aceptada 2026-09-28 |
| [x] | [T11 — Interfaz Warband Manager Web](tasks/T11.md) | completada | T09; cierre tras T10 | Agente ejecutor | Contratos finales de T10 conectados; interfaz y flujos Web aceptados 2026-09-28 |
| [ ] | [T12 — Artefactos, validación Web y cierre](tasks/T12.md) | pendiente | T10/T11 | Coordinador/integrador | — |
| [ ] | [T13 — Reglas del Combat Simulator](tasks/T13.md) | pendiente | T12 | Sin asignar | — |
| [ ] | [T14 — Validación y paridad de combate](tasks/T14.md) | pendiente | T13 | Sin asignar | — |
| [ ] | [T15 — Revisión y cierre del Combat Simulator](tasks/T15.md) | pendiente | T14 | Coordinador | — |

## Fases, entradas y salidas

T01–T05 constituyen la preparación ya aceptada. Las tres fases siguientes se ejecutan en orden y cada una termina en validación vigente y commit local antes de abrir la siguiente.

### Fase 1 — Integración con la KB (T06–T08)

Inicio: T01–T05 aceptadas. T06 clasifica cada obligación como `KB`, `Warband Manager Web`, `Combat Simulator` o `sistema excluido`. T07 normaliza y promueve de forma serial; T08 valida fuente y destino y cierra la fase.

Fin: todos los registros aprobados se cargan una vez desde `sources/knowledge`, sin referencias rotas, pérdida de variantes ni lectura productiva de staging. Fidelidad, traducciones, esquemas e idempotencia acreditadas; commit local de fase 1 creado.

### Fase 2 — Warband Manager Web (T09–T12)

Inicio: fase 1 cerrada. T09 fija construcción, selección y contratos; después T10 implementa campaña y T11 conecta exclusivamente `warband-manager-web`. T12 genera artefactos, valida el flujo completo y cierra la fase.

Fin: las bandas 2A/2B pueden crearse, operar, persistirse, reabrirse y exportarse en Web con ES/EN, accesibilidad y errores correctos. Automatización de campaña cubierta por casos de producto; commit local de fase 2 creado. La aplicación de escritorio ya no existe y queda fuera de alcance.

### Fase 3 — Combat Simulator (T13–T15)

Inicio: fase 2 cerrada. T13 implementa solo las obligaciones de combate clasificadas por T06; T14 demuestra semántica y paridad; T15 revisa el conjunto y cierra la fase.

Fin: cada efecto de combate incluido tiene prueba determinista y paridad en todos los backends aplicables, con RNG, decisiones y estado observable correctos. Gate integral vigente y commit local de fase 3 creados; sin push ni despliegue.

## Paralelismo y barreras de sincronización

Máximo cuatro agentes simultáneos: coordinador más tres trabajadores. La tabla prioriza seguridad de escritura; las dependencias no obligan a mantener agentes ociosos.

| Oleada | Paralelismo permitido | Punto de sincronización |
|---|---|---|
| A | T01–T05 completadas; T06 activo | P0: preparación aceptada e inventario de obligaciones reconciliado |
| B | T07 serial | P1a: KB promovida; detener escritores de datos |
| C | T08 serial | P1: KB validada y commit local de fase 1 |
| D | T09 serial; T10/T11 solo leen | P2a: contratos Web estables |
| E | T10 + T11 con archivos disjuntos | P2b: campaña e interfaz Web aceptadas |
| F | T12 serial | P2: Web validada y commit local de fase 2 |
| G | T13 por lotes/backends disjuntos tras fijar el mecanismo común | P3a: comportamiento de combate implementado |
| H | T14 serial respecto de reparaciones | P3b: paridad de combate aceptada |
| I | T15 serial | P3: revisión integral y commit local de fase 3 |

La lectura preparatoria puede adelantarse, pero ninguna fase escribe antes del commit de cierre de la anterior. T10 y T11 solo escriben en paralelo después de que T09 estabilice sus contratos. T13 puede dividirse por backend únicamente después de fijar el mecanismo modular y con archivos disjuntos.

### Conflictos que requieren serialización

- Catálogos y registros compartidos: T04 durante preparación, T07 durante promoción; después asignación por archivo y lote por el coordinador.
- `runtime`, bindings, constructores y esquemas comunes: un dueño por archivo; T09 fija los contratos Web antes de T10/T11 y T13 fija el mecanismo común de combate antes de repartir backends.
- T10 y T11 acuerdan las entradas y errores antes de que T11 implemente formularios; T11 no inventa una lógica de campaña alternativa.
- Generados web y manifiestos: solo T12 o el coordinador tras una corrección. Nunca varios agentes regenerando a la vez.
- Pruebas que mutan temporalmente datos, como auditorías negativas, no corren mientras otro agente los lee o edita. Ejecutarlas en una copia aislada cuando el runner no garantice aislamiento; comprobar restauración byte a byte.
- T08, T12 y T14 validan sus respectivas fases. Si encuentran fallos, los devuelven al propietario y repiten solo la evidencia invalidada antes del commit de cierre.
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

No es una orden de ejecutar todas las suites en cada tarea. Cada documento concreta el mínimo proporcional y cada fase tiene su propio cierre. T15 consolida únicamente Combat Simulator y comprueba que los cierres anteriores siguen vigentes. No actualizar digests ni cantidades para apagar un fallo sin revisar qué cambió.

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
- [ ] Python/TypeScript del Warband Manager Web y los motores del Combat Simulator mantienen comportamiento, decisiones y orden RNG donde corresponda.
- [ ] Creación, reclutamiento, equipo, contratación, progreso, guardado/reapertura y PDF probados donde sean aplicables; todos los mecanismos nuevos tienen casos de producto.
- [ ] Categorías 2A/2B seleccionables y excluibles; presentación visible y accesible sin IDs técnicos filtrados.
- [ ] Artefactos y evidencia pertenecen a la revisión final; fallos previos y limitaciones reales de validación declarados.
- [ ] Staging retenido; commits locales revisados, sin publicar implementación ni tocar `main`.

## Registro de decisiones y sincronizaciones

| Fecha | Barrera/tarea | Decisión | Evidencia | Aprobación del coordinador |
|---|---|---|---|---|
| 2026-09-25 | Preparación | Publicar snapshot y documentos en `2A2B`; implementación posterior local | Solicitud del usuario; snapshot `9118ca2` | Sí |
| 2026-09-25 | B0 / T01 | Aceptar inventario y baseline; abrir T02, T03, T04 y la exploración de T06 | Entrega de T01 sobre `a31bd8d`; validación puntual de manifiestos y contrato | Sí |
| 2026-09-25 | T02 | Mantener bloqueada hasta reparar y ejecutar el auditor 2A; conservar el cotejo ya realizado y pasar sus notas de fusión a T04 | Entrega de T02 sobre `101ca5d`; `audit_2a_sources.py` usa dos nombres no enlazados y deja chequeos vacuos | Sí |
| 2026-09-25 | T02 | Aceptar las 19 bandas 2A tras reparar el gate; transferir `sources/2A/promotion-merge-notes.md` a T04 | Auditor 2A: 0 abiertos, 14 adjudicados; 23 pruebas enfocadas; cobertura no vacua declarada | Sí |
| 2026-09-25 | T03 | Conservar la revisión de las 61 bandas y bloquear el cierre hasta que T04 resuelva fuentes e identidades; después repetir solo gates afectados | Entrega de T03 sobre `b2e437c`; 60/60 hashes PDF, 0 problemas de banda, 8 problemas de magia y barrera de catálogo declarada | Sí |
| 2026-09-25 | T04 | Aceptar mapa de promoción y decisiones; conservar Taal & Rhya y Shield of Sigmar como variantes y usar sufijo `-miracle-workers`; devolver seis re-puntos a T03 | Fuentes externas recuperadas con URL/hash; auditor 2B con 0 problemas y 66/66 conjuros; mapa `2ab-promotion-map.json` | Sí |
| 2026-09-25 | T03 | Aceptar el cierre tras aplicar seis re-puntos de objetos decididos por T04 | `ingest_2b validate` sin problemas, auditor 2B `problem_count 0`, matriz con 0 referencias sin resolver | Sí |
| 2026-09-25 | T05 | Aceptar la promoción explícita; conservar `warplock_pistol` como variante con entrada `-mim`, mantener los 26 ids históricos y normalizar staging al inicio de T07 antes de promover | Preview de 409 acciones/13 documentos, segunda pasada sin escrituras, colisión ambigua rechazada y 9 pruebas enfocadas; revisión estructural del coordinador | Sí |
| 2026-09-25 | Replanificación | Organizar el trabajo restante en KB (T06–T08), Warband Manager Web (T09–T12) y Combat Simulator (T13–T15); eliminar escritorio, incluir campaña en Web y cerrar cada fase con validación y commit local | Decisión del usuario antes de iniciar T07; T01–T05 permanecen aceptadas | Sí |
| 2026-09-25 | T06 | Aceptar el inventario y reparto por fases; tratar las 366 filas compuestas como 970 obligaciones explícitas y resolver `trait.spectral-touch` primero en T07 | Matriz: 1692 efectos, 2295 obligaciones, particiones reconciliadas, JSON/CSV UTF-8 y sin filas idénticas duplicadas; comprobación puntual del coordinador | Sí |
| 2026-09-25 | T07 | Aceptar la promoción canónica tras cerrar estructura, traducciones, catálogos, referencias y auditorías; conservar tres exclusiones de runtime justificadas y Spectral Touch pendiente de ejecución | 128 bandas, 2399 IDs creados, suite knowledge 602 pasadas/10 omitidas, estructura completa y segunda promoción sin escrituras | Sí |
| 2026-09-26 | T08 / cierre de fase 1 | Aceptar la KB integrada tras reparar los 80 efectos de objeto sin traducción y normalizar la regla pendiente; liberar T09 | 2399 IDs reproducidos, 0 referencias rotas, 396/396 objetos y 4305/4305 nodos con efectos ES, promoción idempotente y suite knowledge 602 pasadas/10 omitidas | Sí |
| 2026-09-27 | T09 | Aceptar los contratos de construcción y selección; adjudicar 12 obligaciones de magia como sistema excluido/X4 y liberar T10/T11 en paralelo | Artefacto fresco con 161/161 bandas construibles, 0 bloqueos abiertos, 25 gates focales verificados y promoción sin escrituras | Sí |
| 2026-09-28 | T10 | Aceptar la automatización de campaña y liberar su integración final en T11; conservar cinco obligaciones como bloqueo de fuente documentado | 567 obligaciones reconciliadas, retirada/sucesión/mutaciones/Born Marksmen cubiertos, 10 gates focales verificados y 30 errores semánticos heredados sin incremento | Sí |
| 2026-09-28 | T11 | Aceptar la interfaz Web tras reconciliar los contratos finales de T10 y liberar T12 | Categorías 2A/2B, variantes y obligaciones de campaña verificadas; 25 pruebas focales y typechecks Web/dominio verdes; artefactos, presentación y PDF transferidos a T12 | Sí |

Añadir aquí solo decisiones de coordinación. Para una regla, enlazar su interpretación y evidencia en el sistema semántico existente. No mantener dos versiones divergentes de una misma decisión.
