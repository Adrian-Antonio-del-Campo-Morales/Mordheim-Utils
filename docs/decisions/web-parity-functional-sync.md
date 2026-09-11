# Functional parity UI sync

Temporary work split for the 33 `partial` desktop-UI rows in
`tests/web/parity/campaign-test-manifest.json`. This is not a permanent
ownership model. Each worker still reserves exact paths in
`web-migration-coordination.md` before editing.

## Shared rules

- Do not port Tk widgets literally; test the equivalent browser-visible
  guarantee.
- Change a manifest row from `partial` only after its focused web test passes.
- Do not touch the hired-sword kernel/workflow lane reserved by `local`.
- Do not edit the manifest generator during a UI unit; record the completed
  desktop test ids for the traceability owner instead.

## Current split

| Lane | Desktop intent | Suggested web seam | Reserved by |
|---|---|---|---|
| A | Sesiones, carga/reapertura, exportación, dirty guard, renombrado, borrador de batalla, seguimiento de parciales y lote final de trazabilidad | `ProductApp`, `features/campaign/**`, `features/battle/**`, manifest solo al cerrar unidades |  |
| B | Validación de formularios numéricos y correcciones manuales | `features/economy/ManualCorrectionsPanel.test.tsx` y producción solo si la prueba demuestra un fallo real | second agent |

## Unit handoff

For each unit, add a `ready` row to `web-migration-coordination.md` with:

1. desktop test ids covered;
2. browser guarantee tested;
3. exact paths modified;
4. focused test command and result;
5. any remaining Tk-only detail that stays `partial`.

The traceability owner batches manifest changes only after the cited tests are
green, so concurrent UI work does not collide in the generated file.
