# Tareas para la reforma del testing

Este documento divide `REWORK_PLAN.md` en paquetes ejecutables. Describe trabajo pendiente: ninguna tarea queda realizada por aparecer aquí. Las dependencias indican cierres verificables, no solo código escrito.

Los fallos y resultados de ejecución actuales quedan fuera del plan: no se recopilan como referencia inicial ni condicionan el inicio de las tareas. Las validaciones posteriores se limitan a comprobar la reforma; los defectos funcionales ajenos no amplían el alcance ni impiden cerrar el trabajo asignado.

## Reglas de ejecución y propiedad

- Un coordinador mantiene el mapa de movimientos, integra los paquetes y actualiza este documento. Los demás responsables devuelven cambios, comprobaciones y bloqueos; no crean documentos de cierre independientes.
- Antes de empezar se identifica la rama, revisión y estado de trabajo real. Los cambios concurrentes se conservan y ningún paquete se apoya en una versión antigua del árbol sin declararlo.
- No se desarrollan nuevos tests ni se aplican mejoras fuera de la tarea asignada. Se reutilizan y adaptan los tests existentes y se realizan únicamente las comprobaciones necesarias para verificar los cambios propios.
- Un único escritor por archivo. Los archivos mixtos se asignan completos en T01; su responsable separa los destinos antes de transferirlos a otros paquetes.
- El coordinador es el único escritor de configuraciones compartidas: `pyproject.toml`, `tests/conftest.py`, launcher y secuenciador generales, configuraciones Vitest/TypeScript, scripts npm, CI y documentación común. También integra las referencias globales de cobertura y evidencias.
- Cada traslado se integra junto con sus ajustes de rutas y descubrimiento. El coordinador aplica esos ajustes al recibir cada paquete; T11 verifica su coherencia final. No se da por terminado un traslado con imports o comandos afectados rotos a la espera de T11.
- Los paquetes pueden prepararse en paralelo con propiedad disjunta. Las pruebas integradas se ejecutan sobre una revisión estable; no se regeneran fixtures mientras otros paquetes los consumen.
- Los archivos de fixtures precompilados tienen un único escritor: T06. Los consumidores solicitan incorporaciones o correcciones; no editan copias ni regeneran resultados esperados.
- Los snapshots individuales de configuración tienen un único responsable de generación: el agente 3 del reparto vigente de T07. El cargador común pertenece al agente 2 y la integración de los contratos de construcción al agente 1. Los consumidores solicitan entradas y no compilan, duplican ni aproximan sustitutos. Ver «T07 — Enfoque acordado para las preparaciones pendientes».
- Se mantienen las fases actuales, las identidades semánticas y la distinción entre autoría, revisión y ejecución. Los problemas concretos pendientes se registran en `TODO.md` por el coordinador.

## Comprobaciones mínimas obligatorias para los agentes

**Retirada de la comprobación de acceso a KB (2026-10-23):** esta decisión prevalece sobre los registros históricos de entrega. No se implementan ni ejecutan bloqueos de imports/archivos, instrumentación, stubs o pruebas de detección de acceso, tampoco en workers. Se mantiene el consumo de fixtures precompilados y la retirada de `compile_fighter` de la preparación de tests de ejecución, comprobables por revisión estática. Los imports indirectos no bloquean cierres ni requieren desacoplar el facade de paridad. La evidencia histórica se conserva sin repetirla y no se presenta como prueba de aislamiento estricto. Solo el modular se espera operativo; no se investigan fallos funcionales del vectorial o nativo.

Se aplica la política de `REWORK_PLAN.md` y `AGENTS.md`. Esta sección rige cualquier mención genérica a «ejecutar», «validar» o «fin verificable» de las tareas. Los registros históricos de entregas se conservan como evidencia; sus baterías amplias no deben repetirse ni se convierten en requisitos para otros agentes.

| Tareas | Verificación de cierre |
| --- | --- |
| T00–T01 | Inspección e inventario; colección/listado solo si hace falta. Sin ejecución funcional |
| T02 | Casos puntuales del contrato del codec, ida y vuelta y carga de fixtures; reutilizar los ya comprobados, sin comprobar bloqueo de KB |
| T03 | Conservación del inventario e imports de rules y comprobación puntual del exportador; sin ejecutar construction, E2E o semánticas completos |
| T04–T05 | Sintaxis, imports, referencias y colección/listado de los archivos movidos. Ejecución puntual solo si se modificó lógica propia de la tarea; no baterías completas de aplicaciones o tooling |
| T06 | Generación, validación de formato, huellas y reconstrucción de datos; sin ejecutar motores ni repetir las pruebas del codec/exportador si siguen siendo válidas |
| T07–T09 | Revisión estática de la preparación con fixtures; colección afectada y muestra mínima de conexión solo si falta evidencia válida; sin bloqueo de KB ni suites completas |
| T10 | Un caso pequeño por ruta modificada de paridad/benchmarking y de workers cuando corresponda; sin certificación estadística o campaña de rendimiento |
| T11 | Una única reconciliación integrada de selección/configuración y los typechecks de workspaces afectados; reutilizar evidencia válida, sin ejecutar todas las suites |
| T12 | Comprobación de los contratos conservados y solo los casos necesarios para confirmar las sustituciones |
| T13 | Revisar la evidencia de los paquetes y completar únicamente comprobaciones integradas pendientes; sin repetir todas las anteriores ni ejecutar una batería funcional global |

**Reglas de repetición y entrega:** cada agente registra comando, selección, revisión o entradas relevantes, resultado y límites en su entrega. Una comprobación solo se repite si cambió el código, una entrada o dependencia relevante, o se corrigió un defecto introducido por la reforma; se indica la causa. El coordinador agrupa los checks compartidos una vez sobre el estado integrado. Un fallo funcional ajeno se comunica sin investigar ni corregir y no bloquea la entrega; un defecto causado por la reforma se corrige dentro de la tarea. No se desarrollan nuevos tests para extender estas comprobaciones.

**Paralelismo inmediato:** para tests Python independientes usar `python -u -m pytest <archivos-o-nodeids-afectados> -n 2 --dist=load -q --durations=10 --tb=short`; dos workers por agente activo y hasta cuatro para una única ejecución integrada con recursos disponibles. Usar `--workers N` si se elige el secuenciador por fases, sin mezclarlo con `-n`/`--dist`. En Vitest seleccionar archivos desde su workspace y limitar a `--maxWorkers=2` si hay otros agentes activos; conservar su paralelismo de archivos existente. La colección es serial; las comprobaciones que comparten escrituras o miden tiempos no se paralelizan. Evitar pools anidados y ejecuciones duplicadas, retirar `| tail` y consultar sesiones persistentes ante timeouts en lugar de reiniciar baterías.

La certificación funcional amplia queda fuera del plan y solo se realiza mediante petición explícita separada. No se exige dejar verde una suite completa para cerrar una tarea ni para aceptar la reorganización.

## Orden de ejecución: cuatro bloques

Los números T00–T13 identifican tareas; no significan que todas deban ejecutarse una detrás de otra. Para simplificar la coordinación, se cierra un bloque completo antes de empezar el siguiente.

```text
BLOQUE 1 — Preparar
    T00: inventario estructural → T01: clasificación y contrato
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

Ejecutar T00 y después T01. El bloque termina cuando están registrados el inventario estructural, los destinos de los archivos, sus responsables y el contrato de los precompilados. No requiere ejecutar las suites ni revisar resultados actuales.

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

## Detalle de tareas — Inventario y contratos

### T00 — Inventariar la estructura y selección de tests

**Inicio:** antes de mover archivos, cambiar selección de suites o generar fixtures.

**Responsable y propiedad:** coordinador; inventario estructural y de selección.

**Trabajo:**

1. Identificar revisión, cambios sin integrar, archivos con otros propietarios y herramientas disponibles.
2. Registrar cómo descubren tests pytest, Vitest y Node; incluir los corpus declarativos, los scripts y los comandos de CI.
3. Inventariar selecciones e identidades mediante inspección estática y, solo si hace falta, colección sin ejecutar cuerpos de tests. Diferenciar archivos, funciones, casos parametrizados y escenarios declarativos.
4. Localizar los contratos, presupuestos y referencias versionadas que deben conservarse, sin medir cobertura ni consultar informes de ejecuciones previas.

**Fin verificable:** existe un inventario trazable de componentes, rutas, runners, selección e identidades; están localizados los contratos a conservar y los cambios concurrentes tienen propietario identificado. No se exige ningún resultado de ejecución.

**Límite:** no ejecutar tests, benchmarks ni campañas de cobertura; no analizar ni registrar fallos actuales; no mover tests ni cambiar presupuestos, reglas o expectativas.

#### T00 — Situación de partida registrada (2026-10-23)

**Estado:** cerrada. No se movieron archivos, no se cambiaron presupuestos, reglas ni expectativas, y no se avanzó a T01.

**Base y propiedad**

- Rama `tests-rework`, revisión `8415ba80c22d4cf61fddd22473e2ebabe776b58e` ("chore: checkpoint parity updates and testing rework plans", 2026-10-23). Al iniciar T00, `git status --porcelain` estaba vacío. Durante la tarea aparecieron cambios concurrentes ajenos —la revisión de alcance de `REWORK_PLAN.md`/`REWORK_PLAN_TASKS.md` y la retirada de `reports/*`— que se conservaron sin modificar ni revertir; este registro es el único cambio propio.
- Existen copias concurrentes en otros worktrees (`.worktrees/aldred-f037` en `820d1499`, `build/cache/*` en `5748c015`/`913d93a0`/`fb3b1f90`, `D:/DEVEL/Mordheim/wt-*` en `a1f92653`, `AppData/Local/Temp/_verify_head` en `cee529cd`). No pertenecen a esta rama, no se modificaron y no condicionan esta referencia.
- Herramientas: Python 3.10.6, pytest 7.1.2, pytest-xdist 3.8.0, coverage 7.9.2, NumPy 2.2.6, PyYAML 6.0; Node 24.21.0, npm 11.19.0, Vitest 3.2.7, TypeScript 5.8.3. `doctor` informa los backends `native` y `numpy` disponibles además del modular. `cargo` no está instalado y ningún runner lo requiere.
- Observación de entorno: la extra `dev` declara `pytest>=8.0`, pero el intérprete local tiene 7.1.2. La colección y el plan funcionan; CI instala la extra sobre Python 3.12. Se registra como diferencia de entorno, no como bloqueo.

**Descubrimiento y selección por runner**

- **pytest.** `pyproject.toml` fija `testpaths=["tests"]`, cinco roots en `pythonpath` y `addopts="--strict-markers"`; registra once marcadores (`phase0_preflight` … `phase7_warband`, `evidence`, `packaging`, `performance`). Los patrones por defecto `test_*.py` y `*_test.py` reúnen 209 + 1 archivos. `tests/conftest.py` recorre los roots clasificados y rechaza todo ítem sin exactamente una categoría o con un marcador ajeno. La selección por rutas la ofrece `python tools/mordheim-utils.py tests --scope` (`all`, `engines`, `modular`, `vectorized`, `native`, `e2e`, `deterministic`, `knowledge`, `verification`, `construction`, `ui`, `cli`, `architecture`). El orden por fase lo ofrece `test-sequence` (plugin `tools/verification/test_sequence.py`) con `--step`, `--sequence-from`, `--extras` y `--workers`.
- **Vitest.** `packages/typescript/vitest.config.ts` (entorno node) incluye `tests/typescript/**/*.test.ts` en tres proyectos: `phase0_preflight` (arquitectura), `phase1_kb_contracts` (`parity-kb-vectors.test.ts`) y `phase7_warband` (resto). `apps/warband-manager-web/vite.config.ts` (jsdom, setup `tests/web/setup.ts`) incluye `tests/web/**/*.test.{ts,tsx}` en `phase0_preflight` (`architecture/boundaries.test.ts`), `packaging` (`architecture/font-publication.test.ts`) y `phase7_warband` (resto). `npm test` en la raíz ejecuta ambos workspaces; la suite web debe invocarse desde `apps/warband-manager-web` porque resuelve artefactos desde `process.cwd()`.
- **Node (`node:test`).** Dos archivos `tests/web/tools/*.test.mjs` con 29 pruebas (`test(...)`: 9 + 20) quedan fuera de los patrones Vitest; los ejecuta con `node --test` la primera fase de `tools/web/presentation-gate.mjs`, encadenada por `npm run check:presentation` y por `npm run lint` (y CI). No hay otras suites `node:test`.
- **Corpus declarativos.** `tests/E2E/modular-engine/cases/**/*.yaml` (1.779 archivos) se carga durante la colección mediante `corpus.py` y produce 5.163 escenarios declarados como `test_cases.py::test_declared_scenario[audit-ID::scenario-ID]`, con categoría derivada del canal de expectativa (`expect_error` → `phase2_construction`; resto → `phase4_modular`); `evidence/coverage-baseline.yaml` es la referencia de `test_non_regression.py`. `tests/specs/semantic/**.yaml` (178 archivos; 181 YAML incluyendo `interactions.yaml`, `interaction-policy.yaml` y `structural/phase-verification.yaml`) se cargan con `load_fixtures()` en `tests/python/verification/test_semantics.py`, que parametriza 3.793 casos authored (`test_authored_semantic_case[...]`). La especificación estructural se consume mediante `audit_phase_verification`, sin node IDs propios. Los datos JSON compartidos viven en `tests/fixtures/parity` (3 archivos), `tests/fixtures/eligibility` (6), `tests/fixtures/campaign-file-corpus` (26) y el presupuesto de cobertura `tests/fixtures/coverage/budget.json`.
- **CI.** `.github/workflows/ci.yml` ejecuta en Python: generación y `--check` del artefacto KB, `pytest tests/python/contracts tests/python/architecture tests/python/knowledge tests/python/construction/test_shared_eligibility.py`, la batería `tests/E2E/modular-engine`, su control `test_non_regression.py` y un `--check` final del artefacto. En TypeScript: `check:eligibility`, typecheck y `npm test` de `packages/typescript`, cuatro archivos web focalizados de localización/tooltips, typecheck/lint/test/build de la app y `boundaries.test.ts` tras el build. `.github/workflows/deploy-pages.yml` repite las suites TypeScript y el build antes de publicar.

**Selección e identidades de partida (verificado el 2026-10-23)**

| Runner | Ítems | Archivos con ítems | Funciones / pruebas | Parametrizados |
| --- | --- | --- | --- | --- |
| pytest | 13.069 | 210 | 2.462 ids de función únicos | 10.969 ítems |
| Vitest `packages/typescript` | 964 | 92 | 964 pruebas | 3 nombres parametrizados |
| Vitest web | 444 | 66 | 444 pruebas | 1 nombre parametrizado |
| `node:test` | 29 | 2 | 9 + 20 | — |

- Reparto pytest por root: `tests/python` 7.815 y `tests/E2E` 5.254 (5.172 de `test_cases.py` —5.163 escenarios declarados y 9 pruebas auxiliares— y 82 del resto de archivos E2E). Por componente: verification 3.972, combat 1.633, construction 1.384, knowledge 591, ui 79, web 63, cli 44, application 23, contracts 10, persistence 10, architecture 6.
- Reparto pytest por categoría: `phase0_preflight` 90, `phase1_kb_contracts` 828, `phase2_construction` 2.731, `phase3_rules` 3.485, `phase4_modular` 5.425, `phase5_vectorized` 201, `phase6_native` 38, `phase7_warband` 143, `evidence` 120, `packaging` 1, `performance` 7. La suma es 13.069; las tres últimas solo se seleccionan con `--extras`/`--sequence-category`.
- Reparto Vitest por proyecto: TypeScript 2/18/944 (`phase0_preflight`/`phase1_kb_contracts`/`phase7_warband`); web 5/2/437 (`phase0_preflight`/`packaging`/`phase7_warband`). Los proyectos son disjuntos.
- Huellas de identidad para comparar en T11: pytest, sha256 de los node IDs ordenados unidos por `\n` = `f72929f707d864fbc98859fceaeae91e44a37caaa3ab33cfdaf4ad392fcbf423`; TypeScript = `24d50f28222f35f3d125fa3570cf16d9875277def6a3c69a3ca421f5e13f4253`; web = `98ccdd5a1ccf746f4ead13bba373459269fa4910bdae86cb2fa8f123fbb21b4c` (clave `proyecto::archivo::nombre`).
- Los escenarios declarativos conservan identidad propia (E2E `audit-ID::scenario-ID`; semánticos por `spec` y caso) y no se confunden con ejecuciones aprobadas.

**Evidencia reutilizada y comprobaciones**

- Reutilizada: la verificación de clasificación de `docs/reference/test-sequence.md` (2026-10-21, 13.029 ítems) solo como antecedente de selección. La colección actual la sustituye: +40 ítems netos (`phase0` 88→90, `phase1` 834→828, `phase5` 171→201, `evidence` 106→120; el resto sin cambio). No se consultan ni registran resultados de ejecuciones previas.
- Verificado sin ejecutar cuerpos: `python -m pytest --collect-only -q` (13.069 ítems, exit 0, 39,92 s, sin errores de colección); `test-sequence --sequence-plan -qq --extras` (recuentos por categoría, suma exacta); `npx vitest list --json` en ambos workspaces (964 y 444 ítems); recuento estático de `test(...)` en los dos archivos `node:test` (9 + 20); `doctor` (backends y roots).
- No ejecutado: ninguna batería funcional ni de cobertura; no se registra ningún resultado de ejecución. El presupuesto de cobertura (`tests/fixtures/coverage/budget.json`) y el baseline E2E (`tests/E2E/modular-engine/evidence/coverage-baseline.yaml`) quedan localizados, sin medir.
- Sin bloqueos para el criterio de T00. Las comprobaciones de comportamiento corresponden a T13.

**Cierre de T00:** existe una referencia trazable de la revisión, las herramientas, el descubrimiento de cada runner, los corpus declarativos, los recuentos por archivo/función/parametrización/escenario y las huellas de identidad; los cambios concurrentes están identificados y se conservaron. El estado de fallos queda explícitamente fuera de la referencia por decisión del coordinador.

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

#### T01 — Reparto, propiedad y contrato registrados (2026-10-23)

**Estado:** cerrada. Solo inspección y documentación: no se movió ni editó ningún test, código, fixture, presupuesto o expectativa; no se ejecutaron baterías. Se reutiliza el inventario de T00 (revisión `8415ba80`, 13.069 ítems pytest, 964 TypeScript y 444 web).

**Criterio de asignación**

- El destino es el **componente cuya garantía se prueba**, no la fase: el marcador `phase*` existente se conserva y sigue siendo el mecanismo de selección. Integración, fixtures y soporte viven dentro de su responsabilidad.
- Un único propietario por archivo. Los archivos mixtos se asignan completos al propietario del original, que separa los bloques y transfiere cada destino antes de cerrar su paquete. Ningún archivo aparece en dos filas del mapa.
- Conservación del inventario: 210 archivos Python / 13.069 ítems; 92 archivos TypeScript / 964 ítems; 68 archivos web / 473 ítems (444 Vitest + 29 `node:test`). Las tablas suman exactamente esos totales.

**Mapa origen → destino — Python**

| Origen | Archivos | Ítems | Destino | Propietario |
| --- | --- | --- | --- | --- |
| `tests/python/architecture/test_boundaries.py` | 1 | 6 | `tests/tooling/architecture/test_boundaries.py` | T05 |
| `tests/python/contracts/test_v5_fixtures.py` | 1 | 10 | `tests/applications/warband_manager/persistence/campaign_file/test_v5_fixtures.py` | T04 |
| `tests/python/knowledge/*.py` (20 archivos) | 20 | 591 | `tests/rules/knowledge/**` | T03 |
| `tests/python/construction/*.py` (62 archivos) | 62 | 1.384 | `tests/rules/construction/**`; los bloques de ejecución de 25 archivos pasan a `tests/engines/modular/rules/**` | T03 (separa y transfiere a T07) |
| `tests/python/combat/modular/*.py`, excepto `test_complex_sequences.py`, `test_exact_phases.py`, `test_interactions.py` y `test_hatred_bindings.py` | 62 | 1.389 | `tests/engines/modular/**` | T07 |
| `tests/python/combat/vectorized/*.py` (11) + `tests/python/combat/modular/test_complex_sequences.py` | 12 | 137 | `tests/engines/vectorized/**` | T08 |
| `tests/python/combat/native/*.py` | 2 | 12 | `tests/engines/native/**` | T09 |
| `tests/python/combat/test_phases.py`, `test_duel_context.py`, `test_kernel_plan.py` + `tests/python/combat/modular/test_exact_phases.py`, `test_interactions.py` | 5 | 89 | `tests/engines/shared/**` | T02 |
| `tests/python/combat/modular/test_hatred_bindings.py` | 1 | 6 | `tests/rules/knowledge/combat/test_hatred_bindings.py` | T03 |
| `tests/python/verification/test_coverage_gate.py`, `test_engine_mutation.py` | 2 | 10 | `tests/tooling/verification/**` | T05 |
| `tests/python/verification/test_semantics.py`, `test_structural.py` | 2 | 3.840 | `tests/rules/integration/**` | T03 |
| `tests/python/verification/test_parity.py`, `test_parity_battery_cases.py`, `test_parity_battery_runner.py`, `test_truncation_parity.py`, `test_duel_replay.py` | 5 | 122 | `tests/engines/parity/**` | T10 |
| `tests/python/web/*.py` (5) + `tests/python/web/parity/vectors_kb_python_test.py` | 6 | 63 | `tests/rules/knowledge/web/**` | T03 |
| `tests/python/application/*.py`, `tests/python/persistence/*.py`, `tests/python/ui/*.py` | 16 | 112 | `tests/applications/combat_lab/{services,persistence,ui}/**` | T04 |
| `tests/python/cli/test_console.py` | 1 | 5 | `tests/applications/combat_lab/cli/test_console.py` | T04 |
| `tests/python/cli/test_benchmarking.py`, `test_calibrate.py` | 2 | 9 | `tests/engines/parity/benchmarks/**` | T10 |
| `tests/python/cli/test_umbrella.py`, `test_test_sequence.py`, `test_parallel_test_sequence.py` | 3 | 30 | `tests/tooling/launcher/**` | T05 |
| `tests/E2E/modular-engine/**` (7 archivos de test, `cases/**` y `evidence/**`) | 7 | 5.254 | `tests/rules/integration/e2e/**` | T03 |

**Mapa origen → destino — TypeScript, web y Node**

| Origen | Archivos | Ítems | Destino | Propietario |
| --- | --- | --- | --- | --- |
| `tests/typescript/domain/**`, `application/**`, `adapters/**` y `parity-vectors.test.ts` | 90 | 944 | `tests/applications/warband_manager/**` | T04 |
| `tests/typescript/parity-kb-vectors.test.ts` | 1 | 18 | `tests/rules/knowledge/parity-kb-vectors.test.ts` | T03 |
| `tests/typescript/architecture/purity.test.ts` | 1 | 2 | `tests/tooling/architecture/purity.test.ts` | T05 |
| `tests/web/features/**`, `App.test.tsx`, `band-set-settings.test.tsx`, `rules-page.test.tsx`, `warband-reference-template.test.tsx`, arquitectura específica de la app (7 archivos) | 62 archivos de test (+ `setup.ts` y `support/fresh-campaign-artefact.ts`) | 398 | `tests/applications/warband_manager/{features,presentation,packaging,support}/**` | T04 |
| `tests/web/tools/**` (3 `.tsx` + 2 `.mjs`), `tests/web/architecture/boundaries.test.ts` | 6 archivos de test (+ `presentation-completeness-detector.d.ts`) | 75 (46 Vitest + 29 `node:test`) | `tests/tooling/web/**` y `tests/tooling/architecture/web-boundaries.test.ts` | T05 |

**Archivos mixtos y separaciones acordadas**

| Archivo | Dueño del original | Permanece | Se transfiere |
| --- | --- | --- | --- |
| `tests/python/verification/test_semantics.py` | T03 | 3.793 casos authored + `test_rapier...` y comprobaciones de conexión → `rules/integration` | 31 pruebas de auditoría/evidencia/certificación → `tests/tooling/evidence/` (T05); 3 contratos KB → `rules/knowledge` (T03) |
| `tests/python/verification/test_parity.py` | T10 | 13 pruebas de ejecución/paridad → `engines/parity` | 17 pruebas de payload, markdown, CLI y estados de informe → `tests/tooling/verification/reports/` (T05) |
| `tests/python/verification/test_truncation_parity.py` | T10 | 6 pruebas de ejecución → `engines/parity` | 2 pruebas de payload/progreso → `tests/tooling/verification/reports/` (T05) |
| `tests/python/verification/test_duel_replay.py` | T10 | 14 pruebas de replay por backend → `engines/parity` | Validación preflight del replay → `tests/engines/shared/test_replay_contract.py` (T02) |
| `tests/python/combat/vectorized/test_rule_families_a.py`, `..._b.py` | T08 | 18 pruebas de ejecución vectorial | Una comprobación de cobertura del catálogo por archivo → `tests/tooling/evidence/` (T05) |
| 25 archivos de `tests/python/construction/` que importan el motor modular | T03 | Compilación, concesiones y rechazos → `rules/construction` | Bloques que llaman `resolve_round`, `resolve_reference_attack`, `prepare_*`, `initialize_*` o `resolve_priority` → `tests/engines/modular/rules/` (T07) |
| `tests/python/combat/modular/test_shifty_activation.py`, `test_spectral_touch_activation.py`, `test_vomit_attack.py` | T07 | Regla y preparación modular | Los ítems/parametrizaciones que ejecutan vectorizado o nativo → `engines/vectorized` (T08), `engines/native` (T09) o `engines/parity` (T10), conservando ids |
| `tests/python/combat/modular/test_complex_sequences.py` | T08 | — | Archivo completo a `engines/vectorized` (usa ayudantes privados vectorizados) |
| `tests/web/architecture/boundaries.test.ts` | T05 | Límites de fuentes → `tooling/architecture` | Dos guardas del bundle construido → `applications/warband_manager/packaging/` (T04) |
| `tests/fixtures/parity/vectors/knowledge_port.json`, `rules_catalogue.json` | T03 | Vectores de paridad KB compartidos → `rules/knowledge/fixtures/parity/` | — |
| `tests/fixtures/parity/vectors/malformed_save.json` | T04 | — | Vector de campaign-file → `applications/warband_manager/fixtures/campaign-file-vectors/` |

Los 25 archivos de construction con ejecución son: `test_canonical_choices`, `test_charge_and_netter`, `test_clockworker_constructs`, `test_condemned_source_profile`, `test_disability_supplied`, `test_dragon_monk_unarmed`, `test_dwarf_inheritance`, `test_hireling_admission`, `test_hireling_closures`, `test_hireling_resources`, `test_intrinsic_attacks`, `test_intrinsic_profile_declarations`, `test_ippan_shu_admission`, `test_kits_and_variants`, `test_local_weapon_items`, `test_morr_marks_loadouts`, `test_natural_variants`, `test_penthesilea_source_corrections`, `test_physical_kits`, `test_supplied_equipment_preparations`, `test_supplied_injury_consequences`, `test_supplied_runes`, `test_supplied_weapon_modifiers`, `test_warpaint_and_wine` y `test_weapon_variant_profiles`. De los archivos que importan algo del paquete de aplicación/motor, dos solo importan `CombatCatalogue` (`test_construction_context_parity`, `test_profile_bindings`) y permanecen íntegros en `rules/construction`; los 35 restantes no importan el motor y también permanecen íntegros.

**Contrato versionado de precompilados**

Alcance: el corpus `tests/engines/fixtures/compiled-cases.json` alimenta únicamente tests de motores, paridad y benchmarks. Los E2E y las especificaciones semánticas originales **no se sustituyen**: siguen en `rules/integration` con su KB, sus declaraciones y sus evidencias. Un caso declarativo solo se exporta si un consumidor de motor lo reutiliza; en ese caso se copian sus expectativas revisadas y se marca su origen.

```json
{
  "schema": "mordheim-compiled-cases",
  "schema_version": 1,
  "generator": { "name": "export-compiled-cases", "version": 1 },
  "source": {
    "revision": "8415ba80c22d4cf61fddd22473e2ebabe776b58e",
    "kb_root": "sources/knowledge",
    "files": [{ "path": "sources/knowledge/...", "sha256": "..." }]
  },
  "cases": [
    {
      "case_key": "unit/modular/shifty_activation/<caso>",
      "origin": {
        "kind": "unit",
        "node_id": "tests/python/combat/modular/test_shifty_activation.py::<test>[<param>]",
        "path": "tests/python/combat/modular/test_shifty_activation.py",
        "sha256": "..."
      },
      "fighters": { "first": { "...": "CompiledFighter completo" }, "second": { "...": "..." } },
      "context": null,
      "auxiliary_participants": [],
      "initial_state": { "first": {}, "second": {} },
      "determinism": {
        "dice": [{ "key": "round.0.first.attack.0.hit", "sides": 6, "value": 4 }],
        "decisions": [{ "key": "...", "value": true }]
      },
      "limits": { "simulations": 1, "seed": 0, "batch_size": 100000, "maximum_rounds": 1 },
      "benchmark": null,
      "expectations": null,
      "fingerprints": { "inputs_sha256": "...", "case_sha256": "..." }
    }
  ],
  "fingerprints": { "cases_sha256": "...", "corpus_sha256": "..." }
}
```

Reglas de codificación y validación:

- **Combatientes.** Se serializan todos los campos de `CompiledFighter`: identificador, `Characteristics`, `main_weapon`, `off_hand`, `global_effects`, `shield_and_skill_effects`, `extra_attacks`, `extra_attacks_without_poison`, `main_weapon_without_poison`, `off_hand_without_poison`, `unarmed_weapon`, `vomit_attack`, `global_effects_without_equipment`, `skill_effects_only`, `mutation_options`, `mutation_equipment`, `random_characteristics`, `construction_tags`, `armour_save`, `helmet_save`, `natural_armour_save`, `natural_armour_unmodified`, `natural_armour_worst_save`, `natural_armour_stacks`, `injury_profile`, `off_hand_attacks`, `mounted`, `missile_weapon_limit`, `ballistic_skill`, `main_hand_slot`, `off_hand_slot`, `stupidity_leadership`, `stupidity_leadership_bonus`, `animal_handler_leadership` y `mob_allies`.
- **Estructuras anidadas.** `EffectSet` se codifica como objeto disperso: solo los campos distintos de su valor por defecto, validados contra el esquema `EffectSet/v1`; un campo ausente significa el valor por defecto declarado y una clave desconocida es error. `CarriedEquipment` conserva `item_id`, `effect`, `kind`, `slot`, `stat_bonuses` y `effect_without_poison`; `MutationOption` conserva `roll`, `effect`, `stat_ops`, `extra_attacks` y `limb_forms`.
- **Contexto y auxiliares.** `DuelContext` serializa `first_id`, `second_id`, `nearby`, `distances`, `contacts`, `terrain`, `charging` y `active_participant`. Los participantes auxiliares son `LocalParticipant` con `participant_id`, `side_id`, `fighter` y `condition`. `charging: null` (selección aleatoria heredada) y `charging: []` (nadie carga) son estados distintos; igual que `contacts: null` frente a `[]`.
- **Estado inicial.** Solo los campos de `FighterState` que el caso sobrescribe, con la misma validación de tipos y el nombre de `Condition`; el estado resultante se conserva como expectativa cuando el caso la declara.
- **Entradas deterministas.** `dice` es una secuencia ordenada de `{key, sides, value}` consumida por `StrictDice`; `decisions` es una secuencia ordenada de `{key, value}` booleana consumida por `StrictDecisions`. El orden es semántico. `limits` fija `simulations`, `seed`, `batch_size` y `maximum_rounds` (positivos; `maximum_rounds` obligatorio). `benchmark` añade, cuando aplica, calentamientos, repeticiones y tamaños de lote; nunca sustituye las opciones del CLI.
- **Claves de caso.** `e2e/<audit_id>/<scenario_id>`, `semantic/<spec_id>/<case_id>`, `unit/<motor>/<archivo>/<prueba>[/<param>]` y `benchmark/<scenario_id>`. Se sanean a ASCII estable; si dos orígenes colisionan se añade un sufijo de 8 caracteres del `node_id`. Una clave publicada no se renombra; T11 compara la selección por `origin.node_id`, no solo por clave.
- **Procedencia y huellas.** `origin` conserva `kind`, `node_id`, ruta relativa POSIX y `sha256` de la fuente; `source.files` registra cada YAML/JSON de KB con su huella. `fingerprints.inputs_sha256` cubre solo entradas y `case_sha256` cubre entradas y expectativas. El cargador recalcula ambas y rechaza discrepancias. No se escriben fechas, rutas absolutas, descripciones, comentarios ni texto editorial.
- **Expectativas.** `expectations` solo existe si la declara una fuente authored/reviewed (`expect_initial`, `expect_rounds`, `expect_final`, `expect_events`, `expect_fighters`, `expect_error`, o el `expect`/`distribution` semántico). El exportador las copia, nunca las deriva del motor. Los tests de motor conservan además sus aserciones en código; el fixture no las sustituye.
- **Reproducibilidad.** Mismo `source`, mismas entradas y mismo exportador producen bytes idénticos: JSON UTF-8, claves ordenadas, separadores compactos, sin Timestamp ni datos de entorno. `schema_version` es exacto; cualquier cambio incompatible sube la versión y el cargador rechaza las demás.

**Interfaz de exportación y carga**

- `tools/verification/compiled_cases.py` (T02) expone `load_cases(path) -> Mapping[str, CompiledCase]` y las funciones `encode_*`/`decode_*` de `CompiledFighter`, `EffectSet`, `DuelContext`, `LocalParticipant` y `CompiledCase`. No importa `mordheim_construction`, `mordheim_knowledge`, `mordheim_combat` ni el runner E2E; solo stdlib y los tipos de `mordheim_core`. Un archivo ausente, una versión distinta, un tipo incorrecto, una clave duplicada o una huella que no coincide producen `CompiledCaseError(case_key, field, reason)`; nunca se recompila ni se regenera el corpus.
- `tools/knowledge/export_compiled_cases.py` (T03) expone `export_cases(specs, *, kb_root, destination) -> ExportReceipt` con `path`, `case_count`, `case_hashes` y `corpus_sha256`. Compila mediante `compile_fighter`, resuelve contexto y auxiliares, valida claves únicas y escribe el JSON canónico. Rechaza prosa y expectativas no declaradas.
- Pruebas: `tests/engines/shared/test_compiled_cases.py` (T02) cubre ida y vuelta, `null` frente a `[]`, secuencias, versión/tipo/clave desconocidos, archivo ausente, huella alterada y funcionamiento sin KB/compilador. `tests/rules/construction/test_export_compiled_cases.py` (T03) cubre reproducibilidad, procedencia, ausencia de prosa y conservación de expectativas.

**Propiedad de implementación, helpers y datos compartidos**

| Área | Archivos | Propietario |
| --- | --- | --- |
| Contratos compartidos de ejecución y códec/cargador | `packages/python/core/**`, `mordheim_combat/phases.py`, `vector_dice.py`, `tools/verification/compiled_cases.py`, `tests/engines/shared/**` | T02 |
| KB, construcción, exportador y corpus originales | `packages/python/knowledge/**`, `roster-construction/**`, `sources/knowledge/**` (solo lectura), `tools/knowledge/**`, `tests/rules/**` | T03 |
| Aplicaciones | `apps/combat-lab/mordheim_combat_lab/{application,persistence,ui}/**`, `cli/commands.py`, `apps/warband-manager-web/src/**`, `packages/typescript/**`, `contracts/campaign-file-v5/**`, `tests/applications/**` | T04 (las opciones de paridad del CLI las integra el coordinador) |
| Tooling y verificación | `tools/web/**`, `tools/verification/**` salvo `test_sequence.py` y `compiled_cases.py`; `verification/{audit,audit_export,consumers,coverage_gate,dice,engine_mutation,integrations,interactions,inventory,mutations,operators,pytest_reporter,reporting,reports,scenarios,specifications,structural}.py`; `tests/tooling/**` | T05 |
| Motores | `mordheim_combat/modular/**` (T07), `vectorized/**` (T08), `native/**` (T09), `kernel.py`/`_combat_compile.py`, `verification/parity/**` y `cli/{benchmarking,scenarios,calibration}.py` (T10) | T07–T10 |
| Fixtures precompilados | `tests/engines/fixtures/**`, incluido `compiled-cases.json` y su manifiesto de huellas | T06 (exclusivo) |
| Configuración compartida | `pyproject.toml`, `tests/conftest.py`, `tools/mordheim-utils.py`, `tools/verification/test_sequence.py`, configuraciones Vitest/TypeScript, scripts npm, CI y documentación común | coordinador |

Datos y helpers compartidos:

- `tests/support/kb-artefact.ts` → `tests/rules/knowledge/support/` (T03); lo consumen los vectores KB de Python/TS y los tests de adaptador de la app (T04), sin copia adicional.
- `tests/web/setup.ts` y `tests/web/support/fresh-campaign-artefact.ts` → `tests/applications/warband_manager/support/` (T04); la suite web los carga mediante la configuración de Vitest y el test de límites de tooling comparte `setup.ts` sin duplicarlo.
- `tests/fixtures/eligibility/**` → `tests/rules/construction/fixtures/eligibility/` (T03); `tests/fixtures/campaign-file-corpus/**` → `tests/applications/warband_manager/fixtures/` (T04); `tests/fixtures/coverage/budget.json` → `tests/tooling/verification/fixtures/` (T05). Los vectores de paridad KB se conservan una sola vez en `tests/rules/knowledge/fixtures/parity/` (T03) y `malformed_save.json` en la app (T04).
- `tests/specs/**` (semánticas, `interactions.yaml`, `interaction-policy.yaml`, `structural/phase-verification.yaml`) → `tests/rules/integration/specs/` (T03). `tests/E2E/modular-engine/{corpus,dice,runner,validate_corpus}.py` y `evidence/` → `tests/rules/integration/e2e/` (T03).
- Los artefactos generados de `outputs/` no se versionan ni tienen propietario de test: los produce el generador de KB (T03) y los benchmarks/paridad (T10); los tests solo los leen.

**Candidatos a redundancia (sin retirar)**

| Id | Candidato | Evidencia | Tratamiento |
| --- | --- | --- | --- |
| C1–C5 | Cinco pares con cuerpo idéntico entre `tests/E2E/modular-engine/test_runner.py` y `tests/python/verification/test_semantics.py`: `test_strict_dice_rejects_unexpected_requests`, `test_strict_dice_checks_unused_rolls_and_repeated_keys`, `test_strict_decisions_rejects_unused_and_unexpected_choices`, `test_adaptive_enumeration_weights_short_circuit_and_mixed_dice_exactly`, `test_enumeration_refuses_to_truncate_unbounded_sequences` | Cuerpo AST idéntico, pero el primero usa `mordheim_modular_e2e.dice` y el segundo `mordheim_combat_lab.verification.dice` | T12 decide; no se elimina por el cuerpo |
| C6 | `test_kb_i18n.py::test_default_locale...` y `test_ui_i18n.py::test_default_locale...` | Cuerpo idéntico; implementaciones distintas (`mordheim_knowledge.i18n` y `mordheim_combat_lab.ui.i18n`) | T12 revisa contrato y sustituto |
| C7 | `test_non_regression.py` se ejecuta dentro de `tests/E2E/modular-engine` y otra vez como paso propio de CI | Doble ejecución del mismo archivo en la misma revisión | Mantener el paso propio y excluirlo de la batería anterior (T12) |
| C8 | `test_profile_save_thresholds.py` en `construction` y en `combat/modular` | Mismas cláusulas impresas, capas distintas (valores compilados frente a ataque real) | T12 compara contratos; no se fusiona por nombre |
| C9 | Pruebas de payload/markdown/estados de paridad repartidas entre `test_parity.py`, `test_parity_battery_cases.py` y `test_parity_battery_runner.py` | Solapamiento de formato y magnitudes | T12 revisa consolidación con resultados controlados |
| C10 | `test_truncation_parity.py` y `test_parity.py::test_certify_deep_pooled_oracle...` | Ambos comparan oráculo pooled con secuencial | T12 conserva si detectan fallos distintos |
| C11 | Casos E2E y casos semánticos sobre las mismas cláusulas | Cobertura solapada, sin identidad de caso común | T12 compara contrato, entradas y fallo detectado; no se deduce equivalencia |
| C12 | `test_hireling_cotejo.py` frente a las matrices de hirelings de `construction` | Distintos contratos (cotejo editorial frente a admisión) | T12 revisa sin retirar |

**Cierre de T01**

- Los 210 archivos pytest, 92 TypeScript y 68 web tienen destino y un único propietario; las tablas conservan los totales de T00. Los archivos mixtos tienen dueño del original y destinos de separación explícitos.
- El contrato fija claves, estructuras anidadas, opcionales, secuencias, determinismo, expectativas, procedencia, huellas e interfaces, de modo que T02 (cargador), T03 (exportador), T06 (corpus) y T07–T10 (consumidores) pueden trabajar sin decisiones incompatibles.
- Sin bloqueos concretos. T12 revisará los candidatos C1–C12; ninguna retirada se ejecuta en T01.

## Detalle de tareas — Infraestructura y separación por responsabilidades

### T02 — Codec y cargador de entradas de ejecución

**Inicio:** T01 cerrado.

**Propiedad:** implementación del codec/cargador acordada en T01 y tests en `tests/engines/shared/`. No escribe el corpus definitivo.

**Trabajo:** reconstruir y serializar las estructuras completas de ejecución; validar versión, tipos y campos; conservar valores opcionales y secuencias. Rechazar archivos ausentes o incompatibles sin recompilación automática. Mantener los imports independientes del compilador, la KB y los runners que cargan corpus originales.

**Fin verificable:** comprobaciones puntuales del contrato demuestran ida y vuelta sin pérdida, rechazo de entradas incompatibles y carga de fixtures; la independencia de imports del cargador se revisa estáticamente, sin pruebas de bloqueo de KB. Se reutilizan los resultados válidos. La interfaz queda estable para T03 y los consumidores. No se ejecutan suites de motores ni de integración.

#### T02 — Codec y cargador entregados (2026-10-23)

**Estado:** cerrada. Implementación en `tools/verification/compiled_cases.py` y pruebas en `tests/engines/shared/test_compiled_cases.py`.

- Cubre serialización completa de `CompiledFighter`, `EffectSet` disperso, `CarriedEquipment`, `MutationOption`, `DuelContext`, `LocalParticipant` y estado inicial; conserva `null` frente a `[]` y el orden de dados/decisiones.
- `load_cases` valida esquema, versión, claves duplicadas y las huellas `inputs_sha256`, `case_sha256`, `cases_sha256` y `corpus_sha256`; no importa KB, compilador ni motores.
- Comprobación: `python -m pytest tests/engines/shared/test_compiled_cases.py -q` → 14 pasan.
- La interfaz quedó estable para T03 y T06; no se modificó ningún contrato de T01.
- **Desviación de alcance registrada:** estos 14 tests son incorporaciones nuevas, no traslados; junto con los 4 del exportador T03 suman 18 tests añadidos. Las 13.069 identidades originales se conservan; el total pasa a 13.087 y no se añadieron más pruebas.

### T03 — Rules y exportador explícito

**Inicio:** T02 cerrado.

**Propiedad:** tests y corpus asignados a `tests/rules/knowledge/`, `construction/` e `integration/`; implementación del exportador y sus pruebas. No escribe fixtures definitivos fuera de T06.

**Trabajo:**

1. Trasladar las pruebas de KB, construcción, especificaciones semánticas y E2E originales, conservando sus identidades, expectativas, metadatos y referencias de evidencia.
2. Mantener las comprobaciones reales de conexión entre KB, compilador y combate; las negativas de admisión siguen comprobando rechazos reales.
3. Implementar la exportación explícita de las configuraciones identificadas en T01, incluidos proveedores de contexto y ajustes propios de benchmarks.
4. Exportar estructuras de ejecución y procedencia técnica sin descripciones ni comentarios de las fuentes. No derivar expectativas normativas del motor.
5. Entregar al coordinador los cambios de rutas de loaders, herramientas y configuraciones necesarios para integrar los traslados.

**Fin verificable:** el inventario, los imports y la colección de los archivos afectados conservan los casos de rules en sus nuevos destinos; una comprobación puntual confirma exportación reproducible y reconstrucción sin pérdida. No se exige ejecutar las suites completas de construction, E2E o semánticas.

#### T03 — Rules, integración y exportador entregados (2026-10-23)

**Estado:** entregada para revisión; no aceptada. Traslados aplicados con `git mv` y rutas/imports adaptados:

- 20 archivos de knowledge → `tests/rules/knowledge/**`; 6 de web/vectores → `tests/rules/knowledge/web/**`; 62 de construction → `tests/rules/construction/**`; E2E y specs → `tests/rules/integration/{e2e,specs}`; semánticas/estructural → `tests/rules/integration/`.
- Exportador nuevo `tools/knowledge/export_compiled_cases.py` y pruebas `tests/rules/construction/test_export_compiled_cases.py`.
- Corrección de integración: `compile_fighter` recibe la raíz de KB, no la raíz del repositorio; sin ella ningún caso con `FighterBuild` podía exportarse. El codec no se modificó.
- Cesión registrada: los 3 contratos KB embebidos en `test_semantics.py` y los bloques de evidencia/informes se cedieron a T05 para separarlos con un único escritor.

**Comprobaciones:** colección completa 13.087 ítems; `tests/rules/construction` 1.388 pasan; codec + exportador 18 pasan; construcción conserva sus 1.384 ítems y los E2E/semánticas originales siguen en integración. No se ejecutó la batería E2E de 5.163 escenarios ni la semántica completa. Sin commits.

### T04 — Aplicaciones y sus contratos

**Inicio:** T01 cerrado.

**Propiedad:** tests asignados a `tests/applications/combat_lab/` y `warband_manager/`, sus helpers y datos propios. Las configuraciones comunes las modifica el coordinador.

**Trabajo:** agrupar servicios, persistencia, consola de producto, dominio de campaña e interfaces con sus aplicaciones. Mantener los contratos de campaña y los tests de integración propios del producto. Diferenciar Node y navegador cuando sea necesario; conservar una sola copia de los datos compartidos.

**Fin verificable:** inventario, sintaxis, imports, referencias y colección/listado conservan los casos previstos en sus nuevos destinos. Los cambios de configuración se han integrado con el coordinador; el typecheck compartido se agrupa, sin repetirlo por agente. No se exige ejecutar las baterías funcionales de las aplicaciones.

#### T04 — Aplicaciones entregadas (2026-10-23)

**Estado:** entregada para revisión; no aceptada. Traslados aplicados:

- Python: 16 archivos / 112 ítems → `tests/applications/combat_lab/{services,persistence,ui,cli}` y `tests/applications/warband_manager/persistence/campaign_file`.
- TypeScript: 90 archivos / 944 ítems → `tests/applications/warband_manager/{domain,application,adapters}` y `parity-vectors.test.ts`.
- Web: 62 archivos / 398 ítems → `tests/applications/warband_manager/{features,presentation,packaging,support}`; corpus de campaña y vector `malformed_save.json` en `fixtures/`.
- Las dos guardas post-build se separaron a `packaging/bundle-boundaries.test.ts`; `tests/tooling/architecture/web-boundaries.test.ts` conserva solo las guardas de fuentes. Se eliminaron los reexports temporales del helper KB y los 36 imports apuntan a `tests/rules/knowledge/support/kb-artefact.ts`.

**Comprobaciones:** Vitest TypeScript 964/964 en 92 archivos; Vitest web 441/444 (3 fallos en `campaign-obligations.test.tsx` por datos de mutaciones/`skill_access`, ajenos a rutas); `npm run typecheck` pasa; colección completa correcta. Los 5 fallos de `test_improvements.py` en la comprobación conjunta son de comportamiento existente y no se investigaron. Sin commits.

### T05 — Tooling y arquitectura

**Inicio:** T01 cerrado.

**Propiedad:** tests asignados a `tests/tooling/` y sus helpers; los archivos originales mixtos siguen el reparto exclusivo de T01.

**Trabajo:** reunir pruebas del launcher, secuenciador, herramientas de verificación, informes, detectores y herramientas web. Trasladar los límites generales de arquitectura; dejar las restricciones específicas con su componente. Separar las comprobaciones del tooling de las que realmente ejecutan un motor. Registrar la repetición de ejecuciones para resolverla en T12.

**Fin verificable:** inventario, sintaxis, imports, referencias y colección/listado prueban la selección propia de tooling; sus detectores conservan controles positivos y negativos y no absorbe pruebas funcionales de otros componentes. Solo se ejecutan casos puntuales si cambia lógica de la tarea, sin ejecutar tooling completo ni sus campañas de cobertura/mutación.

#### T05 — Tooling entregado (2026-10-23)

**Estado:** entregada para revisión; no aceptada. Cesión registrada por el coordinador: T03/T08/T10 cedieron a T05 los bloques mixtos de evidencia e informes para que un único escritor los separara.

- Python: boundaries → `tests/tooling/architecture`; coverage/engine mutation → `tests/tooling/verification`; launcher/secuenciador → `tests/tooling/launcher`; presupuesto → `tests/tooling/verification/fixtures/coverage/budget.json`.
- TS/web: purity y web boundaries → `tests/tooling/architecture`; detectores y `node:test` → `tests/tooling/web`.
- Transferencias: 31 pruebas de evidencia + 3 contratos KB desde `test_semantics.py` (los contratos a knowledge); 17 informes desde `test_parity.py`; 2 de truncación; 2 comprobaciones de catálogo desde vectorizado. Los originales conservan solo sus bloques de ejecución.

**Comprobaciones:** `tests/tooling` + contratos KB 108 pasan y 4 fallan por expectativas de datos ya desactualizadas (66/101 familias frente a 260/998, y `verify_vectorized_parity().complete == False`), no por el traslado; Node 20 + 9 pasan; colección 13.087. No se corrigieron esos fallos ajenos.

**Corrección de revisión (scopes):** `SCOPE_PATHS` vuelve a seleccionar las suites originales reales de `tests/python/combat` y `tests/python/verification` mientras T07–T10 no las trasladen, además de `tests/engines` y `tests/tooling/verification`; `DEFAULT_SUITES` y el presupuesto de cobertura usan esas mismas rutas. Las 13 selecciones existen en disco y `tests/tooling/launcher` + `test_coverage_gate.py` → 38 pasan. No se selecciona ningún directorio inexistente ni se omite una suite original. Sin commits.

## Detalle de tareas — Fixtures y consumidores de motores

### T06 — Generar y congelar las entradas precompiladas

**Inicio:** T03 cerrado; están disponibles el exportador y el codec.

**Propiedad exclusiva:** `tests/engines/fixtures/`, incluido `compiled-cases.json`.

**Trabajo:** generar las entradas requeridas por los consumidores de T07–T10. Comprobar integridad, referencias, ausencia de prosa original y correspondencia con sus configuraciones de origen. Registrar versión y huellas. Conservar las expectativas revisadas, dados, decisiones y estado inicial de los casos deterministas que se reutilicen.

**Fin verificable:** el corpus contiene las entradas acordadas en T01; exportar y cargar conserva íntegramente las estructuras; los casos tienen claves estables y procedencia trazable. Se identifica la versión congelada que consumirán T07–T10.

**Límite:** un caso que no puede representarse se declara con su causa, sin inventar entradas, omitirlo silenciosamente ni convertirlo en aprobado. Si un consumidor descubre una carencia, T06 la corrige de forma serial, publica una nueva versión y señala qué evidencia debe repetirse.

#### T06 — Corpus precompilado congelado (2026-10-23)

**Estado:** completada estructuralmente; pendiente de aceptación final. Corpus regenerado tras corregir las exclusiones basadas en «menos de dos combatientes compilados distintos»:

- `tests/engines/fixtures/compiled-cases.json`: **6.369 casos** = 4.699 E2E + 5 `benchmark/<id>` + 42 `parity/deep/<id>` + **1.623 `unit/**`** (1.602 de motores + 21 de replay), 29.209.623 bytes, `corpus_sha256 = ebed92c1638d4555e5924c56f0c92e43f21b3c8539ce8c4c887a87b455f1c40f`, revisión `8415ba80c22d4cf61fddd22473e2ebabe776b58e`, `schema_version: 1`.
- `compiled-cases.manifest.json`: **80 consumidores** con **1.718 referencias a claves** verificadas contra el corpus, además de `benchmark_scenarios` (5), `deep_test_scenarios('full')` (42), `test_parity.py` (43 con `benchmark/basic`) y `test_duel_replay.py` (21). `consumer_exclusions` queda reducido a **4 archivos** sin dependencia de compilación; `rules_destinations` registra los **5 archivos** cuyas pruebas de compilación/catálogo pertenecen a rules.
- **Cobertura de consumidores:** los **81 archivos de `tests/python/combat`** quedan contabilizados: **76 con correspondencia a claves** (incluido 1 native que reutiliza `parity/deep/sigmarite-vs-undead`), **4 con exclusión sin compilación** y **1 solo con destino rules** (`test_catalogue_runtime.py`). Los cinco destinos rules incluyen ese archivo exclusivo y bloques de otros cuatro archivos que conservan pruebas de ejecución.
- **Correcciones de las exclusiones:**
  - `test_parallel_numpy.py`: sus dos pruebas usan el mismo combatiente dos veces; se incorporaron **2 claves** con el par espejado, sin inventar oponente.
  - `test_mim_mutations.py`: se incorporaron **37 claves** con el humano compilado como `first` y el sacerdote compilado que aporta `mutation_options` como `second`; los roles quedan declarados en el manifiesto.
  - `test_coverage_boundaries.py`: **2 claves** para el participante retirado, con par espejado.
  - `test_duel_context.py`: **11 claves** para sus combatientes sintéticos/canónicos y variantes de contexto.
  - `test_residual_lifecycle.py::test_crimson_shade...`: entrada con el portador vivo y el portador no-muerto que suprime la preparación.
  - `test_native_sigmarite.py::test_native_compile...`: reutiliza `parity/deep/sigmarite-vs-undead`; no se duplicó el caso.
  - En total hay **200 casos `unit/**` de un solo combatiente espejado**, todos con su clave y origen trazables; no se sustituyó ningún escenario.
- **Pruebas de compilación/catálogo trasladadas a rules (registro, sin mover archivos):**
  - `test_catalogue_runtime.py` → `tests/rules/construction/test_catalogue_runtime.py`.
  - `test_shifty_activation.py` (3 pruebas de catálogo/selección) → `tests/rules/construction/test_shifty_activation.py`.
  - `test_local_modifier_variants.py` (2 pruebas de compilación/rechazo) → `tests/rules/construction/test_local_modifier_variants.py`.
  - `test_violent_entry_supplied_summon.py` (1 rechazo de compilación) → `tests/rules/construction/test_violent_entry_supplied_summon.py`.
  - `test_rule_families_a.py` (1 contrato meta de compilación) → `tests/rules/construction/test_rule_families_a.py`.
  Estos registros no mueven archivos ni cambian ids; T07–T13 decidirán el traslado efectivo.
- **Corrección de revisión final:** las cuatro pruebas de `test_native_engine.py` clasificadas como rules y la de `test_native_sigmarite.py` permanecen en `engines/native`, bajo T09: `compile_duel` comprueba la compilación del backend nativo, no la construcción desde KB. Las cuatro primeras reutilizan, respectivamente, `parity/deep/pistol-vs-parry`, `parity/deep/entangle-vs-fencer`, `parity/deep/elite-vs-durable` y `parity/deep/frenzy-vs-heavy`; sigmarite conserva `parity/deep/sigmarite-vs-undead`. Se corrigió únicamente el manifiesto y este registro, sin mover tests ni modificar el corpus.
- **Identificación de entradas:** para cada prueba y `parametrize` se evaluaron helpers, fixtures (`__wrapped__`), asignaciones locales y llamadas `compile_fighter`/`CompiledFighter`, incluyendo helpers transitivos y un interceptor de `compile_fighter` para capturar datos auxiliares como el chart de mutaciones. Los pares se toman de llamadas reales de ataque/duelo; si solo hay un combatiente, se conserva con un par espejado. No se ejecutaron pruebas ni motores.
- **Procedencia:** `source.files` contiene **693 archivos de `sources/knowledge`** leídos realmente, con SHA-256; `origin_files` registra **1.808 archivos de origen**. Cada caso conserva `origin.path`, `origin.node_id` y `origin.sha256`; no hay rutas absolutas, fechas ni prosa editorial.
- **Exclusiones restantes:** **566** = **464 E2E** de rechazo de compilación sin combatientes + **102 pruebas de motor sin dependencia de compilación**. Los 4 archivos sin ninguna clave son `test_exact_phases.py` e `test_interactions.py` (operadores de fase puros) y `test_sorted_dedup.py`/`test_vector_dice.py` (utilidades vectoriales sin combatientes). No se sustituyó ningún escenario por otro más débil.
- **Comprobaciones:** la evidencia previa de T06 acredita que `load_cases` reconstruye los 6.369 casos y recalcula huellas, que los 693 KB y los 1.808 orígenes coinciden con disco y que los 81 archivos están contabilizados; la regeneración produjo el mismo `corpus_sha256`. Tras la corrección del manifiesto se verificaron estáticamente las **1.718 referencias**, los cinco destinos rules y la conservación byte a byte del corpus mediante SHA-256. No se ejecutaron tests ni motores para esta corrección.
- **Límite:** el corpus es la base congelada para T07–T10; cualquier caso adicional se publica como nueva versión. No se ejecutaron motores ni se derivaron expectativas. Sin commits ni pushes.

### T07 — Tests del motor modular

**Inicio:** bloque 2 cerrado: T04, T05 y T06 terminados e integrados.

**Propiedad:** `tests/engines/modular/` y los originales asignados a este paquete.

**Trabajo:** sustituir la preparación mediante KB/compilador por cargas de fixtures, conservando las aserciones de reglas, secuencias, estados y decisiones. Mantener entradas numéricas directas para primitivas. Las pruebas cuyo objeto sea comprobar una compilación permanecen en rules conforme al mapa T01.

**Fin verificable:** la colección conserva identidades y expectativas; la revisión estática confirma la preparación mediante fixtures sin `compile_fighter`; una muestra mínima de conexión solo se ejecuta si falta evidencia válida. No se comprueba el bloqueo de KB ni se exige ejecutar toda la suite modular.

#### T07 — Motor modular entregado para revisión (2026-10-23)

**Estado:** entregada para revisión; no aceptada. De las **954 funciones de test**, **609 ya no compilan**: 591 adaptadas al corpus congelado y 18 que nunca prepararon combatientes (primitivas numéricas directas). Quedan **345**: **61 contratos de construcción** cuyo objeto es una compilación y **284 pruebas de ejecución** que siguen usando `compile_fighter` por carencias del corpus, clasificadas abajo. No se modificó el corpus, el manifiesto, las configuraciones compartidas ni ningún motor.

**Base y propiedad**

- Rama `tests-rework`. Se partió del estado con cambios concurrentes de T03/T04/T05/T06 ya en el árbol; se conservaron sin revertir. Los cuatro archivos cedidos a otros paquetes (`test_complex_sequences.py` → T08; `test_exact_phases.py` e `test_interactions.py` → T02; `test_hatred_bindings.py` → T03) se dejaron intactos y otros agentes los trasladaron después.
- Traslado: **62 archivos** con `git mv` de `tests/python/combat/modular/` a `tests/engines/modular/`. La colección pasa de 1.401 ítems en el directorio original (65 archivos) a **1.383 ítems** en T07; los cuatro archivos cedidos aportan los 18 restantes. Nombres de test, parametrizaciones, marcadores y orden de casos se conservan.
- Nuevo `tests/engines/modular/conftest.py` (propiedad T07, sin tocar `tests/conftest.py`): carga perezosa y única de `tests/engines/fixtures/compiled-cases.json` con `load_cases`, sin importar compilador, KB ni motores. Un caso ausente lanza `AssertionError` con la clave esperada; nunca recompila.

**Interfaz de consumo**

- `precompiled(case_index=0)` (fixture de función) resuelve la clave a partir de la procedencia registrada: `unit/modular/<archivo>/<test>-<conjunto-de-parámetros>-<caso>`. El conjunto de parámetros es la posición de la invocación en el orden de colección de la función, que es el mismo que usó el exportador; el índice de caso permite varias parejas registradas para una misma invocación. `cases` expone el corpus completo para los pocos tests que necesitan elegir explícitamente.
- Semántica de roles verificada y documentada para T08–T10: `call:<helper>` registra `first`/`second` en el orden de los argumentos de la llamada real; **`builders` los registra en orden de compilación**, que puede invertir los roles respecto a la llamada; `same-fighter` indica un único combatiente espejado. Varias conversiones iniciales fallaron por asignar los roles de los casos `builders` como si fueran de llamada; se corrigieron comparando identidad (fighter_id, armas, salvaciones, tags, características).

**Conservación (revisión estática, reutiliza la colección 1.383)**

- Comparación AST de las 954 funciones entre `HEAD` y el estado actual, repetida tras la segunda pasada: **0 diferencias** en el conjunto de tests, en los decoradores `parametrize` y en los marcadores; **0 aserciones eliminadas** (recuento de `assert` por función idéntico). Los 1.383 ítems de colección no cambian: la segunda pasada no altera nombres, parametrizaciones ni descubrimiento. Se revisaron las 33 expresiones de aserción reescritas: todas sustituyen una llamada al constructor por la variable del fixture con el mismo operador y el mismo valor esperado; ninguna cambia el predicado. Una aserción añadida por error en `test_an_indestructible_weapon_can_be_parried_without_a_trap_blade_break_roll` se retiró para dejar el conjunto original.
- Dados, decisiones, contexto, expectativas y transformaciones `dataclasses.replace` locales se conservaron; donde el caso registrado ya contenía el estado posterior a un `replace` idempotente se documentó y se dejó una sola aplicación.

**Evidencia obtenida (no repetida para T07)**

- `python -m pytest tests/engines/modular --collect-only -q` → 1.383 ítems, sin errores de colección.
- Adaptación por lotes: 6 lotes disjuntos (1.367 ítems) ejecutados antes/después de la conversión con idéntico perfil de resultados, incluidos los 4 fallos previos ajenos (`test_the_beast_hunter_qualifiers_are_declared_and_bound`, dos de `test_control_family.py`, `test_every_record_declares_the_canonical_tag`). Las comprobaciones puntuales de los cuatro archivos de la segunda pasada dieron 120, 132, 363 y 79 pasan. La última edición estática (retirada de la aserción añadida) no se volvió a ejecutar, conforme a la validación mínima acordada.
- No se implementaron ni ejecutaron bloqueos de KB: el requisito se retiró. No se ejecutó ninguna batería completa tras la retirada.
- Segunda pasada (grupo 2 y clasificación del grupo 3): sólo revisión estática, sin ejecutar tests, colección, compiladores ni motores. `python -m py_compile tests/engines/modular/*.py` correcto; 591 funciones con fixture y **0** claves de caso ausentes; **0** diferencias frente a `HEAD` en nombres, decoradores y recuento de `assert` de las 954 funciones.

**Clasificación de las 345 restantes (revisión estática)**

| Grupo | Definición | Funciones | Destino |
|---|---|---:|---|
| 1 | Contratos de construcción: asertan sobre la salida de `compile_fighter` o sobre un rechazo, sin ejecutar rondas | **61** (22 archivos) | `tests/rules/construction/` |
| 2 | Ejecución con entradas disponibles en el corpus | **0 pendientes** | cargador `precompiled` |
| 3 | Ejecución con entradas ausentes o incorrectas | **284** (39 archivos) | solicitud a T06 / coordinación |

- **Grupo 1 por archivo:** `test_local_modifier_variants.py` 15, `test_psychology_leadership_connections.py` 8, `test_patrons_and_supplied_states.py` 4, `test_psychology_leadership.py` 4, `test_shifty_activation.py` 4, `test_lunatics_and_mushrooms.py` 3, y 1–2 en `test_always_strikes_first.py`, `test_clockworker_construct_duel.py`, `test_contagious_and_rotten_body.py`, `test_control_family.py`, `test_devoted_and_bitten.py`, `test_dwarf_hireling_kits.py`, `test_ghost_pirate_immunity.py`, `test_hireling_psychology.py`, `test_psychology_identity.py`, `test_shifty.py`, `test_spectral_touch_activation.py`, `test_tc14_whip.py`, `test_trait_projection.py`, `test_violent_entry_supplied_summon.py`, `test_vomit_attack.py`, `test_ye_give_way_results.py`. T06 registró cinco archivos con destino rules; el barrido encuentra además los bloques phase2 de otros diecisiete. **Propiedad:** cedidos al hilo 9 para su separación a `tests/rules/construction/` conservando nombres, decoradores, marcadores, aserciones y cuerpos; T07 no los mueve ni los reescribe.
- **Grupo 2:** la segunda pasada adaptó pruebas en `test_local_modifier_variants.py`, `test_defence_parries_and_ward.py`, `test_psychology_leadership.py`, `test_psychology_identity.py`, `test_source_corrections.py`, `test_leadership_providers.py`, `test_enemy_identity_hatred.py`, `test_weapon_variant_combat.py`, `test_control_family.py` y `test_dark_jester_and_related_families.py`. Los roles se asignaron comparando el estado completo del combatiente registrado (id, características, arma principal/secundaria, armadura, tags, tags de construcción, efectos) con los argumentos del builder original; las inversiones `builders` corregidas incluyen `test_the_cathayan_longsword...` (armoured y portador), `test_a_supplied_engagement...` (llano/sabretusk) y `test_the_nominated_strike...` (usa `first`, no `second`). Comprobación estática de las 591: todo `precompiled(i)` solicitado existe en el corpus para cada conjunto de parámetros (**0 claves ausentes**) y ninguna función usa el fixture sin declararlo.
- **Grupo 3 por archivo:** `test_local_modifier_variants.py` 137, `test_defence_parries_and_ward.py` 18, `test_psychology_leadership.py` 16, `test_psychology_identity.py` 12, `test_enemy_identity_hatred.py` 9, `test_residual_lifecycle.py` 9, `test_source_corrections.py` 9, `test_leadership_providers.py` 8, `test_crude_belch.py` 5, `test_leadership_support.py` 5, `test_shifty_activation.py` 5, y 1–4 en `test_dark_jester_and_related_families.py` (4), `test_domnu_bear_hug.py` (4), `test_duel_observed.py` (4), `test_catalogue_runtime.py` (3), `test_hireling_psychology.py` (3), `test_mim_mutations.py` (3), `test_patrons_and_supplied_states.py` (3), `test_spectral_touch.py` (3), `test_weapon_variant_combat.py` (3), `test_control_family.py` (2), `test_dwarf_troll_slayer.py` (2), `test_alchemist_recovery.py`, `test_all_seeing_eye_of_numas.py`, `test_clockworker_construct_duel.py`, `test_dreamwalkers_undead_foes_fear.py`, `test_duel_equivalences.py`, `test_dwarf_hireling_kits.py`, `test_ghost_pirate_immunity.py`, `test_killing_blow.py`, `test_profile_save_thresholds.py`, `test_psychology_leadership_connections.py`, `test_slayer_deathblow.py`, `test_stateful_rules.py`, `test_tc14_whip.py`, `test_trait_projection.py`, `test_violent_entry_supplied_summon.py`, `test_vomit_attack.py`, `test_ye_give_way_results.py`.
- **Causas del grupo 3**, por orden de volumen: (a) invocaciones que compilan **tres o más combatientes distintos** mientras el caso sólo admite dos —`first`/`second`— (líderes y proveedores, destinatarios múltiples, controles negativos); (b) **controles auxiliares** (`bare()`, `attacker()`, oponentes llanos) no registrados; (c) **estados derivados** (`replace(...)`, `select_shadow_dance`) registrados después de la mutación, no en el estado que el test usa; (d) **invocaciones de parámetro ausentes o con índices salteados**; (e) **casos inexistentes** (`test_catalogue_runtime.py`, `test_duel_observed.py`, `test_dwarf_axe_with_sword...`, `test_local_skill_activation...`, `test_catalogue_offer_roundtrips...`). Los casos `benchmark/*` de `test_duel_observed.py` dependen del límite `maximum_rounds` acordado con T06/T10.

**Solicitud concreta a T06 (sólo las diferencias verificadas)**

| Clave existente | Original que falta | Diferencia exacta |
|---|---|---|
| `.../test_electrical_replaces_only_attack_has_separate_initiative_and_recharges-0-0` (`metal=False`) y `-1-0` (`metal=True`) | `bare(*(('condition.metal-armour',) if metal else ()), initiative=2)` | `second.characteristics.initiative` = **3** en el corpus frente a **2**; en `-1-0` falta `condition.metal-armour` en `global_effects.tags`. `first` coincide. Las dos parejas registradas son idénticas campo a campo, así que el eje `metal` no está representado |
| `.../test_woven_mist_uses_total_attacks_and_initiative_for_first_strike_ties-0-0` y `-0-1` | `dancer('woven-mist')` **antes** de `select_shadow_dance` | El bailarín registrado ya lleva `dance.woven-mist-active`; el test necesita el mismo combatiente (`frenzy=True`, `ward_save=6`, `dance.woven-mist`) **sin** ese tag para ejecutar su propia selección. El oponente de lanza sí coincide |
| `.../test_slay_large_creature_stacks_with_weapon_charge_and_expires-0-0`…`-3-0` | `fighter(*('size.large',))` como víctima | `second` no lleva `size.large` en ninguna de las cuatro invocaciones; `first` (`rule.slay-large-creature`) coincide. Dos de las cuatro parametrizaciones necesitan la víctima etiquetada |

- Añadir a la solicitud general: **si la invocación compila más de dos combatientes, hoy no es representable** con el esquema `first`/`second` del corpus; requiere decisión del coordinador (ampliar el caso o aceptar la excepción). No se inventaron sustitutos ni se cambió ninguna aserción. *Sustituido el 2026-10-23:* la preparación individual por `FighterBuild` cubre más de dos combatientes sin ampliar el caso; ver el apartado de enfoque acordado más abajo.
- Corrección del registro anterior: `test_dark_jester_and_related_families.py::test_a_failed_lycanthrope_roll_keeps_the_printed_injury_penalty` **sí** era representable (`first` llano, `second` con `mechanic.hillman-lycanthrope`, espada) y queda adaptada; el bloqueo anterior era incorrecto. Sigue bloqueada `test_slay_large_creature_stacks_with_weapon_charge_and_expires`.
- **Cesión de propiedad:** el hilo 9 separa los 61 contratos del grupo 1 a `tests/rules/construction/` (archivos de destino nuevos, sin tocar el resto de los archivos de origen); el hilo 8 realiza una auditoría estática de sólo lectura de las conversiones de T07. T07 conserva la coordinación y la escritura de este registro.
- **Pendientes de T07:** los 284 del grupo 3 quedan declarados como adaptación pendiente, no como solución final; no se declara T07 completa. Sin commits ni pushes.

#### T07 — Preparación nominal de cuatro bloques (2026-10-23)

**Estado:** inventario estático preparado; no se han adaptado tests ni lanzado agentes. Rama `tests-rework`, base `8415ba80`, sobre el árbol de trabajo actual. Las huellas por archivo identifican la instantánea; HEAD por sí solo no describe los cambios concurrentes.

**Sustituido (2026-10-23):** el despacho por bloques que describe esta subsección queda sustituido por el enfoque de snapshots individuales por `FighterBuild`. Las listas nominales y sus recuentos se conservan como inventario y evidencia; no asignan trabajo ni habilitan a reclasificar contratos cedidos. Ver «T07 — Enfoque acordado para las preparaciones pendientes (2026-10-23)».

**Corrección del reparto preliminar:** el registro anterior daba 69/68/72/75 funciones de ejecución, pero no incluía los nombres de los 61 contratos ya cedidos a rules. La inspección estática recupera exactamente **345 funciones dependientes de `compile_fighter`**, incluidos esos 61 contratos. No permite etiquetarlos correctamente solo por marcadores: algunos tests de ejecución también llevan marcas de construcción. Los lotes siguientes son candidaturas nominales, no una reclasificación ni permiso para editar contratos cedidos. Los 591 tests ya adaptados y las 18 primitivas quedan fuera.

| Bloque | Candidatas nominales (incluyen contratos reservados) |
|---|---:|
| T07-A | 87 |
| T07-B | 86 |
| T07-C | 86 |
| T07-D | 86 |
| **Total** | **345 = 284 de ejecución + 61 contratos reservados** |

**Barrera de propiedad previa a cada bloque:** el responsable de T07 y el responsable de la extracción a rules marcan cuáles de los nombres enumerados pertenecen a los 61 contratos ya cedidos. Esos nombres se excluyen del trabajo del bloque, sin volver a clasificarlos ni duplicar la extracción. Confirman además que los propietarios anteriores han entregado los archivos afectados. No basta ausencia de procesos o locks para asumir propiedad. El coordinador registra la exclusión nominal y el recuento efectivo antes de autorizar ediciones; se pueden transferir archivos completos todavía no iniciados para compensar una diferencia importante de carga.

**Paralelismo:** los cuatro bloques preparan sus entradas y cambios en paralelo. `test_local_modifier_variants.py` se reparte nominalmente entre A/B: ambos producen parches sobre esta misma instantánea y solo el coordinador escribe el archivo. No se divide el módulo ni se cambian las claves por este reparto. Los demás archivos tienen un solo bloque propietario. Helpers compartidos y `conftest.py` siguen con el coordinador. Las extracciones a rules se aplican mediante el propietario del archivo original, nunca por un segundo escritor concurrente.

**Trabajo autorizado de cada bloque:** identificar estructuras originales ausentes, controles negativos, roles y estado previo a transformaciones; buscar reutilizaciones exactas y entregar solicitudes precisas consumidor/parametrización/rol → entrada. Un test puede cargar varios casos del formato actual; más de dos participantes no justifica por sí solo ampliar el esquema. Completar el consumo cuando el escritor único del corpus publique las claves. No inventar entradas, cambiar aserciones ni aceptar automáticamente excepciones.

**Escritor único del corpus:** corpus, manifiesto y exportador quedan fuera de los cuatro bloques. El coordinador agrupa las solicitudes y autoriza su incorporación al responsable único; los bloques no ejecutan compilación/exportación por separado. Mantener claves existentes y su procedencia. El manifiesto se integra cuando los consumidores estén estables.

**Entrega:** parches o archivos propios, correspondencia de funciones y claves, conservación estática de nombres/decoradores/aserciones/dados/decisiones/contexto y bloqueos exactos. No modificar documentación compartida ni configuraciones. No añadir tests, adaptadores o mejoras, reparar motores, hacer commits o pushes. No ejecutar tests, colección, compiladores, motores, benchmarks ni bloqueos de KB; reutilizar la evidencia anterior.

**Fin:** un bloque con entradas todavía pendientes entrega avance, no cierre. T07 solo cierra tras integrar los cuatro bloques, los 61 contratos y las correspondencias del manifiesto. No se exige obtener suites verdes.

**Despacho:** para asignar un bloque, indicar su letra y remitir a esta sección y a su lista nominal siguiente. Aplican la barrera de propiedad y todas las restricciones anteriores. No es necesario crear otro informe o plan.

##### T07-A — Lista nominal (87 candidatas)

**`tests/engines/modular/test_local_modifier_variants.py`** — 76 candidatas; SHA-256 de la instantánea: `9f2e57517c70595867345b81086cb2a99e42fcd140bedffeb1882bf84b8e788b`.

- `test_mesmerising_dance_blocks_attacks_but_preserves_defence`
- `test_savage_fury_immunity_and_charge_bonus_and_lizardman_exemption`
- `test_penthesilea_canonical_profile_treatment_does_not_duplicate_the_mark`
- `test_penthesilea_dance_transfixes_a_failing_foe_and_fury_scores_the_charge_swing`
- `test_shornaal_uses_highest_two_then_stops_testing_after_success`
- `test_hypnotist_first_attack_breaks_trance_even_when_saved`
- `test_foul_odour_exact_opponents_and_fire_strength`
- `test_wraith_touch_single_unarmed_wound_and_liche_recovery`
- `test_titanic_strength_failed_wound_knocks_down_on_failed_strength`
- `test_ethereal_hit_save_precedes_wound_and_ignores_magic`
- `test_centigor_drunken_frenzy_expires_after_its_turn`
- `test_fire_fear_preserves_branchnymph_printed_psychology_exception`
- `test_racial_hatred_and_noble_disdain_use_canonical_opponent_facts`
- `test_arkhar_is_a_selected_leader_mark_not_a_bandwide_grant`
- `test_wheelo_collision_precedes_blows_and_fear_does_not_cancel_charge`
- `test_sea_singer_beauty_uses_explicit_sex_and_distinct_charge_tests`
- `test_supplied_follow_me_command_expires_after_the_current_turn`
- `test_supplied_ready_to_die_command_changes_the_actual_injury`
- `test_simple_night_goblin_animosity_blocks_only_its_own_turn`
- `test_gaoler_reputation_causes_fear_only_in_humans`
- `test_wizened_supplied_leader_reroll_has_halfling_recipients`
- `test_slayer_compound_rule_preserves_novice_and_rememberer_exceptions`
- `test_ogre_hunter_huuuuge_preserves_light_armour_but_refuses_heavy`
- `test_supplied_righteous_charge_is_mounted_and_expires_after_first_round`
- `test_foul_odour_refuses_any_supplied_open_flame_through_shared_legality`
- `test_ghost_pirate_ethereal_save_is_source_specific`
- `test_wheelo_fitting_modifies_impact_without_changing_crew`
- `test_wheelo_mighty_blow_replaces_strength_with_crew_wound_bonus`
- `test_norse_shield_and_bulwark_are_equipment_bound`
- `test_bog_hunter_stink_applies_to_undead_enemies_too`
- `test_native_whaler_doubles_only_unsaved_aquatic_damage`
- `test_native_pimp_bonus_requires_nominated_female_opponent`
- `test_pimp_nomination_refuses_wrong_recipient_and_nonfemale_target`
- `test_native_priest_strictures_compile_kit_and_refuse_foreign_equipment`
- `test_morrs_servant_fear_exception_has_both_charge_directions`
- `test_native_morr_ceremonial_scythe_is_a_distinct_complete_weapon`
- `test_native_verena_sword_only_keeps_owned_ceremonial_dagger_inactive`
- `test_native_ulric_pelt_is_strength_modified_armour_not_a_ward`
- `test_ulric_pelt_contributes_once_and_the_printed_kit_refuses_other_armour`
- `test_ulric_pelt_protection_is_the_cloak_piece_and_leaves_with_the_cast_off_kit`
- `test_ulric_intense_rivals_reuses_first_round_hatred_only`
- `test_ulric_rival_identity_does_not_expand_to_an_entire_witch_hunter_warband`
- `test_native_war_honed_first_failure_cannot_be_reserved_for_a_later_test`
- `test_war_honed_resource_survives_a_real_crude_belch_round`
- `test_optional_sigmar_enlightened_uses_only_the_supported_opponent_identity`
- `test_sigmar_enlightened_is_offered_separately_and_not_granted_to_other_priests`
- `test_righteous_fury_shared_sisters_skill_filters_targets_and_first_round`
- `test_native_aldred_completes_fellblade_and_its_orc_goblin_extension`
- `test_native_snorri_drinking_results_persist_in_both_player_turns`
- `test_snorri_requires_a_participating_result_without_changing_other_profiles`
- `test_shooting_movement_and_postbattle_hireling_clauses_do_not_block_melee`
- `test_carried_relic_passes_only_first_required_leadership_test`
- `test_arcane_candelabrum_keeps_brazier_attack_but_uses_one_hand`
- `test_native_sister_chooses_two_source_skills_and_completes_a_duel_round`
- `test_native_sister_requires_two_distinct_skills_without_matriarch_access`
- `test_shallya_aura_affects_both_contacting_duelists_except_daemons_and_undead`
- `test_shallya_strictures_only_choose_legal_initial_chargers_and_recognize_onogal`
- `test_son_of_ulric_removes_the_native_unarmed_penalties`
- `test_symbol_of_unity_qualifies_the_opposing_warband`
- `test_house_guard_pride_requires_fierezza_heroes_on_both_sides`
- `test_pikewall_uses_incoming_charge_and_the_active_first_strike_weapon`
- `test_tranquil_fauna_uses_handler_leadership_without_cancelling_charge`
- `test_tranquil_fauna_does_not_guess_animal_or_handler_facts`
- `test_native_eagle_friend_has_separate_first_strike_strength_three_attacks`
- `test_eagle_friend_disappears_with_the_owner_and_respects_tranquil_fauna`
- `test_snerik_keeps_his_source_only_cloak_without_a_fake_duel_effect`
- `test_guiding_dream_rolls_once_and_applies_only_to_the_nominated_hero`
- `test_guiding_dream_refuses_a_nominated_nonhero_and_foreign_mark`
- `test_strigoi_iron_sinews_is_optional_and_changes_real_wounding_once`
- `test_strigoi_kindred_hatred_checks_bloodline_and_preserves_frenzy_and_timing`
- `test_kindred_hatred_requires_bloodline_only_for_vampire_opponents`
- `test_non_slayer_hatred_grant_is_recipient_specific_and_lost_with_psychology_immunity`
- `test_supplied_immunity_condition_consumes_no_fear_test_dice`
- `test_fear_immunity_is_not_psychology_immunity_in_the_real_stupidity_test`
- `test_supplied_hatred_condition_tests_any_enemy_in_the_first_round_only`
- `test_kasgal_dwarf_hard_head_and_hard_to_kill_bind_the_shared_injury_chart`

**`tests/engines/modular/test_mim_mutations.py`** — 3 candidatas; SHA-256 de la instantánea: `22fa295f2a1034483ccb15b0a19d90a86bd22a2a166bed0d12c1686c1d34af78`.

- `test_extra_arm_moves_one_existing_poisoned_copy_with_its_own_clean_snapshot`
- `test_scaled_skin_composes_physical_light_armour_and_shield`
- `test_the_supplied_metal_armour_fact_follows_the_worn_metal_defences`

**`tests/engines/modular/test_weapon_variant_combat.py`** — 3 candidatas; SHA-256 de la instantánea: `c1e5cd09a52bbfa200a41f6def90c403a182b68fedc01e935fc60f9be95ec007`.

- `test_an_ordinary_mace_still_lets_the_worn_armour_save`
- `test_the_cleaver_attack_costs_the_defender_one_point_of_armour_save`
- `test_the_starsword_denies_armour_while_its_ward_exception_saves`

**`tests/engines/modular/test_vomit_attack.py`** — 2 candidatas; SHA-256 de la instantánea: `658860310e273f6eca59590d1efead4b2aaef224597fd696a50c4853e4b30856`.

- `test_canonical_selection_retains_normal_weapon_and_compiles_separate_option`
- `test_unported_option_is_refused_before_optimized_execution`

**`tests/engines/modular/test_contagious_and_rotten_body.py`** — 1 candidatas; SHA-256 de la instantánea: `6bc17b2075508a0407d89debce35c2c04b84c68dcb452e6f243d05067d6766b6`.

- `test_each_origin_executes_contagious_under_its_rotten_body_prerequisite`

**`tests/engines/modular/test_profile_save_thresholds.py`** — 1 candidatas; SHA-256 de la instantánea: `965678acf13de1a1edefb19b7e91a557c45291bbb4a5aa09d3f1d1bd67060ed8`.

- `test_control_compilations_do_not_change_between_boglar_attacks`

**`tests/engines/modular/test_stateful_rules.py`** — 1 candidatas; SHA-256 de la instantánea: `aac3e8f1c7cdafdecf8895998d7621469edd8a2d6fe9b5b908921474c2935e49`.

- `test_reference_spines_acid_blood_and_contagious_are_real_reactions`

##### T07-B — Lista nominal (86 candidatas)

**`tests/engines/modular/test_local_modifier_variants.py`** — 76 candidatas; SHA-256 de la instantánea: `9f2e57517c70595867345b81086cb2a99e42fcd140bedffeb1882bf84b8e788b`.

- `test_woven_mist_uses_total_attacks_and_initiative_for_first_strike_ties`
- `test_shadow_dances_require_a_promoted_minstrel_and_cannot_be_declined_when_available`
- `test_woodsmen_staff_uses_printed_strength_not_balanced_initiative`
- `test_woodsmen_staff_keeps_parry_and_two_hand_compatibility`
- `test_shortsword_keeps_parry_and_grants_the_printed_enemy_armour_bonus`
- `test_fey_quickness_is_acquired_and_combines_with_step_aside`
- `test_bestial_is_innate_vampire_ward_against_mundane_and_magic`
- `test_pestilens_innate_resilience_does_not_stack_with_the_same_selected_skill`
- `test_fen_hard_to_kill_is_recipient_and_fire_qualified`
- `test_priest_bite_follows_both_double_handed_weapons_and_uses_only_own_strength`
- `test_sabretusk_charge_replaces_profile_attacks_only_during_actual_charge`
- `test_unerring_strike_reuses_failed_wound_reroll_on_the_canonical_elf`
- `test_seaguard_has_no_spear_bonus_on_other_weapon_or_other_profile`
- `test_domnu_prize_fighter_only_adds_attack_and_removes_penalties_when_unarmed`
- `test_ogre_hunter_losing_its_last_weapon_falls_back_without_losing_attacks`
- `test_perfect_killer_is_automatic_and_not_applied_to_the_other_hero`
- `test_bitter_valour_rerolls_wounds_using_natural_strength`
- `test_tattoos_are_a_special_save_even_when_armour_is_negated`
- `test_local_skill_activation_is_offered_and_refuses_a_foreign_band`
- `test_wolf_rat_bite_uses_strength_four_without_an_armour_penalty`
- `test_fear_when_charged_changes_hits_only_for_that_round`
- `test_failed_fear_charge_has_no_contact_attacks_or_invented_winner`
- `test_supplied_base_contact_refuses_an_initial_charge_between_the_same_duelists`
- `test_supplied_base_contact_keeps_a_fear_causing_duel_engaged_without_a_charge_test`
- `test_successful_fear_charge_retains_its_real_priority_and_only_one_test`
- `test_source_fear_exemptions_and_automatic_personal_leadership_consume_no_test_dice`
- `test_fear_uses_live_frenzy_loss_and_shared_leader_threshold`
- `test_fear_sixes_override_hit_modifiers_and_automatic_hit_but_allow_one_reroll`
- `test_fear_reaches_shifty_and_collectively_prepared_hits_with_hatred_rerolls`
- `test_fear_requires_known_leadership_only_when_a_test_is_required`
- `test_fear_does_not_turn_passive_spines_into_a_melee_hit_roll`
- `test_acquired_fear_reaches_the_same_real_charge_test`
- `test_band_fear_uses_the_printed_recipient_exceptions`
- `test_chainsaw_sword_grants_bearer_fear_and_only_its_own_armour_penalty`
- `test_cold_blooded_psychology_uses_lowest_two_in_the_real_fear_charge`
- `test_cold_blooded_preserves_explicit_leadership_and_automatic_pass_contracts`
- `test_craven_can_fail_a_fear_charge_even_when_the_fimir_causes_fear`
- `test_draich_craven_received_charge_preserves_cold_blooded_and_sixes_rule`
- `test_troll_stupidity_recipients_are_canonical_and_do_not_leak`
- `test_troll_stupidity_failure_suppresses_attacks_in_the_real_round`
- `test_stupidity_completion_canonical_routes_and_brood_recipient_filter`
- `test_stupidity_completion_supplied_exemption_skips_unknown_leadership_and_clears_history`
- `test_stupidity_completion_handler_uses_own_value_and_never_borrows_leader`
- `test_stupidity_completion_brood_bonus_affects_only_stupidity_tests`
- `test_stupidity_completion_acquired_prior_failure_lasts_until_next_own_turn`
- `test_stupidity_completion_disability_head_injury_uses_the_same_turn_operator`
- `test_remaining_innate_frenzy_grants_execute_and_are_lost_after_knockdown`
- `test_unlimited_hatred_means_any_enemy_not_infinite_duration`
- `test_elf_hatred_filters_individual_identity_and_first_combat_turn`
- `test_elf_identity_and_hatred_do_not_spread_to_animals_or_mixed_recruits`
- `test_stubborn_rerolls_failed_individual_tests_once_with_source_correct_choice`
- `test_barbarian_courage_rerolls_fear_without_rerolling_stupidity`
- `test_fear_immunity_skips_the_test_without_general_leadership_immunity`
- `test_explicit_automatic_leadership_passes_without_dice_or_borrowed_leader`
- `test_psychology_immunity_cancels_individual_tests_and_benefits_only`
- `test_tomb_guardians_psychology_immunity_excludes_the_living_scorpion`
- `test_pilgrims_innate_hatred_retains_first_round_and_immunity_limits`
- `test_spawn_explicit_automatic_leadership_preserves_its_separate_preparation`
- `test_remaining_no_pain_grants_share_the_injury_operator_without_activating_bloated`
- `test_remaining_hard_head_grants_ignore_concussion_without_ignoring_normal_stun`
- `test_slayer_pirates_compound_injury_rules_exclude_thaggi`
- `test_cloak_uses_the_armour_role_and_normal_shield_helmet_composition`
- `test_revenant_is_selected_requires_thirster_and_recovers_at_own_turn_start_despite_fire`
- `test_great_thirster_prerequisite_has_its_own_out_of_action_frenzy_effect`
- `test_rousing_sermon_is_priest_only_once_and_expires_after_own_turn`
- `test_frantic_ignores_weapon_penalties_low_initiative_and_standing_up`
- `test_faith_and_questing_vow_reroll_failed_charge_fear_once`
- `test_questing_vow_is_acquired_knight_only_and_qualifies_non_fear_leadership`
- `test_gibbet_iron_cage_is_inseparable_normal_five_plus_armour`
- `test_frustratingly_tiny_is_acquired_snotling_defence_not_an_innate_goblin_skill`
- `test_canonical_sigmar_and_righteous_aura_restrict_only_first_round_targets`
- `test_honorable_refuses_incapacitated_opponent_without_dice`
- `test_exact_creature_facts_distinguish_undead_possessed_daemons_and_normal_animals`
- `test_undead_hatred_charge_and_morr_injury_reuse_real_operators`
- `test_hellblade_has_exact_nature_filter_and_deadly_wound_boundary`
- `test_torturer_strength_loss_accumulates_to_one_and_exempts_undead`

**`tests/engines/modular/test_spectral_touch.py`** — 3 candidatas; SHA-256 de la instantánea: `37a80c7dcda8ac896053738b2dc1104a0d23d8e23d2eae4faf21ce03de1d8641`.

- `test_real_spirit_host_receives_the_trait_without_fixture_injection`
- `test_established_extra_wound_prevents_barrage_even_when_saved`
- `test_barrage_prerequisite_detects_isolated_mutations`

**`tests/engines/modular/test_always_strikes_first.py`** — 2 candidatas; SHA-256 de la instantánea: `8634905e7b2af86b75f3d68c8a8890f1fc05a634cf147df2c9461e9c84230943`.

- `test_the_fanatic_compiles_the_printed_always_strikes_first_tag`
- `test_lost_innocence_is_selectable_for_the_lahmia_vampire_alone`

**`tests/engines/modular/test_dwarf_troll_slayer.py`** — 2 candidatas; SHA-256 de la instantánea: `7abf29040c937b09a9091bdd46029a41b39b60ba19cb6ed63b92e6bd45f41a1a`.

- `test_monster_slayer_wounds_on_four_but_keeps_a_better_strength`
- `test_berserker_adds_one_only_on_the_charging_turn`

**`tests/engines/modular/test_alchemist_recovery.py`** — 1 candidatas; SHA-256 de la instantánea: `4aee654ec4c4f47b1820f15ce73a0c91c844f220d1c7de928ea80c4d3e352f98`.

- `test_addiction_six_releases_actions_and_grants_vigortia_once`

**`tests/engines/modular/test_dreamwalkers_undead_foes_fear.py`** — 1 candidatas; SHA-256 de la instantánea: `fae6baee59861ff76312eb8bfdb6e93b1bbb37eeac96c2c574f2bdb255835827`.

- `test_a_vampire_charger_takes_no_fear_roll_either`

**`tests/engines/modular/test_shifty.py`** — 1 candidatas; SHA-256 de la instantánea: `f62fa3164429ba3f52fd6208f73997394a71184f2f8ec01c68b2a2e254689902`.

- `test_canonical_halfling_skill_is_selected_and_not_automatically_granted`

##### T07-C — Lista nominal (86 candidatas)

**`tests/engines/modular/test_psychology_leadership.py`** — 20 candidatas; SHA-256 de la instantánea: `45a33132983cb5f460a9254840310d3935b74a6b46e0169b9ba1014dd1490473`.

- `test_ere_we_go_waives_only_the_bearers_own_charging_fear_test`
- `test_ere_we_go_is_shared_by_the_three_green_skin_bands`
- `test_fear_of_elves_is_a_recipient_qualified_directional_fear`
- `test_fear_of_elves_keeps_the_printed_band_and_fanatic_exemptions`
- `test_fear_of_elves_is_a_shared_rule_with_its_own_recipients`
- `test_fear_of_elves_reads_the_models_own_elf_species_fact`
- `test_fear_of_elves_ignores_an_elf_warbands_non_elf_models`
- `test_reikland_military_discipline_widens_the_captains_supplied_radius`
- `test_second_in_command_yields_to_a_usable_witch_doctor`
- `test_second_in_command_grants_only_the_four_inch_big_boss_radius`
- `test_accustomed_to_fear_exempts_only_the_three_printed_undead_kinds`
- `test_accustomed_to_fear_belongs_to_the_four_recipients_only`
- `test_the_two_lahmia_powers_are_selectable_by_their_printed_recipient_only`
- `test_deceive_passes_over_undead_daemons_and_psychology_immune_enemies`
- `test_deceive_never_borrows_a_nearby_leader_for_the_enemy`
- `test_hypnotize_reads_a_supplied_leaders_leadership`
- `test_hypnotize_affects_a_non_immune_enemy_but_not_a_psychology_immune_one`
- `test_enchanting_beauty_lowers_only_a_living_contacting_enemy`
- `test_both_lahmia_powers_keep_the_tests_resource_consumption_on_success`
- `test_ghostly_howl_costs_the_tested_enemy_a_die_of_leadership`

**`tests/engines/modular/test_enemy_identity_hatred.py`** — 9 candidatas; SHA-256 de la instantánea: `23244e91565a7a85200441ee6cae1d88fe63e753b585d93bbd4604694ae1a740`.

- `test_burn_the_witch_targets_the_compiled_spellcaster_identity`
- `test_burn_the_witch_is_shared_by_both_witch_hunter_warbands`
- `test_burn_the_witch_targets_the_casters_the_rule_name_list_missed`
- `test_burn_the_witch_excludes_prayer_users_from_the_caster_identity`
- `test_hang_the_bandit_targets_the_canonical_bandit_and_outlaw_warbands`
- `test_hang_the_bandit_is_shared_by_the_horned_hunter_and_the_initiates`
- `test_profound_hatred_covers_every_opposing_warband_except_the_sisters`
- `test_fanatical_covers_every_printed_warband_category`
- `test_fanatical_reaches_the_attack_tape_only_for_a_listed_warband`

**`tests/engines/modular/test_psychology_leadership_connections.py`** — 9 candidatas; SHA-256 de la instantánea: `9c3878bf4fb86a892dcf038a13d225ffc3e3f593406ad8415f350eee9347d9fe`.

- `test_causes_fear_reaches_the_compiler`
- `test_psychology_immunity_and_fear_immunity_are_distinct_recipients`
- `test_selectable_fear_immunity_needs_its_selection`
- `test_stupidity_and_frenzy_land_on_their_profiles`
- `test_automatic_leadership_auto_passes_a_required_test`
- `test_handler_leadership_and_cold_blooded_reach_their_bands`
- `test_hatred_and_isolationists_reach_their_bands`
- `test_undead_composite_and_its_living_negative_control`
- `test_leader_range_skills_widen_only_their_selected_bearer`

**`tests/engines/modular/test_shifty_activation.py`** — 9 candidatas; SHA-256 de la instantánea: `c55b48a72df4e80ad06fddf73a23e34f19a98afe5b3e67ada8ee2585e57bd278`.

- `test_canonical_heroes_offer_select_compile_once_and_keep_absence_control`
- `test_catalogue_offer_roundtrips_into_canonical_rule_selection`
- `test_unpromoted_canonical_henchmen_do_not_offer_or_compile_the_skill`
- `test_foreign_profile_cannot_select_halfling_skill`
- `test_foreign_profile_cannot_bypass_recipients_with_raw_mechanic_id`
- `test_actual_canonical_bonus_precedes_charger_but_ordinary_attack_does_not`
- `test_absent_not_charged_and_own_charge_controls_have_no_bonus`
- `test_optimized_entries_explicitly_refuse_the_unported_canonical_skill`
- `test_low_level_optimized_entries_refuse_without_losing_other_guards`

**`tests/engines/modular/test_leadership_providers.py`** — 8 candidatas; SHA-256 de la instantánea: `03d0e84d48eb58edaed6d94d8af8d1647cf373fcd69e287c3e06d6f7f72e3569`.

- `test_inspiring_presence_widens_the_dreamer_who_took_it`
- `test_slave_driver_lends_at_three_inches_and_at_six_with_a_scourge`
- `test_slavers_overseer_lends_to_an_explicitly_supplied_slave`
- `test_relay_orders_lends_the_leaders_leadership_through_the_adjutant`
- `test_songster_rerolls_a_failed_test_with_one_more_leadership`
- `test_songster_covers_any_friendly_recipient_without_a_same_band_requirement`
- `test_devoted_rerolls_while_the_warrior_priest_is_supplied`
- `test_broken_spirit_passes_automatically_while_the_slave_merchant_stands`

**`tests/engines/modular/test_crude_belch.py`** — 5 candidatas; SHA-256 de la instantánea: `b9ad9ee8f97d8526f2111bb89c1c766d2f7b728fa6953aa3c8fb65030754ae51`.

- `test_unknown_leadership_and_additional_enemies_fail_before_attack_dice`
- `test_canonical_leader_changes_the_actual_crude_belch_test`
- `test_missing_provider_facts_fail_before_leadership_dice_and_decline_keeps_own_value`
- `test_canonical_darksoul_auto_pass_skips_dice_and_provider_facts`
- `test_additional_canonical_leader_recipients`

**`tests/engines/modular/test_dark_jester_and_related_families.py`** — 4 candidatas; SHA-256 de la instantánea: `cc1e3798e6056a0866bea8894efba5393dbe68814ca2096a13a203508ab6244a`.

- `test_canonical_bindings_and_honest_admission`
- `test_slay_large_creature_stacks_with_weapon_charge_and_expires`
- `test_supplied_charge_and_size_reach_compiled_consumers`
- `test_a_sewn_leader_cannot_lend_its_leadership_ability`

**`tests/engines/modular/test_duel_observed.py`** — 4 candidatas; SHA-256 de la instantánea: `2e05f6cc9ef5b87b66f1e4ee60e5d42d019f2351db0c0a4623ce7e36e1519060`.

- `test_observed_totals_reproduce_the_reference_sample`
- `test_observed_arrays_are_replayable_and_in_range`
- `test_unresolved_duels_report_the_full_round_budget`
- `test_observed_validates_its_bounds`

**`tests/engines/modular/test_catalogue_runtime.py`** — 3 candidatas; SHA-256 de la instantánea: `36ec715ee2d4af15d8c2c91fb3eefd4cbbadd7286ebe6df9b40d03abe7ff39e6`.

- `test_modular_runtime_rejects_a_manually_injected_lance`
- `test_every_legal_profile_can_execute_a_complete_scalar_round`
- `test_every_execution_mechanism_can_enter_the_scalar_round_pipeline`

**`tests/engines/modular/test_dwarf_hireling_kits.py`** — 3 candidatas; SHA-256 de la instantánea: `f534db17762a0a5dac50d9204972b8859b274b157cffa74912898eecf85b3595`.

- `test_the_lantern_rig_stays_a_carried_object_not_a_weapon`
- `test_the_dwarf_hatred_needs_the_enemy_identity`
- `test_the_slayer_pirates_sword_and_pistol_are_one_legal_kit`

**`tests/engines/modular/test_lunatics_and_mushrooms.py`** — 3 candidatas; SHA-256 de la instantánea: `c23f793ed53aac046eee58d45bb0516cb9c266a85a12a73533b61219f1f43d72`.

- `test_every_printed_brew_result_is_supplied_through_its_condition`
- `test_the_brew_table_is_a_supplied_state_and_not_an_unadmitted_condition`
- `test_the_mushrooms_have_no_effect_on_undead_or_the_possessed`

**`tests/engines/modular/test_violent_entry_supplied_summon.py`** — 3 candidatas; SHA-256 de la instantánea: `cf448bb3c4bc002f53021efc940fbd22b1a89fb554c56904118ba99d645ee4eb`.

- `test_repeating_the_supplied_fact_does_not_double_the_bonus`
- `test_the_supplied_fact_needs_its_malignant_spirits_recipient`
- `test_the_rule_binds_the_bonus_to_the_supplied_fact_without_granting_it`

**`tests/engines/modular/test_devoted_and_bitten.py`** — 2 candidatas; SHA-256 de la instantánea: `7f3157e7ac1a1c2b2867d0a6255ed8cb3e2763482f85b883eeae9cfc18aa7296`.

- `test_devoted_is_granted_to_both_printed_recipients_and_to_no_other_profile`
- `test_the_supplied_vampire_condition_projects_only_for_a_recipient`

**`tests/engines/modular/test_ye_give_way_results.py`** — 2 candidatas; SHA-256 de la instantánea: `8661714ab5e1d1171546a6460c3386b0399d331303e674952beadfc2801f6bce`.

- `test_modifiers_do_not_leak_into_non_melee_contexts`
- `test_recipient_guards_and_unselected_noble_has_no_award`

**`tests/engines/modular/test_duel_equivalences.py`** — 1 candidatas; SHA-256 de la instantánea: `79816267c61fea3ff5c1bcc0adb4a21676810e36c0e4827fcb93955434c73037`.

- `test_the_ashigaru_spear_parries_only_under_wall_of_steel`

**`tests/engines/modular/test_slayer_deathblow.py`** — 1 candidatas; SHA-256 de la instantánea: `27da96c830f8fba845c0c263ed086774701b47b1bbbfdbfa1c70f70503a5efd7`.

- `test_tough_as_steel_declares_and_consumes_the_printed_true_grit_chart`

##### T07-D — Lista nominal (86 candidatas)

**`tests/engines/modular/test_defence_parries_and_ward.py`** — 18 candidatas; SHA-256 de la instantánea: `1fec65e38b220df2638f7f0c0cc9e8a50f1e9c14a438a3f93417879e6d2b9866`.

- `test_chosen_of_the_white_tower_rerolls_only_a_sword_or_buckler_parry`
- `test_fen_guard_bark_skin_caps_the_strength_penalty_at_six`
- `test_fen_guard_bark_skin_cutting_edge_is_exempt_from_the_strength_cap`
- `test_fen_guard_bark_skin_fire_ignores_only_the_hide_save`
- `test_halfling_layers_of_fat_ignores_enemy_strength`
- `test_companion_filly_odd_covering_is_a_five_plus_save_negated_by_magic`
- `test_companion_filly_covering_matches_the_dame_precedent`
- `test_silent_brotherhood_cloak_is_the_buckler_item_it_names`
- `test_greenskin_traitor_grants_hatred_to_the_enemy_only_with_psychology_and_first_round_limits`
- `test_corruption_can_force_one_eligible_successful_hit_to_reroll_without_rerolling_a_reroll`
- `test_rememberer_uses_one_selected_pool_with_variant_recipient_and_expiry_limits`
- `test_shaggy_hide_combines_normal_armour_but_respects_the_specific_leather_exception`
- `test_achilles_heel_criticals_when_needing_six_and_stampede_denies_only_charge_armour`
- `test_excellent_reflexes_has_one_special_save_with_a_source_bound_dodge_upgrade`
- `test_magic_acorn_is_hero_only_and_does_not_replace_later_round_misses`
- `test_native_marianna_and_sigmund_source_distinct_no_pain_compositions`
- `test_active_curse_preserves_the_printed_unmodifiable_save`
- `test_dwarf_axe_with_sword_gains_the_printed_failed_parry_reroll`

**`tests/engines/modular/test_psychology_identity.py`** — 14 candidatas; SHA-256 de la instantánea: `e31189465bc6871e0cad21bf979d0f00ce007961420ef96d0fcef5baee2fd5e9`.

- `test_tomb_scorpions_are_living_and_not_undead_in_both_printings`
- `test_the_living_identity_stops_the_undead_foe_exemption_covering_scorpions`
- `test_gnoblars_count_as_greenskins_for_the_canonical_hatred`
- `test_the_fear_exemption_needs_an_undead_charger`
- `test_only_the_nominated_attack_strikes_first`
- `test_the_nominated_attack_and_the_remainder_share_the_pools_own_allocation`
- `test_fanatical_auto_pass_follows_the_supplied_promotion_only`
- `test_free_the_slaves_targets_the_opponents_own_slaver_identity`
- `test_knight_of_purity_autopass_requires_a_supplied_hero_promotion`
- `test_vengeful_hatred_individual_selects_only_the_identified_warrior`
- `test_vengeful_hatred_warband_selects_only_the_identified_warband`
- `test_vengeful_hatred_warband_type_covers_every_warband_of_that_type`
- `test_vengeful_hatred_leader_is_the_identified_instance_that_holds_the_rule`
- `test_vengeful_hatred_refuses_a_half_supplied_or_empty_target`

**`tests/engines/modular/test_residual_lifecycle.py`** — 9 candidatas; SHA-256 de la instantánea: `ca974c1e432e1a573248d0ca7c9298484145155b755c2a2757387cb92d35f141`.

- `test_hypnotic_musk_only_the_printed_animal_or_beast_charger_tests`
- `test_electrical_replaces_only_attack_has_separate_initiative_and_recharges`
- `test_supplied_netted_knockdown_loses_ordinary_frenzy_but_preserves_hood_exception`
- `test_canonical_bear_supplied_tamer_waiver_and_explicit_out_provider`
- `test_canonical_bear_uses_only_nearby_tamer_leadership_for_other_tests`
- `test_canonical_poetry_leader_first_test_and_separate_inspiration`
- `test_canonical_witch_finder_supplied_attempt_requires_named_enemy_and_mark`
- `test_castoff_retains_only_actual_extra_hand_dagger_in_its_physical_slot`
- `test_crimson_shade_has_no_effect_on_undead_or_the_possessed`

**`tests/engines/modular/test_source_corrections.py`** — 9 candidatas; SHA-256 de la instantánea: `75a9c220757057d270b9474f119962374bca33881d1536dcd8823d62ccf14be3`.

- `test_m04_strike_last_controls_whole_round_order`
- `test_m05_spear_order_uses_initiative_in_both_charge_directions`
- `test_m21_spittle_precedes_successful_saving_throws`
- `test_basic_critical_table_doubles_damage_without_an_injury_roll_at_three_wounds`
- `test_weapon_disadvantages_reach_the_consumers`
- `test_m09_pistol_allocation_and_next_turn_fallback`
- `test_m17_infection_toughness_test_faces`
- `test_kusara_suppresses_a_reply_but_never_its_last_attack`
- `test_blackblood_reacts_to_a_close_combat_wound_but_not_to_burning_or_spines`

**`tests/engines/modular/test_patrons_and_supplied_states.py`** — 7 candidatas; SHA-256 de la instantánea: `18fc9b98d2ff84c7b048604c1c6c4562ef4f5199aedb343c7c5feba5d4bce996`.

- `test_hate_stunties_reaches_the_night_goblins_only`
- `test_hate_stunties_is_gone_from_the_sibling_bands_other_records`
- `test_constructs_are_psychology_immune_and_the_human_heroes_are_not`
- `test_troll_brew_results_are_supplied_states_with_their_own_consequences`
- `test_the_promoted_knight_of_purity_auto_passes_a_required_test`
- `test_the_emissary_patron_states_are_the_supplied_branch`
- `test_the_slaanesh_patron_penalty_lands_on_the_engaged_enemy`

**`tests/engines/modular/test_leadership_support.py`** — 5 candidatas; SHA-256 de la instantánea: `b1ccab86bcf9b6716263241a9439e3045586d1029d1a15f7ba73c54a8e50a9f3`.

- `test_dim_witted_leader_lends_his_seven_within_six_inches`
- `test_dark_majesty_widens_the_supplied_leader_radius_to_twelve`
- `test_mob_adds_the_supplied_ally_count_and_denies_the_leader_rule`
- `test_songster_rerolls_one_failed_leadership_test_at_plus_one`
- `test_supplied_victorious_poetry_raises_the_leaders_first_test_once`

**`tests/engines/modular/test_domnu_bear_hug.py`** — 4 candidatas; SHA-256 de la instantánea: `34cedbf76a8d66406217ddacc140de047c0e046cfd194676307bd53db265005f`.

- `test_two_unarmed_hits_replace_into_one_unsaveable_wound`
- `test_losing_the_opposed_roll_deals_no_damage`
- `test_an_armed_domnu_is_never_offered_the_hug`
- `test_hug_replaces_two_hits_and_preserves_a_third_independent_attack`

**`tests/engines/modular/test_hireling_psychology.py`** — 4 candidatas; SHA-256 de la instantánea: `584341673abf6d1da18d24f0d49d593cd73c389ca40edcb2bc4de0a8ae5bc3de`.

- `test_each_trait_fear_row_reaches_causes_fear_once`
- `test_the_ogre_identities_survive_the_fear_projection`
- `test_the_emissary_fear_belongs_to_its_nurgle_patron_only`
- `test_dark_mage_hatred_rerolls_only_against_a_necromancer`

**`tests/engines/modular/test_control_family.py`** — 3 candidatas; SHA-256 de la instantánea: `73479e7051315de509a14de98df5fda53743d6f506ee89d460410a5cd05ae926`.

- `test_khemrian_seduction_reaches_the_legal_selected_recipient_and_round`
- `test_the_lahmia_vampire_reaches_its_own_bloodline_power`
- `test_lahmia_seduction_controls_only_the_printed_male_recipient`

**`tests/engines/modular/test_ghost_pirate_immunity.py`** — 3 candidatas; SHA-256 de la instantánea: `0b1ef3cb5ca0a1550571685bf6438ffc642ad70860db4b036d1198a89e519341`.

- `test_ghost_pirate_poison_immunity_reaches_every_printed_recipient`
- `test_the_living_ghost_pirate_profiles_stay_without_the_immunity`
- `test_poison_immunity_drops_the_poisoned_contribution_of_the_attack`

**`tests/engines/modular/test_trait_projection.py`** — 3 candidatas; SHA-256 de la instantánea: `24c221909060fa607cc3dd356d37b11a6f65906b93bdaaae03b214a4c7a7a532`.

- `test_the_constructs_reach_the_poison_and_no_pain_connections`
- `test_the_bands_human_heroes_stay_without_the_construct_consequences`
- `test_construct_poison_immunity_drops_the_poisoned_contribution`

**`tests/engines/modular/test_clockworker_construct_duel.py`** — 2 candidatas; SHA-256 de la instantánea: `be3f08d03e188a40960a074a9b590ff72e9b25fd4e69599df15badc93cd549d7`.

- `test_both_constructs_carry_their_admitted_immunities`
- `test_a_poisoned_weapon_leaves_the_construct_unpoisoned`

**`tests/engines/modular/test_tc14_whip.py`** — 2 candidatas; SHA-256 de la instantánea: `5426d2512d1824e87c52034f85bda7a588737de9ab07b5506427e2f40b507bf7`.

- `test_canonical_profiles_and_source_variant_stay_distinct`
- `test_snake_fear_is_opponent_qualified_and_does_not_make_heinrich_cause_fear`

**`tests/engines/modular/test_all_seeing_eye_of_numas.py`** — 1 candidatas; SHA-256 de la instantánea: `c176c784f7dc705fde42133b7125d9f075d68c36cec0302d64223e069c8636f5`.

- `test_strength_and_weapon_modifiers_move_the_armour_save_but_never_the_artefact_save`

**`tests/engines/modular/test_killing_blow.py`** — 1 candidatas; SHA-256 de la instantánea: `ba2dfeac32552497134438803907d9fd8f0c8a6ce0f50ecc8438c58107dc6dca`.

- `test_adjacent_hit_and_foreign_profile_still_roll_to_wound`

**`tests/engines/modular/test_spectral_touch_activation.py`** — 1 candidatas; SHA-256 de la instantánea: `19acf57091b8971e6d543fb4e7c1b0cd53ea4cd1ca48133ad90c83db7b88cba4`.

- `test_other_canonical_profiles_do_not_receive_spectral_touch`

#### T07 — Enfoque acordado para las preparaciones pendientes (2026-10-23)

**Estado:** acuerdo registrado; no se ha adaptado ninguna preparación nueva con este enfoque y T07 no se declara cerrada. Se conserva lo entregado: 591 tests adaptados, 18 primitivas numéricas directas y 16 contratos de construcción separados a `tests/rules/construction/`. Quedan **69 preparaciones pendientes de T07-D** —34 parcialmente convertidas y 35 intactas—, con **0 diferencias** de aserciones y decoradores `parametrize` frente a `HEAD` en los archivos revisados. Este apartado no cambia recuentos históricos ni declara aceptada ninguna tarea.

**Regla de preparación**

- Se conservan las conversiones anteriores válidas: nombres, parametrizaciones, aserciones, dados, decisiones, contexto y expectativas no cambian.
- Cada preparación pendiente se resuelve con un **snapshot individual** indexado por el `FighterBuild` completo y por el contexto de compilación relevante. Varios tests que construyan exactamente esa configuración reutilizan el mismo snapshot.
- Se mantienen los builders y las transformaciones posteriores originales; **solo** se sustituye la llamada al compilador por el cargador común. Los cuerpos no se reescriben para acomodar el formato y no se introducen sustitutos aproximados.
- Los contratos de construcción de `tests/rules/construction/` siguen usando el compilador real: comprueban la compilación, no la ejecución. No se adaptan a snapshots.
- Una entrada ausente o incompatible falla de forma explícita y se solicita al responsable de generación. No se recompila automáticamente ni se reutiliza un snapshot que no corresponda.
- El formato del índice y del snapshot lo acuerdan el cargador y la generación antes de producir entradas; este documento no fija nombres de API, campos ni claves.

**Responsabilidades vigentes**

- **Agente 1 — contratos:** integra en `tests/rules/construction/` los contratos de construcción ya separados, con sus cuerpos, aserciones y marcadores. No adapta consumidores ni genera snapshots.
- **Agente 2 — cargador:** implementa el cargador común y el contrato de carga que consumirán los tests. No genera snapshots ni edita contratos.
- **Agente 3 — configuraciones y snapshots:** reúne las configuraciones (`FighterBuild` y contexto de compilación) de las preparaciones pendientes y genera los snapshots cuando el formato esté acordado. Es el único que compila entradas; no edita tests consumidores ni contratos.
- **Consumidores:** su adaptación depende de que el cargador y los snapshots estén disponibles; no se inicia por bloques ni por listas nominales. Cada archivo conserva un único escritor y el coordinador registra la propiedad.

**Validación**

- Revisión estática de builders, transformaciones, aserciones y correspondencia de entradas; sin ejecutar tests, colección, motores ni benchmarks.
- La compilación puntual de entradas corresponde solo al responsable de generación, como comprobación de sus snapshots.
- Sin baterías completas, certificación funcional ni bloqueos de KB. La colección afectada y una muestra mínima de conexión solo se ejecutan si falta evidencia válida, conforme a la política general.

**Divergencias y contradicciones pendientes**

1. **Rechazos de compilación dentro de tests de ejecución:** `test_khemrian_seduction_reaches_the_legal_selected_recipient_and_round` (en `test_control_family.py`) y `test_knight_of_purity_autopass_requires_a_supplied_hero_promotion` (en `test_psychology_identity.py`) no tienen ejecución que congelar. Deben decidirse como contrato de construcción o conservar el compilador de forma explícita; ninguna de las dos opciones se aplica todavía.
2. **Prueba que parchea el pool:** `test_the_nominated_attack_and_the_remainder_share_the_pools_own_allocation` depende de `monkeypatch`, no solo del `FighterBuild`. Falta decidir si se prepara ese estado por una vía acordada o si queda fuera del enfoque.
3. **Correspondencia con el corpus congelado:** el corpus y su manifiesto usan claves de caso y parejas `first`/`second`; el nuevo índice por `FighterBuild` debe conservar la correspondencia con las 591 conversiones previas sin renombrar claves publicadas. T06 sigue siendo el escritor único de `tests/engines/fixtures/` y en este acuerdo no se regenera ni se edita el corpus.
4. **Estados capturados tras una transformación:** las entradas actuales de `electrical` (iniciativa 3 y sin `condition.metal-armour` en la variante `metal=True`) y del bailarín de `woven-mist` no representan el estado que el test usa. El snapshot debe corresponder al estado previo a la transformación; se corrige en la generación, no adaptando el test.

#### T07 — Conexión del paquete de 42 preparaciones al cargador común (2026-10-23)

**Resultado integrado:** de las 42 funciones enumeradas en `outputs/T07-A-pending-builders.md`, tres ya se habían trasladado a rules (`test_sigmar_enlightened_is_offered_separately_and_not_granted_to_other_priests`, `test_canonical_selection_retains_normal_weapon_and_compiles_separate_option` y `test_each_origin_executes_contagious_under_its_rotten_body_prerequisite`). Las **39 restantes** usan ahora el callable `compiled_builds.fighter` en sus preparaciones: 30 en `test_local_modifier_variants.py`, 3 en `test_mim_mutations.py`, 3 en `test_weapon_variant_combat.py`, 1 en `test_vomit_attack.py`, 1 en `test_profile_save_thresholds.py` y 1 en `test_stateful_rules.py`.

La conexión es un fixture local `_frozen_compiles` activado mediante `pytest.mark.usefixtures` únicamente en las funciones del paquete. Reutiliza el fixture de sesión común y sustituye el global `compile_fighter` durante cada prueba; no altera builders, roles ni transformaciones posteriores. Se conserva el import original para preparaciones fuera de este paquete que siguen pendientes: esto no constituye una adaptación global de T07 ni un fallback cuando falta un snapshot.

**Evidencia mínima:** cuerpos y firmas AST originales idénticos; decoradores previos intactos, salvo la adición explícita de `usefixtures`; sintaxis correcta. Las claves capturadas para el paquete están presentes en el documento; las variantes de pikewall (pica/maza) y tranquil fauna (`fauna_animal_kind=handled`) se consultaron explícitamente porque la extracción previa las declaraba no resueltas. Se comprobó la inyección y restauración del callable con una preparación original por archivo, usando solo helpers de construcción aislados y el cargador. No se ejecutaron módulos de tests completos, cuerpos de tests, colección, compiladores, combates, motores ni benchmarks. Snapshot, corpus y manifiesto sin cambios. Sin commits ni pushes.

#### T07 — Reconexión del resto de los tests modulares al cargador común (2026-10-23)

**Resultado:** los tres archivos modulares que aún compilaban con el callable real y seguían en este encargo usan ahora `compiled_builds.fighter`: `test_ye_give_way_results.py`, `test_control_family.py` y `test_local_modifier_variants.py`. Con los 36 archivos reconectados antes y la referencia de `test_leadership_providers.py`, ningún test modular ejecuta el compilador salvo los rechazos deliberados y los dos archivos cedidos a otro responsable.

**Forma de la conexión**

- `test_ye_give_way_results.py`: inyección de módulo, igual que las 36 reconectadas antes (`compile_fighter = None` y fixture autouse que inyecta `compiled_builds.fighter`); se retiró el import del compilador.
- `test_control_family.py` y `test_local_modifier_variants.py`: conservan el import real porque contienen una prueba que comprueba un rechazo del compilador; reutilizan el fixture local `_frozen_compiles` ya existente y activan el cargador con `pytest.mark.usefixtures`. En `test_local_modifier_variants.py` se añadieron 104 marcas (134 en total) y el fixture sigue sin ser autouse; en `test_control_family.py` se añadió el fixture y una sola marca.
- Sin cambios en builds, parámetros, aserciones, dados, decisiones, contexto ni transformaciones posteriores: la comparación AST contra la copia previa a la reconexión no encuentra funciones perdidas ni cuerpos distintos; las únicas diferencias son los decoradores `usefixtures` y el bloque de inyección.

**Cargador y snapshots**

Consulta de los requests de los tres archivos con el cargador real: 275 consumidores, 1 947 llamadas de preparación y 300 claves únicas, todas servidas por `tests/engines/fixtures/compiled-builds.json` (517 entradas en esa revisión, `sha256 8cdcf2db…`; hoy 520 tras el cierre de T07). **No se añadió ninguna entrada**: los ausentes son solo dos rechazos deliberados y dos artefactos del pase estático que ningún test ejecuta —`hero(WON)` en `test_modifiers_do_not_leak_into_non_melee_contexts[1]` y `canonical('guild-of-disgraced-engineers-mim','informers',…)` en la rama `band == 'black-dwarfs'` de `test_remaining_hard_head_grants_ignore_concussion_without_ignoring_normal_stun[1]`—, que no se congelaron por no ser requests de ejecución. Cero compilaciones nuevas.

**Excepciones de compilación conservadas (sin adaptar)**

- `test_control_family::test_khemrian_seduction_reaches_the_legal_selected_recipient_and_round` (`pytest.raises(ValueError, match="special rule is not available")`).
- `test_local_modifier_variants::test_shadow_dances_require_a_promoted_minstrel_and_cannot_be_declined_when_available` (`pytest.raises(ValueError, match="not available")`).

**Archivos liberados a otro responsable**

`test_psychology_identity.py` (`sha256 0cc403c9…`, 32 787 bytes) y `test_defence_parries_and_ward.py` (`sha256 06701577…`, 77 606 bytes) se ceden sin tocar: no tienen inyección, conservan el import real y sus únicos requests sin congelar son sus respectivos rechazos deliberados (`test_knight_of_purity_autopass_requires_a_supplied_hero_promotion` y `test_magic_acorn_is_hero_only_and_does_not_replace_later_round_misses`); el resto de sus builds ya está en el documento. `test_psychology_identity` conserva además `test_the_nominated_attack_and_the_remainder_share_the_pools_own_allocation`, que depende de `monkeypatch`.

**Generación:** `tools/verification/generate_compiled_builds.py --write` publica la unión con las entradas ya congeladas, reutiliza sus resultados sin recompilar, aborta ante conflicto, desaparición o cambio de una entrada congelada y escribe de forma atómica.

**Verificación:** sintaxis e importación de los tres archivos, conservación AST y consultas al cargador; sin tests, colección, motores, combates, benchmarks ni comprobaciones de KB. Sin commits ni pushes.

#### T07 — Cierre de preparaciones con el snapshot ampliado (2026-10-23)

**Estado vigente.** Sustituye, para el estado actual, los recuentos de pendientes de las subsecciones anteriores; estos se conservan como registro histórico de cada revisión.

- `tests/engines/fixtures/compiled-builds.json` contiene ahora **520 entradas**: se añadieron las **tres** de Vengeful Hatred (`67c6a4fd…`, `ec912885…`, `a6199ab7…`) y se conservaron las **517** anteriores sin cambios.
- `test_vengeful_hatred_warband_type_covers_every_warband_of_that_type` lleva `usefixtures("_frozen_compiles")` y sus **seis preparaciones** —portador, cuatro `zombie-3` (dos bandas × dos rosters) y el control negativo de night goblins— resuelven mediante el cargador.
- El rechazo deliberado de Knight of Purity **permanece en el compilador real**: no es una entrada pendiente ni un fallo del snapshot.
- **Límite del generador:** no resuelve automáticamente las variables de bucle de esa configuración (`band`, `collection`, `warband_instance`). Los resultados ya congelados se conservan mediante la generación por unión, de modo que la ampliación no reescribe las entradas previas; no se abre trabajo nuevo por esta limitación.
- Con ello, `test_psychology_identity.py` queda con 11 de 20 tests conectados y solo el mixto de Knight of Purity con compilador real. El resto de modular mantiene el patrón ya registrado.

**Repercusión sobre T11:** no cambia la selección, el manifiesto ni el presupuesto. El documento de builds es un fixture independiente del corpus de casos, así que sus 1.734 claves, 6.385 casos, 14 destinos de rules y `corpus_sha256 = ddf4a7d5…` siguen siendo los vigentes y no requieren remapeo.

### T08 — Tests del motor vectorial

**Inicio:** bloque 2 cerrado: T04, T05 y T06 terminados e integrados.

**Propiedad:** `tests/engines/vectorized/` y los originales asignados a este paquete.

**Trabajo:** adaptar la preparación a los fixtures comunes sin cambiar las aserciones de lotes, estados, decisiones, reproducibilidad y paralelismo. Mantener controles de límites y errores. No reimplementar reglas ni modificar el motor para acomodar los tests.

**Fin verificable:** la colección conserva identidades y expectativas; la revisión estática confirma la preparación mediante fixtures sin `compile_fighter`, incluidos procesos auxiliares afectados. Solo se ejecuta una muestra mínima de conexión si falta evidencia válida, sin bloqueo de KB. Los fallos del vectorial incompleto no se investigan ni se exige ejecutar toda su suite.

#### T08 — Tests vectoriales adaptados (2026-10-23)

**Estado:** consumo de fixtures completado salvo el pendiente `cripple`; entrega para revisión, no aceptada. Solo se trasladaron, dividieron y adaptaron tests: no se modificó el motor, el corpus, el manifiesto ni configuraciones compartidas. La colección de los archivos divididos y una muestra mínima se ejecutaron; el detalle y los límites están en «Comprobaciones ejecutadas». Los fallos funcionales observados pertenecen al motor, a datos del catálogo o al entorno y no se investigaron.

**Traslado e infraestructura**

- Los 12 archivos de T01 se movieron con `git mv` a `tests/engines/vectorized/`: los 11 de `tests/python/combat/vectorized/` y `test_complex_sequences.py` desde `tests/python/combat/modular/`. Se conservan nombres, marcadores `phase*` y el resto del contenido.
- `tests/engines/vectorized/conftest.py` define el fixture de sesión `vector_case`: carga `tests/engines/fixtures/compiled-cases.json` con `tools.verification.compiled_cases.load_cases`, resuelve claves relativas a `unit/vectorized/` y falla con `AssertionError` si la clave no existe. No lee KB ni importa el compilador. Las claves ya publicadas bajo `unit/modular/test_complex_sequences/**` se usan tal cual, porque una clave publicada no se renombra.

**Tests adaptados a fixtures**

| Archivo | Tests adaptados | Correspondencia |
| --- | --- | --- |
| `test_backends.py` | 2 | par congelado del propio test |
| `test_observations.py` | 4 | `first`/`second` del caso; el helper local ya no compila |
| `test_parallel_numpy.py` | 2 (el plan de lotes no compila) | par espejado congelado |
| `test_psychology_vectorized.py` | 6 | variantes congeladas por test; el oponente por defecto se reutiliza del caso de la reliquia |
| `test_complex_sequences.py` | 3 | claves `unit/modular/test_complex_sequences/**` |
| `test_vectorized_engine.py` | 28 | `first`/`second` por caso, con índices por parámetro y por variante |
| `test_shared_families.py` | 6 de ejecución | casos propios; el toro se reutiliza de su caso de carga y el humano del caso del toro |
| `test_rule_families_a.py` | 2 de ejecución | pares congelados (`animal` y `contagious`/`marks`) |
| `test_rule_families_b.py` | 6 de proyección/ejecución | pares congelados; `_tagged` sigue aplicando los tags revisados |
| `test_runtime_regressions.py` | 36 | pares y variantes congeladas; imports del compilador eliminados de esos tests |

- La reutilización entre casos se aceptó solo con igualdad completa de `CompiledFighter`: el luchador base con liderazgo 7 de psicología, el toro de `test_bull_charge...` y el base de `test_bull_charge...` como humano. No se emparejó por nombre.
- Cuando el corpus guarda el combatiente previo a un `replace` del test, se conserva el `replace` original sobre el ejemplar congelado: atacante automático de `hard_to_kill`, martillo sigmarita, variantes `_tagged`, `skink`, hachas enanas y `scarecrow`. En los casos donde el corpus ya guarda el resultado del `replace` se usa directamente.
- Se conservaron aserciones, dados (`FixedRng`, `ScriptedRng`, `SequenceRng`), decisiones, límites (`simulations`, `seed`, `batch_size`, `maximum_rounds` siguen literales en cada test porque el corpus vectorial guarda los límites por defecto), el contrato de paralelismo (`workers` 1/2/4 y comparación exacta) y la parametrización `protection` de `test_profile_two...`; el índice de variante se deriva del propio `EffectSet` para no cambiar los ids.

**Separación de construcción y catálogo (segunda pasada)**

Los bloques cuyo objeto es la construcción de la banda o el catálogo de conocimiento se separaron a `tests/rules/` sin cambiar nombres, decoradores, parametrizaciones, aserciones ni cuerpos. No se añadió ni retiró ningún test: son las mismas funciones, con el mismo marcador `phase5_vectorized`.

| Destino | Origen | Tests |
| --- | --- | --- |
| `tests/rules/construction/test_vectorized_family_contracts_a.py` | `test_rule_families_a.py` | 4 |
| `tests/rules/construction/test_vectorized_family_contracts_b.py` | `test_rule_families_b.py` | 4 |
| `tests/rules/construction/test_shared_family_contracts.py` | `test_shared_families.py` | 2 |
| `tests/rules/construction/test_restricted_weapon_contracts.py` | `test_runtime_regressions.py` | 2 (6 ítems con la parametrización) |
| `tests/rules/knowledge/combat/test_canonical_family_catalogue.py` | `test_shared_families.py` | 6 contratos de catálogo KB |

- **Construcción A:** `test_animal_friendship_and_contagious_traits...`, `test_construction_contracts_enforce...`, `test_pirate_mercenary...` y `test_remaining_meta_contracts...`.
- **Construcción B:** `test_mandatory_mutations...`, `test_construction_contracts_validate...`, `test_proven_warrior...` y `test_scaly_skin_spawn...`.
- **Construcción compartida:** `test_shared_compiler_contracts...` y `test_arms_master...`.
- **Restricciones de equipo:** `test_restricted_weapons_reject...` (5 armas) y `test_restricted_weapons_and_toughened...`.
- **Catálogo KB:** los seis contratos de `implemented-canonical-families.yaml`, roster, parámetros de familias de efecto único, Bow Discipline y textos de Art of Silent Death, con su ayudante `_family_binding`.

**Propiedad de los destinos:** el paquete T08 cede estos archivos a `tests/rules/construction/` y `tests/rules/knowledge/combat/`, cuyos propietarios son el paquete de reglas/construcción (T03) y el de conocimiento. T07 no tiene archivos en esos directorios ni consume sus tests, por lo que la transferencia no solapa su paquete; la cesión queda registrada aquí para el coordinador. T08 conserva la propiedad de los cuatro archivos vectoriales reducidos.

**Estado de la preparación en el paquete vectorial**

- Observación estática, no una comprobación exigida: tras la separación no queda ninguna importación de `mordheim_knowledge` ni de sus cargadores en `tests/engines/vectorized/`.
- `compile_fighter` ya no se usa para preparar estos tests. La única llamada restante es la del `cripple` de `test_disability_guardian...`, conservada como excepción aceptada; el resto de bloques de ejecución carga el corpus (ver «Consumo de fixtures y pendiente cripple»).
- `test_scaly_skin_spawn...` pasó a construcción, por lo que sus variantes `spawn`, `amazon` y `untiring` ya no son una necesidad de T08.

**Bloqueos y necesidades del coordinador**

1. **Rutas compartidas:** `tools/mordheim-utils.py` mantiene `SCOPE_PATHS["vectorized"] = ("tests/python/combat/vectorized",)` y esa misma ruta dentro de `deterministic`; `coverage_gate.DEFAULT_SUITES` también. Tras el traslado deben apuntar a `tests/engines/vectorized` (y `tests/engines/modular` donde corresponda). T08 no editó configuraciones compartidas; sin este ajuste los scopes seleccionan un directorio sin tests.
2. **Corpus v2:** publicado por T06 con 6.385 casos; T08 consumió 15 entradas nuevas y reutilizó dos existentes. No quedan peticiones de T08 salvo la variante `cripple`, que no es recuperable (abajo).
3. **Destino rules:** resuelto en esta pasada mediante la separación descrita; la cesión de propiedad queda registrada para el coordinador y T03. No se modificaron archivos de otros paquetes.
4. **Preparación pendiente:** solo el `cripple` de `test_disability_guardian...` conserva `compile_fighter`, como excepción aceptada y documentada; el resto de T08 carga fixtures.
5. **Datos de catálogo:** la muestra mínima detectó dos fallos en los tests trasladados que no dependen de la ubicación ni de las importaciones: `skill.mighty-blow` no está disponible para `pit-fighters/ogre-pit-fighter` y el roster declara 998 miembros frente a 964 reglas. Se reportan sin investigar ni reparar, porque su causa está en datos/expectativas ajenos a esta separación.

**Comprobaciones ejecutadas**

- `python -m py_compile tests/engines/vectorized/*.py`: sin errores.
- En la primera pasada, `python -m pytest tests/engines/vectorized --collect-only -q`: **135 tests**, exit 0. El inventario de T01 (137) se conserva: los dos tests de cobertura de catálogo de `test_rule_families_a/b` ya habían pasado a `tests/tooling/evidence/test_catalogue_family_coverage.py` con T05. Reparto entonces: backends 2, observations 4, parallel 3, psychology 6, complex 3, rule_families_a 8, rule_families_b 10, runtime 43, shared 22, sorted_dedup 3, vector_dice 3, vectorized_engine 28. Tras la separación, el reparto vigente es el de «Comprobaciones de la separación»: 113 en vectorizado y 22 en rules.
- **Muestra sin KB ni compilador:** seis nodeids de los seis archivos plenamente adaptados, ejecutados con un `MetaPathFinder` que rechaza cualquier import de `mordheim_knowledge` o `mordheim_construction`: **5 pasan, 1 falla** (`test_single_batch_samples_are_unchanged_by_the_parallel_path`, `BrokenProcessPool` del proceso auxiliar). El bloqueo no se activó en ningún caso: la carga y ejecución usaron solo el corpus. El fallo del pool auxiliar no se investigó por ser ajeno a la reforma.
- **Muestra en archivos con bloques acoplados:** ocho nodeids de `runtime_regressions`, `shared_families`, `rule_families_a` y `rule_families_b` (steel whip, gaoler, tentacle, body slam, skink hunter, force of will, contagious, lazy characteristics): **8 pasan**.
- **Claves y equivalencia:** las 105 claves literales resuelven contra el corpus; las dos plantillas dinámicas (`test_observations` y el índice de `protection`) resuelven con sus valores reales. La reutilización entre casos se comprobó por igualdad completa de `CompiledFighter` (base, toro, amigo/animal y los pares de proyección), no por nombre.
- **Identidades:** comparación AST contra `HEAD` de los 12 originales; no hay funciones añadidas ni retiradas salvo los dos tests ya cedidos a T05. Se conservan las parametrizaciones (`runtime` 39 funciones → 43 ítems; `vectorized_engine` 27 → 28; `protection` mantiene sus ids).
- **Corpus intacto:** `load_cases` reconstruye 6.369 casos, 29.209.623 bytes, `corpus_sha256 = ebed92c1638d4555e5924c56f0c92e43f21b3c8539ce8c4c887a87b455f1c40f`, idéntico al manifiesto. No se editaron `compiled-cases.json` ni el manifiesto.
- Los 12 archivos existen en `tests/engines/vectorized/`; en `tests/python/combat/vectorized/` solo queda `__pycache__` y `test_complex_sequences.py` ya no está en `modular/`. Las marcas de fase siguen presentes.

**Comprobaciones de la separación (segunda pasada)**

- `python -m py_compile` de los cuatro archivos vectoriales reducidos y los cinco nuevos: sin errores.
- `pytest --collect-only` de esos nueve archivos: **83 tests**, exit 0 (los mismos que contenían los cuatro archivos antes de dividir). Reparto: `rule_families_a` 4, `rule_families_b` 6, `shared_families` 14, `runtime_regressions` 37; construcción A 4, construcción B 4, construcción compartida 2, restricciones 6, catálogo KB 6.
- `pytest -q --collect-only tests/engines/vectorized`: **113 tests**, exit 0. Con los 22 trasladados a `tests/rules/` se conservan los **135** del inventario anterior. No se añadieron ni retiraron funciones: las 22 trasladadas conservan nombre, decoradores, parámetros y cuerpo extraídos por AST.
- **Muestra mínima de conexión** (5 nodeids, uno por archivo nuevo): **3 pasan y 2 fallan**. Pasan `test_remaining_meta_contracts...`, `test_proven_warrior...` y `test_restricted_weapons_and_toughened...`, lo que confirma `ROOT = parents[3]` y las importaciones. Fallan `test_arms_master...` (`skill.mighty-blow` no disponible para `pit-fighters/ogre-pit-fighter`) y `test_family_roster...` (998 miembros frente a 964 reglas). Ambos fallos proceden de datos/expectativas del catálogo, no de la ubicación ni de las importaciones; se reportan sin investigar ni reparar. El test KB sí cargó `ROOT = parents[4]` correctamente.

#### T08 — Solicitud de entradas precompiladas a T06 (2026-10-23)

**Estado:** registro histórico. Esta tabla conserva la solicitud original; T06 ya publicó las entradas y T08 las consumió. Las claves y reutilizaciones finales están en «Consumo de fixtures y pendiente cripple». La fila `cripple` no se publicó. No se generaron fixtures ni se modificaron `compiled-cases.json` ni su manifiesto desde T08.

Convención: `build(band, profile, collection=...)` equivale a `FighterBuild("mordheim", band_id=band, profile_id=profile, collection=collection, ...)`; `runtime.build(...)` equivale a `FighterBuild(ruleset="mordheim", characteristics=Characteristics(3, strength, toughness, wounds, 3, attacks), ...)`.

| Test consumidor | Variante | Configuración exacta | Clave propuesta |
| --- | --- | --- | --- |
| `tests/engines/vectorized/test_rule_families_a.py::test_anvil_head_death_blow_energy_focus_and_mark_are_executable_combat_choices` | `energy` | `build("battle-monks-of-cathay", "dragon-monks", characteristics=Characteristics(4, 3, 3, 1, 4, 3), main_weapon_id="weapon.fist", special_rule_ids=("band--battle-monks-special-skills-energy-focus",), energy_focus_attacks=2)` | `unit/vectorized/test_rule_families_a/test_anvil_head_death_blow_energy_focus_and_mark_are_executable_combat_choices-0-1` |
| ídem | `mark` | `build("lustria-lizardmen", "skink-priest", collection="trollheim", special_rule_ids=("band--sacred-mark-of-the-old-ones",))` | `...-0-2` |
| `tests/engines/vectorized/test_rule_families_a.py::test_disability_guardian_unarmed_and_onogal_have_observable_runtime_effects` | `cripple` | `build("chaos-streets-mordheim-inhabitants", "cripples", collection="trollheim")` | `unit/vectorized/test_rule_families_a/test_disability_guardian_unarmed_and_onogal_have_observable_runtime_effects-0-1` |
| `tests/engines/vectorized/test_shared_families.py::test_unarmed_fighting_and_eshin_mastery_have_their_exact_attack_bonuses` | Eshin Mordheim, desarmado | `build("skaven-clan-eshin", "assassin-adept", main_weapon_id="weapon.fist", special_rule_ids=("band--skaven-special-skills-art-of-silent-death",))` | `unit/vectorized/test_shared_families/test_unarmed_fighting_and_eshin_mastery_have_their_exact_attack_bonuses-0-1` |
| ídem | Eshin Trollheim, desarmado | `build("trollheim-skaven-clan-eshin", "assassin-adept", collection="trollheim", main_weapon_id="weapon.fist", special_rule_ids=("band--skaven-special-skills-art-of-silent-death",))` | `...-0-2` |
| ídem | Deathbringer, desarmado | `build("chaos-streets-deathbringers", "shadow-blade", collection="trollheim", main_weapon_id="weapon.fist", special_rule_ids=("band--deathbringer-special-skills-art-of-unarmed-combat",))` | `...-0-3` |
| ídem | Eshin Mordheim, garras | la variante 1 con `main_weapon_id="weapon.fighting-claws"` | `...-0-4` |
| ídem | Eshin Trollheim, garras | la variante 2 con `main_weapon_id="weapon.fighting-claws"` | `...-0-5` |
| ídem | Deathbringer, garras | la variante 3 con `main_weapon_id="weapon.fighting-claws"` | `...-0-6` |
| `tests/engines/vectorized/test_runtime_regressions.py::test_steel_whip_charge_bonus_matches_modular_round_modifier` | seis armas | `runtime.build(main_weapon_id=...)` con `weapon.bagh-nakh`, `weapon.stiletto`, `weapon.cathayan-longsword`, `weapon.yari-two-handed`, `weapon.long-boat-hook` y `weapon.draich`; `second = runtime.build()` (el plano de `-0-0`) | `unit/vectorized/test_runtime_regressions/test_steel_whip_charge_bonus_matches_modular_round_modifier-0-1` … `-0-6`, en ese orden |
| `tests/engines/vectorized/test_runtime_regressions.py::test_frenzy_persists_and_pistols_only_fire_in_the_first_round` | pistola + espada | `runtime.build(main_weapon_id="weapon.pistol", off_hand_id="weapon.sword")` | `unit/vectorized/test_runtime_regressions/test_frenzy_persists_and_pistols_only_fire_in_the_first_round-0-1` |
| ídem | espada + pistola | `runtime.build(main_weapon_id="weapon.sword", off_hand_id="weapon.pistol", attacks=2)` | `...-0-2` |
| `tests/engines/vectorized/test_runtime_regressions.py::test_tentacle_chooses_one_allocation_and_spends_it_once` | enemigo resistente | `runtime.build(toughness=6, wounds=6)` | `unit/vectorized/test_runtime_regressions/test_tentacle_chooses_one_allocation_and_spends_it_once-0-1` |

**Consumo:** T06 publicó las entradas y T08 las consumió con `vector_case` y el mismo cargador `load_cases`, sustituyendo solo la preparación `compile_fighter` de esos tests concretos. No se cambiaron aserciones, dados, límites ni escenarios, y no se sustituyó ninguna variante por otra más débil. La fila `cripple` quedó bloqueada y se documenta abajo.

**Efecto de la separación sobre el corpus:** los tests trasladados a `tests/rules/` ya no consumen sus claves `unit/vectorized/...::builders` (`animal_friendship...`, `construction_contracts...`, `pirate_mercenary...`, `remaining_meta...`, `mandatory_mutations...`, `construction_contracts_validate...`, `proven_warrior...`, `scaly_skin...`, `shared_compiler_contracts...`, `arms_master...`, `restricted_weapons...`). T06 puede podarlas en una versión futura; T08 no las tocó.

#### T08 — Consumo de fixtures y pendiente cripple (2026-10-23)

**Estado:** consumo completado salvo un único caso. T06 publicó la versión ampliada del corpus con **6.385 casos** (16 nuevas: 15 de T08 y 1 de T10) y T08 adaptó con ellas todos los bloques de ejecución que aún compilaban. No se modificaron aserciones, dados, decisiones, escenarios, motor, corpus, manifiesto ni configuraciones compartidas.

**Consumo (15 entradas nuevas de T08):**

- `test_rule_families_a.py::test_anvil_head...`: anvil/death desde `-0-0`, `energy` desde `-0-1`; `mark` **reutiliza** `test_contagious_retaliates_and_mark_of_old_ones_is_spent_only_once-0-1` (`first`).
- `test_rule_families_a.py::test_disability_guardian...`: guardian/marked desde `-0-0`; el `cripple` sigue compilando (abajo).
- `test_shared_families.py::test_unarmed_fighting...`: monjes desde `-0-0`; las seis variantes desarmadas/garras desde `-0-1`…`-0-6` (Eshin Mordheim, Eshin Trollheim y Deathbringer, cada uno con puño y garras).
- `test_runtime_regressions.py::test_steel_whip...`: seis armas desde `-0-1`…`-0-6`, con el oponente plano de `-0-0`.
- `test_runtime_regressions.py::test_frenzy_persists...`: `-0-0`, la nueva `-0-2` y la clave **reutilizada** `test_pistol_and_sword_allocate_attacks_to_the_correct_weapon-0-0` (`first`).
- `test_runtime_regressions.py::test_tentacle...`: enemigo T6/W6 desde `-0-1`.

Las cifras 6.369 y el `corpus_sha256` de las comprobaciones anteriores corresponden a la versión consumida en la segunda pasada; la versión vigente es la de 6.385 casos publicada por T06. T10 tiene una entrada nueva adicional (`test_duel_replay/test_disability_initialization_marker_is_not_a_spent_resource-0-1`), que no pertenece a T08.

**Pendiente único: `cripple`**

- **Test exacto:** `tests/engines/vectorized/test_rule_families_a.py::test_disability_guardian_unarmed_and_onogal_have_observable_runtime_effects`.
- **Build original:** `compile_fighter(FighterBuild("mordheim", band_id="chaos-streets-mordheim-inhabitants", profile_id="cripples", collection="trollheim"), ROOT)`, seguido de `_new_state(cripple, 1, FixedRng(4))`.
- **Error de compilación:** `ValueError: Disability requires one permanent supplied result (condition.disability-1..6)`.
- **Entrada precompilada exacta:** no existe ni es recuperable. El único crippler congelado del corpus usa `condition.disability-6`, que no reproduce la tirada 4 esperada por el test; los artefactos disponibles solo contienen referencias de auditoría/tags, no un `CompiledFighter` con discapacidad 4.
- **Excepción aceptada:** conservar temporalmente esa única llamada a `compile_fighter` y el escenario original, sin modificar aserciones, sustituir la discapacidad por `disability-6` ni reparar el compilador. No se inventa una configuración ni se genera una entrada desde el estado posterior. El punto queda registrado en `TODO.md` para decisión de T06/coordinación y no se declara resuelto por fixtures.

### T09 — Tests del motor nativo

**Inicio:** bloque 2 cerrado: T04, T05 y T06 terminados e integrados.

**Propiedad:** `tests/engines/native/` y los originales asignados a este paquete.

**Trabajo:** usar los mismos fixtures, conservar los controles específicos de la extensión y distinguir su ausencia, incompatibilidad y ejecución real. Comprobar que las pruebas funcionales utilizan el backend nativo y no una sustitución silenciosa.

**Fin verificable:** la colección conserva identidades y expectativas; con una extensión compatible, una muestra mínima demuestra la conexión con el backend nativo sin fallback, solo si falta evidencia válida. La preparación mediante fixtures se revisa estáticamente, sin bloqueo de KB. Si la extensión no está disponible, se entrega la adaptación estructural y se declara pendiente esa comprobación, sin iniciar una reparación del entorno ni presentarla como pasada. No se exige ejecutar toda la suite nativa ni certificarla funcionalmente para cerrar la reorganización.

#### T09 — Adaptación del motor nativo entregada (2026-10-23)

**Estado:** adaptación estructural entregada, pendiente de aceptación. No se modificaron motores, corpus, manifiesto, configuraciones compartidas ni otros paquetes; no se hicieron commits ni pushes.

**Movimientos e identidades**

- `tests/python/combat/native/test_native_engine.py` → `tests/engines/native/test_native_engine.py`.
- `tests/python/combat/native/test_native_sigmarite.py` → `tests/engines/native/test_native_sigmarite.py`.
- Se conservan los **12 node IDs** de función (10 + 2), sus nombres, el marcador `phase6_native` y sus aserciones. La colección no añade, elimina ni duplica casos.

**Consumo de fixtures**

- Los seis casos unitarios de `test_native_engine.py` cargan sus claves `unit/native/test_native_engine/...-0-0`; el auto, acumulación por lotes, simetría, determinismo, paridad estadística y dos armas conservan sus simulaciones, semillas, tamaños de lote y expectativas en código.
- Las cuatro pruebas reclasificadas de `test_native_engine.py` cargan `parity/deep/{pistol-vs-parry, entangle-vs-fencer, frenzy-vs-heavy, elite-vs-durable}`; `test_native_sigmarite.py` carga `parity/deep/sigmarite-vs-undead`.
- Se eliminó `compile_fighter`, `knowledge_root`, `FighterBuild`, `Characteristics` y `DEEP_SCENARIOS` de ambos archivos. No quedan referencias a `mordheim_knowledge` ni `mordheim_construction`.
- Las cinco pruebas reclasificadas conservan la comprobación de compilación nativa mediante `compile_duel`, directa o a través de `compare_statistical_parity`; sus escenarios siguen siendo los mismos.
- Las importaciones de `compare_statistical_parity` son locales a las pruebas que las usan, de modo que la colección y las pruebas de compilación no cargan el facade de paridad.

**Controles del backend**

- `_require_native` mantiene el `pytest.skip` cuando la extensión no está compilada.
- Las pruebas funcionales llaman a `simulate_duel`/`compare_statistical_parity` con `backend="native"`; la prueba de selección automática comprueba que `available_backends()[0] == "native"` y que `auto` produce el mismo resultado que `native`. No hay fallback silencioso en las rutas funcionales.
- El test de origen del port sigue leyendo `_combat_native.pyx` y conserva sus dos aserciones sin fixtures.

**Comprobaciones realizadas**

- `python -m py_compile tests/engines/native/test_native_engine.py tests/engines/native/test_native_sigmarite.py` → OK.
- Inspección estática: sin `compile_fighter`, `FighterBuild`, `DEEP_SCENARIOS` ni `knowledge_root`; la única llamada con `backend="auto"` es la prueba que verifica la selección automática.
- `pytest tests/engines/native --collect-only -q` con bloqueo de importación de `mordheim_knowledge`, `mordheim_construction` y `mordheim_modular_e2e`, y bloqueo de apertura de `sources/knowledge/**` → **12 tests**, exit 0, 0,40 s.
- Muestra mínima con el mismo bloqueo: las dos compilaciones de `test_native_engine.py` y el test de origen de `test_native_sigmarite.py` pasan; la compilación Sigmarite falla en `require_optimized_support` porque el port nativo aún no admite variantes de modificador local. **3 pasan, 1 falla**. El fallo se atribuye al motor incompleto y no se investigó ni corrigió.
- Muestra funcional con el mismo bloqueo: `test_native_is_selected_by_auto_when_available` **pasa** (1 passed, 4,36 s), carga el fixture unitario, selecciona `native` y no accede a la KB.

**Ajuste de integración del manifiesto**

- Antes de editar se confirmó que no había otro escritor activo: sin procesos de exportación, sin `.lock`/`.tmp`/`.part` en `tests/engines/fixtures` y sin cambios del manifiesto desde la verificación anterior.
- Se actualizaron los dos consumidores a `tests/engines/native/test_native_engine.py` y `tests/engines/native/test_native_sigmarite.py`, y la referencia de la exclusión del test de origen Sigmarite a la misma ubicación.
- Se conservaron las **1.718 claves**, los **11 tests** de consumidor, los **6.369 casos**, las **566 exclusiones**, las **4 exclusiones de consumidor**, los **5 destinos rules**, **1.808** orígenes y **693** archivos KB. Las 10 claves del consumidor de motor y la clave Sigmarite existen en el corpus.
- Se conservó como procedencia histórica la entrada `origin_files` con `tests/python/combat/native/test_native_engine.py` y su huella; no se tocaron `corpus_sha256`, la revisión, los casos ni las huellas del corpus.
- Validación solo por lectura JSON: el manifiesto y el corpus cargan, `coverage` y recuentos no cambian, el manifiesto conserva `corpus_sha256 = ebed92c1638d4555e5924c56f0c92e43f21b3c8539ce8c4c887a87b455f1c40f` y el corpus mantiene su mtime. No se ejecutaron tests, motores ni benchmarks.

**Bloqueos y traspasos**

- El motor nativo sigue incompleto; no se ejecutaron las pruebas estadísticas ni se investigaron sus fallos esperados. No se presenta la suite nativa como funcionalmente verde.
- Las pruebas que usan `compare_statistical_parity` no pueden ejecutarse bajo el bloqueo estricto de importación de `mordheim_knowledge`: el facade `mordheim_combat_lab.verification.parity` importa `mordheim_knowledge.loader` sin leer datos. La muestra mínima evitó esa ruta. Actualización de alcance: el bloqueo de importación se ha retirado y no se exige desacoplar el facade; este punto deja de ser un pendiente de aceptación.

### T10 — Paridad y benchmarking con entradas precompiladas

**Inicio:** bloque 2 cerrado: T04, T05 y T06 terminados e integrados.

**Propiedad:** tests de `tests/engines/parity/` y rutas de ejecución de paridad/benchmarking asignadas en T01. Los tests del formato de informes pertenecen a T05/T12; las opciones compartidas del CLI las integra el coordinador.

**Trabajo:**

1. Separar preparación y ejecución para que comparaciones y benchmarks carguen directamente el corpus, incluidos contexto y participantes auxiliares.
2. Proporcionar las mismas entradas al modular, vectorial y nativo. Conservar las magnitudes, tolerancias y estados de resultado definidos por las herramientas actuales.
3. Mantener calentamientos, repeticiones, tamaños de lote y medición de rendimiento; adaptar también los workers y las estrategias paralelas existentes.
4. Conservar la ejecución del modular como oráculo. Las referencias guardadas son opcionales y deben identificar las entradas y parámetros a los que corresponden.
5. Escribir resultados generados en `outputs/`, conservando los contratos de informes y comparación con resultados anteriores.

**Fin verificable:** un caso pequeño por ruta modificada, con parámetros controlados y muestras mínimas, demuestra carga directa y selección del backend, incluidos los auxiliares afectados, solo si falta evidencia válida. La preparación mediante fixtures se revisa estáticamente, sin pruebas de bloqueo de KB. Estas comprobaciones prueban la conexión y no certifican equivalencia estadística ni rendimiento. Las rutas incompatibles se informan sin aprobarse mediante fallback; no se ejecutan campañas completas.

#### T10 — Paridad y benchmarks con entradas precompiladas entregados (2026-10-23)

**Estado:** entregada para revisión; no aceptada. Sin commits ni pushes. Se conservaron los cambios concurrentes de T05–T09 (parte de la separación de informes de T05 ya estaba aplicada en `test_parity.py` y `test_truncation_parity.py`).

**Base:** rama `tests-rework`, revisión `8415ba80`. Corpus congelado de T06 (`corpus_sha256 = ebed92c1638d4555e5924c56f0c92e43f21b3c8539ce8c4c887a87b455f1c40f`, 6.369 casos) cargado con `tools.verification.compiled_cases.load_cases`; no se modificaron corpus, manifiesto ni configuraciones compartidas.

**Traslados y adaptación**

- `tests/python/verification/{test_parity,test_parity_battery_cases,test_parity_battery_runner,test_truncation_parity,test_duel_replay}.py` → `tests/engines/parity/` con `git mv`.
- `tests/python/cli/{test_benchmarking,test_calibrate}.py` → `tests/engines/parity/benchmarks/`.
- `tests/engines/parity/conftest.py` nuevo: `precompiled_cases()` y fixture de sesión `cases` (mismo patrón que T07), sin compilador, KB ni motores.
- `test_parity.py`: el par `basic` y las 42 parejas del arquetipo salen de `benchmark/basic` y `parity/deep/<id>` (`first`, `second`, `limits.maximum_rounds`). Comparaciones, semillas, muestras, tolerancias y aserciones no cambian. Los dos inventarios (`verify_vectorized_parity`, `verify_specification_parity`) no ejecutan duelos y siguen siendo comprobaciones de catálogo por contrato.
- `test_truncation_parity.py`: `_pair()` lee `benchmark/<id>` del corpus; horizontes, muestras y presupuesto de rondas intactos.
- `test_duel_replay.py`: cada prueba carga su pareja y su contexto de las claves `unit/parity/test_duel_replay/...`; se conservan los guiones escalar/optimizado, las decisiones y las aserciones. Donde el corpus congeló la pareja simple, las deltas de build declaradas por la prueba (bull-charge, inspiring-sermon, disability) se reaplican con `replace` sobre el combatiente congelado; `_disabled()` reproduce exactamente las tres estructuras que producía el build con `skill_ids`/`condition_ids`. No queda ninguna compilación.
- `benchmarks/test_benchmarking.py`: la composición de la suite no cambia; la prueba de admisión por construcción pasa a comprobar que cada escenario tiene su caso precompilado (`benchmark/<id>`, `parity/deep/<id>`) con el mismo presupuesto de rondas. Los parámetros de benchmark del corpus (`simulations`, `batch_size`, `warmups`, `repeats`) se conservan sin cambios.
- `benchmarks/test_calibrate.py`: usa `_fixture_pairs(pair_set)` —filas `(first, second, maximum_rounds, id)` desde `parity/deep/<id>`— y lo inyecta con `pair_source`.
- `cli/calibration.py` (propiedad T10): `run_calibration(..., pair_source=None)` con `source = pair_source or _pairs`. Separa preparación y ejecución sin cambiar el comportamiento de la CLI (`_pairs` sigue siendo el origen por defecto).

**Conservación de entradas**

- `_fixture_pairs("mini") == calibration._pairs("mini")`: igualdad completa de `CompiledFighter`, contexto y rondas.
- Las 42 parejas `parity/deep/<id>` igualan `compile_fighter` más los tags de benchmark del escenario, con `maximum_rounds` idéntico; `benchmark/basic` = 50 y `benchmark/long` = 75.
- Las 15 claves de replay usadas igualan los builders compilados y sus contextos; los valores esperados no se tocaron.
- `fast`/`full` difieren de `_pairs` solo por los tags sintéticos de benchmark (`attack.blessed|fire|magical`) que el corpus sí conserva.

**Comprobaciones**

- `python -m py_compile` de los 8 archivos de test/ayuda y `calibration.py` → OK.
- `python -m pytest tests/engines/parity --collect-only -q` → 106 ítems (13 paridad, 11 catálogo, 21 runner, 6 truncación, 46 replay, 4 benchmarking, 5 calibración), exit 0. Mismas funciones y parametrizaciones que antes del traslado (46 replay = 15 funciones con sus parámetros).
- Muestra mínima (2 paridad, 1 truncación, 2 replay modular, 1 preflight, 4 benchmarking): 10 pasan (12,66 s); con `compile_fighter` sustituido por un stub que falla: 9 pasan (12,65 s), prueba de aislamiento sin KB.
- Ruta de calibración: una pareja `benchmark/basic` por `run_calibration` con `pair_source` → `pair_ids {native: [basic], numpy: [basic]}`, 4,43 s.
- No se ejecutaron campañas de paridad, certificaciones estadísticas, benchmarks completos ni reintentos.

**Fallos ajenos (no investigados ni corregidos)**

- `benchmarks/test_calibrate.py`: 5 errores de setup. El backend numpy falla en 5 de las 10 parejas `mini` también con las entradas previas de `calibration._pairs`: `regen-vs-fire` → `ValueError: Leadership test requires explicit non-negative integer Leadership`; `sigmarite-vs-undead`, `natural-armour-vs-magic` y `paired-poison-vs-undead` → «Local modifier variants…»; `random-characteristics-vs-stable` → «Residual modular effects…». Es una limitación vectorial, independiente de la carga por fixtures.
- `test_parity_battery_cases.py`: 2 fallos de expectativas de datos ya desactualizadas (`trait.natural-armour-save` frente a `band--beastmen-special-skills-shaggy-hide`; `defence.buckler` ausente en `c06-reroll-capacity`). El archivo solo se trasladó.

**Bloqueos y peticiones al coordinador (no se editaron)**

- `tools/mordheim-utils.py` `SCOPE_PATHS`: `deterministic` cita `tests/python/verification/test_duel_replay.py` y `test_parity.py`, y `verification` cita `tests/python/verification`; ambas rutas quedan vacías tras el traslado. Ajuste requerido hacia `tests/engines/parity`.
- `verification/coverage_gate.py` y `verification/engine_mutation.py` (T05) siguen refiriendo los archivos en `tests/python/verification`.
- `docs/reference/verification.md` y `docs/guides/implement-and-verify-rules.md` citan las rutas antiguas.
- `compiled-cases.manifest.json` (T06) conserva `consumer: tests/python/verification/test_parity.py|test_duel_replay.py`; el corpus mantiene `origin.node_id` histórico, que es lo que T11 compara. No se tocaron fixtures.
- Carencia de corpus (a decidir por T06): las parejas de replay congelan el par simple; las variantes bull-charge/inspiring-sermon/disability se reconstruyen en la prueba. Una variante congelada eliminaría la reconstrucción.

**Cierre de T10:** las siete rutas asignadas viven en `tests/engines/parity` y cargan el corpus congelado; comparaciones, benchmarks y replay no leen la KB ni compilan combatientes, y la muestra mínima por ruta modificada pasa con `compile_fighter` bloqueado. La calibración conserva la preparación por defecto en la CLI y la sustituye por fixtures en la prueba. Los fallos vectoriales y de datos se declaran como ajenos, sin aprobarlos ni ampliar el alcance.

## Detalle de tareas — Integración y depuración

### T11 — Consolidar selección, comandos y conservación

**Inicio:** T04, T05 y T07–T10 cerrados; sus ajustes globales ya se han integrado con cada traslado.

**Responsable y propiedad:** coordinador; archivos comunes, configuración de runners, CI, cobertura y documentación.

**Trabajo:** reconciliar los scopes y fases con la nueva estructura, mantener los comandos existentes y comprobar los globs de pytest, Vitest y Node. Actualizar referencias de evidencia y herramientas auxiliares. Conciliar la selección final con T00 mediante el mapa T01, incluyendo los corpus originales y los casos precompilados derivados. Agrupar la colección/listado integrado y el typecheck por workspace afectado una única vez, reutilizando evidencia válida y sin lanzar suites funcionales completas.

**Fin verificable:** cada caso previsto tiene destino y runner; no hay pérdidas accidentales, inclusiones dobles, imports rotos ni referencias activas a rutas retiradas. Los gates de cobertura siguen seleccionando sus detectores y no han reducido sus garantías.

**Límite:** el cambio de ruta de un node ID se registra como movimiento, no como eliminación y creación sin relación. Los recuentos no sustituyen la correspondencia entre identidades.

#### T11 — Reconciliación integrada (2026-10-23)

**Estado:** reconciliación aplicada sobre el árbol actual. Esta pasada no ejecutó colección, tests, typechecks, compiladores, motores ni benchmarks; solo comprobaciones estáticas de rutas, YAML y lectura JSON. T13 permanece abierta con la evidencia integrada mínima de su apartado.

**Selección, scopes y presupuesto**

- `tools/mordheim-utils.py`: los 13 `SCOPE_PATHS` (`all`, `engines`, `modular`, `vectorized`, `native`, `e2e`, `deterministic`, `knowledge`, `verification`, `construction`, `ui`, `cli`, `architecture`) apuntan a `tests/engines/{modular,vectorized,native,shared,...}`, `tests/engines/parity/**`, `tests/rules/**`, `tests/applications/combat_lab/ui` y `tests/tooling/**`. Sus 29 referencias (25 rutas únicas) existen en disco; `deterministic` incluye las cuatro rutas de `engines/shared` y las dos de `engines/parity`.
- `verification/coverage_gate.py`: `DEFAULT_SUITES` conserva sus 8 rutas (`engines/modular`, `engines/vectorized`, cuatro de `engines/shared`, dos de `engines/parity`), todas existentes. El presupuesto sigue en `tests/tooling/verification/fixtures/coverage/budget.json` con su destino actual: solo su lista `suites` se remapeó a esas 8 rutas; esquema, áreas por módulo y líneas presupuestadas no cambian.
- CI: la red Python (`campaign_file`, `tooling/architecture`, `rules/knowledge`, `test_shared_eligibility`), la batería E2E, el paso propio de no regresión, el typecheck de packages y los dos pasos Vitest (`tests/applications/warband_manager/features/campaign/**` y boundaries) referencian rutas existentes. `pyproject.toml` mantiene `testpaths = ["tests"]`.
- **Referencia histórica conservada:** `docs/reference/test-sequence.md` líneas 275 y 277 nombran `tests/python/combat/vectorized` y `tests/python/combat/native` dentro de «Verification performed on 2026-10-21». Son ubicaciones de aquella ejecución, no referencias operativas pendientes; no deben remapearse.

**Manifiesto**

- De los 80 consumidores, 78 son rutas de archivo y se remapearon a `tests/engines/**` (todas existen); los 2 restantes son los escenarios de `mordheim_combat_lab.cli.scenarios` y no cambian. Las 4 exclusiones de consumidor también se remapearon. `rules_destinations` pasó de 5 a 14 entradas con destino y nombres de test reales, y sus 14 destinos existen en disco.
- Claves: 1.718 → **1.734** (15 de T08 y la variante modular disability-3 de T10), sin duplicar ninguna existente. Se conservaron los 6.385 casos, `corpus_sha256 = ddf4a7d533b1407f55a6585c26f675db071151060de41c86d28f57a629f348ad`, la revisión, `coverage`, los 1.811 `origin_files`, los 693 `kb_files` y las 566 exclusiones; las rutas y huellas históricas de procedencia no se reescribieron.
- Validación solo por lectura JSON: el manifiesto carga, todas las rutas de consumidor existen, las 1.734 claves resuelven en el corpus y no hay claves duplicadas dentro de un consumidor.
- El cierre de T07 (520 entradas de builds, tres de ellas nuevas) no altera esta reconciliación: el documento de builds no forma parte del manifiesto ni del corpus de casos y no exige remapeo de consumidores, destinos ni presupuesto.

**C7 de CI**

- La batería «Run the modular engine E2E battery» ejecuta `tests/rules/integration/e2e -q --ignore=tests/rules/integration/e2e/test_non_regression.py`; el paso «Check accepted E2E coverage has not regressed» conserva `python -m pytest tests/rules/integration/e2e/test_non_regression.py -q`. El YAML parsea y solo cambió esa opción.

**Límites de esta pasada**

- No se repitió la colección ni el typecheck integrado: los agrupa el coordinador en T13. Los recuentos de T09 (1.718 claves, 5 destinos, 1.808 orígenes) y la base de T10 (6.369 casos, `corpus_sha256 = ebed92c1…`) quedan como evidencia histórica de su revisión, sustituida por los valores vigentes anteriores.

### T12 — Consolidar tests y eliminar redundancia demostrada

**Inicio:** T11 cerrado; existe una selección integrada comparable con la inicial.

**Propiedad:** los responsables de cada componente, con reparto disjunto; coordinador para cambios entre componentes, CI y evidencia común.

**Trabajo:**

1. Revisar cada candidato registrado: contrato, entradas, límites, implementación ejercitada y fallo detectado. Los cinco pares con cuerpo idéntico no se consideran duplicados por ese único motivo.
2. Fusionar o parametrizar solo cuando se conserve la capacidad de detectar fallos. Identificar el sustituto de cada comprobación retirada.
3. Probar formatos de informes con resultados controlados, conservando comprobaciones específicas de conexión real con los motores.
4. Mantener el control de no regresión E2E como paso propio de CI y excluir ese archivo de la batería inmediatamente anterior para evitar su doble ejecución.
5. Justificar las sustituciones mediante contratos y detectores existentes, conservando los presupuestos versionados. No crear nuevos tests ni abrir campañas generales de mutaciones, cobertura o rendimiento; no usar resultados anteriores a la reforma para decidir retiradas.

**Fin verificable:** cada retirada o fusión tiene justificación y sustitución trazable; se cuantifican casos conservados, movidos, fusionados y retirados sin contabilizar un simple traslado como reducción. Se integra la selección y se ejecutan solo los casos necesarios para verificar la sustitución, sin repetir baterías completas.

**Límite:** no rebajar presupuestos ni retirar pruebas de implementaciones distintas por parecido superficial. Los fallos actuales no son un criterio para conservar, retirar o corregir tests.

#### T12 — Cierre documental (2026-10-23)

**Estado:** cierre documental de los candidatos C1–C12. No se ejecutaron nuevas consolidaciones, retiradas, campañas de cobertura ni mediciones; no se modificaron tests, presupuestos ni configuración. T12 no se presenta como certificación funcional.

- **C1–C5 — conservados.** Los cinco cuerpos siguen siendo idénticos, pero ejercitan implementaciones distintas (`mordheim_modular_e2e.dice` frente a `mordheim_combat_lab.verification.dice`). No hay sustituto que preserve ambos detectores, así que no se retira ninguno.
- **C6 — conservado.** `mordheim_knowledge.i18n` y `mordheim_combat_lab.ui.i18n` son implementaciones distintas; el contrato de cada locale no se sustituye por parecido de cuerpo.
- **C7 — aplicado en CI.** La batería E2E excluye `test_non_regression.py` y el archivo conserva su paso propio, con lo que desaparece la doble ejecución sin retirar el control.
- **C8 — conservado.** `test_profile_save_thresholds.py` mantiene sus dos capas: 20 contratos de umbrales compilados en `rules/construction` y 18 pruebas de ataque real con entradas congeladas en `engines/modular`. No se fusionan por nombre ni se debilita ninguna.
- **C9–C12 — conservados sin consolidación.** Formatos de informe, truncación/paridad pooled, casos E2E frente a semánticos y cotejo de hirelings frente a admisión siguen detectando fallos distintos o carecen de identidad de caso común; no se identificó sustituto trazable y no se abrió ninguna campaña de resultados controlados.
- **Presupuestos:** ninguna consolidación reduce el presupuesto versionado de cobertura. El único cambio en `budget.json` es el remapeo de su lista `suites` a las 8 rutas actuales (T11); áreas, esquema y líneas presupuestadas siguen intactos y los gates siguen seleccionando sus detectores.

**Excepciones explícitas de compilación real**

- Rechazos deliberados del compilador mezclados con ejecución, conservados intactos porque sustituir el callable convertiría la negativa en un error de snapshot ausente: `test_knight_of_purity_autopass_requires_a_supplied_hero_promotion` (psicología), `test_magic_acorn_is_hero_only_and_does_not_replace_later_round_misses` (defensa), `test_khemrian_seduction_reaches_the_legal_selected_recipient_and_round` (familia de control) y `test_shadow_dances_require_a_promoted_minstrel_and_cannot_be_declined_when_available` (modificadores locales).
- **Cripple (T08):** `test_disability_guardian_unarmed_and_onogal_have_observable_runtime_effects` conserva `compile_fighter` porque no existe ni es recuperable una entrada con `condition.disability-4`; excepción aceptada y registrada.

**Reconexión modular: estado real del árbol**

- `test_psychology_identity.py`: 11 de 20 tests llevan `_frozen_compiles`. El test de warband-type de Vengeful Hatred **queda conectado**: el documento de builds regenerado (18:08, 520 entradas) ya contiene sus cuatro requests — incluidos los tres antes ausentes `67c6a4fd…`, `ec912885…` y `a6199ab7…` — y el cargador resuelve el portador, los cuatro `zombie-3` y el control negativo de night goblins. Solo el mixto de Knight of Purity sigue con compilador real.
- `test_defence_parries_and_ward.py`: 15 de 92 tests conectados; solo el mixto de Magic Acorn conserva compilación real.
- Resto de `engines/modular`: el patrón dominante es `compile_fighter = None` con `_frozen_compiles` autouse o marcas locales; `test_leadership_support.py` ya recibe `compiled_builds.fighter` como argumento. No se detectan otras llamadas reales al compilador salvo las excepciones listadas.
- Fuera de modular, el único uso real es el `cripple` de `tests/engines/vectorized/test_rule_families_a.py`, ya declarado.

**Evidencia histórica, no vigente**

- Los recuentos de T09 (1.718 claves, 5 destinos rules, 1.808 orígenes, 6.369 casos, `corpus_sha256 = ebed92c1…`) y la base de T10 describen su revisión, no el estado actual. El manifiesto vigente tiene 1.734 claves, 14 destinos, 1.811 orígenes y 6.385 casos con `ddf4a7d5…`; ambas cifras se conservan como registro y no se recalculan.

## Detalle de tareas — Aceptación final

### T13 — Validar el conjunto y cerrar la reforma

**Inicio:** T12 cerrado, archivos integrados y fixtures congelados. No hay escritores activos sobre los componentes que se validan.

**Responsable:** coordinador. Puede repartir comprobaciones independientes sobre la misma revisión, con salidas separadas y sin regeneraciones compartidas.

**Trabajo:**

1. Revisar la reconciliación de T11 y confirmar selección, fases, comandos y descubrimiento sin duplicados. No repetir colección ni typecheck sin un cambio relevante posterior.
2. Reutilizar la evidencia válida de colección y conexión con fixtures, incluidos los workers afectados. Revisar estáticamente la preparación precompilada y completar solo conexiones pendientes. No implementar ni ejecutar comprobaciones de ausencia de acceso a KB, bloqueos, instrumentación ni intentos deliberados de acceso.
3. Confirmar por inventario, referencias y expectativas que rules y los E2E originales conservan su integración y evidencia aceptada, sin ejecutar sus baterías completas.
4. Reutilizar las comprobaciones puntuales de aplicaciones, tooling, codec, exportación y conexiones de paridad/benchmarking. Ejecutar solo las pendientes o invalidadas; declarar la comprobación nativa no realizada si la extensión no está disponible.
5. Confirmar conservación de contratos, presupuestos y expectativas sin medir cobertura ni iniciar campañas de mutaciones, estadística o rendimiento. No comparar con resultados de ejecución previos ni exigir éxito funcional global.
6. Recoger en este documento el resultado global, las comprobaciones realizadas y los límites. Registrar defectos pendientes en `TODO.md`.

**Fin verificable:** se satisfacen los criterios estructurales y de conexión de `REWORK_PLAN.md` con la evidencia mínima indicada, cada cambio está explicado y las limitaciones se declaran. Los fallos funcionales ajenos no bloquean este cierre; ninguna comprobación no realizada se presenta como pasada. No se exige una batería funcional global ni se declara certificación completa de los motores.

**Comprobaciones integradas ejecutadas (2026-10-23)**

Revisión `8415ba80`, rama `tests-rework`, árbol con 2.469 entradas de cambios concurrentes que esta pasada no modificó.

- **Colección:** `python -m pytest --collect-only -q` desde la raíz. Dos pasadas idénticas: **13.148 tests recogidos**, `EXIT 0`, 0 errores de colección (53,89 s en frío, 18,94 s en caliente). Sin duplicados: 13.148 node ids, 13.148 únicos. Sin referencias activas a `tests/python`. Reparto: `tests/rules` 11.296, `tests/engines` 1.618, `tests/applications` 127, `tests/tooling` 107. Los 5 ítems de `test_non_regression.py` aparecen en la colección global, pero la batería de CI los excluye y su paso propio los ejecuta una sola vez (C7).
- **Typecheck:** `npm run typecheck` (encadena `npm run typecheck --workspaces`) → `EXIT 0`, sin diagnósticos. Cubre `campaign-web-core` y `warband-manager-web`, ambos con `tsc --noEmit`.

**Límites:** no se ejecutaron tests funcionales, Vitest, motores, benchmarks, generadores ni compilación de perfiles. Las baterías funcionales las ejecuta el usuario; no se reciben aquí sus resultados ni se presentan como pasados. No se modificó código, tests, configuración, snapshots ni artefactos generados; las salidas se conservaron fuera del repositorio y no se crearon informes adicionales.

Las referencias de `docs/reference/test-sequence.md` (líneas 275 y 277) pertenecen a la evidencia histórica del 2026-10-21 y se conservan. No constituyen un pendiente de T13.

Evidencia reutilizable ya obtenida: lectura JSON del manifiesto, del corpus y del documento de builds, existencia de las rutas de scopes/suites/CI, parseo del YAML de CI, `py_compile` de los dos archivos reconectados y consultas al cargador de builds: las 34 configuraciones de la pasada anterior más las 6 del test de warband-type sobre el documento regenerado, todas resueltas. Las tres entradas antes ausentes ya no son un pendiente. Las excepciones de compilación real y el `cripple` son decisiones registradas, no comprobaciones pendientes. La comprobación nativa sigue sin realizarse si la extensión no está disponible, y los fallos funcionales ajenos de vectorial/paridad no son criterio de cierre.

#### T13 — Correcciones de la ejecución manual integrada (2026-10-23)

**Estado:** incidencias de migración de la salida manual corregidas. La ejecución aportada por el usuario terminó con 1.360 pasan, 13 fallan y 11 errores. No se repitió la batería completa; se reutilizó esa evidencia y se ejecutaron únicamente los casos afectados.

- **Orden de fixtures:** `test_shifty_activation.py::opponent`, de alcance módulo, consultaba el global `compile_fighter = None` antes de la inyección de alcance función. Ahora recibe `compiled_builds` y usa directamente su callable, conservando el build y su alcance. Se corrigieron los 11 errores de preparación.
- **Raíces tras el traslado:** `test_control_family.py`, `test_dark_jester_and_related_families.py` y `test_patrons_and_supplied_states.py` conservaban `parents[4]` y apuntaban fuera del repositorio. Se ajustó únicamente la raíz a `parents[3]`, sin modificar datos o expectativas.
- **Entrada compartida por backend:** `test_duel_context.py::test_real_pool_preserves_context` carga explícitamente el caso `-0-0` para NumPy/nativo. La construcción original y su bonus de carga son idénticos para ambos; no se añadió fallback al cargador ni se alteró el corpus.
- **Snapshots ausentes:** se incorporaron nueve requests exactos (siete observados y dos controles posteriores de los mismos consumidores), conservando las 520 entradas anteriores sin cambios. Documento vigente: **529 entradas**, SHA-256 de archivo `4336e758bea6d7fb223674d0debac3f1d874d0b5736f919fc3bc7e74fd0f4ccf`. Las dos incorporaciones adicionales cubren trained-bear con exención suministrada de estupidez y el control witch-hunters de Fanatical. No se modificaron generador, manifiesto ni corpus de casos.
- **Roles en entradas antiguas:** Mourngul tenía intercambiados los casos de hellblade mágico y maza; engagement tenía invertidos el llano y el sabretusk respecto al original. Se corrigieron solo los bindings y su comentario. Igualdad completa comprobada frente a las construcciones originales; sin cambios en motores, dados ni aserciones.

**Evidencia puntual final reutilizada:**

1. Agente de fixtures/rutas: selección serial de los dos tests parametrizados de shifty (11 ítems), las tres comprobaciones de rutas y `test_real_pool_preserves_context` (dos backends): **16 pasan, 9,67 s**.
2. Coordinador: `python -u -m pytest tests/engines/modular/test_dreamwalkers_undead_foes_fear.py::test_a_vampire_charger_takes_no_fear_roll_either tests/engines/modular/test_defence_parries_and_ward.py::test_fen_guard_bark_skin_cutting_edge_is_exempt_from_the_strength_cap tests/engines/modular/test_local_modifier_variants.py::test_stupidity_completion_supplied_exemption_skips_unknown_leadership_and_clears_history tests/engines/modular/test_patrons_and_supplied_states.py::test_the_slaanesh_patron_penalty_lands_on_the_engaged_enemy tests/engines/modular/test_local_modifier_variants.py::test_fey_quickness_is_acquired_and_combines_with_step_aside tests/engines/modular/test_enemy_identity_hatred.py::test_fanatical_reaches_the_attack_tape_only_for_a_listed_warband -n 2 --dist=load -q --durations=5 --tb=short`: **7 pasan, 6,12 s, exit 0**.
3. Agente de bindings: Mourngul pasa; engagement pasa tras su corrección. Solo se repitió engagement al corregirlo: **los dos casos finales pasan**.

En total, **25 ítems distintos afectados pasan** (incluye el control NumPy del caso compartido que ya pasaba). Se conserva la evidencia de colección y typecheck: estos arreglos no añaden ni retiran tests, parametrizaciones o categorías ni cambian archivos TypeScript. Los imports y fixtures afectados se comprobaron en las ejecuciones puntuales. No se declara una nueva batería global verde. Rama `tests-rework`, base `8415ba80`, sobre el árbol de trabajo con cambios previos conservados; sin commits ni pushes.

**Cierre:** T13 completada para la reorganización y reconexión, con las excepciones registradas. No incluye certificación funcional global ni cambios de reglas o implementación de motores.
