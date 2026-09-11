# warband-manager-web

Web port of the Mordheim Campaign Manager — React + Vite + TypeScript.

The scope, architecture rules, remaining parity work and release gates are in
[`docs/decisions/web-migration.md`](../../docs/decisions/web-migration.md).

## Commands

| Command | Purpose |
| --- | --- |
| `npm install` | install dependencies (Node 20+) |
| `npm run dev` | Vite dev server |
| `npm test` | run unit tests once (Vitest, jsdom) |
| `npm run test:watch` | Vitest in watch mode |
| `npm run lint` | ESLint |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run build` | typecheck + production build to `dist/` |
| `npm run preview` | serve the production build locally |

Set `GITHUB_PAGES=1` when building for GitHub Pages to publish under the
repository sub-path (`/Mordheim-Utils/`). CI and Pages wiring are maintained
at repository level.

## Layering rules

- The app is the shell. Campaign domain and application code lives in
  `packages/typescript/` and is imported here, never duplicated.
- The shell receives domain behavior through composition; it must not bypass
  the application service.
- No Combat Lab, NumPy, Cython, Tkinter, YAML loading or browser storage for
  campaigns; these are permanent product boundaries.
