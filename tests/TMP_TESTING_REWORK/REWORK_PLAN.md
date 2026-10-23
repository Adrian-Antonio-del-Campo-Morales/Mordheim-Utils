# Reorganización de tests y separación de los motores de la KB

## Objetivo y decisiones acordadas

Organizar todo el árbol por responsabilidad, aislar los tests de los tres motores mediante entradas precompiladas y eliminar únicamente redundancias demostradas.

Se mantienen las fases de ejecución actuales: los directorios indicarán **qué componente se prueba**; las fases seguirán indicando **qué garantía se verifica y en qué orden**.

La reforma no depende de los fallos ni de los resultados de ejecución actuales. El inventario inicial documentará estructura, selección e identidades, sin ejecutar tests ni recopilar resultados previos. Las comprobaciones posteriores validarán los cambios de la reforma; los defectos funcionales ajenos no se convierten en tareas ni requisitos de cierre.

Se reutilizarán y adaptarán los tests existentes. No se desarrollarán nuevos tests ni se aplicarán mejoras fuera de la tarea asignada.

## Política de comprobaciones mínimas

Cerrar una tarea exige comprobar sus cambios y sus contratos; no exige dejar verde una batería completa. Esta política se aplica a agentes, pre-coordinadores y coordinador final, y rige los criterios de cierre de todas las tareas.

| Cambio | Comprobación suficiente |
| --- | --- |
| Traslado de tests, helpers o datos; actualización de rutas | Sintaxis, imports, referencias e inventario/colección de los archivos afectados, sin ejecutar sus cuerpos |
| Selección y configuración de runners | Listado de casos y conservación de identidades, sin pérdidas ni duplicados; el coordinador agrupa colección global y typecheck |
| Cargador y exportador | Comprobaciones puntuales de ida y vuelta, conservación de datos, rechazo de entradas incompatibles e independencia de KB donde corresponda |
| Adaptación de un motor a fixtures | Colección del paquete y una muestra mínima de casos existentes representativos de la conexión modificada |
| Conexión de paridad o benchmarks | Un caso pequeño por ruta modificada, con parámetros controlados; sin campañas estadísticas ni mediciones de rendimiento amplias |
| Consolidación de tests | Correspondencia de contratos, expectativas y detectores; ejecutar solo los casos necesarios para verificar la sustitución |

- Cada subagente comprueba exclusivamente su paquete. No ejecuta suites completas de applications, tooling, rules o engines para validar un cambio local.
- El coordinador realiza una única comprobación integrada de selección, imports y configuración, reutilizando lo ya comprobado; el typecheck se agrupa por workspace afectado y solo se repite si cambia una entrada relevante.
- La evidencia se conserva con comando, selección, revisión o entradas relevantes, resultado y límites. Integrar otro paquete no la invalida si no cambian el código ni las dependencias que comprobaba.
- Repetir una comprobación requiere una causa identificada: cambio de código, entradas o dependencia relevante, o corrección de un defecto introducido por la reforma. No repetir selecciones ya terminadas por costumbre, para confirmar un resultado ajeno o porque otro paquete haya finalizado.
- Los fallos ajenos se comunican sin investigarlos ni corregirlos y no impiden entregar el paquete. Los defectos de rutas, carga, selección o contratos causados por la reforma sí se resuelven dentro de su tarea, con una repetición acotada.
- La certificación funcional amplia, las baterías completas y las campañas de cobertura, mutaciones, estadística o rendimiento quedan fuera de los cierres, incluido T13. Requieren una petición explícita separada. La aceptación de la reforma no se presentará como certificación funcional global.

### Paralelismo de las comprobaciones seleccionadas

- Usar el xdist existente para tests Python independientes: `python -u -m pytest <archivos-o-nodeids-afectados> -n 4 --dist=load -q --durations=10 --tb=short`. Con varios agentes, dos workers por agente; con una única ejecución integrada y recursos disponibles, hasta cuatro. No usar `-n auto` indiscriminadamente.
- En el secuenciador por fases usar su opción `--workers N`, respetando las barreras actuales y sin añadir `-n` ni `--dist`. No cambiar el scheduler como parte de esta política. La colección sin ejecución se mantiene serial.
- Vitest ya reparte archivos: seleccionar solo los afectados desde su workspace y limitar con `--maxWorkers=2` cuando haya otros agentes ejecutando comprobaciones. No añadir concurrencia dentro de los archivos de test.
- Evitar pools anidados y escritores compartidos. Si xdist reparte casos, no multiplicar además los workers internos del motor. Las operaciones sobre fixtures compartidos y las comprobaciones sensibles a tiempos permanecen seriales.
- Mantener salida visible, sin `| tail`, y sesiones persistentes consultables. Ante un timeout de la herramienta, comprobar si el proceso propio sigue activo antes de relanzar; conservar resultados ya obtenidos y no interrumpir procesos ajenos.
- El paralelismo acelera la selección mínima; no justifica ampliar su alcance ni desarrollar infraestructura adicional.

## Arquitectura propuesta

```text
tests/
├── tooling/            # Launcher, verificación, informes y herramientas web
├── rules/
│   ├── knowledge/      # Esquemas, referencias, traducciones y artefactos KB
│   ├── construction/   # Elegibilidad, compilación, concesiones y rechazos
│   └── integration/    # Recorrido real desde la KB hasta el combate
├── engines/
│   ├── fixtures/       # Entradas precompiladas compartidas por los motores
│   │   └── compiled-cases.json
│   ├── shared/         # Contratos de ejecución, primitivas y cargador de fixtures
│   ├── modular/
│   ├── vectorized/
│   ├── native/
│   └── parity/
└── applications/
    ├── combat_lab/
    └── warband_manager/
```

- La raíz tendrá cuatro bloques por responsabilidad: tooling, rules, engines y applications. Integración, fixtures y soporte se ubicarán dentro del componente al que pertenecen.
- Dentro de cada responsabilidad se distinguirá Python, Node o navegador cuando lo exija su ejecución.
- Los contratos de campaña pertenecen a Warband Manager; la elegibilidad compartida, a `rules/construction`; los artefactos de conocimiento, a `rules/knowledge`.
- La consola del producto pertenece a Combat Lab. El launcher del repositorio y su secuenciador pertenecen a tooling.
- Los límites generales entre paquetes se comprobarán en tooling; los contratos de arquitectura específicos permanecerán con su componente. Los contratos compartidos de ejecución se agruparán en `engines/shared`.
- Las especificaciones semánticas y los E2E originales se conservarán en `rules/integration`, con sus declaraciones, expectativas y evidencias. La integración propia de cada aplicación permanecerá dentro de esa aplicación.
- Los fixtures y helpers serán locales a su propietario. Los datos compartidos entre lenguajes se conservarán una sola vez dentro de la responsabilidad correspondiente.
- Los archivos mixtos se dividirán cuando comprueben contratos separables. Un escenario coherente que atraviese varias capas permanecerá como integración del componente correspondiente.

## Entradas precompiladas y ejecución

- Los tests de motores que necesiten combatientes cargarán `tests/engines/fixtures/compiled-cases.json`, con `CompiledFighter`, contexto resuelto y participantes auxiliares. Las pruebas de primitivas conservarán sus entradas numéricas directas.
- Modular, vectorial, nativo, paridad y benchmarks consumirán las mismas entradas precompiladas, sin duplicar los fixtures por motor. La división en más archivos se hará solo cuando el tamaño o la separación de familias lo justifiquen.
- Los casos deterministas conservarán dados, decisiones, estado inicial y expectativas revisadas. Las expectativas no se regenerarán a partir de las salidas del motor.
- Un exportador explícito preparará las entradas utilizando la KB. Guardará versión, procedencia y huellas de los datos; excluirá descripciones y comentarios originales.
- El cargador reconstruirá y validará las estructuras sin importar el compilador ni los cargadores de conocimiento. Un fixture ausente o incompatible producirá un error; nunca activará una recompilación automática.
- Las pruebas de generación desde la KB pertenecerán a `rules/construction`; las del cargador independiente de la KB, a `engines/shared`.
- Paridad y benchmarks compartirán esas entradas, también en procesos auxiliares. El modular seguirá ejecutándose como oráculo; las referencias estadísticas guardadas serán resultados opcionales.
- Los resultados generados de benchmarks y comparaciones permanecerán en `outputs/`. Los fixtures de ejecución y las expectativas deterministas revisadas permanecerán versionados junto a sus casos.
- Las pruebas que comprueben la conexión real entre reglas, compilación y combate permanecerán en `rules/integration`. Congelar sus entradas no sustituirá esa garantía.

### Preparación individual por configuración (2026-10-23)

**Sustituye** el despacho nominal T07-A/B/C/D para las preparaciones pendientes. Las listas, sus huellas y sus recuentos se conservan como inventario y evidencia; no asignan trabajo.

- Se conservan las conversiones anteriores válidas: nombres, parametrizaciones, aserciones, dados, decisiones, contexto y expectativas no cambian.
- Cada preparación pendiente se resuelve con un **snapshot individual** indexado por el `FighterBuild` completo y por el contexto de compilación relevante. Varios tests que construyan exactamente la misma configuración reutilizan el mismo snapshot.
- Se mantienen los builders y las transformaciones posteriores originales; **solo** se sustituye la llamada al compilador por el cargador común. Los cuerpos no se reescriben para acomodar el formato.
- Los contratos de construcción de `rules/construction` siguen usando el compilador real: su objeto es la compilación, no la ejecución.
- Una entrada ausente o incompatible falla de forma explícita. No hay recompilación automática, sustitución aproximada ni caso de reserva.
- El formato concreto del índice y del snapshot no se fija aquí: lo acuerdan el cargador y la generación antes de producir entradas.

**Responsabilidades vigentes**

- **Agente 1 — contratos:** integra en `tests/rules/construction/` los contratos de construcción ya separados. No adapta consumidores ni genera snapshots.
- **Agente 2 — cargador:** implementa el cargador común y su contrato de carga. No genera snapshots ni edita contratos.
- **Agente 3 — configuraciones y snapshots:** reúne las configuraciones pendientes y genera los snapshots cuando el formato esté acordado. Es el único que compila entradas; no edita tests consumidores ni contratos.
- **Consumidores:** su adaptación depende de que el cargador y los snapshots estén disponibles; no se inicia por bloques. Se mantiene un único escritor por archivo y el coordinador registra la propiedad.

La validación sigue siendo la mínima: revisión estática y comprobaciones puntuales del cargador y de la correspondencia de entradas. La compilación puntual de entradas corresponde solo al responsable de generación; no se ejecutan baterías completas, certificación funcional ni bloqueos de KB.

## Análisis y reducción de redundancia

Antes de retirar pruebas, se clasificará cada candidata por contrato, entradas, límites comprobados, implementación ejecutada y fallo que detecta.

Se aplicarán estos criterios:

- **Conservar** comprobaciones de una misma regla que detecten fallos distintos en compilación, ejecución o integración.
- **Fusionar o parametrizar** comprobaciones equivalentes cuando se mantengan los límites y la identificación de fallos.
- **Separar informes y ejecución:** comprobar formatos con resultados controlados y conservar pruebas específicas de conexión con los motores.
- **Evitar ejecuciones repetidas:** mantener el control E2E de no regresión como paso visible de CI y excluirlo de la batería ejecutada inmediatamente antes.
- **Retirar** pruebas de comportamiento eliminado o comprobaciones subsumidas solo cuando exista un sustituto identificado y evidencia suficiente.

Los cinco pares con cuerpos idénticos encontrados no se eliminarán automáticamente: actualmente ejercitan implementaciones distintas.

El resultado cuantificará pruebas conservadas, trasladadas, fusionadas y retiradas, con su justificación. No se fijará un objetivo artificial de reducción.

## Estado de reconciliación y cierre documental (2026-10-23)

- **T11 aplicada.** La selección apunta a los destinos actuales: los 13 `SCOPE_PATHS` de `tools/mordheim-utils.py` (29 referencias, 25 rutas únicas) y las 8 suites de `coverage_gate.DEFAULT_SUITES` resuelven en `tests/engines/**`, `tests/rules/**`, `tests/applications/**` y `tests/tooling/**`; el presupuesto de `tests/tooling/verification/fixtures/coverage/budget.json` conserva esquema, áreas y líneas, con solo su lista `suites` remapeada a esas 8 rutas. El manifiesto se remapeó (80 consumidores, 4 exclusiones), pasó de 1.718 a **1.734** claves y registra **14** destinos de rules, conservando los 6.385 casos y su `corpus_sha256`. C7 quedó aplicado en CI: la batería E2E excluye `test_non_regression.py` y el paso propio del archivo se mantiene.
- **T12 cerrada documentalmente.** C7 aplicado; C1–C6 y C8–C12 conservados sin nuevas consolidaciones ni retiradas, con sus motivos en `REWORK_PLAN_TASKS.md`. Se mantienen los presupuestos y no se declara certificación funcional.
- **Excepciones registradas.** Los rechazos deliberados del compilador mezclados con ejecución y el caso `cripple` de T08 conservan `compile_fighter` real; no se sustituyen por un error de snapshot ausente.
- **T07 vigente.** `compiled-builds.json` tiene **529 entradas**: las 520 de la revisión anterior (incluidas las tres de Vengeful Hatred) más nueve requests necesarios detectados al ejecutar los consumidores. Las 520 entradas anteriores se conservaron sin cambios. `test_vengeful_hatred_warband_type_covers_every_warband_of_that_type` lleva `usefixtures("_frozen_compiles")` y sus seis preparaciones resuelven. El generador conserva los resultados congelados por generación por unión. Los rechazos deliberados siguen en el compilador real. Esto no altera la selección, el manifiesto ni el presupuesto de T11.
- **Reconexión modular.** `test_psychology_identity.py` conecta 11 de sus 20 tests y `test_defence_parries_and_ward.py` 15 de 92; el resto de modular usa el patrón `compile_fighter = None` con fixture o ya recibe `compiled_builds.fighter`. El test de warband-type de Vengeful Hatred queda conectado con el documento de builds regenerado, que ya contiene sus tres entradas antes ausentes. Permanecen con compilador real por rechazo deliberado cuatro tests mixtos (Knight of Purity, Magic Acorn, Khemrian Seduction y Shadow Dances) y el caso `cripple`.
- **T13 completada para la migración.** `python -m pytest --collect-only -q` recogió **13.148 tests** con `EXIT 0`, sin errores ni duplicados; `npm run typecheck` devolvió `EXIT 0` en ambos workspaces. La ejecución manual del usuario detectó defectos de fixtures, rutas, snapshots y bindings; se corrigieron y los **25 ítems afectados seleccionados pasan**, reutilizando la evidencia integrada. No se repitió ni se declara verde una batería funcional global. Se mantienen las excepciones registradas. Las rutas antiguas de `docs/reference/test-sequence.md` (líneas 275 y 277) son evidencia histórica y se conservan.

## Migración y aceptación

**Actualización de alcance (2026-10-23):** se retira la comprobación de ausencia de acceso a la KB: no se implementan bloqueos de imports o archivos, instrumentación, stubs ni pruebas de intentos deliberados de acceso, tampoco para workers. Se mantiene la preparación mediante entradas precompiladas; basta su revisión estática. Los imports indirectos no bloquean la aceptación ni exigen desacoplar el facade de paridad. La evidencia histórica se conserva, sin repetirla ni afirmar aislamiento estricto. Solo se espera funcionamiento correcto del modular; los fallos funcionales del vectorial y nativo no se investigan dentro de esta reforma.

1. Inventariar estructura, selección e identidades de los tests sobre una revisión identificada, preservando los cambios concurrentes y sin ejecutar pruebas de partida.
2. Reubicar por responsabilidad y actualizar imports, runners, scopes, proyectos Vitest, configuración TypeScript, CI, cobertura y referencias de evidencia.
3. Introducir fixtures y adaptar las suites de motores, paridad y benchmarks. Las 345 candidatas que dependían del compilador y el reparto nominal T07-A/B/C/D quedan como inventario histórico: el despacho por bloques está sustituido por la preparación individual descrita en «Preparación individual por configuración». Los 61 contratos de construcción se integran en `rules/construction` y conservan el compilador real; las preparaciones de ejecución restantes se resuelven con snapshots por `FighterBuild`. Se conserva un único escritor por archivo compartido y por corpus.
4. Aplicar las consolidaciones demostradas y realizar la comprobación integrada final mínima, reutilizando la evidencia válida de los paquetes.

La entrega deberá demostrar:

- Correspondencia entre los casos anteriores y su nueva ubicación o sustitución justificada.
- Conservación de identidades semánticas, expectativas y evidencias aceptadas.
- Revisión estática de la preparación mediante fixtures precompilados, sin llamadas a `compile_fighter` en los tests de ejecución, salvo las excepciones registradas en T12 (rechazos deliberados del compilador y el caso `cripple`). Colección afectada y muestra mínima de conexión solo cuando falte evidencia válida. No se exige ejecutar las suites completas.
- Igualdad de las estructuras antes de exportar y después de cargar.
- Conservación de contratos, detectores y presupuestos de cobertura versionados, sin capturar una medición inicial ni rebajarlos para absorber pérdidas.
- Descubrimiento de cada test por su runner previsto, sin inclusiones duplicadas.
- Funcionamiento de los comandos existentes con los nuevos destinos.

No se cambiarán reglas de combate ni se corregirán defectos ajenos como parte de los movimientos. Los problemas nuevos se registrarán en `TODO.md`. Los cierres de los paquetes y la aceptación final se basan en esta política de comprobaciones mínimas, sin repetir baterías amplias ya ejecutadas ni exigir su éxito.
