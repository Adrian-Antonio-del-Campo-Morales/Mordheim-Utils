# Web deployment & CI (P8.1)

**Status:** implemented (web migration Phase 8, `web-migration-parallel-plan.md` §9).
**Workflows:** [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) ·
[`.github/workflows/deploy-pages.yml`](../../.github/workflows/deploy-pages.yml)

## CI (`ci.yml`) — runs on every push/PR

Two parallel jobs, gated by a final `ci-green` check:

1. **`python`** — installs `mordheim-utils` reproducibly from `pyproject.toml`
   (`pip install -e ".[dev]"`), generates the KB artefact
   (`tools/knowledge/generate_knowledge_web.py`), verifies determinism with
   `--check` **twice** (before and after the test run: a test mutating the
   artefact fails the pipeline), runs the Python regression net
   (`tests/web tests/contracts tests/campaign tests/architecture tests/knowledge`).
2. **`typescript`** — `npm ci` in `packages/typescript` and
   `apps/warband-manager-web` (lockfile-driven), generates + `--check`s the
   KB artefact, copies it to `apps/warband-manager-web/public/knowledge/`,
   then typecheck → lint → tests → `vite build`. The built `dist/` is
   uploaded as a CI artifact for inspection.

A failure of contract validation, KB validation, any test or the build
blocks the pipeline (acceptance criterion of P8.1).

## Pages publication (`deploy-pages.yml`) — runs on `main` after CI

1. Re-installs, re-generates and `--check`s the KB artefact.
2. Stages it as a static asset at `public/knowledge/knowledge-web.json`
   (per the bundling decision: fetched at runtime, not inlined —
   see [`web-kb-bundling.md`](web-kb-bundling.md)).
3. Re-runs both TypeScript suites (publication requires green tests even
   when the push skipped CI, e.g. a `workflow_dispatch`).
4. Builds with `GITHUB_PAGES=1`, which activates the `base: "/Mordheim-Utils/"`
   switch prepared in P3.1's `vite.config.ts`. The app uses no
   history-based routing, so deep links work under Pages without extra
   configuration.
5. Guards against publishing user data: fails if any `*.mordheim` file ends
   up inside `dist/`. The build comes from a clean checkout; nothing from
   user-data directories is copied into `public/`.
6. Uploads **only `dist/`** via `upload-pages-artifact` and deploys with
   the official `actions/deploy-pages@v4` flow (OIDC, no PAT).

## Requirements on the repository side

- **Pages source** must be set to **GitHub Actions** (Settings → Pages).
  Until then the deploy job fails at `actions/deploy-pages` — intentional:
  activation of publication is the integrator's decision after P7
  (plan §9 note).
- The publish branch filter is `main`; adjust when the integration branch
  is renamed/merged.

## Local reproduction of the CI steps

```bash
pip install -e ".[dev]"
python tools/knowledge/generate_knowledge_web.py
python tools/knowledge/generate_knowledge_web.py --check
python -m pytest tests/web tests/contracts tests/campaign tests/architecture tests/knowledge -q
```

```bash
cd packages/typescript && npm ci && npm run typecheck && npm test
cd ../../apps/warband-manager-web && npm ci
mkdir -p public/knowledge
cp ../../build/generated/knowledge-web/knowledge-web.json public/knowledge/
npm run typecheck && npm run lint && npm test && npm run build
```

Every command above was executed verbatim against this branch and passed.
