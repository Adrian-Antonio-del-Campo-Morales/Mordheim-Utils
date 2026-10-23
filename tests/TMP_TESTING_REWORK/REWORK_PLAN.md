# Reorganización de tests y separación de los motores de la KB

## Objetivo y decisiones acordadas

Organizar todo el árbol por responsabilidad, aislar los tests de los tres motores mediante entradas precompiladas y eliminar únicamente redundancias demostradas.

Se mantienen las fases de ejecución actuales: los directorios indicarán **qué componente se prueba**; las fases seguirán indicando **qué garantía se verifica y en qué orden**.

La inspección estática registra 209 archivos Python con 2.469 funciones de test, 92 archivos TypeScript y 68 archivos web. Estas cifras no equivalen a casos ejecutados ni permiten determinar cuántos son prescindibles.

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

## Migración y aceptación

1. Registrar la selección actual y los fallos conocidos sobre una misma revisión, preservando los cambios concurrentes.
2. Reubicar por responsabilidad y actualizar imports, runners, scopes, proyectos Vitest, configuración TypeScript, CI, cobertura y referencias de evidencia.
3. Introducir fixtures y adaptar las suites de motores, paridad y benchmarks.
4. Aplicar las consolidaciones demostradas y ejecutar la validación integrada final.

La entrega deberá demostrar:

- Correspondencia entre los casos anteriores y su nueva ubicación o sustitución justificada.
- Conservación de identidades semánticas, expectativas y evidencias aceptadas.
- Colección y ejecución de motores con acceso a KB y fuentes bloqueado desde el inicio del proceso, incluidos los workers.
- Igualdad de las estructuras antes de exportar y después de cargar.
- Ausencia de pérdida de cobertura o detectores relevantes; no se rebajarán presupuestos para absorber pérdidas.
- Descubrimiento de cada test por su runner previsto, sin inclusiones duplicadas.
- Funcionamiento de los comandos existentes con los nuevos destinos.

No se cambiarán reglas de combate ni se corregirán defectos ajenos como parte de los movimientos. Los problemas nuevos se registrarán en `TODO.md`.
