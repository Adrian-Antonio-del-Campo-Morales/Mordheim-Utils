# warband-manager-web

Web port of the Mordheim Campaign Manager — React + Vite + TypeScript.

Part of the parallel web migration: this is the **P3.1 workspace** from
[`web-migration-parallel-plan.md`](../../web-migration-parallel-plan.md).

## Commands

| Command | Purpose |
| --- | --- |
| `npm install` | install dependencies (Node 20+; developed with Node 26) |
| `npm run dev` | Vite dev server |
| `npm test` | run unit tests once (Vitest, jsdom) |
| `npm run test:watch` | Vitest in watch mode |
| `npm run lint` | ESLint |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run build` | typecheck + production build to `dist/` |
| `npm run preview` | serve the production build locally |

Set `GITHUB_PAGES=1` when building for GitHub Pages to publish under the
repository sub-path (`/Mordheim-Utils/`). CI/Pages wiring is task **P8.1** —
do not add workflows from this workspace.

## Layering rules

- This app is only the shell. Campaign **domain** and **application** code
  lives in `packages/typescript/` (tasks P3.4/P3.5/P5.1) and is imported here,
  never duplicated.
- The shell must not import domain code directly yet; it will receive it via
  composition in the vertical slice (P5.2).
- Permanent exclusions (plan §2.4): no Combat Lab, NumPy, Cython, Tkinter,
  YAML loading, and no `localStorage`/IndexedDB for campaigns.

## Parallel-work note

Other agents work on sibling tasks (P3.2 v4 adapter, P4.x KB pipeline,
P3.4 interfaces) in the same repository. This directory is owned by P3.1:
if you need a change here (e.g. new script, shared alias), coordinate via the
parallel plan's ownership rules instead of editing directly.
