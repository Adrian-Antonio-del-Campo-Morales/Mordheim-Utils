# Web Test Migration Plan — desktop regression net → web

Objetivo: llevar la red de regresión del desktop (`tests/campaign/` ~296 tests, `tests/ui/`) a la versión web, con equivalencia de comportamiento y trazabilidad uno-a-varios. No traducción mecánica de nombres.

## Alcance

Migrar todo test aplicable al Warband Manager:

- `tests/campaign/` (25 archivos, ~296 funciones de test).
- Parte de campaña de `tests/knowledge/`.
- Tests de contrato, persistencia e interoperabilidad.
- Tests UI de campaña y comportamiento equivalente en navegador.
- Tests de accesibilidad, responsive, import/export, cambios sin guardar.

Exclusiones (con motivo documentado en la matriz):

- Combat Lab, `mordheim_combat`, NumPy, Cython, paridad/cobertura del motor.
- Tests CLI de Combat Lab, simulación del motor.
- Preferencias, workbooks y controles exclusivos de Tkinter.
- PDF (sin equivalente web; `X` documentado).

## Matriz de trazabilidad

Cada test desktop se clasifica:

| Marca | Significado |
|---|---|
| `M` | migra a test de dominio TypeScript |
| `A` | adapta a test de aplicación web |
| `U` | test de UI React |
| `I` | test de interoperabilidad Python↔TS |
| `S` | comportamiento compartido KB/contrato |
| `X` | excluido, con motivo |

Criterio: equivalencia de comportamiento. Varios tests desktop redundantes pueden consolidarse en un escenario web; la matriz mantiene la trazabilidad `desktop-test-id → web-test-id(s)`.

## Reparto paralelo (3 agentes)

### REPO REWORK 222222 — inventario y paridad compartida

Ownership: matriz completa de trazabilidad, clasificación de `tests/campaign|knowledge|contracts`, harness común de paridad, vectores compartidos de comportamiento, fixtures, gate de completitud de matriz.

Entregables:

```text
tests/web/parity/
  campaign-test-manifest.json
  manifest.test.ts
  python_manifest_test.py
  fixtures/
```

Vectores compartidos grandes, si hacen falta: `contracts/campaign-test-vectors/` (README + draft + timeline + battle-post-battle + inventory-economy + exploration + progression). Vectores = inputs y observables; nunca reglas ni implementación Python.

### REPO REWORK 333333 — dominio y aplicación TypeScript

Ownership: `packages/typescript/domain/campaign/`, `packages/typescript/application/campaign/`, tests Node/Vitest de casos de uso.

Bloques: (1) draft/composición inicial; (2) timeline/selección/historial; (3) persistencia/round-trip; (4) undo/recuperación; (5) equipo/stash/asignaciones; (6) batallas/disponibilidad; (7) post-battle; (8) injuries/recuperación; (9) experiencia/avances; (10) hirelings/exploración/búsquedas/comercio; (11) economía/precios/restricciones; (12) estados incompletos/errores/operaciones rechazadas.

### REPO REWORK 2 (este hilo) — UI web y adaptaciones de navegador

Ownership: `apps/warband-manager-web/src/**/*.test.{ts,tsx}`, utilidades de test web, tests de interacción/accesibilidad/responsive.

Bloques:

1. Importar y exportar `.mordheim` (selector de fichero, confirm-replace, error surfaces).
2. Indicador de cambios sin guardar y avisos de navegación.
3. Timeline UI: enumeración de momentos, selección, navegación.
4. Draft UI: composición inicial, límites de construcción, validación visible.
5. Inventario/economía UI: asignar, comprar, vender, stash.
6. Batalla/post-battle UI: registro, heridas, XP, pasos.
7. Hirelings/exploración/búsqueda UI.
8. Undo UI en cada operación con deshacer.
9. Accesibilidad y pantallas pequeñas (extiende P7.4).
10. Exportaciones (texto/tablas) con snapshot de salida.

## Estrategia de tests (obligatoria, vigente)

Estrategia escalonada de R3 — 3 agentes comparten árbol, nunca red completa concurrente:

- **T0** (segundos): `--collect-only` + import checks.
- **T1**: solo tests que referencian ficheros editados.
- **T2**: una suite afectada.
- **T3**: red completa, un agente a la vez, ventana reclamada en el log.

Artefactos transitorios (`.coverage`, `*.c`) se borran, nunca se commitean.

## Definition of Done

- Cada test desktop aplicable tiene fila en matriz con destino y estado.
- Tests dominio TS ejecutan vectores compartidos.
- `.mordheim` v4 conserva semántica en ambas direcciones.
- KB usa IDs y fuente canónica.
- Sin `skip` para ocultar gaps.
- Tests web existentes siguen verdes; desktop aplicable sigue verde.
- CI valida matriz, paridad, typecheck, build.
- Diferencias legítimas de plataforma (Tkinter, PDF) documentadas como `X`.

## Orden de integración

1. Crear plan y log. 2. Reclamar ownership. 3. Baseline T0. 4. Matriz de trazabilidad. 5. Harness y vectores. 6. Tests dominio/aplicación. 7. Tests UI. 8. Gaps funcionales. 9. Gates de paridad. 10. T3 único. 11. Informe final + `remaining-work-plan.md`.

Sin commits ni cambios fuera del ownership asignado. Coordinación: `docs/decisions/web-test-migration-log.md`.
