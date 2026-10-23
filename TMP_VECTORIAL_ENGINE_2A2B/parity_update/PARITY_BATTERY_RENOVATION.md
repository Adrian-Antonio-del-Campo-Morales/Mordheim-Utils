# Renovación de la batería de paridad estadística

## 1. Decisión vigente y alcance

**Mantener la filosofía anterior: ejecutar muestras de duelos en el modular y en el candidato y comparar estadísticamente sus resultados.** La renovación mejora la selección de escenarios desde las cláusulas y variantes; no convierte la paridad estadística en una suite de eventos internos.

Esta revisión, acordada el 22 de octubre de 2026, sustituye las instrucciones anteriores que exigían testigos internos, checkpoints o instrumentación nueva como condición de comparación o aprobación estadística. Las entregas, adendas y revisiones obsoletas se han retirado. La información de diseño útil se conserva en [SCENARIO_DESIGN_REFERENCE.md](SCENARIO_DESIGN_REFERENCE.md), los datos auxiliares y el catálogo ejecutable; no se reinician los inventarios. [P03-deliverable.md](P03-deliverable.md) registra el estado de la adaptación, pendiente hasta que se implemente.

El motor se recibe como implementado. Este trabajo no cambia motores ni sus planes, no reabre G07 y no atribuye a su evidencia anterior la cobertura nueva. La adaptación y su campaña posterior conservan alcance y resultados propios.

Los documentos externos `../README.md`, `../PLAN_IMPLEMENTACION.md` y `../G07_PARIDAD_CONTRA_MODULAR.md` describen el plan del motor y su aceptación con la batería histórica. G07 es independiente de P04/P05. Para este rework rigen este documento, `PROMPTS_AGENTES.md` y el estado de `P03-deliverable.md`; los encargos del motor no autorizan ampliar la instrumentación ni cambian estas condiciones de preparación.

## 2. Aprovechar el trabajo realizado

Se conservan el inventario de cláusulas y variantes, los escenarios materializados, los pares con/sin regla, sus orígenes E2E, los niveles acumulativos, la CLI y la infraestructura histórica de ejecución y comparación reutilizable. No se copia el corpus E2E ni se reconstruye la validación del modular.

Se retira como requisito estadístico la publicación de contadores de eventos, banderas de activación, categorías internas, hashes de equipo, tentativas de parada y checkpoints. No se encarga implementarlos en ningún motor. Las sondas existentes pueden permanecer; no hay que eliminarlas ni ampliarlas.

Un bloqueo que solo pide un testigo interno no puede impedir ejecutar y comparar un duelo estadístico válido. En cambio, una entrada necesaria que el motor no acepta —por ejemplo, un estado inicial especial— sigue siendo una limitación real. No se borra ese bloqueo a ciegas ni se ejecuta otro estado bajo el mismo nombre. El escenario se conserva con disposición explícita y referencia de cobertura, sin contarlo como ejecutado ni aprobado.

## 3. Selección de escenarios desde las reglas

Cada caso identifica origen, variante y claves canónicas, participantes, equipo, reglas, contexto, decisiones admitidas, horizonte, muestras y semillas. Su preparación debe poder llevar a la situación relevante durante un duelo real. Portar una etiqueta no demuestra por sí solo que la regla influya en la muestra.

Reutilizar pares con/sin regla cuando su preparación sea materialmente distinta y válida. Ambos miembros son duelos estadísticos normales: no exigen reproducción exacta de tiradas ni predicados de contadores. Una misma semilla no garantiza la misma secuencia de tiradas entre motores.

La comparación modular/candidato de cada miembro sigue siendo el criterio de paridad. En una campaña posterior, el contraste con/sin regla en el modular puede aportar evidencia de sensibilidad. Una diferencia no detectable con la muestra disponible no prueba ausencia de efecto ni fallo del candidato: deja la sensibilidad sin demostrar. No introducir un gate universal nuevo para los pares ni ajustar escenarios a la salida del candidato.

Si una variante no tiene señal útil en los resultados disponibles, registrar ese límite. Buscar primero una preparación o un horizonte válidos con las entradas existentes. No resolver el límite encargando instrumentación nueva.

## 4. Ejecución y comparación

El modular validado sigue siendo el oráculo. Cada candidato ejecuta sus duelos reales, sin delegar en el modular ni usar resultados fabricados.

La comparación básica conserva las proporciones históricas de victoria del primero, victoria del segundo y duelo sin resolver, con sus tolerancias y criterios existentes. Reutilizar el comparador histórico donde encaje. Las distribuciones de duración, heridas y condiciones finales pueden aprovecharse donde las APIs actuales las expongan en ambos motores con significado compatible y ya exista comparación aplicable. Su ausencia no bloquea la comparación básica; el informe identifica qué magnitudes comparó. No añadir recursos internos como magnitudes obligatorias nuevas.

No aumentar tolerancias ni reducir muestras para obtener aprobación. Los valores pequeños de autoría o diagnóstico no se presentan como muestras suficientes de aceptación: sensibilidad y coste se comprueban después.

Compilar entradas reutilizadas una vez y compartir la muestra modular entre candidatos cuando coincidan caso, entradas, contexto, decisiones, semillas, muestras, horizonte y versión real. Reutilizar mecanismos existentes, sin otro sistema de caché. No exigir igualdad fila a fila entre muestras independientes.

## 5. Perfiles y cobertura

| Perfil acumulativo | Contenido |
| --- | --- |
| `quick` | Subconjunto representativo de las fases y reglas principales. |
| `complete` | `quick` más los escenarios base de las variantes inventariadas y controles válidos. |
| `deep` | `complete` más composiciones justificadas, intercambio de lados, horizontes y sensibilidad adicional. |

No reservar una regla base únicamente a `deep` ni fijar cuotas arbitrarias. Conservar la selección existente siempre que sea válida; no reiniciar autoría para recuperar recuentos antiguos.

El informe distingue selección de diseño por cláusula/variante, escenarios ejecutados, magnitudes comparadas, resultado estadístico, sensibilidad demostrada o pendiente y casos no ejecutables con causa. **Paridad estadística aprobada no significa verificación exhaustiva de todas las reglas internas.** Una variante con caso seleccionado pero pendiente o sin sensibilidad demostrada no puede presentarse como comportamiento comprobado.

El perfil completo conserva el denominador de diseño aunque tenga casos incompatibles. No ocultar casos para obtener `complete=True`. La completitud de ejecución se basa en los casos estadísticos requeridos del perfil, no en disponer de sondas ni en acreditar cobertura semántica absoluta. Los casos aprobados sin sensibilidad acreditada se distinguen expresamente en el informe de cobertura.

## 6. Secuencia y cierre

| Paso | Trabajo y cierre |
| --- | --- |
| Adaptación estadística de P01–P03 | Reutilizar catálogo y conexión; retirar dependencias de testigos internos y controles de eventos del camino estadístico; mantener limitaciones reales de entrada. Actualizar comprobantes y documentación. |
| P04, campaña posterior | Ejecutar muestras y medir coste y sensibilidad. Calibrar parámetros sin relajar criterios para obtener PASS. |
| P05, campaña posterior | Ejecutar aceptación sobre una base identificada; informar resultados, cobertura y límites reales. |

No volver a lanzar P00 ni encadenar rondas de inventario. La adaptación termina con catálogo → duelos reales → comparación estadística → CLI/informe conectado y limitaciones identificadas. No depende de ampliar observación o estado en los motores. Un defecto propio de conexión se corrige; una limitación de entrada queda visible.

Se mantiene para el encargo inmediato la restricción de preparación estática: no ejecutar tests, importaciones de validación, `py_compile`, compilaciones ni motores. Dejar comprobantes escritos y comandos posteriores exactos, sin declararlos ejecutados. P04/P05 requieren un encargo posterior explícito; esta revisión documental no autoriza campañas.

## 7. Propiedad y entrega

Escritura de implementación: herramientas de paridad, conexión en CLI, comprobantes afectados y documentación de uso. Preservar la ruta histórica sin `--profile` y la selección `--profile quick|complete|deep`; no añadir otro modo. Conservar selección de backend, informar ausencia de nativo sin fallback y no certificar nativo con evidencia NumPy.

No modificar motores modular/vectorial/nativo, modelos compartidos, planes del motor, KB, CSV canónico ni corpus E2E. No añadir dependencias, intérpretes de eventos, DSL, planificadores o registros de progreso. No hacer commits ni pushes. Preservar cambios concurrentes y un escritor por archivo. Referenciar problemas concretos pendientes en `TODO.md`, sin convertir observabilidad fuera de alcance en trabajo obligatorio nuevo.

Actualizar una sola entrega: `P03-deliverable.md`. Distinguir adaptación estadística vigente e implementación instrumentada histórica. Identificar archivos cambiados, reutilización, disposición de casos, limitaciones reales, comprobantes escritos y no ejecutados y comandos propuestos. No actualizar estados de verificación del CSV por autoría o etiquetas.
