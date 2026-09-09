# Decision: web namespace inventory & final-name proposal (P9.1)

Task: [`web-migration-parallel-plan.md`](../../web-migration-parallel-plan.md) §10, **P9.1** (serial).
Status: **proposal for integrator review** — no code renamed. P9.2/P9.3
start only after sign-off here.

Principle (plan §10): names by **responsibility**, not by repeating the
product name. A name that already states its responsibility is *final*; a
name that only restates "mordheim" is *provisional*.

---

## 1. Inventory

### Python (desktop)

| Element | Current | Import sites | Verdict |
| --- | --- | --- | --- |
| Package | `mordheim_campaign` (src layout) | 61 files (`src/`, `tests/`, `tools/`) | **Final** — consistent with sibling product packages (`mordheim_combat`, `mordheim_knowledge`, `mordheim_ui`, …); states its responsibility (the campaign manager) |
| Entry point | `mordheim-campaign-manager = mordheim_campaign.app:main` | `pyproject.toml` | **Final** |
| Dist name | `mordheim-utils` | `pyproject.toml` | **Final** (whole-product distribution) |
| Internal layers | `application/`, `domain/`, `persistence/`, `ui/` | — | **Final** (responsibility-named since Phase 2) |

Provisional imports found: **none**. Every import is product-consistent and
responsibility-named.

**One compatibility facade remains** (relevant for P9.4):
`mordheim_campaign/application/state.py` — a Phase 2 shim re-exporting
`domain.models` unchanged. Internal consumers still importing it:
`application/post_battle_engine.py`, `persistence/campaigns.py`,
`persistence/warband_pdf.py`, `ui/equipment_display.py`,
`ui/panels/timeline.py` (~5 files).

### TypeScript (web)

| Element | Current | Sites | Verdict |
| --- | --- | --- | --- |
| Workspace package name | `mordheim-web-packages` | `packages/typescript/package.json` | **Provisional** — restates the product, says nothing about responsibility |
| App package | `warband-manager-web` | `apps/warband-manager-web/package.json` | **Final** — names the responsibility (the web warband manager) |
| Path aliases | `@domain/`, `@app/`, `@adapters/` | 16 app files + tsconfig/vite | **Final** — purely responsibility-named; deliberately *not* `@mordheim/*` |
| Domain namespace | `domain/campaign/` (`kernel/`, helpers) | — | **Final** |
| Application namespace | `application/campaign/` + `features/{advances,battle,draft,equipment,hirelings,injuries,review}` | — | **Final** |
| Adapters | `adapters/campaign-file`, `adapters/knowledge-reader` | — | **Final** — named by the port they implement |
| App feature dirs | `src/features/*` mirroring the above | — | **Final** (mirror convention documented in P6.1–P6.8) |

The only *provisional* name in the tree is `mordheim-web-packages`.

## 2. Proposal

| Task | Action | Impact |
| --- | --- | --- |
| **P9.2** (Python rename) | **No-op.** Nothing provisional to rename; keeping `mordheim_campaign` avoids a 61-site churn with zero user-visible gain | none |
| **P9.3** (TS rename) | Rename the workspace package `mordheim-web-packages` → **`campaign-web-core`** (responsibility: the shared core the web app consumes). `package.json` name + the two doc references only. Import paths do **not** change: consumers use the `@domain/@app/@adapters` aliases and relative imports, never the package name | 1 `package.json` field, ≤2 docs |
| **P9.4** (facades) | Retire `application/state.py`: mechanically move its ~5 internal consumers to `from mordheim_campaign.domain.models import …`, delete the shim, run the campaign suite. Only after the compatibility period the integrator defines (recommended: together with the P9.3 rename, same release) | ~5 files' import lines + 1 deletion |

## 3. Decision points for the integrator

1. Approve `campaign-web-core` (or pick another responsibility-named
   alternative, e.g. `warband-core`) — one-line rename in P9.3.
2. Confirm **no Python rename** (recommended): renames `mordheim_campaign`
   only if a future external consumer demands it.
3. Confirm the alias set `@domain/@app/@adapters` as the public import
   surface of the app (already true; would formalize it).

## 4. Verification after P9.3/P9.4 (when executed)

- P9.3: `packages/typescript/package.json` name updated; `npm test` and
  `npm run typecheck` unchanged (name is not an import path); docs grep
  `mordheim-web-packages` returns 0 hits; no other file touched.
- P9.4: grep `application.state` over `src/` and `tests/` returns 0 hits;
  `tests/campaign` fully green (the regression net from Phase 0).
