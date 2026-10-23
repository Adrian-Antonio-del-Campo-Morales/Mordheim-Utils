# Tareas para la reforma del testing

Este documento divide `REWORK_PLAN.md` en paquetes ejecutables. Describe trabajo pendiente: ninguna tarea queda realizada por aparecer aquí. Las dependencias indican cierres verificables, no solo código escrito.

## Reglas de ejecución y propiedad

- Un coordinador mantiene el mapa de movimientos, integra los paquetes y actualiza este documento. Los demás responsables devuelven cambios, comprobaciones y bloqueos; no crean documentos de cierre independientes.
- Antes de empezar se identifica la rama, revisión y estado de trabajo real. Los cambios concurrentes se conservan y ningún paquete se apoya en una versión antigua del árbol sin declararlo.
- Un único escritor por archivo. Los archivos mixtos se asignan completos en T01; su responsable separa los destinos antes de transferirlos a otros paquetes.
- El coordinador es el único escritor de configuraciones compartidas: `pyproject.toml`, `tests/conftest.py`, launcher y secuenciador generales, configuraciones Vitest/TypeScript, scripts npm, CI y documentación común. También integra las referencias globales de cobertura y evidencias.
- Cada traslado se integra junto con sus ajustes de rutas y descubrimiento. El coordinador aplica esos ajustes al recibir cada paquete; T11 verifica su coherencia final. No se da por terminado un traslado con imports o comandos afectados rotos a la espera de T11.
- Los paquetes pueden prepararse en paralelo con propiedad disjunta. Las pruebas integradas se ejecutan sobre una revisión estable; no se regeneran fixtures mientras otros paquetes los consumen.
- Los archivos de fixtures precompilados tienen un único escritor: T06. Los consumidores solicitan incorporaciones o correcciones; no editan copias ni regeneran resultados esperados.
- Se mantienen las fases actuales, las identidades semánticas y la distinción entre autoría, revisión y ejecución. Los problemas concretos pendientes se registran en `TODO.md` por el coordinador.

## Orden de ejecución: cuatro bloques

Los números T00–T13 identifican tareas; no significan que todas deban ejecutarse una detrás de otra. Para simplificar la coordinación, se cierra un bloque completo antes de empezar el siguiente.

```text
BLOQUE 1 — Preparar
    T00: estado inicial → T01: clasificación y contrato
                         ↓
BLOQUE 2 — Tres frentes en paralelo
    A: T02: cargador → T03: rules y exportador → T06: generar fixtures
    B: T04: aplicaciones
    C: T05: tooling
    ESPERAR A QUE TERMINEN A, B Y C
                         ↓
BLOQUE 3 — Cuatro paquetes independientes
    T07: modular | T08: vectorial | T09: nativo | T10: paridad/benchmarks
    ESPERAR A QUE TERMINEN LOS CUATRO
                         ↓
BLOQUE 4 — Integrar y cerrar
    T11: integración → T12: redundancia → T13: validación final
```

### Bloque 1 — Preparación, en serie

Ejecutar T00 y después T01. El bloque termina cuando están registrados el estado inicial, los destinos de los archivos, sus responsables y el contrato de los precompilados.

### Bloque 2 — Infraestructura y reorganización, en paralelo

Después de T01 pueden trabajar tres responsables a la vez:

| Frente | Orden dentro del frente | Cuándo termina |
| --- | --- | --- |
| A — Infraestructura de motores y rules | T02 → T03 → T06, una detrás de otra | El cargador, el exportador y rules están integrados y los fixtures están generados y congelados |
| B — Aplicaciones | T04 | Los tests de las aplicaciones están trasladados e integrados con sus runners |
| C — Tooling | T05 | Los tests de herramientas y arquitectura están trasladados e integrados |

**T02, T03 y T06 no se ejecutan en paralelo entre sí.** Mientras A avanza por esas tres tareas, B y C pueden avanzar independientemente. El bloque se cierra cuando terminan T04, T05 y T06.

Este cierre conjunto es una barrera de coordinación: aunque una adaptación de motor pudiera empezar antes, en este reparto se espera a que los tres frentes estén integrados.

### Bloque 3 — Adaptar los consumidores, en paralelo

Con el bloque 2 cerrado, T07, T08, T09 y T10 pueden ejecutarse independientemente sobre los mismos fixtures congelados. Cada paquete tiene archivos propios y ninguno modifica el corpus compartido.

Con un coordinador y tres agentes ejecutores, la asignación inicial será T07, T08 y T09. Cuando uno termine, ese ejecutor toma T10; no necesita esperar a que terminen los otros dos. Para pasar al bloque 4 deben estar cerradas las cuatro tareas.

### Bloque 4 — Integración y cierre, en serie

Ejecutar T11 → T12 → T13. T12 puede repartir candidatos a redundancia entre componentes sin escritores compartidos; todos deben quedar integrados antes de T13. T13 puede repartir comprobaciones independientes sobre una misma revisión estable, sin modificar los archivos que se están validando.

El coordinador es el único escritor de los archivos comunes durante todos los bloques. Si T06 necesita corregir los fixtures durante el bloque 3, se detienen los consumidores afectados, se publica la nueva versión y se repite solo la evidencia invalidada.

## Detalle de tareas — Estado inicial y contratos

### T00 — Registrar la situación de partida

**Inicio:** antes de mover archivos, cambiar selección de suites o generar fixtures.

**Responsable y propiedad:** coordinador; inventario inicial y evidencias de ejecución.

**Trabajo:**

1. Identificar revisión, cambios sin integrar, archivos con otros propietarios y herramientas disponibles.
2. Registrar cómo descubren tests pytest, Vitest y Node; incluir los corpus declarativos, los scripts y los comandos de CI.
3. Obtener las selecciones e identidades de partida. Diferenciar archivos, funciones, casos parametrizados y escenarios declarativos; no confundirlos con ejecuciones aprobadas.
4. Reutilizar evidencia válida y ejecutar las comprobaciones necesarias para fijar fallos previos y cobertura de referencia. Declarar lo no ejecutado o bloqueado.

**Fin verificable:** existe una referencia trazable de qué se selecciona, qué se ha ejecutado y qué falla antes de la reforma; los cambios concurrentes tienen propietario identificado.

**Límite:** no mover tests ni cambiar presupuestos, reglas o expectativas.

### T01 — Cerrar clasificación, propiedad y formato de intercambio

**Inicio:** T00 cerrado.

**Responsable y propiedad:** coordinador; mapa único de movimientos y contrato común.

**Trabajo:**

1. Asignar cada archivo o grupo coherente a tooling, rules, engines o applications. Dentro de rules, separar knowledge, construction e integration.
2. Resolver los archivos mixtos y asignar un único responsable a cada original y a cada destino. Distinguir comprobaciones de compilación de comprobaciones de ejecución.
3. Identificar las entradas que necesitan congelarse: combatientes, contexto, participantes auxiliares, decisiones, estado inicial, dados y expectativas cuando correspondan.
4. Fijar el formato versionado, las claves de casos y la interfaz compartida de exportación/carga. Incluir estructuras anidadas, valores opcionales, secuencias, procedencia y huellas; conservar identificadores usados por el cálculo.
5. Asignar las pruebas del codec a engines/shared, las del exportador a rules/construction y los archivos de implementación a responsables exclusivos. Concretar también los destinos de helpers y fixtures compartidos entre lenguajes.
6. Anotar candidatos a redundancia, sin eliminarlos todavía. Los originales E2E y semánticos conservan su función de integración con KB.

**Fin verificable:** todos los archivos tienen destino y propietario; el contrato permite desarrollar productor y consumidores sin decisiones incompatibles; están identificadas las entradas y expectativas que deben conservarse.

**Límite:** no deducir equivalencia semántica por nombres, cuerpos de código o conteos; no cambiar interpretaciones de reglas.

## Detalle de tareas — Infraestructura y separación por responsabilidades

### T02 — Codec y cargador de entradas de ejecución

**Inicio:** T01 cerrado.

**Propiedad:** implementación del codec/cargador acordada en T01 y tests en `tests/engines/shared/`. No escribe el corpus definitivo.

**Trabajo:** reconstruir y serializar las estructuras completas de ejecución; validar versión, tipos y campos; conservar valores opcionales y secuencias. Rechazar archivos ausentes o incompatibles sin recompilación automática. Mantener los imports independientes del compilador, la KB y los runners que cargan corpus originales.

**Fin verificable:** las comprobaciones de ida y vuelta conservan las estructuras; las entradas inválidas fallan con causa identificable; el cargador funciona con el acceso a KB y fuentes bloqueado. La interfaz queda estable para T03 y los consumidores.

### T03 — Rules y exportador explícito

**Inicio:** T02 cerrado.

**Propiedad:** tests y corpus asignados a `tests/rules/knowledge/`, `construction/` e `integration/`; implementación del exportador y sus pruebas. No escribe fixtures definitivos fuera de T06.

**Trabajo:**

1. Trasladar las pruebas de KB, construcción, especificaciones semánticas y E2E originales, conservando sus identidades, expectativas, metadatos y referencias de evidencia.
2. Mantener las comprobaciones reales de conexión entre KB, compilador y combate; las negativas de admisión siguen comprobando rechazos reales.
3. Implementar la exportación explícita de las configuraciones identificadas en T01, incluidos proveedores de contexto y ajustes propios de benchmarks.
4. Exportar estructuras de ejecución y procedencia técnica sin descripciones ni comentarios de las fuentes. No derivar expectativas normativas del motor.
5. Entregar al coordinador los cambios de rutas de loaders, herramientas y configuraciones necesarios para integrar los traslados.

**Fin verificable:** las suites de rules se descubren por sus nuevos destinos, los casos mantienen su significado y el exportador genera entradas reproducibles que el cargador T02 puede reconstruir sin pérdida.

### T04 — Aplicaciones y sus contratos

**Inicio:** T01 cerrado.

**Propiedad:** tests asignados a `tests/applications/combat_lab/` y `warband_manager/`, sus helpers y datos propios. Las configuraciones comunes las modifica el coordinador.

**Trabajo:** agrupar servicios, persistencia, consola de producto, dominio de campaña e interfaces con sus aplicaciones. Mantener los contratos de campaña y los tests de integración propios del producto. Diferenciar Node y navegador cuando sea necesario; conservar una sola copia de los datos compartidos.

**Fin verificable:** los runners correspondientes descubren los casos previstos, imports y recursos se resuelven desde las nuevas rutas y las comprobaciones afectadas conservan su comportamiento. Los cambios de configuración se han integrado con el coordinador.

### T05 — Tooling y arquitectura

**Inicio:** T01 cerrado.

**Propiedad:** tests asignados a `tests/tooling/` y sus helpers; los archivos originales mixtos siguen el reparto exclusivo de T01.

**Trabajo:** reunir pruebas del launcher, secuenciador, herramientas de verificación, informes, detectores y herramientas web. Trasladar los límites generales de arquitectura; dejar las restricciones específicas con su componente. Separar las comprobaciones del tooling de las que realmente ejecutan un motor. Registrar la repetición de ejecuciones para resolverla en T12.

**Fin verificable:** tooling tiene selección propia, sus detectores conservan controles positivos y negativos y no absorbe por error las pruebas funcionales de motores o aplicaciones.

## Detalle de tareas — Fixtures y consumidores de motores

### T06 — Generar y congelar las entradas precompiladas

**Inicio:** T03 cerrado; están disponibles el exportador y el codec.

**Propiedad exclusiva:** `tests/engines/fixtures/`, incluido `compiled-cases.json`.

**Trabajo:** generar las entradas requeridas por los consumidores de T07–T10. Comprobar integridad, referencias, ausencia de prosa original y correspondencia con sus configuraciones de origen. Registrar versión y huellas. Conservar las expectativas revisadas, dados, decisiones y estado inicial de los casos deterministas que se reutilicen.

**Fin verificable:** el corpus contiene las entradas acordadas en T01; exportar y cargar conserva íntegramente las estructuras; los casos tienen claves estables y procedencia trazable. Se identifica la versión congelada que consumirán T07–T10.

**Límite:** un caso que no puede representarse se declara con su causa, sin inventar entradas, omitirlo silenciosamente ni convertirlo en aprobado. Si un consumidor descubre una carencia, T06 la corrige de forma serial, publica una nueva versión y señala qué evidencia debe repetirse.

### T07 — Tests del motor modular

**Inicio:** bloque 2 cerrado: T04, T05 y T06 terminados e integrados.

**Propiedad:** `tests/engines/modular/` y los originales asignados a este paquete.

**Trabajo:** sustituir la preparación mediante KB/compilador por cargas de fixtures, conservando las aserciones de reglas, secuencias, estados y decisiones. Mantener entradas numéricas directas para primitivas. Las pruebas cuyo objeto sea comprobar una compilación permanecen en rules conforme al mapa T01.

**Fin verificable:** los tests asignados al modular se colectan y ejecutan con el acceso a KB y fuentes bloqueado; mantienen las expectativas e identidades previstas, sin llamadas indirectas a `compile_fighter`.

### T08 — Tests del motor vectorial

**Inicio:** bloque 2 cerrado: T04, T05 y T06 terminados e integrados.

**Propiedad:** `tests/engines/vectorized/` y los originales asignados a este paquete.

**Trabajo:** adaptar la preparación a los fixtures comunes sin cambiar las aserciones de lotes, estados, decisiones, reproducibilidad y paralelismo. Mantener controles de límites y errores. No reimplementar reglas ni modificar el motor para acomodar los tests.

**Fin verificable:** los casos previstos conservan su comportamiento y se ejecutan sin KB ni compilador, también en sus procesos auxiliares. Las restricciones del backend siguen siendo visibles.

### T09 — Tests del motor nativo

**Inicio:** bloque 2 cerrado: T04, T05 y T06 terminados e integrados.

**Propiedad:** `tests/engines/native/` y los originales asignados a este paquete.

**Trabajo:** usar los mismos fixtures, conservar los controles específicos de la extensión y distinguir su ausencia, incompatibilidad y ejecución real. Comprobar que las pruebas funcionales utilizan el backend nativo y no una sustitución silenciosa.

**Fin verificable:** con una extensión compatible, los casos previstos se ejecutan sin KB y mantienen sus expectativas. Si no puede ejecutarse la extensión, la preparación puede quedar implementada, pero la validación nativa queda explícitamente pendiente y T13 no puede certificarla como pasada.

### T10 — Paridad y benchmarking con entradas precompiladas

**Inicio:** bloque 2 cerrado: T04, T05 y T06 terminados e integrados.

**Propiedad:** tests de `tests/engines/parity/` y rutas de ejecución de paridad/benchmarking asignadas en T01. Los tests del formato de informes pertenecen a T05/T12; las opciones compartidas del CLI las integra el coordinador.

**Trabajo:**

1. Separar preparación y ejecución para que comparaciones y benchmarks carguen directamente el corpus, incluidos contexto y participantes auxiliares.
2. Proporcionar las mismas entradas al modular, vectorial y nativo. Conservar las magnitudes, tolerancias y estados de resultado definidos por las herramientas actuales.
3. Mantener calentamientos, repeticiones, tamaños de lote y medición de rendimiento; adaptar también los workers y las estrategias paralelas existentes.
4. Conservar la ejecución del modular como oráculo. Las referencias guardadas son opcionales y deben identificar las entradas y parámetros a los que corresponden.
5. Escribir resultados generados en `outputs/`, conservando los contratos de informes y comparación con resultados anteriores.

**Fin verificable:** al menos una ejecución representativa de cada ruta soportada demuestra que la carga directa funciona, que cada backend solicitado se identifica correctamente y que el aislamiento se mantiene en el proceso principal y en los auxiliares. Las rutas incompatibles se informan, sin aprobarse mediante fallback.

## Detalle de tareas — Integración y depuración

### T11 — Consolidar selección, comandos y conservación

**Inicio:** T04, T05 y T07–T10 cerrados; sus ajustes globales ya se han integrado con cada traslado.

**Responsable y propiedad:** coordinador; archivos comunes, configuración de runners, CI, cobertura y documentación.

**Trabajo:** reconciliar los scopes y fases con la nueva estructura, mantener los comandos existentes y comprobar los globs de pytest, Vitest y Node. Actualizar referencias de evidencia y herramientas auxiliares. Conciliar la selección final con T00 mediante el mapa T01, incluyendo los corpus originales y los casos precompilados derivados.

**Fin verificable:** cada caso previsto tiene destino y runner; no hay pérdidas accidentales, inclusiones dobles, imports rotos ni referencias activas a rutas retiradas. Los gates de cobertura siguen seleccionando sus detectores y no han reducido sus garantías.

**Límite:** el cambio de ruta de un node ID se registra como movimiento, no como eliminación y creación sin relación. Los recuentos no sustituyen la correspondencia entre identidades.

### T12 — Consolidar tests y eliminar redundancia demostrada

**Inicio:** T11 cerrado; existe una selección integrada comparable con la inicial.

**Propiedad:** los responsables de cada componente, con reparto disjunto; coordinador para cambios entre componentes, CI y evidencia común.

**Trabajo:**

1. Revisar cada candidato registrado: contrato, entradas, límites, implementación ejercitada y fallo detectado. Los cinco pares con cuerpo idéntico no se consideran duplicados por ese único motivo.
2. Fusionar o parametrizar solo cuando se conserve la capacidad de detectar fallos. Identificar el sustituto de cada comprobación retirada.
3. Probar formatos de informes con resultados controlados, conservando comprobaciones específicas de conexión real con los motores.
4. Mantener el control de no regresión E2E como paso propio de CI y excluir ese archivo de la batería inmediatamente anterior para evitar su doble ejecución.
5. Comparar la cobertura y reutilizar detectores o mutaciones existentes; añadir comprobaciones enfocadas solo cuando sean necesarias para demostrar la sustitución. No abrir una campaña general de mutaciones o rendimiento.

**Fin verificable:** cada retirada o fusión tiene justificación y sustitución trazable; se cuantifican casos conservados, movidos, fusionados y retirados sin contabilizar un simple traslado como reducción. La selección y las comprobaciones afectadas quedan integradas de nuevo.

**Límite:** no rebajar presupuestos, borrar fallos previos ni retirar pruebas de implementaciones distintas por parecido superficial.

## Detalle de tareas — Aceptación final

### T13 — Validar el conjunto y cerrar la reforma

**Inicio:** T12 cerrado, archivos integrados y fixtures congelados. No hay escritores activos sobre los componentes que se validan.

**Responsable:** coordinador. Puede repartir comprobaciones independientes sobre la misma revisión, con salidas separadas y sin regeneraciones compartidas.

**Trabajo:**

1. Confirmar selección, fases, comandos existentes y descubrimiento sin duplicados en todos los runners.
2. Ejecutar las suites de motores con bloqueo de acceso a KB y fuentes desde antes de importar o colectar, propagado a los workers. Demostrar que un intento deliberado de acceso es detectado.
3. Ejecutar rules y los E2E originales con su integración real; conservar sus controles de admisión y evidencia aceptada.
4. Verificar aplicaciones, tooling, codec, exportación y rutas de paridad/benchmarking afectadas. Comprobar explícitamente la ejecución del backend nativo cuando corresponda.
5. Confirmar conservación de cobertura y expectativas; reutilizar evidencia de paquetes que siga siendo válida en la revisión integrada y repetir solo la invalidada o necesaria para el cierre.
6. Recoger en este documento el resultado global, las comprobaciones realizadas y los límites. Registrar defectos pendientes en `TODO.md`.

**Fin verificable:** están satisfechos los criterios de aceptación de `REWORK_PLAN.md`, cada cambio de test está explicado y ninguna validación obligatoria se presenta como pasada si sigue pendiente, bloqueada o sin ejecutar.

**Cierre:** esta tarea concluye la reforma del testing. No incluye cambios de reglas de combate ni implementación u optimización adicional de los motores.
