# Actualización de paridad: fases y prompts para agentes

Documento de ejecución del plan [PARITY_BATTERY_RENOVATION.md](PARITY_BATTERY_RENOVATION.md). P00, P01 y P02 ya tienen avances que deben revisarse con el criterio de preparación descrito aquí. Crear prompts, preparar casos o integrar el ejecutor no acredita paridad.

Raíz de referencia: `D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK`. Todas las rutas siguientes son relativas a la raíz de la copia de trabajo asignada. Si el agente usa otra copia, debe conservar las mismas rutas relativas y recibir la base completa, incluidos los cambios locales necesarios.

## Dos trabajos y dos cierres independientes

El plan del motor vectorial está terminando **G07 con su batería actual**. El rework está ejecutando **P01 y P02**. Ambos trabajos conservan su base, propiedad y evidencia; ninguno tiene que esperar al otro para cerrar su propio alcance.

Este documento solo organiza el rework y su campaña posterior. No modifica los
encargos, condiciones de cierre ni planes del motor: la entrega identificada de
G07 se recibe como entrada de P04/P05, con el alcance que su propio informe declare.

- **Cierre del motor/G07:** versión identificada, batería realmente usada, resultados y límites. No espera a P03/P04/P05 ni atribuye a su batería la cobertura de los tests renovados.
- **Cierre del rework/P03:** todos los tests de rápido/completo/profundo definidos y conectados: variantes, cláusulas, entradas, estados/contextos, decisiones, observables, criterios, CLI e informes, con muestras y horizontes iniciales explícitos. Se diseñan desde las cláusulas y el modular validado, sin ejecutar NumPy/nativo ni exigir resultados del candidato. No quedan escenarios o variantes por autorar en P04.

Se permiten comprobaciones propias de la batería (carga, referencias, selección, comparador e informes) y uso enfocado del oráculo modular para preparar referencias o confirmar una activación necesaria. El modular ya está validado: estas ejecuciones no son otra campaña de validación modular. Los datos sintéticos usados para probar infraestructura nunca son evidencia de comportamiento ni paridad de un motor.

Una entrada, decisión u observación que un candidato no pueda suministrar se registra con contrato concreto, propietario y caso afectado. No determina qué tests se diseñan ni bloquea el cierre de tests correctamente preparados. Sí impiden cerrar el rework los defectos propios: omitir reglas, entradas, variantes o criterios, perder obligaciones, comparador incorrecto o conexión incompleta. No se elimina una obligación por falta de soporte del motor ni se persigue el estado de G07 durante la autoría.

**P04 y P05 son una campaña posterior**, fuera del cierre del rework: P04 mide ambos motores y calibra parámetros de ejecución; P05 ejecuta la aceptación con la batería renovada. Usan una versión fija entregada por G07, pero no son G07, no reabren su cierre ni heredan automáticamente su cobertura. El `complete` de ejecución y `--require-complete` conservan su significado de campaña; no son el criterio de cierre de preparación P00–P03.

## Orden de ejecución

| Trabajo | Encargo | Entrega y condición de cierre | Puede empezar |
| --- | --- | --- | --- |
| Rework: inventario y contrato | P00 | Inventario discriminante y contrato común. Revisión 4 aceptada con A8–A10. | Base ya disponible; no reabrir su cierre. |
| Rework: construcción | P01 | Todos los escenarios y selección de los tres niveles conforme a P00. | En curso, en paralelo con P02. |
| Rework: construcción | P02 | Adaptador y comparador preparados conforme al mismo contrato. | En curso, en paralelo con P01. |
| Rework: integración y cierre | P03 | Todos los tests definidos y conectados en rápido/completo/profundo; sin autoría pendiente para P04. | Tras aceptar P01/P02; no requiere resultados del motor. |
| Campaña posterior: medición | P04 | Costes por motor y parámetros calibrados, sin cambiar cobertura ni completar tests faltantes. | Tras P03 y con versión fija del motor entregado por G07. |
| Campaña posterior: aceptación | P05 | Evidencia de ejecución de la batería renovada y sus límites. | Tras P04 sobre la misma base identificable. |

**Rework:** P00 → (P01 + P02 en paralelo) → P03 → cierre del rework.
**Motor:** G00–G06 → G07 con su batería actual → cierre de ese alcance.
**Después:** P03 cerrado + versión fija entregada por G07 → P04 → P05.

No lanzar todos los encargos a la vez. P01/P02 conservan P00 revisión 4 + A8–A10 como contrato; esta separación no cambia sus interfaces ni tareas en curso. Rápido/completo/profundo son niveles de la batería, no fases de desarrollo. El coordinador revisa e integra cada entrega antes de abrir su dependiente, sin volver a pedir autorización para trabajo ya encargado. Una dependencia externa explícita no convierte tests correctamente preparados en una entrega parcial; un defecto propio sí.

## Instrucciones comunes obligatorias

Todo prompt de este documento incorpora estas instrucciones:

1. **El modular se considera implementado y validado.** Es el oráculo. Sigue su código, los contratos aceptados y la evidencia disponible. No reinterpretes reglas ni inicies otra validación modular.
2. **Céntrate en la tarea de paridad.** Reutiliza herramientas, escenarios, E2E y especificaciones existentes. No copies el corpus modular ni construyas otra suite modular. No hagas un escenario por cláusula o por identificador si comparten de forma demostrada el comportamiento relevante.
3. **Pruebas nuevas mínimas.** Cero comprobaciones de infraestructura nuevas si bastan las existentes; añade el mínimo que detecte un defecto real del adaptador, selector o informe. Los escenarios de paridad necesarios para cubrir huecos sí forman parte del encargo: no existe un límite artificial de uno para toda esta batería. Cada escenario adicional debe distinguir un comportamiento, variante o interacción que no cubran los reutilizados.
4. No mantengas manualmente dos grandes colecciones de tiradas. Reutiliza reproducción y adaptadores existentes. Una semilla igual no implica tiradas iguales. Una comparación exacta necesita correspondencia justificada entre las situaciones ejecutadas; en otro caso usa una comparación estadística adecuada y declara sus límites.
5. En P00–P03 no ejecutes comparaciones contra NumPy/nativo ni exijas sus resultados. P04/P05 pertenecen a la campaña posterior de medición y aceptación, fuera del cierre del rework. Implementa las llamadas para que la futura campaña use los motores reales. En la campaña posterior, un candidato que delega en el modular, un resultado fabricado, una búsqueda textual de etiquetas o una preparación que evita la fase relevante no acreditan paridad. Separa comprobaciones de infraestructura, referencias modulares y ejecución de candidatos.
6. La cobertura debe distinguir: comportamiento declarado, caso preparado, referencia modular disponible, dependencia del candidato, escenario ejecutado, activación observada y comparación aprobada. Durante la preparación las tres últimas quedan sin acreditar contra candidatos. Compartir consumidor o efecto ayuda a localizar trabajo; no demuestra equivalencia semántica. No uses solo la tasa de victoria para acreditar recursos, duración o estados que esa tasa no distingue.
7. Mantén niveles acumulativos: **rápido ⊆ completo ⊆ profundo** en obligaciones y escenarios base. Completo declara casos y criterios para todos los comportamientos inventariados y sus variantes obligatorias; su futura ejecución debe comprobarlos; profundo añade interacciones y sensibilidad. No reserves un comportamiento entero para profundo. Un muestreo mayor puede satisfacer el menor sin volver a ejecutarlo si se conserva su trazabilidad.
8. **Los presupuestos de tiempo se fijan después de medir.** No prometas duraciones, reduzcas tolerancias, omitas casos ni rebajes muestras silenciosamente para cumplir un tiempo. Interrupción, incompatibilidad, ausencia de soporte o presupuesto insuficiente producen evidencia incompleta, nunca éxito. No repitas semillas hasta conseguir un aprobado.
9. El CSV único es `sources/knowledge/verification/clause-contracts.csv`. Consúltalo mediante `tools/knowledge/clause_registry.py`; reutiliza claves, contratos, condiciones, consumidores y evidencia. No añadas columnas ni otro CSV de progreso. Solo el coordinador escribe el registro, preservando `status.native` y todos los valores ajenos. Los agentes entregan propuestas concretas, nunca actualizaciones masivas basadas en etiquetas.
10. Las referencias de cobertura viven junto a los escenarios ejecutables; los informes se generan a partir de ellos y de las ejecuciones. Los documentos de entrega son evidencia y traspaso de trabajo, no otro registro canónico de estados. El inventario de P00 es una base de diseño: no mantener después una segunda copia manual sincronizada con el catálogo.
11. Lee `AGENTS.md` y las instrucciones aplicables antes de editar. Comprueba rama, revisión y cambios locales. Preserva el trabajo concurrente. No hagas commits ni pushes. No ejecutes formateos masivos ni campañas ajenas al encargo.
12. Cada archivo tiene un único escritor. No edites el motor modular, el vectorial, el nativo, la KB, el CSV ni el corpus E2E desde estos encargos. Si falta un punto de observación, entrada de estado o decisión del vectorial, entrega al propietario G00/G02/G06 la petición mínima, su consumidor y un ejemplo; conserva el caso preparado y su dependencia explícita. La falta de esa capacidad no bloquea el cierre de la preparación ni P03 si el contrato y su tratamiento están definidos. No crees un segundo motor en el adaptador.
13. Antes de modificar archivos compartidos con G07 o G00, el coordinador debe registrar su cesión efectiva. No basta con que aparezcan en una lista de archivos permitidos. En particular, `_replay.py` participa en G00 y `cli/commands.py` ya tiene cambios locales en la base de preparación. Una base HEAD limpia que omita esos cambios no es equivalente a la copia entregada.
14. Cada agente **debe crear o actualizar su documento de entrega**, incluso ante trabajo parcial o bloqueado. No basta una respuesta en el chat. Solo escribe su entrega; no sobrescribe las de otros agentes. En una reanudación actualiza el mismo fichero, conservando evidencia válida y señalando la sustituida.

## Lecturas compartidas

- `TMP_VECTORIAL_ENGINE_2A2B/parity_update/PARITY_BATTERY_RENOVATION.md`: diseño acordado.
- Este documento completo: instrucciones, orden, propiedad y aceptación.
- `TMP_VECTORIAL_ENGINE_2A2B/README.md`, `PLAN_IMPLEMENTACION.md` y `G07_PARIDAD_CONTRA_MODULAR.md`: coordinación con el portado.
- `docs/reference/verification.md`: infraestructura histórica. Sus afirmaciones de cobertura y tiempos deben contrastarse; no sustituyen el inventario actual ni cambian la premisa de modular validado.
- `apps/combat-lab/mordheim_combat_lab/verification/parity/`: comparaciones, reproducción, informes y selección de evidencia.
- `apps/combat-lab/mordheim_combat_lab/cli/scenarios.py` y `cli/commands.py`: escenarios, opciones y ejecución actuales.
- `tests/E2E/modular-engine/{README.md,corpus.py,runner.py,cases/}` y `tests/specs/semantic/`: fuentes reutilizables de situaciones, entradas, decisiones y observaciones. Leer lo relevante por familias, no cada fichero varias veces.

No copies todas estas fuentes en la entrega. Cita rutas, símbolos e identidades de escenarios que permitan continuar el trabajo.

## Propiedad de archivos y coordinación con G07

`parity/` en esta tabla significa `apps/combat-lab/mordheim_combat_lab/verification/parity/`.

| Encargo | Escritura autorizada |
| --- | --- |
| P00 | Su documento de entrega; sin cambios de producción. |
| P01 | `parity/_battery_cases.py`, catálogo mínimo nuevo; un comprobante enfocado opcional `tests/python/verification/test_parity_battery_cases.py`; su entrega. |
| P02 | `parity/_battery_runner.py`, adaptador mínimo nuevo; `parity/_specifications.py`; `tests/python/verification/test_duel_replay.py`; un comprobante opcional `tests/python/verification/test_parity_battery_runner.py`; su entrega. |
| P03 | Integración secuencial de los archivos anteriores; `parity/__init__.py`, `_report.py`, `_vectorized.py`, `_statistical.py`, `_deep.py`, `_truncations.py`; `cli/commands.py`; `tests/python/verification/test_parity.py`, `test_truncation_parity.py`; `tests/python/cli/test_benchmarking.py`; `docs/reference/verification.md`; su entrega. |
| P04 | Tras cesión, solo parámetros de ejecución del catálogo `_battery_cases.py` (muestras, semillas y horizontes) y documentación de medición en `docs/reference/verification.md`; su entrega y medidas. No añade tests ni cambia la cobertura o algoritmos de combate. |
| P05 | Su entrega y certificados de ejecución. Las correcciones de código vuelven al propietario correspondiente. |

Los dos módulos nuevos separan datos y ejecución para permitir P01/P02 en paralelo. P00 debe fijar el mínimo contrato entre ambos, reutilizando los tipos ya existentes. No crear un framework, lenguaje de escenarios, jerarquía de plugins ni dependencias nuevas. Si la exploración demuestra una ubicación existente claramente mejor, P00 propone la sustitución exacta y el coordinador registra la propiedad antes de lanzar P01/P02; no mantener las dos ubicaciones.

`cli/scenarios.py` se reutiliza por referencia: no duplicar sus enfrentamientos ni alterar sus conjuntos históricos de benchmark al añadir los nuevos perfiles de paridad. `_replay.py` se reutiliza en lectura; cualquier edición adicional requiere cesión expresa tras G00 y queda registrada por el coordinador. No se autorizan cambios del motor a través de esta cesión.

P00–P03 concretan el **rework de la batería**, autorizado y con cierre propio en P03. G07 termina con su batería actual y no espera este trabajo. No hay escritores simultáneos sobre los mismos archivos. P04/P05 son la campaña posterior con la batería renovada: su evidencia referencia la versión entregada por G07 como antecedente, sin sustituir ni sobrescribir `G07-deliverable.md`, ni heredar cobertura por coincidencia de resultados. Se conserva la evidencia válida de cada campaña con su alcance.

## Formato y ubicación de las entregas

Crear `TMP_VECTORIAL_ENGINE_2A2B/parity_update/Pxx-deliverable.md`, sustituyendo Pxx por el encargo. Los resultados auxiliares necesarios pueden guardarse en `TMP_VECTORIAL_ENGINE_2A2B/parity_update/Pxx-results/`, con nombres que distingan ejecuciones; no crear carpetas vacías ni grandes volcados sin necesidad.

Cada entrega contendrá:

- Base recibida: revisión, cambios locales relevantes y procedencia de las entregas dependientes. Para evidencia ejecutada, identificar también las entradas y código realmente utilizados; HEAD solo no basta en una copia con cambios.
- Trabajo terminado y archivos/símbolos modificados.
- Comportamientos, variantes y claves tratados; referencias a casos reutilizados y justificación de los nuevos.
- Comandos realmente ejecutados, resultados, duración y ubicación de referencias. Separar infraestructura, preparación de referencias modulares y ejecución futura pendiente. P00–P03 no necesitan ni deben producir resultados candidatos; los históricos se conservan solo como tales, sin usarlos como criterio de cierre.
- Decisiones técnicas que necesita el siguiente agente, interfaces y cesiones acordadas.
- Trabajo propio de tests pendiente, separado de dependencias futuras del motor, con propietario, contrato y ejemplo concreto. Una entrega puede estar terminada como preparación y tener todas sus comparaciones candidatas pendientes.
- Propuestas para el CSV, si hay evidencia aplicable; nunca confundir preparación con `verified`.

Al terminar, responder con la ruta de la entrega y un resumen breve. El coordinador recoge también los documentos de las copias aisladas al integrar el código. No depender de que otro agente pueda leer el chat anterior.

## Prompt P00 — Inventario de comportamientos y contrato de trabajo

```text
Ejecuta P00 de la renovación de paridad en el repositorio asignado.
Lee TMP_VECTORIAL_ENGINE_2A2B/parity_update/PROMPTS_AGENTES.md completo,
sus instrucciones comunes y el plan PARITY_BATTERY_RENOVATION.md de esa carpeta.
Tu escritura se limita a parity_update/P00-deliverable.md y, si resulta necesario,
a resultados auxiliares de tu propiedad bajo parity_update/P00-results/.
Todas esas rutas están bajo TMP_VECTORIAL_ENGINE_2A2B.

El modular ya está validado. Esta tarea identifica cobertura diferencial necesaria,
no reinterpreta reglas ni vuelve a verificar el modular. El diseño es independiente del estado del vectorial: no ejecutes comparaciones ni sondas de resultados candidatos. Reutiliza la revisión 4 aceptada y las adendas A8–A10; no reinicies el inventario.

TRABAJO
1. Consulta las claves admitidas del CSV y sus consumidores, condiciones y evidencia.
   Reutiliza la partición G00-G06 para localizar código. Separa consecuencias del
   compilador compartido de comportamientos propios de ejecución; conserva ambas
   trazabilidades sin exigir duelos nuevos para todo lo que ya es compartido.
2. Relaciona comportamientos con escenarios E2E, especificaciones semánticas,
   reproducciones y enfrentamientos de paridad existentes. Revisa qué ejecutan
   realmente. Las equivalencias de comportamiento deben justificarse con contratos
   e implementación; no agrupes automáticamente solo por tag o nombre de función.
3. Para cada comportamiento y variante necesaria identifica: claves originales,
   preparación/activación, observable que detectaría una diferencia, referencia
   reutilizable y hueco concreto. Incluye ausencia, límites, excepciones, consumo,
   recuperación, orden, decisiones y dirección del participante cuando apliquen.
4. Propón el mínimo conjunto completo y su subconjunto rápido. Selecciona las
   interacciones profundas por estado/fase compartidos y orden de ejecución;
   no generes todas las combinaciones. Conserva escenarios históricos útiles.
5. Clasifica las dificultades de adaptación: estado inicial, contexto, decisiones,
   orden de tiradas, checkpoints, observaciones o rechazo de una construcción.
   Para una limitación del motor, indica el propietario G00/G02/G06 y la entrada
   y salida mínimas necesarias. No autorices emulación del motor en el adaptador.
6. Fija en tu entrega el contrato concreto entre P01 y P02: representación mínima
   del caso y sus referencias, selección de nivel, llamada de ejecución, observables,
   resultado y distinción entre incompatibilidad, divergencia y no ejecutado en la campaña futura. Define cómo representar hoy una preparación/observación pendiente del candidato sin sustituirla por otra situación.
   Reutiliza los tipos y funciones existentes; especifica nombres y campos exactos
   tras inspeccionarlos; si falta una capacidad candidata, documenta la interfaz mínima requerida y su propietario, sin exigir implementarla ahora. Para comparaciones estadísticas nuevas fija qué magnitud
   se compara y cómo se evaluará su sensibilidad; no improvisar tolerancias al fallar.
7. Entrega a P03 la conexión prevista con CLI/informes y a P04 los casos que deben
   medirse primero. Indica cambios de propiedad necesarios antes del paralelo.

VALIDACIÓN Y ENTREGA
No ejecutes candidatos ni campañas de paridad, ni escribas pruebas nuevas. Valida referencias,
identidades y reconciliación del universo admitido: cada clave debe tener una
disposición trazable, incluso si está pendiente o pertenece al compilador compartido.
No declares cobertura por tener una fila en la tabla.
Crea P00-deliverable.md con el inventario de diseño, huecos y contrato concreto.
Es obligatorio también si queda parcial. El coordinador debe poder lanzar P01 y
P02 con la misma interfaz, sin que ambos tengan que decidirla otra vez. Acepta P00 por inventario y contrato suficientes; no por disponibilidad ni resultados del vectorial.
```

## Prompt P01 — Catálogo de escenarios y tres niveles

```text
Ejecuta P01 de la renovación de paridad.
Lee TMP_VECTORIAL_ENGINE_2A2B/parity_update/PROMPTS_AGENTES.md completo y su plan.
Lee P00-deliverable.md de la misma carpeta y la base integrada por el coordinador.
Inicio: P00 revisión 4 aceptada con A8–A10 e interfaz fijada. Continúa en paralelo con P02. Prepara los casos desde las cláusulas y el modular, sin ejecutar ni aceptar candidatos ni perseguir G07.
Respeta la tabla de propiedad; tu entrega obligatoria es
TMP_VECTORIAL_ENGINE_2A2B/parity_update/P01-deliverable.md.

TRABAJO
1. Implementa el catálogo mínimo acordado con P00 en parity/_battery_cases.py.
   Cada caso debe referenciar su origen, comportamientos/variantes, claves del CSV,
   niveles, preparación y comparación prevista. No duplicar contratos completos
   ni convertir el catálogo en otro registro manual de estados.
2. Reutiliza los enfrentamientos existentes por referencia y los datos necesarios
   de E2E/especificaciones mediante sus cargadores o la adaptación mínima acordada.
   No copies el corpus, modifiques sus expectativas ni edites escenarios originales.
3. Añade únicamente casos que distingan huecos concretos de P00. El completo debe
   representar todas las obligaciones identificadas y cómo se comprobarán; el rápido recorrer las fases
   principales; el profundo añadir interacciones justificadas, variantes de lado,
   contextos y horizontes. No imponer que los recuentos sigan siendo 10/30/42.
4. Incluye situaciones multisimulación que permitan detectar recursos compartidos,
   máscaras mal aplicadas y filas ya inactivas. Define una observación discriminante;
   lanzar un lote grande sin comprobar estas diferencias no basta.
5. Para sucesos raros, reutiliza una situación dirigida que los active y permita
   observarlos. No acreditar una regla solo porque el luchador lleva su etiqueta.
6. No resuelvas dependencias de P02 suprimiendo observaciones o variantes.
   Conserva íntegra la preparación de la situación de origen: regla, estado,
   contexto y decisiones. Si aún no puede ejecutarse contra el candidato, declara
   la entrada/observación requerida y su propietario; no la sustituyas por un duelo
   sin la regla. Un caso correctamente preparado puede aceptarse con esa dependencia.

VALIDACIÓN Y ENTREGA
Comprueba carga, claves válidas, identidades únicas, referencias existentes y
anidamiento rápido/completo/profundo. Reutiliza checks; si falta uno, añade el
mínimo comprobante del catálogo, no tests modulares por escenario.
No ejecutes candidatos. Puedes usar el modular de forma enfocada si necesitas
preparar una referencia o comprobar el disparador, sin revalidarlo. Documenta
casos reutilizados, nuevos y sus motivos; separa trabajo de tests sin terminar de
dependencias del motor. Estas últimas no impiden aceptar P01 como preparación. Crea o actualiza
P01-deliverable.md aunque la entrega sea parcial. No escribas el CSV.
```

## Prompt P02 — Ejecutor diferencial y observaciones

```text
Ejecuta P02 de la renovación de paridad.
Lee TMP_VECTORIAL_ENGINE_2A2B/parity_update/PROMPTS_AGENTES.md completo y su plan.
Lee P00-deliverable.md y utiliza el contrato común fijado para P01/P02 con las
correcciones de coordinación vigentes y el alcance de preparación de este documento.
Inicio: P00 entregado. Trabaja en paralelo con P01 con archivos disjuntos. Este encargo prepara el adaptador; no ejecuta candidatos ni valida sus resultados.
Tu entrega obligatoria es
TMP_VECTORIAL_ENGINE_2A2B/parity_update/P02-deliverable.md.

TRABAJO
1. Implementa la adaptación mínima en parity/_battery_runner.py reutilizando
   _replay.py, _specifications.py, los ejecutores reales y tipos existentes.
   Revisa los cargadores E2E y sus restricciones; no suponer que todos sus casos
   aceptan simplemente cambiar el nombre del backend.
2. Implementa el camino que ejecutará las mismas situaciones semánticas en
   modular y NumPy en la campaña posterior. Normaliza solo diferencias de
   representación y prepara la comparación de heridas, estados, recursos y
   decisiones/checkpoints definidos en P00. No ejecutes esa comparación ahora ni
   ajustes casos o criterios a resultados del candidato ni al avance de G07.
3. Conserva las decisiones y el contexto. No ignores un estado inicial que el
   candidato no admita. Si falta soporte, devuelve incompatibilidad explícita y
   la petición mínima al propietario del motor; no cambies sus archivos. Deja
   conectada la gestión explícita de esa dependencia: no exige esperar a que el
   motor la implemente para aceptar el adaptador preparado.
4. Usa reproducción exacta solo donde pueda justificarse la correspondencia de
   tiradas y decisiones. Los órdenes físicos pueden diferir. Reutiliza adaptadores
   existentes; evita dos guiones extensos mantenidos a mano. La comparación
   estadística no debe presentarse como una reproducción exacta.
5. Respeta la convención de rondas de cada driver: usa resultados después de un
   horizonte equivalente cuando el contador de resolución no sea comparable.
   No declares una divergencia solo por un contador interno con distinto significado.
6. Prepara las situaciones multisimulación acordadas con P01 para la futura
   ejecución real por lotes y observación de decisiones/recursos por fila. Define
   un criterio que distinga acoplamiento; dos muestras aleatorias independientes
   no tienen por qué contener las mismas categorías. No diagnostiques fallos de
   máscara por la sola ausencia de una categoría rara ni ejecutes el candidato ahora.
7. Devuelve resultados con evidencia suficiente para distinguir: comprobación
   aprobada, divergencia, incompatibilidad, error de infraestructura y no ejecutado.
   Ningún fallback silencioso al modular y ningún caso omitido cuentan como éxito.

VALIDACIÓN Y ENTREGA
Comprueba importación, contrato y lógica propia de adaptación/comparación con
los checks existentes que no ejecuten candidatos. Reutiliza los mecanismos de
prueba disponibles; si falta un comprobante esencial, añade solo el mínimo para
que una diferencia, incompatibilidad o ausencia de observación no apruebe por error.
Datos sintéticos sirven para comprobar esa infraestructura, nunca como evidencia
de ejecución o paridad. No ejecutes suites de reproducción que comparen NumPy o
nativo durante esta preparación. Un fallo histórico del candidato se registra
para su fase futura y no bloquea P02. No reconstruyas pruebas modulares ni una
suite por regla. Acepta el adaptador por su preparación y dependencias explícitas.
Registra llamadas/interfaces, observaciones soportadas, limitaciones, comandos y
resultados en P02-deliverable.md, obligatorio aunque el trabajo quede parcial.
```

## Prompt P03 — Integración, CLI e informes de cobertura

```text
Ejecuta P03 de la renovación de paridad.
Lee TMP_VECTORIAL_ENGINE_2A2B/parity_update/PROMPTS_AGENTES.md completo y su plan,
y las entregas P00, P01 y P02. Inicio: catálogo y ejecutor integrados en la misma
base y cesión de archivos compartidos confirmada por el coordinador. Las entregas se aceptan como preparación; no se exige motor implementado ni resultados candidatos.
Tu entrega obligatoria es
TMP_VECTORIAL_ENGINE_2A2B/parity_update/P03-deliverable.md.

TRABAJO
1. Conecta catálogo y ejecutor al comando de paridad existente. Añade selección
   explícita --backend numpy|native|all y --profile quick|complete|deep para los
   nuevos perfiles. Mantén el comportamiento histórico sin --profile, incluyendo
   --level y --pair-set. Los nuevos perfiles no son alias de los viejos tamaños.
   Si --profile se combina con un selector antiguo explícito de batería, informa
   conflicto y no ejecutes una mezcla ambigua; los defaults implícitos no son conflicto.
2. Para los nuevos perfiles usa NumPy por defecto. --backend native explícito
   nunca cae a NumPy si falta soporte; informa incompleto/error. En all muestra
   disponibilidad y cobertura separadas por backend, sin certificar uno ausente.
   No implementes reglas nativas: prepara una selección reutilizable para el futuro.
3. Conecta comparaciones exactas y estadísticas según P00. Conserva las tolerancias
   existentes para las magnitudes actuales. Para magnitudes nuevas aplica el criterio
   justificado antes de ejecutar, identificando muestras, límites y sensibilidad.
   No declares equivalencia absoluta por no observar una diferencia estadística.
4. Reutiliza compilaciones y la muestra modular entre candidatos. Para reutilizar
   evidencia guardada, comprueba entradas compiladas, preparación, contexto,
   decisiones/tiradas o semillas, muestras/horizontes, versión del oráculo y del
   adaptador y observables. Considera cambios locales, no solo HEAD. Una referencia
   obsoleta se invalida; no es prueba fallida del candidato ni evidencia reutilizable.
   Usa certificados/resultados simples, sin otro sistema de caché o seguimiento.
5. Genera informes con denominador y cobertura por comportamiento/variante y claves:
   declarado, preparado, referencia modular disponible, dependencia del candidato,
   ejecutado, activado/comprobado, pendiente, incompatible y divergente.
   Separa evidencia estructural de comportamiento; revisa especialmente el uso
   histórico de búsquedas de tags en _vectorized.py. No heredar esos verified como
   comprobación ejecutada de la nueva batería.
6. Informa perfil, backend, revisión real, entradas, muestras, tiempos por motor,
   casos nuevos/reutilizados y resultados cuando se ejecuten. Durante preparación
   no inventes tiempos ni resultados candidatos; informa esa ejecución pendiente.
   Un rápido aprobado en la campaña futura no acredita el completo.
   Preserva campos existentes de certificados; añade los datos nuevos de forma
   compatible o versiona explícitamente si la semántica del formato exige cambiar.
7. Con --require-complete cualquier obligación requerida pendiente, omisión por
   presupuesto, error o divergencia debe dar salida no satisfactoria. Sin esa opción,
   una divergencia o error sigue fallando; una ejecución parcial debe identificarse
   claramente. No confundir all([]) con una batería completa aprobada. Esta es
   semántica de ejecución futura; que --require-complete no pueda aprobar todavía
   por ausencia de motor no impide cerrar P03 como conexión preparada.
8. Cierra el rework con todos los tests de rápido/completo/profundo definidos y
   conectados: casos, variantes, cláusulas, preparación, observables, comparación,
   selección, CLI e informes. Registra muestras, semillas y horizontes iniciales.
   Si falta autoría, devuelve la corrección a P01/P02; no la difieras a P04.
9. Actualiza la documentación de uso y deja comandos exactos para la campaña
   posterior P04/P05. P04 solo calibra parámetros preservando cobertura. No
   optimices motores ni incorpores cambios de otras campañas de cli/commands.py.

VALIDACIÓN Y ENTREGA
Reutiliza las comprobaciones de selección, CLI e informes de test_parity.py,
test_truncation_parity.py y test_benchmarking.py según lo modificado, sin ejecutar
sus comparaciones candidatas. Verifica selección, compatibilidad histórica,
representación de aprobado/divergencia/incompatibilidad/ejecución parcial y rechazo
de referencia obsoleta mediante los mecanismos existentes o el mínimo comprobante
propio de infraestructura. Los datos sintéticos no acreditan paridad. No añadas
cientos de pruebas ni ejecutes una muestra NumPy/nativa. Puedes preparar una
referencia real modular si hace falta comprobar su carga y trazabilidad.
Entrega P03-deliverable.md como cierre del rework: todos los tests y variantes de
los tres niveles definidos y conectados, comandos futuros utilizables, parámetros
iniciales, comprobaciones propias, cesiones y dependencias externas explícitas.
Las comparaciones candidatas pueden estar pendientes, pero no la autoría de tests
ni su conexión. Un caso meramente etiquetado no es un test preparado. No declares
paridad; no esperes ni reabras G07. P04/P05 quedan fuera de este cierre.
```

## Prompt P04 — Campaña posterior: medición y calibración

```text
Ejecuta P04 de la campaña posterior con la batería de paridad renovada.
Lee TMP_VECTORIAL_ENGINE_2A2B/parity_update/PROMPTS_AGENTES.md completo y su plan,
las entregas P00–P03, los comandos finales P03 y G07-deliverable.md como antecedente.
Inicio: rework cerrado en P03 y versión fija del motor entregado por G07, con base
identificable. Propiedad de parámetros cedida por P01/P03; sin cambios concurrentes
en el código medido. G07 no depende de este encargo ni se reabre para iniciarlo.
Tu entrega obligatoria es
TMP_VECTORIAL_ENGINE_2A2B/parity_update/P04-deliverable.md.

TRABAJO
1. Mide compilación/preparación, modular y candidato real separadamente. Empieza
   por representantes de coste bajo, medio, alto y sucesos infrecuentes; amplía
   para medir los perfiles ya definidos. Registra equipo, workers, muestras,
   semillas, horizontes, referencias reutilizadas y coste frío. No inventes tiempos.
2. Calibra solo muestras, semillas, horizontes y parámetros de ejecución. Conserva
   escenarios, variantes, observables, criterios y cobertura de P03. No añadas
   familias ni completes tests que debían estar definidos al cerrar el rework.
3. Comprueba sensibilidad y coste con criterios fijados antes de ver resultados.
   Conserva mínimos y tolerancias históricos aplicables; no rebajes muestras por
   un techo arbitrario ni repitas semillas hasta conseguir aprobación.
4. Si falta autoría, entrada o comparador del test, devuelve el defecto a P01/P02/P03
   mediante el coordinador. Si falta capacidad o aparece diferencia del candidato,
   registra el caso y propietario del motor. No ocultes huecos como ahorro ni
   declares medida/calibración completa de perfiles con obligaciones omitidas.
   No edites motores ni conviertas esta medición en una aceptación anticipada.
5. Reutiliza paralelismo y referencias válidas sin otro planificador. Distingue
   ejecución fría de ahorro por referencia modular. Mantén trazabilidad de la base.
6. Fija parámetros finales y comandos para P05 preservando todas las obligaciones.
   Esta calibración no exige que P05 haya aprobado y no sustituye sus resultados.

VALIDACIÓN Y ENTREGA
Comprueba anidamiento y ausencia de obligaciones perdidas con los checks afectados;
no escribas pruebas de reglas ni escenarios nuevos. Entrega P04-deliverable.md con
mediciones reales por motor, parámetros iniciales/finales, sensibilidad, coste,
limitaciones y comandos reproducibles P05. Separa estimaciones de medidas. Si
queda parcial, identifica casos, causa y propietario sin reabrir el cierre de G07
ni confundir la calibración pendiente con el cierre de preparación ya hecho en P03.
Resultados auxiliares en P04-results/ solo cuando sean necesarios.
```

## Prompt P05 — Campaña posterior: aceptación con la batería renovada

```text
Ejecuta P05, aceptación con la batería de paridad renovada tras el cierre del rework. Es una campaña posterior e independiente de G07; no se ejecuta durante P00–P03.
Lee TMP_VECTORIAL_ENGINE_2A2B/parity_update/PROMPTS_AGENTES.md completo, el plan
y las entregas P00–P04. Lee G07-deliverable.md para identificar la versión del
motor y el alcance de su evidencia anterior; no heredes su cobertura para los
nuevos tests. Tu entrega obligatoria es
TMP_VECTORIAL_ENGINE_2A2B/parity_update/P05-deliverable.md.

CONDICIÓN DE INICIO
Rework cerrado en P03, versión fija del motor entregado por G07 y calibración P04
terminada sobre esa base identificable. Sin escritores concurrentes en el código
que se certifica. No se requiere volver a cerrar G07 ni cambiar su batería.
Si falta una condición, registra lo pendiente; no ejecutes una aceptación ficticia.

TRABAJO
1. Ejecuta los tres perfiles contra NumPy con los comandos de P03/P04. Aprovecha
   resultados de perfiles contenidos cuando procedan de la misma revisión y cumplan
   todos los requisitos; no repetir duelos idénticos solo para tener tres informes.
   Comprueba además que cada selector ejecuta el subconjunto que promete.
2. Verifica que completo contabiliza todas las obligaciones admitidas del inventario,
   con trazabilidad al CSV, y que profundo cubre las interacciones seleccionadas.
   Las cláusulas de compilación compartida mantienen su evidencia diferenciada;
   no se convierten en ejecución vectorial por una tasa de victoria coincidente.
3. Revisa evidencia de activación, observaciones, muestras y exclusiones. Cualquier
   comportamiento requerido sin comparación aplicable impide declarar cierre,
   aunque todos los casos ejecutados pasen. No certificar nativo con evidencia NumPy.
4. Reproduce una divergencia con el menor caso ya disponible y envíala a su
   propietario P01/P02/P03 o G00-G06 por medio del coordinador. No cambies el modular,
   expectativas o tolerancias para conseguir aprobación. No edites motores.
5. Tras las correcciones, repite lo afectado y reúne una confirmación final coherente
   sobre la revisión integrada. Reutiliza evidencia no invalidada justificando su
   vigencia; no combinar resultados incompatibles de revisiones distintas.
6. Entrega propuestas de status.numpy por claves solo para la evidencia realmente
   aplicable. El coordinador escribe el CSV y conserva native. Esta campaña
   acredita la batería renovada sobre su versión fija; no sustituye el informe
   G07 ni convierte automáticamente su evidencia histórica en cobertura nueva.

ENTREGA Y CIERRE
Crea P05-deliverable.md con revisión/entradas, resultados por nivel, cobertura,
tiempos, certificados bajo P05-results/ si procede, divergencias, huecos y propuestas
para el CSV. Entrega también si queda bloqueado o parcial, con el siguiente paso
concreto. Referencia G07-deliverable.md como antecedente de versión y batería
anterior, sin exigir sobrescribirlo ni reabrir su cierre.
Solo declara aceptación si todas las obligaciones requeridas están comprobadas y
no quedan divergencias conocidas. No prometas exhaustividad de todas las posibles
combinaciones de reglas. No desarrolles nuevas pruebas modulares ni optimices.
```

## Cómo lanzar cada encargo

Copiar el bloque del agente correspondiente y asignarle una copia de la base integrada. El prompt obliga a leer este documento, por lo que sus instrucciones comunes y límites no se pierden al copiarlo. El coordinador debe facilitar las entregas previas como archivos, no como resúmenes de chat.

Las entregas y revisiones existentes se reutilizan como punto de partida; no se presupone su cierre por estar escritas. El coordinador acepta ahora la preparación de los tests y registra por separado las dependencias del motor. P04/P05 se lanzan como campaña posterior solo tras el cierre del rework y con la versión fija del motor entregado por G07; ninguno condiciona el cierre anterior de G07 o P03.
