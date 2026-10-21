# Implementación del motor vectorial NumPy

Los encargos individuales, sus cláusulas y el orden de lanzamiento están en [README.md](README.md), junto a los ficheros G00–G08 de este directorio. Sus anexos asignan responsabilidad; el CSV conserva el progreso canónico.

## Objetivo y premisas obligatorias

Completar el motor NumPy existente hasta reproducir el comportamiento del motor modular dentro del alcance admitido del proyecto. Después, comprobar la paridad y optimizar la implementación correcta.

**Se da por completada la implementación y la verificación final del motor modular.** Esa verificación se gestiona por separado y no es una tarea de este plan.

**El portado parte del código modular, no de una nueva interpretación de las reglas.** Sus funciones, condiciones, orden de ejecución, estados y consumidores definen el comportamiento que debe trasladarse. Los contratos del CSV y los E2E existentes aportan contexto y evidencia ya disponible. No se repetirá el análisis de fuentes ni se reconstruirá una batería de pruebas por regla.

El trabajo tiene tres fases secuenciales:

1. Implementar las características que faltan, con pruebas nuevas mínimas.
2. Comprobar la paridad de NumPy contra el modular y corregir divergencias.
3. Medir y optimizar el motor vectorial manteniendo la paridad.

Se conserva el motor NumPy actual, la compilación compartida y las interfaces públicas de entrada y resultado. No se implementa Cython en esta fase del proyecto, no se amplía el alcance de las reglas y no se crean nuevos sistemas de seguimiento.

## Registro único: cómo se utiliza el CSV

Archivo canónico: `sources/knowledge/verification/clause-contracts.csv`.

La unidad de seguimiento es la cláusula identificada por `(id, clause_id)`. La unidad de implementación es el comportamiento compartido: una modificación puede satisfacer varias cláusulas. No se deben convertir miles de filas en miles de tareas ni en miles de tests.

| Información necesaria | Campo existente que se utiliza |
| --- | --- |
| Identificar las cláusulas | `id`, `clause_id` |
| Determinar el alcance | `clause_scope` |
| Comprender el comportamiento aceptado | `semantic_contract`, `parameters`, `conditions` |
| Localizar la implementación modular y agrupar trabajo relacionado | `consumer`, `effect_id`, `relation` |
| Registrar consumidores NumPy | Añadir referencias a `consumer`, conservando las anteriores |
| Registrar evidencia aplicable | `verification` y contexto explícito de NumPy en `notes` |
| Explicar un bloqueo o una discrepancia | `notes`, indicando el motor y el problema concreto |
| Registrar progreso | Únicamente `status.numpy` |

No se añaden columnas de paquete, propietario, consumidor o evidencia por motor. Los encargos de los agentes contienen las claves asignadas; no se necesita persistir otra clasificación en el CSV.

### Estados y relación con las fases

La columna `status` ya contiene un objeto JSON con estados independientes, por ejemplo:

```json
{"numpy":"implemented","native":"pending"}
```

| Estado de NumPy | Significado operativo |
| --- | --- |
| `pending` | Falta determinar o completar su portado; no demuestra por sí solo ausencia de código. |
| `in_progress` | Se está implementando el comportamiento correspondiente. |
| `implemented` | El comportamiento está conectado e integrado en NumPy. Falta la comprobación de paridad de la fase 2. |
| `verified` | Ha superado la comparación aplicable de la fase 2 sobre la versión integrada. |
| `blocked` | Existe una dependencia o problema concreto explicado en `notes`. |

Solo se trabaja sobre cláusulas admitidas (`clause_scope=YES`). Las demás conservan su clasificación y el objeto de estado correspondiente. No se modifica `status.native`, ni se reinicia el seguimiento modular existente.

El coordinador es el único escritor del CSV. Consulta, prepara y aplica cambios mediante `tools/knowledge/clause_registry.py`, conservando las protecciones de concurrencia y respaldo. Al actualizar `status`, debe preservar el valor nativo leído del registro actual; no sobrescribirlo con un valor supuesto.

Consulta de ejemplo:

```powershell
python -X utf8 tools/knowledge/clause_registry.py query --backend numpy --status pending --fields id,clause_id,consumer,status --limit 100000
```

Los recuentos proceden del CSV actual, sin cifras fijadas en este documento. Se muestran cláusulas pendientes, en curso, implementadas, verificadas y bloqueadas. Para medir implementación se suman `implemented` y `verified`; para medir paridad se cuenta únicamente `verified`. Ambos porcentajes usan como denominador las cláusulas admitidas y no son estimaciones de esfuerzo o tiempo.

Una coincidencia textual de etiquetas o la existencia de una prueba modular no permite marcar NumPy como verificado. Tampoco se exige un test individual para cada fila: varias cláusulas pueden compartir evidencia cuando corresponda al comportamiento que realmente se ha comparado.

## Fase 1 — Implementar las características que faltan, con pruebas mínimas

### 1.1. Preparar una base común

Fijar la versión modular aceptada y una base de trabajo común para los agentes, incluyendo los cambios todavía no confirmados que formen parte de la entrega. Preservar el trabajo concurrente. No sustituir el árbol actual por una versión antigua para obtener una base limpia.

A partir de los consumidores y contratos existentes del CSV, comparar la implementación modular con el NumPy actual. Esta comparación localiza diferencias de implementación; no vuelve a interpretar reglas ni a revisar todos los E2E.

Para cada grupo de comportamiento, distinguir:

- Ya resuelto por la compilación compartida: reutilizarlo y comprobar su conexión con el consumidor NumPy.
- Ya implementado en NumPy: conservarlo y llevarlo a la comprobación de paridad de la fase 2.
- Ausente o incompleto: portar la parte faltante desde el modular.

Que una cláusula se resuelva en construcción no obliga a duplicar código en NumPy. Que una etiqueta exista en NumPy tampoco demuestra que su consecuencia esté conectada.

### 1.2. Completar primero los puntos compartidos

El coordinador prepara los cambios que varios agentes necesitarán:

- Separar la admisión de capacidades NumPy y nativas en el límite compartido del motor. Completar NumPy no debe habilitar automáticamente Cython. Mantener el rechazo explícito de lo todavía no soportado y el comportamiento conservador de las llamadas antiguas sin selección de backend.
- Revisar los accesos por simulación directa, paralela, reproducción de duelos y selección automática, para que todos apliquen la admisión del motor que realmente ejecutan.
- Ampliar el estado vectorial solo con los datos exigidos por los comportamientos portados: recursos consumidos, temporizadores, decisiones, cambios de equipo, características variables y estados de ronda.
- Conservar `CompiledFighter`, `DuelContext` y los resultados públicos existentes. Las diferencias de ejecución entre simulaciones se representan con arrays, máscaras y, cuando corresponda, agrupaciones por configuración de equipo.

No crear un framework nuevo de efectos ni un segundo compilador. No implementar NumPy como una llamada al duelo modular por cada simulación. Los bucles sobre rondas, ataques, decisiones excepcionales o grupos de equipo son válidos cuando sean necesarios; el trabajo numérico de los lotes debe ejecutarse en la ruta NumPy.

### 1.3. Portar por comportamiento

| Área | Referencia modular | Destino y trabajo vectorial |
| --- | --- | --- |
| Estado y equipo | `state`, `equipment`, `mutations` | Estado por simulación y equipo efectivo, incluyendo pérdida, sustitución y cambios durante el combate. |
| Ataques y prioridad | `contexts`, `pools`, `attacks` | Operadores, cantidades, orden, modificadores y resolución de ataques, defensas, daño y reacciones. |
| Rondas y efectos persistentes | `rounds`, `psychology`, `leadership`, `alchemy`, `aftermath` | Control de rondas, contexto local, recuperación, decisiones, recursos y expiración. |

Estos nombres corresponden a módulos de `mordheim_combat.modular`. Se amplían las capas existentes de `mordheim_combat.vectorized`; solo se extrae un módulo cuando sea necesario para una propiedad clara del código.

Cada entrega debe conectar entrada compilada, estado individual, operación, ejecución de ronda y resultado. Debe conservar del modular las condiciones de activación, el orden y los límites por ataque, turno o combate. Una decisión o recurso consumido en una simulación no puede aplicarse al resto del lote.

### 1.4. Política estricta de pruebas mínimas

**En esta fase se desarrolla implementación, no una nueva batería de pruebas.**

- Reutilizar las pruebas vectoriales y de integración existentes para detectar regresiones inmediatas del cambio.
- Añadir cero pruebas si las existentes bastan.
- Cuando la funcionalidad nueva necesite un comprobante propio, añadir como referencia habitual un único caso pequeño y representativo en una suite vectorial o de paridad existente.
- Añadir más únicamente si existe un fallo o un hueco concreto que ese caso no puede distinguir. Explicar ese motivo en la entrega; no crear matrices exhaustivas por rutina.
- Contar escenarios reales: reunir cientos de casos parametrizados en una función no cumple el objetivo de pruebas mínimas.
- No copiar los E2E modulares, no crear una prueba por cláusula y no desarrollar nuevas pruebas modulares para acreditar NumPy.
- No ejecutar la matriz completa de paridad por cada funcionalidad. Esa comprobación pertenece a la fase 2.

Si se descubre una posible contradicción del modular, registrar el caso concreto por separado. No iniciar una auditoría de reglas ni cambiar el resultado de referencia para hacer pasar NumPy.

### Salida de la fase 1

Todo el alcance admitido está integrado en la ruta NumPy y las comprobaciones enfocadas aplicables pasan. Las cláusulas correspondientes quedan `implemented` (o conservan `verified` si ya tenían evidencia vigente). No deben quedar funcionalidades pendientes ocultas mediante fallback modular, etiquetas sin consumidor o restricciones levantadas sin implementación.

## Fase 2 — Comprobar la paridad contra el modular

### 2.1. Reutilizar las baterías existentes

La [renovación de paridad](parity_update/PARITY_BATTERY_RENOVATION.md) autoriza
preparar su ampliación en paralelo a fase 1, con los
[prompts P00–P05](parity_update/PROMPTS_AGENTES.md). Ahora solo se preparan tests;
el vectorial no está terminado. No se ejecutan candidatos ni se exigen resultados
suyos para aceptar el inventario, catálogo, adaptador o conexión CLI/informes.
Se comprueba la infraestructura propia y, cuando haga falta, se usa el oráculo
para preparar referencias y medir coste, sin revalidarlo. Las dependencias del
motor se documentan con contrato y propietario, sin bloquear P03 por su ausencia.
P04 puede cerrar su preparación y medición modular ahora; completa la calibración
candidata tras G00–G06. P05 ejecuta entonces la aceptación de fase 2/G07 con la
batería preparada, sin repetir otra campaña independiente.

Usar el modular aceptado como referencia y NumPy como candidato explícito. No volver a ejecutar su proceso de certificación modular completo.

La base de comparación será la infraestructura existente:

- Pruebas vectoriales y comparaciones exactas ya mantenidas.
- Los cinco combates básicos.
- La matriz de combates predefinidos `fast` y `full` (actualmente 30 y 42 enfrentamientos).
- Las comparaciones a distintos horizontes de rondas.
- Los casos de reproducción de duelos existentes para observar recursos y estados cuando sea necesario.

Usar `fast` para investigar e integrar correcciones y `full` para la aceptación final. No ejecutar ambas repetidamente cuando no haya cambios que lo justifiquen.

Relacionar los comportamientos portados con lo que ejercitan esos escenarios. Si una funcionalidad nueva no aparece en ninguna comparación aplicable, extender un escenario existente o añadir el caso mínimo que cubra ese hueco. No ampliar la batería por cada cláusula ni por todas las combinaciones posibles.

### 2.2. Ejecutar realmente NumPy

El comando actual de paridad incorpora el nativo cuando está instalado. Añadir selección `--backend numpy|native|all`, manteniendo `all` como comportamiento predeterminado compatible. Las ejecuciones de esta fase seleccionan `numpy` y comparan exclusivamente modular contra NumPy.

Los informes deben identificar el backend ejecutado. No aceptar fallback modular como evidencia NumPy. Las búsquedas de campos y etiquetas pueden conservarse como inventario, pero no bastan para acreditar resultados.

### 2.3. Comparar y corregir

Comparar las tasas de victoria del primer combatiente, del segundo y de combate sin resolver mediante las tolerancias existentes. Las pruebas por horizonte comprueban también divergencias temporales que podrían ocultarse en el resultado final.

Ante un fallo:

1. Localizar el comportamiento modular y la ruta NumPy afectados.
2. Reutilizar el escenario fallido o reducirlo al caso mínimo que permita diagnosticarlo.
3. Corregir el portado NumPy.
4. Reejecutar esa comparación y las existentes directamente afectadas.

No debilitar expectativas ni ampliar tolerancias para conseguir aprobación. No asumir que compartir semilla implica compartir tiradas entre motores. Reutilizar guiones específicos por backend cuando ya existan.

Mantener los tamaños de muestra y presupuestos vigentes como punto de partida. Las muestras pequeñas de diagnóstico no sustituyen la ejecución final. Si las ampliaciones exceden el presupuesto por invocación, repartir los escenarios en tandas identificadas sin omitirlos silenciosamente.

La evidencia estadística acredita las comparaciones ejecutadas; no demuestra exhaustivamente todas las combinaciones posibles. Para un problema de recursos, decisiones o contaminación entre filas que no distingan los resultados agregados, reutilizar una observación existente o añadir únicamente el caso vectorial mínimo necesario.

### Salida de la fase 2

Pasan las comparaciones aplicables y la matriz final sobre la misma versión integrada, sin divergencias conocidas. El coordinador vincula la evidencia a las cláusulas correspondientes y cambia `status.numpy` de `implemented` a `verified`.

No cerrar todas las filas por el mero resultado global de un comando: el vínculo entre comportamiento y comparación debe ser aplicable. Tampoco exigir pruebas individuales a cláusulas que comparten implementación y evidencia.

## Fase 3 — Medir y optimizar

### 3.1. Medir la implementación correcta

Usar la versión que ha superado la fase 2 como referencia de rendimiento. Registrar entorno, revisión, tamaño de lote, número de simulaciones, tiempo y memoria disponible mediante las herramientas existentes.

Reutilizar los escenarios de benchmark: `mini` para localizar costes y los casos relevantes de `full` para confirmar efectos en distintos tipos de combate. Medir por separado el tiempo de ejecución del motor cuando la compilación no forme parte de lo optimizado.

### 3.2. Optimizar los costes demostrados

Priorizar cambios locales con efecto medible: trabajo repetido dentro de las rondas, asignaciones temporales, tamaños de lote, máscaras, agrupación de ataques y cálculo de valores constantes.

No introducir una nueva arquitectura, dependencias o una reescritura general sin un cuello de botella medido que lo requiera. No modificar las reglas, el comportamiento observable ni el motor modular para ganar velocidad.

Para cada cambio:

1. Medir el caso afectado con la misma configuración antes y después, utilizando repeticiones comparables.
2. Ejecutar las comparaciones de paridad existentes afectadas.
3. Conservar la optimización cuando la mejora sea reproducible y no cause regresiones relevantes en los escenarios comprobados.

Si un cambio afecta al comportamiento de cláusulas verificadas, devolver temporalmente esas filas a `implemented` hasta ejecutar la comparación correspondiente. No invalidar el registro entero por cada cambio local.

No añadir tests de reglas durante la optimización. Un nuevo comprobante solo se justifica si reproduce un defecto concreto introducido o descubierto por ella.

### Salida de la fase 3

Entregar tiempos y consumo comparados con la base correcta de la fase 2, cambios conservados y limitaciones observadas. La versión optimizada debe conservar la paridad; tras cambios en componentes centrales, ejecutar una confirmación final de la batería aplicable sobre esa versión.

No se fija una aceleración mínima universal. Se cierra cuando los cuellos de botella priorizados han sido tratados o documentados con su coste y las mejoras conservadas están medidas. Las optimizaciones mayores sin beneficio demostrado quedan fuera de esta entrega.

## Coordinación de agentes externos

Un coordinador y hasta tres implementadores. Cada agente recibe un encargo con claves del CSV, funciones modulares de referencia, archivos permitidos, dependencias y comprobaciones existentes que reutilizar. El encargo obliga expresamente a partir del modular y a limitar al mínimo las pruebas nuevas.

Reparto inicial: operadores; ataques y equipo; rondas y efectos persistentes. El coordinador conserva tipos compartidos, admisión por backend, conexiones entre áreas, herramientas compartidas y escritura del CSV.

Trabajar en copias aisladas de una misma base. Dos agentes no editan simultáneamente el mismo archivo. Los cambios que atraviesan áreas se integran en orden de dependencia; una entrega parcial no se marca como comportamiento integrado.

Cada agente devuelve parche, cláusulas cubiertas, comprobaciones ejecutadas, casos nuevos añadidos y bloqueos. No crea su propio registro de progreso ni modifica el CSV compartido. El coordinador integra y reutiliza evidencia válida en vez de repetir investigaciones y comprobaciones sin motivo.

## Criterio final de entrega

- Alcance admitido implementado en NumPy a partir del modular.
- Paridad aplicable superada sobre la versión final, con evidencia identificada.
- CSV actualizado únicamente en los campos necesarios, conservando el estado nativo y la trazabilidad existente.
- Pruebas nuevas limitadas a huecos o defectos concretos; sin duplicación de la suite modular.
- Rendimiento medido y optimizaciones conservadas respaldadas por comparación.
- Sin commits ni pushes salvo autorización posterior.

Este documento es el plan de trabajo. Su existencia y los estados iniciales del CSV no acreditan ejecución ni paridad del motor vectorial.
