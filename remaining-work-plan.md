# Remaining work plan — migración web

Fecha: 2026-09-09 · Rama: `web-repo-rework` · Último checkpoint: `1c047d8`

Este documento describe el trabajo pendiente tras completar todas las tareas
P3–P9 de [`web-migration-parallel-plan.md`](web-migration-parallel-plan.md),
comparado contra el plan maestro [`web-migration-plan.md`](web-migration-plan.md)
(secciones 5, 9, 12 y 14).

---

## 1. Estado actual

Completado y verificado (Python 4.704 passed salvo 2 fallos preexistentes;
packages TS 147/147; app 45/45; build OK):

- Fases 0–2: preparación, contrato `.mordheim` v4, dominio Python extraído.
- Fases 3–8: workspace TS, KB web, vertical slice, 8 bloques funcionales,
  calidad (round-trip matrix, corpus corrupto, guardarraíles, accesibilidad,
  presupuesto KB), workflows de CI/Pages.
- Fase 9: renombrado lógico de namespaces (P9.1–P9.4), fachada
  `application/state.py` retirada.

Pendiente en el árbol (sin commit, ~34 archivos): P9.3 (renombrado
`campaign-web-core`), P9.4 (retirada de fachada) y P5.2-final de Agent A
(swap a KB real). **Commit checkpoint requerido antes de cualquier otra
tarea.**

---

## 2. Trabajo restante

### R1 — Commit y PR (bloqueante, integrador)

- Commit de los ~34 archivos pendientes con staging selectivo (ownership
  mixto en el árbol; ver log de coordinación).
- Push de `web-repo-rework` y PR hacia `main`.

### R2 — Activación de GitHub Pages (bloqueante, integrador)

Único criterio de finalización (§14) sin cumplir: "el sitio se publique
correctamente en GitHub Pages".

1. Settings → Pages → Source: **GitHub Actions**.
2. Merge a `main` (los workflows de P8.1 disparan validación y deploy).
3. Verificar primer despliegue en `https://adrian-antonio-del-campo-morales.github.io/Mordheim-Utils/`.

Documentado en `docs/decisions/web-deployment.md`.

### R3 — Reestructuración física del monorepo (plan maestro §5)

La estructura física objetivo **no se ha ejecutado**. Estado actual vs
objetivo:

| Objetivo (§5) | Estado actual | Acción |
| --- | --- | --- |
| `apps/combat-lab/` | no existe | mover/componer desde `mordheim_combat_lab` |
| `apps/warband-manager-desktop/` | ✅ `mordheim_desktop` (composition root extraído de `mordheim_campaign`; consola `mordheim-campaign-manager` apunta a él) | — |
| `apps/warband-manager-web/` | ✅ | — |
| `packages/python/{core,knowledge,roster-construction,combat-engine,campaign}/` | 7 paquetes en `src/mordheim_*` | reubicar |
| `packages/python/adapters/desktop-ui/` | no existe | extraer adaptadores de UI |
| `packages/typescript/...` | ✅ (decisión: `ui/web` se queda en `apps/.../src/features/` — componentes acoplados a la app; packages/typescript se mantiene libre de framework) | decidido |
| `contracts/knowledge/` | no existe | **no aplica** (decisión S8: el artefacto KB es un artefacto generado, su única fuente de verdad es el generador; un esquema manual solo divergiría) |
| resto (`sources/`, `tests/`, `tools/`, `docs/`) | ✅ conforme | — |

Impacto estimado de mover los 7 paquetes de `src/`:

- `pyproject.toml`: `package-dir`, `packages.find`, posiblemente
  `[tool.setuptools]` por paquete.
- ~61 import sites (`from mordheim_campaign ...` en `src/`, `tests/`,
  `tools/`) si cambian los nombres importables; **cero** si solo se mueven
  directorios manteniendo namespaces (opción soportada por §5).
- CI (P8.1) y cualquier ruta de build/empaquetado (PyInstaller en `dev`
  extras).
- `tests/` completos como red de regresión.

Recomendación de ejecución: en sub-tareas independientes, una por paquete,
manteniendo namespaces importables en el primer paso (solo movimiento
físico + `pyproject.toml`), y renombrado importable después si se quiere.

### R4 — Mejoras opcionales (no bloqueantes, plan §9)

- Drag-and-drop para importar `.mordheim` (§9 lo marca como "mejora
  posterior").
- Aviso `beforeunload` al cerrar/recargar con cambios sin exportar (§9:
  "cuando sea posible"; la confirmación antes de reemplazar ya existe).

---

## 3. Orden recomendado

1. R1 (commit) — bloquea todo lo demás.
2. R2 (Pages) — cierra el último criterio de §14 con el código actual.
3. R3 (reestructuración física) — trabajo nuevo, requiere plan de sub-tareas
   y window sin otros cambios en `src/`.
4. R4 (opcionales) — cualquier momento tras R2.

## 4. Fuera de alcance confirmado

- Combat Lab (funcional), NumPy/Cython, persistencia web (localStorage/
  IndexedDB), motores de combate en el bundle — exclusiones permanentes del
  plan §2/§3, ya garantizadas por P7.3.
